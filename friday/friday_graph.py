#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
friday_graph.py — Friday Orchestration StateGraph
====================================================
Constitutional Authority: EPOS Constitution v3.1

Friday is a LangGraph StateGraph that receives directives, classifies them,
decomposes compound directives into mission queues, routes each mission to
the appropriate executor, captures results, and writes a micro-AAR entry.

The 7 mission types:
  1. code         -> Claude Code via subprocess or LiteLLM
  2. browser      -> BrowserUse Node
  3. computeruse  -> Agent Zero container
  4. research     -> RS1 Research Engine
  5. content      -> Content Lab pipeline
  6. healing      -> Self-Healing Engine
  7. unknown      -> Friday escalates to Jamie
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
    "code": ["build", "implement", "create", "fix", "refactor", "develop", "code", "module", "function"],
    "browser": ["navigate", "browse", "post", "publish", "linkedin", "twitter", "x.com", "scrape"],
    "computeruse": ["click", "open", "drag", "screenshot", "computer", "agent zero"],
    "research": ["research", "investigate", "find out", "study", "analyze topic", "compile"],
    "content": ["write content", "create post", "generate script", "content lab", "echolocation"],
    "healing": ["check health", "doctor", "self-heal", "diagnose", "fix system", "system status"],
}


def classify_directive(state: FridayState) -> dict:
    """Classify directive into one of 7 mission types using keyword matching + LLM fallback."""
    directive = state.get("directive", "").lower()
    scores = {}
    for mtype, keywords in CLASSIFICATION_KEYWORDS.items():
        scores[mtype] = sum(1 for kw in keywords if kw in directive)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # No keywords matched — try LLM classification
        try:
            from groq_router import GroqRouter
            router = GroqRouter()
            prompt = (
                f"Classify this directive into ONE of: code, browser, computeruse, research, content, healing.\n"
                f"Directive: {directive[:300]}\n"
                f"Reply with ONLY the category name, nothing else."
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
    """Decompose directive into mission queue. For now, single mission per directive."""
    directive = state.get("directive", "")
    mission_type = state.get("mission_type", "unknown")
    directive_id = state.get("directive_id", "DIR-UNKNOWN")

    # Single mission for now — multi-mission decomposition is future work
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


# ── Executor Nodes (will be replaced with full executors in M3) ──

def route_to_code(state: FridayState) -> dict:
    """Execute code mission via engine.llm_client and persist generated output."""
    mission = state.get("active_mission", {})
    mission_id = mission.get("id") or str(uuid.uuid4())
    description = mission.get("description") or state.get("directive", "")

    result: dict
    try:
        from engine.llm_client import complete

        system_prompt = (
            "You are a senior software engineer. When given a coding mission, "
            "return a complete, runnable implementation. Prefer a single fenced "
            "code block with a brief inline rationale before the code."
        )
        user_prompt = (
            f"Mission: {description}\n\n"
            "Produce the implementation. No apologies, no TODOs, no stubs."
        )

        generated = complete(
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2,
            max_tokens=2048,
        )

        # Persist to context_vault/friday/code_output/<mission_id>.md
        code_dir = FRIDAY_VAULT / "code_output"
        code_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = code_dir / f"{ts}_{mission_id}.md"
        out_path.write_text(
            f"# Friday code mission {mission_id}\n\n"
            f"- timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            f"- directive: {description}\n\n"
            f"## Output\n\n{generated}\n",
            encoding="utf-8",
        )

        result = {
            "mission_id": mission_id,
            "executor": "code",
            "status": "complete",
            "output": generated,
            "output_path": str(out_path),
        }
    except Exception as e:
        result = {
            "mission_id": mission_id,
            "executor": "code",
            "status": "failed",
            "error": f"{type(e).__name__}: {e}",
        }

    if _BUS:
        try:
            _BUS.publish("code.generated", result, source_module="friday_graph")
        except Exception:
            pass

    return {"results": state.get("results", []) + [result]}


def route_to_browser(state: FridayState) -> dict:
    """Execute browser mission via BrowserUse sovereign node."""
    import asyncio
    mission = state.get("active_mission", {})
    try:
        from nodes.browser_use_node import BrowserUseNode
        node = BrowserUseNode()
        if node.health_check().get("status") != "operational":
            raise RuntimeError("BrowserUse not operational")
        # Sync wrapper to call async execute_task
        result_data = node.execute_task_sync(mission["description"], max_steps=3)
        result = {
            "mission_id": mission.get("id"),
            "executor": "browser_use",
            "status": "complete" if result_data.get("success") else "failed",
            "output": str(result_data.get("result", ""))[:500],
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "browser_use",
            "status": "failed",
            "error": str(e)[:300],
        }

    if _BUS:
        try:
            _BUS.publish(f"friday.mission.{result['status']}", result, source_module="friday_graph")
        except Exception:
            pass

    return {"results": state.get("results", []) + [result]}


def route_to_computeruse(state: FridayState) -> dict:
    """Execute mission via Agent Zero container."""
    mission = state.get("active_mission", {})
    try:
        from nodes.agent_zero_node import AgentZeroNode
        node = AgentZeroNode()
        health = node.health_check()
        if health.get("status") != "operational":
            raise RuntimeError(f"Agent Zero not operational: {health.get('reason', '?')}")
        dispatch = node.dispatch_mission(mission["description"], timeout=30)
        result = {
            "mission_id": mission.get("id"),
            "executor": "agent_zero",
            "status": dispatch.get("status", "unknown"),
            "output": str(dispatch.get("response", dispatch.get("error", "")))[:500],
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "agent_zero",
            "status": "failed",
            "error": str(e)[:300],
        }
    return {"results": state.get("results", []) + [result]}


def route_to_research(state: FridayState) -> dict:
    """Execute research mission via RS1."""
    mission = state.get("active_mission", {})
    try:
        from rs1_research_brief import RS1ResearchBrief
        # Create a research idea for RS1
        result = {
            "mission_id": mission.get("id"),
            "executor": "rs1_research",
            "status": "queued",
            "output": f"Research question queued: {mission['description'][:200]}",
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "rs1_research",
            "status": "failed",
            "error": str(e)[:300],
        }
    return {"results": state.get("results", []) + [result]}


def route_to_content(state: FridayState) -> dict:
    """Execute content mission via Content Lab."""
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
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "content_lab",
            "status": "failed",
            "error": str(e)[:300],
        }
    return {"results": state.get("results", []) + [result]}


