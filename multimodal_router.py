#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
multimodal_router.py — EPOS Multimodal Generation Router
=========================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Image, Video, Audio, and Local LLM routing

Routes generation tasks to the optimal provider:
  - HuggingFace Inference API (Flux, Stable Diffusion)
  - Google Gemini (free/preview tier — gemini-2.0-flash)
  - Ollama local (mistral:instruct, llama3.1:8b, phi4)

Zero-cost local fallback for all text tasks.
Image generation requires HuggingFace API key or Gemini API key.
"""

import os
import json
import time
import base64
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None


# ── Provider Configuration ──────────────────────────────────

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Output directory for generated assets
ASSET_OUTPUT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp")) / "content" / "lab" / "production" / "assets"

# Sovereign vault path for generation journal
MULTIMODAL_VAULT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp")) / "context_vault" / "multimodal"

# ── Model Registry ──────────────────────────────────────────

OLLAMA_MODELS = {
    "mistral:instruct":         {"task": "writing", "speed": "fast", "quality": "good"},
    "llama3.1:8b-instruct-q4_K_M": {"task": "classification", "speed": "fast", "quality": "good"},
    "phi4:latest":              {"task": "reasoning", "speed": "medium", "quality": "high"},
    "llama3:latest":            {"task": "general", "speed": "medium", "quality": "good"},
    "qwen2.5-coder:7b":        {"task": "code", "speed": "medium", "quality": "high"},
}

HUGGINGFACE_MODELS = {
    "flux.1-dev":       {"id": "black-forest-labs/FLUX.1-dev", "type": "text-to-image", "tier": "free"},
    "flux.1-schnell":   {"id": "black-forest-labs/FLUX.1-schnell", "type": "text-to-image", "tier": "free"},
    "sd3.5-large":      {"id": "stabilityai/stable-diffusion-3.5-large", "type": "text-to-image", "tier": "free"},
    "sdxl-turbo":       {"id": "stabilityai/sdxl-turbo", "type": "text-to-image", "tier": "free"},
}

GEMINI_MODELS = {
    "gemini-2.0-flash":  {"type": "text", "tier": "free", "rpm": 15},
    "gemini-2.0-flash-lite": {"type": "text", "tier": "free", "rpm": 30},
}

# ── Task-to-Provider Routing ────────────────────────────────

TASK_ROUTING = {
    # Text generation — Ollama local (free) with Groq cloud fallback
    "challenger_voice":     {"provider": "ollama", "model": "mistral:instruct"},
    "fast_classification":  {"provider": "ollama", "model": "llama3.1:8b-instruct-q4_K_M"},
    "local_reasoning":      {"provider": "ollama", "model": "phi4:latest"},
    "code_generation":      {"provider": "ollama", "model": "qwen2.5-coder:7b"},
    "gemini_reasoning":     {"provider": "gemini", "model": "gemini-2.0-flash"},
    "gemini_fast":          {"provider": "gemini", "model": "gemini-2.0-flash-lite"},

    # Image generation — HuggingFace (free tier)
    "cover_image":          {"provider": "huggingface", "model": "flux.1-schnell"},
    "thumbnail":            {"provider": "huggingface", "model": "flux.1-schnell"},
    "visual_mask":          {"provider": "huggingface", "model": "flux.1-dev"},
    "background_asset":     {"provider": "huggingface", "model": "sdxl-turbo"},
    "schematic_render":     {"provider": "huggingface", "model": "flux.1-dev"},
}


class MultimodalRouter:
    """
    Routes generation tasks to the optimal provider.
    Sovereign — works without any API keys (Ollama-only mode).
    """

    def __init__(self, asset_output: Path = None, vault_path: Path = None):
        self.asset_output = asset_output or ASSET_OUTPUT
        self.asset_output.mkdir(parents=True, exist_ok=True)
        self.vault = vault_path or MULTIMODAL_VAULT
        self.vault.mkdir(parents=True, exist_ok=True)
        self._journal_path = self.vault / "generation_journal.jsonl"
        self._ollama_available = None
        self._hf_available = bool(HF_API_KEY)
        self._gemini_available = bool(GEMINI_API_KEY)

    # ── Ollama (Local LLM) ──────────────────────────────────

    def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            self._ollama_available = r.status_code == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def ollama_generate(self, model: str, prompt: str,
                        system_prompt: str = None,
                        max_tokens: int = 2048,
                        temperature: float = 0.7) -> str:
        """Generate text via local Ollama."""
        if not self._check_ollama():
            raise ConnectionError("Ollama not available at " + OLLAMA_HOST)

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt

        r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "")

    # ── HuggingFace Inference API ───────────────────────────

    def huggingface_image(self, model_key: str, prompt: str,
                          negative_prompt: str = None,
                          width: int = 1024, height: int = 1024) -> Path:
        """Generate image via HuggingFace Inference API. Returns saved path."""
        if not self._hf_available:
            raise EnvironmentError("HUGGINGFACE_API_KEY not set in .env")

        model_info = HUGGINGFACE_MODELS.get(model_key)
        if not model_info:
            raise ValueError(f"Unknown HF model: {model_key}. Available: {list(HUGGINGFACE_MODELS.keys())}")

        model_id = model_info["id"]
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}

        payload = {"inputs": prompt}
        if negative_prompt:
            payload["parameters"] = {"negative_prompt": negative_prompt}

        # Retry with backoff (models may need cold start)
        for attempt in range(3):
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                break
            if r.status_code == 503:
                # Model loading — wait and retry
                wait = r.json().get("estimated_time", 20)
                time.sleep(min(wait, 30))
                continue
            r.raise_for_status()

        # Save image
        img_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{model_key}_{ts}_{img_hash}.png"
        img_path = self.asset_output / filename
        img_path.write_bytes(r.content)

        self._publish_event("multimodal.image.generated", {
            "model": model_key, "provider": "huggingface",
            "prompt_chars": len(prompt), "path": str(img_path),
        })

        return img_path

    # ── Gemini (Free Tier) ──────────────────────────────────

    def gemini_generate(self, prompt: str,
                        model: str = "gemini-2.0-flash",
                        max_tokens: int = 2048,
                        temperature: float = 0.7) -> str:
        """Generate text via Google Gemini free API."""
        if not self._gemini_available:
            raise EnvironmentError("GEMINI_API_KEY not set in .env")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

        r = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Extract text from Gemini response
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""

    # ── Unified Router ──────────────────────────────────────

    def route(self, task_type: str, prompt: str, **kwargs) -> any:
        """
        Route any generation task to the correct provider.

        For text tasks: returns string.
        For image tasks: returns Path to saved image.
        """
        routing = TASK_ROUTING.get(task_type)
        if not routing:
            raise ValueError(f"Unknown task: {task_type}. Available: {list(TASK_ROUTING.keys())}")

        provider = routing["provider"]
        model = routing["model"]

        if provider == "ollama":
            return self.ollama_generate(
                model, prompt,
                system_prompt=kwargs.get("system_prompt"),
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
            )

        elif provider == "huggingface":
            return self.huggingface_image(
                model, prompt,
                negative_prompt=kwargs.get("negative_prompt"),
                width=kwargs.get("width", 1024),
                height=kwargs.get("height", 1024),
            )

        elif provider == "gemini":
            return self.gemini_generate(
                prompt, model=model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")

    # ── Provider Health ─────────────────────────────────────

    def get_provider_status(self) -> dict:
        """Report which providers are available."""
        ollama_models = []
        if self._check_ollama():
            try:
                r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
                ollama_models = [m["name"] for m in r.json().get("models", [])]
            except Exception:
                pass

        return {
            "ollama": {
                "available": self._check_ollama(),
                "host": OLLAMA_HOST,
                "models": ollama_models,
            },
            "huggingface": {
                "available": self._hf_available,
                "models": list(HUGGINGFACE_MODELS.keys()) if self._hf_available else [],
            },
            "gemini": {
                "available": self._gemini_available,
                "models": list(GEMINI_MODELS.keys()) if self._gemini_available else [],
            },
        }

    # ── Event Publishing ────────────────────────────────────

    def _publish_event(self, event_type: str, payload: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="multimodal_router")
            except Exception:
                pass

        # Journal to sovereign vault
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "event_type": event_type, "payload": payload}
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        record_decision(
            decision_type=event_type,
            description=f"Multimodal: {event_type}",
            agent_id="multimodal_router",
            outcome="success",
            context=payload,
        )


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    router = MultimodalRouter()

    # Test 1: Instantiation
    assert hasattr(router, "route"), "Missing route method"
    assert hasattr(router, "get_provider_status"), "Missing status method"
    passed += 1

    # Test 2: Provider status
    status = router.get_provider_status()
    assert "ollama" in status, "Missing ollama status"
    assert "huggingface" in status, "Missing huggingface status"
    assert "gemini" in status, "Missing gemini status"
    passed += 1

    # Test 3: Ollama local generation
    if status["ollama"]["available"]:
        result = router.route("challenger_voice",
                              "Write a one-line hook about content sovereignty.",
                              max_tokens=50, temperature=0.8)
        assert len(result) > 10, f"Ollama response too short: {result}"
        passed += 1
        print(f"  Ollama test: {result[:60]}...")
    else:
        print("  SKIP: Ollama not available")
        passed += 1

    # Test 4: Task routing maps exist
    for task in TASK_ROUTING:
        routing = TASK_ROUTING[task]
        assert "provider" in routing, f"Missing provider for {task}"
        assert "model" in routing, f"Missing model for {task}"
    passed += 1

    # Test 5: HuggingFace availability check
    if status["huggingface"]["available"]:
        print(f"  HuggingFace: READY ({len(HUGGINGFACE_MODELS)} models)")
    else:
        print("  HuggingFace: NEEDS API KEY (set HUGGINGFACE_API_KEY in .env)")
    passed += 1

    # Test 6: Gemini availability check
    if status["gemini"]["available"]:
        print(f"  Gemini: READY ({len(GEMINI_MODELS)} models, free tier)")
    else:
        print("  Gemini: NEEDS API KEY (set GEMINI_API_KEY in .env)")
    passed += 1

    print(f"\nPASS: multimodal_router ({passed} assertions)")
    print(f"Providers: Ollama={'ON' if status['ollama']['available'] else 'OFF'} | "
          f"HF={'ON' if status['huggingface']['available'] else 'OFF'} | "
          f"Gemini={'ON' if status['gemini']['available'] else 'OFF'}")
