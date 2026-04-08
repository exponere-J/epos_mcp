import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
GRAPH_PATH = BASE_DIR / "kernel" / "config" / "decision_graph.json"


@dataclass
class RouteOption:
    id: str
    label: str
    pipeline: str
    conditions: List[str]


@dataclass
class DecisionNode:
    id: str
    description: str
    strategy: str
    archetype_bias: List[str]
    routes: List[RouteOption]


class DecisionGraph:
    def __init__(self, graph_data: Dict[str, Any]):
        self.version: str = graph_data.get("version", "v1")
        self.root_id: str = graph_data.get("root", "root")
        nodes_raw: Dict[str, Any] = graph_data.get("nodes", {})
        self.nodes: Dict[str, DecisionNode] = {}

        for node_id, node in nodes_raw.items():
            routes = [
                RouteOption(
                    id=r["id"],
                    label=r["label"],
                    pipeline=r["pipeline"],
                    conditions=r.get("conditions", []),
                )
                for r in node.get("routes", [])
            ]
            self.nodes[node_id] = DecisionNode(
                id=node["id"],
                description=node.get("description", ""),
                strategy=node.get("strategy", ""),
                archetype_bias=node.get("archetype_bias", []),
                routes=routes,
            )

    def get_node(self, node_id: Optional[str]) -> Optional[DecisionNode]:
        if not node_id:
            node_id = self.root_id
        return self.nodes.get(node_id)

    def choose_route(
        self,
        node_id: str,
        intent: Optional[str] = None,
        risk: Optional[str] = None,
    ) -> Optional[Tuple[RouteOption, DecisionNode]]:
        """
        Very simple rule-first matcher:
        - match intent:foo
        - match risk:bar
        If nothing matches, return the first route (fallback).
        """
        node = self.get_node(node_id)
        if not node or not node.routes:
            return None

        def condition_matches(route: RouteOption) -> bool:
            conds = route.conditions or []
            if intent:
                expected = f"intent:{intent}"
                if expected not in conds:
                    return False
            if risk:
                expected = f"risk:{risk}"
                if expected not in conds and any(c.startswith("risk:") for c in conds):
                    return False
            return True

        # First: exact match
        for r in node.routes:
            if condition_matches(r):
                return r, node

        # Fallback: first route
        return node.routes[0], node


def load_decision_graph(path: Path = GRAPH_PATH) -> DecisionGraph:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return DecisionGraph(data)
