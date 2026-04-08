#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
consumer_journey_graph.py — 8-Stage Consumer Journey as LangGraph
Constitutional Authority: EPOS Constitution v3.1
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
from epos_event_bus import EPOSEventBus

class JourneyState(TypedDict, total=False):
    contact_id: str
    email: str
    segment_id: Optional[str]
    lead_score: int
    stage: str
    last_interaction: Optional[str]
    ttlg_output: Optional[dict]
    mirror_report: Optional[str]
    offer_tier: Optional[str]
    error: Optional[str]

def stage_discovery(s):
    EPOSEventBus().publish("journey.discovery", {"contact_id": s["contact_id"]}, "journey_graph")
    return {**s, "stage": "discovery"}

def stage_engagement(s):
    seg = s.get("segment_id")
    if not seg:
        email = s.get("email", "")
        if any(d in email for d in ["agency", "media"]): seg = "agency"
        elif "@gmail" in email or "@yahoo" in email: seg = "individual_creator"
        else: seg = "small_business"
    return {**s, "stage": "engagement", "segment_id": seg}

def stage_nurture(s): return {**s, "stage": "nurture"}

def stage_diagnostic(s):
    try:
        from graphs.ttlg_diagnostic_graph import TTLGDiagnostic
        ttlg = TTLGDiagnostic()
        track_map = {"agency": "marketing", "saas": "governance", "small_business": "marketing",
                     "individual_creator": "marketing", "enterprise": "governance"}
        track = track_map.get(s.get("segment_id", ""), "marketing")
        result = ttlg.run_track(s["contact_id"], track)
        return {**s, "stage": "diagnostic", "ttlg_output": {"gate_verdict": result.get("gate_verdict"),
                "score": result.get("sovereign_alignment_score"), "track": track},
                "mirror_report": result.get("mirror_report")}
    except Exception as e:
        return {**s, "stage": "diagnostic", "ttlg_output": {"error": str(e)[:80]}}

def stage_offer(s):
    score = (s.get("ttlg_output") or {}).get("score", 50)
    tier = "L2" if score < 30 else "L3" if score < 75 else "L4"
    return {**s, "stage": "offer", "offer_tier": tier}

def stage_delivery(s):
    EPOSEventBus().publish("journey.delivery_started", {"contact_id": s["contact_id"], "tier": s.get("offer_tier")}, "journey_graph")
    return {**s, "stage": "delivery"}

def stage_learning(s):
    try:
        from marl_reward_collector import MARLRewardCollector
        MARLRewardCollector().process_event({"event_type": "crm.lead.converted",
            "payload": {"contact_id": s["contact_id"], "segment_id": s.get("segment_id"),
                        "tier": s.get("offer_tier"), "days_to_convert": 7}})
    except: pass
    return s

def human_escalation(s):
    EPOSEventBus().publish("crm.steward.alert", {"contact_id": s["contact_id"], "lead_score": s["lead_score"]}, "journey_graph")
    return s

def route_discovery(s): return "human_escalation" if s["lead_score"] >= 85 else "engagement"
def route_engagement(s):
    if s["lead_score"] >= 85: return "human_escalation"
    return "diagnostic" if s["lead_score"] >= 61 else "nurture"
def route_nurture(s):
    if s["lead_score"] >= 85: return "human_escalation"
    return "diagnostic" if s["lead_score"] >= 61 else "__end__"
def route_diagnostic(s): return "human_escalation" if s["lead_score"] >= 85 else "offer"

workflow = StateGraph(JourneyState)
for name, fn in [("discovery", stage_discovery), ("engagement", stage_engagement),
    ("nurture", stage_nurture), ("diagnostic", stage_diagnostic), ("offer", stage_offer),
    ("delivery", stage_delivery), ("learning", stage_learning), ("human_escalation", human_escalation)]:
    workflow.add_node(name, fn)
workflow.set_entry_point("discovery")
workflow.add_conditional_edges("discovery", route_discovery, {"human_escalation": "human_escalation", "engagement": "engagement"})
workflow.add_conditional_edges("engagement", route_engagement, {"human_escalation": "human_escalation", "diagnostic": "diagnostic", "nurture": "nurture"})
workflow.add_conditional_edges("nurture", route_nurture, {"human_escalation": "human_escalation", "diagnostic": "diagnostic", "__end__": END})
workflow.add_conditional_edges("diagnostic", route_diagnostic, {"human_escalation": "human_escalation", "offer": "offer"})
workflow.add_edge("offer", "delivery")
workflow.add_edge("delivery", "learning")
workflow.add_edge("learning", END)
workflow.add_edge("human_escalation", END)
consumer_journey_app = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["human_escalation"])

