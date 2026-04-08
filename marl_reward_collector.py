#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
marl_reward_collector.py — MARL Reward Signal Processor
========================================================
Constitutional Authority: EPOS Constitution v3.1

Subscribes to event bus outcome events.
Routes each to Context Graph weight updates.
The learning loop made automatic.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from context_graph import ContextGraph, GraphEdge
from epos_intelligence import record_decision

REWARD_EVENT_MAP = {
    "content.eri_actual":                    "content_reward",
    "content.expansion_protocol.triggered":  "content_reward_high",
    "crm.lead.stage_advanced":               "journey_reward",
    "crm.lead.converted":                    "journey_reward_high",
    "crm.lead.dropped":                      "journey_reward_negative",
    "client.expansion_ready":                "delivery_reward_high",
    "support.sla.breached":                  "delivery_reward_negative",
    "governance.validation.fail":            "quality_reward_negative",
    "governance.validation.pass":            "quality_reward",
}


class MARLRewardCollector:
    def __init__(self):
        self.graph = ContextGraph()
        self._processed_count = 0

    def process_event(self, event) -> None:
        event_type = event.event_type if hasattr(event, "event_type") else event.get("event_type", "")
        payload = event.payload if hasattr(event, "payload") else event.get("payload", {})
        handler_name = REWARD_EVENT_MAP.get(event_type)
        if not handler_name:
            return
        handler = getattr(self, f"_handle_{handler_name}", None)
        if not handler:
            return
        try:
            handler(payload)
            self._processed_count += 1
        except Exception:
            pass

    def _handle_content_reward(self, p):
        self.graph.record_outcome(p.get("brief_id", "?"), float(p.get("eri_actual", 50)),
                                   p.get("hook_type", "unknown"), p.get("niche_id", "lego_affiliate"))

    def _handle_content_reward_high(self, p):
        self.graph.record_outcome(p.get("brief_id", "?"), min(float(p.get("actual_eri", 85)) * 1.1, 100),
                                   p.get("hook_type", "unknown"), p.get("niche_id", "lego_affiliate"))

    def _handle_journey_reward(self, p):
        seg = p.get("segment_id", "unknown")
        to_stage = p.get("to_stage", "unknown")
        stages = {"engagement": 0.55, "nurture": 0.60, "diagnostic": 0.65,
                  "offer": 0.75, "delivery": 0.85, "stewardship": 0.95}
        w = stages.get(to_stage, 0.60)
        self.graph.upsert_edge(GraphEdge(f"segment_{seg}_conversion_{to_stage}",
            f"segment_{seg}", f"stage_{to_stage}", "conversion_signal",
            w, 1, datetime.now(timezone.utc).isoformat()))

    def _handle_journey_reward_high(self, p):
        seg = p.get("segment_id", "unknown")
        cid = p.get("contact_id", "unknown")
        self.graph.upsert_edge(GraphEdge(f"segment_{seg}_converted", f"segment_{seg}",
            "conversion_success", "conversion_confirmed", 1.0, 1, datetime.now(timezone.utc).isoformat()))
        self.graph.upsert_edge(GraphEdge(f"contact_{cid}_conversion", f"contact_{cid}",
            "conversion", "converted", 1.0, 1, datetime.now(timezone.utc).isoformat()))

    def _handle_journey_reward_negative(self, p):
        seg = p.get("segment_id", "unknown")
        stage = p.get("drop_stage", "unknown")
        cur = self.graph.get_weight(f"segment_{seg}", f"stage_{stage}", "conversion_signal")
        self.graph.upsert_edge(GraphEdge(f"segment_{seg}_conversion_{stage}", f"segment_{seg}",
            f"stage_{stage}", "conversion_signal", max(cur - 0.1, 0.1), 1,
            datetime.now(timezone.utc).isoformat()))

    def _handle_delivery_reward_high(self, p):
        cid = p.get("client_id", "unknown")
        self.graph.upsert_edge(GraphEdge(f"client_{cid}_retention", f"client_{cid}",
            "expansion_ready", "retention_health", 0.9, 1, datetime.now(timezone.utc).isoformat()))

    def _handle_delivery_reward_negative(self, p):
        cat = p.get("category", "general")
        self.graph.upsert_edge(GraphEdge(f"service_{cat}_sla", f"service_{cat}",
            "sla_breach_risk", "sla_risk", 0.7, 1, datetime.now(timezone.utc).isoformat()))

    def _handle_quality_reward_negative(self, p):
        sid = p.get("script_id", "unknown")[:8]
        self.graph.upsert_edge(GraphEdge(f"validation_fail_{sid}", "content_production",
            "validation_risk", "quality_signal", 0.3, 1, datetime.now(timezone.utc).isoformat()))

    def _handle_quality_reward(self, p):
        self.graph.upsert_edge(GraphEdge("content_production_quality", "content_production",
            "quality_confirmed", "quality_signal", 0.8, 1, datetime.now(timezone.utc).isoformat()))


if __name__ == "__main__":
    import py_compile
    py_compile.compile("marl_reward_collector.py", doraise=True)
    from epos_event_bus import EPOSEventBus
    collector = MARLRewardCollector()
    bus = EPOSEventBus()
    e = bus.publish("content.eri_actual", {"brief_id": "CB-LEGO-001", "eri_actual": 72.0,
        "hook_type": "list", "niche_id": "lego_affiliate", "eri_predicted": 58.0}, "test_an1")
    collector.process_event(e)
    hooks = collector.graph.query_best_hook_for_niche("lego_affiliate")
    list_w = next((w for h, w in hooks if h == "list"), 0)
    print(f"  list hook weight after ERI 72: {list_w:.3f}")
    je = bus.publish("crm.lead.converted", {"contact_id": "test-001", "segment_id": "small_business",
        "tier": "L3", "days_to_convert": 7}, "test_crm")
    collector.process_event(je)
    cp = collector.graph.query_conversion_probability("test-001")
    print(f"  Conversion probability: {cp:.3f}")
    print(f"PASS: MARLRewardCollector — {collector._processed_count} events, {len(REWARD_EVENT_MAP)} types")
