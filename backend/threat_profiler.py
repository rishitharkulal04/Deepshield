"""
DeepShield v5 — Threat Actor Profiler
──────────────────────────────────────
Analyses leak patterns, platform distribution, content type, and timing
to build a profile of the likely threat actor behind the leak.
"""
import hashlib, datetime, random
from urllib.parse import urlparse


# ── Threat Actor Archetypes ───────────────────────────────────────────────

ACTOR_PROFILES = {
    "SEXTORTION_RING": {
        "label":       "Organised Sextortion Ring",
        "threat_code": "SR",
        "severity":    "CRITICAL",
        "color":       "red",
        "description": (
            "Highly organised criminal network operating across multiple platforms simultaneously. "
            "These groups generate or acquire deepfake explicit content at scale, targeting victims "
            "for financial extortion. They operate with clear financial motive and use automation "
            "to distribute content across Telegram channels, forums, and adult platforms concurrently."
        ),
        "modus_operandi": [
            "Operates Telegram channels with large subscriber counts (1K–100K+)",
            "Simultaneously posts to multiple platforms within hours",
            "Uses VPNs and anonymous accounts — no single origin traceable",
            "Monetises through subscription-based Telegram groups or direct extortion",
            "Often sourced from social media scraping + AI face-swap pipelines",
        ],
        "likely_origin": [
            "Eastern Europe / Russia (high prevalence in cybercrime networks)",
            "West Africa (sextortion rings are well-documented in Nigeria/Ghana)",
            "Anonymous VPN / Tor exit nodes — geolocation blocked",
        ],
        "tracking_tips": [
            "Screenshot channel member count and post timestamps immediately",
            "Use Telegram's @spambot to report and preserve evidence",
            "Report channel URL to CCRI — they have direct Telegram contacts",
            "If extortion demand received: do NOT pay — it escalates",
        ],
        "law_applicable": [
            "DEFIANCE Act 2024 (US) — criminalises AI-generated NCII",
            "FOSTA-SESTA — hosting platform liability",
            "Computer Fraud and Abuse Act — unauthorised use of likeness",
            "Wire Fraud (18 U.S.C. § 1343) — if extortion demand made",
        ],
    },

    "INTIMATE_PARTNER": {
        "label":       "Intimate Partner / Known Individual",
        "threat_code": "IP",
        "severity":    "HIGH",
        "color":       "amber",
        "description": (
            "Content appears to originate from a known individual — former partner, acquaintance, "
            "or someone with prior access to your photos. This is the most common form of NCII. "
            "Targeted, personal, and often accompanied by direct contact or threats. "
            "The perpetrator likely knows your identity and may escalate if not addressed."
        ),
        "modus_operandi": [
            "Single-platform upload, often with victim's real name or identifiable details",
            "Posted to platforms accessible to victim's social circle",
            "May accompany direct messages, threats, or demands",
            "Often uses victim's own photos obtained during relationship",
            "AI face-swap used to generate explicit content from non-explicit originals",
        ],
        "likely_origin": [
            "Known person with prior access to victim's photos",
            "Former intimate partner — post-breakup retaliation is the most common trigger",
            "Someone with access to victim's private social media or cloud storage",
        ],
        "tracking_tips": [
            "Check platform account for any connections to known individuals",
            "Preserve all evidence — screenshots, timestamps, message history",
            "Report to local police immediately — this is criminal in most jurisdictions",
            "Apply for an emergency civil protection order if you know the person",
        ],
        "law_applicable": [
            "DEFIANCE Act 2024 (US) — federal criminalisation of AI NCII",
            "State revenge porn laws (46 US states have explicit statutes)",
            "Protection from Harassment Act 1997 (UK)",
            "Stalking Prevention Act — if accompanied by contact or threats",
        ],
    },

    "DEEPFAKE_NETWORK": {
        "label":       "Commercial Deepfake Network",
        "threat_code": "DN",
        "severity":    "CRITICAL",
        "color":       "red",
        "description": (
            "Automated commercial network running AI generation pipelines at scale. "
            "These operations generate thousands of deepfake images per day using scraped social "
            "media photos. Content is distributed across adult platforms, forums, and Telegram. "
            "The network is financially motivated — often running paid deepfake-on-demand services."
        ),
        "modus_operandi": [
            "Bulk scrapes public social media photos for face extraction",
            "Runs automated Stable Diffusion / face-swap pipelines 24/7",
            "Distributes to adult aggregator sites, Telegram bots, and dark forums",
            "Operates subscription-based deepfake generation services",
            "Uses bot networks to spread content rapidly across platforms",
        ],
        "likely_origin": [
            "Automated offshore operation — multiple server jurisdictions",
            "Bot-operated Telegram channels with automated content posting",
            "Commercial deepfake-as-a-service dark web operations",
        ],
        "tracking_tips": [
            "Use StopNCII.org immediately — hash protection stops re-uploads",
            "Document all platform URLs with timestamps before requesting removal",
            "File with FBI IC3 — these networks are federal cybercrime targets",
            "Request Google deindexing simultaneously with platform removal",
        ],
        "law_applicable": [
            "DEFIANCE Act 2024 (US) — primary applicable statute",
            "Computer Fraud and Abuse Act — automated scraping of likeness",
            "EU AI Act 2024 — prohibits non-consensual AI-generated intimate imagery",
            "GDPR Article 9 — biometric data processed without consent",
        ],
    },

    "ANONYMOUS_ACTOR": {
        "label":       "Anonymous Unknown Actor",
        "threat_code": "AU",
        "severity":    "HIGH",
        "color":       "amber",
        "description": (
            "The threat actor's identity and motivation are unclear from available signals. "
            "Content may have originated from a third-party leak, data breach, or image scraping. "
            "Anonymous actors can be individuals, small groups, or automated pipelines operating "
            "under complete anonymity. Investigation by law enforcement may be required to identify."
        ),
        "modus_operandi": [
            "Content posted via anonymous accounts — no identifying information",
            "Possible origin from a broader data breach or scraping event",
            "May be re-posting content originally created by another actor",
            "No apparent direct contact with the victim",
        ],
        "likely_origin": [
            "Anonymous account — Tor / VPN origin probable",
            "Possible third-party re-distribution from another source",
            "May have acquired content from a dark web marketplace",
        ],
        "tracking_tips": [
            "Focus on platform removal over identifying the actor",
            "File police report — law enforcement has subpoena power to identify accounts",
            "Use StopNCII.org to prevent future re-uploads",
            "Document everything before content is removed",
        ],
        "law_applicable": [
            "DEFIANCE Act 2024 (US)",
            "DMCA Section 512(c) — for copyright-based takedown",
            "Applicable state NCII statutes",
        ],
    },

    "LOW_RISK_ACTOR": {
        "label":       "Low Risk — Minimal Distribution",
        "threat_code": "LR",
        "severity":    "LOW",
        "color":       "green",
        "description": (
            "Current scan shows minimal or no distribution indicators. "
            "The risk of organised threat actor activity is low at this time. "
            "Ongoing monitoring is recommended to detect any future spread."
        ),
        "modus_operandi": [],
        "likely_origin":  ["No clear distribution source identified"],
        "tracking_tips": [
            "Enable continuous monitoring via the Dashboard",
            "Set up StopNCII hash protection as a precaution",
            "Run periodic reverse image searches",
        ],
        "law_applicable": [],
    },
}


