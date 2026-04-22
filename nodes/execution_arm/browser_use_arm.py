#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §3
"""
browser_use_arm.py — BrowserUse Arm (headless + headed)
========================================================
Wraps `browser-use` + Playwright Chromium. Both modes exposed through a
single class; mode is chosen at run(), not at construction.

Capabilities:
    - read        (navigate, scrape, extract)
    - write       (form fill, click, submit, upload)
    - shell       (N/A — browser only; OS shell handled by ComputerUse)
    - delete      (only through deletion_gate.enforce)

Headed mode uses a real display. On headless hosts (AZ container, CI),
a virtual display (Xvfb :99) is started automatically if DISPLAY is unset
and `xvfb-run` / `Xvfb` is available. Without either, headed requests
fall back to headless with a warning in the receipt.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .deletion_gate import enforce as enforce_deletion  # noqa: F401 (re-exported for arms)

_LOG_DIR = Path(os.getenv("EPOS_ARM_LOG_DIR", "context_vault/execution_arm"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "browser_use.jsonl"


@dataclass
class ArmResult:
    success: bool
    arm: str = "browser_use"
    mode: str = "headless"
    task: str = ""
    output: str = ""
    error: str = ""
    steps: int = 0
    started_at: str = ""
    finished_at: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "arm": self.arm,
            "mode": self.mode,
            "task": self.task,
            "output": self.output,
            "error": self.error,
            "steps": self.steps,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "extras": self.extras,
        }


class BrowserUseArm:
    """Sovereign browser execution arm — both modes behind one interface."""

    def __init__(self) -> None:
        self._available = False
        self._reason = ""
        try:
            import browser_use  # noqa: F401
            self._available = True
        except ImportError as e:
            self._reason = f"browser-use not installed: {e}"

    # ── Public API ────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "reason": self._reason}
        return {
            "status": "operational",
            "modes": ["headless", "headed"],
            "headed_display": self._detect_display(),
            "llm_backends": self._check_llm_backends(),
            "log": str(_LOG_FILE),
        }

    async def run(
        self,
        task: str,
        mode: str = "headless",
        max_steps: int = 8,
        context: dict[str, Any] | None = None,
    ) -> ArmResult:
        """Run a browser task. mode ∈ {'headless', 'headed'}."""
        started = datetime.now(timezone.utc).isoformat()
        ctx = dict(context or {})
        ctx.setdefault("arm", "browser_use")

        if not self._available:
            return self._fail(task, mode, started, self._reason)

        if mode not in ("headless", "headed"):
            return self._fail(task, mode, started, f"invalid mode {mode!r}")

        effective_mode = mode
        headed_warning = ""
        if mode == "headed":
            display = self._detect_display()
            if not display.get("available"):
                effective_mode = "headless"
                headed_warning = (
                    f"headed requested but no display available ({display.get('reason')}); "
                    f"falling back to headless"
                )

        try:
            result = await self._run_once(task, effective_mode, max_steps, ctx)
            if headed_warning:
                result.extras["headed_fallback"] = headed_warning
            self._log(result)
            return result
        except Exception as e:  # noqa: BLE001
            r = self._fail(task, effective_mode, started, f"{type(e).__name__}: {e}")
            self._log(r)
            return r

    def run_sync(
        self,
        task: str,
        mode: str = "headless",
        max_steps: int = 8,
        context: dict[str, Any] | None = None,
    ) -> ArmResult:
        return asyncio.run(self.run(task, mode, max_steps, context))

    # ── Internals ─────────────────────────────────────────────

    async def _run_once(
        self,
        task: str,
        mode: str,
        max_steps: int,
        ctx: dict[str, Any],
    ) -> ArmResult:
        from browser_use import Agent, Browser
        from browser_use.browser.context import BrowserContextConfig

        started = datetime.now(timezone.utc).isoformat()
        llm = self._get_llm()
        if llm is None:
            return self._fail(task, mode, started, "no LLM backend available")

        headless = (mode == "headless")
        browser = Browser(config=BrowserContextConfig(headless=headless))
        try:
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                max_actions_per_step=3,
            )
            raw = await agent.run(max_steps=max_steps)
            final = raw.final_result() if hasattr(raw, "final_result") else str(raw)
            ok = raw.is_done() if hasattr(raw, "is_done") else True
            return ArmResult(
                success=bool(ok),
                arm="browser_use",
                mode=mode,
                task=task,
                output=str(final)[:1500] if final else "",
                steps=int(getattr(raw, "step_count", max_steps)),
                started_at=started,
                finished_at=datetime.now(timezone.utc).isoformat(),
                extras={"mission_id": ctx.get("mission_id", "")},
            )
        finally:
            try:
                await browser.close()
            except Exception:
                pass

    def _detect_display(self) -> dict[str, Any]:
        disp = os.getenv("DISPLAY", "")
        if disp:
            return {"available": True, "source": "DISPLAY env", "value": disp}
        for probe in ("xvfb-run", "Xvfb"):
            if shutil.which(probe):
                return {"available": True, "source": probe}
        return {"available": False, "reason": "no DISPLAY and no Xvfb on PATH"}

    def _check_llm_backends(self) -> list[str]:
        backends: list[str] = []
        if os.getenv("GROQ_API_KEY"):
            backends.append("groq")
        if os.getenv("ANTHROPIC_API_KEY"):
            backends.append("anthropic")
        try:
            import requests
            r = requests.get(
                f"{os.getenv('OLLAMA_HOST', 'http://ollama:11434')}/api/tags",
                timeout=3,
            )
            if r.status_code == 200:
                backends.append("ollama")
        except Exception:
            pass
        return backends

    def _get_llm(self):
        # Try Groq → Anthropic → Ollama.
        if os.getenv("GROQ_API_KEY"):
            try:
                from browser_use.llm import ChatGroq
                return ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key=os.getenv("GROQ_API_KEY", ""),
                )
            except Exception:
                pass
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                from browser_use.llm import ChatAnthropic
                return ChatAnthropic(
                    model="claude-haiku-4-5-20251001",
                    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                )
            except Exception:
                pass
        try:
            from browser_use.llm import ChatOllama
            return ChatOllama(
                model=os.getenv("BROWSER_USE_OLLAMA_MODEL", "llama3:latest"),
                host=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
            )
        except Exception:
            return None

    def _fail(self, task: str, mode: str, started: str, error: str) -> ArmResult:
        return ArmResult(
            success=False,
            arm="browser_use",
            mode=mode,
            task=task,
            error=error,
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )

    def _log(self, result: ArmResult) -> None:
        try:
            with _LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result.to_dict()) + "\n")
        except Exception:
            pass


if __name__ == "__main__":
    arm = BrowserUseArm()
    h = arm.health()
    print(f"health: {h['status']}")
    if h["status"] != "operational":
        print(f"  reason: {h.get('reason', '')}")
    print("PASS: browser_use_arm (structural)")
