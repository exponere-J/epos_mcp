import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class Route:
    id: str
    label: str
    match_any: List[str]
    pipeline: str
    priority: int

class DecisionRouter:
    def __init__(self, graph_path: str = "kernel/config/decision_graph.json"):
        self.graph_path = Path(graph_path)
        self.graph = self._load_graph()
        self.routes = self._parse_routes(self.graph)

    def _load_graph(self) -> Dict[str, Any]:
        if not self.graph_path.exists():
            raise FileNotFoundError(f"Decision graph not found: {self.graph_path}")
        return json.loads(self.graph_path.read_text(encoding="utf-8"))

    def _parse_routes(self, graph: Dict[str, Any]) -> List[Route]:
        routes = []
        for r in graph.get("routes", []):
            routes.append(Route(
                id=r["id"],
                label=r.get("label", r["id"]),
                match_any=r.get("match_any", []),
                pipeline=r["pipeline"],
                priority=int(r.get("priority", 0))
            ))
        # highest priority first
        routes.sort(key=lambda x: x.priority, reverse=True)
        return routes

    def route(self, tags: List[str]) -> Tuple[str, Optional[Route]]:
        """
        tags are normalized strings like:
        - 'intent:code'
        - 'intent:marketing'
        - 'intent:personal'
        """
        tag_set = set(t.strip().lower() for t in tags if t)

        for r in self.routes:
            for m in r.match_any:
                if m.strip().lower() in tag_set:
                    return r.pipeline, r
        return "fallback.llm_classify", None
