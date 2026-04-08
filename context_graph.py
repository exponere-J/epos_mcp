#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
context_graph.py — EPOS Weighted Knowledge Graph
==================================================
Constitutional Authority: EPOS Constitution v3.1

Maps relationships between every entity EPOS knows about.
Edge weights update from real outcomes via exponential moving average.
Agents query at reasoning time for calibrated decisions.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault


@dataclass
class GraphNode:
    node_id: str
    node_type: str
    attributes: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    relationship: str
    weight: float
    evidence_count: int
    last_updated: str


class ContextGraph:
    """Weighted knowledge graph. Learning from every outcome."""

    def __init__(self):
        vault = get_context_vault()
        graph_dir = vault / "graph"
        graph_dir.mkdir(parents=True, exist_ok=True)
        self.GRAPH_PATH = graph_dir / "context_graph.json"
        self.EVENTS_PATH = graph_dir / "graph_events.jsonl"
        if not self.GRAPH_PATH.exists():
            self.GRAPH_PATH.write_text(
                json.dumps({"nodes": {}, "edges": {}}, indent=2),
                encoding="utf-8",
            )

    def _load(self) -> dict:
        return json.loads(self.GRAPH_PATH.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self.GRAPH_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def upsert_node(self, node: GraphNode) -> None:
        data = self._load()
        data["nodes"][node.node_id] = asdict(node)
        self._save(data)

    def upsert_edge(self, edge: GraphEdge) -> None:
        """Update edge weight using exponential moving average."""
        data = self._load()
        existing = data["edges"].get(edge.edge_id)
        if existing:
            old_weight = existing.get("weight", 0.5)
            edge.weight = round(0.7 * old_weight + 0.3 * edge.weight, 4)
            edge.evidence_count = existing.get("evidence_count", 0) + 1
        data["edges"][edge.edge_id] = asdict(edge)
        self._save(data)
        with open(self.EVENTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event_type": "edge_updated", "edge_id": edge.edge_id,
                                "new_weight": edge.weight,
                                "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n")

    def get_weight(self, source_id: str, target_id: str, relationship: str) -> float:
        data = self._load()
        edge_id = f"{source_id}_{target_id}_{relationship}"
        edge = data["edges"].get(edge_id)
        return edge["weight"] if edge else 0.5

    def query_best_hook_for_niche(self, niche_id: str) -> List[Tuple[str, float]]:
        data = self._load()
        prefix = f"niche_{niche_id}_hook_"
        results = [(eid.replace(prefix, ""), e["weight"])
                    for eid, e in data["edges"].items() if eid.startswith(prefix)]
        results.sort(key=lambda x: x[1], reverse=True)
        return results if results else [("list", 0.5), ("question", 0.45)]

    def query_best_segment_for_content(self, content_type: str, platform: str) -> list:
        data = self._load()
        prefix = f"segment_content_{content_type}_{platform}_"
        results = [(eid.replace(prefix, ""), e["weight"])
                    for eid, e in data["edges"].items() if eid.startswith(prefix)]
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def query_conversion_probability(self, contact_id: str) -> float:
        data = self._load()
        edge = data["edges"].get(f"contact_{contact_id}_conversion")
        return edge["weight"] if edge else 0.5

    def record_outcome(self, brief_id: str, eri_actual: float,
                       hook_type: str, niche_id: str, **kwargs) -> None:
        from epos_intelligence import record_decision
        from epos_event_bus import EPOSEventBus
        weight = min(eri_actual / 100.0, 1.0)
        edge_id = f"niche_{niche_id}_hook_{hook_type}"
        self.upsert_edge(GraphEdge(
            edge_id=edge_id, source_id=f"niche_{niche_id}",
            target_id=f"hook_{hook_type}", relationship="eri_resonance",
            weight=weight, evidence_count=1,
            last_updated=datetime.now(timezone.utc).isoformat(),
        ))
        self.upsert_node(GraphNode(
            node_id=f"niche_{niche_id}", node_type="niche",
            attributes={"niche_id": niche_id},
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        ))
        record_decision(
            decision_type="graph.outcome_recorded",
            description=f"Context graph: {niche_id}/{hook_type} ERI {eri_actual:.1f}",
            agent_id="context_graph", outcome="updated",
            context={"brief_id": brief_id, "hook_type": hook_type,
                     "niche_id": niche_id, "eri_actual": eri_actual, "weight": weight},
        )
        EPOSEventBus().publish("graph.edge.updated",
            {"niche": niche_id, "hook_type": hook_type,
             "eri_actual": eri_actual, "new_weight": weight}, "context_graph")


if __name__ == "__main__":
    import py_compile
    py_compile.compile("context_graph.py", doraise=True)
    graph = ContextGraph()
    graph.upsert_node(GraphNode("niche_lego_affiliate", "niche",
        {"name": "LEGO Affiliate"}, datetime.now(timezone.utc).isoformat(),
        datetime.now(timezone.utc).isoformat()))
    print("  Node upserted: niche_lego_affiliate")
    graph.record_outcome("CB-LEGO-001", 72.0, "list", "lego_affiliate")
    graph.record_outcome("CB-LEGO-004", 45.0, "question", "lego_affiliate")
    print("  Outcomes recorded: list=72, question=45")
    hooks = graph.query_best_hook_for_niche("lego_affiliate")
    assert len(hooks) >= 2
    assert hooks[0][0] == "list"
    assert hooks[0][1] > hooks[1][1]
    print(f"  Best hook: {hooks[0][0]} ({hooks[0][1]:.3f})")
    w = graph.get_weight("unknown_a", "unknown_b", "test")
    assert w == 0.5
    print(f"  Neutral default: {w}")
    print("PASS: ContextGraph — learning from outcomes")
