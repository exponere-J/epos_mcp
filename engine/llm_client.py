#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
# File: ${EPOS_ROOT}/engine/llm_client.py
"""
engine/llm_client.py — Unified LLM client with 3 runtime modes
================================================================
Constitutional Authority: EPOS Constitution v3.1
File: C:/Users/Jamie/workspace/epos_mcp/engine/llm_client.py

Modes (selected via LLM_MODE env var):
    groq_direct   (default) — routes through groq_router.GroqRouter
    litellm_proxy          — routes through localhost:4000 (OpenAI-compatible)
    ollama_direct          — routes through localhost:11434 /api/chat

Public API:
    ping()                                  -> dict (status + mode + backend info)
    complete(model, system, messages, ...)  -> str  (full response text)
    stream(model, system, messages, ...)    -> iterator[str] (chunks)

Usage:
    from engine.llm_client import ping, complete
    print(ping())
    print(complete("llama-3.3-70b-versatile", "You are terse.", [{"role":"user","content":"hi"}]))
"""

from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import requests

# Load .env if present (do not crash if dotenv missing)
try:
    from dotenv import load_dotenv
    _ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(_ROOT / ".env")
except Exception:
    pass


# ── Configuration ──────────────────────────────────────────────

LLM_MODE = os.getenv("LLM_MODE", "groq_direct").lower().strip()
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", os.getenv("LITELLM_URL", "http://litellm:4000")).rstrip("/")
LITELLM_API_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-epos-local-proxy")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434").rstrip("/")

DEFAULT_MODEL_BY_MODE = {
    "groq_direct":   os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile"),
    "litellm_proxy": os.getenv("LITELLM_DEFAULT_MODEL", "qwen3-32b"),
    "ollama_direct": os.getenv("OLLAMA_DEFAULT_MODEL", "phi3:mini"),
}

VALID_MODES = {"groq_direct", "litellm_proxy", "ollama_direct"}


def _mode() -> str:
    if LLM_MODE not in VALID_MODES:
        raise ValueError(
            f"LLM_MODE='{LLM_MODE}' invalid. Must be one of: {sorted(VALID_MODES)}"
        )
    return LLM_MODE


def _default_model() -> str:
    return DEFAULT_MODEL_BY_MODE[_mode()]


