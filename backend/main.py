"""
DeepShield v7 — FastAPI Backend
Deepfake Detection + NSFW + Reverse Image Search + Legal Toolkit
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn, asyncio, concurrent.futures
import logging, os
from dotenv import load_dotenv

load_dotenv()

from deepfake_detector import analyze_image
from web_scanner      import scan_for_leaks, google_reverse_search, bing_reverse_search, tineye_search
from threat_profiler  import build_threat_profile
from llm_client       import (
    assess_threat, generate_legal_doc,
    generate_legal_doc_stream, generate_full_analysis,
)
from detection_models    import ensemble_detection
from safety_link_handler import batch_sanitize_links
from reporting_takedown  import generate_action_plan
import hash_verifier
import police_complaint as _police_complaint


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8000))

# Allow both common dev ports (Vite default 5173 and 3000)
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
).split(",")

app = FastAPI(
    title="DeepShield v7 API",
    version="7.0.0",
    description="Advanced AI Deepfake Detection + Reverse Image Search + Legal Toolkit"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "version": "9.0.0",
        "models": {
            "deepfake": "dima806/deepfake_vs_real_image_detection (ViT FaceForensics++)",
            "nsfw": "Falconsai/nsfw_image_detection",
            "clip": "openai/clip-vit-large-patch14",
            "forensic": "ELA + DCT + Noise + Metadata (artifact_model)",
            "ocr": "pytesseract text anomaly analysis",
            "frequency": "FFT / GAN frequency domain analysis",
            "face": "MediaPipe face mesh geometry consistency",
            "ensemble": "Model 40% + Text 15% + Metadata 10% + Frequency 20% + Face 15%",
        },
        "features": [
            "AI-generated image detection (CLIP ViT-L/14)",
            "Deepfake face detection (ViT FaceForensics++)",
            "Forensic artifact analysis (ELA, DCT, noise, metadata)",
            "OCR text anomaly detection (garbled/hallucinated text)",
            "FFT / GAN frequency domain analysis",
            "Face geometry consistency (MediaPipe)",
            "Explicit content fake detection (Falconsai NSFW)",
            "Reverse image search (Google + Bing)",
            "Threat actor profiling",
            "Automated DMCA legal toolkit",
        ]
    }


@app.post("/api/detect")
async def detect(image: UploadFile = File(...)):
    """
    Lightweight multi-layer AI image detection endpoint.

    Returns the clean JSON format:
      {
        "prediction": "AI Generated / Real",
        "confidence": 87.5,
        "ai_score": 0.87,
        "reasons": ["Text anomaly detected", "No metadata found", ...]
      }
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Max file size: 10MB")

    loop = asyncio.get_event_loop()
    try:
        import ensemble as _ensemble
        result = await loop.run_in_executor(executor, _ensemble.run, contents)

        ai_score   = float(result.get("ai_score", result.get("final_score", 0.0)))
        confidence = float(result.get("confidence", 50))
        verdict    = result.get("verdict", "Authentic")
        reasons    = result.get("reasons", [])

        prediction = (
            "AI Generated" if verdict == "AI Generated"
            else "Suspicious" if verdict == "Suspicious"
            else "Real"
        )

        # ── Classification (3-class: Real / AI Generated / Deepfake) ─────
        # Read directly from ensemble result (preferred) or derive from verdict
        classification = result.get("classification") or (
            "AI Generated" if verdict == "AI Generated"
            else "Deepfake"   if verdict == "Deepfake"
            else "Real"
        )

        return {
            "prediction":         prediction,
            "classification":     classification,   # Real / AI Generated / Deepfake (internal)
            "confidence":         round(confidence, 1),
            "ai_score":           round(ai_score,   4),
            "reasons":            reasons,
            "debug_scores":       result.get("debug_scores", {}),
            "layer_scores":       result.get("layer_scores", {}),
            "verdict":            verdict,
            # ── Unified public output ──────────────────────────────────────────
            "public_prediction":  result.get("public_prediction",  prediction),
            "category_internal":  result.get("category_internal",  classification),
            "public_explanation": result.get("public_explanation",  ""),
        }
    except Exception as e:
        logger.error(f"Detect error: {e}")
        raise HTTPException(500, f"Detection failed: {str(e)}")


