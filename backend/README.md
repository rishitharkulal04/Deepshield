# DeepShield v7 — Backend Setup & Run Guide

## What Changed (v6 → v7)

### Architecture
Three new modular files replace the monolithic detection logic:

| File | Role |
|---|---|
| `deepfake_model.py` | ViT FaceForensics++ face-manipulation detection |
| `clip_model.py` | CLIP ViT-L/14 AI image vs real photography |
| `artifact_model.py` | ELA, DCT, noise, texture, metadata forensics |
| `ensemble.py` | Weighted scoring + calibrated thresholds + FP guard |

`deepfake_detector.py` and `detection_models.py` are now thin adapters —
they keep the same output contract so `main.py` and the frontend are **untouched**.

### Key Accuracy Improvements
- **CLIP model upgraded**: `clip-vit-base-patch32` → `clip-vit-large-patch14` (much stronger)
- **CLIP uses logit_scale softmax** (not raw cosine similarity) — properly calibrated
- **DCT spectral analysis** added — catches GAN / diffusion model frequency artifacts
- **LBP-like texture regularity** — detects unnaturally repeating AI textures
- **False-positive veto**: if all 3 models independently say "real", score is capped to Authentic
- **Calibrated thresholds**: `> 0.75` = AI Generated, `> 0.55` = Suspicious, `≤ 0.55` = Authentic
- **Ensemble requires 2-of-3** model agreement to flag as AI (reduces single-model false positives)

---

## Requirements

- Python 3.10+
- ~3 GB disk space for model downloads (first run)
- 8 GB RAM minimum (16 GB recommended)
- GPU (optional but speeds up inference 5–10×)

---

## Installation

```bash
# 1. Navigate to backend directory
cd DeepShield/backend

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On first run the following models will be downloaded automatically:
- `dima806/deepfake_vs_real_image_detection` (~350 MB) — ViT deepfake detector
- `openai/clip-vit-large-patch14` (~1.7 GB) — CLIP AI image classifier
- `Falconsai/nsfw_image_detection` (~350 MB) — NSFW content classifier

Total: ~2.4 GB on first run. Cached to `~/.cache/huggingface/` automatically.

---

## Running the Frontend (unchanged)

```bash
cd DeepShield/client
npm install        # first time only
npm run dev
```

Frontend runs at http://localhost:5173  
Backend API at http://localhost:8000  
API docs at http://localhost:8000/docs

---

## Detection Logic Summary

```
final_score = 0.50 × clip_ai_prob
            + 0.30 × deepfake_prob
            + 0.20 × artifact_prob

if final_score > 0.75  →  "AI Generated" (CONFIRMED_FAKE / LIKELY_FAKE)
if final_score > 0.55  →  "Suspicious"
else                   →  "Authentic" (SAFE)

False-positive guard:
  if deepfake_prob < 0.20
  AND clip_real_prob > 0.62
  AND artifact_prob < 0.38
  → score capped below Suspicious threshold regardless of formula
```

---

## Troubleshooting

**CUDA out of memory**: Models will automatically fall back to CPU.

**Slow inference**: Expected ~5–15s per image on CPU. Use a GPU for <2s.

**Model download fails**: Check internet connection; models download from Hugging Face Hub.

**Port in use**:
```bash
uvicorn main:app --reload --port 8001
```
Then update frontend `VITE_API_URL` in `.env`.

---

## File Structure (backend only)

```
backend/
├── main.py                  # FastAPI app (unchanged)
├── deepfake_detector.py     # analyze_image() entry point (updated)
├── detection_models.py      # ensemble_detection() adapter (updated)
├── deepfake_model.py        # NEW: ViT face deepfake module
├── clip_model.py            # NEW: CLIP AI image detection module
├── artifact_model.py        # NEW: forensic signal detection module
├── ensemble.py              # NEW: ensemble scoring + calibration
├── requirements.txt         # Updated
├── llm_client.py            # Unchanged
├── web_scanner.py           # Unchanged
├── threat_profiler.py       # Unchanged
├── reporting_takedown.py    # Unchanged
├── safety_link_handler.py   # Unchanged
└── reverse_image_search.py  # Unchanged
```
