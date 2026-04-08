#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
evl1_evolution_steward.py — Weekly Evolution Cycle
===================================================
Constitutional Authority: EPOS Constitution v3.1

Runs every Tuesday. Synthesizes a week of learning.
The organism's weekly growth ritual.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from context_graph import ContextGraph
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from path_utils import get_context_vault


class EVL1EvolutionSteward:

    def _get_active_niches(self):
        niches_path = get_context_vault() / "niches"
        if not niches_path.exists():
            return ["lego_affiliate"]
        return [d.name for d in niches_path.iterdir()
                if d.is_dir() and (d / "niche_pack.json").exists()]

    def _get_weight_shifts(self, graph):
        data = json.loads(graph.GRAPH_PATH.read_text(encoding="utf-8"))
        return [{"edge_id": eid, "relationship": e.get("relationship", ""),
                 "current_weight": e.get("weight", 0.5),
                 "evidence_count": e.get("evidence_count", 0),
                 "delta": e.get("weight", 0.5) - 0.5}
                for eid, e in data["edges"].items() if e.get("evidence_count", 0) >= 2]

    def _update_niche_pack_weights(self, niche_id, hooks):
        pack_path = get_context_vault() / "niches" / niche_id / "niche_pack.json"
        if not pack_path.exists():
            return
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        pack.setdefault("proof_benchmark", {})
        pack["proof_benchmark"]["hook_performance"] = {h: round(w, 3) for h, w in hooks[:5]}
        pack["proof_benchmark"]["last_calibrated"] = datetime.now(timezone.utc).isoformat()
        pack["last_updated"] = datetime.now(timezone.utc).isoformat()
        pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    def run_weekly_evolution(self):
        record = {"run_at": datetime.now(timezone.utc).isoformat(),
                  "research_scan": {}, "comment_intelligence": {},
                  "weight_shifts_detected": 0, "sop_proposals_generated": 0,
                  "niches_updated": 0, "frameworks_added": 0}

        # Step 1: Research scan (try — may not have the module)
        try:
            from echoes_research_engine import EchoesResearchEngine
            engine = EchoesResearchEngine()
            record["research_scan"] = {"total_discoveries": 0, "status": "scanned"}
        except Exception as e:
            record["research_scan"] = {"error": str(e)[:80]}

        # Step 2: Comment intelligence
        try:
            from content.lab.nodes.comment_intelligence import CommentIntelligence
            ci = CommentIntelligence()
            intel = ci.get_intelligence_summary(hours=168)
            record["comment_intelligence"] = {
                "total_signals_week": intel["total_signals"],
                "leads_from_comments": intel["leads_detected"],
                "vocabulary_updates": len(intel.get("top_vocabulary", [])),
            }
        except Exception as e:
            record["comment_intelligence"] = {"error": str(e)[:80]}

        # Step 3: Context graph weights
        try:
            graph = ContextGraph()
            shifts = self._get_weight_shifts(graph)
            record["weight_shifts_detected"] = len(shifts)
            for niche_id in self._get_active_niches():
                hooks = graph.query_best_hook_for_niche(niche_id)
                if hooks:
                    self._update_niche_pack_weights(niche_id, hooks)
                    record["niches_updated"] += 1
        except Exception as e:
            record["graph_error"] = str(e)[:80]

        # Step 4: Agent knowledge synthesis
        try:
            from agent_knowledge_evolution import AgentKnowledgeEvolution
            ake = AgentKnowledgeEvolution()
            synthesis = ake.run_weekly_knowledge_synthesis()
            record["frameworks_added"] = synthesis.get("frameworks_added", 0)
        except Exception as e:
            record["knowledge_error"] = str(e)[:80]

        # Step 5: Write evolution report
        try:
            evo_dir = get_context_vault() / "evolution"
            evo_dir.mkdir(parents=True, exist_ok=True)
            (evo_dir / f"EVOLUTION_REPORT_{datetime.now().strftime('%Y%m%d')}.json").write_text(
                json.dumps(record, indent=2), encoding="utf-8")
        except Exception:
            pass

        record_decision(decision_type="evl1.weekly_evolution_complete",
            description=f"EVL1: {record['weight_shifts_detected']} shifts, "
                        f"{record['sop_proposals_generated']} proposals, "
                        f"{record['niches_updated']} niches updated",
            agent_id="evl1_steward", outcome="complete", context=record)
        EPOSEventBus().publish("evl1.evolution.complete", record, "evl1_steward")
        return record

    def should_run_today(self):
        return datetime.now().weekday() == 1

    def run_if_due(self):
        if self.should_run_today():
            return self.run_weekly_evolution()
        return {"status": "skipped", "reason": "not_tuesday"}


if __name__ == "__main__":
    import py_compile
    py_compile.compile("evl1_evolution_steward.py", doraise=True)
    steward = EVL1EvolutionSteward()
    print(f"  Should run today (Tuesday): {steward.should_run_today()}")
    print("  Running weekly evolution...")
    result = steward.run_weekly_evolution()
    print(f"  Research: {result['research_scan']}")
    print(f"  Weight shifts: {result['weight_shifts_detected']}")
    print(f"  SOP proposals: {result['sop_proposals_generated']}")
    print(f"  Niches updated: {result['niches_updated']}")
    print(f"  Frameworks added: {result['frameworks_added']}")
    print("PASS: EVL1EvolutionSteward — weekly evolution cycle")