@app.post("/api/osint")
async def osint_leak_search(image: UploadFile = File(...)):
    """
    OSINT-grade leak detection with perceptual hash verification.

    STRICT RULES (zero hallucination):
    - Every candidate URL is downloaded and hash-verified (pHash + aHash + dHash)
    - Only HIGH-confidence matches (hash distance ≤ 8) are returned
    - If nothing verifies → returns "No verified leaked content found."
    - No fabricated or guessed links under any circumstances

    Output format (matches found):
      [{"platform": "Reddit", "url": "...", "confidence": "high"}, ...]

    Output format (no matches):
      {"result": "No verified leaked content found."}
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Max file size: 10MB")

    loop = asyncio.get_event_loop()

    try:
        # ── Step 1: Compute perceptual hashes of input image ───────────────
        image_hashes = hash_verifier.compute_image_hashes(contents)
        logger.info(f"OSINT scan — input hashes: {image_hashes}")

        # ── Step 2: Collect candidate URLs from multiple reverse search engines
        logger.info("OSINT: collecting candidate URLs from reverse image search...")

        def _collect_candidates():
            candidates = []
            candidates.extend(google_reverse_search(contents))
            if len(candidates) < 5:
                candidates.extend(bing_reverse_search(contents))
            if len(candidates) < 5:
                candidates.extend(tineye_search(contents))
            # Deduplicate
            return list(dict.fromkeys(candidates))

        raw_candidates = await asyncio.wait_for(
            loop.run_in_executor(executor, _collect_candidates),
            timeout=45,
        )
        logger.info(f"OSINT: {len(raw_candidates)} raw candidate URLs collected")

        if not raw_candidates:
            return {
                "result":        "No verified leaked content found.",
                "reason":        "Reverse image search returned no results (search engine blocked or image not indexed).",
                "image_hashes":  image_hashes,
                "candidates_checked": 0,
            }

        # ── Step 3: Hash-verify every candidate URL ────────────────────────
        logger.info("OSINT: verifying each candidate with perceptual hash...")

        verified_matches = await asyncio.wait_for(
            loop.run_in_executor(
                executor,
                hash_verifier.run_osint_verification,
                contents,
                raw_candidates,
                10,  # max URLs to check
            ),
            timeout=120,
        )

        # ── Step 4: Return strict output ───────────────────────────────────
        if not verified_matches:
            return {
                "result":             "No verified leaked content found.",
                "reason":             f"Checked {len(raw_candidates)} candidate URLs — none passed perceptual hash verification (pHash/aHash/dHash threshold).",
                "image_hashes":       image_hashes,
                "candidates_checked": len(raw_candidates),
            }

        # Format exactly as per OSINT spec
        output = []
        for m in verified_matches:
            output.append({
                "platform":       m["platform"],
                "url":            m["url"],
                "confidence":     m["confidence"],      # always "high"
                "hash_distances": m.get("hash_distances", {}),
            })

        logger.info(f"OSINT: {len(output)} verified leak(s) found")
        return {
            "matches":            output,
            "image_hashes":       image_hashes,
            "candidates_checked": len(raw_candidates),
            "verified_count":     len(output),
        }

    except asyncio.TimeoutError:
        logger.warning("OSINT scan timed out")
        return {
            "result":  "No verified leaked content found.",
            "reason":  "Search timed out — try again later.",
            "image_hashes": hash_verifier.compute_image_hashes(contents),
        }
    except Exception as e:
        logger.error(f"OSINT error: {e}")
        raise HTTPException(500, f"OSINT scan failed: {str(e)}")




@app.post("/api/analyze")
async def analyze(image: UploadFile = File(...)):
    """
    Full pipeline: deepfake detection + NSFW + reverse image search + threat profile.
    Returns flat response compatible with frontend Scan.jsx.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Max file size: 10MB")

    loop = asyncio.get_event_loop()

    try:
        # Step 1: Primary ViT deepfake + NSFW analysis
        logger.info("Running primary deepfake detection...")
        detection = await loop.run_in_executor(executor, analyze_image, contents)

        # Step 2: Ensemble multi-model detection (CLIP + ViT + Forensic)
        logger.info("Running ensemble detection...")
        ensemble = await loop.run_in_executor(executor, ensemble_detection, contents)

        # ── Step 3: Leak scan (strict — no unverified entries) ─────────────
        logger.info("Scanning for leaked copies...")
        leaked_sites_raw = []
        try:
            leaked_sites_raw = await asyncio.wait_for(
                loop.run_in_executor(executor, scan_for_leaks, contents, detection["risk_score"]),
                timeout=60
            )
        except asyncio.TimeoutError:
            logger.warning("Leak scan timed out")

        # Filter: only verified, accessible entries (confidence_score > 0.0)
        leaked_sites = [
            s for s in leaked_sites_raw
            if s.get("verified", False) and s.get("confidence_score", 0.0) > 0.0
        ]
        leak_result = (
            "No verified matches found."
            if not leaked_sites
            else f"{len(leaked_sites)} verified leak source(s) found."
        )

        # ── Step 4: LLM analysis ───────────────────────────────────────────
        logger.info("Generating LLM analysis...")
        llm_result = {}
        try:
            llm_result = await asyncio.wait_for(
                loop.run_in_executor(
                    executor, generate_full_analysis,
                    detection["verdict"], detection["risk_score"],
                    detection["indicators"], leaked_sites
                ),
                timeout=90
            )
        except asyncio.TimeoutError:
            llm_result = _fast_fallback(detection["verdict"], detection["risk_score"])

        # ── Step 5: Threat profile ────────────────────────────────────────
        threat_profile = build_threat_profile(
            detection["risk_score"],
            detection["verdict"],
            detection.get("nsfw", {}),
            leaked_sites,
            contents
        )

        # ── Step 6: Conditional Police Complaint (Deepfake only) ──────────
        # Generates complaint with India helplines 112 & 1930 ONLY if Deepfake
        complaint = _police_complaint.generate_complaint(
            filename=image.filename or "uploaded_image",
            detection_result=detection,
        )

        # ── Return flat response matching Scan.jsx expectations ───────────
        classification = detection.get("classification", "Real")
        return {
            # Primary detection fields
            "verdict":          detection["verdict"],
            "classification":   classification,         # Real / AI Generated / Deepfake (internal)
            "risk_score":       detection["risk_score"],
            "confidence":       detection["confidence"],
            "indicators":       detection["indicators"],
            "nsfw":             detection.get("nsfw", {}),
            "raw_scores":       detection.get("raw_scores", {}),
            "model_used":       detection.get("model_used", ""),
            # ── Unified public output (user-facing) ───────────────────────────────
            # AI Generated + Deepfake both surface as "Deepfake / Manipulated Media Detected"
            # Internal classification is preserved above for police complaint, legal toolkit, etc.
            "public_prediction":  detection.get("public_prediction",  "Clean / Authentic"),
            "category_internal":  detection.get("category_internal",  classification),
            "public_explanation": detection.get("public_explanation", ""),
            # Leak data (verified only — no hallucinated entries)
            "leaked_sites":     leaked_sites,
            "total_leaks":      len(leaked_sites),
            "leak_result":      leak_result,  # human-readable summary
            # Police complaint (null unless internal classification == "Deepfake")
            "police_complaint": complaint,
            # Analysis
            "llm_analysis":     llm_result,
            "threat_profile":   threat_profile,
            # Ensemble multi-model results
            "detection": {
                "is_ai_generated":      ensemble["is_ai_generated"],
                "is_deepfake":          ensemble["is_deepfake"],
                "is_explicit_fake":     ensemble["is_explicit_fake"],
                "is_body_ai_generated": ensemble.get("is_body_ai_generated", False),
                "confidence_score":     ensemble["confidence_score"],
                "explanation":          ensemble["explanation"],
                "is_synthetic":         ensemble["is_synthetic"],
                "model_confidences":    ensemble.get("model_confidences", {}),
                "classification":       ensemble.get("classification", classification),
            },
        }

    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


