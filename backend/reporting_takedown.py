"""
DeepShield v6 — Reporting & Takedown Coordinator
═════════════════════════════════════════════════
Provides comprehensive reporting and takedown actions:
  • Direct reporting URLs for each platform
  • DMCA takedown templates
  • Removal services and coordinators
  • Legal resources and support contacts
  • Automated action recommendations
"""

import logging
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Platform Reporting Registry ────────────────────────────────────────────
# Comprehensive database of reporting endpoints and removal tools

PLATFORM_REMOVAL_ACTIONS = {
    "telegram": {
        "name": "Telegram",
        "threat_level": "CRITICAL",
        "reporting": {
            "direct_report": {
                "label": "Report via @SpamBot",
                "url": "https://t.me/spambot",
                "method": "Direct message in Telegram",
                "time_to_remove": "24-72 hours",
                "effectiveness": "HIGH"
            },
            "abuse_email": {
                "label": "Email abuse@telegram.org",
                "url": "mailto:abuse@telegram.org",
                "method": "Email with channel/group link",
                "time_to_remove": "48-72 hours",
                "effectiveness": "HIGH"
            },
            "dmca_email": {
                "label": "DMCA notice to dmca@telegram.org",
                "url": "mailto:dmca@telegram.org",
                "method": "Formal DMCA takedown",
                "time_to_remove": "24-48 hours",
                "effectiveness": "CRITICAL"
            }
        },
        "support_resources": [
            {"name": "StopNCII", "url": "https://stopncii.org", "description": "Cross-platform blocking and reporting"},
            {"name": "CCRI Crisis Helpline", "url": "https://cybercivilrights.org", "description": "24/7 crisis support"}
        ],
        "legal_basis": ["DEFIANCE Act 2024 (US)", "Digital Services Act (EU)"],
        "template": """
            Subject: Report Non-Consensual Intimate Image - URGENT
            
            To: abuse@telegram.org
            
            Channel/Group: [INSERT CHANNEL/GROUP LINK]
            Post Date: [INSERT DATE]
            Content Type: [Deepfake/AI-generated intimate imagery]
            
            This content violates:
            - Your Terms of Service (Non-consensual intimate imagery)
            - DEFIANCE Act 2024 (AI-generated NCII)
            - Digital Services Act (Platform responsibility)
            
            IMMEDIATE TAKEDOWN REQUESTED.
        """
    },
    
    "reddit": {
        "name": "Reddit",
        "threat_level": "MEDIUM",
        "reporting": {
            "ncii_report": {
                "label": "NCII Report Form",
                "url": "https://www.reddit.com/report",
                "method": "Use Reddit's NCII report form",
                "time_to_remove": "24 hours",
                "effectiveness": "CRITICAL"
            },
            "safety_email": {
                "label": "Email safety@reddit.com",
                "url": "mailto:safety@reddit.com",
                "method": "Email with post link and proof",
                "time_to_remove": "24-48 hours",
                "effectiveness": "HIGH"
            }
        },
        "support_resources": [
            {"name": "StopNCII", "url": "https://stopncii.org", "description": "Hash protection database"},
            {"name": "Reddit Content Policy", "url": "https://www.redditinc.com/policies/content-policy", "description": "Official policy on NCII"}
        ],
        "legal_basis": ["DEFIANCE Act 2024 (US)", "FOSTA-SESTA"],
        "template": """
            Subject: URGENT: NCII Takedown Request
            
            To: safety@reddit.com
            
            Post Link: [INSERT REDDIT LINK]
            Subreddit: [INSERT SUBREDDIT]
            
            This post contains non-consensual intimate imagery that I did not consent to have posted.
            Content type: [AI-generated deepfake / synthetic intimate imagery]
            
            This violates Reddit's Content Policy and the DEFIANCE Act 2024.
            IMMEDIATE REMOVAL REQUIRED.
        """
    },
    
    "twitter": {
        "name": "X / Twitter",
        "threat_level": "HIGH",
        "reporting": {
            "intimate_images": {
                "label": "Report Intimate Images",
                "url": "https://help.twitter.com/forms/private_information",
                "method": "Use Twitter's intimate images form",
                "time_to_remove": "12-24 hours",
                "effectiveness": "CRITICAL"
            },
            "dmca_notice": {
                "label": "File DMCA Notice",
                "url": "https://help.twitter.com/forms/dmca",
                "method": "Formal copyright/likeness takedown",
                "time_to_remove": "24-48 hours",
                "effectiveness": "CRITICAL"
            },
            "abusive_user": {
                "label": "Report Abusive User",
                "url": "https://help.twitter.com/forms/abusiveuser",
                "method": "Report user account",
                "time_to_remove": "24-72 hours",
                "effectiveness": "HIGH"
            }
        },
        "support_resources": [
            {"name": "X Safety Help", "url": "https://help.twitter.com/en/safety-and-security", "description": "Official safety resources"},
            {"name": "StopNCII", "url": "https://stopncii.org", "description": "Cross-platform coordination"}
        ],
        "legal_basis": ["DEFIANCE Act 2024 (US)", "Online Safety Act 2023 (UK)"],
        "template": """
            Subject: URGENT: Non-Consensual Intimate Image Takedown
            
            To: help.twitter.com/forms/private_information
            
            Tweet Link: [INSERT TWEET LINK]
            Posted by: [INSERT ACCOUNT]
            
            Content: AI-generated deepfake intimate imagery posted without consent
            
            This violates:
            - X's Private Information Policy
            - DEFIANCE Act 2024 (US) - AI NCII is now FEDERAL CRIME
            
            IMMEDIATE REMOVAL + ACCOUNT SUSPENSION REQUESTED.
        """
    },
    
    "facebook": {
        "name": "Facebook / Meta",
        "threat_level": "MEDIUM",
        "reporting": {
            "ncii_report": {
                "label": "NCII Report Form",
                "url": "https://www.facebook.com/help/contact/567360covered",
                "method": "Use Meta's NCII form",
                "time_to_remove": "24 hours",
                "effectiveness": "CRITICAL"
            },
            "dmca_request": {
                "label": "DMCA Request",
                "url": "https://www.facebook.com/help/contact/634636770043106",
                "method": "File copyright/likeness takedown",
                "time_to_remove": "24-48 hours",
                "effectiveness": "CRITICAL"
            }
        },
        "support_resources": [
            {"name": "Meta Safety Center", "url": "https://www.facebook.com/help/", "description": "Official help resources"},
            {"name": "StopNCII", "url": "https://stopncii.org", "description": "Cross-platform coordination"}
        ],
        "legal_basis": ["DEFIANCE Act 2024 (US)"],
        "template": """
            Subject: URGENT: Deepfake NCII Removal
            
            Post Link: [INSERT FACEBOOK LINK]
            
            This post contains AI-generated synthetic intimate imagery.
            Posted without consent in violation of:
            - Meta's NCII Policy
            - DEFIANCE Act 2024
            
            IMMEDIATE REMOVAL + ACCOUNT BAN REQUESTED.
        """
    },
    
    "pornhub": {
        "name": "Pornhub",
        "threat_level": "CRITICAL",
        "reporting": {
            "dmca_notice": {
                "label": "DMCA Copyright Notice",
                "url": "https://www.pornhub.com/dmca",
                "method": "File DMCA for copyrighted likeness/image",
                "time_to_remove": "24 hours",
                "effectiveness": "CRITICAL"
            },
            "ncii_report": {
                "label": "Report Non-Consensual Content",
                "url": "https://www.pornhub.com/report",
                "method": "Report NCII content",
                "time_to_remove": "24 hours",
                "effectiveness": "HIGH"
            }
        },
        "support_resources": [
            {"name": "NCMEC", "url": "https://www.ncmec.org", "description": "National Center for Missing & Exploited Children"},
            {"name": "StopNCII", "url": "https://stopncii.org", "description": "Specialized support for online NCII"}
        ],
        "legal_basis": ["DEFIANCE Act 2024 (US)", "FOSTA-SESTA", "NCMEC reporting"],
        "template": """
            Subject: URGENT DMCA - Non-Consensual Deepfake Content
            
            To: dmca@pornhub.com
            
            Video URL: [INSERT VIDEO LINK]
            Uploaded: [INSERT DATE]
            
            DEFIANCE ACT VIOLATION: This is an AI-generated deepfake of non-consensual intimate imagery.
            As of 2024, creation and distribution of synthetic NCII is a FEDERAL FELONY in the US.
            
            I am the person depicted in this non-consensual deepfake.
            IMMEDIATE REMOVAL + IP BAN REQUIRED.
            
            Reporting to: NCMEC, FBI, and relevant law enforcement.
        """
    },
    
    "4chan": {
        "name": "4chan",
        "threat_level": "CRITICAL",
        "reporting": {
            "report_button": {
                "label": "Use 4chan Report Button",
                "url": "https://www.4chan.org/",
                "method": "Click report under post (right-click post number)",
                "time_to_remove": "6-24 hours",
                "effectiveness": "LOW (4chan has limited moderation)"
            },
            "dmca_notice": {
                "label": "DMCA via 4chan DMCA Agent",
                "url": "https://www.4chan.org/dmca",
                "method": "Formal DMCA takedown",
                "time_to_remove": "24-48 hours",
                "effectiveness": "MEDIUM"
            }
        },
        "support_resources": [
            {"name": "FBI IC3", "url": "https://ic3.gov", "description": "Report cybercrime"},
            {"name": "NCMEC", "url": "https://www.ncmec.org", "description": "Report exploitation"}
        ],
        "legal_basis": ["DEFIANCE Act 2024 (US)", "18 U.S.C. § 1030 (CFAA)"],
        "template": """
            4chan has limited DMCA response. RECOMMENDED: File with FBI IC3 and local law enforcement.
            
            Evidence to collect:
            - Screenshot with timestamp
            - URL/Post number
            - Thread archive (archive.org)
            
            This is a federal crime under DEFIANCE Act 2024.
            Law enforcement has greater authority than 4chan moderation.
        """
    }
}


