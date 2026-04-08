#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
dashboard_engine.py — EPOS Dashboard Aggregation Engine
=========================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Unified Ecosystem Visibility

Aggregates health, revenue, content, and intelligence data from all
EPOS nodes into a single dashboard surface. Powers CLI, Command Center
web UI, and reporting endpoints.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
except ImportError:
    EPOSEventBus = None

from path_utils import get_context_vault


DASHBOARD_VAULT = get_context_vault() / "dashboard"


class DashboardEngine:
    """Unified ecosystem dashboard aggregator."""

    def __init__(self):
        self.vault = get_context_vault()
        DASHBOARD_VAULT.mkdir(parents=True, exist_ok=True)
        self._journal_path = DASHBOARD_VAULT / "dashboard_journal.jsonl"
        self._bus = None
        if EPOSEventBus:
            try:
                self._bus = EPOSEventBus()
            except Exception:
                pass

    def get_full_dashboard(self) -> dict:
        dashboard = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_health": self._node_health(),
            "revenue": self._revenue(),
            "content": self._content(),
            "intelligence": self._intelligence(),
            "journey": self._journey(),
        }
        # Publish dashboard refresh event
        if self._bus:
            try:
                self._bus.publish("dashboard.refreshed", {
                    "nodes": dashboard["node_health"].get("total_nodes", 0),
                    "revenue": dashboard["revenue"].get("total", 0),
                    "events": dashboard["intelligence"].get("events", 0),
                }, source_module="dashboard_engine")
            except Exception:
                pass
        # Journal
        entry = {"timestamp": dashboard["timestamp"], "event_type": "dashboard.refreshed",
                 "summary": {"nodes": dashboard["node_health"].get("total_nodes", 0),
                             "revenue": dashboard["revenue"].get("total", 0)}}
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return dashboard

    def _node_health(self) -> dict:
        catalog_path = self.vault / "marketplace" / "certifications" / "marketplace_catalog.json"
        if not catalog_path.exists():
            return {"total_nodes": 0, "by_readiness": {}, "nodes": []}
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        nodes = []
        for nid, data in catalog.get("nodes", {}).items():
            nodes.append({"id": nid, "name": data.get("name", nid),
                          "score": data.get("total_score", 0),
                          "readiness": data.get("readiness", "unknown")})
        nodes.sort(key=lambda n: n["score"], reverse=True)
        by_r = {}
        for n in nodes:
            by_r[n["readiness"]] = by_r.get(n["readiness"], 0) + 1
        return {"total_nodes": len(nodes), "by_readiness": by_r, "nodes": nodes}

    def _revenue(self) -> dict:
        journal = self.vault / "financial" / "payments" / "transactions.jsonl"
        if not journal.exists():
            return {"total": 0, "count": 0}
        total, count = 0, 0
        for line in journal.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            try:
                e = json.loads(line)
                if e.get("event_type") in ("payment.received", "payment.succeeded"):
                    total += e.get("payload", {}).get("amount", 0)
                    count += 1
            except Exception: pass
        return {"total": total, "count": count}

    def _content(self) -> dict:
        sparks = len(list((self.vault / "sparks").glob("SPARK-*.json"))) if (self.vault / "sparks").exists() else 0
        briefs = sum(1 for _ in self.vault.glob("missions/*/CB-*.json"))
        scripts_dir = Path(__file__).parent / "content" / "lab" / "production"
        scripts = len(list(scripts_dir.rglob("*_script.md"))) if scripts_dir.exists() else 0
        return {"sparks": sparks, "briefs": briefs, "scripts": scripts}

    def _intelligence(self) -> dict:
        events = 0
        ep = self.vault / "events" / "system" / "events.jsonl"
        if ep.exists():
            events = sum(1 for l in ep.read_text(encoding="utf-8").splitlines() if l.strip())
        fotw = len(list((self.vault / "fotw" / "expressions").glob("EXPR-*.json"))) if (self.vault / "fotw" / "expressions").exists() else 0
        return {"events": events, "fotw_expressions": fotw}

    def _journey(self) -> dict:
        jp = self.vault / "crm" / "journey" / "journeys.jsonl"
        if not jp.exists():
            return {"total": 0, "stages": {}}
        stages, total = {}, 0
        for line in jp.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            try:
                e = json.loads(line)
                s = e.get("stage", "unknown")
                stages[s] = stages.get(s, 0) + 1
                total += 1
            except Exception: pass
        return {"total": total, "stages": stages}

    def print_dashboard(self):
        d = self.get_full_dashboard()
        nh = d["node_health"]
        rev = d["revenue"]
        cp = d["content"]
        intel = d["intelligence"]
        j = d["journey"]

        print("=" * 60)
        print("  EPOS COMMAND CENTER")
        print("=" * 60)
        print(f"\n  NODES: {nh['total_nodes']} certified")
        for r, c in nh.get("by_readiness", {}).items():
            print(f"    {r}: {c}")
        print(f"\n  REVENUE: ${rev['total']:.2f} ({rev['count']} transactions)")
        print(f"\n  CONTENT: {cp['sparks']} sparks | {cp['briefs']} briefs | {cp['scripts']} scripts")
        print(f"\n  INTELLIGENCE: {intel['events']} events | {intel['fotw_expressions']} expressions")
        print(f"\n  JOURNEY: {j['total']} tracked")
        for s, c in j.get("stages", {}).items():
            print(f"    {s}: {c}")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    passed = 0
    engine = DashboardEngine()
    d = engine.get_full_dashboard()
    assert "node_health" in d and "revenue" in d and "content" in d
    passed += 1
    assert d["node_health"]["total_nodes"] > 0
    passed += 1
    engine.print_dashboard()
    print(f"\nPASS: dashboard_engine ({passed} assertions)")