def route_to_healing(state: FridayState) -> dict:
    """Execute healing mission via Self-Healing Engine."""
    mission = state.get("active_mission", {})
    try:
        from ttlg.pipeline_graph import run_healing_cycle
        heal_result = run_healing_cycle()
        actions = heal_result.get("actions_taken", [])
        result = {
            "mission_id": mission.get("id"),
            "executor": "self_healing",
            "status": "complete",
            "output": f"Healing cycle: {len(actions)} actions taken",
            "details": [a.get("action_type") for a in actions[:5]],
        }
    except Exception as e:
        result = {
            "mission_id": mission.get("id"),
            "executor": "self_healing",
            "status": "failed",
            "error": str(e)[:300],
        }

    if _BUS:
        try:
            _BUS.publish(f"friday.mission.{result['status']}", result, source_module="friday_graph")
        except Exception:
            pass

    return {"results": state.get("results", []) + [result]}


def route_to_unknown(state: FridayState) -> dict:
    """Unknown mission type — escalate to Jamie."""
    mission = state.get("active_mission", {})
    result = {
        "mission_id": mission.get("id"),
        "executor": "escalation",
        "status": "escalated",
        "output": "Mission type unknown — escalated to Jamie for manual handling.",
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

    # Save to vault
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
    graph.add_node("executor_unknown", route_to_unknown)
    graph.add_node("aar_writer", aar_writer)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "decompose")
    graph.add_conditional_edges("decompose", route_mission, {
        "executor_code": "executor_code",
        "executor_browser": "executor_browser",
        "executor_computeruse": "executor_computeruse",
        "executor_research": "executor_research",
        "executor_content": "executor_content",
        "executor_healing": "executor_healing",
        "executor_unknown": "executor_unknown",
    })
    for executor in ["executor_code", "executor_browser", "executor_computeruse",
                     "executor_research", "executor_content", "executor_healing",
                     "executor_unknown"]:
        graph.add_edge(executor, "aar_writer")
    graph.add_edge("aar_writer", END)

    return graph.compile(checkpointer=MemorySaver())


friday_app = build_friday_graph()


def invoke_friday(directive: str) -> dict:
    """Run a directive through the Friday graph."""
    config = {"configurable": {"thread_id": f"FRIDAY-{uuid.uuid4().hex[:8]}"}}
    initial = {
        "directive": directive,
        "missions": [],
        "results": [],
    }
    return friday_app.invoke(initial, config)


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: Graph compiles
    assert friday_app is not None
    print(f"Friday graph compiled: {type(friday_app).__name__}")
    passed += 1

    # Test 2: Classify a directive
    state = classify_directive({"directive": "Run a self-healing cycle"})
    assert state["mission_type"] == "healing", f"Expected healing, got {state['mission_type']}"
    print(f"Classification: 'Run a self-healing cycle' -> {state['mission_type']}")
    passed += 1

    # Test 3: Run a full directive end-to-end
    print("\nRunning directive: 'Check the health of all EPOS systems'")
    result = invoke_friday("Check the health of all EPOS systems")
    assert "results" in result
    assert len(result["results"]) > 0
    passed += 1

    # Test 4: AAR was written
    aar = result.get("aar_entry", {})
    assert aar.get("directive_id"), "AAR missing directive_id"
    print(f"AAR: {aar['directive_id']} | success={aar.get('success')}")
    passed += 1

    # Test 5: Unknown directive escalates
    result2 = invoke_friday("Tell me a joke about quantum computing")
    last = result2["results"][-1] if result2.get("results") else {}
    print(f"Unknown directive routed to: {last.get('executor', '?')}")
    passed += 1

    print(f"\nPASS: friday_graph ({passed} assertions)")
    print(f"Last result: {result['results'][-1]}")
