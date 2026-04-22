#!/usr/bin/env python3
"""
groq_router.py — EPOS Groq Model Router
=========================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/groq_router.py
# EPOS GOVERNANCE WATERMARK

Routes LLM tasks to the correct Groq model based on task type.
Centralizes model selection — all modules call GroqRouter instead
of picking models ad-hoc.

MODEL ASSIGNMENT MATRIX:
  reasoning / scripting / analysis → llama-3.3-70b-versatile
  classification / tagging / routing → llama-3.1-8b-instant
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_intelligence import record_decision


class GroqRouter:
    """
    Centralized Groq model routing.
    Maps task types to optimal models.
    Logs every completion to epos_intelligence.
    """

    TASK_MODEL_MAP = {
        "scripting":        "llama-3.3-70b-versatile",
        "analysis":         "llama-3.3-70b-versatile",
        "reasoning":        "llama-3.3-70b-versatile",
        "governance":       "llama-3.3-70b-versatile",
        "constitutional":   "llama-3.3-70b-versatile",
        "hook_generation":  "llama-3.3-70b-versatile",
        "classification":   "llama-3.1-8b-instant",
        "tagging":          "llama-3.1-8b-instant",
        "routing":          "llama-3.1-8b-instant",
        "summarization":    "llama-3.1-8b-instant",
        "caption":          "llama-3.1-8b-instant",
        "seo":              "llama-3.1-8b-instant",
    }

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GROQ_API_KEY not found in .env")
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError("groq library not installed. Run: pip install groq")

    FALLBACK_MODEL = "llama-3.1-8b-instant"
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 2.0  # seconds

    def route(
        self,
        task_type: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Route task to correct model. Execute. Return text response.
        Logs to epos_intelligence.
        On rate limit: retries with exponential backoff, then falls back to 8b model.
        """
        model = self.TASK_MODEL_MAP.get(task_type, "llama-3.3-70b-versatile")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result, used_model = self._call_with_retry(model, messages, max_tokens, temperature)

        record_decision(
            decision_type="groq.completion",
            description=f"Groq {task_type} via {used_model}",
            agent_id="groq_router",
            outcome="success",
            context={
                "task_type": task_type,
                "model": used_model,
                "requested_model": model,
                "fallback_used": used_model != model,
                "prompt_chars": len(prompt),
                "response_chars": len(result),
            },
        )
        return result

    def _call_with_retry(
        self,
        model: str,
        messages: list,
        max_tokens: int,
        temperature: float,
    ) -> tuple:
        """
        Attempt completion with retries and fallback.
        Returns (result_text, model_used).
        """
        from groq import RateLimitError

        last_error = None
        # Try primary model with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content, model
            except RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)

        # Fallback to 8b model if primary was different
        if model != self.FALLBACK_MODEL:
            try:
                response = self.client.chat.completions.create(
                    model=self.FALLBACK_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content, self.FALLBACK_MODEL
            except Exception:
                pass  # Fall through to Ollama

        # Final fallback: Ollama local (sovereign — $0, no API dependency)
        ollama_result = self._ollama_fallback(messages, max_tokens, temperature)
        if ollama_result:
            return ollama_result

        raise last_error

    def _ollama_fallback(self, messages: list, max_tokens: int, temperature: float):
        """Last-resort fallback to local Ollama. Returns (text, model) or None."""
        import requests
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        ollama_model = os.getenv("OLLAMA_FALLBACK_MODEL", "mistral:instruct")
        try:
            # Convert chat messages to single prompt
            prompt_parts = []
            for m in messages:
                if m["role"] == "system":
                    prompt_parts.append(f"[System] {m['content']}")
                else:
                    prompt_parts.append(m["content"])
            prompt = "\n\n".join(prompt_parts)

            r = requests.post(f"{ollama_host}/api/generate", json={
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            }, timeout=120)
            if r.status_code == 200:
                text = r.json().get("response", "")
                if text:
                    return text, f"ollama:{ollama_model}"
        except Exception:
            pass
        return None

    def get_model_for_task(self, task_type: str) -> str:
        """Return model name for a task type without executing."""
        return self.TASK_MODEL_MAP.get(task_type, "llama-3.3-70b-versatile")


if __name__ == "__main__":
    router = GroqRouter()

    # Test: classification
    result = router.route(
        "classification",
        "Classify this content: 'Top 5 LEGO sets under $50' — what hook type?",
        system_prompt="Return one word: question, list, how_to, controversy, story, statistic",
        max_tokens=10,
        temperature=0.1,
    )
    clean = result.strip().lower()
    # Extract the actual type word from potentially verbose response
    valid_types = ["question", "list", "how_to", "controversy", "story", "statistic"]
    matched = next((t for t in valid_types if t in clean), None)
    assert matched is not None, f"No valid type found in response: {result}"
    print(f"  Classification test: {matched} — PASS")

    # Test: model mapping
    assert router.get_model_for_task("scripting") == "llama-3.3-70b-versatile"
    assert router.get_model_for_task("classification") == "llama-3.1-8b-instant"
    print("  Model mapping: PASS")

    print("PASS: groq_router all self-tests passed")
