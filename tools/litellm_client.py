#!/usr/bin/env python3
"""
File: /mnt/c/Users/Jamie/workspace/epos_mcp/tools/litellm_client.py
Constitutional Authority: EPOS Constitution v3.1
Governed: True

EPOS LLM Client — Unified proxy for all LLM calls.

Routing priority:
  1. Ollama (local)     — free, private, no latency to cloud
  2. Groq (cloud fast)  — fast inference, rate-limited
  3. Error              — never silently returns empty

Model assignments:
  CODING tasks  → Ollama qwen2.5-coder:7b (local)
  FAST tasks    → Groq llama-3.1-8b-instant
  REASONING     → Groq llama-3.3-70b-versatile
  FALLBACK      → whatever is available

Usage:
    from tools.litellm_client import run_model, ModelTarget

    # Auto-routed (Ollama first, Groq fallback)
    result = run_model("Explain this code", target=ModelTarget.CODING)

    # Force specific backend
    result = run_model("Quick summary", target=ModelTarget.FAST)
"""

import os
import json
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

import litellm
from dotenv import load_dotenv

# ── Environment ──────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
GROQ_MODEL_REASONING = os.getenv("GROQ_MODEL_REASONING", "llama-3.3-70b-versatile")

# Absolute log path per Article II Rule 1
_EPOS_ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = _EPOS_ROOT / "logs" / "llm_calls.jsonl"
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)

# Suppress litellm noise
litellm.suppress_debug_info = True
os.environ["LITELLM_LOG"] = "ERROR"


# ── Model Targets ────────────────────────────────────────────

class ModelTarget(Enum):
    """Semantic model targets — mapped to actual models at runtime."""
    CODING = "coding"           # Best for code generation/review
    FAST = "fast"               # Fastest response, good enough quality
    REASONING = "reasoning"     # Deep analysis, complex tasks
    LOCAL = "local"             # Force local Ollama
    GROQ = "groq"              # Force Groq cloud


# Model routing table
_MODEL_MAP = {
    ModelTarget.CODING: [
        ("ollama/qwen2.5-coder:7b", "ollama"),
        (f"groq/{GROQ_MODEL_FAST}", "groq"),
    ],
    ModelTarget.FAST: [
        (f"groq/{GROQ_MODEL_FAST}", "groq"),
        ("ollama/phi3:mini", "ollama"),
    ],
    ModelTarget.REASONING: [
        (f"groq/{GROQ_MODEL_REASONING}", "groq"),
        ("ollama/phi4:latest", "ollama"),
    ],
    ModelTarget.LOCAL: [
        ("ollama/qwen2.5-coder:7b", "ollama"),
        ("ollama/phi4:latest", "ollama"),
    ],
    ModelTarget.GROQ: [
        (f"groq/{GROQ_MODEL_FAST}", "groq"),
        (f"groq/{GROQ_MODEL_REASONING}", "groq"),
    ],
}


# ── Backend Availability ─────────────────────────────────────

def _ollama_available() -> bool:
    """Check if Ollama is responding."""
    try:
        import requests
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _groq_available() -> bool:
    """Check if Groq API key is configured."""
    return bool(GROQ_API_KEY) and GROQ_API_KEY != "PASTE_YOUR_KEY_HERE"


