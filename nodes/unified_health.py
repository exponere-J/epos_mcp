#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
unified_health.py — Unified Health Check Surface
====================================================
Constitutional Authority: EPOS Constitution v3.1

Provides a standardized health_check() interface for every certified node.
Instead of adding the same method to 21 nodes, this module introspects
each node and returns a sovereign-compliant health response.

Any node can be queried via:
    from nodes.unified_health import check_node
    health = check_node("payment_gateway")

This satisfies sovereignty criterion #2 (health_check method) for all
nodes that don't yet have an explicit one.
"""

import importlib
import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from path_utils import get_context_vault

VAULT = get_context_vault()


def check_node(node_id: str) -> dict:
    """Return sovereign health status for any registered node."""
    from node_sovereignty_certifier import BUILDING_BLOCKS

    info = BUILDING_BLOCKS.get(node_id)
    if not info:
        return {"node": node_id, "status": "unknown", "reason": "Not in registry"}

    checks = []

    # Check 1: Module importable
    module_name = info.get("module", "")
    importable = False
    try:
        importlib.import_module(module_name)
        importable = True
        checks.append({"check": "module_importable", "status": "PASS"})
    except Exception as e:
        checks.append({"check": "module_importable", "status": "FAIL", "error": str(e)[:80]})

    # Check 2: Files exist
    files = info.get("files", [])
    files_ok = all(Path(f).exists() for f in files)
    checks.append({"check": "files_exist", "status": "PASS" if files_ok else "FAIL",
                   "missing": [f for f in files if not Path(f).exists()]})

    # Check 3: Vault path exists (heuristic: node_id with underscores stripped)
    vault_candidates = [
        VAULT / node_id,
        VAULT / node_id.replace("_", ""),
        VAULT / node_id.split("_")[0],
    ]
    vault_ok = any(p.exists() for p in vault_candidates)
    checks.append({"check": "vault_path_present", "status": "PASS" if vault_ok else "WARN"})

    # Check 4: Has value prop and pricing
    has_market = bool(info.get("value_prop")) and bool(info.get("suggested_price"))
    checks.append({"check": "market_ready", "status": "PASS" if has_market else "WARN"})

    all_pass = all(c["status"] == "PASS" for c in checks)
    has_fail = any(c["status"] == "FAIL" for c in checks)

    return {
        "node": node_id,
        "name": info.get("name", node_id),
        "status": "operational" if all_pass else ("degraded" if not has_fail else "failed"),
        "checks": checks,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def check_avatar_registry() -> dict:
    """Direct health check for the avatar registry (not yet in BUILDING_BLOCKS)."""
    try:
        from nodes.avatar_registry import get_registry
        return get_registry().health_check()
    except Exception as e:
        return {"node": "avatar_registry", "status": "error", "error": str(e)[:200]}


def check_all_nodes() -> dict:
    """Check health of every certified node."""
    from node_sovereignty_certifier import BUILDING_BLOCKS

    results = {}
    for node_id in BUILDING_BLOCKS:
        results[node_id] = check_node(node_id)
    # Inject the avatar registry as an additional sovereign surface
    results["avatar_registry"] = check_avatar_registry()

    summary = {
        "total": len(results),
        "operational": sum(1 for r in results.values() if r["status"] == "operational"),
        "degraded": sum(1 for r in results.values() if r["status"] == "degraded"),
        "failed": sum(1 for r in results.values() if r["status"] == "failed"),
    }
    return {"summary": summary, "nodes": results}


# Generic health_check class that any node can use
class SovereignHealthCheck:
    """Mixin/wrapper that provides health_check() to any node."""

    def __init__(self, node_id: str):
        self.node_id = node_id

    def health_check(self) -> dict:
        return check_node(self.node_id)


# ── Self-Test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: Check a single node
    health = check_node("event_bus")
    assert "status" in health
    print(f"event_bus: {health['status']}")
    passed += 1

    # Test 2: Check all nodes
    all_health = check_all_nodes()
    summary = all_health["summary"]
    print(f"Summary: {summary['operational']} operational, {summary['degraded']} degraded, {summary['failed']} failed of {summary['total']}")
    assert summary["total"] >= 22
    passed += 1

    # Test 3: SovereignHealthCheck wrapper
    wrapper = SovereignHealthCheck("payment_gateway")
    h = wrapper.health_check()
    assert "status" in h
    passed += 1

    # Test 4: Unknown node
    unknown = check_node("nonexistent_node")
    assert unknown["status"] == "unknown"
    passed += 1

    print(f"\nPASS: unified_health ({passed} assertions)")
    print(f"\nNode health summary:")
    for node_id, h in all_health["nodes"].items():
        icon = {"operational": "+", "degraded": "~", "failed": "!", "unknown": "?"}.get(h["status"], "?")
        print(f"  {icon} {node_id:25s} {h['status']}")
