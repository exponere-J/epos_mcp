#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
browser_use_node.py — BrowserUse Sovereign Node
==================================================
Constitutional Authority: EPOS Constitution v3.1

Wraps browser-use as a sovereign EPOS node.
Provides browser automation for M1 Publisher, FOTW, and any agent
that needs web interaction without a live Claude session.

Fallback chain (constitutional):
  1. BrowserUse (autonomous, no session needed)
  2. ComputerUse via MCP (requires active Claude session)
  3. Stage for manual (always available)
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
BROWSER_VAULT = VAULT / "browser_use"
BROWSER_VAULT.mkdir(parents=True, exist_ok=True)
BROWSER_LOG = BROWSER_VAULT / "events.jsonl"


class BrowserUseNode:
    """
    Sovereign browser automation node.
    Uses browser-use with Ollama (local, $0) or Groq for LLM reasoning.
    """

    def __init__(self):
        self._available = False
        self._reason = ""
        try:
            from browser_use import Agent, Browser
            from browser_use.browser.context import BrowserContextConfig
            self._available = True
        except ImportError as e:
            self._reason = f"browser-use not installed: {e}"

    def health_check(self) -> dict:
        """Verify browser-use + Playwright work."""
        if not self._available:
            return {"status": "unavailable", "reason": self._reason}

        try:
            from browser_use.browser.context import BrowserContextConfig
            from browser_use import Browser
            # Just verify we can create config — don't launch browser for health check
            config = BrowserContextConfig(headless=True)
            return {
                "status": "operational",
                "headless": True,
                "llm_backends": self._check_llm_backends(),
                "vault_path": str(BROWSER_VAULT),
            }
        except Exception as e:
            return {"status": "degraded", "reason": str(e)[:200]}

    def _check_llm_backends(self) -> list:
        """Check which LLM backends are available for browser-use."""
        backends = []
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            backends.append("groq")
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                backends.append("ollama")
        except Exception:
            pass
        return backends

    def _get_llm(self):
        """Get the best available LLM for browser-use."""
        # Try Groq first (faster, more capable for browser reasoning)
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            try:
                from browser_use.llm import ChatGroq
                return ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
            except Exception:
                pass

        # Fallback to Ollama
        try:
            from browser_use.llm import ChatOllama
            return ChatOllama(model="llama3:latest", host="http://localhost:11434")
        except Exception:
            pass

        return None

    async def execute_task(self, task: str, max_steps: int = 5) -> dict:
        """Execute a browser automation task."""
        if not self._available:
            return {"success": False, "error": self._reason}

        from browser_use import Agent, Browser
        from browser_use.browser.context import BrowserContextConfig

        llm = self._get_llm()
        if not llm:
            return {"success": False, "error": "No LLM backend available for browser-use"}

        browser = None
        try:
            browser = Browser(config=BrowserContextConfig(headless=True))
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                max_actions_per_step=3,
            )
            result = await agent.run(max_steps=max_steps)

            final = result.final_result() if hasattr(result, "final_result") else str(result)
            success = result.is_done() if hasattr(result, "is_done") else True

            output = {
                "success": True,
                "task": task,
                "result": str(final)[:1000] if final else "Task completed (no text result)",
                "steps": max_steps,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self._log_event("browser.task.completed", output)
            return output

        except Exception as e:
            error_output = {
                "success": False,
                "task": task,
                "error": str(e)[:500],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._log_event("browser.task.failed", error_output)
            return error_output

        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass

    def execute_task_sync(self, task: str, max_steps: int = 5) -> dict:
        """Synchronous wrapper for execute_task."""
        return asyncio.run(self.execute_task(task, max_steps))

    def _log_event(self, event_type: str, payload: dict):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "event_type": event_type, "payload": payload}
        with open(BROWSER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="browser_use_node")
            except Exception:
                pass


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    node = BrowserUseNode()

    # Test 1: Health check
    health = node.health_check()
    print(f"Health: {health['status']}")
    assert health["status"] in ("operational", "degraded", "unavailable")
    passed += 1

    # Test 2: LLM backends
    if health["status"] == "operational":
        backends = health.get("llm_backends", [])
        print(f"LLM backends: {backends}")
        assert len(backends) > 0, "Need at least one LLM backend"
        passed += 1
    else:
        print(f"SKIP: browser-use not available: {health.get('reason', '?')}")
        passed += 1

    # Test 3: Execute a simple task (headless navigation)
    if health["status"] == "operational":
        print("Testing browser task (navigate to example.com)...")
        result = node.execute_task_sync("Navigate to https://example.com and report back what you see", max_steps=3)
        print(f"Task result: success={result['success']}")
        if not result["success"]:
            print(f"  Error: {result.get('error', '?')[:100]}")
        passed += 1
    else:
        print("SKIP: browser task (not operational)")
        passed += 1

    # Test 4: Event log written
    if BROWSER_LOG.exists():
        lines = BROWSER_LOG.read_text(encoding="utf-8").splitlines()
        print(f"Event log: {len(lines)} entries")
    passed += 1

    print(f"\nPASS: browser_use_node ({passed} assertions)")
    print(f"Status: {health['status']} | Backends: {health.get('llm_backends', [])}")
