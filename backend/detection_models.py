"""
DeepShield — detection_models.py (v7 — thin adapter)
=====================================================
ensemble_detection() is called by main.py to fill the `detection` sub-dict
returned to the frontend (Scan.jsx).

This module now delegates to ensemble.run() so there is a single source
of truth for scoring. The output schema is unchanged from v6.
"""

import logging
import ensemble

logger = logging.getLogger(__name__)


def ensemble_detection(image_bytes: bytes) -> dict:
    """
    Wrapper around ensemble.run() that returns the exact schema
    expected by main.py's `detection` key.
    """
    try:
        result = ensemble.run(image_bytes)

        return {
            "is_ai_generated":       result["is_ai_generated"],
            "is_deepfake":           result["is_deepfake"],
            "is_explicit_fake":      result.get("is_explicit_fake", False),
            "is_body_ai_generated":  result.get("is_body_ai_generated", False),
            "confidence_score":      result["confidence_score"],
            "explanation":           result["explanation"],
            "is_synthetic":          result["is_synthetic"],
            "model_confidences":     result.get("model_confidences", {}),
        }

    except Exception as exc:
        logger.error(f"ensemble_detection wrapper error: {exc}")
        return {
            "is_ai_generated":       False,
            "is_deepfake":           False,
            "is_explicit_fake":      False,
            "is_body_ai_generated":  False,
            "confidence_score":      0.0,
            "explanation":           f"Detection error: {str(exc)}",
            "is_synthetic":          False,
            "model_confidences":     {},
        }
