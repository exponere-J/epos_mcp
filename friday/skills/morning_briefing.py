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


# ── PM Surface integration (Directive 20260414-03) ───────────────────────────

def get_pm_briefing() -> str:
    """Generate PM surface section for Friday morning briefing.

    Returns:
        Human-readable sentence(s) about current PM state.
    """
    try:
        from epos.pm.store import PMStore
        pm = PMStore()
        summary = pm.get_summary()

        total = summary.get("total_items", 0)
        if total == 0:
            return "Your PM surface is clear. No pending items."

        # Count across all tabs
        pending = in_progress = blocked = complete = 0
        tab_names = [k for k in summary if isinstance(summary[k], dict)]
        for tab_key in tab_names:
            tab = summary[tab_key]
            pending     += tab.get("pending", 0)
            in_progress += tab.get("in_progress", 0)
            blocked     += tab.get("blocked", 0)
            complete    += tab.get("complete", 0)

        briefing = f"You have {total} item{'s' if total != 1 else ''} across {len(tab_names)} tabs. "

        parts = []
        if pending:     parts.append(f"{pending} pending")
        if in_progress: parts.append(f"{in_progress} in progress")
        if blocked:     parts.append(f"{blocked} blocked")
        if complete:    parts.append(f"{complete} complete")
        if parts:
            briefing += ", ".join(parts) + "."

        if blocked > 0:
            briefing += (f" ATTENTION: {blocked} item{'s are' if blocked != 1 else ' is'} "
                         f"blocked and need{'s' if blocked == 1 else ''} your review.")

        return briefing

    except Exception as e:
        return f"PM surface unavailable: {str(e)[:100]}"


def get_reward_briefing() -> str:
    """Generate reward signal summary for Friday morning briefing.

    Returns:
        Human-readable reward bus status and QLoRA hold state.
    """
    try:
        from epos.rewards.reward_aggregator import aggregate_rewards
        summary = aggregate_rewards(window="today")

        if summary["total_signals"] == 0:
            return "No reward signals recorded today."

        briefing = (f"{summary['total_signals']} reward signal"
                    f"{'s' if summary['total_signals'] != 1 else ''} today. "
                    f"Net reward: {summary['net_reward']:+.2f}.")

        if summary.get("needs_review_count", 0) > 0:
            n = summary["needs_review_count"]
            briefing += (f" ATTENTION: {n} signal{'s' if n != 1 else ''} need"
                         f"{'s' if n == 1 else ''} review. "
                         f"QLoRA checkpoint deployment is held until reviewed.")

        if summary.get("top_negative_patterns"):
            top = summary["top_negative_patterns"][0]
            briefing += (f" Top gap: {top['pattern'].replace('_', ' ')} "
                         f"({top['count']} instance{'s' if top['count'] != 1 else ''}).")

        return briefing

    except Exception as e:
        return f"Reward summary unavailable: {str(e)[:100]}"


def get_decay_briefing() -> str:
    """Run confidence decay sweep and return status for morning briefing.

    Returns:
        Human-readable decay status sentence(s).
    """
    try:
        from epos.ccp.decay import get_decay_summary
        return get_decay_summary()
    except Exception as e:
        return f"Decay engine unavailable: {str(e)[:100]}"


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

    # Layer 4: PM Surface + Reward Bus + Decay (Directive 20260414-03)
    lines += ["", "## PM Surface"]
    lines.append(f"  {get_pm_briefing()}")

    lines += ["", "## Reward Bus"]
    lines.append(f"  {get_reward_briefing()}")

    lines += ["", "## Confidence Decay"]
    lines.append(f"  {get_decay_briefing()}")

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
        "pm_briefing": get_pm_briefing(),
        "reward_briefing": get_reward_briefing(),
        "decay_briefing": get_decay_briefing(),
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
