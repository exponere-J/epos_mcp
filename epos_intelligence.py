#!/usr/bin/env python3
"""
epos_intelligence.py — EPOS Business Intelligence & Decision Logging
=====================================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles II, VII, VIII
Mission ID: EPOS Core Heal — Module 4 of 9
File Location: C:/Users/Jamie/workspace/epos_mcp/epos_intelligence.py

Single responsibility: Record decisions, mission outcomes, governance metrics,
and flywheel effects to structured JSONL logs. Provide analytics queries
over those logs.

Dependencies: path_utils (Module 1), roles (Module 3)
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

from path_utils import get_epos_root, get_logs_dir


# ── Paths ────────────────────────────────────────────────────────

def _bi_dir() -> Path:
    d = get_epos_root() / "context_vault" / "bi_history"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _decisions_log() -> Path:
    return _bi_dir() / "decisions.jsonl"


def _metrics_log() -> Path:
    return _bi_dir() / "flywheel_metrics.jsonl"


def _governance_log() -> Path:
    return get_epos_root() / "context_vault" / "governance" / "file_registry.jsonl"


def _mission_log() -> Path:
    return get_logs_dir() / "mission_history.jsonl"


# ── JSONL Helpers ────────────────────────────────────────────────

def _append_jsonl(filepath: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    """Append a single JSON object as a line to a JSONL file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        return {"status": "recorded"}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}


def _load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """Load all entries from a JSONL file."""
    if not filepath.exists():
        return []
    entries = []
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


# ── Recording API ────────────────────────────────────────────────

def record_decision(
    decision_type: str,
    description: str,
    agent_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    outcome: Optional[str] = None,
    flywheel_stage: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a strategic or operational decision to the BI log.

    Args:
        decision_type: Category (e.g. "mission_assignment", "governance_override")
        description: Human-readable description of what was decided
        agent_id: Which agent made the decision (from roles.AgentId)
        context: Additional structured data
        outcome: Result if known
        flywheel_stage: Which flywheel this feeds (content/revenue/data_moat/sovereign_scaling)

    Returns:
        {"status": "recorded", "entry": {...}} or {"status": "error", ...}
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "decision_type": decision_type,
        "description": description,
        "agent_id": agent_id,
        "context": context or {},
        "outcome": outcome,
        "flywheel_stage": flywheel_stage,
    }
    result = _append_jsonl(_decisions_log(), entry)
    if result["status"] == "recorded":
        result["entry"] = entry
    return result


def record_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic event recording. Primary interface for other components.

    The event dict is written as-is with a _bi_timestamp added.
    """
    event["_bi_timestamp"] = datetime.now().isoformat()
    return _append_jsonl(_decisions_log(), event)


def record_mission_outcome(
    mission_id: str,
    status: str,
    agent_id: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    error: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record a mission completion or failure."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "mission_id": mission_id,
        "status": status,
        "agent_id": agent_id,
        "execution_time_ms": execution_time_ms,
        "error": error,
        "details": details or {},
    }
    return _append_jsonl(_mission_log(), entry)


def record_flywheel_metric(
    flywheel: str,
    metric_name: str,
    value: Any,
    unit: str = "",
) -> Dict[str, Any]:
    """
    Record a flywheel metric data point.

    Args:
        flywheel: One of content, revenue, data_moat, sovereign_scaling
        metric_name: Specific metric (e.g. "pieces_per_week", "mrr")
        value: The measurement
        unit: Optional unit label
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "flywheel": flywheel,
        "metric": metric_name,
        "value": value,
        "unit": unit,
    }
    return _append_jsonl(_metrics_log(), entry)


# ── Analytics API ────────────────────────────────────────────────

def get_mission_analytics(days: int = 7) -> Dict[str, Any]:
    """Aggregate mission outcomes over a time window."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(_mission_log()) if e.get("timestamp", "") >= cutoff]

    if not entries:
        return {"period_days": days, "total_missions": 0, "message": "No mission data"}

    statuses = Counter(e.get("status") for e in entries)
    times = [e.get("execution_time_ms", 0) for e in entries if e.get("execution_time_ms")]
    errors = Counter(
        e.get("error", "unknown")[:80]
        for e in entries
        if e.get("status") in ("failed", "degraded")
    )

    return {
        "period_days": days,
        "total_missions": len(entries),
        "by_status": dict(statuses),
        "success_rate": round(statuses.get("completed", 0) / len(entries), 3) if entries else 0,
        "avg_execution_ms": int(sum(times) / len(times)) if times else 0,
        "top_errors": dict(errors.most_common(5)),
    }


def get_governance_analytics(days: int = 7) -> Dict[str, Any]:
    """Aggregate governance events over a time window."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(_governance_log()) if e.get("timestamp", "") >= cutoff]

    if not entries:
        return {"period_days": days, "total_events": 0, "message": "No governance data"}

    results = Counter(e.get("result") for e in entries)
    violations = Counter()
    for e in entries:
        for v in e.get("violations", []):
            violations[v] += 1

    total = len(entries)
    promoted = sum(1 for e in entries if "PROMOTED" in str(e.get("result", "")))

    return {
        "period_days": days,
        "total_events": total,
        "by_result": dict(results),
        "promotion_rate": round(promoted / total, 3) if total else 0,
        "top_violations": dict(violations.most_common(5)),
    }


