"""
DeepShield — OCR Text Anomaly Detection (v3 — calibrated, false-positive safe)
==============================================================================
Changes from v2:
  - Uses shutil.which() to detect Tesseract BEFORE importing pytesseract
  - Empty / short text → score = 0.0 (never suspicious)
  - Only genuinely garbled text (≥6 tokens with high garbled ratio) raises score
  - Score scale: 0.0 normal, 0.6–0.8 clearly random/broken text
"""

import io
import re
import shutil
import string
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# ── Dependency check using shutil.which (most reliable) ───────────────────

import sys, os

_TESSERACT_AVAILABLE = False
_TESS_CMD = None

def _find_tesseract():
    global _TESSERACT_AVAILABLE, _TESS_CMD

    # 1. Check PATH first
    found = shutil.which("tesseract")
    if found:
        _TESS_CMD = found
        _TESSERACT_AVAILABLE = True
        return

    # 2. Windows common install locations (in case PATH not updated)
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            _TESS_CMD = c
            _TESSERACT_AVAILABLE = True
            return

    _TESSERACT_AVAILABLE = False
    logger.warning("Tesseract binary not found in PATH or common locations — OCR skipped")

_find_tesseract()

if _TESSERACT_AVAILABLE:
    try:
        import pytesseract
        if _TESS_CMD:
            pytesseract.pytesseract.tesseract_cmd = _TESS_CMD
        _ver = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract {_ver} ready at {_TESS_CMD or 'PATH'} — OCR enabled")
    except Exception as e:
        _TESSERACT_AVAILABLE = False
        logger.warning(f"pytesseract init failed: {e} — OCR skipped")


# ── Token anomaly helpers (unchanged - just stricter minimum token threshold) ──

def _garbled_ratio(text: str) -> float:
    tokens = text.split()
    if not tokens:
        return 0.0
    vowels = set("aeiouAEIOU")
    garbled = 0
    for tok in tokens:
        clean = tok.strip(string.punctuation)
        if len(clean) < 2:
            continue
        has_vowel = any(c in vowels for c in clean)
        if len(clean) > 5 and not has_vowel:
            garbled += 1
            continue
        if len(clean) > 3 and not (clean.istitle() or clean.isupper() or clean.islower()):
            mixed = sum(1 for c in clean if c.isupper()) / len(clean)
            if 0.2 < mixed < 0.8:
                garbled += 1
                continue
        run, max_run = 0, 0
        for ch in clean.lower():
            if ch.isalpha() and ch not in vowels:
                run += 1; max_run = max(max_run, run)
            else:
                run = 0
        if max_run > 4:
            garbled += 1
    return garbled / max(len(tokens), 1)


def _has_random_string(text: str) -> bool:
    pattern = r'\b[A-Z]{2,}[\.\-_][A-Z]{2,}\b|\b[A-Z0-9]{6,}\b'
    common = {"HTTP", "HTTPS", "URL", "PDF", "JPEG", "PNG", "JPG", "THE", "AND", "FOR", "NOT", "ARE", "WITH"}
    return any(m not in common and not m.isnumeric() for m in re.findall(pattern, text))


# ── Main run ───────────────────────────────────────────────────────────────

def run(image_bytes: bytes) -> dict:
    """
    OCR text anomaly analysis.

    Score guide:
      0.0   → no text found or Tesseract unavailable
      0.0   → clean, readable text (no anomaly)
      0.6–0.8 → heavily garbled / random character soup
    """
    if not _TESSERACT_AVAILABLE:
        return {
            "text_anomaly_score": 0.0,
            "extracted_text": "",
            "flags": ["OCR skipped — Tesseract not installed"],
            "available": False,
        }

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        if w < 800:
            img = img.resize((int(w * 800 / w), int(h * 800 / w)), Image.Resampling.LANCZOS)

        try:
            raw_text = pytesseract.image_to_string(img, config="--psm 11 --oem 3")
        except Exception as ocr_err:
            logger.warning(f"OCR extraction error: {ocr_err}")
            return {
                "text_anomaly_score": 0.0,
                "extracted_text": "",
                "flags": [f"OCR extraction failed: {str(ocr_err)[:60]}"],
                "available": True,
            }

        text = raw_text.strip()
        n_tokens = len(text.split())

        # ── No text → score 0.0, never suspicious ────────────────────────
        if not text or n_tokens < 2:
            return {
                "text_anomaly_score": 0.0,
                "extracted_text": "",
                "flags": ["No visible text in image — OCR score neutral"],
                "available": True,
            }

        logger.info(f"OCR: {n_tokens} tokens extracted")

        # ── Require ≥ 6 tokens before penalising (avoid single-word FPs) ──
        if n_tokens < 6:
            return {
                "text_anomaly_score": 0.0,
                "extracted_text": text[:200],
                "flags": [f"Too few tokens ({n_tokens}) — OCR score neutral"],
                "available": True,
            }

        score  = 0.0
        flags  = []
        garbled    = _garbled_ratio(text)
        has_random = _has_random_string(text)

        if garbled > 0.60:
            score += 0.60
            flags.append(f"Text anomaly: {int(garbled*100)}% garbled tokens (AI hallucinated text)")
        elif garbled > 0.35:
            score += 0.25
            flags.append(f"Partial text anomaly: {int(garbled*100)}% garbled tokens")

        if has_random and n_tokens >= 6:
            score += 0.20
            flags.append("Random uppercase string detected (AI text artifact pattern)")

        score = round(min(0.80, score), 4)   # hard cap at 0.80

        if not flags:
            flags.append(f"Text present ({n_tokens} tokens) — appears coherent")

        return {
            "text_anomaly_score": score,
            "extracted_text": text[:400],
            "n_tokens": n_tokens,
            "garbled_ratio": round(garbled, 3),
            "flags": flags[:3],
            "available": True,
        }

    except Exception as exc:
        logger.error(f"OCR analysis error: {exc}")
        return {
            "text_anomaly_score": 0.0,
            "extracted_text": "",
            "flags": [f"OCR analysis error: {str(exc)[:80]}"],
            "available": False,
        }
