"""
DeepShield v6 — Safety-Aware Link Handler
═════════════════════════════════════════════
Safely handles potentially unsafe or explicit content links:
  • Sanitizes URLs
  • Adds warnings for sensitive content
  • Provides safe preview links where possible
  • Masks direct links to sensitive platforms
  • Logs access for audit trails
"""

import logging
from typing import Dict, List
from urllib.parse import urlparse, quote
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Platform Classification ────────────────────────────────────────────────
PLATFORM_RISK_LEVELS = {
    "pornhub.com": "CRITICAL",
    "xhamster.com": "CRITICAL",
    "xvideos.com": "CRITICAL",
    "reddit.com": "MEDIUM",
    "telegram.org": "MEDIUM",
    "4chan.org": "HIGH",
    "8kun.top": "CRITICAL",
    "twitter.com": "LOW",
    "facebook.com": "LOW",
    "instagram.com": "LOW",
}

SENSITIVE_KEYWORDS = [
    "porn", "nude", "nsfw", "xxx", "adult", "explicit",
    "sex", "deepfake", "fake", "nonconsensual"
]


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except:
        return "unknown"


def _get_platform_risk_level(url: str) -> str:
    """Determine risk level of platform from URL."""
    domain = _extract_domain(url)
    
    # Check if exact match
    if domain in PLATFORM_RISK_LEVELS:
        return PLATFORM_RISK_LEVELS[domain]
    
    # Check if partial match
    for known_domain, risk in PLATFORM_RISK_LEVELS.items():
        if known_domain in url:
            return risk
    
    return "UNKNOWN"


def _contains_sensitive_keywords(url: str, title: str = "") -> bool:
    """Check if URL or title contains sensitive keywords."""
    combined = f"{url} {title}".lower()
    return any(keyword in combined for keyword in SENSITIVE_KEYWORDS)


def _create_safe_preview_link(url: str) -> str:
    """
    Create a safe preview link that doesn't directly expose the URL.
    Returns a hash-based identifier that can be logged without exposing content.
    """
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
    return f"preview://{url_hash}"


def _mask_sensitive_url(url: str) -> str:
    """Replace sensitive URL with masked version for logging."""
    domain = _extract_domain(url)
    return f"[MASKED: {domain}]"


def sanitize_link(
    url: str,
    source_domain: str = "",
    title: str = "",
    is_explicit: bool = False,
    match_confidence: float = 0.0
) -> Dict:
    """
    Sanitize a potentially unsafe link with context warnings.
    
    Args:
        url: The URL to sanitize
        source_domain: Domain where link was found
        title: Optional title/description
        is_explicit: Whether content is explicit
        match_confidence: Confidence score (0-100)
    
    Returns:
        {
            "sanitized": true/false,
            "safe_to_display": true/false,
            "original_domain": "example.com",
            "preview_link": "preview://hash",
            "masked_url": "[MASKED: example.com]",
            "sensitive_content": true/false,
            "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|UNKNOWN",
            "warning_message": "...",
            "recommendations": ["action1", "action2"],
            "access_log_entry": {
                "timestamp": "ISO-8601",
                "domain": "example.com",
                "risk_level": "CRITICAL",
                "action": "blocked|warned|allowed"
            }
        }
    """
    try:
        risk_level = _get_platform_risk_level(url)
        has_sensitive_keywords = _contains_sensitive_keywords(url, title)
        is_sensitive = is_explicit or has_sensitive_keywords
        
        # Determine if safe to display
        safe_to_display = risk_level not in ["CRITICAL", "HIGH"]
        
        # Generate warnings
        warnings = []
        recommendations = []
        
        if is_sensitive:
            warnings.append("⚠️ Content flagged as sensitive or explicit")
            recommendations.append("Verify user consent before accessing")
            recommendations.append("Use VPN/privacy protection")
            recommendations.append("Consider platform reporting instead")
        
        if risk_level == "CRITICAL":
            warnings.append("🚨 CRITICAL: Platform hosts harmful content")
            safe_to_display = False
            recommendations.append("DO NOT click directly - use platform report buttons instead")
            recommendations.append("Contact platform abuse team via official channels")
        elif risk_level == "HIGH":
            warnings.append("⚠️ HIGH RISK: Platform known for unsafe content")
            recommendations.append("Use caution before accessing")
        
        if match_confidence < 70:
            warnings.append(f"Low confidence match ({match_confidence}%) - may be unrelated")
        
        domain = _extract_domain(url)
        
        action = "blocked" if not safe_to_display else ("warned" if is_sensitive else "allowed")
        
        return {
            "sanitized": True,
            "safe_to_display": safe_to_display,
            "original_domain": domain,
            "source_domain": source_domain,
            "preview_link": _create_safe_preview_link(url),
            "masked_url": _mask_sensitive_url(url),
            "sensitive_content": is_sensitive,
            "risk_level": risk_level,
            "warning_message": " | ".join(warnings) if warnings else "No warnings",
            "recommendations": recommendations,
            "match_confidence": match_confidence,
            "access_log_entry": {
                "domain": domain,
                "risk_level": risk_level,
                "is_sensitive": is_sensitive,
                "action": action,
                "match_confidence": match_confidence
            }
        }
    
    except Exception as e:
        logger.error(f"Link sanitization error: {e}")
        return {
            "sanitized": False,
            "safe_to_display": False,
            "error": str(e),
            "recommendations": ["Report this error to platform"]
        }


