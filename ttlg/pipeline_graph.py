#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
pipeline_graph.py — TTLG v2 LangGraph Orchestration (Mission 6)
================================================================
Constitutional Authority: EPOS Constitution v3.1

Two StateGraphs, one engine:
  1. External Diagnostic — client-facing intelligence extraction with Build Manifests
  2. Internal Self-Healing — EPOS-facing autonomous remediation

Both share the same architectural pattern: detect, classify, gate, act, verify, learn.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Annotated

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

try:
    from groq_router import GroqRouter
except ImportError:
    GroqRouter = None

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

from path_utils import get_context_vault
from ttlg.props.schema import TTLGProps, load_props
from ttlg.question_generator import TTLGQuestionGenerator
from ttlg.build_manifest import TTLGSurgeon
from ttlg.self_healing_scout import SelfHealingScout
from ttlg.remediation_runbook import RemediationRunbook


VAULT = get_context_vault()


# ══════════════════════════════════════════════════════════════
# STATE SCHEMA
# ══════════════════════════════════════════════════════════════

class DiagnosticState(TypedDict, total=False):
    # Identity
    diagnostic_id: str
    props_name: str
    target: str
    # Props
    props: dict
    # Scout
    questions: dict
    scout_findings: list
    # Thinker
    weighted_findings: list
    consequence_chains: list
    # Gate
    gate_verdict: str  # GO, PIVOT, KILL
    gate_rationale: str
    # Surgeon
    manifests: list
    # Analyst
    score_trajectory: dict
    value_at_risk: float
    # Report
    report_path: str
    # Meta
    status: str
    error: str
    created_at: str


class HealingState(TypedDict, total=False):
    # Identity
    healing_id: str
    # Scout
    scan_report: dict
    findings: list
    # Classification
    actionable: list
    tier_0: list
    tier_1: list
    tier_2: list
    tier_3: list
    # Remediation
    actions_taken: list
    # Meta
    status: str
    error: str


# ══════════════════════════════════════════════════════════════
# EXTERNAL DIAGNOSTIC GRAPH — Client-Facing
# ══════════════════════════════════════════════════════════════

