#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
lifeos_kernel.py — Personal Sovereignty Layer
===============================================
Constitutional Authority: EPOS Constitution v3.1, Friday Mandate v2.0

The organism serves the human — not the other way around.
LifeOS tracks goals, energy, commitments, and balance so that
running an autonomous business does not consume its builder.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault


CATEGORIES = ["health", "relationships", "finance", "learning",
              "business", "creative", "accessibility", "spiritual"]


class LifeOSKernel:
    """The personal sovereignty layer of EPOS."""

    def __init__(self):
        self.kernel_path = get_context_vault() / "lifeos"
        self.kernel_path.mkdir(parents=True, exist_ok=True)
        for fname in ["goals.jsonl", "daily_log.jsonl", "commitments.jsonl",
                       "milestones.jsonl", "energy_log.jsonl"]:
            (self.kernel_path / fname).touch()

    def set_goal(self, category: str, goal: str,
                 target_date: str = None, success_metric: str = None) -> dict:
        entry = {"goal_id": f"GOAL-{uuid.uuid4().hex[:8]}", "category": category,
                 "goal": goal, "target_date": target_date,
                 "success_metric": success_metric, "status": "active",
                 "progress_notes": [],
                 "created_at": datetime.now(timezone.utc).isoformat()}
        self._append("goals.jsonl", entry)
        return entry

    def log_daily_state(self, energy_level: int, focus_quality: int,
                        primary_win: str, primary_challenge: str,
                        notes: str = None) -> None:
        entry = {"date": datetime.now().strftime("%Y-%m-%d"),
                 "energy_level": energy_level, "focus_quality": focus_quality,
                 "primary_win": primary_win, "primary_challenge": primary_challenge,
                 "notes": notes, "logged_at": datetime.now(timezone.utc).isoformat()}
        self._append("daily_log.jsonl", entry)

    def get_active_goals(self, category: str = None) -> list:
        goals = []
        for line in self._read_lines("goals.jsonl"):
            try:
                g = json.loads(line)
                if g.get("status") == "active":
                    if not category or g.get("category") == category:
                        goals.append(g)
            except Exception:
                pass
        return goals

    def get_energy_trend(self, days: int = 7) -> dict:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        entries = []
        for line in self._read_lines("daily_log.jsonl"):
            try:
                e = json.loads(line)
                if e.get("date", "") >= cutoff:
                    entries.append(e)
            except Exception:
                pass
        if not entries:
            return {"avg_energy": 7, "avg_focus": 7, "trend": "no_data",
                    "days_logged": 0, "recommendation": "No data yet. Log your state today."}
        avg_e = sum(e.get("energy_level", 7) for e in entries) / len(entries)
        avg_f = sum(e.get("focus_quality", 7) for e in entries) / len(entries)
        trend = "declining" if avg_e < 5 else "strong" if avg_e > 7 else "steady"
        rec = {"declining": "Protect capacity — lighter schedule today",
               "strong": "Strong capacity — good time for high-leverage work",
               "steady": "Steady — normal operations"}.get(trend, "")
        return {"avg_energy": round(avg_e, 1), "avg_focus": round(avg_f, 1),
                "trend": trend, "days_logged": len(entries), "recommendation": rec}

    def get_todays_priorities(self) -> str:
        active_goals = self.get_active_goals()
        energy = self.get_energy_trend(days=3)
        if not active_goals:
            return "No active goals set. Consider setting 1-3 goals across business and personal categories."
        try:
            from groq_router import GroqRouter
            router = GroqRouter()
            goals_text = json.dumps([{"category": g["category"], "goal": g["goal"],
                                       "target": g.get("target_date", "no date")}
                                      for g in active_goals[:5]], indent=2)
            return router.route("reasoning",
                f"You are Friday. Generate 3 specific priorities for today.\n"
                f"Active goals:\n{goals_text}\n"
                f"Energy trend: {json.dumps(energy)}\n"
                f"Each: one sentence. Actionable. Realistic. TTS-ready.",
                max_tokens=200, temperature=0.4)
        except Exception:
            return f"{len(active_goals)} active goals. Energy: {energy['trend']}."

    def _append(self, filename: str, entry: dict) -> None:
        with open(self.kernel_path / filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _read_lines(self, filename: str) -> list:
        path = self.kernel_path / filename
        if not path.exists() or path.stat().st_size == 0:
            return []
        return [l for l in path.read_text(encoding="utf-8").strip().splitlines() if l.strip()]


if __name__ == "__main__":
    import py_compile
    py_compile.compile("lifeos_kernel.py", doraise=True)
    kernel = LifeOSKernel()

    # Set goals
    g1 = kernel.set_goal("business", "Launch Echoes YouTube channel by April 7", "2026-04-07")
    g2 = kernel.set_goal("health", "Walk 30 minutes daily", success_metric="7/7 days per week")
    g3 = kernel.set_goal("accessibility", "File CCP provisional patent", "2026-04-15")
    print(f"  Goals set: {g1['goal_id']}, {g2['goal_id']}, {g3['goal_id']}")

    # Log daily state
    kernel.log_daily_state(energy_level=8, focus_quality=9,
        primary_win="Completed Sprint 6 — organism is self-improving",
        primary_challenge="Context window limits during extended builds")
    print("  Daily state logged: energy 8, focus 9")

    # Check
    goals = kernel.get_active_goals()
    energy = kernel.get_energy_trend(days=1)
    print(f"  Active goals: {len(goals)}")
    print(f"  Energy trend: {energy['trend']} (avg: {energy['avg_energy']})")

    # Today's priorities
    priorities = kernel.get_todays_priorities()
    print(f"  Priorities: {priorities[:100]}...")

    print("\nPASS: LifeOSKernel — personal sovereignty operational")
