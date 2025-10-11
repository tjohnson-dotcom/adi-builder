# ai_pipeline.py
# Lightweight helpers to call Ollama (Mistral + Phi-3) for MCQs & Activities.
# Works offline, returns strict JSON you can render directly.

from __future__ import annotations
import json
import os
import requests
from typing import Any, Dict, List, Optional

# ---------------------------
# Configuration (edit if you like)
# ---------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Default models (good for 16 GB RAM on CPU)
MODEL_BRAINSTORM = os.getenv("LLM_BRAINSTORM", "mistral")   # or "mixtral:8x7b" if you have a good GPU
MODEL_NORMALIZE
