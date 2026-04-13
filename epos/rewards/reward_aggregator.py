#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/rewards/reward_aggregator.py — Reward Signal Aggregator
=============================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-02 (Reward Bus Backwire)

Aggregates reward signals from all JSONL files for QLoRA consumption,
Friday briefing, and nightly training hold decisions.

Key behaviors:
  - Idempotent: deduplicates by timestamp + signal_name + trace_id
  - Window-aware: "today", "this_week", "all_time"
  - Escalation: sets qlora_deployment_held=True when needs_review > 0
  - Rotation: archives weekly files older than 4 weeks
  - Friday summary: human-readable text for morning briefing

Usage:
    from epos.rewards.reward_aggregator import aggregate_rewards, rotate_files

    summary = aggregate_rewards(window="today")
    if summary["qlora_deployment_held"]:
        print("HELD:", summary["needs_review_count"], "signals need review")

    rotate_files()  # Called by nightly cron
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
REWARDS_DIR = EPOS_ROOT / "context_vault" / "rewards"


def get_current_week() -> str:
    """Return current ISO week string: e.g. '2026W16'."""
    now = datetime.now(timezone.utc)
    return f"{now.year}W{now.isocalendar()[1]:02d}"


def _load_all_signals(rewards_dir: Path = None) -> List[dict]:
    """Load all reward signals from all weekly JSONL files."""
    base = rewards_dir or REWARDS_DIR
    signals = []
    if not base.exists():
        return signals
    for jsonl_file in sorted(base.glob("*_rewards_*.jsonl")):
        try:
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            signals.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except OSError:
            continue
    return signals


def _deduplicate(signals: List[dict]) -> List[dict]:
    """Remove duplicate signals by timestamp + signal_name + trace_id."""
    seen = set()
    unique = []
    for s in signals:
        key = f"{s.get('timestamp','')}|{s.get('signal_name','')}|{s.get('trace_id','')}"
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def _filter_by_window(signals: List[dict], window: str) -> List[dict]:
    """Filter signals by time window."""
    now = datetime.now(timezone.utc)
    if window == "today":
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
        return [s for s in signals if s.get("timestamp", "") >= cutoff]
    elif window == "this_week":
        week = get_current_week()
        return [s for s in signals if s.get("week") == week]
    elif window == "all_time":
        return signals
    else:
        return signals


def aggregate_rewards(
    window: str = "today",
    rewards_dir: Optional[Path] = None,
) -> dict:
    """
    Aggregate all reward signals for QLoRA consumption.

    Args:
        window: "today" | "this_week" | "all_time"
        rewards_dir: Override rewards directory (for testing)

    Returns:
        {
            "window": str,
            "generated_at": str,
            "total_signals": int,
            "net_reward": float,
            "by_source": {source: {"signals": N, "net": float}, ...},
            "by_type": {type: {"count": N, "net": float}, ...},
            "needs_review": [signal, ...],
            "needs_review_count": int,
            "qlora_deployment_held": bool,
            "top_negative_patterns": [{pattern, count, total}, ...],
            "qlora_targets": [signal_name, ...],
            "friday_summary": str,
        }
    """
    base = rewards_dir or REWARDS_DIR

    # Load + deduplicate + filter
    raw_signals = _load_all_signals(base)
    unique_signals = _deduplicate(raw_signals)
    signals = _filter_by_window(unique_signals, window)

    # Aggregate by source
    by_source: dict = defaultdict(lambda: {"signals": 0, "net": 0.0})
    for s in signals:
        src = s.get("source", "unknown")
        by_source[src]["signals"] += 1
        by_source[src]["net"] += s.get("value", 0.0)

    # Aggregate by type
    by_type: dict = defaultdict(lambda: {"count": 0, "net": 0.0})
    for s in signals:
        stype = s.get("signal_type", "unknown")
        by_type[stype]["count"] += 1
        by_type[stype]["net"] += s.get("value", 0.0)

    # Round net values
    for src in by_source:
        by_source[src]["net"] = round(by_source[src]["net"], 4)
    for stype in by_type:
        by_type[stype]["net"] = round(by_type[stype]["net"], 4)

    # Needs-review signals
    needs_review = [s for s in signals if s.get("needs_review")]

    # Top negative patterns
    neg_counts: dict = defaultdict(lambda: {"count": 0, "total": 0.0})
    for s in signals:
        if s.get("value", 0.0) < 0:
            name = s.get("signal_name", "unknown")
            neg_counts[name]["count"] += 1
            neg_counts[name]["total"] += s.get("value", 0.0)

    top_negatives = sorted(
        [{"pattern": k, **v} for k, v in neg_counts.items()],
        key=lambda x: x["total"]  # most negative first
    )[:5]

    for item in top_negatives:
        item["total"] = round(item["total"], 4)

    qlora_targets = [n["pattern"] for n in top_negatives]

    # Net reward
    net = round(sum(s.get("value", 0.0) for s in signals), 4)

    # QLoRA hold decision
    review_count = len(needs_review)
    qlora_held = review_count > 0

    # Friday summary (voice-readable)
    friday_summary = (
        f"{len(signals)} reward signal{'s' if len(signals) != 1 else ''} "
        f"recorded {window.replace('_', ' ')}. "
        f"Net reward: {net:+.2f}."
    )
    if review_count > 0:
        friday_summary += (
            f" ATTENTION: {review_count} signal{'s' if review_count != 1 else ''} "
            f"need{'s' if review_count == 1 else ''} your review. "
            f"QLoRA checkpoint deployment is held until reviewed."
        )
    if top_negatives:
        p = top_negatives[0]
        friday_summary += (
            f" Top gap: {p['pattern'].replace('_', ' ')} "
            f"({p['count']} instance{'s' if p['count'] != 1 else ''}, "
            f"total {p['total']:+.2f})."
        )

    return {
        "window": window,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_signals": len(signals),
        "net_reward": net,
        "by_source": dict(by_source),
        "by_type": dict(by_type),
        "needs_review": needs_review,
        "needs_review_count": review_count,
        "qlora_deployment_held": qlora_held,
        "top_negative_patterns": top_negatives,
        "qlora_targets": qlora_targets,
        "friday_summary": friday_summary,
    }