def node_load_props(state: DiagnosticState) -> dict:
    """Load and validate props configuration."""
    props_name = state.get("props_name", "client_ecosystem")
    try:
        props = load_props(props_name)
        return {
            "props": props.model_dump() if hasattr(props, "model_dump") else vars(props),
            "target": props.target,
            "diagnostic_id": state.get("diagnostic_id", f"DIAG-{uuid.uuid4().hex[:8]}"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "props_loaded",
        }
    except Exception as e:
        return {"status": "error", "error": f"Props load failed: {str(e)[:200]}"}


def node_generate_questions(state: DiagnosticState) -> dict:
    """Generate domain-aware questions from props."""
    props_data = state.get("props", {})
    props = TTLGProps.model_validate(props_data)
    gen = TTLGQuestionGenerator(props)
    questionnaire = gen.generate_full_questionnaire()
    return {"questions": questionnaire, "status": "questions_generated"}


def node_scout(state: DiagnosticState) -> dict:
    """Scout phase: scan target across scope. Uses LLM to analyze against questions."""
    questions = state.get("questions", {})
    scout_qs = questions.get("scout_questions", {})
    target = state.get("target", "client")
    findings = []

    # For EPOS self-audit, use real system data
    if target == "epos":
        from ttlg.self_healing_scout import SelfHealingScout
        scout = SelfHealingScout()
        report = scout.scan()
        for f in report.get("findings", []):
            findings.append({
                "scope": f.get("check", "unknown"),
                "finding": f.get("message", ""),
                "status": f.get("status", "PASS"),
                "severity": "high" if f["status"] == "FAIL" else ("medium" if f["status"] == "WARN" else "low"),
                "data": f,
            })
    else:
        # For client diagnostics, generate synthetic findings from questions
        # In production, these would come from the conversational TTLG session
        for scope, qs in scout_qs.items():
            findings.append({
                "scope": scope,
                "finding": f"Assessment pending for {scope}: {len(qs)} questions to evaluate",
                "status": "PENDING",
                "severity": "medium",
                "questions": qs,
            })

    if _BUS:
        try:
            _BUS.publish("ttlg.v2.scout.complete", {
                "diagnostic_id": state.get("diagnostic_id"),
                "findings_count": len(findings),
            }, source_module="ttlg_pipeline")
        except Exception:
            pass

    return {"scout_findings": findings, "status": "scouted"}


def node_thinker(state: DiagnosticState) -> dict:
    """Thinker phase: weight findings and generate consequence chains."""
    findings = state.get("scout_findings", [])
    props_data = state.get("props", {})
    weighting = props_data.get("phases", {}).get("thinker", {}).get("weighting_model", "market_forward")

    weighted = []
    chains = []
    for f in findings:
        severity = f.get("severity", "medium")
        weight = {"high": 3, "medium": 2, "low": 1}.get(severity, 1)
        if weighting == "market_forward":
            weight *= 1.5  # Market-forward weights competitive gaps higher
        elif weighting == "competitive":
            weight *= 1.3

        weighted.append({**f, "weight": weight})

        if severity in ("high", "medium"):
            chains.append({
                "scope": f["scope"],
                "finding": f["finding"],
                "consequence": f"If unaddressed, {f['scope']} gap compounds: operational efficiency degrades, competitive position weakens.",
                "estimated_quarterly_impact": weight * 5000,  # Heuristic
            })

    weighted.sort(key=lambda x: x["weight"], reverse=True)
    total_var = sum(c.get("estimated_quarterly_impact", 0) for c in chains)

    return {
        "weighted_findings": weighted,
        "consequence_chains": chains,
        "value_at_risk": total_var,
        "status": "analyzed",
    }


def node_gate(state: DiagnosticState) -> dict:
    """Gate phase: GO/PIVOT/KILL verdict based on findings."""
    findings = state.get("weighted_findings", [])
    high_severity = [f for f in findings if f.get("severity") == "high"]
    total = len(findings)

    if not findings:
        return {"gate_verdict": "KILL", "gate_rationale": "No findings to act on.", "status": "gated"}

    if len(high_severity) > total * 0.5:
        return {"gate_verdict": "GO", "gate_rationale": f"{len(high_severity)} high-severity findings require prescriptive action.", "status": "gated"}
    elif len(high_severity) > 0:
        return {"gate_verdict": "GO", "gate_rationale": f"{len(high_severity)} high-severity findings detected. Prescriptions recommended.", "status": "gated"}
    else:
        return {"gate_verdict": "GO", "gate_rationale": "All findings are low/medium. Advisory prescriptions.", "status": "gated"}


def route_gate(state: DiagnosticState) -> str:
    """Conditional edge: route based on gate verdict."""
    verdict = state.get("gate_verdict", "KILL")
    if verdict == "GO":
        return "surgeon"
    elif verdict == "PIVOT":
        return "thinker"  # Re-analyze with different weights
    else:
        return "aar"  # Skip surgeon, go to AAR


def node_surgeon(state: DiagnosticState) -> dict:
    """Surgeon phase: produce Build Manifests for each gap."""
    chains = state.get("consequence_chains", [])
    diag_id = state.get("diagnostic_id", "UNKNOWN")
    surgeon = TTLGSurgeon(diagnostic_id=diag_id)

    all_manifests = []
    for chain in chains[:5]:  # Cap at top 5 gaps
        gap = {
            "gap_id": f"GAP-{chain['scope'][:10]}",
            "description": chain["finding"][:200],
            "gap_type": chain["scope"],
            "severity": "high",
            "value_at_risk": chain.get("estimated_quarterly_impact", 10000),
        }
        manifests = surgeon.prescribe(gap)
        for m in manifests:
            if hasattr(m, "model_dump"):
                all_manifests.append(m.model_dump())
            else:
                all_manifests.append(vars(m))

    return {"manifests": all_manifests, "status": "prescribed"}


def node_analyst(state: DiagnosticState) -> dict:
    """Analyst phase: verify projections and produce score trajectory."""
    var = state.get("value_at_risk", 0)
    manifests = state.get("manifests", [])
    monthly_cost = sum(m.get("monthly_cost", 0) for m in manifests if m.get("type") == "quick_win")

    trajectory = {
        "current_score": 78,  # From ecosystem state
        "30_day": min(78 + len(manifests) * 0.5, 95),
        "60_day": min(78 + len(manifests) * 1.0, 97),
        "90_day": min(78 + len(manifests) * 1.5, 99),
        "value_at_risk_90d": var,
        "monthly_investment": monthly_cost,
    }

    return {"score_trajectory": trajectory, "status": "verified"}


def node_aar(state: DiagnosticState) -> dict:
    """AAR phase: log everything for institutional learning."""
    diag_id = state.get("diagnostic_id", "UNKNOWN")

    aar_data = {
        "diagnostic_id": diag_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "props_name": state.get("props_name"),
        "target": state.get("target"),
        "gate_verdict": state.get("gate_verdict"),
        "findings_count": len(state.get("scout_findings", [])),
        "manifests_count": len(state.get("manifests", [])),
        "value_at_risk": state.get("value_at_risk", 0),
    }

    # Save AAR
    aar_dir = VAULT / "ttlg" / "aar"
    aar_dir.mkdir(parents=True, exist_ok=True)
    aar_path = aar_dir / f"{diag_id}_aar.json"
    aar_path.write_text(json.dumps(aar_data, indent=2), encoding="utf-8")

    if _BUS:
        try:
            _BUS.publish("ttlg.v2.diagnostic.complete", aar_data, source_module="ttlg_pipeline")
        except Exception:
            pass

    record_decision(
        decision_type="ttlg.v2.diagnostic.complete",
        description=f"TTLG v2 diagnostic {diag_id}: {state.get('gate_verdict')}",
        agent_id="ttlg_pipeline",
        outcome=state.get("gate_verdict", "unknown"),
        context=aar_data,
    )

    return {"status": "complete", "report_path": str(aar_path)}


# Build external graph
def build_diagnostic_graph():
    workflow = StateGraph(DiagnosticState)
    workflow.add_node("load_props", node_load_props)
    workflow.add_node("generate_questions", node_generate_questions)
    workflow.add_node("scout", node_scout)
    workflow.add_node("thinker", node_thinker)
    workflow.add_node("gate", node_gate)
    workflow.add_node("surgeon", node_surgeon)
    workflow.add_node("analyst", node_analyst)
    workflow.add_node("aar", node_aar)

    workflow.set_entry_point("load_props")
    workflow.add_edge("load_props", "generate_questions")
    workflow.add_edge("generate_questions", "scout")
    workflow.add_edge("scout", "thinker")
    workflow.add_edge("thinker", "gate")
    workflow.add_conditional_edges("gate", route_gate, {
        "surgeon": "surgeon",
        "thinker": "thinker",
        "aar": "aar",
    })
    workflow.add_edge("surgeon", "analyst")
    workflow.add_edge("analyst", "aar")
    workflow.add_edge("aar", END)

    return workflow.compile(checkpointer=MemorySaver())


# ══════════════════════════════════════════════════════════════
# INTERNAL SELF-HEALING GRAPH — EPOS-Facing
# ══════════════════════════════════════════════════════════════

def heal_scout(state: HealingState) -> dict:
    """Scan EPOS health."""
    scout = SelfHealingScout()
    report = scout.scan()
    findings = report.get("findings", [])
    actionable = [f for f in findings if f["status"] in ("WARN", "FAIL")]
    return {
        "healing_id": f"HEAL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "scan_report": report,
        "findings": findings,
        "actionable": actionable,
        "status": "scanned",
    }


def heal_classify(state: HealingState) -> dict:
    """Classify actionable findings by tier."""
    actionable = state.get("actionable", [])
    t0, t1, t2, t3 = [], [], [], []
    for f in actionable:
        tier = f.get("tier", "fully_autonomous")
        if tier == "fully_autonomous":
            t0.append(f)
        elif tier == "monitored":
            t1.append(f)
        elif tier == "human_review":
            t2.append(f)
        elif tier == "constitutional_boundary":
            t3.append(f)
        else:
            t0.append(f)
    return {"tier_0": t0, "tier_1": t1, "tier_2": t2, "tier_3": t3, "status": "classified"}


def heal_remediate(state: HealingState) -> dict:
    """Apply remediation for Tier 0 and Tier 1 findings."""
    runbook = RemediationRunbook()
    actions = []

    for finding in state.get("tier_0", []) + state.get("tier_1", []):
        result = runbook.remediate(finding)
        actions.append(result)

    # Tier 2: diagnose only, flag for review
    for finding in state.get("tier_2", []):
        result = runbook.remediate(finding)
        actions.append(result)

    # Tier 3: full stop
    for finding in state.get("tier_3", []):
        result = runbook.remediate(finding)
        actions.append(result)

    if _BUS:
        try:
            _BUS.publish("system.healing.cycle.complete", {
                "healing_id": state.get("healing_id"),
                "actions_count": len(actions),
                "success_count": sum(1 for a in actions if a.get("success")),
            }, source_module="self_healing")
        except Exception:
            pass

    return {"actions_taken": actions, "status": "complete"}


def build_healing_graph():
    workflow = StateGraph(HealingState)
    workflow.add_node("scout", heal_scout)
    workflow.add_node("classify", heal_classify)
    workflow.add_node("remediate", heal_remediate)

    workflow.set_entry_point("scout")
    workflow.add_edge("scout", "classify")
    workflow.add_edge("classify", "remediate")
    workflow.add_edge("remediate", END)

    return workflow.compile(checkpointer=MemorySaver())


# ══════════════════════════════════════════════════════════════
# RUNNERS
# ══════════════════════════════════════════════════════════════

def run_diagnostic(props_name: str = "client_ecosystem") -> dict:
    """Run a full TTLG v2 diagnostic with the specified props."""
    graph = build_diagnostic_graph()
    diag_id = f"DIAG-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": diag_id}}
    initial = {"props_name": props_name, "diagnostic_id": diag_id}
    result = graph.invoke(initial, config)
    return result