def get_decision_analytics(days: int = 7) -> Dict[str, Any]:
    """Aggregate decision log over a time window."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(_decisions_log()) if e.get("timestamp", "") >= cutoff]

    if not entries:
        return {"period_days": days, "total_decisions": 0, "message": "No decision data"}

    types = Counter(e.get("decision_type") for e in entries)
    agents = Counter(e.get("agent_id") for e in entries if e.get("agent_id"))
    flywheels = Counter(e.get("flywheel_stage") for e in entries if e.get("flywheel_stage"))

    return {
        "period_days": days,
        "total_decisions": len(entries),
        "by_type": dict(types),
        "by_agent": dict(agents),
        "by_flywheel": dict(flywheels),
    }


def get_system_health_summary() -> Dict[str, Any]:
    """Complete BI health summary combining all analytics."""
    return {
        "generated_at": datetime.now().isoformat(),
        "missions": get_mission_analytics(days=7),
        "governance": get_governance_analytics(days=7),
        "decisions": get_decision_analytics(days=7),
        "bi_engine": {
            "version": "2.0.0",
            "decisions_log": str(_decisions_log()),
            "decisions_log_size": _decisions_log().stat().st_size if _decisions_log().exists() else 0,
            "metrics_log_size": _metrics_log().stat().st_size if _metrics_log().exists() else 0,
            "mission_log_size": _mission_log().stat().st_size if _mission_log().exists() else 0,
        },
    }


# ── Legacy Compatibility ─────────────────────────────────────────

def ensure_bi_decision_log() -> Path:
    """Ensure bi_decision_log.json exists for Doctor compatibility."""
    legacy_path = get_epos_root() / "bi_decision_log.json"
    if not legacy_path.exists():
        entries = _load_jsonl(_decisions_log())
        legacy_path.write_text(
            json.dumps({
                "decisions": entries[-100:] if entries else [],
                "synced_at": datetime.now().isoformat(),
            }, indent=2),
            encoding="utf-8",
        )
    return legacy_path


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EPOS Intelligence Engine v2.0")
    parser.add_argument("--summary", action="store_true", help="Full health summary")
    parser.add_argument("--missions", action="store_true", help="Mission analytics")
    parser.add_argument("--governance", action="store_true", help="Governance analytics")
    parser.add_argument("--decisions", action="store_true", help="Decision analytics")
    parser.add_argument("--record", type=str, help="Record event (JSON string)")
    parser.add_argument("--sync-legacy", action="store_true", help="Sync legacy BI log")
    parser.add_argument("--days", type=int, default=7, help="Lookback window")
    args = parser.parse_args()

    if args.summary:
        print(json.dumps(get_system_health_summary(), indent=2))
    elif args.missions:
        print(json.dumps(get_mission_analytics(args.days), indent=2))
    elif args.governance:
        print(json.dumps(get_governance_analytics(args.days), indent=2))
    elif args.decisions:
        print(json.dumps(get_decision_analytics(args.days), indent=2))
    elif args.record:
        try:
            data = json.loads(args.record)
            print(json.dumps(record_event(data), indent=2))
        except json.JSONDecodeError:
            print("Error: --record requires valid JSON")
    elif args.sync_legacy:
        print("Synced:", ensure_bi_decision_log())
    else:
        # Default: quick summary
        s = get_system_health_summary()
        print("EPOS Intelligence Engine v2.0")
        print(f"  Missions (7d): {s['missions']['total_missions']} total")
        print(f"  Governance (7d): {s['governance']['total_events']} events")
        print(f"  Decisions (7d): {s['decisions']['total_decisions']} recorded")

        # Quick self-test
        r = record_decision("self_test", "Module 4 self-test", agent_id="ttlg")
        assert r["status"] == "recorded"
        print("  Self-test: PASS")