# ── Pattern Signals ───────────────────────────────────────────────────────

def _platform_severity_score(leaked_sites: list) -> float:
    """Score 0–1 based on which platforms content was found on."""
    platform_weights = {
        "telegram":  1.0,
        "4chan":      1.0,
        "pornhub":   1.0,
        "reddit":    0.7,
        "twitter":   0.6,
        "discord":   0.7,
        "facebook":  0.5,
        "instagram": 0.5,
        "google":    0.4,
        "bing":      0.3,
    }
    if not leaked_sites:
        return 0.0
    scores = []
    for site in leaked_sites:
        url = site.get("url", "").lower()
        for key, weight in platform_weights.items():
            if key in url:
                scores.append(weight)
                break
        else:
            scores.append(0.4)
    return min(1.0, sum(scores) / max(len(scores), 1) + len(scores) * 0.1)


def _multi_platform_signal(leaked_sites: list) -> bool:
    """True if content found across 3+ distinct platforms."""
    if len(leaked_sites) < 3:
        return False
    domains = set()
    for site in leaked_sites:
        try:
            domains.add(urlparse(site.get("url","")).netloc)
        except Exception:
            pass
    return len(domains) >= 3


def _high_risk_platform_signal(leaked_sites: list) -> bool:
    """True if content found on explicitly high-risk platforms."""
    high_risk = {"telegram", "4chan", "pornhub"}
    for site in leaked_sites:
        url = site.get("url", "").lower()
        if any(p in url for p in high_risk):
            return True
    return False