def get_platform_removal_actions(platform: str) -> Dict:
    """Get all removal actions for a specific platform."""
    if platform not in PLATFORM_REMOVAL_ACTIONS:
        return {"error": f"Platform '{platform}' not in database"}
    
    return PLATFORM_REMOVAL_ACTIONS[platform]


def get_recommended_actions(
    platforms_found: List[str],
    threat_level: str = "MEDIUM"
) -> Dict:
    """
    Get recommended removal actions based on where content was found.
    
    Args:
        platforms_found: List of platform domains where content appears
        threat_level: Overall threat level
    
    Returns:
        Prioritized action plan
    """
    try:
        actions = []
        critical_actions = []
        
        for platform in platforms_found:
            platform_info = get_platform_removal_actions(platform)
            if "error" not in platform_info:
                # Add reporting options
                for report_type, report_info in platform_info.get("reporting", {}).items():
                    action = {
                        "platform": platform_info["name"],
                        "action": report_info["label"],
                        "url": report_info["url"],
                        "method": report_info["method"],
                        "time_to_remove": report_info["time_to_remove"],
                        "effectiveness": report_info["effectiveness"],
                        "priority": "CRITICAL" if report_info["effectiveness"] == "CRITICAL" else "HIGH"
                    }
                    
                    if action["priority"] == "CRITICAL":
                        critical_actions.append(action)
                    else:
                        actions.append(action)
        
        # Sort: critical first, then by effectiveness
        all_actions = critical_actions + actions
        
        return {
            "total_actions": len(all_actions),
            "critical_actions": len(critical_actions),
            "recommended_order": all_actions,
            "urgent_summary": f"URGENT: Start with the {len(critical_actions)} CRITICAL effectiveness actions",
            "legal_escalation": "If platform does not respond within 48 hours, escalate to FBI IC3 and law enforcement"
        }
    
    except Exception as e:
        logger.error(f"Recommended actions error: {e}")
        return {"error": str(e)}