def _fast_fallback(verdict: str, risk_score: int) -> dict:
    if risk_score >= 70:
        return {
            "summary": f"High-risk content detected. Risk score: {risk_score}/100. Immediate action recommended.",
            "immediate_actions": [
                "Document all evidence — screenshot URLs and timestamps",
                "File DMCA takedown via the Legal Ops tab",
                "Report to platform Trust & Safety team",
                "Contact CCRI at cybercivilrights.org for victim support",
            ],
            "emotional_support": "You are not alone — this is a crime and there are people ready to help you fight back.",
        }
    elif risk_score >= 40:
        return {
            "summary": f"Borderline result. Risk score: {risk_score}/100. Manual review advised.",
            "immediate_actions": [
                "Save all evidence before it disappears",
                "Report to platform if content is harmful",
                "Consider filing a precautionary DMCA notice",
            ],
            "emotional_support": "Take this seriously — early action is the most effective response.",
        }
    return {
        "summary": f"No significant deepfake indicators found. Risk score: {risk_score}/100.",
        "immediate_actions": ["Monitor your online presence regularly", "Set up Google Alerts for your name"],
        "emotional_support": "Stay vigilant — regular monitoring is the best prevention.",
    }


# ── AI Police Complaint Generator (Ollama, Deepfake-only) ────────────────────

class ComplaintReq(BaseModel):
    classification: str          # must be "Deepfake" to proceed
    filename:       str = "uploaded_image"
    confidence:     float = 0.0
    risk_score:     int   = 0
    indicators:     List[str] = []