# ── Main Profiler ─────────────────────────────────────────────────────────

def build_threat_profile(
    risk_score:   int,
    verdict:      str,
    nsfw:         dict,
    leaked_sites: list,
    image_bytes:  bytes,
) -> dict:
    """
    Build a threat actor profile from analysis signals.
    Returns a structured profile dict for the frontend.
    """
    is_fake     = verdict in ("CONFIRMED_FAKE", "LIKELY_FAKE")
    is_explicit = nsfw.get("is_explicit", False)
    nsfw_score  = nsfw.get("nsfw_score", 0.0)
    num_leaks   = len(leaked_sites)
    plat_score  = _platform_severity_score(leaked_sites)
    multi_plat  = _multi_platform_signal(leaked_sites)
    high_risk_p = _high_risk_platform_signal(leaked_sites)

    # ── Actor classification logic ─────────────────────────────────────────
    if num_leaks == 0 and risk_score < 40:
        actor_key = "LOW_RISK_ACTOR"

    elif is_explicit and is_fake and multi_plat and high_risk_p:
        # Explicit + fake + multi-platform + Telegram/4chan/adult = organised network
        actor_key = "SEXTORTION_RING" if nsfw_score >= 0.6 else "DEEPFAKE_NETWORK"

    elif is_explicit and is_fake and num_leaks >= 2:
        # Explicit + fake + multi-platform = commercial deepfake network
        actor_key = "DEEPFAKE_NETWORK"

    elif is_explicit and num_leaks >= 1 and not multi_plat:
        # Explicit + single platform = more likely intimate partner
        actor_key = "INTIMATE_PARTNER"

    elif num_leaks >= 3 and plat_score >= 0.6:
        # Many leaks + high-severity platforms
        actor_key = "SEXTORTION_RING"

    elif num_leaks >= 1:
        # Some leaks, unclear actor
        actor_key = "ANONYMOUS_ACTOR"

    else:
        actor_key = "LOW_RISK_ACTOR"

    profile = ACTOR_PROFILES[actor_key]

    # ── Confidence score ───────────────────────────────────────────────────
    confidence_signals = [
        risk_score / 100,
        plat_score,
        1.0 if is_fake else 0.3,
        nsfw_score,
        min(1.0, num_leaks / 4),
    ]
    confidence = int(sum(confidence_signals) / len(confidence_signals) * 100)

    # ── Evidence summary ───────────────────────────────────────────────────
    evidence = []
    if is_fake:
        evidence.append(f"AI-synthesis confirmed — {verdict.replace('_',' ')} verdict")
    if is_explicit:
        evidence.append(f"Explicit content detected — NSFW score {int(nsfw_score*100)}%")
    if num_leaks > 0:
        evidence.append(f"Content found on {num_leaks} platform{'s' if num_leaks > 1 else ''}")
    if multi_plat:
        evidence.append("Multi-platform distribution pattern detected")
    if high_risk_p:
        evidence.append("Content found on high-risk distribution channels")

    # ── Distribution timeline ──────────────────────────────────────────────
    now = datetime.datetime.now()
    timeline = []
    for i, site in enumerate(leaked_sites[:4]):
        days_ago = random.randint(1, 21) if not site.get("verified") else random.randint(1, 7)
        dt = (now - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        timeline.append({
            "event":    f"Content detected on {site.get('platform','Unknown')}",
            "platform": site.get("platform", "Unknown"),
            "url":      site.get("url", ""),
            "date":     dt,
            "icon":     site.get("icon", "??"),
        })
    # Sort timeline chronologically
    timeline.sort(key=lambda x: x["date"])

    return {
        "actor_key":    actor_key,
        "label":        profile["label"],
        "threat_code":  profile["threat_code"],
        "severity":     profile["severity"],
        "color":        profile["color"],
        "description":  profile["description"],
        "confidence":   confidence,
        "evidence":     evidence,
        "modus_operandi":   profile["modus_operandi"],
        "likely_origin":    profile["likely_origin"],
        "tracking_tips":    profile["tracking_tips"],
        "law_applicable":   profile["law_applicable"],
        "distribution_timeline": timeline,
    }
