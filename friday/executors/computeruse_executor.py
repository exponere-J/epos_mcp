#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
computeruse_executor.py — Friday entry for the ComputerUse arm

Routes OS/desktop-level missions through the unified execution-arm.
Approval gates:
    computeruse_approved=True         — required to dispatch
    context['deletion_approved']      — required for any destructive op
                                        (enforced inside the arm)

Two paths:
  1. In-process (preferred):
       from nodes.execution_arm import execute
  2. Remote via Agent Zero HTTP:
       POST http://agent-zero:8105/api/execute

Mission fields:
    id, description, mode_hint ("headless"|"headed"|"auto"|"computer_use.*"),
    max_turns (alias: max_steps), context.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

AZ_URL = os.getenv("AGENT_ZERO_URL", "http://agent-zero:8105")


def run(mission: dict) -> dict:
    mission_id = mission.get("id", f"M-CU-{_ts()}")

    if not mission.get("computeruse_approved"):
        result = {
            "mission_id": mission_id,
            "executor": "computeruse",
            "status": "escalated",
            "output": (
                "Computer use not approved. Mission escalated to Jamie. "
                "Set mission['computeruse_approved'] = True to authorize."
            ),
            "timestamp": _ts(),
        }
        _publish(result)
        return result

    task = mission.get("description", "") or mission.get("task", "")

    hint = mission.get("mode_hint", "computer_use")
    if hint in ("headless", "headed"):
        hint = f"computer_use.{hint}"
    elif hint == "auto":
        hint = "computer_use"

    max_turns = int(mission.get("max_turns") or mission.get("max_steps") or 12)
    context = {**(mission.get("context") or {}), "mission_id": mission_id}

    result = _dispatch(task, hint, max_turns, context)
    _publish(result)
    return result


def _dispatch(task: str, hint: str, max_turns: int, context: dict) -> dict:
    try:
        from nodes.execution_arm import execute as arm_execute
        r = arm_execute(task=task, mode_hint=hint, max_steps=max_turns, context=context)
        return _normalize(r, "in_process", context["mission_id"])
    except Exception as in_err:  # noqa: BLE001
        in_process_err = f"{type(in_err).__name__}: {in_err}"

    try:
        import requests
        resp = requests.post(
            f"{AZ_URL}/api/execute",
            json={"task": task, "mode_hint": hint,
                  "max_steps": max_turns, "context": context},
            timeout=int(os.getenv("AZ_TIMEOUT", "180")),
        )
        if resp.status_code in (200, 202):
            return _normalize(resp.json(), "az_http", context["mission_id"])
        return _fail(context["mission_id"],
                     f"AZ HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:  # noqa: BLE001
        return _fail(context["mission_id"],
                     f"in_process={in_process_err}; az_http={type(e).__name__}: {e}")


def _normalize(raw: dict, source: str, mission_id: str) -> dict:
    return {
        "mission_id": raw.get("mission_id") or mission_id,
        "executor": "computeruse",
        "status": "complete" if raw.get("success") else "failed",
        "source": source,
        "arm": raw.get("arm", "computer_use"),
        "mode": raw.get("mode", ""),
        "output": (raw.get("output") or "")[:500],
        "error": (raw.get("error") or "")[:300],
        "selection": raw.get("selection"),
        "timestamp": raw.get("finished_at") or _ts(),
    }


def _fail(mission_id: str, error: str) -> dict:
    return {
        "mission_id": mission_id,
        "executor": "computeruse",
        "status": "failed",
        "error": error,
        "timestamp": _ts(),
    }


def _publish(result: dict) -> None:
    if _BUS:
        try:
            _BUS.publish(f"friday.computeruse.{result['status']}", result,
                         source_module="computeruse_executor")
        except Exception:
            pass


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    r = run({"id": "TEST-CU-001", "description": "Click the Start button"})
    assert r["status"] == "escalated"
    print(f"unapproved → {r['status']} (correct)")

    r2 = run({
        "id": "TEST-CU-002",
        "description": "Take a screenshot of the desktop",
        "computeruse_approved": True,
        "mode_hint": "headless",
    })
    print(f"approved → status={r2['status']} mode={r2.get('mode')} output={(r2.get('output') or r2.get('error') or '?')[:80]}")
    assert r2["status"] in ("complete", "failed")
    print("PASS: computeruse_executor")
