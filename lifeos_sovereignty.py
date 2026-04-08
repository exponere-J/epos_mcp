#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
lifeos_sovereignty.py - Personal Sovereignty Integration Layer
Constitutional Authority: EPOS Constitution v3.1, Friday Mandate v2.0

The organism serves the human. This module connects daily rhythm,
calendar, relationships, reflections, and growth timeline into
one coherent operating loop. Friday calls this at each anchor.

The person using this system is not broken. They are becoming.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus


class LifeOSSovereignty:
    """Integration layer connecting all LifeOS components."""

    def __init__(self):
        self.vault = get_context_vault()
        self.root = self.vault / "lifeos"
        self.root.mkdir(parents=True, exist_ok=True)
        for d in ["reflections", "relationships", "calendar", "milestones"]:
            (self.root / d).mkdir(parents=True, exist_ok=True)
        for f in ["daily_log.jsonl", "growth_timeline.jsonl", "relationship_os.jsonl",
                   "kaizen_log.jsonl", "service_ledger.jsonl", "hard_things.jsonl",
                   "accountability_mirror.jsonl"]:
            (self.root / f).touch()

    # ── MORNING CHECK-IN ──────────────────────────────────

    def run_morning_check_in(self, energy: int, intention: str,
                              serve_today: str, notes: str = None) -> dict:
        from lifeos_kernel import LifeOSKernel
        kernel = LifeOSKernel()
        kernel.log_daily_state(energy, energy, intention, "", notes)

        adjustment = None
        if energy <= 4:
            adjustment = "Low energy. Deep work deferred. Connect and Maintain prioritized."

        priorities = kernel.get_todays_priorities()
        gesture = self.get_relationship_gesture_due()

        pm = {"date": datetime.now().strftime("%Y-%m-%d"), "energy": energy,
              "intention": intention, "serve_today": serve_today,
              "calendar_adjustment": adjustment, "priorities": priorities,
              "relationship_gesture": gesture,
              "generated_at": datetime.now(timezone.utc).isoformat()}

        (self.root / f"pm_{datetime.now().strftime('%Y%m%d')}.json").write_text(
            json.dumps(pm, indent=2), encoding="utf-8")

        EPOSEventBus().publish("lifeos.morning_checkin.complete",
                               {"energy": energy, "intention": intention},
                               "lifeos_sovereignty")
        return pm

    # ── MIDDAY RECALIBRATION ──────────────────────────────

    def run_midday_recalibration(self, what_happened: str,
                                  afternoon_change: str = None) -> dict:
        recal = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "what_happened": what_happened, "afternoon_change": afternoon_change}
        (self.root / f"recal_{datetime.now().strftime('%Y%m%d')}.json").write_text(
            json.dumps(recal, indent=2), encoding="utf-8")
        return {"response": afternoon_change or "Afternoon continues as planned.", "recal": recal}

    # ── NIGHTLY REFLECTION ────────────────────────────────

    def run_nightly_reflection(self, day_summary: str, energy_end: int,
                                wins: list, challenges: list,
                                pattern_noticed: str, insight: str,
                                tomorrow_change: str, served_today: str,
                                served_how: str, felt_like: str,
                                hard_thing_done: str = None,
                                accountability: str = None,
                                is_breakthrough: bool = False,
                                breakthrough_description: str = None,
                                tomorrow_intention: str = None,
                                tomorrow_word: str = None) -> dict:
        date_str = datetime.now().strftime("%Y-%m-%d")
        reflection = {
            "date": date_str, "energy_end": energy_end, "day_summary": day_summary,
            "wins": wins, "challenges": challenges, "pattern_noticed": pattern_noticed,
            "insight": insight, "tomorrow_change": tomorrow_change,
            "service": {"served": served_today, "how": served_how, "felt": felt_like},
            "hard_thing": hard_thing_done, "accountability": accountability,
            "breakthrough": {"is_breakthrough": is_breakthrough, "description": breakthrough_description},
            "tomorrow_seed": {"intention": tomorrow_intention, "word": tomorrow_word},
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }

        refl_path = self.root / "reflections" / f"reflection_{date_str}.json"
        refl_path.write_text(json.dumps(reflection, indent=2), encoding="utf-8")

        self._log_service(served_today, served_how, felt_like)
        if hard_thing_done:
            self._log_hard_thing(hard_thing_done)
        if accountability:
            self._log_accountability(accountability)
        self._log_kaizen(tomorrow_change, pattern_noticed, insight)

        if is_breakthrough and breakthrough_description:
            self.log_milestone("BREAKTHROUGH", breakthrough_description[:80],
                               breakthrough_description, "general", felt_like)

        # Generate morning synthesis
        try:
            from groq_router import GroqRouter
            synthesis = GroqRouter().route("reasoning",
                f"You are Friday. Generate 80-word morning synthesis from last night.\n"
                f"Pattern: {pattern_noticed}\nInsight: {insight}\n"
                f"Tomorrow: {tomorrow_change}\nIntention: {tomorrow_intention or 'not set'}\n"
                f"Start with 'Last night you noticed...' End with today's first move. TTS-ready.",
                max_tokens=200, temperature=0.3)
        except Exception:
            synthesis = f"Last night you noticed: {pattern_noticed}. Today: {tomorrow_change}."

        EPOSEventBus().publish("lifeos.reflection.complete",
            {"date": date_str, "energy_end": energy_end, "breakthrough": is_breakthrough},
            "lifeos_sovereignty")

        record_decision(decision_type="lifeos.nightly_reflection",
            description=f"Reflection: {date_str} energy {energy_end}/10",
            agent_id="lifeos_sovereignty", outcome="complete",
            context={"date": date_str, "breakthrough": is_breakthrough})

        return {"morning_synthesis": synthesis,
                "system_updates": {"calendar": tomorrow_change,
                                   "milestone": breakthrough_description if is_breakthrough else None},
                "reflection_saved": str(refl_path)}

    # ── MILESTONES ────────────────────────────────────────

    def log_milestone(self, milestone_type: str, title: str, description: str,
                      domain: str, emotion: str = "present",
                      what_enabled: str = None) -> dict:
        milestone = {
            "milestone_id": f"MS-{uuid.uuid4().hex[:8]}", "type": milestone_type,
            "date": datetime.now().strftime("%Y-%m-%d"), "title": title,
            "description": description, "domain": domain, "emotion_at_time": emotion,
            "what_made_it_possible": what_enabled,
            "day_number": self._journey_day(),
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.root / "growth_timeline.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(milestone) + "\n")
        EPOSEventBus().publish("growth.milestone.logged", milestone, "lifeos_sovereignty")
        return milestone

    def _journey_day(self) -> int:
        path = self.root / "growth_timeline.jsonl"
        if not path.exists():
            return 1
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            return 1
        try:
            first = json.loads(lines[0])
            start = datetime.strptime(first["date"], "%Y-%m-%d")
            return (datetime.now() - start).days + 1
        except Exception:
            return len(lines) + 1

    # ── RELATIONSHIPS ─────────────────────────────────────

    def add_relationship(self, name: str, tier: int, rel_type: str,
                          context: str = None, love_lang: str = None) -> dict:
        record = {
            "person_id": f"REL-{name.lower().replace(' ','-')}", "name": name,
            "tier": tier, "relationship_type": rel_type,
            "last_touchpoint": None,
            "next_gesture_due": (datetime.now() + timedelta(
                days={1: 7, 2: 14, 3: 30, 4: 60}.get(tier, 30))).strftime("%Y-%m-%d"),
            "context_notes": context or "", "love_language": love_lang or "unknown",
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.root / "relationship_os.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def get_relationship_gesture_due(self) -> dict:
        path = self.root / "relationship_os.jsonl"
        if not path.exists() or path.stat().st_size == 0:
            return {}
        today = datetime.now().strftime("%Y-%m-%d")
        due = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                if r.get("next_gesture_due", "9999") <= today:
                    due.append(r)
            except Exception:
                pass
        if not due:
            return {}
        due.sort(key=lambda x: x.get("tier", 4))
        top = due[0]
        return {"name": top["name"], "tier": top["tier"],
                "suggestion": f"{top['name']} is due for a touch. A quick message takes 30 seconds."}

    # ── PM SURFACE ────────────────────────────────────────

    def get_pm_surface(self) -> dict:
        from lifeos_kernel import LifeOSKernel
        kernel = LifeOSKernel()
        pm_path = self.root / f"pm_{datetime.now().strftime('%Y%m%d')}.json"
        today_pm = {}
        if pm_path.exists():
            try:
                today_pm = json.loads(pm_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        goals = kernel.get_active_goals()
        energy = kernel.get_energy_trend(days=7)
        streak = self._hard_things_streak()
        signals_path = Path(__file__).parent / "context_vault" / "steward_signals" / "queue.jsonl"
        pending = 0
        if signals_path.exists():
            for line in signals_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        if json.loads(line).get("status") == "pending":
                            pending += 1
                    except Exception:
                        pass
        return {"date": datetime.now().strftime("%A, %B %d"),
                "energy": today_pm.get("energy", 0),
                "intention": today_pm.get("intention", "Not set"),
                "serve_today": today_pm.get("serve_today", ""),
                "priorities": today_pm.get("priorities", ""),
                "relationship_gesture": today_pm.get("relationship_gesture", {}),
                "active_goals": len(goals), "energy_trend": energy.get("trend", "steady"),
                "hard_things_streak": streak, "steward_signals_pending": pending}

    # ── WEEKLY REVIEW ─────────────────────────────────────

    def generate_weekly_review(self) -> str:
        reflections = self._week_reflections()
        hard = self._week_hard_things()
        service = self._week_service()
        day = self._journey_day()
        try:
            from groq_router import GroqRouter
            insights = json.dumps([r.get("insight", "") for r in reflections[-7:]])[:600]
            return GroqRouter().route("reasoning",
                f"Friday weekly review. Reflections: {len(reflections)}. "
                f"Hard things: {len(hard)}. Service: {len(service)}. Journey day: {day}.\n"
                f"Insights: {insights}\n"
                f"Write 200-word review. TTS-ready. End with journey day count.",
                max_tokens=350, temperature=0.4)
        except Exception:
            return f"Week: {len(reflections)} reflections, {len(hard)} hard things. Day {day}."

    # ── PRIVATE HELPERS ───────────────────────────────────

    def _log_service(self, served, how, felt):
        with open(self.root / "service_ledger.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": datetime.now().strftime("%Y-%m-%d"),
                                "served": served, "how": how, "felt": felt}) + "\n")

    def _log_hard_thing(self, desc):
        with open(self.root / "hard_things.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": datetime.now().strftime("%Y-%m-%d"),
                                "description": desc,
                                "streak": self._hard_things_streak() + 1}) + "\n")

    def _log_accountability(self, text):
        with open(self.root / "accountability_mirror.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": datetime.now().strftime("%Y-%m-%d"),
                                "reflection": text}) + "\n")

    def _log_kaizen(self, doing, noticing, insight):
        with open(self.root / "kaizen_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": datetime.now().strftime("%Y-%m-%d"),
                                "doing": doing, "noticing": noticing, "insight": insight}) + "\n")

    def _hard_things_streak(self) -> int:
        path = self.root / "hard_things.jsonl"
        if not path.exists() or path.stat().st_size == 0:
            return 0
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        if not entries:
            return 0
        today = datetime.now().date()
        streak = 0
        for i in range(len(entries) - 1, -1, -1):
            try:
                d = datetime.strptime(entries[i]["date"], "%Y-%m-%d").date()
                if d == today - timedelta(days=streak):
                    streak += 1
                else:
                    break
            except Exception:
                break
        return streak

    def _week_reflections(self):
        path = self.root / "reflections"
        cutoff = datetime.now() - timedelta(days=7)
        result = []
        for f in path.glob("reflection_*.json"):
            try:
                r = json.loads(f.read_text(encoding="utf-8"))
                if datetime.strptime(r["date"], "%Y-%m-%d") >= cutoff:
                    result.append(r)
            except Exception:
                pass
        return sorted(result, key=lambda x: x["date"])

    def _week_hard_things(self):
        return self._read_recent("hard_things.jsonl", 7)

    def _week_service(self):
        return self._read_recent("service_ledger.jsonl", 7)

    def _read_recent(self, filename, days):
        path = self.root / filename
        if not path.exists():
            return []
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                if e.get("date", "") >= cutoff:
                    result.append(e)
            except Exception:
                pass
        return result


