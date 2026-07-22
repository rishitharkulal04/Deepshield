# DeepShield v8 — AI Deepfake Detection + Leak Finder

> **Frontend:** v2.0 (React/Vite) — UI fully preserved
> **Backend:** v8 (FastAPI, 4-signal ensemble) — enhanced for Gemini, DALL-E, Firefly, Midjourney
> **New in v8:** Real content URLs in leak results · TinEye search · Edge/chroma forensic signals

---

## AI Detection Models (v8 Ensemble)

| Model | Weight | Detects |
|-------|--------|---------|
| openai/clip-vit-large-patch14 | 50% | Gemini, DALL-E 3, Midjourney, Stable Diffusion, Firefly, Leonardo, Bing Image Creator |
| dima806/deepfake_vs_real_image_detection | 25% | Face deepfakes, face-swaps (ViT FaceForensics++) |
| Forensic Artifacts | 25% | ELA, DCT, Noise, Edge coherence, Chroma noise, Metadata, Texture |
| Falconsai/nsfw_image_detection | Additive | Explicit / NSFW classification |

Total first-run download: ~2.1 GB (cached after first run)

---

## Leak Detection — Real Content URLs

Each leak result now shows:
- CONTENT URL — the exact page where content was found
- View Content Page button — opens the page directly
- Report This Content — platform's abuse/report form
- DMCA button — direct takedown form
- Copy URL — for evidence documentation

Search engines used (in order): Google Lens → Bing Visual Search → TinEye

---

## Project Structure

```
DeepShield_Final/
├── README.md
├── frontend/
│   ├── src/pages/        Scan.jsx  Assess.jsx  Legal.jsx  Dashboard.jsx  Landing.jsx
│   ├── vite.config.js    proxies /api → localhost:8000
│   ├── package.json
│   └── .env
└── backend/
    ├── main.py           routes + CORS + .env
    ├── ensemble.py       CLIP 50% + ViT 25% + Forensic 25%
    ├── clip_model.py     CLIP ViT-L/14 + Gemini/DALL-E/Firefly prompts
    ├── deepfake_model.py dima806 ViT deepfake detector
    ├── artifact_model.py ELA/DCT/Noise/Edge/Chroma/Metadata
    ├── deepfake_detector.py  analyze_image() entry + NSFW
    ├── detection_models.py   ensemble_detection() wrapper
    ├── web_scanner.py    Google+Bing+TinEye real reverse search
    ├── threat_profiler.py
    ├── llm_client.py
    ├── reporting_takedown.py
    ├── requirements.txt
    └── .env
```

---

## Environment Variables

backend/.env
```
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
OLLAMA_URL=http://localhost:11434
```

frontend/.env
```
VITE_API_URL=http://localhost:8000
```

---

## Setup and Run

### Requirements
- Python 3.10+
- Node.js 18+ and npm
- pip

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Backend: http://localhost:8000
API docs: http://localhost:8000/docs
Note: First run downloads ~2.1 GB of models automatically.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:3000

### Optional — Ollama LLM (for legal docs + threat analysis)
```bash
# Install: https://ollama.ai/download
ollama serve
ollama pull tinyllama    # fast, ~600 MB
# or: ollama pull phi3  # better quality, ~2.3 GB
```
Without Ollama, image detection still works fully — only LLM text features are affected.

---

## API Endpoints

GET  /api/health          backend health + model info
POST /api/analyze         full pipeline: deepfake + NSFW + leaks + threat
POST /api/assess          text threat assessment (LLM)
POST /api/legal           generate legal document
POST /api/legal/stream    streaming legal doc
POST /api/action-plan     platform-specific action plan

---

## Troubleshooting

Models fail to download: check internet connection. Cache at ~/.cache/huggingface/
CORS error: check ALLOWED_ORIGINS in backend/.env includes your frontend port
LLM 503: run `ollama serve` then `ollama pull tinyllama`
Port 3000 in use: change port in frontend/vite.config.js and add it to ALLOWED_ORIGINS
Leak search shows RISK-BASED results: Google/Bing blocked automated search in your region — intelligence estimates are shown instead of confirmed matches
