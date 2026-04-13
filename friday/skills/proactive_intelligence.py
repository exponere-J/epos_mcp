#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
proactive_intelligence.py — Friday Proactive Intelligence Engine
=================================================================
Constitutional Authority: EPOS Constitution v3.1

Scans metrics, threads, and event bus for conditions that warrant
proactive alerting — without waiting for Jamie to ask.

Alert types:
  - Service degradation (any critical service down > 30 min)
  - Stale threads (open threads > STALE_THRESHOLD_HOURS)
  - Event bus anomaly (error rate spike)
  - LLM failure spike (>3 failures in 24h)
  - Content queue empty (ready_to_post = 0)
  - Doctor not run in > 24h
  - Reactor position missing (full bus reprocessing on restart)
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()


def scan() -> List[dict]:
    """
    Run all proactive intelligence checks.
    Returns list of alert dicts with keys: level, type, message, action.
    """
    from friday.skills.metrics_observatory import snapshot
    from friday.skills.thread_tracker import list_stale

    alerts = []
    m = snapshot()

    # --- Service degradation ---
    for svc, key in [
        ("EPOS Core", "epos_core_up"),
        ("LiteLLM", "litellm_up"),
        ("Governance Gate", "governance_gate_up"),
    ]:
        if m.get(key) is False:
            alerts.append({
                "level": "CRITICAL",
                "type": "service_down",
                "message": f"{svc} is unreachable",
                "action": f"Check container: docker compose ps | grep {svc.lower().replace(' ', '-')}",
            })

    # --- LLM failure spike ---
    llm_failures = m.get("llm_failures_24h", 0) or 0
    if llm_failures >= 3:
        alerts.append({
            "level": "WARN",
            "type": "llm_failure_spike",
            "message": f"LLM failures in last 24h: {llm_failures}",
            "action": "Check GROQ_API_KEY, LiteLLM logs, Ollama container",
        })

    # --- Event bus error rate ---
    total_24h = m.get("event_bus_entries_24h", 0) or 1
    errors_24h = m.get("event_bus_errors_24h", 0) or 0
    if total_24h > 10 and (errors_24h / total_24h) > 0.15:
        alerts.append({
            "level": "WARN",
            "type": "event_bus_error_rate",
            "message": f"Event bus error rate: {errors_24h}/{total_24h} ({100*errors_24h//total_24h}%) in 24h",
            "action": "Review context_vault/events/system/events.jsonl for error patterns",
        })

    # --- Content queue empty ---
    if m.get("echoes_ready_to_post", 0) == 0:
        alerts.append({
            "level": "INFO",
            "type": "content_queue_empty",
            "message": "Echoes ready_to_post queue is empty",
            "action": "Run content pipeline: invoke_friday('Run content lab signal loop')",
        })

    # --- Doctor not run recently ---
    doctor_age = m.get("doctor_last_passed")
    if doctor_age is None or doctor_age > 24:
        alerts.append({
            "level": "WARN",
            "type": "doctor_stale",
            "message": f"Doctor last passed: {f'{doctor_age}h ago' if doctor_age else 'never'}",
            "action": "Run: invoke_friday('Run EPOS doctor scan')",
        })

    # --- Reactor position missing ---
    if m.get("reactor_position_age_h") is None:
        alerts.append({
            "level": "INFO",
            "type": "reactor_position_missing",
            "message": "No .reactor_position — daemon will reprocess full event bus on next restart",
            "action": "This is a known gap. Reactor position file is created on first run.",
        })

    # --- Stale threads ---
    stale = list_stale()
    if stale:
        alerts.append({
            "level": "INFO",
            "type": "stale_threads",
            "message": f"{len(stale)} thread(s) stale: {', '.join(t['id'] for t in stale[:3])}",
            "action": "Review and update or close stale threads",
        })

    # Publish all alerts to event bus
    if alerts and _BUS:
        try:
            _BUS.publish("friday.proactive.alerts", {
                "alert_count": len(alerts),
                "critical": sum(1 for a in alerts if a["level"] == "CRITICAL"),
                "alerts": alerts[:10],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, source_module="proactive_intelligence")
        except Exception:
            pass

    return alerts


def format_alerts(alerts: List[dict]) -> str:
    """Format alerts as a human-readable block."""
    if not alerts:
        return "No proactive alerts. All systems nominal."
    lines = [f"Proactive alerts ({len(alerts)}):"]
    for a in alerts:
        icon = {"CRITICAL": "🔴", "WARN": "🟡", "INFO": "🔵"}.get(a["level"], "⚪")
        lines.append(f"  {icon} [{a['level']}] {a['message']}")
        lines.append(f"     → {a['action']}")
    return "\n".join(lines)


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running proactive intelligence scan...")
    alerts = scan()
    print(format_alerts(alerts))
    print(f"\nPASS: proactive_intelligence ({len(alerts)} alerts)")