def get_legal_support_resources() -> Dict:
    """Get comprehensive legal and support resources."""
    return {
        "legal_resources": {
            "defiance_act_2024": {
                "name": "DEFIANCE Act 2024 (US)",
                "url": "https://www.congress.gov/",  # Actual link would be updated
                "description": "Federal law criminalizing creation & distribution of AI-generated NCII",
                "penalties": "Up to 7 years prison + $150,000 fine"
            },
            "fosta_sesta": {
                "name": "FOSTA-SESTA",
                "url": "https://www.eff.org/deeplinks/2018/03/fosta-sesta",
                "description": "Holds platforms liable for NCII hosted on their services",
                "key_point": "Platforms must remove NCII or face penalties"
            }
        },
        "support_organizations": {
            "stopncii": {
                "name": "StopNCII.org",
                "url": "https://stopncii.org",
                "services": "Rapid removal coordination + hash protection",
                "availability": "24/7"
            },
            "ccri": {
                "name": "Cyber Civil Rights Initiative (CCRI)",
                "url": "https://cybercivilrights.org",
                "services": "Crisis support + legal referrals",
                "phone": "888-999-8339",
                "availability": "24/7"
            },
            "ncmec": {
                "name": "National Center for Missing & Exploited Children",
                "url": "https://www.ncmec.org",
                "services": "Report exploitation to law enforcement",
                "availability": "24/7"
            }
        },
        "law_enforcement": {
            "fbi_ic3": {
                "name": "FBI Internet Crime Complaint Center",
                "url": "https://ic3.gov",
                "services": "Report cybercrime and extortion",
                "for": "Sextortion, threats, extortion"
            },
            "ncic": {
                "name": "National Crime Information Center",
                "url": "https://crime-data-explorer.fbi.gov/",
                "services": "Track threats and harassment",
                "for": "Stalking, threats, harassment"
            }
        }
    }