def health_check() -> Dict[str, Any]:
    """Return status of all LLM backends."""
    ollama_ok = _ollama_available()
    groq_ok = _groq_available()

    # List Ollama models if available
    ollama_models = []
    if ollama_ok:
        try:
            import requests
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            ollama_models = [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass

    return {
        "ollama": {"available": ollama_ok, "host": OLLAMA_HOST, "models": ollama_models},
        "groq": {"available": groq_ok, "models": [GROQ_MODEL_FAST, GROQ_MODEL_REASONING]},
        "ready": ollama_ok or groq_ok,
    }


# ── Core LLM Call ────────────────────────────────────────────

def run_model(
    prompt: str,
    system_prompt: Optional[str] = None,
    target: ModelTarget = ModelTarget.CODING,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    max_retries: int = 2,
    timeout_seconds: int = 120,
    **kwargs,
) -> Dict[str, Any]:
    """
    Route an LLM call through the priority chain.

    Args:
        prompt: User message
        system_prompt: Optional system message
        target: ModelTarget enum — determines model routing
        temperature: Sampling temperature
        max_tokens: Maximum response tokens
        max_retries: Retries per backend before moving to fallback
        timeout_seconds: Per-call timeout

    Returns:
        {"status": "success"|"error", "text": str, "model": str,
         "backend": str, "latency_ms": int, "timestamp": str}
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    candidates = _MODEL_MAP.get(target, _MODEL_MAP[ModelTarget.CODING])

    # Filter to available backends
    ollama_ok = _ollama_available()
    groq_ok = _groq_available()

    for model_name, backend in candidates:
        if backend == "ollama" and not ollama_ok:
            continue
        if backend == "groq" and not groq_ok:
            continue

        # Attempt this model
        for attempt in range(max_retries):
            start = time.time()
            try:
                call_kwargs = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": timeout_seconds,
                    **kwargs,
                }

                if backend == "ollama":
                    call_kwargs["api_base"] = OLLAMA_HOST
                elif backend == "groq":
                    call_kwargs["api_key"] = GROQ_API_KEY

                response = litellm.completion(**call_kwargs)
                latency_ms = int((time.time() - start) * 1000)

                text = ""
                if hasattr(response, "choices") and len(response.choices) > 0:
                    text = response.choices[0].message.content or ""
                else:
                    text = str(response)

                result = {
                    "status": "success",
                    "text": text.strip(),
                    "model": model_name,
                    "backend": backend,
                    "latency_ms": latency_ms,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                _log_audit({
                    "action": "llm_call_success",
                    "model": model_name,
                    "backend": backend,
                    "target": target.value,
                    "latency_ms": latency_ms,
                    "text_length": len(text),
                    "attempt": attempt + 1,
                })
                return result

            except Exception as e:
                latency_ms = int((time.time() - start) * 1000)
                _log_audit({
                    "action": "llm_call_retry",
                    "model": model_name,
                    "backend": backend,
                    "error": str(e)[:200],
                    "attempt": attempt + 1,
                    "latency_ms": latency_ms,
                })
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

        # All retries exhausted for this model — try next in chain
        _log_audit({
            "action": "llm_backend_exhausted",
            "model": model_name,
            "backend": backend,
            "target": target.value,
        })

    # All candidates exhausted
    error_msg = (
        f"All LLM backends failed for target={target.value}. "
        f"Ollama={'up' if ollama_ok else 'down'}, "
        f"Groq={'configured' if groq_ok else 'no key'}"
    )
    _log_audit({"action": "llm_all_backends_failed", "target": target.value, "error": error_msg})

    return {
        "status": "error",
        "text": error_msg,
        "model": None,
        "backend": None,
        "latency_ms": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Audit Logging ────────────────────────────────────────────

def _log_audit(entry: Dict[str, Any]):
    """Append structured log entry to JSONL audit file."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass  # Audit logging must never crash the caller


# ── Self-Test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  EPOS LLM Client — Self-Test")
    print("=" * 60)

    # Health check
    h = health_check()
    print(f"\n  Ollama: {'ONLINE' if h['ollama']['available'] else 'OFFLINE'}")
    if h["ollama"]["available"]:
        print(f"    Models: {', '.join(h['ollama']['models'][:5])}")
    print(f"  Groq:   {'CONFIGURED' if h['groq']['available'] else 'NO KEY'}")
    print(f"  Ready:  {h['ready']}")

    if not h["ready"]:
        print("\n  ERROR: No LLM backends available. Cannot test.")
        exit(1)

    # Test 1: CODING target (Ollama qwen2.5-coder)
    print("\n  Test 1: CODING target...")
    r1 = run_model("Reply with exactly: READY", target=ModelTarget.CODING, temperature=0.1)
    print(f"    Status: {r1['status']}")
    print(f"    Model:  {r1['model']}")
    print(f"    Backend: {r1['backend']}")
    print(f"    Latency: {r1['latency_ms']}ms")
    print(f"    Response: {r1['text'][:80]}")
    assert r1["status"] == "success", f"CODING failed: {r1['text']}"

    # Test 2: FAST target (Groq)
    if h["groq"]["available"]:
        print("\n  Test 2: FAST target (Groq)...")
        r2 = run_model("Reply with exactly: FAST", target=ModelTarget.FAST, temperature=0.1)
        print(f"    Status: {r2['status']}")
        print(f"    Model:  {r2['model']}")
        print(f"    Backend: {r2['backend']}")
        print(f"    Latency: {r2['latency_ms']}ms")
        print(f"    Response: {r2['text'][:80]}")
        assert r2["status"] == "success", f"FAST failed: {r2['text']}"
    else:
        print("\n  Test 2: FAST — SKIPPED (no Groq key)")

    # Test 3: REASONING target
    if h["groq"]["available"]:
        print("\n  Test 3: REASONING target...")
        r3 = run_model("What is 2+2? Reply with just the number.", target=ModelTarget.REASONING, temperature=0.1)
        print(f"    Status: {r3['status']}")
        print(f"    Model:  {r3['model']}")
        print(f"    Latency: {r3['latency_ms']}ms")
        print(f"    Response: {r3['text'][:80]}")
        assert r3["status"] == "success"
    else:
        print("\n  Test 3: REASONING — SKIPPED")

    # Verify audit log exists
    assert AUDIT_LOG.exists(), f"Audit log not created at {AUDIT_LOG}"
    line_count = sum(1 for _ in open(AUDIT_LOG))
    print(f"\n  Audit log: {AUDIT_LOG} ({line_count} entries)")

    print("\n" + "=" * 60)
    print("  PASS: All LLM client tests passed")
    print("=" * 60)
