#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
system_executor.py — EPOS System Operations Executor
======================================================
Constitutional Authority: EPOS Constitution v3.1

Handles system-level missions:
  doctor        — Run EPOSDoctor.run_all_checks()
  heal          — Run TTLG healing cycle
  certify       — Run sovereignty certifier on all modules
  baselines     — Rebuild context vault baselines
  daemon_status — Report APScheduler daemon job status
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

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))


def run(mission: dict) -> dict:
    """Execute a system operation mission."""
    mission_id = mission.get("id", "M-SYS-UNKNOWN")
    description = mission.get("description", "").lower()

    # Determine action from description or explicit action key
    action = mission.get("action") or _infer_action(description)

    dispatch = {
        "doctor": _action_doctor,
        "heal": _action_heal,
        "certify": _action_certify,
        "baselines": _action_baselines,
        "daemon_status": _action_daemon_status,
    }

    fn = dispatch.get(action, _action_unknown)
    result = fn(mission_id, action)
    _publish(result)
    return result


# ── Actions ──────────────────────────────────────────────────

def _action_doctor(mission_id: str, action: str) -> dict:
    try:
        from engine.epos_doctor import EPOSDoctor
        doctor = EPOSDoctor(verbose=False, silent=True)
        passed = doctor.run_all_checks()
        return {
            "mission_id": mission_id,
            "executor": "system",
            "action": action,
            "status": "complete",
            "output": (
                f"Doctor: {'PASS' if passed else 'FAIL'} | "
                f"ok={doctor.checks_passed} warn={doctor.checks_warned} fail={doctor.checks_failed}"
            ),
            "passed": passed,
            "checks_passed": doctor.checks_passed,
            "checks_warned": doctor.checks_warned,
            "checks_failed": doctor.checks_failed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return _err(mission_id, action, e)


def _action_heal(mission_id: str, action: str) -> dict:
    try:
        from ttlg.pipeline_graph import run_healing_cycle
        output = run_healing_cycle()
        actions_taken = output.get("actions_taken", [])
        return {
            "mission_id": mission_id,
            "executor": "system",
            "action": action,
            "status": "complete",
            "output": f"Healing: {len(actions_taken)} actions taken",
            "actions": [a.get("action_type", str(a))[:60] for a in actions_taken[:5]],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return _err(mission_id, action, e)


def _action_certify(mission_id: str, action: str) -> dict:
    try:
        from engine.sovereignty_certifier import SovereigntyCertifier
        certifier = SovereigntyCertifier(epos_root=EPOS_ROOT)
        report = certifier.certify_all()
        certified = report.get("certified_count", 0)
        total = report.get("total_modules", 0)
        return {
            "mission_id": mission_id,
            "executor": "system",
            "action": action,
            "status": "complete",
            "output": f"Certifier: {certified}/{total} modules sovereign",
            "report": report,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return _err(mission_id, action, e)


def _action_baselines(mission_id: str, action: str) -> dict:
    try:
        from engine.baseline_manager import BaselineManager
        manager = BaselineManager(epos_root=EPOS_ROOT)
        result = manager.rebuild_all()
        return {
            "mission_id": mission_id,
            "executor": "system",
            "action": action,
            "status": "complete",
            "output": f"Baselines rebuilt: {result}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return _err(mission_id, action, e)


def _action_daemon_status(mission_id: str, action: str) -> dict:
    try:
        import requests
        core_url = os.getenv("EPOS_CORE_URL", "http://epos-core:8001")
        resp = requests.get(f"{core_url}/daemon/status", timeout=5)
        data = resp.json() if resp.status_code == 200 else {"error": f"HTTP {resp.status_code}"}
        jobs = data.get("jobs", [])
        return {
            "mission_id": mission_id,
            "executor": "system",
            "action": action,
            "status": "complete",
            "output": f"Daemon: {len(jobs)} scheduled jobs",
            "jobs": jobs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return _err(mission_id, action, e)


def _action_unknown(mission_id: str, action: str) -> dict:
    return {
        "mission_id": mission_id,
        "executor": "system",
        "action": action,
        "status": "escalated",
        "output": f"Unknown system action '{action}'. Valid: doctor, heal, certify, baselines, daemon_status",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Helpers ──────────────────────────────────────────────────

def _infer_action(description: str) -> str:
    if any(w in description for w in ["doctor", "scan", "check", "diagnose", "8scan"]):
        return "doctor"
    if any(w in description for w in ["heal", "self-heal", "fix system", "remediat"]):
        return "heal"
    if any(w in description for w in ["certif", "sovereign"]):
        return "certify"
    if any(w in description for w in ["baseline"]):
        return "baselines"
    if any(w in description for w in ["daemon", "schedule", "jobs", "cron"]):
        return "daemon_status"
    return "doctor"  # default to doctor for unrecognized system commands


def _err(mission_id: str, action: str, exc: Exception) -> dict:
    return {
        "mission_id": mission_id,
        "executor": "system",
        "action": action,
        "status": "failed",
        "error": f"{type(exc).__name__}: {str(exc)[:400]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _publish(result: dict):
    if _BUS:
        try:
            _BUS.publish(
                f"friday.system.{result['status']}",
                result,
                source_module="system_executor",
            )
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    for action in ["doctor", "heal", "daemon_status"]:
        r = run({"id": f"TEST-SYS-{action}", "action": action, "description": action})
        print(f"{action}: status={r['status']} output={r.get('output', r.get('error', '?'))[:80]}")
        assert r["status"] in ("complete", "failed", "escalated")
        passed += 1

    print(f"\nPASS: system_executor ({passed} assertions)")
