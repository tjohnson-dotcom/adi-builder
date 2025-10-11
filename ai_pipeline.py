# ai_pipeline.py
# ------------------------------------------------------------
# Offline AI helper to call Ollama (Mistral + Phi-3) for
# question and activity generation. Works entirely locally.
# ------------------------------------------------------------

from __future__ import annotations
import json, os, requests
from typing import Any, Dict, List, Optional

# ------------------------
# Configuration
# ------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_BRAINSTORM = os.getenv("LLM_BRAINSTORM", "mistral")  # For idea generation
MODEL_NORMALIZE = os.getenv("LLM_NORMALIZE", "phi3:mini")  # For cleanup/JSON enforcement


# ------------------------
# Helper function to call Ollama
# ------------------------
def run_ollama(model: str, prompt: str) -> str:
    """Call Ollama model and return raw text output."""
    payload = {"model": model, "prompt": prompt}
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    result = response.text.split('"response":"')[-1]
    return result.replace('"}', '').strip()


# ------------------------
# Pipeline functions
# ------------------------
def brainstorm_questions(topic: str, bloom: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate draft MCQs or activities using the brainstorm model (Mistral).
    """
    prompt = f"""
    Generate {count} {bloom}-level multiple choice questions for the topic "{topic}".
    Each item should be formatted in JSON with:
      - question
      - options (list of 4)
      - answer (letter)
      - bloom_level
      - rationale (short)
    Do not include explanations outside JSON.
    """
    text = run_ollama(MODEL_BRAINSTORM, prompt)
    return normalize_json(text)


def brainstorm_activities(topic: str, bloom: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    Generate learning activities instead of MCQs.
    """
    prompt = f"""
    Suggest {count} {bloom}-level learning activities for "{topic}".
    Return valid JSON:
      - title
      - description
      - outcome
      - bloom_level
    No prose or markdown, just JSON.
    """
    text = run_ollama(MODEL_BRAINSTORM, prompt)
    return normalize_json(text)


# ------------------------
# JSON normalization
# ------------------------
def normalize_json(text: str) -> Any:
    """
    Clean and validate JSON using Phi-3 model.
    """
    prompt = f"""
    Convert the following text into a valid, parsable JSON list:
    ---
    {text}
    ---
    Output JSON only, no markdown, no explanation.
    """
    normalized = run_ollama(MODEL_NORMALIZE, prompt)
    try:
        return json.loads(normalized)
    except Exception:
        # Fallback if Phi-3 still outputs unclean text
        try:
            cleaned = normalized[normalized.find("[") : normalized.rfind("]") + 1]
            return json.loads(cleaned)
        except Exception:
            return [{"error": "Invalid JSON returned"}]


# ------------------------
# Quick test (optional)
# ------------------------
if __name__ == "__main__":
    result = brainstorm_questions("Thermofluids", "Apply", 3)
    print(json.dumps(result, indent=2))
