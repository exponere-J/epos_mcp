#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/ccp/decay.py — Confidence Decay Engine
============================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-03 (Integration Wiring + Confidence Decay)

Prevents stale PM elements from accumulating. Elements lose confidence
over time if not acted upon. When confidence drops below 0.50, the element
is auto-archived to stale_elements.jsonl and Friday is notified.

Decay schedule (per 12-hour window):
  0-24h:   No decay — element is fresh
  24-48h:  -0.05 per 12h — gentle nudge
  48-72h:  -0.10 per 12h — urgency increases
  72h+:    -0.15 per 12h — element going stale

Exemptions:
  - status "confirmed" or "in_progress" → NO DECAY (locked)
  - status "blocked" → paused (not decaying, but Friday alerts)
  - type "decision" → 50% decay rate (decisions age slower)
  - type "constitutional_proposal" → NO DECAY (governance is permanent)

Wire into daemon: every 12 hours via APScheduler.
Wire into Friday: get_decay_summary() in morning_briefing.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
PM_DIR = EPOS_ROOT / "context_vault" / "pm"
STALE_ARCHIVE = PM_DIR / "stale_elements.jsonl"

# ── Reward bus ────────────────────────────────────────────────────────────────
try:
    from epos.rewards.publish_reward import publish_reward as _pub_reward
    def _reward(signal_name: str, value: float, signal_type: str = "process",
                context: str = "", needs_review: bool = False) -> None:
        try:
            _pub_reward(signal_name=signal_name, value=value,
                        signal_type=signal_type, source="decay_engine",
                        context=context, needs_review=needs_review)
        except Exception:
            pass
except ImportError:
    def _reward(*a, **kw): pass

# ── Decay configuration ───────────────────────────────────────────────────────

# (hours_threshold, decay_per_12h)
# Decay accumulates as: sum of (hours_in_band / 12) * rate
DECAY_SCHEDULE = [
    (24,          0.00),   # 0-24h: no decay
    (48,          0.05),   # 24-48h: gentle
    (72,          0.10),   # 48-72h: moderate
    (float("inf"), 0.15),  # 72h+: aggressive
]

SLOW_DECAY_TYPES = {"decision"}               # 50% rate
NO_DECAY_TYPES = {"constitutional_proposal"}  # never expires
DECAY_EXEMPT_STATUSES = {"confirmed", "in_progress"}
DECAY_PAUSED_STATUSES = {"blocked"}           # no decay, but Friday alerts

ARCHIVE_THRESHOLD = 0.50    # auto-archive when confidence drops below this
AGING_THRESHOLD = 0.70      # "aging — review or discard" warning band

PM_TABS = [
    "action_items",
    "decisions",
    "research_queue",
    "blockers",
    "idea_pipeline",
    "client_insights",
]


# ── Core decay math ───────────────────────────────────────────────────────────

def calculate_decay(
    original_confidence: float,
    hours_since_creation: float,
    element_type: str = "",
    status: str = "pending",
) -> float:
    """Calculate decayed confidence for an element.

    Args:
        original_confidence: Confidence at extraction time (0.0–1.0)
        hours_since_creation: Age of element in hours
        element_type: CCP element type string
        status: Current PM status

    Returns:
        Decayed confidence value (0.0–1.0), rounded to 3 decimal places
    """
    # Exemptions
    if element_type in NO_DECAY_TYPES:
        return original_confidence
    if status in DECAY_EXEMPT_STATUSES:
        return original_confidence
    if status in DECAY_PAUSED_STATUSES:
        return original_confidence  # paused — Friday alerts separately

    # Accumulate decay across schedule bands
    total_decay = 0.0
    remaining_hours = hours_since_creation
    prev_threshold = 0.0

    for threshold, rate_per_12h in DECAY_SCHEDULE:
        if remaining_hours <= 0:
            break
        hours_in_band = min(remaining_hours, threshold - prev_threshold)
        periods = hours_in_band / 12.0
        total_decay += periods * rate_per_12h
        remaining_hours -= hours_in_band
        prev_threshold = threshold

    # Slow-decay types get half the rate
    if element_type in SLOW_DECAY_TYPES:
        total_decay *= 0.5

    decayed = max(0.0, original_confidence - total_decay)
    return round(decayed, 3)