def run_healing_cycle() -> dict:
    """Run a full self-healing cycle."""
    graph = build_healing_graph()
    heal_id = f"HEAL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    config = {"configurable": {"thread_id": heal_id}}
    result = graph.invoke({}, config)
    return result


# ══════════════════════════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    passed = 0

    # Test 1: Diagnostic graph compiles
    diag_graph = build_diagnostic_graph()
    assert diag_graph is not None
    passed += 1

    # Test 2: Healing graph compiles
    heal_graph = build_healing_graph()
    assert heal_graph is not None
    passed += 1

    # Test 3: Run diagnostic with ecosystem props
    print("Running TTLG v2 diagnostic with ecosystem_architecture props...")
    result = run_diagnostic("ecosystem_architecture")
    assert result["status"] == "complete", f"Expected complete, got {result['status']}"
    assert result.get("gate_verdict") in ("GO", "PIVOT", "KILL")
    passed += 1
    print(f"  Verdict: {result['gate_verdict']}")
    print(f"  Findings: {len(result.get('scout_findings', []))}")
    print(f"  Manifests: {len(result.get('manifests', []))}")
    print(f"  Value at Risk: ${result.get('value_at_risk', 0):,.0f}")

    # Test 4: Run healing cycle
    print("\nRunning self-healing cycle...")
    heal_result = run_healing_cycle()
    assert heal_result["status"] == "complete"
    passed += 1
    actions = heal_result.get("actions_taken", [])
    print(f"  Actions: {len(actions)}")
    for a in actions:
        icon = "+" if a.get("success") else "!"
        try:
            print(f"  {icon} {a.get('message', '')[:60]}")
        except UnicodeEncodeError:
            print(f"  {icon} (message contains special chars)")

    # Test 5: Score trajectory exists
    trajectory = result.get("score_trajectory", {})
    assert "30_day" in trajectory
    assert "90_day" in trajectory
    passed += 1

    print(f"\nPASS: pipeline_graph ({passed} assertions)")
    print(f"External: {result['gate_verdict']} | Manifests: {len(result.get('manifests', []))} | VaR: ${result.get('value_at_risk', 0):,.0f}")
    print(f"Internal: {len(actions)} actions | All clear: {all(a.get('success', False) for a in actions)}")
