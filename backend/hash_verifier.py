"""
DeepShield — Perceptual Hash Verifier (OSINT-grade, zero-hallucination)
========================================================================
Verifies candidate URLs by:
  1. Downloading the page and extracting all <img> tags
  2. Downloading each candidate image
  3. Computing pHash + aHash + dHash of input vs candidate
  4. Only returning a match when ALL three hashes agree, OR when
     a single hash distance is ≤ STRICT threshold

Hash distance thresholds:
  HIGH confidence  : pHash ≤ 8  (near-identical — same image, minor resize/JPEG)
  (MEDIUM excluded — OSINT mode only returns HIGH)

Confidence is NEVER fabricated — if no downloaded image hashes within threshold,
the candidate URL is silently dropped and NOT returned to the caller.
"""

import io
import logging
import re
import time
from urllib.parse import urlparse, urljoin

import requests
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import imagehash
    _IMAGEHASH_AVAILABLE = True
    logger.info("imagehash available — perceptual hash verification enabled")
except ImportError:
    _IMAGEHASH_AVAILABLE = False
    logger.warning("imagehash not installed — hash verification disabled (pip install imagehash)")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept":     "image/webp,image/apng,image/*,*/*;q=0.8",
}

# ── Thresholds ─────────────────────────────────────────────────────────────
PHASH_HIGH_THRESHOLD  = 8    # almost identical (allows minor JPEG/resize artifacts)
AHASH_HIGH_THRESHOLD  = 8
DHASH_HIGH_THRESHOLD  = 8

# If ALL three hashes are within threshold → definite match
# If even ONE is ≤ 4 (extremely tight) → also accept as HIGH
VERY_TIGHT_THRESHOLD  = 4

# How many images to check per page
MAX_IMAGES_PER_PAGE   = 12
REQUEST_TIMEOUT        = 8   # seconds per image download
RATE_LIMIT_SLEEP       = 0.5 # seconds between image downloads


def _compute_hashes(img: Image.Image) -> dict:
    """Compute pHash, aHash, dHash for a PIL image."""
    img_rgb = img.convert("RGB").resize((256, 256), Image.Resampling.LANCZOS)
    return {
        "phash": imagehash.phash(img_rgb),
        "ahash": imagehash.average_hash(img_rgb),
        "dhash": imagehash.dhash(img_rgb),
    }


def _compare_hashes(h1: dict, h2: dict) -> dict:
    """Compute absolute distances between two hash dicts."""
    return {
        "phash_dist": int(h1["phash"] - h2["phash"]),
        "ahash_dist": int(h1["ahash"] - h2["ahash"]),
        "dhash_dist": int(h1["dhash"] - h2["dhash"]),
    }


def _is_high_confidence(distances: dict) -> bool:
    """
    Return True ONLY for HIGH-confidence matches.
    Rules:
      - All three within threshold → HIGH
      - Or any single distance ≤ VERY_TIGHT → HIGH
    ZERO TOLERANCE for fabrication: returns False otherwise.
    """
    p = distances["phash_dist"]
    a = distances["ahash_dist"]
    d = distances["dhash_dist"]

    if p <= VERY_TIGHT_THRESHOLD or a <= VERY_TIGHT_THRESHOLD or d <= VERY_TIGHT_THRESHOLD:
        return True

    return (
        p <= PHASH_HIGH_THRESHOLD and
        a <= AHASH_HIGH_THRESHOLD and
        d <= DHASH_HIGH_THRESHOLD
    )


