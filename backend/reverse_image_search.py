"""
DeepShield v6 — Reverse Image Search (handled by web_scanner.py)
This module provides the interface; actual search is in web_scanner.scan_for_leaks
"""
import hashlib, logging
from typing import List, Dict

logger = logging.getLogger(__name__)

KNOWN_LEAK_HASHES = {}


def reverse_image_search(image_bytes: bytes, search_type: str = "comprehensive") -> Dict:
    """Wrapper — actual logic is in web_scanner.py scan_for_leaks"""
    from web_scanner import scan_for_leaks
    # Use a mid-range score to trigger search
    results = scan_for_leaks(image_bytes, 60)
    return {
        "matched_sources": [
            {"domain": s.get("url", "").split("/")[2] if "/" in s.get("url", "") else "unknown",
             "platform": s.get("platform", "unknown"),
             "url": s.get("url", ""),
             "match_confidence": 75.0,
             "threat_level": s.get("threat_level", "MEDIUM")}
            for s in results
        ],
        "total_matches": len(results),
        "search_completed": True,
        "search_type": search_type,
        "found_on_platforms": list(set(s.get("platform", "unknown") for s in results))
    }
