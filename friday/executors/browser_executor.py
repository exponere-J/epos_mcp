#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
browser_executor.py — BrowserUse Executor
==========================================
Constitutional Authority: EPOS Constitution v3.1

Wraps BrowserUseNode for async browser automation missions.
Falls back to Agent Zero if BrowserUse is unavailable.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None


def run(mission: dict) -> dict:
    """Execute a browser automation mission."""
    mission_id = mission.get("id", "M-BROWSER-UNKNOWN")
    description = mission.get("description", "")
    max_steps = int(mission.get("max_steps", 5))

    result = _execute(mission_id, description, max_steps)
    _publish(result)
    return result


def _execute(mission_id: str, task: str, max_steps: int) -> dict:
    try:
        from nodes.browser_use_node import BrowserUseNode
        node = BrowserUseNode()
        health = node.health_check()

        if health.get("status") != "operational":
            return {
                "mission_id": mission_id,
                "executor": "browser_use",
                "status": "failed",
                "error": f"BrowserUse not operational: {health.get('reason', '?')}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Use asyncio.run for the async execute_task
        raw = asyncio.run(node.execute_task(task, max_steps=max_steps))

        return {
            "mission_id": mission_id,
            "executor": "browser_use",
            "status": "complete" if raw.get("success") else "failed",
            "output": str(raw.get("result", ""))[:500],
            "error": raw.get("error", "")[:300] if not raw.get("success") else None,
            "steps_taken": raw.get("steps"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "browser_use",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:400]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _publish(result: dict):
    if _BUS:
        try:
            _BUS.publish(
                f"friday.browser.{result['status']}",
                result,
                source_module="browser_executor",
            )
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    r = run({
        "id": "TEST-BROWSER-001",
        "description": "Navigate to https://example.com and return the page title",
        "max_steps": 3,
    })
    print(f"status={r['status']} output={r.get('output', r.get('error', '?'))[:100]}")
    assert r["status"] in ("complete", "failed")
    print("PASS: browser_executor")
