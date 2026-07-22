"""
DeepShield — Frequency Domain / GAN Artifact Detection (v2 — calibrated)
=========================================================================
Changes from v1:
  - All sub-scores clamped to 0.0–0.50 max (was 0.0–1.0)
  - Radial falloff threshold raised (less sensitive to real photos)
  - Quadrant asymmetry threshold raised (many real photos are slightly asymmetric)
  - Periodic peak detector requires stronger peak-to-mean ratio
  - HF noise floor threshold raised (real photos shot at low ISO are also clean)
  - Overall cap: frequency_score ≤ 0.50

Score meaning:
  0.0–0.15 → real photo spectrum
  0.15–0.35 → borderline / inconclusive
  0.35–0.50 → GAN/diffusion artifacts likely
"""

import io
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def _fft_magnitude(gray_np: np.ndarray) -> np.ndarray:
    f  = np.fft.fft2(gray_np.astype(np.float32))
    fs = np.fft.fftshift(f)
    return np.log1p(np.abs(fs))


def _radial_falloff_score(magnitude: np.ndarray) -> float:
    """
    Calibrated: most real photos have a steep DC-to-Nyquist falloff too.
    Only flag truly anomalous profiles (AI has EXTRA steep falloff past mid-band).
    Clamped to 0.0–0.50.
    """
    h, w   = magnitude.shape
    cy, cx = h // 2, w // 2
    y_idx, x_idx = np.ogrid[:h, :w]
    dist   = np.sqrt((y_idx - cy)**2 + (x_idx - cx)**2)
    max_r  = min(cy, cx)

    rings = 5
    ring_means = []
    for i in range(rings):
        r0, r1 = (i / rings) * max_r, ((i+1) / rings) * max_r
        mask = (dist >= r0) & (dist < r1)
        if mask.sum() > 0:
            ring_means.append(float(magnitude[mask].mean()))

    if len(ring_means) < 2:
        return 0.0

    rm = np.array(ring_means) / (ring_means[0] + 1e-9)
    total_drop = rm[0] - rm[-1]

    # Raised baseline: real photos drop ~0.80–0.95 (wider range than before)
    # Only score when drop > 0.90 (unusually steep)
    raw = max(0.0, (total_drop - 0.90) / 0.10)
    return float(round(min(0.50, raw * 0.50), 4))


def _quadrant_asymmetry_score(magnitude: np.ndarray) -> float:
    """
    Clamped to 0.0–0.50. Real photos shot handheld or with vignetting
    already show noticeable quadrant asymmetry — raised CV threshold.
    """
    h, w   = magnitude.shape
    cy, cx = h // 2, w // 2
    q = np.array([
        magnitude[:cy, :cx].mean(),
        magnitude[:cy, cx:].mean(),
        magnitude[cy:, :cx].mean(),
        magnitude[cy:, cx:].mean(),
    ])
    cv = q.std() / (q.mean() + 1e-9)
    # Raised threshold: CV > 0.15 (was 0.20) before any score
    raw = max(0.0, (cv - 0.15) / 0.20)
    return float(round(min(0.50, raw * 0.50), 4))


def _periodic_peak_score(magnitude: np.ndarray) -> float:
    """
    GAN upsampling leaves strong periodic peaks in mid-band.
    Requires peak/mean > 6 (raised from 3+5 before scoring).
    Clamped to 0.0–0.50.
    """
    h, w   = magnitude.shape
    cy, cx = h // 2, w // 2
    y_idx, x_idx = np.ogrid[:h, :w]
    dist   = np.sqrt((y_idx - cy)**2 + (x_idx - cx)**2)
    r_min  = 0.10 * min(cy, cx)
    r_max  = 0.40 * min(cy, cx)
    mid    = magnitude[(dist >= r_min) & (dist <= r_max)]

    if len(mid) < 50:
        return 0.0

    band_mean = mid.mean()
    band_std  = mid.std()
    if band_std < 1e-6 or band_mean < 1e-6:
        return 0.0

    peak = mid.max()
    peak_ratio = peak / band_mean

    # Need peak/mean > 6 (real photos can hit 3–5 due to lens diffraction rings)
    raw = max(0.0, (peak_ratio - 6.0) / 4.0)
    return float(round(min(0.50, raw * 0.50), 4))


