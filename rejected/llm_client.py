import os
import json
import requests
from typing import Optional, Dict, Any

# LLM_MODE:
# - "ollama" -> uses /api/chat (Ollama native)
# - "openai" -> uses /v1/chat/completions (OpenAI-compatible server)
# - "auto"   -> try openai then fall back to ollama
LLM_MODE = os.getenv("LLM_MODE", "ollama").lower()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        h["Authorization"] = f"Bearer {LLM_API_KEY}"
    return h

def ping() -> Dict[str, Any]:
    """
    Verify Ollama server is reachable and list available models (Ollama only).
    """
    url = f"{LLM_BASE_URL}/api/tags"
    r = requests.get(url, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()

def _call_openai(system_prompt: str, user_prompt: str, temperature: float, model: Optional[str] = None) -> str:
    url = f"{LLM_BASE_URL}/v1/chat/completions"
    payload = {
        "model": model or LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    r = requests.post(url, json=payload, headers=_headers(), timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def _call_ollama(system_prompt: str, user_prompt: str, temperature: float, model: Optional[str] = None) -> str:
    url = f"{LLM_BASE_URL}/api/chat"
    payload = {
        "model": model or LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": temperature},
        "stream": False,
    }
    r = requests.post(url, json=payload, headers=_headers(), timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2, model: Optional[str] = None) -> str:
    """
    Main entrypoint used by EPOS workers.
    """
    mode = LLM_MODE
    if mode == "openai":
        return _call_openai(system_prompt, user_prompt, temperature, model=model)
    if mode == "ollama":
        return _call_ollama(system_prompt, user_prompt, temperature, model=model)

    # auto
    try:
        return _call_openai(system_prompt, user_prompt, temperature, model=model)
    except Exception:
        return _call_ollama(system_prompt, user_prompt, temperature, model=model)
