"""
DeepShield — Forensic Artifact Detection Module (v8 — Enhanced)
================================================================
Purely algorithmic signals — catches what neural nets miss.

Signals:
  1. ELA   (Error Level Analysis)         — AI images have unnaturally flat ELA
  2. Noise uniformity                     — AI lacks natural sensor noise variation
  3. DCT spectral analysis               — AI images have characteristic frequency peaks
  4. Texture regularity (LBP-like)       — AI textures are unnaturally repeating
  5. Metadata analysis                   — missing EXIF, AI-standard dimensions
  6. Color distribution                  — AI images are suspiciously smooth/saturated
  7. Edge coherence                      — AI edges are too perfect / sharp
  8. Chroma noise                        — AI has unnatural chroma channel distribution
"""

import io, logging
import numpy as np
from PIL import Image, ImageFilter, ImageChops

logger = logging.getLogger(__name__)

# Standard AI model output sizes (SDXL, SD 1.5, Midjourney, DALL-E, Gemini, Firefly)
_AI_DIMENSIONS = {
    (512, 512), (512, 768), (768, 512), (768, 768),
    (768, 1024), (1024, 768), (1024, 1024),
    (1024, 1536), (1536, 1024), (832, 1216), (1216, 832),
    (896, 1152), (1152, 896), (1344, 768), (768, 1344),
    (1024, 576), (576, 1024),
}


def _ela_score(img: Image.Image) -> float:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    buf.seek(0)
    compressed = Image.open(buf).convert("RGB")
    diff = ImageChops.difference(img.convert("RGB"), compressed)
    arr  = np.array(diff).astype(np.float32)
    std  = arr.std()
    score = max(0.0, 1.0 - min(std / 8.0, 1.0))
    return float(round(score, 4))


def _noise_uniformity_score(img: Image.Image) -> float:
    gray = np.array(img.convert("L"), dtype=np.float32)
    h, w = gray.shape
    ps = max(16, min(32, h // 8, w // 8))
    noise_levels = []
    for i in range(0, h - ps, ps):
        for j in range(0, w - ps, ps):
            patch   = gray[i:i+ps, j:j+ps]
            blurred = np.array(
                Image.fromarray(patch.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1)),
                dtype=np.float32
            )
            noise_levels.append(float(np.std(patch - blurred)))
    if len(noise_levels) < 4:
        return 0.0
    mean_noise = np.mean(noise_levels)
    cv = np.std(noise_levels) / (mean_noise + 1e-6)
    return float(round(max(0.0, 1.0 - min(cv / 0.5, 1.0)), 4))


def _dct_spectral_score(img: Image.Image) -> float:
    try:
        gray = np.array(img.convert("L").resize((256, 256)), dtype=np.float32)
        fft       = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.log1p(np.abs(fft_shift))
        h, w  = magnitude.shape
        cy, cx = h // 2, w // 2
        y_idx, x_idx = np.ogrid[:h, :w]
        dist = np.sqrt((y_idx - cy)**2 + (x_idx - cx)**2)
        low_mask  = dist < 20
        mid_mask  = (dist >= 20) & (dist < 60)
        high_mask = dist >= 60
        low_e  = float(magnitude[low_mask].mean())
        mid_e  = float(magnitude[mid_mask].mean())
        high_e = float(magnitude[high_mask].mean())
        if mid_e < 1e-6:
            return 0.0
        falloff = (low_e - high_e) / (mid_e + 1e-6)
        return float(round(max(0.0, min(1.0, (falloff - 2.0) / 6.0)), 4))
    except Exception:
        return 0.0


def _texture_regularity_score(img: Image.Image) -> float:
    try:
        gray = np.array(img.convert("L").resize((128, 128)), dtype=np.float32)
        offsets  = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        patterns = []
        for dy, dx in offsets:
            shifted = np.roll(np.roll(gray, dy, axis=0), dx, axis=1)
            patterns.append((gray - shifted).flatten())
        patterns = np.array(patterns)
        variance_per_pixel = np.var(patterns, axis=0)
        mean_var = float(np.mean(variance_per_pixel))
        return float(round(max(0.0, 1.0 - min(mean_var / 150.0, 1.0)), 4))
    except Exception:
        return 0.0


def _edge_coherence_score(img: Image.Image) -> float:
    """
    AI images tend to have unnaturally sharp / over-coherent edges.
    Real photos have edge variation from camera shake, noise, focus.
    """
    try:
        gray  = np.array(img.convert("L").resize((256, 256)), dtype=np.float32)
        sobel_x = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=np.float32)
        sobel_y = sobel_x.T
        from scipy.ndimage import convolve
        gx = convolve(gray, sobel_x)
        gy = convolve(gray, sobel_y)
        mag = np.sqrt(gx**2 + gy**2)
        # Ratio of very high-gradient pixels (super-sharp AI edges)
        edge_ratio = float(np.mean(mag > mag.mean() * 3.0))
        # Very high edge_ratio → AI-generated (too crisp)
        return float(round(min(1.0, edge_ratio * 4.0), 4))
    except Exception:
        return 0.0


