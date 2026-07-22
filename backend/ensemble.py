"""
DeepShield — Smart Ensemble Scoring v12 (Three-Class Classification)
=====================================================================
5-signal weighted ensemble with 3-class output:
  - "Deepfake"     : face-swap / face-manipulation on a real image
  - "AI Generated" : full-scene AI/synthetic image (Stable Diffusion, DALL-E, etc.)
  - "Real"         : authentic photograph with no significant AI signals

Formula:
  ai_score = model_score*0.50 + text_anomaly*0.10 + metadata*0.10
           + frequency_score*0.20 + face_anomaly*0.10

Thresholds (v12):
  Deepfake class  : deepfake_prob > 0.50  (ViT primary signal)
  AI Generated    : ai_score > 0.65       (ensemble primary signal)
  Real            : everything else

False-positive veto (v12 — narrowed):
  ALL conditions must hold AND score < 0.65 AND is_deepfake_face is False:
  deepfake_prob < 0.15, clip_real > 0.65, artifact < 0.35
  NOTE: `is_deepfake_face` guard prevents vetoing deepfakes that fool CLIP.
"""

import logging

import deepfake_model
import clip_model
import artifact_model
import ocr_analysis
import frequency_analysis
import face_analysis

logger = logging.getLogger(__name__)

# ── Layer weights (v10) ────────────────────────────────────────────────────
WEIGHT_MODEL     = 0.50   # CLIP + ViT combined (primary signal)
WEIGHT_TEXT      = 0.10   # OCR text anomaly
WEIGHT_METADATA  = 0.10   # EXIF / dimensions
WEIGHT_FREQUENCY = 0.20   # FFT / GAN
WEIGHT_FACE      = 0.10   # Face geometry

CLIP_SUB_WEIGHT  = 0.67   # 2/3 of model_score from CLIP
VIT_SUB_WEIGHT   = 0.33   # 1/3 of model_score from ViT

# ── Thresholds (v11) ───────────────────────────────────────────────────────
THRESHOLD_AI         = 0.65   # ensemble score → AI Generated
THRESHOLD_SUSPICIOUS = 0.40   # ensemble score → borderline (unused in new 3-class)
THRESHOLD_DEEPFAKE   = 0.50   # deepfake_prob  → Deepfake class

# ── False-positive veto ─────────────────────────────────────────────────────
VETO_DF_MAX        = 0.15
VETO_CLIP_REAL_MIN = 0.65
VETO_ARTIFACT_MAX  = 0.35

# ── CLIP Override ───────────────────────────────────────────────────────────
CLIP_OVERRIDE_CLIP_MIN     = 0.78
CLIP_OVERRIDE_ARTIFACT_MIN = 0.20


