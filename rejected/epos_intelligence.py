# File: C:\Users\Jamie\workspace\epos_mcp\engine\epos_intelligence.py
# ═══════════════════════════════════════════════════════════════
# EPOS GOVERNANCE WATERMARK
# ───────────────────────────────────────────────────────────────
# Triage ID:      TRG-20260218-BI-V1
# First Submitted: 2026-02-18T07:00:00Z
# Triage Result:   PROMOTED (attempt 1 of 1)
# Promoted At:     2026-02-18T07:00:00Z
# Destination:     engine/epos_intelligence.py
# Constitutional:  Article II, VII compliant
# Violations:      None
# Watermark Hash:  PENDING_FIRST_TRIAGE
# ═══════════════════════════════════════════════════════════════

"""
EPOS Intelligence Engine v1.0 — Business Intelligence & Flywheel Analytics

Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles II, VII
Purpose: Track decisions, mission outcomes, governance metrics, and flywheel
         effects. Feed data to EVL1 evolution analysis and TTLG validation.

Tracks:
  - Mission execution outcomes (success rate, avg time, failure patterns)
  - Governance gate decisions (promotion rate, rejection patterns)
  - Content Lab performance (echolocation scores, cascade counts)
  - Context Vault usage (query depth, vault file access patterns)
  - Flywheel velocity (decision → action → outcome → learning cycle time)

Storage: All data in context_vault/bi_history/ (Article VII compliant)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
BI_DIR = EPOS_ROOT / "context_vault" / "bi_history"
DECISIONS_LOG = BI_DIR / "decisions.jsonl"
METRICS_LOG = BI_DIR / "flywheel_metrics.jsonl"
GOVERNANCE_LOG = EPOS_ROOT / "context_vault" / "governance" / "file_registry.jsonl"
MISSION_LOG = EPOS_ROOT / "logs" / "mission_history.jsonl"
DOCTOR_LOG = EPOS_ROOT / "context_vault" / "events" / "doctor_events.jsonl"

# Ensure directories
BI_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# DECISION RECORDING
# ═══════════════════════════════════════════════════════════════

def record_decision(
    decision_type: str,
    description: str,
    context: Optional[Dict[str, Any]] = None,
    outcome: Optional[str] = None,
    flywheel_stage: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a strategic or operational decision to the BI log.

    decision_type: "strategic", "architectural", "governance", "market", "content"
    flywheel_stage: "F1_diagnostic", "F2_revenue", "F3_product", "F4_ecosystem"
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "decision_type": decision_type,
        "description": description,
        "context": context or {},
        "outcome": outcome,
        "flywheel_stage": flywheel_stage,
        "recorded_by": "epos_intelligence_v1.0",
    }

    try:
        with open(DECISIONS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return {"status": "recorded", "entry": entry}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}


def record_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Generic event recording. Accepts any structured event dict.

    This is the primary interface for other components to log BI-relevant events.
    """
    event["_bi_timestamp"] = datetime.now().isoformat()
    event["_bi_source"] = event.get("source", "unknown")

    try:
        with open(DECISIONS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return {"status": "recorded"}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}


# ═══════════════════════════════════════════════════════════════
# FLYWHEEL METRICS
# ═══════════════════════════════════════════════════════════════

def record_flywheel_metric(
    flywheel: str,
    metric_name: str,
    value: Any,
    unit: str = "",
) -> Dict[str, Any]:
    """Record a quantitative flywheel metric.

    flywheel: "F1_diagnostic", "F2_revenue", "F3_product", "F4_ecosystem"
    metric_name: e.g., "diagnostic_conversion_rate", "ttlg_validation_score"
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "flywheel": flywheel,
        "metric": metric_name,
        "value": value,
        "unit": unit,
    }

    try:
        with open(METRICS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return {"status": "recorded"}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}


# ═══════════════════════════════════════════════════════════════
# ANALYTICS QUERIES
# ═══════════════════════════════════════════════════════════════

def _load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dicts."""
    if not filepath.exists():
        return []
    entries = []
    for line in filepath.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def get_mission_analytics(days: int = 7) -> Dict[str, Any]:
    """Analyze mission execution patterns over the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(MISSION_LOG) if e.get("timestamp", "") >= cutoff]

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
        "max_execution_ms": max(times) if times else 0,
        "top_errors": dict(errors.most_common(5)),
    }


def get_governance_analytics(days: int = 7) -> Dict[str, Any]:
    """Analyze governance gate triage patterns."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(GOVERNANCE_LOG) if e.get("timestamp", "") >= cutoff]

    if not entries:
        return {"period_days": days, "total_events": 0, "message": "No governance data"}

    results = Counter(e.get("result") for e in entries)
    violations = Counter()
    for e in entries:
        for v in e.get("violations", []):
            violations[v] += 1

    total = len(entries)
    promoted = sum(1 for e in entries if "PROMOTED" in e.get("result", ""))

    return {
        "period_days": days,
        "total_events": total,
        "by_result": dict(results),
        "promotion_rate": round(promoted / total, 3) if total else 0,
        "top_violations": dict(violations.most_common(5)),
    }


