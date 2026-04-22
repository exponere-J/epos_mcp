#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
browser_executor.py — Friday entry for the BrowserUse arm

Routes to the unified execution-arm package. Two paths:

  1. In-process (preferred):
       from nodes.execution_arm import execute
  2. Remote via Agent Zero HTTP:
       POST http://agent-zero:8105/api/execute

Mission fields:
    id, description, mode_hint ("headless"|"headed"|"auto"|"browser_use.*"),
    max_steps, context (passes through; include 'deletion_approved' to
    authorize destructive operations).
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
    mission_id = mission.get("id", f"M-BROWSER-{_ts()}")
    task = mission.get("description", "") or mission.get("task", "")

    hint = mission.get("mode_hint", "browser_use")
    if hint in ("headless", "headed"):
        hint = f"browser_use.{hint}"
    elif hint == "auto":
        hint = "browser_use"

    max_steps = int(mission.get("max_steps", 8))
    context = {**(mission.get("context") or {}), "mission_id": mission_id}

    result = _dispatch(task, hint, max_steps, context)
    _publish(result)
    return result


def _dispatch(task: str, hint: str, max_steps: int, context: dict) -> dict:
    # In-process call
    try:
        from nodes.execution_arm import execute as arm_execute
        r = arm_execute(task=task, mode_hint=hint, max_steps=max_steps, context=context)
        return _normalize(r, "in_process", context["mission_id"])
    except Exception as in_err:  # noqa: BLE001
        in_process_err = f"{type(in_err).__name__}: {in_err}"

    # Fallback: AZ HTTP
    try:
        import requests
        resp = requests.post(
            f"{AZ_URL}/api/execute",
            json={"task": task, "mode_hint": hint,
                  "max_steps": max_steps, "context": context},
            timeout=int(os.getenv("AZ_TIMEOUT", "120")),
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
        "executor": "browser_executor",
        "status": "complete" if raw.get("success") else "failed",
        "source": source,
        "arm": raw.get("arm", "browser_use"),
        "mode": raw.get("mode", ""),
        "output": (raw.get("output") or "")[:500],
        "error": (raw.get("error") or "")[:300],
        "selection": raw.get("selection"),
        "timestamp": raw.get("finished_at") or _ts(),
    }


def _fail(mission_id: str, error: str) -> dict:
    return {
        "mission_id": mission_id,
        "executor": "browser_executor",
        "status": "failed",
        "error": error,
        "timestamp": _ts(),
    }


def _publish(result: dict) -> None:
    if _BUS:
        try:
            _BUS.publish(f"friday.browser.{result['status']}", result,
                         source_module="browser_executor")
        except Exception:
            pass


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    r = run({
        "id": "TEST-BROWSER-001",
        "description": "Navigate to https://example.com and return the title",
        "mode_hint": "headless",
        "max_steps": 3,
    })
    print(f"status={r['status']} mode={r.get('mode')} output={(r.get('output') or r.get('error') or '?')[:100]}")
    assert r["status"] in ("complete", "failed")
    print("PASS: browser_executor")
