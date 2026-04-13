#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
morning_briefing.py — Friday Morning Briefing
===============================================
Constitutional Authority: EPOS Constitution v3.1

Assembles and delivers the daily morning briefing.
Pulls from: metrics_observatory, thread_tracker, proactive_intelligence.
Output written to context_vault/friday/briefings/<date>.md and event bus.

Triggered by: APScheduler at 06:00 America/New_York daily.
Can also be invoked manually: invoke_friday("morning briefing")
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
BRIEFINGS_DIR = VAULT / "friday" / "briefings"
BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)


def generate() -> dict:
    """
    Generate the morning briefing.
    Returns dict with keys: text, metrics, alerts, threads, path.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A %B %d, %Y")

    # 1. Metrics snapshot
    from friday.skills.metrics_observatory import snapshot, METRIC_DEFINITIONS
    metrics = snapshot()

    # 2. Proactive alerts
    from friday.skills.proactive_intelligence import scan, format_alerts
    alerts = scan()

    # 3. Thread summary
    from friday.skills.thread_tracker import list_open, list_stale, summary as thread_summary
    open_threads = list_open()
    stale_threads = list_stale()

    # Layer 3: External Market Awareness
    market_brief = ""
    market_signals = {}
    try:
        from friday.skills.research_scanner import FridayResearchScanner
        scanner = FridayResearchScanner()
        market_brief = scanner.generate_market_brief()
        market_signals = scanner.scan_market_signals()
    except Exception as _e:
        market_brief = f"Market scan unavailable: {_e}"

    # 4. Assemble text
    lines = [
        f"# Friday Morning Briefing — {date_str}",
        f"Generated: {now.isoformat()}",
        "",
        "## System Health",
    ]

    health_metrics = [
        ("epos_core_up", "EPOS Core"),
        ("litellm_up", "LiteLLM"),
        ("governance_gate_up", "Governance Gate"),
        ("learning_server_up", "Learning Server"),
    ]
    for key, label in health_metrics:
        val = metrics.get(key)
        icon = "✓" if val else "✗"
        lines.append(f"  {icon} {label}: {'UP' if val else 'DOWN'}")

    lines += [
        "",
        "## Activity (24h / 7d)",
        f"  Event bus entries (24h): {metrics.get('event_bus_entries_24h', 'N/A')}",
        f"  Event bus errors (24h):  {metrics.get('event_bus_errors_24h', 'N/A')}",
        f"  LLM requests (24h):      {metrics.get('llm_requests_24h', 'N/A')}",
        f"  Posts published (7d):    {metrics.get('posts_published_7d', 'N/A')}",
        f"  TTLG diagnostics (7d):  {metrics.get('ttlg_diagnostics_7d', 'N/A')}",
        f"  Git commits (7d):        {metrics.get('git_commits_7d', 'N/A')}",
        f"  Friday missions total:   {metrics.get('friday_missions_total', 'N/A')}",
        "",
        "## Content Pipeline",
        f"  Ready to post:     {metrics.get('echoes_ready_to_post', 'N/A')}",
        f"  Sparks (7d):       {metrics.get('sparks_generated_7d', 'N/A')}",
        f"  Briefs (7d):       {metrics.get('briefs_generated_7d', 'N/A')}",
    ]

    # Proactive alerts section
    lines += ["", "## Alerts"]
    if alerts:
        from friday.skills.proactive_intelligence import format_alerts
        lines.append(format_alerts(alerts))
    else:
        lines.append("  No alerts. All systems nominal.")

    # Threads section
    lines += ["", "## Open Threads"]
    if open_threads:
        for t in open_threads[:5]:
            stale_flag = " [STALE]" if t in stale_threads else ""
            lines.append(f"  {t['id']}: {t['title']}{stale_flag}")
        if len(open_threads) > 5:
            lines.append(f"  ... and {len(open_threads) - 5} more")
    else:
        lines.append("  No open threads.")

    # Layer 3: Market Awareness (research scanner)
    lines += ["", "## Market Awareness"]
    lines.append(f"  {market_brief}" if market_brief else "  No market signals available.")

    text = "\n".join(lines)

    # 5. Persist
    date_key = now.strftime("%Y-%m-%d")
    briefing_path = BRIEFINGS_DIR / f"{date_key}_morning_briefing.md"
    briefing_path.write_text(text, encoding="utf-8")

    # 6. Publish to event bus
    payload = {
        "date": date_key,
        "alert_count": len(alerts),
        "critical_alerts": sum(1 for a in alerts if a["level"] == "CRITICAL"),
        "open_threads": len(open_threads),
        "stale_threads": len(stale_threads),
        "epos_core_up": metrics.get("epos_core_up"),
        "market_signals": len(market_signals),
        "briefing_path": str(briefing_path),
        "timestamp": now.isoformat(),
    }
    if _BUS:
        try:
            _BUS.publish("friday.briefing.morning", payload, source_module="morning_briefing")
        except Exception:
            pass

    return {
        "text": text,
        "metrics": metrics,
        "alerts": alerts,
        "threads": open_threads,
        "market_awareness": {
            "market_brief": market_brief,
            "signals": market_signals,
        },
        "path": str(briefing_path),
        "date": date_key,
    }


def deliver() -> str:
    """Generate and return briefing text. Entry point for APScheduler."""
    result = generate()
    return result["text"]


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating morning briefing...")
    result = generate()
    print(result["text"])
    print(f"\nSaved to: {result['path']}")
    print(f"Alerts: {len(result['alerts'])} | Threads: {len(result['threads'])}")
    print("\nPASS: morning_briefing")
