#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
computeruse_executor.py — Computer Use Executor
================================================
Constitutional Authority: EPOS Constitution v3.1

Routes computer-use missions to Agent Zero with computer_use tools enabled.
Constitutional approval is REQUIRED — mission must carry computeruse_approved=True.
Missions lacking approval are escalated, not silently dropped.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

AZ_URL = os.getenv("AGENT_ZERO_URL", "http://agent-zero:8105")


def run(mission: dict) -> dict:
    """Execute a computer-use mission via Agent Zero."""
    mission_id = mission.get("id", "M-CU-UNKNOWN")
    description = mission.get("description", "")

    # Constitutional gate — computer use requires explicit approval
    if not mission.get("computeruse_approved"):
        result = {
            "mission_id": mission_id,
            "executor": "computeruse",
            "status": "escalated",
            "output": (
                "Computer use not approved. Mission escalated to Jamie. "
                "Set mission['computeruse_approved'] = True to authorize."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _publish(result)
        return result

    result = _dispatch_to_az(mission_id, description)
    _publish(result)
    return result


def _dispatch_to_az(mission_id: str, task: str) -> dict:
    import requests
    session = requests.Session()

    try:
        payload = {
            "text": task,
            "tools": ["computer_use"],
            "context": {
                "source": "friday_computeruse",
                "mission_id": mission_id,
            },
        }

        resp = session.post(
            f"{AZ_URL}/api/message_async",
            json=payload,
            timeout=int(os.getenv("AZ_TIMEOUT", "120")),
        )

        if resp.status_code in (200, 202):
            data = resp.json() if resp.text else {}
            return {
                "mission_id": mission_id,
                "executor": "computeruse",
                "status": "dispatched",
                "output": str(data.get("response") or data.get("message") or data)[:500],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "mission_id": mission_id,
                "executor": "computeruse",
                "status": "failed",
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except requests.exceptions.ConnectionError:
        return {
            "mission_id": mission_id,
            "executor": "computeruse",
            "status": "failed",
            "error": f"Agent Zero unreachable at {AZ_URL}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "computeruse",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:300]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _publish(result: dict):
    if _BUS:
        try:
            _BUS.publish(
                f"friday.computeruse.{result['status']}",
                result,
                source_module="computeruse_executor",
            )
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    # Test 1: Missing approval → escalated
    r = run({"id": "TEST-CU-001", "description": "Click the Start button"})
    assert r["status"] == "escalated", f"Expected escalated, got {r['status']}"
    print(f"Unapproved: status={r['status']} ✓")

    # Test 2: With approval → dispatched or failed (AZ may be down in test)
    r2 = run({
        "id": "TEST-CU-002",
        "description": "Take a screenshot of the desktop",
        "computeruse_approved": True,
    })
    print(f"Approved: status={r2['status']} output={r2.get('output', r2.get('error', '?'))[:80]}")
    assert r2["status"] in ("dispatched", "failed")

    print("PASS: computeruse_executor")