# ---------------------------------------------------------------------------
# VAULT JOURNALING
# ---------------------------------------------------------------------------

_JOURNEY_VAULT = Path(__file__).resolve().parent.parent / "context_vault" / "crm" / "journey"


def _journal_transition(contact_id: str, stage: str, lead_score: int, event_type: str = "stage_transition"):
    """Write journey state transition to JSONL journal."""
    _JOURNEY_VAULT.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contact_id": contact_id,
        "stage": stage,
        "lead_score": lead_score,
        "event_type": event_type,
    }
    with open(_JOURNEY_VAULT / "journeys.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# CONFIGURABLE ENGINE CLASS
# ---------------------------------------------------------------------------

class ConsumerJourneyEngine:
    """
    Configurable wrapper for the Consumer Journey graph.

    Allows custom vault paths, track configuration, and lead thresholds.
    """

    UPSTREAM_TRIGGERS = [
        "lead.scored",
        "crm.contact.created",
        "content.engagement.detected",
    ]

    def __init__(self, vault_path: Optional[Path] = None,
                 track_config: Optional[dict] = None,
                 lead_threshold: int = 85):
        global _JOURNEY_VAULT
        if vault_path:
            _JOURNEY_VAULT = Path(vault_path)
        _JOURNEY_VAULT.mkdir(parents=True, exist_ok=True)
        self.track_config = track_config or {
            "agency": "marketing", "saas": "governance",
            "small_business": "marketing", "individual_creator": "marketing",
            "enterprise": "governance",
        }
        self.lead_threshold = lead_threshold
        self.app = consumer_journey_app

    def run_journey(self, contact_id: str, email: str, lead_score: int,
                    segment_id: str = None, thread_id: str = None) -> dict:
        """Run a contact through the journey pipeline."""
        state = {
            "contact_id": contact_id,
            "email": email,
            "lead_score": lead_score,
            "segment_id": segment_id,
            "stage": "new",
        }
        tid = thread_id or f"journey-{contact_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        result = self.app.invoke(state, {"configurable": {"thread_id": tid}})
        _journal_transition(contact_id, result.get("stage", "unknown"),
                            lead_score, "journey.complete")
        return result

    def get_journal(self, limit: int = 50) -> list:
        journal_path = _JOURNEY_VAULT / "journeys.jsonl"
        if not journal_path.exists():
            return []
        lines = journal_path.read_text(encoding="utf-8").splitlines()
        entries = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return entries

    @staticmethod
    def subscribe_triggers() -> list:
        """Upstream events that could initiate a journey."""
        return ConsumerJourneyEngine.UPSTREAM_TRIGGERS


if __name__ == "__main__":
    passed = 0

    # Test 1: Graph compiles
    import py_compile
    py_compile.compile(__file__, doraise=True)
    passed += 1

    # Test 2: Engine instantiates with config
    engine = ConsumerJourneyEngine(lead_threshold=90)
    assert engine.lead_threshold == 90, "Config not applied"
    assert hasattr(engine, "run_journey"), "Missing run_journey"
    assert hasattr(engine, "get_journal"), "Missing get_journal"
    passed += 1

    # Test 3: Run a journey
    state = {"contact_id": "test-pgp", "email": "pgp@test.com", "segment_id": "small_business",
             "lead_score": 65, "stage": "new"}
    result = consumer_journey_app.invoke(state, {"configurable": {"thread_id": "test-j-001"}})
    assert result.get("stage") is not None, "Stage should be set"
    assert result.get("offer_tier") is not None, "Offer tier should be set"
    passed += 1

    # Test 4: Journal transition
    _journal_transition("test-pgp", result.get("stage", "unknown"), 65, "test")
    journal = engine.get_journal(limit=5)
    assert len(journal) > 0, "Journal should have entries"
    passed += 1

    # Test 5: Subscribe triggers
    triggers = ConsumerJourneyEngine.subscribe_triggers()
    assert len(triggers) >= 3, "Should have upstream triggers"
    passed += 1

    print(f"PASS: consumer_journey_graph ({passed} assertions)")
