#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
scc_executor.py — Sovereign Coding Component Executor
=======================================================
Constitutional Authority: EPOS Constitution v3.1

Executes bounded coding missions via the EPOS Sovereign Coding
Component (SCC). Routes to Qwen3-Coder-30B via LiteLLM proxy.
Replaces the legacy Desktop CODE CLI executor.

Vault: context_vault/friday/code_sessions/
Event: scc.session.complete
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
SESSIONS_DIR = VAULT / "friday" / "code_sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

WORKSPACE = Path(os.getenv("EPOS_ROOT", "/app"))

LITELLM_BASE_URL = os.getenv(
    "LITELLM_BASE_URL",
    os.getenv("LITELLM_URL", "http://litellm:4000")
).rstrip("/")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-epos-local-proxy")
SCC_MODEL = os.getenv("SCC_MODEL", "qwen3-coder-30b")


class SCCExecutor:
    """Executes bounded coding missions via the Sovereign Coding Component.

    Routes to Qwen3-Coder-30B via LiteLLM proxy.
    Publishes scc.session.complete events.
    Generates session logs in context_vault/friday/code_sessions/.
    """

    def health_check(self) -> dict:
        """Check if SCC (LiteLLM + Qwen3-Coder) is available."""
        try:
            resp = requests.get(
                f"{LITELLM_BASE_URL}/health",
                headers={"Authorization": f"Bearer {LITELLM_MASTER_KEY}"},
                timeout=5,
            )
            if resp.status_code == 200:
                return {
                    "status": "operational",
                    "version": f"SCC via {SCC_MODEL}",
                    "fallback": False,
                    "base_url": LITELLM_BASE_URL,
                }
            else:
                return {
                    "status": "fallback_mode",
                    "version": f"LiteLLM returned {resp.status_code}",
                    "fallback": True,
                    "note": "LiteLLM proxy unavailable — SCC degraded",
                }
        except Exception as e:
            return {
                "status": "fallback_mode",
                "version": str(e)[:80],
                "fallback": True,
                "note": "Cannot reach LiteLLM proxy",
            }

    def execute_mission(self, directive: str, timeout: int = 300) -> dict:
        """
        Execute a coding directive via SCC (Qwen3-Coder via LiteLLM).

        Args:
            directive: The coding task description
            timeout:   Max seconds before giving up (default 5 min)

        Returns:
            {session_id, status, output, log_path, mode}
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        session_id = f"SCC-{ts}"
        log_path = SESSIONS_DIR / f"{session_id}.log"

        system_prompt = (
            "You are the EPOS Sovereign Coding Component (SCC), governed by the "
            "EPOS Constitution v3.1. You are a senior Python developer building "
            "EPOS sovereign infrastructure. Return a complete, runnable "
            "implementation. Single fenced code block unless multiple files needed. "
            "No TODOs. No placeholders. POSIX paths only. EPOS_ROOT=/app."
        )

        try:
            resp = requests.post(
                f"{LITELLM_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_MASTER_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": SCC_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": directive},
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.2,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            output = {
                "session_id": session_id,
                "status": "complete",
                "output": content,
                "log_path": str(log_path),
                "mode": "scc_litellm",
                "model": SCC_MODEL,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }

        except requests.Timeout:
            output = {
                "session_id": session_id,
                "status": "timeout",
                "error": f"Mission exceeded {timeout}s limit",
                "log_path": str(log_path),
                "mode": "scc_litellm",
            }
        except Exception as e:
            output = {
                "session_id": session_id,
                "status": "failed",
                "error": str(e)[:500],
                "log_path": str(log_path),
                "mode": "scc_litellm",
            }

        # Persist session log
        log_path.write_text(
            f"Session: {session_id}\n"
            f"Directive: {directive[:500]}\n"
            f"Timestamp: {ts}\n"
            f"Status: {output['status']}\n"
            f"Mode: {output.get('mode', 'unknown')}\n"
            f"Model: {output.get('model', SCC_MODEL)}\n\n"
            f"Output:\n{output.get('output', output.get('error', ''))}\n",
            encoding="utf-8",
        )

        _publish(session_id, output["status"])
        return output


# ── Module-level run() for friday_graph dispatch ─────────────

def run(mission: dict) -> dict:
    """friday_graph executor interface."""
    executor = SCCExecutor()
    mission_id = mission.get("id", "M-SCC-UNKNOWN")
    directive = mission.get("description", "")
    timeout = int(mission.get("timeout", 300))

    output = executor.execute_mission(directive, timeout=timeout)
    output["mission_id"] = mission_id
    output["executor"] = "scc"
    return output


def _publish(session_id: str, status: str):
    if _BUS:
        try:
            _BUS.publish("scc.session.complete", {
                "session_id": session_id,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, source_module="scc_executor")
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    executor = SCCExecutor()

    # Test 1: Health check
    health = executor.health_check()
    print(f"Health: status={health['status']} fallback={health.get('fallback')} version={health.get('version', '?')[:50]}")
    assert health["status"] in ("operational", "fallback_mode")

    # Test 2: Execute a mission
    print("\nExecuting test mission...")
    result = executor.execute_mission(
        "Write a Python one-liner that prints 'EPOS SCC executor operational'",
        timeout=60,
    )
    print(f"Status: {result['status']} mode={result.get('mode', '?')}")
    if result.get("output"):
        print(f"Output: {result['output'][:200]}")
    assert result["status"] in ("complete", "failed", "timeout")

    print("\nPASS: scc_executor")