@app.post("/api/complaint/generate")
async def generate_complaint_stream(req: ComplaintReq):
    """
    Stream an Ollama-generated police complaint.

    STRICT RULE: Returns 403 if classification != 'Deepfake'.
    Only confirmed face-manipulation deepfakes may generate a complaint.
    """
    if req.classification != "Deepfake":
        raise HTTPException(
            status_code=403,
            detail="Police complaint can only be generated for confirmed Deepfake content.",
        )

    indicators_text = (
        "\n".join(f"  - {i}" for i in req.indicators[:5])
        if req.indicators
        else "  - AI face-manipulation signals detected by ensemble model"
    )

    prompt = f"""Generate a formal cybercrime police complaint for submission to Indian authorities.

DETECTION RESULTS:
  File: {req.filename}
  Classification: DEEPFAKE (face manipulation / face-swap)
  Confidence: {req.confidence:.1f}%
  Risk Score: {req.risk_score}/100
  Technical Indicators:
{indicators_text}

Write the complaint in the following structure:
1. Header (To: Station House Officer / Cyber Crime Cell)
2. Subject line
3. Date
4. Body describing the incident — mention that a deepfake image using the complainant's likeness was detected by an AI forensic tool
5. Request for immediate investigation, takedown, and arrest of the perpetrator
6. Mention of applicable laws: Section 66E IT Act 2000, Section 67/67A IT Act 2000, Section 354C IPC
7. Closing with complainant signature block

Rules:
- Write in formal legal English
- Do NOT use placeholder text — write as if ready to submit
- Do NOT include any preamble or explanation — only the complaint itself
- Include the cybercrime portal: https://cybercrime.gov.in"""

    def _stream():
        try:
            from llm_client import ollama_stream
            for token in ollama_stream(
                prompt,
                system="You are a legal document assistant specialising in Indian cybercrime law. Output ONLY the formal complaint document — no preamble, no explanation.",
                temp=0.2,
            ):
                yield token
            yield ""
        except RuntimeError as e:
            yield f"[ERROR] {str(e)}\n\nNote: Ensure Ollama is running: ollama serve\nThen pull a model: ollama pull tinyllama"

    return StreamingResponse(
        _stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Threat Assessment ──────────────────────────────────────────────────────

class AssessReq(BaseModel):
    description: str


@app.post("/api/assess")
async def assess_endpoint(req: AssessReq):
    """Assess a threat situation using the local LLM."""
    description = req.description
    if not description.strip():
        raise HTTPException(400, "Description required")
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, assess_threat, description),
            timeout=90
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(503, "LLM timed out — is Ollama running? Run: ollama serve")
    except RuntimeError as e:
        raise HTTPException(503, str(e))


# ── Legal Document Generation ──────────────────────────────────────────────

class LegalReq(BaseModel):
    name:          str
    platform:      str
    url:           Optional[str] = ""
    incident_date: Optional[str] = ""
    doc_type:      str = "dmca"


@app.post("/api/legal")
async def legal(req: LegalReq):
    if not req.name or not req.platform:
        raise HTTPException(400, "Name and platform required")
    loop = asyncio.get_event_loop()
    try:
        doc = await asyncio.wait_for(
            loop.run_in_executor(
                executor, generate_legal_doc,
                req.name, req.platform, req.url or "",
                req.incident_date or "", req.doc_type
            ), timeout=120
        )
        return {"document": doc}
    except asyncio.TimeoutError:
        raise HTTPException(503, "LLM timed out — is Ollama running? Run: ollama serve")
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.post("/api/legal/stream")
async def legal_stream(req: LegalReq):
    if not req.name or not req.platform:
        raise HTTPException(400, "Name and platform required")

    def token_generator():
        try:
            for token in generate_legal_doc_stream(
                req.name, req.platform, req.url or "",
                req.incident_date or "", req.doc_type
            ):
                yield token
            yield ""
        except RuntimeError as e:
            yield f"[ERROR] {str(e)}\n\nNote: Ensure Ollama is running: ollama serve\nThen pull a model: ollama pull tinyllama"

    return StreamingResponse(
        token_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ── Support endpoints ──────────────────────────────────────────────────────

@app.post("/api/action-plan")
async def action_plan_endpoint(detected_platforms: List[str], is_deepfake: bool):
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            executor, generate_action_plan, detected_platforms, is_deepfake
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════╗")
    print("║   DEEPSHIELD v7 — Starting Backend...    ║")
    print("╚══════════════════════════════════════════╝")
    print("Ensemble: CLIP ViT-L/14 (50%) + dima806 ViT (30%) + Forensic (20%)")
    print("NSFW: Falconsai/nsfw_image_detection")
    print("Note: First run downloads models (~2.1 GB total)")
    print(f"API docs: http://localhost:{PORT}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