def _normalize_messages(
    system: Optional[str],
    messages: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    if system:
        out.append({"role": "system", "content": system})
    out.extend(messages or [])
    return out


# ── ping() ─────────────────────────────────────────────────────

def ping() -> Dict[str, Any]:
    """Check reachability of the active backend. Returns status dict."""
    mode = _mode()
    started = time.time()
    info: Dict[str, Any] = {"mode": mode, "ok": False}

    try:
        if mode == "groq_direct":
            # Import lazily so unrelated modes do not require groq.
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from groq_router import GroqRouter  # noqa: E402
            router = GroqRouter()
            info["backend"] = "groq"
            info["api_key_present"] = bool(router.api_key)
            info["default_model"] = _default_model()
            info["ok"] = bool(router.api_key)

        elif mode == "litellm_proxy":
            url = f"{LITELLM_BASE_URL}/health/liveliness"
            try:
                r = requests.get(url, timeout=5)
                info["status_code"] = r.status_code
                info["ok"] = r.status_code == 200
            except Exception:
                # Fallback: hit /v1/models which every proxy exposes
                r = requests.get(
                    f"{LITELLM_BASE_URL}/v1/models",
                    headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
                    timeout=5,
                )
                info["status_code"] = r.status_code
                info["ok"] = r.status_code == 200
                if info["ok"]:
                    info["models"] = [m.get("id") for m in r.json().get("data", [])][:10]
            info["backend"] = LITELLM_BASE_URL
            info["default_model"] = _default_model()

        elif mode == "ollama_direct":
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            info["backend"] = OLLAMA_HOST
            info["status_code"] = r.status_code
            info["ok"] = r.status_code == 200
            if info["ok"]:
                info["models"] = [m.get("name") for m in r.json().get("models", [])][:10]
            info["default_model"] = _default_model()

    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"

    info["latency_ms"] = int((time.time() - started) * 1000)
    return info


# ── complete() ─────────────────────────────────────────────────

def complete(
    model: Optional[str] = None,
    system: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 120,
) -> str:
    """
    Run a non-streaming completion. Returns the assistant response text.
    `messages` follows OpenAI chat format: [{"role":"user","content":"..."}].
    """
    if messages is None:
        messages = []
    model = model or _default_model()
    mode = _mode()
    msgs = _normalize_messages(system, messages)

    if mode == "groq_direct":
        # groq_router handles retries + fallback itself.
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from groq_router import GroqRouter  # noqa: E402
        router = GroqRouter()
        # GroqRouter.route expects single prompt + system; collapse chat history.
        user_prompt = _collapse_user_messages(messages)
        task_type = "reasoning"  # default — downstream can override via model
        # If caller passed a known task_type via `model`, respect it.
        if model in router.TASK_MODEL_MAP:
            task_type = model
        return router.route(
            task_type=task_type,
            prompt=user_prompt,
            system_prompt=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    if mode == "litellm_proxy":
        url = f"{LITELLM_BASE_URL}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {LITELLM_API_KEY}",
            "Content-Type": "application/json",
        }
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"] or ""

    if mode == "ollama_direct":
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": model,
            "messages": msgs,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return (data.get("message") or {}).get("content", "")

    raise RuntimeError(f"Unreachable: mode={mode}")


# ── stream() ───────────────────────────────────────────────────

def stream(
    model: Optional[str] = None,
    system: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 300,
) -> Iterator[str]:
    """
    Stream a completion as an iterator of text chunks.
    groq_direct yields the full response as a single chunk (no native streaming in router).
    """
    if messages is None:
        messages = []
    model = model or _default_model()
    mode = _mode()
    msgs = _normalize_messages(system, messages)

    if mode == "groq_direct":
        text = complete(
            model=model, system=system, messages=messages,
            temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        )
        yield text
        return

    if mode == "litellm_proxy":
        url = f"{LITELLM_BASE_URL}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {LITELLM_API_KEY}",
            "Content-Type": "application/json",
        }
        with requests.post(url, headers=headers, json=payload, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            for raw in r.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                body = raw[5:].strip()
                if body == "[DONE]":
                    break
                try:
                    obj = json.loads(body)
                    delta = obj["choices"][0].get("delta", {})
                    chunk = delta.get("content")
                    if chunk:
                        yield chunk
                except Exception:
                    continue
        return

    if mode == "ollama_direct":
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": model,
            "messages": msgs,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        with requests.post(url, json=payload, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    msg = obj.get("message") or {}
                    chunk = msg.get("content")
                    if chunk:
                        yield chunk
                    if obj.get("done"):
                        break
                except Exception:
                    continue
        return

    raise RuntimeError(f"Unreachable: mode={mode}")


# ── helpers ────────────────────────────────────────────────────

def _collapse_user_messages(messages: List[Dict[str, str]]) -> str:
    """Flatten a chat history into a single user-visible prompt for groq_router."""
    parts: List[str] = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        if role == "user":
            parts.append(content)
        elif role == "assistant":
            parts.append(f"[previous assistant reply] {content}")
        elif role == "system":
            # system prompt handled separately; skip here
            continue
        else:
            parts.append(f"[{role}] {content}")
    return "\n\n".join(parts) if parts else ""


# ── self-test ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("LLM_MODE =", _mode())
    result = ping()
    print("ping:", json.dumps(result, indent=2, default=str))
    if result.get("ok"):
        try:
            text = complete(
                system="You answer in one word.",
                messages=[{"role": "user", "content": "Say READY and nothing else."}],
                max_tokens=20,
                temperature=0.0,
            )
            print("complete:", repr(text[:120]))
        except Exception as e:
            print("complete failed:", e)
