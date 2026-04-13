#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/rewards/publish_reward.py — Universal Reward Signal Publisher
===================================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-02 (Reward Bus Backwire)

Single function used by every EPOS system to publish reward signals.
All signals conform to the universal schema and are written to weekly
rotating JSONL files under context_vault/rewards/.

Signal schema:
    {
        "timestamp": "2026-04-14T08:30:00Z",
        "week": "2026W16",
        "directive_id": "20260414-02",
        "trace_id": "evt-uuid-from-event-bus",
        "source": "voice_pipeline|sanitation|shadow_protocol|ccp|pm_surface",
        "signal_type": "process|outcome|negative|compound",
        "signal_name": "raw_capture_saved",
        "value": 0.2,
        "context": "Voice session CAP-20260414T083000Z: audio + metadata saved",
        "needs_review": false
    }

needs_review is set TRUE when:
  - process_score > 0.5 AND outcome_score < 0 (good habits, bad result)
  - Any negative signal with value < -0.3
  - Any signal where Jamie overrode the system's suggestion

Storage: context_vault/rewards/{source}_rewards_{week}.jsonl
Rotation: Weekly files, archived after 4 weeks (see reward_aggregator.py)
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
REWARDS_DIR = EPOS_ROOT / "context_vault" / "rewards"


def get_current_week() -> str:
    """Return current ISO week string: e.g. '2026W16'."""
    now = datetime.now(timezone.utc)
    return f"{now.year}W{now.isocalendar()[1]:02d}"


def publish_reward(
    signal_name: str,
    value: float,
    signal_type: str = "process",
    source: str = "unknown",
    directive_id: Optional[str] = None,
    context: str = "",
    needs_review: bool = False,
    trace_id: Optional[str] = None,
    auto_flag_negative: bool = True,
) -> dict:
    """
    Publish a reward signal to the organism's learning pipeline.

    Writes to context_vault/rewards/{source}_rewards_{week}.jsonl.
    Thread-safe: each write is a single append (atomic on POSIX).

    Args:
        signal_name:    Human-readable signal identifier
                        (e.g. "raw_capture_saved", "scc_produced_stub")
        value:          Reward value (-1.0 to +1.0 typical; no hard limit)
        signal_type:    "process" | "outcome" | "negative" | "compound"
        source:         Originating system
                        (voice_pipeline | sanitation | shadow_protocol | ccp | pm_surface)
        directive_id:   Active directive (falls back to ACTIVE_DIRECTIVE env var)
        context:        Human-readable context string (max ~200 chars)
        needs_review:   Force review flag (also auto-set for value < -0.3)
        trace_id:       Event bus trace ID for correlation (auto-generated if None)
        auto_flag_negative: Auto-set needs_review=True when value < -0.3

    Returns:
        The published signal dict (also written to JSONL)
    """
    REWARDS_DIR.mkdir(parents=True, exist_ok=True)

    week = get_current_week()

    # Auto-flag strongly negative signals for review
    if auto_flag_negative and value < -0.3:
        needs_review = True

    signal = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "week": week,
        "directive_id": directive_id or os.getenv("ACTIVE_DIRECTIVE", "unknown"),
        "trace_id": trace_id or str(uuid.uuid4())[:8],
        "source": source,
        "signal_type": signal_type,
        "signal_name": signal_name,
        "value": round(float(value), 4),
        "context": context[:300],
        "needs_review": needs_review,
    }

    # Write to source-specific weekly file
    filepath = REWARDS_DIR / f"{source}_rewards_{week}.jsonl"
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal) + "\n")
    except OSError:
        # Non-fatal: reward logging must never crash the caller
        pass

    return signal
