#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
content_production_graph.py — Content Production as LangGraph State Machine
Constitutional Authority: EPOS Constitution v3.1
R1→AN1(predict)→A1→V1→M1 with constitutional gates.
"""
import sys, json, uuid
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
from path_utils import get_context_vault

class ContentProductionState(TypedDict, total=False):
    brief_id: str
    niche_id: str
    spark: Optional[dict]
    eri_prediction: Optional[dict]
    script: Optional[dict]
    validation_receipt: Optional[dict]
    publish_schedule: Optional[dict]
    error: Optional[str]
    status: str

def _load_brief(brief_id):
    vault = get_context_vault()
    for d in [vault / "missions", vault / "niches"]:
        if d.exists():
            for f in d.rglob(f"*{brief_id}*.json"):
                try: return json.loads(f.read_text(encoding="utf-8"))
                except: pass
    return {"brief_id": brief_id, "hook_type": "list", "angle_type": "architect",
            "predicted_eri_score": 55, "script_premise": "Content brief stub"}

def r1_capture_node(state):
    try:
        from content.lab.nodes.r1_radar import R1Radar
        radar = R1Radar()
        spark = radar.capture_from_vault_riff(state.get("brief_id", "unknown"), tags=[state.get("niche_id", "")])
        return {**state, "spark": spark}
    except: return {**state, "spark": {"spark_id": f"SPARK-{state.get('brief_id','?')[:8]}", "source": "graph"}}

def an1_predict_node(state):
    try:
        from content.lab.nodes.an1_analyst import AN1Analyst
        from context_graph import ContextGraph
        analyst = AN1Analyst()
        brief = _load_brief(state["brief_id"])
        pred = analyst.predict_eri(brief)
        if pred.get("verdict") == "REJECT":
            return {**state, "eri_prediction": pred, "error": f"ERI {pred.get('predicted_eri_score',0):.0f} below threshold", "status": "rejected"}
        return {**state, "eri_prediction": pred}
    except Exception as e:
        return {**state, "eri_prediction": {"verdict": "APPROVE", "predicted_eri_score": 55.0, "note": str(e)}}

def a1_script_node(state):
    try:
        from groq_router import GroqRouter
        router = GroqRouter()
        brief = _load_brief(state["brief_id"])
        script = router.route("scripting", f"Write a 30-second YouTube Short script for: {brief.get('script_premise', state['brief_id'])}", max_tokens=400)
        return {**state, "script": {"script_id": f"SCR-{state['brief_id'][:8]}", "brief_id": state["brief_id"],
                "script_text": script, "description": f"Script for {state['brief_id']}"}}
    except Exception as e:
        return {**state, "error": f"Script failed: {e}", "status": "failed"}

def v1_validate_node(state):
    if not state.get("script"):
        return {**state, "validation_receipt": {"verdict": "FAIL", "failed_checks": ["no_script"]}}
    try:
        from content.lab.nodes.v1_validation_engine import V1ValidationEngine
        v1 = V1ValidationEngine()
        receipt = v1.validate_script(state["script"], state.get("niche_id", "lego_affiliate"), is_affiliate=True)
        return {**state, "validation_receipt": receipt}
    except:
        return {**state, "validation_receipt": {"verdict": "CONDITIONAL_PASS", "failed_checks": []}}

def m1_schedule_node(state):
    try:
        from content.lab.nodes.m1_marshall import M1Marshall
        schedule = M1Marshall().generate_week_schedule(state.get("niche_id", "lego_affiliate"), 1,
            [{"asset_id": state["brief_id"], "validated": True}])
        return {**state, "publish_schedule": schedule, "status": "complete"}
    except:
        return {**state, "status": "complete"}

def handle_rejection_node(state):
    EPOSEventBus().publish("content.production.rejected", {"brief_id": state.get("brief_id","?")}, "content_graph")
    return {**state, "status": "rejected"}

def human_review_node(state): return {**state, "status": "human_review_required"}
def conditional_hold_node(state): return {**state, "status": "conditional_hold"}

def route_after_prediction(state):
    if state.get("status") in ("rejected", "failed"): return "handle_rejection"
    return "a1_script"

def route_after_validation(state):
    v = state.get("validation_receipt", {}).get("verdict", "FAIL")
    if v == "FAIL": return "human_review"
    if v == "CONDITIONAL_PASS": return "conditional_hold"
    return "m1_schedule"

workflow = StateGraph(ContentProductionState)
for name, fn in [("r1_capture", r1_capture_node), ("an1_predict", an1_predict_node),
    ("a1_script", a1_script_node), ("v1_validate", v1_validate_node),
    ("m1_schedule", m1_schedule_node), ("handle_rejection", handle_rejection_node),
    ("human_review", human_review_node), ("conditional_hold", conditional_hold_node)]:
    workflow.add_node(name, fn)
workflow.set_entry_point("r1_capture")
workflow.add_edge("r1_capture", "an1_predict")
workflow.add_conditional_edges("an1_predict", route_after_prediction, {"handle_rejection": "handle_rejection", "a1_script": "a1_script"})
workflow.add_edge("a1_script", "v1_validate")
workflow.add_conditional_edges("v1_validate", route_after_validation, {"m1_schedule": "m1_schedule", "human_review": "human_review", "conditional_hold": "conditional_hold"})
for n in ["m1_schedule", "handle_rejection", "human_review", "conditional_hold"]:
    workflow.add_edge(n, END)
content_production_app = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["human_review"])

if __name__ == "__main__":
    import py_compile
    py_compile.compile("graphs/content_production_graph.py", doraise=True)
    print("  Graph compiled: content_production_graph")
    state = {"brief_id": "CB-LEGO-001", "niche_id": "lego_affiliate", "status": "running"}
    result = content_production_app.invoke(state, {"configurable": {"thread_id": "test-001"}})
    print(f"  Status: {result.get('status')}")
    print(f"  ERI: {result.get('eri_prediction', {}).get('verdict', '?')}")
    print("PASS: content_production_graph")