def generate_action_plan(
    detected_platforms: List[str],
    is_deepfake: bool,
    threat_level: str = "MEDIUM"
) -> Dict:
    """Generate a complete action plan for victim."""
    try:
        legal_info = get_legal_support_resources()
        platform_actions = get_recommended_actions(detected_platforms, threat_level)
        
        return {
            "action_plan": {
                "phase_1_immediate": {
                    "timeline": "Now - Next 1 hour",
                    "actions": [
                        "Take screenshots of all found content (for evidence)",
                        "Contact platform via CRITICAL effectiveness reporting URL",
                        "Call CCRI crisis line for emotional support: 888-999-8339",
                        "Do NOT pay any extortion demands"
                    ]
                },
                "phase_2_escalation": {
                    "timeline": "1-24 hours",
                    "actions": [
                        "If deepfake: File report with FBI IC3 (https://ic3.gov)",
                        "File police report with local law enforcement",
                        "Contact StopNCII for cross-platform coordination",
                        "Request emergency protective order if known threat"
                    ]
                },
                "phase_3_legal": {
                    "timeline": "24-72 hours",
                    "actions": [
                        "Consult with attorney specializing in cyberharassment",
                        "File DMCA notice if platform doesn't respond",
                        "Report to relevant regulatory bodies",
                        "Consider civil lawsuit if identified perpetrator"
                    ]
                },
                "platform_actions": platform_actions.get("recommended_order", []),
                "critical_actions_count": platform_actions.get("critical_actions", 0),
                "support_resources": legal_info,
                "key_legal_points": [
                    "DEFIANCE Act 2024: Creating/distributing AI-generated NCII is a FEDERAL FELONY",
                    "You are the victim - DO NOT blame yourself",
                    "Platforms are legally required to remove this content",
                    "Law enforcement takes these cases seriously - report promptly",
                    "DO NOT contact perpetrator - all communication should be through authorities"
                ]
            },
            "timestamp": datetime.now().isoformat(),
            "plan_valid_until": "Continuously - all resources remain available"
        }
    
    except Exception as e:
        logger.error(f"Action plan generation error: {e}")
        return {"error": str(e)}
