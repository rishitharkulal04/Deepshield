"""
DeepShield — Conditional Police Complaint Generator
=====================================================
Generates a cybercrime police complaint ONLY when the image is
confirmed as a Deepfake (face-swap / face-manipulation on a real person).

Rules:
  - Returns a complaint dict ONLY if classification == "Deepfake"
  - Returns None for "Real" or "AI Generated" images
  - Includes India emergency helplines: 112 and 1930
"""

import datetime
from typing import Optional


# ── India Cybercrime Helplines ─────────────────────────────────────────────

HELPLINES = [
    {
        "number":      "112",
        "label":       "National Emergency Helpline (Police / Ambulance / Fire)",
        "description": "Dial 112 immediately if you are in imminent danger or need emergency assistance.",
        "available":   "24/7",
    },
    {
        "number":      "1930",
        "label":       "National Cybercrime Helpline (India)",
        "description": (
            "Report cybercrime including deepfake image abuse, non-consensual "
            "intimate imagery (NCII), and online harassment. Also file at: "
            "https://cybercrime.gov.in"
        ),
        "available":   "24/7",
        "portal":      "https://cybercrime.gov.in",
    },
    {
        "number":      "CCRI Crisis Helpline",
        "label":       "Cyber Civil Rights Initiative (International Support)",
        "description": "Free crisis support for victims of non-consensual intimate image abuse.",
        "url":         "https://cybercivilrights.org/ccri-crisis-helpline/",
        "available":   "Mon–Fri, 10am–6pm ET",
    },
]

# ── Legal References ────────────────────────────────────────────────────────

LEGAL_REFS = [
    "Section 66E of the Information Technology Act, 2000 (Privacy violation)",
    "Section 67 of the IT Act, 2000 (Publishing obscene material in electronic form)",
    "Section 67A of the IT Act, 2000 (Publishing sexually explicit act in electronic form)",
    "Section 354C of the Indian Penal Code (Voyeurism)",
    "Section 509 of the Indian Penal Code (Word, gesture intended to insult modesty of a woman)",
    "DEFIANCE Act 2024 (US) — if content is hosted on US-based platforms",
]


def generate_complaint(
    filename: str,
    detection_result: dict,
    victim_name: str = "[VICTIM NAME]",
    incident_date: Optional[str] = None,
) -> Optional[dict]:
    """
    Generate a police complaint ONLY if the image is classified as a Deepfake.

    Parameters
    ----------
    filename         : original uploaded filename
    detection_result : the dict returned by deepfake_detector.analyze_image()
    victim_name      : victim's name (filled later by user in legal toolkit)
    incident_date    : ISO date string; defaults to today

    Returns
    -------
    dict   — complaint object if Deepfake detected
    None   — if not a Deepfake (Real or AI Generated)
    """
    classification = detection_result.get("classification", "Real")

    # STRICT RULE: only generate for confirmed Deepfakes
    if classification != "Deepfake":
        return None

    if not incident_date:
        incident_date = datetime.date.today().isoformat()

    confidence  = detection_result.get("confidence", 0)
    risk_score  = detection_result.get("risk_score", 0)
    indicators  = detection_result.get("indicators", [])

    complaint_text = _build_complaint_text(
        filename, victim_name, incident_date, confidence, risk_score, indicators
    )

    return {
        "generated":         True,
        "classification":    "Deepfake",
        "confidence":        confidence,
        "risk_score":        risk_score,
        "incident_date":     incident_date,
        "filename":          filename,
        "complaint_text":    complaint_text,
        "helplines":         HELPLINES,
        "legal_references":  LEGAL_REFS,
        "submission_portal": "https://cybercrime.gov.in",
        "immediate_steps": [
            " Call 1930 (National Cybercrime Helpline) immediately",
            " Take screenshots / preserve evidence before it is deleted",
            " File an online complaint at https://cybercrime.gov.in",
            " Email the platform abuse team with the content URL",
            " Use StopNCII.org to hash-block the image across platforms",
            " Visit your nearest police station with this report",
        ],
        "warning": (
            "This complaint template is auto-generated as a starting point. "
            "Fill in your personal details, verify the content of the complaint, "
            "and consult a legal professional before submission."
        ),
    }


def _build_complaint_text(
    filename: str,
    victim_name: str,
    incident_date: str,
    confidence: int,
    risk_score: int,
    indicators: list,
) -> str:
    """Build the formatted police complaint body text."""

    indicators_text = "\n".join(f"  • {i}" for i in indicators[:5]) if indicators else "  • AI face-manipulation detected by ensemble model"

    return f"""TO,
THE STATION HOUSE OFFICER / CYBER CRIME CELL
[Police Station Name]
[City / District]

SUBJECT: Complaint regarding creation and distribution of Deepfake / Non-consensual Intimate Imagery (NCII)

DATE: {incident_date}

Respected Sir/Madam,

I, {victim_name}, hereby formally lodge this complaint regarding the creation and/or potential distribution of a Deepfake image that uses my likeness without my consent.

1. INCIDENT DETAILS
   - File Analysed      : {filename}
   - Detection Date     : {incident_date}
   - AI Detection Tool  : DeepShield Ensemble v11 (CLIP ViT-L/14 + dima806 ViT)
   - Classification     : DEEPFAKE (face manipulation / face-swap detected)
   - Confidence Score   : {confidence}%
   - Risk Score         : {risk_score}/100

2. TECHNICAL EVIDENCE
   The following AI-forensic signals confirm the image is a deepfake:
{indicators_text}

3. RELIEF SOUGHT
   a) Immediate identification and arrest of the person(s) responsible for creating this deepfake.
   b) Identification and takedown of any platform or URL where this image has been shared.
   c) Seizure of all digital evidence from the accused's devices.
   d) Legal action under relevant sections of the IT Act and IPC (see below).

4. APPLICABLE LAW
   - Section 66E IT Act 2000 — Violation of privacy
   - Section 67 / 67A IT Act 2000 — Publishing obscene/sexually explicit content
   - Section 354C IPC — Voyeurism
   - Section 509 IPC — Insulting modesty of a woman

5. EMERGENCY CONTACTS USED
   - National Cybercrime Helpline: 1930
   - National Emergency: 112
   - Online Portal: https://cybercrime.gov.in

I hereby declare that the information provided is true to the best of my knowledge.

Yours sincerely,
{victim_name}
[Full Address]
[Phone Number]
[Email Address]

[Signature]
"""
