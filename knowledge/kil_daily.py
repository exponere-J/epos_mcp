#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
kil_daily.py — Knowledge Ingestion Layer Daily Trigger
========================================================
Constitutional Authority: EPOS Constitution v3.1

Scans baseline registry for stale entries, generates research questions,
tracks 30-day cycles, and manages improvement candidates.
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
BASELINES_DIR = VAULT / "knowledge" / "baselines"
IMPROVEMENTS_DIR = VAULT / "knowledge" / "improvements"
CYCLES_DIR = VAULT / "knowledge" / "cycles"
KIL_LOG = VAULT / "knowledge" / "kil_log.jsonl"

STALE_THRESHOLD_DAYS = 30


class KILDaily:
    """Knowledge Ingestion Layer — daily scan and research question generation."""

    def __init__(self):
        for d in (BASELINES_DIR, IMPROVEMENTS_DIR, CYCLES_DIR):
            d.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        """Execute daily KIL scan."""
        baselines = self._scan_baselines()
        stale = [b for b in baselines if b["stale"]]
        questions = self._generate_questions(stale)
        cycle = self._check_cycle()

        result = {
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "total_baselines": len(baselines),
            "stale_baselines": len(stale),
            "research_questions": len(questions),
            "current_cycle": cycle.get("cycle_id", "none"),
            "cycle_phase": cycle.get("phase", "none"),
        }

        self._log(result)

        if stale and _BUS:
            for s in stale:
                try:
                    _BUS.publish("knowledge.baseline.stale", {
                        "role": s["role"], "last_updated": s["last_updated"],
                        "days_stale": s["days_stale"],
                    }, source_module="kil_daily")
                except Exception:
                    pass

        return result

    def _scan_baselines(self) -> list:
        """Scan all baselines and check freshness."""
        baselines = []
        now = datetime.now(timezone.utc)
        for f in sorted(BASELINES_DIR.glob("*_baseline.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            last = datetime.strptime(data.get("last_updated", "2020-01-01"), "%Y-%m-%d")
            last = last.replace(tzinfo=timezone.utc)
            days = (now - last).days
            baselines.append({
                "role": data.get("role", f.stem),
                "name": data.get("name", data.get("role", "")),
                "version": data.get("baseline_version", "0.0.0"),
                "last_updated": data.get("last_updated", "unknown"),
                "days_stale": days,
                "stale": days > STALE_THRESHOLD_DAYS,
                "validation": data.get("operational_validation", "unknown"),
            })
        return baselines

    def _generate_questions(self, stale_baselines: list) -> list:
        """Generate research questions for stale baselines."""
        questions = []
        for b in stale_baselines:
            q = {
                "role": b["role"],
                "question": f"What is the current best practice for {b['name']} as of {datetime.now(timezone.utc).strftime('%Y-%m')}?",
                "context": f"Baseline version {b['version']} last updated {b['last_updated']} ({b['days_stale']} days ago)",
                "priority": "high" if b["days_stale"] > 60 else "medium",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            questions.append(q)
            # Save to research queue
            queue_path = IMPROVEMENTS_DIR / "research_queue.jsonl"
            with open(queue_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(q) + "\n")
        return questions

    def _check_cycle(self) -> dict:
        """Check current 30-day cycle status."""
        cycle_path = CYCLES_DIR / "current_cycle.json"
        if not cycle_path.exists():
            return {"cycle_id": "none", "phase": "not_initialized"}
        return json.loads(cycle_path.read_text(encoding="utf-8"))

    def initialize_cycle(self, focus: str, hypothesis: str,
                          primary_metric: str, delta_threshold: str = ">20%") -> dict:
        """Initialize a new 30-day research cycle."""
        now = datetime.now(timezone.utc)
        cycle = {
            "cycle_id": f"CYCLE-{now.strftime('%Y%m%d')}",
            "focus": focus,
            "start_date": now.strftime("%Y-%m-%d"),
            "end_date": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
            "phase": "operate_locked",
            "research_council_brief": {
                "focus": focus,
                "hypothesis": hypothesis,
                "primary_metric": primary_metric,
                "delta_threshold": delta_threshold,
            },
            "measurements": [],
            "improvements_generated": [],
            "article_brief": None,
        }
        (CYCLES_DIR / "current_cycle.json").write_text(
            json.dumps(cycle, indent=2), encoding="utf-8")

        if _BUS:
            try:
                _BUS.publish("knowledge.cycle.started", {
                    "cycle_id": cycle["cycle_id"], "focus": focus,
                }, source_module="kil_daily")
            except Exception:
                pass

        return cycle

    def list_baselines(self) -> list:
        return self._scan_baselines()

    def list_improvements(self) -> list:
        queue = IMPROVEMENTS_DIR / "research_queue.jsonl"
        if not queue.exists():
            return []
        items = []
        for line in queue.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
        return items

    def _log(self, result: dict):
        KIL_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(KIL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    kil = KILDaily()

    # Test 1: Scan baselines
    baselines = kil.list_baselines()
    assert len(baselines) >= 10, f"Expected 10+ baselines, got {len(baselines)}"
    passed += 1

    # Test 2: Run KIL
    result = kil.run()
    assert "total_baselines" in result
    print(f"Baselines: {result['total_baselines']} | Stale: {result['stale_baselines']}")
    passed += 1

    # Test 3: Initialize cycle
    cycle = kil.initialize_cycle(
        focus="Content Lab Autonomous Agency Operations",
        hypothesis="Echoes will achieve >100 pieces published with resonance scoring producing capacity-shift decisions by Day 14",
        primary_metric="Content published count + resonance score distribution",
        delta_threshold=">20% variance from benchmarks")
    assert cycle["cycle_id"].startswith("CYCLE-")
    assert cycle["phase"] == "operate_locked"
    passed += 1

    # Test 4: Cycle readable
    current = kil._check_cycle()
    assert current["cycle_id"] == cycle["cycle_id"]
    passed += 1

    print(f"\nPASS: kil_daily ({passed} assertions)")
    print(f"Cycle: {cycle['cycle_id']} | Focus: {cycle['focus'][:50]}")