def create_safe_report_context(
    url: str,
    platform: str,
    threat_level: str = "MEDIUM"
) -> Dict:
    """
    Create a safe context for reporting without exposing content.
    Returns information needed to report without viewing.
    """
    domain = _extract_domain(url)
    
    return {
        "report_context": {
            "platform": platform,
            "domain": domain,
            "threat_level": threat_level,
            "url_hash": hashlib.sha256(url.encode()).hexdigest(),
            "can_view_directly": threat_level not in ["CRITICAL", "HIGH"],
            "should_report_instead": threat_level in ["CRITICAL", "HIGH"]
        },
        "safe_actions": [
            "Use platform's built-in report button (no content viewing needed)",
            "Contact platform abuse team via official email",
            "File DMCA takedown through proper channels",
            "Report to NCMEC/relevant authorities without viewing content"
        ],
        "never_do": [
            "Don't screenshot or save content",
            "Don't forward to unverified recipients",
            "Don't click suspicious links",
            "Don't engage with poster/platform account"
        ]
    }


def batch_sanitize_links(
    links: List[Dict],
    include_sensitive: bool = False
) -> Dict:
    """
    Sanitize multiple links in batch.
    
    Args:
        links: List of {"url": "...", "source": "...", "title": "...", "is_explicit": bool, "confidence": float}
        include_sensitive: Whether to include sensitive links in results
    
    Returns:
        {
            "total_links": N,
            "safe_links": [...],
            "unsafe_links": [...],
            "sensitive_links": [...],
            "recommendations": ["action1", "action2"]
        }
    """
    try:
        safe_links = []
        unsafe_links = []
        sensitive_links = []
        overall_recommendations = set()
        
        for link_info in links:
            url = link_info.get("url", "")
            if not url:
                continue
            
            sanitized = sanitize_link(
                url,
                source_domain=link_info.get("source", ""),
                title=link_info.get("title", ""),
                is_explicit=link_info.get("is_explicit", False),
                match_confidence=link_info.get("confidence", 0.0)
            )
            
            # Categorize
            if sanitized.get("sensitive_content"):
                if include_sensitive:
                    sensitive_links.append(sanitized)
            elif not sanitized.get("safe_to_display"):
                unsafe_links.append(sanitized)
            else:
                safe_links.append(sanitized)
            
            # Collect recommendations
            for rec in sanitized.get("recommendations", []):
                overall_recommendations.add(rec)
        
        return {
            "total_links": len(links),
            "safe_links_count": len(safe_links),
            "unsafe_links_count": len(unsafe_links),
            "sensitive_links_count": len(sensitive_links),
            "safe_links": safe_links,
            "unsafe_links": unsafe_links,
            "sensitive_links": sensitive_links,
            "recommendations": list(overall_recommendations),
            "summary": f"{len(safe_links)} safe | {len(unsafe_links)} unsafe | {len(sensitive_links)} sensitive"
        }
    
    except Exception as e:
        logger.error(f"Batch link sanitization error: {e}")
        return {
            "error": str(e),
            "recommendations": ["Report this error to platform"]
        }