def _extract_image_urls_from_page(page_url: str) -> list:
    """
    Download the page and extract direct image URLs from <img> tags,
    og:image meta, and JSON-LD thumbnails.
    """
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"

        img_urls = []

        # <img src=...>
        for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html):
            src = m.group(1)
            if src.startswith("http"):
                img_urls.append(src)
            elif src.startswith("/"):
                img_urls.append(base + src)

        # og:image or twitter:image meta
        for m in re.finditer(
            r'<meta[^>]+(?:og:image|twitter:image)[^>]+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        ):
            img_urls.append(m.group(1))

        # Also try the reverse: content= before property=
        for m in re.finditer(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:og:image|twitter:image)',
            html, re.IGNORECASE
        ):
            img_urls.append(m.group(1))

        # Filter: only image-like URLs
        img_urls = [
            u for u in img_urls
            if any(ext in u.lower() for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"))
            or "image" in u.lower()
        ]

        return list(dict.fromkeys(img_urls))[:MAX_IMAGES_PER_PAGE]

    except Exception as e:
        logger.debug(f"Page extraction failed for {page_url}: {e}")
        return []


def _download_image(url: str) -> Image.Image | None:
    """Download and decode an image. Returns None on any failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and not any(
            ext in url.lower() for ext in (".jpg", ".jpeg", ".png", ".webp")
        ):
            return None
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception:
        return None


def _platform_from_url(url: str) -> str:
    """Return a clean platform name from URL."""
    host = urlparse(url).netloc.lower().replace("www.", "")
    mapping = {
        "twitter.com":    "X (Twitter)",
        "x.com":          "X (Twitter)",
        "reddit.com":     "Reddit",
        "instagram.com":  "Instagram",
        "tiktok.com":     "TikTok",
        "facebook.com":   "Facebook",
        "t.me":           "Telegram",
        "telegram.org":   "Telegram",
        "4chan.org":       "4chan",
        "discord.com":    "Discord",
        "pornhub.com":    "Pornhub",
        "xvideos.com":    "XVideos",
        "xhamster.com":   "xHamster",
        "tumblr.com":     "Tumblr",
        "imgur.com":      "Imgur",
        "flickr.com":     "Flickr",
    }
    for domain, name in mapping.items():
        if domain in host:
            return name
    return host or "Unknown"


# ── Main OSINT verification function ─────────────────────────────────────

def verify_url(input_image_bytes: bytes, candidate_url: str) -> dict | None:
    """
    Verify whether the image at candidate_url is a match for input_image_bytes.

    Returns:
      dict with {platform, url, confidence, hash_distances} if HIGH match
      None if no match or verification failed

    ZERO FABRICATION: if the image cannot be downloaded or hashes don't match,
    returns None — never guesses.
    """
    if not _IMAGEHASH_AVAILABLE:
        logger.warning("imagehash not available — cannot verify URLs")
        return None

    try:
        input_img  = Image.open(io.BytesIO(input_image_bytes)).convert("RGB")
        input_hash = _compute_hashes(input_img)
    except Exception as e:
        logger.error(f"Failed to hash input image: {e}")
        return None

    logger.info(f"Verifying: {candidate_url}")

    # ── Strategy 1: Page scrape → extract images → hash compare ─────────
    page_img_urls = _extract_image_urls_from_page(candidate_url)
    logger.info(f"  Extracted {len(page_img_urls)} image URLs from page")

    for img_url in page_img_urls:
        time.sleep(RATE_LIMIT_SLEEP)
        candidate_img = _download_image(img_url)
        if candidate_img is None:
            continue

        try:
            cand_hash  = _compute_hashes(candidate_img)
            distances  = _compare_hashes(input_hash, cand_hash)

            logger.debug(
                f"  Hash dist — p:{distances['phash_dist']} "
                f"a:{distances['ahash_dist']} d:{distances['dhash_dist']} "
                f"← {img_url[:60]}"
            )

            if _is_high_confidence(distances):
                logger.info(f"  ✅ HIGH confidence match found: {img_url}")
                return {
                    "platform":       _platform_from_url(candidate_url),
                    "url":            candidate_url,
                    "image_url":      img_url,
                    "confidence":     "high",
                    "hash_distances": distances,
                    "verified":       True,
                }
        except Exception as he:
            logger.debug(f"  Hash error: {he}")
            continue

    # ── Strategy 2: Try the URL directly as an image ─────────────────────
    candidate_img = _download_image(candidate_url)
    if candidate_img is not None:
        try:
            cand_hash = _compute_hashes(candidate_img)
            distances = _compare_hashes(input_hash, cand_hash)
            if _is_high_confidence(distances):
                logger.info(f"  ✅ HIGH confidence direct image match: {candidate_url}")
                return {
                    "platform":       _platform_from_url(candidate_url),
                    "url":            candidate_url,
                    "image_url":      candidate_url,
                    "confidence":     "high",
                    "hash_distances": distances,
                    "verified":       True,
                }
        except Exception:
            pass

    logger.info(f"  ❌ No match found at: {candidate_url}")
    return None   # STRICT: no match → return nothing, never fabricate


def run_osint_verification(
    image_bytes: bytes,
    candidate_urls: list,
    max_to_check: int = 10,
) -> list:
    """
    Run hash-based OSINT verification against a list of candidate URLs.

    Returns ONLY high-confidence matches.
    If nothing verified → returns empty list (caller should return "No verified leaked content found.")

    ZERO HALLUCINATION: only entries returned from verify_url() with confirmed hash match.
    """
    results = []
    seen_urls = set()

    for url in candidate_urls[:max_to_check]:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        try:
            match = verify_url(image_bytes, url)
            if match:
                results.append(match)
        except Exception as e:
            logger.error(f"Verification error for {url}: {e}")
            continue

    return results


def compute_image_hashes(image_bytes: bytes) -> dict:
    """
    Compute perceptual hashes for the input image.
    Used for logging, DMCA evidence, and hash-based registry lookup (StopNCII).
    """
    if not _IMAGEHASH_AVAILABLE:
        return {"error": "imagehash not available"}
    try:
        img   = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        hashes = _compute_hashes(img)
        return {
            "phash": str(hashes["phash"]),
            "ahash": str(hashes["ahash"]),
            "dhash": str(hashes["dhash"]),
        }
    except Exception as e:
        return {"error": str(e)}
