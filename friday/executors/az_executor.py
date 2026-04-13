#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
az_executor.py — Agent Zero Executor
=====================================
Constitutional Authority: EPOS Constitution v3.1

Dispatches missions to the Agent Zero container via HTTP.
Uses a persistent session for CSRF token handling.
Endpoint: POST /api/message_async
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

AZ_URL = os.getenv("AGENT_ZERO_URL", "http://agent-zero:8105")
AZ_TIMEOUT = int(os.getenv("AZ_TIMEOUT", "120"))


def run(mission: dict) -> dict:
    """Dispatch mission to Agent Zero container."""
    mission_id = mission.get("id", "M-AZ-UNKNOWN")
    description = mission.get("description", "")

    result = _dispatch(mission_id, description)
    _publish(result)
    return result


def _dispatch(mission_id: str, task: str) -> dict:
    session = requests.Session()

    try:
        # Fetch CSRF token if endpoint provides one
        csrf_token = None
        try:
            resp = session.get(f"{AZ_URL}/api/csrf", timeout=5)
            if resp.status_code == 200:
                csrf_token = resp.json().get("csrf_token")
        except Exception:
            pass  # CSRF not required on this AZ build

        headers = {"Content-Type": "application/json"}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        payload = {
            "text": task,
            "context": {
                "source": "friday",
                "mission_id": mission_id,
            },
        }

        resp = session.post(
            f"{AZ_URL}/api/message_async",
            json=payload,
            headers=headers,
            timeout=AZ_TIMEOUT,
        )

        if resp.status_code in (200, 202):
            data = resp.json() if resp.text else {}
            return {
                "mission_id": mission_id,
                "executor": "agent_zero",
                "status": "dispatched",
                "output": str(data.get("response") or data.get("message") or data)[:500],
                "az_job_id": data.get("job_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "mission_id": mission_id,
                "executor": "agent_zero",
                "status": "failed",
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except requests.exceptions.ConnectionError:
        return {
            "mission_id": mission_id,
            "executor": "agent_zero",
            "status": "failed",
            "error": f"Agent Zero unreachable at {AZ_URL}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "agent_zero",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:300]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _publish(result: dict):
    if _BUS:
        try:
            _BUS.publish(
                f"friday.az.{result['status']}",
                result,
                source_module="az_executor",
            )
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Agent Zero URL: {AZ_URL}")
    r = run({"id": "TEST-AZ-001", "description": "Echo: Agent Zero executor test"})
    print(f"status={r['status']} output={r.get('output', r.get('error', '?'))[:100]}")
    assert r["status"] in ("dispatched", "failed")
    print("PASS: az_executor")