def run(image_bytes: bytes) -> dict:  # noqa: C901
    logger.info("Ensemble v10: running 5-layer detection pipeline...")

    # ── Layer 1: CLIP + ViT ─────────────────────────────────────────────────
    logger.info("  [1a] ViT deepfake model...")
    df_result    = deepfake_model.run(image_bytes)
    deepfake_prob = df_result.get("deepfake_prob", 0.0)

    logger.info("  [1b] CLIP AI-image model...")
    clip_result  = clip_model.run(image_bytes)
    clip_ai_prob = clip_result.get("ai_prob", 0.0)

    model_score = CLIP_SUB_WEIGHT * clip_ai_prob + VIT_SUB_WEIGHT * deepfake_prob

    # ── Layer 2: OCR ────────────────────────────────────────────────────────
    logger.info("  [2] OCR text anomaly...")
    ocr_result = ocr_analysis.run(image_bytes)
    text_score = ocr_result.get("text_anomaly_score", 0.0)

    # ── Layer 3: Forensic artifacts + metadata ──────────────────────────────
    logger.info("  [3] Forensic / metadata analysis...")
    art_result    = artifact_model.run(image_bytes)
    artifact_prob = art_result.get("artifact_prob", 0.0)
    meta_signals  = art_result.get("signals", {})
    metadata_score = float(meta_signals.get("metadata", 0.0))

    # ── Layer 4: Frequency ───────────────────────────────────────────────────
    logger.info("  [4] Frequency / GAN analysis...")
    freq_result     = frequency_analysis.run(image_bytes)
    frequency_score = freq_result.get("frequency_score", 0.0)

    # ── Layer 5: Face ────────────────────────────────────────────────────────
    logger.info("  [5] Face consistency analysis...")
    face_result = face_analysis.run(image_bytes)
    face_score  = face_result.get("face_anomaly_score", 0.0)

    # ── Debug log — all intermediate scores ─────────────────────────────────
    debug_scores = {
        "model_score":     round(model_score,     4),
        "text_score":      round(text_score,       4),
        "metadata_score":  round(metadata_score,   4),
        "frequency_score": round(frequency_score,  4),
        "face_score":      round(face_score,       4),
        "clip_ai_prob":    round(clip_ai_prob,     4),
        "deepfake_prob":   round(deepfake_prob,    4),
        "artifact_prob":   round(artifact_prob,    4),
    }
    logger.info(f"  DEBUG layer scores: {debug_scores}")
    print(f"[DeepShield v10] Layer scores: {debug_scores}")

    # ── Step 1: Weighted ensemble ─────────────────────────────────────────
    ai_score = (
        WEIGHT_MODEL     * model_score     +
        WEIGHT_TEXT      * text_score      +
        WEIGHT_METADATA  * metadata_score  +
        WEIGHT_FREQUENCY * frequency_score +
        WEIGHT_FACE      * face_score
    )
    ai_score = round(min(1.0, max(0.0, ai_score)), 4)
    logger.info(f"  Ensemble score: {ai_score:.4f}")

    # ── Step 2: Soft boost — only when CLIP + forensics strongly agree ────
    if clip_ai_prob > 0.80 and artifact_prob > 0.60:
        ai_score = min(1.0, ai_score * 1.05)
        ai_score = round(ai_score, 4)
        logger.info(f"  Soft boost applied → {ai_score:.4f}")

    # ── Pre-compute deepfake class flag (needed by both Step 3 veto and Step 5 verdict) ───
    # Priority 1: ViT deepfake_prob > 0.50 → face manipulation on a real image.
    # Must be evaluated BEFORE Step 3 so the FP veto guard can reference it.
    is_deepfake_face = deepfake_prob > THRESHOLD_DEEPFAKE

    # ── Step 3: False-positive veto ───────────────────────────────────────
    # Guard: if ViT has already flagged this as a deepfake face, do NOT veto.
    # A deepfake that fools CLIP (high clip_real) would otherwise be suppressed
    # to "Real" even though the face-manipulation model is confident.
    veto_real = (
        deepfake_prob < VETO_DF_MAX and
        clip_result.get("real_prob", 0.0) > VETO_CLIP_REAL_MIN and
        artifact_prob < VETO_ARTIFACT_MAX
    )
    if veto_real and ai_score < THRESHOLD_AI and not is_deepfake_face:
        ai_score = min(ai_score, THRESHOLD_SUSPICIOUS - 0.01)
        ai_score = round(ai_score, 4)
        logger.info(f"  FP veto applied → {ai_score:.4f}")
    elif veto_real and is_deepfake_face:
        logger.info("  FP veto SKIPPED — deepfake_face flag is set (ViT confident)")

    # ── Step 4: CLIP Override Rule ────────────────────────────────────────
    clip_override = (
        clip_ai_prob  >= CLIP_OVERRIDE_CLIP_MIN and
        artifact_prob >= CLIP_OVERRIDE_ARTIFACT_MIN and
        deepfake_prob <  0.15 and
        not veto_real
    )
    if clip_override and ai_score < THRESHOLD_AI:
        boosted  = clip_ai_prob * 0.78 + artifact_prob * 0.22
        ai_score = max(ai_score, boosted)
        ai_score = round(min(1.0, ai_score), 4)
        logger.info(f"  CLIP override → {ai_score:.4f}")

    # ── Step 5: Three-Class Verdict ──────────────────────────────────────
    # Priority 2: ensemble score high → full-scene AI synthetic image
    is_ai_generated  = (not is_deepfake_face) and (ai_score > THRESHOLD_AI)

    if is_deepfake_face:
        classification = "Deepfake"
        verdict        = "Deepfake"   # used by existing code paths
        is_ai          = False        # deepfake ≠ fully AI-generated scene
    elif is_ai_generated:
        classification = "AI Generated"
        verdict        = "AI Generated"
        is_ai          = True
    else:
        classification = "Real"
        verdict        = "Real"       # replaces old "Authentic"
        is_ai          = False

    risk_score  = int(round(ai_score * 100)) if not is_deepfake_face else int(round(deepfake_prob * 100))
    confidence  = _compute_confidence(ai_score, deepfake_prob, clip_ai_prob, artifact_prob)
    explanation = _build_explanation(
        verdict, ai_score, df_result, clip_result, art_result,
        ocr_result, freq_result, face_result, clip_override
    )
    indicators  = _build_indicators(
        df_result, clip_result, art_result,
        ocr_result, freq_result, face_result,
        ai_score, veto_real, clip_override
    )
    reasons = _build_reasons(
        ocr_result, art_result, freq_result, face_result,
        clip_result, df_result, clip_override
    )

    return {
        # ── Three-class fields (new) ──────────────────────────────────────
        "classification":        classification,  # "Real" / "AI Generated" / "Deepfake"
        "is_deepfake_face":      is_deepfake_face,
        # ── Core fields (backward compat) ────────────────────────────────
        "verdict":               verdict,
        "risk_score":            risk_score,
        "confidence":            confidence,
        "indicators":            indicators,
        "final_score":           ai_score,
        "ai_score":              ai_score,
        "is_ai_generated":       is_ai_generated,
        "is_deepfake":           is_deepfake_face,
        "is_synthetic":          is_ai_generated or is_deepfake_face,
        "is_explicit_fake":      False,
        "is_body_ai_generated":  False,
        "confidence_score":      confidence,
        "explanation":           explanation,
        "reasons":               reasons,
        "clip_override_applied": clip_override,
        # Debug / transparency
        "debug_scores":   debug_scores,
        "layer_scores": {
            "model_score":      round(model_score,      4),
            "text_anomaly":     round(text_score,        4),
            "metadata_score":   round(metadata_score,    4),
            "frequency_score":  round(frequency_score,   4),
            "face_anomaly":     round(face_score,        4),
        },
        "model_confidences": {
            "clip_ai_prob":      round(clip_ai_prob   * 100, 1),
            "deepfake_prob":     round(deepfake_prob   * 100, 1),
            "artifact_prob":     round(artifact_prob   * 100, 1),
            "ai_generated":      round(clip_ai_prob   * 100, 1),
            "deepfake":          round(deepfake_prob   * 100, 1),
            "explicit_fake":     0.0,
            "body_manipulation": round(artifact_prob   * 100, 1),
        },
        "raw_scores": {
            "final_ensemble_score": ai_score,
            "clip_ai_prob":         clip_ai_prob,
            "clip_real_prob":       clip_result.get("real_prob", 0.0),
            "deepfake_prob":        deepfake_prob,
            "artifact_prob":        artifact_prob,
            "text_anomaly_score":   text_score,
            "frequency_score":      frequency_score,
            "face_anomaly_score":   face_score,
            "fake_probability":     ai_score,
            "ela":                  meta_signals.get("ela",               0.0),
            "noise_uniformity":     meta_signals.get("noise_uniformity",  0.0),
            "dct_spectral":         meta_signals.get("dct_spectral",      0.0),
            "edge_coherence":       meta_signals.get("edge_coherence",    0.0),
            "chroma_noise":         meta_signals.get("chroma_noise",      0.0),
        },
        "_ocr":  ocr_result,
        "_freq": freq_result,
        "_face": face_result,
        # ── Unified public output (user-facing) ─────────────────────────────
        # Internal classification ("Real"/"AI Generated"/"Deepfake") is kept above.
        # These three fields present the simplified view the user sees in the UI.
        **_public_verdict_output(ai_score, classification, deepfake_prob, clip_ai_prob),
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def _compute_confidence(final: float, df: float, clip: float, art: float) -> int:
    scores = [clip, df, art]
    mean   = sum(scores) / 3
    var    = sum((s - mean)**2 for s in scores) / 3
    agree  = max(0.0, 1.0 - var * 4)

    if final > THRESHOLD_AI:
        dist = (final - THRESHOLD_AI) / (1.0 - THRESHOLD_AI)
    elif final > THRESHOLD_SUSPICIOUS:
        dist = 0.0
    else:
        dist = (THRESHOLD_SUSPICIOUS - final) / THRESHOLD_SUSPICIOUS

    raw = 0.5 + 0.3 * dist + 0.2 * agree
    return int(round(min(100, max(10, raw * 100))))


def _build_reasons(ocr, art, freq, face, clip, df, clip_override) -> list:
    reasons = []
    clip_prob = clip.get("ai_prob", 0.0)

    if clip_prob >= 0.80:
        reasons.append(f"CLIP model: {clip_prob*100:.0f}% AI-generated confidence")
        top = clip.get("top_ai_signal", "")
        if top:
            reasons.append(f"Top AI signal: '{top}'")
    elif clip_prob >= 0.55:
        reasons.append(f"CLIP model: {clip_prob*100:.0f}% AI probability (borderline)")

    if ocr.get("text_anomaly_score", 0) > 0.3:
        reasons.append("Suspicious text detected — garbled/random character sequences")

    for flag in art.get("flags", []):
        if "EXIF" in flag or "AI model output size" in flag:
            reasons.append(flag)
            break

    if freq.get("frequency_score", 0) > 0.30:
        reasons.append(f"GAN frequency artifacts detected (score: {freq['frequency_score']:.2f})")

    if face.get("face_detected") and face.get("face_anomaly_score", 0) > 0.40:
        reasons.append(f"Face geometry anomaly (score: {face['face_anomaly_score']:.2f})")

    ela = art.get("signals", {}).get("ela", 0.0)
    if ela > 0.70:
        reasons.append(f"ELA: flat error level ({ela:.2f}) — AI synthesis signature")

    if clip_override:
        reasons.append("CLIP override: full-scene AI image pattern (Gemini/DALL-E)")

    df_prob = df.get("deepfake_prob", 0.0)
    if df_prob > 0.60:
        reasons.append(f"Deepfake detected — {df_prob*100:.0f}% manipulation probability")

    return reasons[:8] if reasons else ["No strong AI indicators found — image appears authentic"]


def _build_explanation(verdict, score, df, clip, art, ocr, freq, face, clip_override=False) -> str:
    parts = []
    if verdict == "Authentic":
        parts.append(f"Image analysis indicates an authentic photograph (ensemble score {score:.2f}).")
        if clip.get("real_prob", 0) > 0.6:
            parts.append("CLIP model strongly matches real photography.")
        return " ".join(parts)

    if verdict == "Suspicious":
        parts.append(f"Borderline result (ensemble score {score:.2f}). Manual review advised.")
        if clip.get("ai_prob", 0) > 0.45:
            top = clip.get("top_ai_signal", "")
            parts.append(f"CLIP AI similarity detected. Strongest match: '{top}'." if top else "CLIP AI similarity detected.")
        return " ".join(parts)

    # AI Generated
    parts.append(f"High probability of AI/synthetic origin (ensemble score {score:.2f}).")
    if clip_override:
        parts.append(f"CLIP override: {clip.get('ai_prob',0)*100:.0f}% AI confidence. Full-scene AI image.")
    elif clip.get("ai_prob", 0) > 0.55:
        parts.append(f"CLIP: {clip.get('ai_prob',0)*100:.0f}% AI vs {clip.get('real_prob',0)*100:.0f}% real.")
    if ocr.get("text_anomaly_score", 0) > 0.3:
        parts.append("Anomalous text patterns detected.")
    if freq.get("frequency_score", 0) > 0.30:
        parts.append("GAN/diffusion frequency artifacts found.")
    if face.get("face_detected") and face.get("face_anomaly_score", 0) > 0.40:
        parts.append("Facial geometry shows AI generation characteristics.")
    return " ".join(parts)


def _build_indicators(df, clip, art, ocr, freq, face, score, veto, clip_override=False) -> list:
    items = []
    ai_p  = clip.get("ai_prob", 0.0)
    re_p  = clip.get("real_prob", 0.0)
    top   = clip.get("top_ai_signal", "")

    # CLIP
    if ai_p > 0.65:
        label = f"CLIP model: {ai_p*100:.0f}% AI-generated vs {re_p*100:.0f}% real"
        if top: label += f" — '{top}'"
        items.append(label)
    elif ai_p > 0.40:
        items.append(f"CLIP model: borderline ({ai_p*100:.0f}% AI / {re_p*100:.0f}% real)")
    else:
        items.append(f"CLIP model: {re_p*100:.0f}% real photography confidence")

    # ViT
    df_p = df.get("deepfake_prob", 0.0)
    if df_p > 0.65:
        items.append(f"ViT: {df_p*100:.0f}% deepfake probability — HIGH")
    elif clip_override:
        items.append(f"ViT: {df_p*100:.0f}% (full-scene AI — CLIP override)")
    else:
        items.append(f"ViT: {df_p*100:.0f}% deepfake probability")

    # OCR
    ocr_s = ocr.get("text_anomaly_score", 0.0)
    if ocr_s > 0.3:
        items.append(f"OCR text anomaly: {ocr_s:.2f}")
    elif ocr.get("available"):
        items.append("OCR: no anomalous text")

    # Frequency
    freq_s = freq.get("frequency_score", 0.0)
    if freq_s > 0.30:
        items.append(f"GAN frequency score: {freq_s:.2f}")
    elif freq.get("available"):
        items.append(f"Frequency: {freq_s:.2f} — natural spectrum")

    # Face
    face_s = face.get("face_anomaly_score", 0.0)
    if face.get("face_detected"):
        tag = "AI geometry" if face_s > 0.40 else "natural geometry"
        items.append(f"Face: {face_s:.2f} — {tag}")
    elif face.get("available"):
        items.append("Face: no face detected")

    # Forensic flags (top 2)
    for flag in art.get("flags", [])[:2]:
        if flag and "No significant" not in flag:
            items.append(flag)

    if clip_override:
        items.append(f"CLIP override fired (CLIP={ai_p*100:.0f}%)")
    if veto and score < THRESHOLD_SUSPICIOUS:
        items.append("FP-guard active — image judged authentic")

    items.append(
        f"Ensemble v12: {score:.3f} | "
        f"Model 50% + Text 10% + Meta 10% + Freq 20% + Face 10%"
    )
    return items[:10]


# ── Unified public output (user-facing layer) ──────────────────────────────────

def _public_verdict_output(
    ai_score:      float,
    classification: str,
    deepfake_prob:  float,
    clip_ai_prob:   float,
) -> dict:
    """
    Maps internal detection scores to the simplified user-facing verdict.

    Rules (output-only, no model changes):
      ai_score >= 0.65  → "Deepfake / Manipulated Media Detected"
      ai_score >= 0.40  → "Suspicious (Possible Deepfake)"
      else              → "Clean / Authentic"

    Both "AI Generated" and "Deepfake" internal classes collapse to the same
    public label because end-users need a single actionable verdict.
    The internal classification / ai_score / deepfake_prob are preserved
    in all other return fields for legal docs, police complaints, and logging.
    """
    # Public prediction
    if ai_score >= 0.65:
        public_prediction = "Deepfake / Manipulated Media Detected"
    elif ai_score >= 0.40:
        public_prediction = "Suspicious (Possible Deepfake)"
    else:
        public_prediction = "Clean / Authentic"

    # Internal category label (more precise — used in legal toolkit / reports)
    if classification == "Deepfake":
        category_internal = "Deepfake (Face Manipulation)"
    elif classification == "AI Generated":
        category_internal = "AI Generated / Synthetic"
    else:
        category_internal = "Real / Authentic"

    # Explanation rules
    if classification == "Deepfake" or deepfake_prob >= 0.50:
        public_explanation = "This image shows signs of facial manipulation (deepfake)."
    elif classification == "AI Generated" or (ai_score >= 0.65 and clip_ai_prob >= 0.55):
        public_explanation = "This appears to be fully AI-generated synthetic content."
    elif ai_score >= 0.40:
        public_explanation = "This image contains suspicious patterns but is not conclusive."
    else:
        public_explanation = "No significant AI synthesis or manipulation indicators detected."

    return {
        "public_prediction":  public_prediction,
        "category_internal":  category_internal,
        "public_explanation": public_explanation,
    }