if __name__ == "__main__":
    import py_compile
    py_compile.compile("lifeos_sovereignty.py", doraise=True)
    print("PASS: lifeos_sovereignty.py compiles clean")

    s = LifeOSSovereignty()

    # Test 1: Morning check-in
    pm = s.run_morning_check_in(8, "Build with clarity and serve with intention", "Future Jamie")
    assert pm["energy"] == 8
    print(f"  Morning check-in: energy {pm['energy']}/10")

    # Test 2: Log Journey Start milestone
    ms = s.log_milestone("JOURNEY_START", "Day 1 - LifeOS sovereignty online",
                          "The system that holds structure while the internal work happens.",
                          "business", "determined")
    assert ms["milestone_id"].startswith("MS-")
    print(f"  Milestone: {ms['milestone_id']} day {ms['day_number']}")

    # Test 3: Add relationship
    s.add_relationship("Stacey", 1, "collaborator", "Reviews documents with Jamie")
    gesture = s.get_relationship_gesture_due()
    print(f"  Gesture: {gesture.get('suggestion', 'none')[:60]}")

    # Test 4: Nightly reflection
    result = s.run_nightly_reflection(
        day_summary="Built the sovereignty framework.",
        energy_end=7, wins=["lifeos online"], challenges=["scope expansion"],
        pattern_noticed="I build well when intention is clear",
        insight="The system holds what I cannot hold alone.",
        tomorrow_change="Morning check-in before opening laptop",
        served_today="Future Jamie", served_how="Built the holding system",
        felt_like="meaningful", hard_thing_done="Committed to nightly reflection",
        tomorrow_intention="Live one full day inside the system", tomorrow_word="begin")
    assert len(result["morning_synthesis"]) > 30
    print(f"  Synthesis: {result['morning_synthesis'][:80]}...")

    # Test 5: PM surface
    surface = s.get_pm_surface()
    print(f"  PM: energy {surface['energy']}, signals {surface['steward_signals_pending']}")

    print(f"\nPASS: LifeOSSovereignty operational. Day {s._journey_day()}.")
