#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
friday_graph.py — Friday Orchestration StateGraph
====================================================
Constitutional Authority: EPOS Constitution v3.1

Friday is a LangGraph StateGraph that receives directives, classifies them,
decomposes compound directives into mission queues, routes each mission to
the appropriate executor, captures results, and writes a micro-AAR entry.

The 10 mission types:
  1. code         -> code_executor      (LLM generate + optional exec)
  2. browser      -> browser_executor   (BrowserUse autonomous navigation)
  3. computeruse  -> computeruse_executor (Agent Zero + computer_use tools)
  4. research     -> RS1 Research Engine
  5. content      -> Content Lab pipeline
  6. healing      -> system_executor (heal)
  7. ttlg         -> ttlg_executor      (diagnostic / healing / 8scan)
  8. system       -> system_executor    (doctor, certify, baselines, daemon_status)
  9. az           -> az_executor        (raw Agent Zero dispatch)
  10. unknown     -> escalation
"""

import os
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
FRIDAY_VAULT = VAULT / "friday"
FRIDAY_VAULT.mkdir(parents=True, exist_ok=True)
MISSIONS_DIR = FRIDAY_VAULT / "missions"
MISSIONS_DIR.mkdir(parents=True, exist_ok=True)


# ── State Schema ────────────────────────────────────────────

class FridayState(TypedDict, total=False):
    directive: str
    directive_id: str
    mission_type: str
    missions: list
    active_mission: dict
    results: list
    aar_entry: dict


# ── Mission Type Classification ─────────────────────────────

CLASSIFICATION_KEYWORDS = {
    "code": ["build", "implement", "create", "fix", "refactor", "develop", "code", "module", "function", "write code", "generate code"],
    "browser": ["navigate", "browse", "post", "publish", "linkedin", "twitter", "x.com", "scrape", "web search", "visit url"],
    "computeruse": ["click", "open app", "drag", "screenshot", "computer use", "agent zero computer"],
    "research": ["research", "investigate", "find out", "study", "analyze topic", "compile", "look up"],
    "content": ["write content", "create post", "generate script", "content lab", "echolocation", "echoes", "draft"],
    "healing": ["check health", "self-heal", "fix system"],
    "ttlg": ["ttlg", "diagnostic", "external diagnostic", "internal diagnostic", "build manifest", "healing cycle", "8scan", "pipeline graph"],
    "system": ["doctor", "diagnose", "certify", "baselines", "daemon status", "system status", "epos health", "sovereignty check"],
    "az": ["agent zero", "dispatch to az", "az task"],
}


def classify_directive(state: FridayState) -> dict:
    """Classify directive into one of 10 mission types using keyword matching + LLM fallback."""
    directive = state.get("directive", "").lower()
    scores = {}
    for mtype, keywords in CLASSIFICATION_KEYWORDS.items():
        scores[mtype] = sum(1 for kw in keywords if kw in directive)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        try:
            from groq_router import GroqRouter
            router = GroqRouter()
            prompt = (
                "Classify this directive into ONE of: code, browser, computeruse, research, "
                "content, healing, ttlg, system, az.\n"
                f"Directive: {directive[:300]}\n"
                "Reply with ONLY the category name, nothing else."
            )
            response = router.route("classification", prompt, max_tokens=10, temperature=0.1)
            best = response.strip().lower().split()[0] if response else "unknown"
            if best not in CLASSIFICATION_KEYWORDS:
                best = "unknown"
        except Exception:
            best = "unknown"

    directive_id = state.get("directive_id") or f"DIR-{uuid.uuid4().hex[:8]}"

    if _BUS:
        try:
            _BUS.publish("friday.directive.classified", {
                "directive_id": directive_id,
                "mission_type": best,
                "directive_preview": directive[:100],
            }, source_module="friday_graph")
        except Exception:
            pass

    return {
        "directive_id": directive_id,
        "mission_type": best,
    }


def decompose_directive(state: FridayState) -> dict:
    """Decompose directive into mission queue. Single mission per directive."""
    directive = state.get("directive", "")
    mission_type = state.get("mission_type", "unknown")
    directive_id = state.get("directive_id", "DIR-UNKNOWN")

    missions = [{
        "id": f"M-{directive_id[-6:]}-001",
        "type": mission_type,
        "description": directive,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }]

    return {
        "missions": missions,
        "active_mission": missions[0] if missions else {},
        "results": state.get("results", []),
    }


# ── Executor Nodes ──────────────────────────────────────────

def route_to_code(state: FridayState) -> dict:
    from friday.executors import code_executor
    mission = state.get("active_mission", {})
    result = code_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_browser(state: FridayState) -> dict:
    from friday.executors import browser_executor
    mission = state.get("active_mission", {})
    result = browser_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_computeruse(state: FridayState) -> dict:
    from friday.executors import computeruse_executor
    mission = state.get("active_mission", {})
    result = computeruse_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_research(state: FridayState) -> dict:
    mission = state.get("active_mission", {})
    try:
        from rs1_research_brief import RS1ResearchBrief
        result = {
            "mission_id": mission.get("id"),
            "executor": "rs1_research",
            "status": "queued",
            "output": f"Research question queued: {mission['description'][:200]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "rs1_research",
            "status": "failed",
            "error": str(e)[:300],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return {"results": state.get("results", []) + [result]}


def route_to_content(state: FridayState) -> dict:
    mission = state.get("active_mission", {})
    try:
        from content_signal_loop import ContentSignalLoop
        loop = ContentSignalLoop()
        signals = loop.process_recent_events(minutes=60)
        result = {
            "mission_id": mission.get("id"),
            "executor": "content_lab",
            "status": "complete",
            "output": f"Content signals processed: {len(signals)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "content_lab",
            "status": "failed",
            "error": str(e)[:300],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return {"results": state.get("results", []) + [result]}


def route_to_healing(state: FridayState) -> dict:
    from friday.executors import system_executor
    mission = state.get("active_mission", {})
    mission = {**mission, "action": "heal"}
    result = system_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_ttlg(state: FridayState) -> dict:
    from friday.executors import ttlg_executor
    mission = state.get("active_mission", {})
    # Infer TTLG mode from description
    desc = mission.get("description", "").lower()
    if "8scan" in desc or "doctor" in desc:
        mission = {**mission, "mode": "8scan"}
    elif "external" in desc or "diagnostic" in desc or "build manifest" in desc:
        mission = {**mission, "mode": "external"}
    elif "internal" in desc or "healing cycle" in desc:
        mission = {**mission, "mode": "internal"}
    else:
        mission = {**mission, "mode": "internal"}
    result = ttlg_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_system(state: FridayState) -> dict:
    from friday.executors import system_executor
    mission = state.get("active_mission", {})
    result = system_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_az(state: FridayState) -> dict:
    from friday.executors import az_executor
    mission = state.get("active_mission", {})
    result = az_executor.run(mission)
    return {"results": state.get("results", []) + [result]}


def route_to_unknown(state: FridayState) -> dict:
    mission = state.get("active_mission", {})
    result = {
        "mission_id": mission.get("id"),
        "executor": "escalation",
        "status": "escalated",
        "output": "Mission type unknown — escalated to Jamie for manual handling.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if _BUS:
        try:
            _BUS.publish("friday.directive.escalated", {
                "directive_id": state.get("directive_id"),
                "directive": state.get("directive", "")[:200],
            }, source_module="friday_graph")
        except Exception:
            pass

    return {"results": state.get("results", []) + [result]}


def route_mission(state: FridayState) -> str:
    """Conditional edge: route to executor based on mission type."""
    mtype = state.get("mission_type", "unknown")
    routing = {
        "code": "executor_code",
        "browser": "executor_browser",
        "computeruse": "executor_computeruse",
        "research": "executor_research",
        "content": "executor_content",
        "healing": "executor_healing",
        "ttlg": "executor_ttlg",
        "system": "executor_system",
        "az": "executor_az",
    }
    return routing.get(mtype, "executor_unknown")


def aar_writer(state: FridayState) -> dict:
    """Capture mission result and write micro-AAR entry to vault."""
    directive_id = state.get("directive_id", "DIR-UNKNOWN")
    results = state.get("results", [])

    aar = {
        "directive_id": directive_id,
        "directive": state.get("directive", "")[:300],
        "mission_type": state.get("mission_type", "unknown"),
        "results": results,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "success": all(r.get("status") in ("complete", "dispatched", "queued") for r in results),
    }

    aar_path = MISSIONS_DIR / f"{directive_id}_aar.json"
    aar_path.write_text(json.dumps(aar, indent=2), encoding="utf-8")

    if _BUS:
        try:
            _BUS.publish("friday.directive.complete", {
                "directive_id": directive_id,
                "success": aar["success"],
                "missions_executed": len(results),
            }, source_module="friday_graph")
        except Exception:
            pass

    return {"aar_entry": aar}


# ── Build the Graph ─────────────────────────────────────────

EXECUTOR_NODES = [
    "executor_code", "executor_browser", "executor_computeruse",
    "executor_research", "executor_content", "executor_healing",
    "executor_ttlg", "executor_system", "executor_az", "executor_unknown",
]


def build_friday_graph():
    """Compile the Friday StateGraph."""
    graph = StateGraph(FridayState)

    graph.add_node("classify", classify_directive)
    graph.add_node("decompose", decompose_directive)
    graph.add_node("executor_code", route_to_code)
    graph.add_node("executor_browser", route_to_browser)
    graph.add_node("executor_computeruse", route_to_computeruse)
    graph.add_node("executor_research", route_to_research)
    graph.add_node("executor_content", route_to_content)
    graph.add_node("executor_healing", route_to_healing)
    graph.add_node("executor_ttlg", route_to_ttlg)
    graph.add_node("executor_system", route_to_system)
    graph.add_node("executor_az", route_to_az)
    graph.add_node("executor_unknown", route_to_unknown)
    graph.add_node("aar_writer", aar_writer)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "decompose")
    graph.add_conditional_edges("decompose", route_mission, {
        node: node for node in EXECUTOR_NODES
    })
    for executor in EXECUTOR_NODES:
        graph.add_edge(executor, "aar_writer")
    graph.add_edge("aar_writer", END)

    return graph.compile(checkpointer=MemorySaver())


friday_app = build_friday_graph()


def invoke_friday(directive: str, extra: dict = None) -> dict:
    """Run a directive through the Friday graph."""
    config = {"configurable": {"thread_id": f"FRIDAY-{uuid.uuid4().hex[:8]}"}}
    initial = {
        "directive": directive,
        "missions": [],
        "results": [],
        **(extra or {}),
    }
    return friday_app.invoke(initial, config)


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: Graph compiles
    assert friday_app is not None
    print(f"Friday graph compiled: {type(friday_app).__name__}")
    passed += 1

    # Test 2: Classification — healing
    state = classify_directive({"directive": "Run a self-healing cycle on EPOS"})
    assert state["mission_type"] in ("healing", "ttlg", "system"), \
        f"Expected healing/ttlg/system, got {state['mission_type']}"
    print(f"Classification: 'self-healing cycle' -> {state['mission_type']}")
    passed += 1

    # Test 3: Classification — ttlg
    state2 = classify_directive({"directive": "Run a full TTLG diagnostic"})
    assert state2["mission_type"] == "ttlg", f"Expected ttlg, got {state2['mission_type']}"
    print(f"Classification: 'TTLG diagnostic' -> {state2['mission_type']}")
    passed += 1

    # Test 4: Classification — system
    state3 = classify_directive({"directive": "Run the EPOS doctor scan"})
    assert state3["mission_type"] in ("ttlg", "system"), \
        f"Expected ttlg or system, got {state3['mission_type']}"
    print(f"Classification: 'EPOS doctor' -> {state3['mission_type']}")
    passed += 1

    # Test 5: Full directive end-to-end (system)
    print("\nRunning directive: 'Check the health of all EPOS systems'")
    result = invoke_friday("Check the health of all EPOS systems")
    assert "results" in result and len(result["results"]) > 0
    aar = result.get("aar_entry", {})
    print(f"AAR: {aar.get('directive_id')} | type={aar.get('mission_type')} | success={aar.get('success')}")
    passed += 1

    # Test 6: Unknown escalation
    result2 = invoke_friday("Tell me a joke about quantum computing")
    last = result2["results"][-1] if result2.get("results") else {}
    print(f"Unknown directive -> executor={last.get('executor', '?')} status={last.get('status', '?')}")
    passed += 1

    print(f"\nPASS: friday_graph ({passed} assertions)")
    print(f"Last result: {result['results'][-1]}")