def rotate_files(rewards_dir: Optional[Path] = None, keep_weeks: int = 4) -> dict:
    """
    Archive weekly JSONL files older than keep_weeks.
    Current week is always kept. Returns rotation summary.

    Args:
        rewards_dir: Override rewards directory (for testing)
        keep_weeks: Number of recent weeks to keep (default: 4)

    Returns:
        {"archived": [filename, ...], "kept": [filename, ...]}
    """
    base = rewards_dir or REWARDS_DIR
    archive_dir = base / "archive"
    current_week = get_current_week()

    # Parse year+week from filename: {source}_rewards_{year}W{week}.jsonl
    now = datetime.now(timezone.utc)
    current_year, current_week_num, _ = now.isocalendar()

    archived = []
    kept = []

    if not base.exists():
        return {"archived": [], "kept": []}

    for jsonl_file in base.glob("*_rewards_*.jsonl"):
        stem = jsonl_file.stem  # e.g. "voice_rewards_2026W16"
        parts = stem.rsplit("_", 1)
        if len(parts) != 2:
            kept.append(jsonl_file.name)
            continue

        week_str = parts[1]  # e.g. "2026W16"
        try:
            year_part, week_part = week_str.split("W")
            file_year = int(year_part)
            file_week = int(week_part)
        except (ValueError, AttributeError):
            kept.append(jsonl_file.name)
            continue

        # Calculate weeks ago
        weeks_ago = (current_year - file_year) * 52 + (current_week_num - file_week)

        if weeks_ago > keep_weeks:
            archive_dir.mkdir(parents=True, exist_ok=True)
            dest = archive_dir / jsonl_file.name
            try:
                jsonl_file.rename(dest)
                archived.append(jsonl_file.name)
            except OSError:
                kept.append(jsonl_file.name)
        else:
            kept.append(jsonl_file.name)

    return {"archived": archived, "kept": kept}


def check_qlora_hold() -> bool:
    """
    Nightly training script calls this to check if deployment should be held.

    Usage in nightly_training.py:
        from epos.rewards.reward_aggregator import check_qlora_hold
        if check_qlora_hold():
            print("HELD: needs_review signals unresolved")
            sys.exit(0)  # Training runs but checkpoint does not deploy

    Returns:
        True if QLoRA checkpoint deployment should be held
    """
    summary = aggregate_rewards(window="this_week")
    return summary["qlora_deployment_held"]