def _chroma_noise_score(img: Image.Image) -> float:
    """
    Real photos have chroma noise from sensor; AI images have suspiciously clean chroma.
    """
    try:
        arr = np.array(img.convert("RGB").resize((128, 128)), dtype=np.float32)
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        rg_diff = np.std(r - g)
        rb_diff = np.std(r - b)
        # Real sensors: chroma channel differences are noisy (high std)
        # AI images: channels are harmonised → low std
        avg_chroma_noise = (rg_diff + rb_diff) / 2.0
        score = max(0.0, 1.0 - min(avg_chroma_noise / 12.0, 1.0))
        return float(round(score, 4))
    except Exception:
        return 0.0


def _metadata_score(img: Image.Image) -> tuple:
    score  = 0.0
    flags  = []
    has_exif = False
    try:
        exif = img._getexif()
        if exif and len(exif) > 2:
            has_exif = True
    except Exception:
        pass

    if not has_exif:
        # Many real images (WhatsApp, screenshots, web images) have no EXIF —
        # this alone is a very weak signal. Score 0.05, not suspicious.
        flags.append("No EXIF metadata — stripped or AI-generated image")
        score += 0.05   # was 0.25 — reduced to avoid false positives

    w, h = img.size
    if (w, h) in _AI_DIMENSIONS:
        flags.append(f"Resolution {w}×{h} is a standard AI model output size")
        score += 0.40
    elif w % 64 == 0 and h % 64 == 0 and has_exif is False:
        # Only penalise 64-grid dimensions when EXIF is also missing
        # (real cameras export 64-aligned JPEGs from some apps — not rare)
        flags.append(f"Dimensions {w}×{h} multiples of 64 — possible AI latent grid")
        score += 0.10   # was 0.20

    return round(min(1.0, score), 4), flags



def _color_smoothness_score(img: Image.Image) -> float:
    try:
        arr  = np.array(img.convert("RGB").resize((128, 128)), dtype=np.float32)
        diff_h = np.diff(arr, axis=1)
        diff_v = np.diff(arr, axis=0)
        roughness = float(np.mean(np.abs(diff_h)) + np.mean(np.abs(diff_v))) / 2
        return float(round(max(0.0, 1.0 - min(roughness / 10.0, 1.0)), 4))
    except Exception:
        return 0.0


def run(image_bytes: bytes) -> dict:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        ela      = _ela_score(img)
        noise    = _noise_uniformity_score(img)
        dct      = _dct_spectral_score(img)
        texture  = _texture_regularity_score(img)
        color    = _color_smoothness_score(img)
        edge     = _edge_coherence_score(img)
        chroma   = _chroma_noise_score(img)
        meta_score, meta_flags = _metadata_score(img)

        # Weighted aggregate — v8: added edge + chroma signals
        artifact_prob = (
            ela        * 0.22 +
            noise      * 0.18 +
            dct        * 0.18 +
            texture    * 0.12 +
            color      * 0.08 +
            edge       * 0.10 +
            chroma     * 0.08 +
            meta_score * 0.04
        )
        artifact_prob = round(min(1.0, artifact_prob), 4)

        flags = list(meta_flags)
        if ela > 0.65:
            flags.append(f"ELA: abnormally flat error level ({ela:.2f}) — AI synthesis signature")
        elif ela > 0.45:
            flags.append(f"ELA: low error level variation ({ela:.2f}) — possible AI generation")
        if noise > 0.65:
            flags.append(f"Noise: unnaturally uniform ({noise:.2f}) — AI image signature")
        elif noise > 0.45:
            flags.append(f"Noise: slightly low variance ({noise:.2f}) — inconclusive")
        if dct > 0.55:
            flags.append(f"DCT spectrum: AI frequency falloff detected ({dct:.2f})")
        if texture > 0.60:
            flags.append(f"Texture: unnaturally repeating patterns ({texture:.2f})")
        if edge > 0.55:
            flags.append(f"Edge coherence: suspiciously perfect edges ({edge:.2f}) — AI render signature")
        if chroma > 0.55:
            flags.append(f"Chroma: unnaturally clean colour channels ({chroma:.2f}) — no sensor noise")
        if color > 0.55:
            flags.append(f"Colour smoothness: unnaturally smooth gradients ({color:.2f})")
        if not flags:
            flags.append("No significant forensic artifacts detected")

        return {
            "artifact_prob": artifact_prob,
            "signals": {
                "ela": ela, "noise_uniformity": noise,
                "dct_spectral": dct, "texture_regularity": texture,
                "color_smoothness": color, "edge_coherence": edge,
                "chroma_noise": chroma, "metadata": meta_score,
            },
            "flags": flags[:7],
            "available": True,
        }

    except Exception as exc:
        logger.error(f"Artifact detection error: {exc}")
        return {
            "artifact_prob": 0.0, "signals": {},
            "flags": ["Artifact analysis unavailable"],
            "available": False, "error": str(exc),
        }
