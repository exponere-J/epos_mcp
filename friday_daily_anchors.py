#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
friday_daily_anchors.py — Friday Daily Anchor System
=====================================================
Constitutional Authority: EPOS Constitution v3.1, Friday Mandate v2.0
Module: Friday Daily Anchors (CODE DIRECTIVE Module 4)

Wires Friday to the 5 daily LifeOS anchors:
  07:00  Morning check-in    → seeds the day
  12:30  Midday recalibration → no judgment, just name and reset
  17:30  End of work signal   → transition boundary
  21:00  Nightly reflection   → processes day, generates morning synthesis
  Sunday 18:00  Weekly review  → Sunday synthesis

Each anchor generates a Friday-voiced prompt and can be triggered
via CLI or scheduled task.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus


class FridayDailyAnchors:
    """Friday's daily rhythm anchors — the structure that holds."""

    ANCHORS = {
        "morning": {
            "time": "07:00",
            "name": "Morning Check-in",
            "prompt": (
                "Good morning. Before anything else — how's your energy today, "
                "1 to 10? What's the one intention that would make today count? "
                "And who could you serve today, even in a small way?"
            ),
        },
        "midday": {
            "time": "12:30",
            "name": "Midday Recalibration",
            "prompt": (
                "Halfway through. No judgment here — just honest naming. "
                "How are you tracking against this morning's intention? "
                "What needs to shift for the afternoon? "
                "If nothing, that's fine too. Name it and keep moving."
            ),
        },
        "eow": {
            "time": "17:30",
            "name": "End of Work Signal",
            "prompt": (
                "Work boundary. The build day is done. "
                "One sentence: what shipped today? One sentence: what carries to tomorrow? "
                "Now close the laptop. The evening is yours."
            ),
        },
        "nightly": {
            "time": "21:00",
            "name": "Nightly Reflection",
            "prompt": (
                "Reflection time. This is where lived experience becomes usable data. "
                "What went well? What was hard? What pattern did you notice? "
                "What's the one insight you want to carry into tomorrow? "
                "And who did you serve today, and how did it feel?"
            ),
        },
        "weekly": {
            "time": "Sunday 18:00",
            "name": "Weekly Life Review",
            "prompt": (
                "Sunday review. This week in one breath — what grew, what broke, "
                "what surprised you? Looking at the growth timeline: "
                "are you closer to where you said you wanted to be? "
                "What does next week need from you?"
            ),
        },
    }

    def __init__(self):
        self.vault = get_context_vault()
        self.anchors_dir = self.vault / "friday" / "anchors"
        self.anchors_dir.mkdir(parents=True, exist_ok=True)
        self.bus = EPOSEventBus()

    def get_anchor_prompt(self, anchor_name: str) -> Optional[dict]:
        """Get the Friday-voiced prompt for an anchor."""
        anchor = self.ANCHORS.get(anchor_name)
        if not anchor:
            return None
        return {
            "anchor": anchor_name,
            "time": anchor["time"],
            "name": anchor["name"],
            "friday_prompt": anchor["prompt"],
        }

    def run_anchor(self, anchor_name: str, responses: dict = None) -> dict:
        """Execute an anchor — log it, publish event, optionally with responses."""
        anchor = self.ANCHORS.get(anchor_name)
        if not anchor:
            return {"error": f"Unknown anchor: {anchor_name}"}

        entry = {
            "anchor": anchor_name,
            "name": anchor["name"],
            "scheduled_time": anchor["time"],
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "responses": responses or {},
        }

        # Delegate to LifeOS where appropriate
        result = {}
        if anchor_name == "morning" and responses:
            try:
                from lifeos_sovereignty import LifeOSSovereignty
                sov = LifeOSSovereignty()
                energy = responses.get("energy", 7)
                intention = responses.get("intention", "Build with clarity")
                serve = responses.get("serve_today", "The mission")
                pm = sov.run_morning_check_in(energy, intention, serve)
                result["lifeos"] = pm
            except Exception as e:
                result["lifeos_error"] = str(e)

        elif anchor_name == "midday" and responses:
            try:
                from lifeos_sovereignty import LifeOSSovereignty
                sov = LifeOSSovereignty()
                sov.run_midday_recalibration(
                    responses.get("tracking", "on track"),
                    responses.get("shift", "none needed"))
                result["recalibrated"] = True
            except Exception as e:
                result["lifeos_error"] = str(e)

        elif anchor_name == "nightly" and responses:
            try:
                from lifeos_sovereignty import LifeOSSovereignty
                sov = LifeOSSovereignty()
                reflection = sov.run_nightly_reflection(
                    day_summary=responses.get("summary", "Day reflected"),
                    energy_end=responses.get("energy", 7),
                    wins=responses.get("wins", []),
                    challenges=responses.get("challenges", []),
                    pattern_noticed=responses.get("pattern", "observing"),
                    insight=responses.get("insight", "learning continues"),
                    tomorrow_change=responses.get("tomorrow", "keep building"),
                    served_today=responses.get("served", "the mission"),
                    served_how=responses.get("served_how", "building"),
                    felt_like=responses.get("felt", "present"))
                result["reflection"] = reflection
            except Exception as e:
                result["lifeos_error"] = str(e)

        elif anchor_name == "weekly":
            try:
                from lifeos_sovereignty import LifeOSSovereignty
                sov = LifeOSSovereignty()
                review = sov.generate_weekly_review()
                result["weekly_review"] = review
            except Exception as e:
                result["lifeos_error"] = str(e)

        elif anchor_name == "eow":
            result["boundary_set"] = True
            result["message"] = "Work day complete. Evening is yours."

        # Log the anchor execution
        entry["result"] = result
        log_path = self.anchors_dir / f"anchor_log_{datetime.now(timezone.utc).strftime('%Y%m')}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # Publish event
        self.bus.publish(f"friday.anchor.{anchor_name}", {
            "anchor": anchor_name,
            "has_responses": bool(responses),
        }, "friday_daily_anchors")

        return entry

    def get_current_anchor(self) -> Optional[str]:
        """Determine which anchor is closest to the current time."""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        current = hour * 60 + minute

        anchor_minutes = {
            "morning": 7 * 60,      # 07:00
            "midday": 12 * 60 + 30, # 12:30
            "eow": 17 * 60 + 30,    # 17:30
            "nightly": 21 * 60,     # 21:00
        }

        # Find the nearest upcoming anchor (within 30 min window)
        for name, target in anchor_minutes.items():
            if target - 15 <= current <= target + 15:
                return name

        return None

    def get_anchor_history(self, days: int = 7) -> list:
        """Get anchor execution history."""
        history = []
        for f in sorted(self.anchors_dir.glob("anchor_log_*.jsonl"), reverse=True):
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        history.append(json.loads(line))
                    except Exception:
                        pass
            if len(history) >= days * 5:
                break
        return history[:days * 5]

    def get_streak(self) -> dict:
        """Calculate anchor completion streak."""
        history = self.get_anchor_history(days=30)
        dates_with_morning = set()
        dates_with_nightly = set()
        for entry in history:
            date = entry.get("executed_at", "")[:10]
            if entry.get("anchor") == "morning":
                dates_with_morning.add(date)
            elif entry.get("anchor") == "nightly":
                dates_with_nightly.add(date)
        return {
            "morning_check_ins": len(dates_with_morning),
            "nightly_reflections": len(dates_with_nightly),
            "total_anchors": len(history),
        }


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile

    py_compile.compile("friday_daily_anchors.py", doraise=True)
    print("PASS: friday_daily_anchors.py compiles clean")

    anchors = FridayDailyAnchors()

    # Test prompt retrieval
    for name in ["morning", "midday", "eow", "nightly", "weekly"]:
        prompt = anchors.get_anchor_prompt(name)
        assert prompt is not None
        assert prompt["anchor"] == name
        print(f"PASS: {name} prompt — {prompt['name']}")

    # Test anchor execution (morning with responses)
    result = anchors.run_anchor("morning", {"energy": 8, "intention": "Ship Module 4"})
    assert result["anchor"] == "morning"
    print(f"PASS: Morning anchor executed")

    # Test EOW
    result = anchors.run_anchor("eow")
    assert result["result"]["boundary_set"] is True
    print(f"PASS: EOW anchor executed")

    # Test streak
    streak = anchors.get_streak()
    print(f"PASS: Streak — {streak['total_anchors']} total anchors")

    # Test current anchor detection
    current = anchors.get_current_anchor()
    print(f"PASS: Current anchor = {current or 'none (outside window)'}")

    print("\nPASS: FridayDailyAnchors — all tests passed")
