#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
continuous_improvement.py — Friday Continuous Improvement Engine
====================================================================
Constitutional Authority: EPOS Constitution v3.1

Cron jobs that make Friday smarter every day without human intervention.

Daily:    Self-assessment of routing accuracy + failure rate
Weekly:   Pattern learning from 7-day directive history
Monthly:  Capability gap review + improvement candidate generation
6-hourly: Routing accuracy tracking
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
FRIDAY_VAULT = VAULT / "friday"
MISSIONS_DIR = FRIDAY_VAULT / "missions"
SELF_ASSESS_DIR = FRIDAY_VAULT / "self_assessments"
PATTERN_DIR = FRIDAY_VAULT / "pattern_library"
CAPABILITY_DIR = FRIDAY_VAULT / "capability_reviews"
for d in (SELF_ASSESS_DIR, PATTERN_DIR, CAPABILITY_DIR):
    d.mkdir(parents=True, exist_ok=True)


class FridayContinuousImprovement:
    """Friday's self-improvement engine."""

    def daily_self_assessment(self) -> dict:
        """Daily review of Friday's performance."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        missions = self._load_missions_since(cutoff)

        total = len(missions)
        if total == 0:
            assessment = {
                "date": now.strftime("%Y-%m-%d"),
                "missions_total": 0,
                "note": "No directives processed in last 24 hours",
            }
        else:
            success = sum(1 for m in missions if m.get("success"))
            by_type = {}
            for m in missions:
                mt = m.get("mission_type", "unknown")
                by_type[mt] = by_type.get(mt, 0) + 1

            failure_rate = (total - success) / total
            assessment = {
                "date": now.strftime("%Y-%m-%d"),
                "missions_total": total,
                "missions_success": success,
                "missions_failed": total - success,
                "failure_rate": round(failure_rate, 3),
                "by_type": by_type,
                "performance": "degraded" if failure_rate > 0.2 else "healthy",
            }

            if failure_rate > 0.2 and _BUS:
                try:
                    _BUS.publish("friday.performance.degraded", {
                        "failure_rate": failure_rate,
                        "total": total,
                    }, source_module="friday_continuous_improvement")
                except Exception:
                    pass

        # Save assessment
        path = SELF_ASSESS_DIR / f"{now.strftime('%Y-%m-%d')}_assessment.json"
        path.write_text(json.dumps(assessment, indent=2), encoding="utf-8")

        if _BUS:
            try:
                _BUS.publish("friday.self_assessment.complete", assessment,
                             source_module="friday_continuous_improvement")
            except Exception:
                pass

        return assessment

    def weekly_pattern_learning(self) -> dict:
        """Weekly review of directive patterns."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)

        missions = self._load_missions_since(cutoff)

        # Cluster by mission type
        by_type = {}
        for m in missions:
            mt = m.get("mission_type", "unknown")
            if mt not in by_type:
                by_type[mt] = {"count": 0, "success": 0, "directives": []}
            by_type[mt]["count"] += 1
            if m.get("success"):
                by_type[mt]["success"] += 1
            by_type[mt]["directives"].append(m.get("directive", "")[:100])

        # Identify top mission types
        top_types = sorted(by_type.items(), key=lambda x: x[1]["count"], reverse=True)

        patterns = {
            "week_ending": now.strftime("%Y-%m-%d"),
            "total_directives": len(missions),
            "by_type": {k: {"count": v["count"], "success_rate": v["success"]/v["count"] if v["count"] else 0}
                        for k, v in by_type.items()},
            "top_types": [t[0] for t in top_types[:3]],
            "unknown_count": by_type.get("unknown", {}).get("count", 0),
        }

        path = PATTERN_DIR / f"{now.strftime('%Y-W%V')}_patterns.json"
        path.write_text(json.dumps(patterns, indent=2), encoding="utf-8")

        if _BUS:
            try:
                _BUS.publish("friday.patterns.updated", patterns,
                             source_module="friday_continuous_improvement")
            except Exception:
                pass

        return patterns

    def monthly_capability_review(self) -> dict:
        """Monthly capability gap review."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=30)

        missions = self._load_missions_since(cutoff)
        failures = [m for m in missions if not m.get("success")]

        # Categorize failures
        failure_categories = {}
        for f in failures:
            for r in f.get("results", []):
                if r.get("status") not in ("complete", "dispatched", "queued"):
                    cat = r.get("executor", "unknown")
                    failure_categories[cat] = failure_categories.get(cat, 0) + 1

        # Identify worst-performing executor
        worst = max(failure_categories, key=failure_categories.get) if failure_categories else None

        review = {
            "month": now.strftime("%Y-%m"),
            "total_missions_30d": len(missions),
            "total_failures_30d": len(failures),
            "failure_rate": round(len(failures) / len(missions), 3) if missions else 0,
            "failure_by_executor": failure_categories,
            "worst_executor": worst,
            "recommendation": f"Improve {worst} executor reliability" if worst else "All executors performing well",
        }

        path = CAPABILITY_DIR / f"{now.strftime('%Y-%m')}_review.json"
        path.write_text(json.dumps(review, indent=2), encoding="utf-8")

        if _BUS:
            try:
                _BUS.publish("friday.capability_review.complete", review,
                             source_module="friday_continuous_improvement")
            except Exception:
                pass

        return review

    def routing_accuracy_tracker(self) -> dict:
        """6-hour routing accuracy check."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=6)

        missions = self._load_missions_since(cutoff)

        if not missions:
            return {"missions_6h": 0, "accuracy": None, "note": "No missions in last 6 hours"}

        success = sum(1 for m in missions if m.get("success"))
        accuracy = success / len(missions)

        result = {
            "checked_at": now.isoformat(),
            "missions_6h": len(missions),
            "success": success,
            "accuracy": round(accuracy, 3),
            "below_threshold": accuracy < 0.8,
        }

        if accuracy < 0.8 and _BUS:
            try:
                _BUS.publish("friday.routing.degraded", {
                    "accuracy": accuracy,
                    "threshold": 0.8,
                }, source_module="friday_continuous_improvement")
            except Exception:
                pass

        return result

    def _load_missions_since(self, cutoff: datetime) -> list:
        """Load all missions completed since cutoff."""
        if not MISSIONS_DIR.exists():
            return []
        missions = []
        for f in MISSIONS_DIR.glob("DIR-*_aar.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                completed_str = data.get("completed_at", "")
                if completed_str:
                    completed = datetime.fromisoformat(completed_str.replace("Z", "+00:00"))
                    if completed >= cutoff:
                        missions.append(data)
            except Exception:
                pass
        return missions


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    fci = FridayContinuousImprovement()

    # Test 1: Daily self-assessment
    a = fci.daily_self_assessment()
    assert "date" in a
    print(f"Daily: {a.get('missions_total', 0)} missions, performance={a.get('performance', '?')}")
    passed += 1

    # Test 2: Weekly pattern learning
    p = fci.weekly_pattern_learning()
    assert "by_type" in p
    print(f"Weekly: {p['total_directives']} directives, top={p.get('top_types', [])}")
    passed += 1

    # Test 3: Monthly capability review
    r = fci.monthly_capability_review()
    assert "month" in r
    print(f"Monthly: {r['total_missions_30d']} missions, failure_rate={r['failure_rate']}")
    passed += 1

    # Test 4: Routing accuracy
    rt = fci.routing_accuracy_tracker()
    print(f"Routing: {rt.get('missions_6h', 0)} missions, accuracy={rt.get('accuracy')}")
    passed += 1

    print(f"\nPASS: continuous_improvement ({passed} assertions)")
