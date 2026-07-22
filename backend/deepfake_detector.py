"""
DeepShield — Forensic Image Analysis Engine (v7 — Ensemble Rewrite)
====================================================================
This module is the primary entry point called by main.py → analyze_image().

It now delegates to the modular ensemble pipeline:
  deepfake_model  → ViT FaceForensics++ (face deepfake)
  clip_model      → CLIP ViT-L/14 (AI image detection)
  artifact_model  → ELA / DCT / noise / metadata (forensic signals)
  ensemble        → weighted scoring + calibrated thresholds

Output contract is identical to the original deepfake_detector.py so
main.py requires ZERO changes.
"""

import io
import logging
from PIL import Image

import ensemble

logger = logging.getLogger(__name__)

NSFW_MODEL = "Falconsai/nsfw_image_detection"
_nsfw_detector = None


def _get_nsfw_detector():
    global _nsfw_detector
    if _nsfw_detector is None:
        import torch
        from transformers import pipeline
        logger.info("Loading NSFW model...")
        _nsfw_detector = pipeline(
            "image-classification",
            model=NSFW_MODEL,
            device=0 if torch.cuda.is_available() else -1,
        )
        logger.info("NSFW model loaded.")
    return _nsfw_detector


NSFW_LABEL_MAP = {
    "nsfw": "EXPLICIT", "sfw": "SAFE", "normal": "SAFE", "safe": "SAFE",
    "explicit": "EXPLICIT", "porn": "EXPLICIT", "sexy": "SUGGESTIVE",
    "hentai": "AI_HENTAI", "drawing": "DRAWING", "neutral": "SAFE",
}


def _run_nsfw(image_bytes: bytes) -> dict:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        detector = _get_nsfw_detector()
        results = detector(img, top_k=5)

        scores = {}
        for r in results:
            label = r["label"].lower().strip()
            category = NSFW_LABEL_MAP.get(label, label.upper())
            scores[category] = max(scores.get(category, 0.0), r["score"])

        explicit_score   = scores.get("EXPLICIT",   0.0)
        suggestive_score = scores.get("SUGGESTIVE", 0.0)
        ai_hentai_score  = scores.get("AI_HENTAI",  0.0)
        safe_score       = scores.get("SAFE",        0.0)
        nsfw_score       = max(explicit_score, ai_hentai_score) + suggestive_score * 0.4

        if nsfw_score >= 0.75:
            category, level = "EXPLICIT", "CRITICAL"
        elif nsfw_score >= 0.50:
            category, level = "EXPLICIT", "HIGH"
        elif nsfw_score >= 0.30:
            category, level = "SUGGESTIVE", "MEDIUM"
        elif ai_hentai_score >= 0.4:
            category, level = "AI_HENTAI", "HIGH"
        else:
            category, level = "SAFE", "NONE"

        flags = []
        if category == "EXPLICIT":
            flags.append(f"Explicit content detected — confidence {int(explicit_score*100)}%")
        elif category == "AI_HENTAI":
            flags.append("AI-generated explicit illustration detected")
        elif category == "SUGGESTIVE":
            flags.append("Suggestive content detected — borderline NSFW classification")
        if not flags:
            flags.append("No explicit content detected by NSFW classification model")

        return {
            "is_explicit": category in ("EXPLICIT", "AI_HENTAI"),
            "category": category,
            "level": level,
            "nsfw_score": round(nsfw_score, 4),
            "explicit_score": round(explicit_score, 4),
            "suggestive_score": round(suggestive_score, 4),
            "safe_score": round(safe_score, 4),
            "flags": flags[:5],
            "raw_scores": scores,
            "model_used": NSFW_MODEL,
        }
    except Exception as exc:
        logger.error(f"NSFW detection failed: {exc}")
        return {
            "is_explicit": False, "category": "UNKNOWN", "level": "UNKNOWN",
            "nsfw_score": 0.0, "explicit_score": 0.0,
            "suggestive_score": 0.0, "safe_score": 0.0,
            "flags": ["NSFW model unavailable — manual review recommended"],
            "raw_scores": {}, "model_used": NSFW_MODEL, "error": str(exc),
        }


def analyze_image(image_bytes: bytes) -> dict:
    """
    Full analysis pipeline.

    Returns dict with keys:
      risk_score, verdict, confidence, indicators,
      model_used, nsfw, raw_scores
    """
    logger.info("analyze_image: starting ensemble pipeline...")

    # 1. Core ensemble (deepfake + CLIP + artifact)
    result = ensemble.run(image_bytes)

    # 2. NSFW detection
    nsfw_result = _run_nsfw(image_bytes)

    # 3. NSFW additive boost (small, capped)
    risk_score = result["risk_score"]
    if nsfw_result.get("is_explicit") and nsfw_result.get("nsfw_score", 0) > 0.5:
        nsfw_boost = int(nsfw_result["nsfw_score"] * 15)
        risk_score = min(100, risk_score + nsfw_boost)

    # 4. Three-class classification (from ensemble v11)
    classification = result.get("classification", "Real")  # "Real" / "AI Generated" / "Deepfake"

    # 4a. Risk-score based legacy verdict (kept for any downstream consumers)
    if classification == "Deepfake":
        verdict = "Deepfake"
    elif classification == "AI Generated":
        verdict = "AI Generated"
    elif risk_score >= 75:
        verdict = "AI Generated"
    elif risk_score >= 55:
        verdict = "Suspicious"
    else:
        verdict = "Real"

    # 5. Indicators
    indicators = list(result.get("indicators", []))
    for flag in nsfw_result.get("flags", [])[:2]:
        if flag and "No explicit" not in flag:
            indicators.append(flag)
    indicators = indicators[:6]

    return {
        "classification": classification,          # "Real" / "AI Generated" / "Deepfake"
        "risk_score":     risk_score,
        "verdict":        verdict,
        "confidence":     result["confidence"],
        "indicators":     indicators,
        "model_used":     "Ensemble v12: CLIP ViT-L/14 + dima806 ViT + Forensic Artifacts",
        "nsfw":           nsfw_result,
        "raw_scores":     result["raw_scores"],
        "is_deepfake":    result.get("is_deepfake", False),
        "is_ai_generated": result.get("is_ai_generated", False),
        # ── Unified user-facing output (from ensemble._public_verdict_output) ──
        "public_prediction":  result.get("public_prediction",  "Clean / Authentic"),
        "category_internal":  result.get("category_internal",  "Real / Authentic"),
        "public_explanation": result.get("public_explanation", ""),
    }
