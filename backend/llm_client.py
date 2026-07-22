"""
LLM Client — Ollama — Optimized for speed
- Shorter prompts
- Lower token counts
- Fast JSON fallback
"""
import requests, json, re

OLLAMA_URL = "http://localhost:11434"

def get_model() -> str:
    try:
        res = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        models = [m["name"].split(":")[0] for m in res.json().get("models", [])]
        # Prefer fastest models first
        for pref in ["tinyllama", "phi3", "llama3", "llama3.2", "mistral", "gemma"]:
            if pref in models: return pref
        return models[0] if models else "tinyllama"
    except:
        return "tinyllama"

def ollama(prompt: str, system: str = "", temp: float = 0.3) -> str:
    try:
        res = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": get_model(),
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": 250,   # Short — just enough
                "num_ctx": 1024,      # Small context = faster
                "num_thread": 8,      # Use more CPU threads
            }
        }, timeout=90)
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama not running. Run: ollama serve")
    except requests.exceptions.Timeout:
        raise RuntimeError("LLM timed out.")
    except Exception as e:
        raise RuntimeError(f"LLM error: {e}")

def ollama_stream(prompt: str, system: str = "", temp: float = 0.3):
    """Yields tokens in real time."""
    try:
        with requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": get_model(),
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {
                "temperature": temp,
                "num_predict": 400,
                "num_ctx": 1024,
                "num_thread": 8,
            }
        }, timeout=180, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama not running. Run: ollama serve")
    except Exception as e:
        raise RuntimeError(f"Stream error: {e}")

def extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    start, end = text.find("{"), text.rfind("}") + 1
    if start != -1 and end > start:
        try: return json.loads(text[start:end])
        except: pass
    try: return json.loads(text)
    except: raise ValueError(f"JSON parse failed: {text[:200]}")

def generate_full_analysis(verdict: str, risk_score: int, indicators: list, leaked_sites: list) -> dict:
    """Short prompt = fast response."""
    system = "Respond ONLY in valid JSON. No explanation."
    prompt = f"""Deepfake scan: verdict={verdict}, risk={risk_score}/100
JSON only:
{{"summary":"1-2 sentences","immediate_actions":["a1","a2","a3"],"emotional_support":"1 sentence"}}"""
    try:
        return extract_json(ollama(prompt, system=system, temp=0.2))
    except:
        return _fallback_analysis(verdict, risk_score)

def _fallback_analysis(verdict: str, risk_score: int) -> dict:
    if risk_score >= 65:
        return {
            "summary": f"High risk detected ({risk_score}/100). Strong AI synthesis indicators present. Immediate action recommended.",
            "immediate_actions": ["Document all evidence now", "File DMCA via Legal Ops tab", "Report to platform Trust & Safety", "Contact CCRI at cybercivilrights.org"],
            "emotional_support": "You are not alone — this is a crime and there are people ready to help you fight back."
        }
    elif risk_score >= 40:
        return {
            "summary": f"Borderline result ({risk_score}/100). Manual review advised — some synthesis indicators present.",
            "immediate_actions": ["Save all evidence", "Report to platform if content is harmful", "Consider a precautionary DMCA notice"],
            "emotional_support": "Take this seriously — early action is always the most effective response."
        }
    return {
        "summary": f"No significant deepfake indicators found. Risk score: {risk_score}/100.",
        "immediate_actions": ["Monitor your online presence regularly", "Set up Google Alerts for your name"],
        "emotional_support": "Stay vigilant — regular monitoring is the best prevention strategy."
    }

def assess_threat(description: str) -> dict:
    system = "Respond ONLY in valid JSON."
    prompt = f"""Situation: "{description[:300]}"
JSON: {{"threat_level":"HIGH","urgency_score":8,"immediate_steps":["s1","s2","s3"],"legal_options":["o1","o2"],"support_message":"msg","estimated_spread_risk":"HIGH"}}"""
    try:
        return extract_json(ollama(prompt, system=system, temp=0.2))
    except:
        return {
            "threat_level": "HIGH", "urgency_score": 7,
            "immediate_steps": ["Document all evidence immediately", "Report to platform trust & safety", "File a police report"],
            "legal_options": ["DMCA Section 512 takedown", "File under DEFIANCE Act 2024"],
            "support_message": "This is not your fault. You have legal rights and support is available.",
            "estimated_spread_risk": "HIGH"
        }

def generate_legal_doc(name: str, platform: str, url: str, date: str, doc_type: str) -> str:
    prompts = {
        "dmca": f"Write a short DMCA 512(c) takedown. Victim:{name}. Platform:{platform}. URL:{url or 'TBD'}. Date:{date or 'Recent'}. Include: copyright claim, URL, good faith statement, signature.",
        "police": f"Write a short police report for deepfake NCII. Victim:{name}. Platform:{platform}. Date:{date or 'Recent'}. Cite DEFIANCE Act 2024.",
        "platform": f"Write a short Trust & Safety removal request. Reporter:{name}. Platform:{platform}. URL:{url or 'TBD'}. Demand NCII deepfake removal.",
    }
    return ollama(prompts.get(doc_type, prompts["dmca"]), temp=0.2)

def generate_legal_doc_stream(name: str, platform: str, url: str, date: str, doc_type: str):
    prompts = {
        "dmca": f"Write a short DMCA 512(c) takedown. Victim:{name}. Platform:{platform}. URL:{url or 'TBD'}. Date:{date or 'Recent'}. Include: copyright claim, URL, good faith statement, signature.",
        "police": f"Write a short police report for deepfake NCII. Victim:{name}. Platform:{platform}. Date:{date or 'Recent'}. Cite DEFIANCE Act 2024.",
        "platform": f"Write a short Trust & Safety removal request. Reporter:{name}. Platform:{platform}. URL:{url or 'TBD'}. Demand NCII deepfake removal.",
    }
    return ollama_stream(prompts.get(doc_type, prompts["dmca"]), temp=0.2)