def _hf_noise_floor_score(magnitude: np.ndarray) -> float:
    """
    Real cameras vary widely in HF noise (ISO, sensor size, lens).
    Only flag extremely clean HF (real portrait cameras can be clean too).
    Raised threshold, clamped to 0.0–0.50.
    """
    h, w   = magnitude.shape
    cy, cx = h // 2, w // 2
    y_idx, x_idx = np.ogrid[:h, :w]
    dist   = np.sqrt((y_idx - cy)**2 + (x_idx - cx)**2)
    max_r  = min(cy, cx)

    hf_mask  = dist > 0.70 * max_r
    low_mask = dist < 0.30 * max_r
    if hf_mask.sum() == 0 or low_mask.sum() == 0:
        return 0.0

    ratio = float(magnitude[hf_mask].mean()) / (float(magnitude[low_mask].mean()) + 1e-9)

    # Real low-ISO / mirrorless photos can have ratio ~0.08–0.15 (clean)
    # Only flag ratio < 0.05 (extremely clean = likely AI)
    raw = max(0.0, (0.05 - ratio) / 0.05)
    return float(round(min(0.50, raw * 0.50), 4))


# ── Main run ───────────────────────────────────────────────────────────────

def run(image_bytes: bytes) -> dict:
    try:
        img  = Image.open(io.BytesIO(image_bytes)).convert("L").resize((256, 256), Image.Resampling.LANCZOS)
        gray = np.array(img, dtype=np.float32)
        mag  = _fft_magnitude(gray)

        falloff    = _radial_falloff_score(mag)
        asymmetry  = _quadrant_asymmetry_score(mag)
        peaks      = _periodic_peak_score(mag)
        hf_clean   = _hf_noise_floor_score(mag)

        logger.debug(f"FFT — falloff:{falloff:.3f} asym:{asymmetry:.3f} peaks:{peaks:.3f} hf:{hf_clean:.3f}")

        # Weighted combination — all inputs already clamped to 0–0.50
        frequency_score = (
            falloff   * 0.35 +
            asymmetry * 0.15 +
            peaks     * 0.25 +
            hf_clean  * 0.25
        )
        # Hard cap at 0.50 — frequency alone never pushes to AI verdict
        frequency_score = round(min(0.50, frequency_score), 4)

        flags = []
        if peaks > 0.30:
            flags.append(f"GAN frequency: periodic mid-band peaks ({peaks:.2f}) — upsampling artifact")
        if falloff > 0.30:
            flags.append(f"GAN frequency: abnormal spectral falloff ({falloff:.2f})")
        if hf_clean > 0.30:
            flags.append(f"GAN frequency: suspiciously clean HF noise floor ({hf_clean:.2f})")
        if asymmetry > 0.30:
            flags.append(f"GAN frequency: quadrant asymmetry ({asymmetry:.2f})")
        if not flags:
            flags.append(f"Frequency spectrum natural (score: {frequency_score:.2f})")

        return {
            "frequency_score": frequency_score,
            "signals": {
                "radial_falloff":     falloff,
                "quadrant_asymmetry": asymmetry,
                "periodic_peaks":     peaks,
                "hf_noise_clean":     hf_clean,
            },
            "flags":     flags[:3],
            "available": True,
        }

    except Exception as exc:
        logger.error(f"Frequency analysis error: {exc}")
        return {
            "frequency_score": 0.0,
            "signals": {},
            "flags": [f"Frequency analysis error: {str(exc)[:80]}"],
            "available": False,
        }