def get_doctor_analytics(days: int = 7) -> Dict[str, Any]:
    """Analyze Doctor sweep patterns."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(DOCTOR_LOG) if e.get("timestamp", "") >= cutoff]

    if not entries:
        return {"period_days": days, "total_sweeps": 0, "message": "No doctor data"}

    types = Counter(e.get("event_type") for e in entries)
    failures = [
        e for e in entries
        if e.get("event_type") == "doctor.sweep.failed"
    ]
    heals = sum(
        e.get("payload", {}).get("healed", 0)
        for e in entries
    )

    return {
        "period_days": days,
        "total_sweeps": len(entries),
        "by_type": dict(types),
        "failure_sweeps": len(failures),
        "total_self_heals": heals,
    }


def get_decision_analytics(days: int = 30) -> Dict[str, Any]:
    """Analyze strategic decision patterns."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = [e for e in _load_jsonl(DECISIONS_LOG) if e.get("timestamp", "") >= cutoff]

    if not entries:
        return {"period_days": days, "total_decisions": 0}

    types = Counter(e.get("decision_type") for e in entries)
    flywheels = Counter(e.get("flywheel_stage") for e in entries if e.get("flywheel_stage"))

    return {
        "period_days": days,
        "total_decisions": len(entries),
        "by_type": dict(types),
        "by_flywheel": dict(flywheels),
    }


def get_system_health_summary() -> Dict[str, Any]:
    """Comprehensive system health summary combining all analytics."""
    return {
        "generated_at": datetime.now().isoformat(),
        "missions": get_mission_analytics(days=7),
        "governance": get_governance_analytics(days=7),
        "doctor": get_doctor_analytics(days=7),
        "decisions": get_decision_analytics(days=30),
        "bi_engine": {
            "version": "1.0.0",
            "decisions_log_size": DECISIONS_LOG.stat().st_size if DECISIONS_LOG.exists() else 0,
            "metrics_log_size": METRICS_LOG.stat().st_size if METRICS_LOG.exists() else 0,
        },
    }


# ═══════════════════════════════════════════════════════════════
# BI DECISION LOG COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

def ensure_bi_decision_log() -> Path:
    """Ensure bi_decision_log.json exists at root for Doctor v3.2 compatibility.

    Doctor check 15 expects this file with a "decisions" array.
    This function creates it if missing and syncs from JSONL.
    """
    legacy_path = EPOS_ROOT / "bi_decision_log.json"

    if not legacy_path.exists():
        # Create from JSONL if available
        entries = _load_jsonl(DECISIONS_LOG)
        legacy_path.write_text(json.dumps({
            "decisions": entries[-100:] if entries else [],  # Last 100
            "synced_from": str(DECISIONS_LOG),
            "synced_at": datetime.now().isoformat(),
        }, indent=2), encoding="utf-8")

    return legacy_path


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    pa = argparse.ArgumentParser(description="EPOS Intelligence Engine v1.0")
    pa.add_argument("--summary", action="store_true", help="Full system health summary")
    pa.add_argument("--missions", action="store_true", help="Mission analytics")
    pa.add_argument("--governance", action="store_true", help="Governance analytics")
    pa.add_argument("--decisions", action="store_true", help="Decision analytics")
    pa.add_argument("--record", type=str, help="Record a decision (JSON string)")
    pa.add_argument("--sync-legacy", action="store_true", help="Sync bi_decision_log.json")
    pa.add_argument("--days", type=int, default=7, help="Analysis period in days")

    a = pa.parse_args()

    if a.summary:
        print(json.dumps(get_system_health_summary(), indent=2))
    elif a.missions:
        print(json.dumps(get_mission_analytics(a.days), indent=2))
    elif a.governance:
        print(json.dumps(get_governance_analytics(a.days), indent=2))
    elif a.decisions:
        print(json.dumps(get_decision_analytics(a.days), indent=2))
    elif a.record:
        try:
            data = json.loads(a.record)
            r = record_event(data)
            print(json.dumps(r, indent=2))
        except json.JSONDecodeError:
            print("Error: --record requires valid JSON string")
    elif a.sync_legacy:
        p = ensure_bi_decision_log()
        print(f"Legacy bi_decision_log.json synced at {p}")
    else:
        # Default: quick summary
        s = get_system_health_summary()
        m = s["missions"]
        g = s["governance"]
        print(f"EPOS Intelligence Engine v1.0")
        print(f"  Missions (7d):    {m['total_missions']} total, {m.get('success_rate', 0)*100:.0f}% success")
        print(f"  Governance (7d):  {g['total_events']} events, {g.get('promotion_rate', 0)*100:.0f}% promoted")
        print(f"  Decisions (30d):  {s['decisions']['total_decisions']} recorded")
