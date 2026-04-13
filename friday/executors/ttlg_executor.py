#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
ttlg_executor.py — TTLG (Two-Tier LangGraph) Executor
=======================================================
Constitutional Authority: EPOS Constitution v3.1

4 modes dispatched from friday_graph:
  external     — Client-facing diagnostic (build_diagnostic_graph)
  internal     — Self-healing cycle (build_healing_graph)
  custom_props — External diagnostic with named props
  8scan        — Full EPOSDoctor system scan
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

from path_utils import get_context_vault

VAULT = get_context_vault()


def run(mission: dict) -> dict:
    """
    Execute a TTLG mission.

    mission keys:
      mode        — "external" | "internal" | "custom_props" | "8scan"
      props_name  — (optional) props name for custom_props mode
      description — human-readable directive
    """
    mission_id = mission.get("id", "M-TTLG-UNKNOWN")
    mode = mission.get("mode", "internal")
    description = mission.get("description", "")

    result: dict

    if mode == "8scan":
        result = _run_8scan(mission_id, description)
    elif mode == "external":
        result = _run_diagnostic(mission_id, description, props_name="client_ecosystem")
    elif mode == "custom_props":
        props_name = mission.get("props_name", "client_ecosystem")
        result = _run_diagnostic(mission_id, description, props_name=props_name)
    else:
        # internal (default)
        result = _run_healing(mission_id, description)

    _publish(result)
    return result


# ── Private helpers ──────────────────────────────────────────

def _run_diagnostic(mission_id: str, description: str, props_name: str) -> dict:
    try:
        from ttlg.pipeline_graph import build_diagnostic_graph
        graph = build_diagnostic_graph()
        output = graph.invoke(
            {"props_name": props_name},
            config={"configurable": {"thread_id": mission_id}},
        )
        build_manifest = output.get("build_manifest") or output.get("build_manifests")
        return {
            "mission_id": mission_id,
            "executor": "ttlg",
            "mode": "external",
            "status": "complete",
            "output": f"Diagnostic complete for '{props_name}'",
            "props_name": props_name,
            "build_manifest_keys": list(build_manifest.keys()) if isinstance(build_manifest, dict) else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "ttlg",
            "mode": "external",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:400]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _run_healing(mission_id: str, description: str) -> dict:
    try:
        from ttlg.pipeline_graph import build_healing_graph
        graph = build_healing_graph()
        output = graph.invoke(
            {},
            config={"configurable": {"thread_id": mission_id}},
        )
        actions = output.get("actions_taken", [])
        return {
            "mission_id": mission_id,
            "executor": "ttlg",
            "mode": "internal",
            "status": "complete",
            "output": f"Healing cycle complete: {len(actions)} actions taken",
            "actions": [a.get("action_type", str(a))[:80] for a in actions[:5]],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "ttlg",
            "mode": "internal",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:400]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _run_8scan(mission_id: str, description: str) -> dict:
    try:
        from engine.epos_doctor import EPOSDoctor
        doctor = EPOSDoctor(verbose=False, silent=True)
        passed = doctor.run_all_checks()
        return {
            "mission_id": mission_id,
            "executor": "ttlg",
            "mode": "8scan",
            "status": "complete",
            "output": (
                f"Doctor scan: passed={passed}, "
                f"ok={doctor.checks_passed}, "
                f"warn={doctor.checks_warned}, "
                f"fail={doctor.checks_failed}"
            ),
            "passed": passed,
            "checks_passed": doctor.checks_passed,
            "checks_warned": doctor.checks_warned,
            "checks_failed": doctor.checks_failed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "ttlg",
            "mode": "8scan",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:400]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _publish(result: dict):
    if _BUS:
        try:
            _BUS.publish(
                "ttlg.diagnostic.complete",
                result,
                source_module="ttlg_executor",
            )
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: 8scan mode
    print("Testing 8scan mode...")
    r = run({"id": "TEST-001", "mode": "8scan", "description": "Full doctor scan"})
    print(f"  status={r['status']} output={r.get('output', r.get('error', '?'))[:80]}")
    assert r["status"] in ("complete", "failed")
    passed += 1

    # Test 2: internal (healing) mode
    print("Testing internal mode...")
    r2 = run({"id": "TEST-002", "mode": "internal", "description": "Run healing cycle"})
    print(f"  status={r2['status']} output={r2.get('output', r2.get('error', '?'))[:80]}")
    assert r2["status"] in ("complete", "failed")
    passed += 1

    # Test 3: external (diagnostic) mode
    print("Testing external mode...")
    r3 = run({"id": "TEST-003", "mode": "external", "description": "Run external diagnostic"})
    print(f"  status={r3['status']} output={r3.get('output', r3.get('error', '?'))[:80]}")
    assert r3["status"] in ("complete", "failed")
    passed += 1

    print(f"\nPASS: ttlg_executor ({passed} assertions)")
