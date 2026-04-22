#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
callable.py — Universal Entrypoint for the Execution Arm
=========================================================
Sovereign directive (2026-04-21):
    "Callable by any component, agent or process in the ecosystem."

Three call surfaces, one core:

    1. In-process Python
         from nodes.execution_arm import execute
         result = execute(task="...", mode_hint="auto", ...)

    2. Event bus
         publish 'execution.arm.request' with payload {task, mode_hint, ...}
         subscribe 'execution.arm.response' for result

    3. REST (served by AZ bridge)
         POST /api/execute  { "task": "...", "mode_hint": "..." }

Results are always a dict shaped like ArmResult.to_dict() plus:
    - 'selection': the mode_selector.Selection.to_dict()
    - 'deletion_log_path': where attempts are logged

The core is sync-safe (wraps async internally). Everything is idempotent
with respect to the log files — two identical calls log two entries.
"""

from __future__ import annotations

import asyncio
import os
import threading
from datetime import datetime, timezone
from typing import Any

from .browser_use_arm import ArmResult as BrowserResult, BrowserUseArm
from .computer_use_arm import ArmResult as ComputerResult, ComputerUseArm
from .deletion_gate import _LOG_PATH as _DELETION_LOG  # noqa: PLC2701
from .mode_selector import Selection, select

_LOCK = threading.Lock()
_BROWSER_ARM: BrowserUseArm | None = None
_COMPUTER_ARM: ComputerUseArm | None = None


def _browser() -> BrowserUseArm:
    global _BROWSER_ARM
    with _LOCK:
        if _BROWSER_ARM is None:
            _BROWSER_ARM = BrowserUseArm()
        return _BROWSER_ARM


def _computer() -> ComputerUseArm:
    global _COMPUTER_ARM
    with _LOCK:
        if _COMPUTER_ARM is None:
            _COMPUTER_ARM = ComputerUseArm()
        return _COMPUTER_ARM


def execute(
    task: str,
    mode_hint: str | None = "auto",
    max_steps: int = 8,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Synchronous, universal entrypoint. Picks the variant and runs it.

    Args:
        task: natural-language description of what to do.
        mode_hint: None/'auto' lets the reasoner decide. Also accepts
                   explicit 'browser_use.headless', 'headed', etc.
        max_steps: per-arm step/turn cap.
        context: mission context dict. Passes through to arms.
                 Include 'deletion_approved' to authorize deletions.

    Returns:
        Result dict with 'success', 'arm', 'mode', 'output'/'error',
        'selection', and timestamps.
    """
    return asyncio.run(execute_async(task, mode_hint, max_steps, context))


async def execute_async(
    task: str,
    mode_hint: str | None = "auto",
    max_steps: int = 8,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Async entrypoint. Prefer this inside event loops."""
    ctx = dict(context or {})
    ctx.setdefault("mission_id", f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}")

    selection = select(task=task, context=ctx, mode_hint=mode_hint)

    if selection.arm == "browser_use":
        arm_result: BrowserResult | ComputerResult = await _browser().run(
            task=task, mode=selection.mode, max_steps=max_steps, context=ctx,
        )
    else:  # computer_use
        arm_result = await _computer().run(
            task=task, mode=selection.mode, max_turns=max_steps, context=ctx,
        )

    payload = arm_result.to_dict()
    payload["selection"] = selection.to_dict()
    payload["deletion_log_path"] = str(_DELETION_LOG)
    payload["mission_id"] = ctx["mission_id"]
    return payload


def health() -> dict[str, Any]:
    """Report the operational state of each arm + display stack."""
    return {
        "browser_use": _browser().health(),
        "computer_use": _computer().health(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Event-bus binding ────────────────────────────────────────────
#
# Optional: if epos_event_bus is importable in the process, this helper
# will auto-subscribe on import. Callers publish:
#     'execution.arm.request' {task, mode_hint, max_steps, context, reply_to}
# The handler publishes:
#     'execution.arm.response' <result dict>
# and, if reply_to is provided, the same payload on that custom topic.

def install_event_bus_handler() -> bool:
    """Install the event-bus subscriber. Returns True on success."""
    try:
        from epos_event_bus import EPOSEventBus  # type: ignore
    except Exception:
        return False

    bus = EPOSEventBus()

    def _handler(event):
        payload = (event or {}).get("payload", {}) or {}
        try:
            result = execute(
                task=payload.get("task", ""),
                mode_hint=payload.get("mode_hint", "auto"),
                max_steps=int(payload.get("max_steps", 8)),
                context=payload.get("context") or {},
            )
        except Exception as e:  # noqa: BLE001
            result = {"success": False, "error": f"{type(e).__name__}: {e}"}

        reply_to = payload.get("reply_to")
        try:
            bus.publish("execution.arm.response", result, source_module="execution_arm")
            if reply_to:
                bus.publish(reply_to, result, source_module="execution_arm")
        except Exception:
            pass

    try:
        bus.subscribe("execution.arm.request", _handler)
        return True
    except Exception:
        return False


_AUTOSUBSCRIBE = os.getenv("EPOS_ARM_AUTOSUBSCRIBE", "1") not in ("0", "false", "False")
if _AUTOSUBSCRIBE:
    try:
        install_event_bus_handler()
    except Exception:
        pass


if __name__ == "__main__":
    # Dry-run: selection works without the underlying deps.
    dry = select(task="Show me the LinkedIn post preview", context=None, mode_hint="auto")
    print(f"dry-selection: {dry.variant} — {dry.reason}")

    print("health:", health())
    print("PASS: callable (structural)")
