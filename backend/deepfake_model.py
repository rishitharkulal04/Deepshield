"""
DeepShield — Deepfake Detection Module (v2)
============================================
Uses dima806/deepfake_vs_real_image_detection (ViT fine-tuned on FaceForensics++)
for facial manipulation / face-swap deepfake detection.

Key improvements over v1:
  - Proper 224x224 resize with padding (not thumbnail which distorts)
  - Returns calibrated 0-1 probability (not raw classifier score)
  - Graceful fallback if model unavailable
  - Explicit handling of LABEL_0 / LABEL_1 numeric labels (dima806 model
    sometimes returns numeric labels instead of 'Fake'/'Real' strings,
    causing the substring parser to silently default everything to Real)
"""

import io
import logging
import torch
import numpy as np
from PIL import Image
from transformers import pipeline

logger = logging.getLogger(__name__)

DEEPFAKE_MODEL = "dima806/deepfake_vs_real_image_detection"

_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        logger.info("Loading deepfake ViT model (dima806) — first run ~350 MB ...")
        device = 0 if torch.cuda.is_available() else -1
        try:
            _detector = pipeline(
                "image-classification",
                model=DEEPFAKE_MODEL,
                device=device,
            )
            logger.info("Deepfake ViT model loaded.")
        except Exception as exc:
            logger.error(f"Failed to load deepfake model on GPU, retrying CPU: {exc}")
            _detector = pipeline(
                "image-classification",
                model=DEEPFAKE_MODEL,
                device=-1,
            )
    return _detector


def preprocess(image_bytes: bytes, size: int = 224) -> Image.Image:
    """
    Resize to (size x size) with letterbox padding to avoid distortion.
    Returns RGB PIL image ready for the model.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # Maintain aspect ratio, pad with neutral gray
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (128, 128, 128))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    canvas.paste(img, offset)
    return canvas


def run(image_bytes: bytes) -> dict:
    """
    Run deepfake detection.

    Returns:
        deepfake_prob  : float  [0, 1] — probability image is a deepfake
        real_prob      : float  [0, 1] — probability image is real
        raw_label      : str    — top label from model
        available      : bool   — False if model could not be loaded
    """
    try:
        img = preprocess(image_bytes)
        detector = _get_detector()
        results = detector(img, top_k=2)

        fake_prob = 0.0
        real_prob = 0.0

        # dima806 model numeric label mapping:
        #   LABEL_0 → Fake (deepfake class)
        #   LABEL_1 → Real
        # This must be resolved BEFORE the substring search because
        # "label_0" does not match any keyword and falls through silently,
        # causing the model to default everything to Real.
        NUMERIC_LABEL_MAP = {
            "label_0": "fake",
            "label_1": "real",
            "0":       "fake",
            "1":       "real",
        }

        for r in results:
            raw_lbl = r["label"]
            lbl = NUMERIC_LABEL_MAP.get(raw_lbl.lower(), raw_lbl.lower())
            score = float(r["score"])
            # dima806 model labels: "Fake" and "Real" (or remapped from LABEL_0/1)
            if any(k in lbl for k in ("fake", "deepfake", "artificial", "synthetic", "generated")):
                fake_prob = max(fake_prob, score)
            elif any(k in lbl for k in ("real", "authentic", "natural", "genuine")):
                real_prob = max(real_prob, score)

        # If only one class returned, infer the other
        if fake_prob == 0.0 and real_prob == 0.0:
            top_lbl = results[0]["label"].lower()
            if any(k in top_lbl for k in ("fake", "deepfake", "synthetic")):
                fake_prob = float(results[0]["score"])
                real_prob = 1.0 - fake_prob
            else:
                real_prob = float(results[0]["score"])
                fake_prob = 1.0 - real_prob
        elif fake_prob == 0.0:
            fake_prob = 1.0 - real_prob
        elif real_prob == 0.0:
            real_prob = 1.0 - fake_prob

        # Normalize to sum to 1
        total = fake_prob + real_prob
        if total > 0:
            fake_prob /= total
            real_prob /= total

        return {
            "deepfake_prob": round(fake_prob, 4),
            "real_prob": round(real_prob, 4),
            "raw_label": results[0]["label"],
            "available": True,
        }

    except Exception as exc:
        logger.error(f"Deepfake model error: {exc}")
        return {
            "deepfake_prob": 0.0,
            "real_prob": 1.0,
            "raw_label": "error",
            "available": False,
            "error": str(exc),
        }