# ── Decay sweep ───────────────────────────────────────────────────────────────

def apply_decay_sweep(pm_dir: Optional[Path] = None) -> dict:
    """Sweep all PM tabs, apply decay, archive expired elements.

    Called every 12 hours by EPOS daemon scheduler.

    Returns:
        {
            "swept_tabs": int,
            "expired_count": int,
            "decayed_count": int,
            "blocked_count": int,
            "archived_to": str | None,
        }
    """
    base = pm_dir or PM_DIR
    now = datetime.now(timezone.utc)
    expired = []
    decayed_items = []
    blocked_alerts = []

    for tab_name in PM_TABS:
        tab_file = base / f"{tab_name}.json"
        if not tab_file.exists():
            continue

        try:
            data = json.loads(tab_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        items = data.get("items", []) if isinstance(data, dict) else data
        updated_items = []

        for item in items:
            # Parse age
            raw_ts = item.get("created_at", now.isoformat()).replace("Z", "+00:00")
            try:
                created = datetime.fromisoformat(raw_ts)
                # Ensure timezone-aware
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
            except Exception:
                created = now

            hours_age = (now - created).total_seconds() / 3600.0

            # Get confidence values
            original_conf = item.get("original_confidence",
                                     item.get("confidence", 1.0))
            el_type = item.get("element_type", item.get("type", ""))
            status = item.get("status", "pending")

            current_conf = calculate_decay(
                original_confidence=original_conf,
                hours_since_creation=hours_age,
                element_type=el_type,
                status=status,
            )

            # Track blocked items for Friday alert
            if status in DECAY_PAUSED_STATUSES:
                blocked_alerts.append(item)

            item["confidence"] = current_conf
            item["hours_age"] = round(hours_age, 1)

            if current_conf < ARCHIVE_THRESHOLD:
                # Archive expired element
                expired.append({"tab": tab_name, "item": item})
                archive_entry = {
                    "archived_at": now.isoformat(),
                    "reason": "confidence_decay",
                    "tab": tab_name,
                    "original_confidence": original_conf,
                    "final_confidence": current_conf,
                    "hours_age": round(hours_age, 1),
                    "element": item,
                }
                STALE_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
                with open(STALE_ARCHIVE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(archive_entry) + "\n")

                _reward("element_expired_unreviewed", -0.2,
                        signal_type="negative",
                        context=f"Expired [{tab_name}]: type={el_type} "
                                f"conf {original_conf:.2f}→{current_conf:.2f} "
                                f"after {hours_age:.0f}h",
                        needs_review=True)
            else:
                if current_conf < original_conf:
                    decayed_items.append({
                        "tab": tab_name,
                        "id": item.get("id"),
                        "decay": round(original_conf - current_conf, 3),
                    })
                updated_items.append(item)

        # Rewrite tab without expired items
        if isinstance(data, dict):
            data["items"] = updated_items
            data["updated_at"] = now.isoformat()
            tab_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            tab_file.write_text(json.dumps(updated_items, indent=2), encoding="utf-8")

    return {
        "swept_tabs": len(PM_TABS),
        "expired_count": len(expired),
        "decayed_count": len(decayed_items),
        "blocked_count": len(blocked_alerts),
        "archived_to": str(STALE_ARCHIVE) if expired else None,
        "sweep_at": now.isoformat(),
    }


# ── Friday briefing integration ───────────────────────────────────────────────

def get_decay_summary(pm_dir: Optional[Path] = None) -> str:
    """Run decay sweep and return human-readable status for Friday briefing.

    Returns:
        Single-sentence string suitable for voice delivery.
    """
    try:
        result = apply_decay_sweep(pm_dir=pm_dir)
    except Exception as e:
        return f"Decay engine error: {str(e)[:80]}"

    expired = result["expired_count"]
    decayed = result["decayed_count"]
    blocked = result["blocked_count"]

    parts = []

    if expired > 0:
        parts.append(
            f"ATTENTION: {expired} element{'s' if expired != 1 else ''} "
            f"expired from confidence decay and archived to stale_elements.jsonl."
        )

    if blocked > 0:
        parts.append(
            f"{blocked} item{'s are' if blocked != 1 else ' is'} blocked and paused from decay — "
            f"review required."
        )

    if decayed > 0 and expired == 0:
        parts.append(
            f"{decayed} element{'s are' if decayed != 1 else ' is'} showing confidence decay — "
            f"review pending items to prevent expiration."
        )

    if not parts:
        return "All PM elements are fresh. No decay detected."

    return " ".join(parts)


# ── Verification helper ───────────────────────────────────────────────────────

def verify_decay(original_confidence: float, hours_ago: float,
                 element_type: str = "", status: str = "pending") -> dict:
    """Compute expected decay for a given scenario. Used in tests.

    Example:
        verify_decay(0.95, 36)  # → ~0.85 (2 periods × 0.05 in 24-48h band)
        verify_decay(0.70, 80)  # → < 0.50 (archived after 80h)
    """
    decayed = calculate_decay(original_confidence, hours_ago, element_type, status)
    return {
        "original": original_confidence,
        "hours_ago": hours_ago,
        "element_type": element_type,
        "status": status,
        "decayed_confidence": decayed,
        "net_decay": round(original_confidence - decayed, 3),
        "will_archive": decayed < ARCHIVE_THRESHOLD,
        "is_aging": ARCHIVE_THRESHOLD <= decayed < AGING_THRESHOLD,
    }


if __name__ == "__main__":
    # Quick self-test
    print("=== Decay Engine Self-Test ===")

    # Scenario 1: 36h old, confidence 0.95
    # Band breakdown: 0-24h=0 decay, 24-36h=1 period×0.05=0.05 → 0.90
    r1 = verify_decay(0.95, 36)
    expected1 = 0.90
    ok1 = abs(r1["decayed_confidence"] - expected1) < 0.01
    print(f"  36h: {r1['original']} → {r1['decayed_confidence']} "
          f"(expected ~{expected1}) {'PASS' if ok1 else 'FAIL'}")

    # Scenario 2: 80h old, confidence 0.70 → should be < 0.50
    r2 = verify_decay(0.70, 80)
    ok2 = r2["decayed_confidence"] < 0.50
    print(f"  80h: {r2['original']} → {r2['decayed_confidence']} "
          f"(expected < 0.50) {'PASS' if ok2 else 'FAIL'}")

    # Scenario 3: decision, 80h, 0.70 → slow decay, should NOT be < 0.50
    r3 = verify_decay(0.70, 80, element_type="decision")
    ok3 = r3["decayed_confidence"] >= 0.50
    print(f"  80h decision: {r3['original']} → {r3['decayed_confidence']} "
          f"(expected ≥ 0.50 slow decay) {'PASS' if ok3 else 'FAIL'}")

    # Scenario 4: constitutional_proposal, 200h → NO decay
    r4 = verify_decay(0.95, 200, element_type="constitutional_proposal")
    ok4 = r4["decayed_confidence"] == 0.95
    print(f"  200h constitution: {r4['original']} → {r4['decayed_confidence']} "
          f"(expected 0.95 no decay) {'PASS' if ok4 else 'FAIL'}")

    passed = sum([ok1, ok2, ok3, ok4])
    print(f"\n{passed}/4 scenarios correct")
    print("\nPASS: decay engine" if passed == 4 else "\nFAIL: decay engine")
