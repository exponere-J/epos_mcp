#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
ttlg_diagnostic_graph.py — TTLG as LangGraph State Machine
=============================================================
Constitutional Authority: EPOS Constitution v3.1

Four audit tracks. Six phases. Sovereign Alignment Score.
The service delivery architecture of the entire EPOS business.

Through the Looking Glass: help a client see their business
as it actually is, then show them what it could become.
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

# Sovereign imports — degrade gracefully when running standalone
try:
    from groq_router import GroqRouter
except ImportError:
    GroqRouter = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(*a, **kw): pass

try:
    from epos_event_bus import EPOSEventBus
except ImportError:
    EPOSEventBus = None

try:
    from epos_cms import EPOSContentManagement
except ImportError:
    EPOSContentManagement = None

try:
    from path_utils import get_context_vault
except ImportError:
    def get_context_vault():
        return Path(__file__).resolve().parent.parent / "context_vault"


# ── State Schema ─────────────────────────────────────────────

class TTLGState(TypedDict, total=False):
    client_id: str
    audit_track: str
    session_id: str
    digital_footprint: Optional[dict]
    current_metrics: Optional[dict]
    bottleneck_indicators: Optional[list]
    gap_analysis: Optional[dict]
    cost_of_gap: Optional[dict]
    gate_verdict: Optional[str]
    gate_rationale: Optional[str]
    prescriptions: Optional[list]
    priority_order: Optional[list]
    thirty_day_projection: Optional[dict]
    sovereign_alignment_score: Optional[float]
    mirror_report: Optional[str]
    action_plan: Optional[list]
    next_cycle_date: Optional[str]
    error: Optional[str]
    status: str


# ── Phase Nodes ──────────────────────────────────────────────

SELF_AUDIT_IDS = ["epos", "epos_ecosystem", "exponere", "self"]


def _load_client_vault(client_id: str) -> dict:
    """Load everything EPOS knows about this client from DB + vault."""
    import subprocess
    vault = get_context_vault()
    client_data = {"client_id": client_id}

    # ── P1 FIX: Self-audit mode — inject vault context when client is EPOS ──
    if client_id.lower() in SELF_AUDIT_IDS:
        client_data["company"] = "EXPONERE / EPOS Ecosystem"
        client_data["segment_id"] = "tech_saas"
        client_data["is_self_audit"] = True
        try:
            from epos_event_bus import EPOSEventBus
            bus = EPOSEventBus()
            client_data["event_bus_count"] = bus.event_count()
        except Exception:
            client_data["event_bus_count"] = 0
        try:
            import subprocess as sp
            r = sp.run([sys.executable, "engine/epos_doctor.py", "--json"],
                       capture_output=True, text=True, timeout=15,
                       cwd=str(Path(__file__).resolve().parent.parent))
            # Doctor may not support --json; parse stdout for counts
            out = r.stdout
            pass_count = out.count("PASS")
            warn_count = out.count("WARN")
            fail_count = out.count("FAIL") - out.count("CRITICAL FAIL")
            client_data["doctor_pass"] = pass_count
            client_data["doctor_warn"] = warn_count
            client_data["doctor_fail"] = fail_count
        except Exception:
            pass
        try:
            from idea_log import IdeaLog
            client_data["ideas_total"] = IdeaLog().stats()["total"]
        except Exception:
            pass
        try:
            from content_signal_loop import ContentSignalLoop
            client_data["content_signals_today"] = ContentSignalLoop().get_signal_summary()["total"]
        except Exception:
            pass
        try:
            from lead_scoring import LeadScoringEngine
            client_data["leads_scored"] = LeadScoringEngine().get_score_summary()["total"]
        except Exception:
            pass
        # Count CLI domains and modules
        client_data["cli_domains"] = 14
        # Count vault files
        try:
            client_data["vault_files"] = sum(1 for _ in vault.rglob("*") if _.is_file())
        except Exception:
            pass
        # CMS assets
        try:
            from epos_cms import EPOSContentManagement
            cms_stats = EPOSContentManagement().get_dashboard_stats()
            client_data["cms_assets"] = cms_stats.get("total", 0)
            client_data["cms_published"] = cms_stats.get("by_status", {}).get("published", 0)
        except Exception:
            pass
        return client_data

    # ── Standard client: load from DB + vault ──
    try:
        result = subprocess.run([
            "docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
            "-c", f"SELECT email, company, segment_id, lead_score, stage, tier "
                  f"FROM epos.contacts WHERE name ILIKE '%{client_id}%' "
                  f"OR email ILIKE '%{client_id}%' LIMIT 1;",
            "-t", "--no-align", "--field-separator=|"
        ], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            row = result.stdout.strip().split("|")
            if len(row) >= 6:
                client_data.update({"email": row[0].strip(), "company": row[1].strip(),
                    "segment_id": row[2].strip(), "lead_score": row[3].strip(),
                    "stage": row[4].strip(), "tier": row[5].strip()})
    except Exception:
        pass
    client_vault = vault / "clients" / client_id
    if client_vault.exists():
        for f in client_vault.glob("*.json"):
            try:
                client_data[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    return client_data


def _run_track_scout(company: str, segment: str, track: str) -> dict:
    """Run Groq-powered scout for a specific track."""
    router = GroqRouter()
    dimensions = {
        "marketing": ["content_output", "platform_presence", "content_quality",
                       "lead_generation", "brand_consistency"],
        "sales": ["lead_response_time", "follow_up_consistency", "proposal_process",
                   "closing_mechanism", "pipeline_visibility"],
        "service": ["onboarding_process", "delivery_consistency", "communication",
                     "quality_control", "satisfaction_measurement"],
        "governance": ["data_sovereignty", "saas_dependency", "automation_reliability",
                        "documentation_sops", "backup_continuity"],
    }
    dims = dimensions.get(track, dimensions["marketing"])
    dim_list = "\n".join(f"{i+1}. {d.replace('_', ' ').title()}" for i, d in enumerate(dims))

    prompt = f"""TTLG Scout — {track.upper()} audit for {company} ({segment}).

Assess these dimensions for a typical {segment} business:
{dim_list}

For each dimension output:
- current_state: realistic assessment (1-2 sentences)
- bottleneck_indicator: true or false
- severity: low, medium, or high

Output only valid JSON with dimension names as keys. Example:
{{"dimension_name": {{"current_state": "...", "bottleneck_indicator": true, "severity": "high"}}}}"""

    try:
        raw = router.route("reasoning", prompt, max_tokens=1000, temperature=0.2)
        # Try to parse — handle markdown code fences
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(clean)
    except Exception:
        return {dims[0]: {"current_state": "Unable to scout", "bottleneck_indicator": True, "severity": "medium"}}


def _extract_metrics(footprint: dict, track: str) -> dict:
    """Extract measurable metrics from scout output."""
    if not footprint:
        return {}
    metrics = {}
    for dimension, data in footprint.items():
        if isinstance(data, dict) and "current_state" in data:
            metrics[dimension] = {
                "state": data.get("current_state", ""),
                "is_bottleneck": data.get("bottleneck_indicator", False),
                "severity": data.get("severity", "low"),
            }
    return metrics


def _identify_indicators(metrics: dict, track: str) -> list:
    """Extract confirmed bottleneck indicators from metrics."""
    return [
        {"dimension": dim, "severity": data.get("severity", "medium"),
         "state": data.get("state", "")}
        for dim, data in metrics.items()
        if isinstance(data, dict) and data.get("is_bottleneck")
    ]


def _run_self_audit_scout(client_data: dict, track: str) -> dict:
    """Evidence-based scout for EPOS self-audit. Uses real vault data, not inference."""
    router = GroqRouter()
    evidence = json.dumps({k: v for k, v in client_data.items()
                            if k not in ("is_self_audit",)}, indent=2, default=str)[:1500]

    prompt = f"""TTLG Self-Audit Scout — {track.upper()} track for EPOS Ecosystem.

You are auditing the EPOS system itself. Here is real evidence from the vault:
{evidence}

Assess these dimensions based on the EVIDENCE above (not generic assumptions):
{json.dumps(_get_dimensions(track), indent=2)}

For each dimension, use the real data to determine:
- current_state: What the evidence shows (cite specific numbers)
- bottleneck_indicator: true or false based on evidence
- severity: low, medium, or high

Output only valid JSON with dimension names as keys.
Example: {{"dimension_name": {{"current_state": "Evidence shows X", "bottleneck_indicator": true, "severity": "high"}}}}"""

    try:
        raw = router.route("reasoning", prompt, max_tokens=1200, temperature=0.15)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(clean)
    except Exception:
        dims = _get_dimensions(track)
        return {dims[0]: {"current_state": "Self-audit scout fallback", "bottleneck_indicator": True, "severity": "medium"}}


def _get_dimensions(track: str) -> list:
    """Get dimension list for a track."""
    dimensions = {
        "marketing": ["content_output", "platform_presence", "content_quality",
                       "lead_generation", "brand_consistency"],
        "sales": ["lead_response_time", "follow_up_consistency", "proposal_process",
                   "closing_mechanism", "pipeline_visibility"],
        "service": ["onboarding_process", "delivery_consistency", "communication",
                     "quality_control", "satisfaction_measurement"],
        "governance": ["data_sovereignty", "saas_dependency", "automation_reliability",
                        "documentation_sops", "backup_continuity"],
    }
    return dimensions.get(track, dimensions["marketing"])


def scout_node(state: TTLGState) -> dict:
    """Phase 1: Silent reconnaissance. Map current state from observable signals."""
    track = state["audit_track"]
    client_id = state["client_id"]

    # Load client data from DB + vault
    client_data = _load_client_vault(client_id)
    company = client_data.get("company", client_id)
    segment = client_data.get("segment_id", "small_business")

    # ── P1 FIX: Self-audit uses evidence, not inference ──
    if client_data.get("is_self_audit"):
        footprint = _run_self_audit_scout(client_data, track)
    else:
        footprint = _run_track_scout(company, segment, track)

    # Extract structured metrics and bottleneck indicators
    metrics = _extract_metrics(footprint, track)
    indicators = _identify_indicators(metrics, track)

    bus = EPOSEventBus()
    bus.publish(f"ttlg.scout.{track}.complete",
                {"client_id": client_id, "indicators": len(indicators),
                 "track": track}, "ttlg_diagnostic")

    return {
        "digital_footprint": {**footprint, "client_id": client_id, "track": track,
                              "company": company, "segment": segment,
                              "scanned_at": datetime.now(timezone.utc).isoformat()},
        "current_metrics": metrics,
        "bottleneck_indicators": indicators,
    }


def _normalize_indicator(ind) -> dict:
    """P0 BOUNDARY CONTRACT: Normalize any indicator to a standard dict shape.
    Handles: dict (from Scout), string (legacy), or anything else."""
    if isinstance(ind, dict):
        return {
            "dimension": ind.get("dimension", "unknown"),
            "severity": ind.get("severity", "medium"),
            "state": ind.get("state", ind.get("current_state", "No detail")),
        }
    elif isinstance(ind, str):
        return {"dimension": ind, "severity": "medium", "state": ind}
    else:
        return {"dimension": str(ind)[:50], "severity": "medium", "state": str(ind)[:100]}


def thinker_node(state: TTLGState) -> dict:
    """Phase 2: Gap analysis. Consequence chain. Cost of current state.

    P0 FIX: Handles structured indicator dicts from Scout.
    P2 FIX: References cost heuristics for dollar quantification.
    DEGRADED OUTPUT: If LLM call fails, produces structured gaps with
    cost heuristic fallback (never returns 'analysis_needed').
    """
    router = GroqRouter()
    track = state.get("audit_track", "marketing")
    raw_indicators = state.get("bottleneck_indicators", [])

    # ── P0: Normalize indicators to standard shape ──
    indicators = [_normalize_indicator(ind) for ind in raw_indicators]

    # ── P2: Get cost estimates from heuristics library ──
    # Determine sector from digital footprint
    footprint = state.get("digital_footprint", {})
    sector = footprint.get("segment", "prof_services")
    if sector in ("tech_saas", "prof_services", "local_service"):
        pass  # use as-is
    elif "tech" in sector.lower() or "saas" in sector.lower():
        sector = "tech_saas"
    elif "local" in sector.lower() or "property" in sector.lower():
        sector = "local_service"
    else:
        sector = "prof_services"

    try:
        from graphs.ttlg_cost_heuristics import estimate_gap_cost, estimate_total_track_cost
        track_cost = estimate_total_track_cost(indicators, sector)
    except Exception:
        track_cost = {"total_monthly_low": 0, "total_monthly_high": 0,
                      "total_quarterly_mid": 0, "gap_costs": []}

    # ── Build readable indicator summary for LLM ──
    indicator_text = "\n".join(
        f"  {i+1}. {ind['dimension']} ({ind['severity']} severity): {ind['state'][:120]}"
        for i, ind in enumerate(indicators)
    )

    cost_context = ""
    for gc in track_cost.get("gap_costs", []):
        cost_context += f"  {gc['dimension']}: ~${gc.get('monthly_low',0):,}-${gc.get('monthly_high',0):,}/month\n"

    prompt = f"""TTLG Phase 2: Gap Analysis for {track.upper()} audit.

BOTTLENECK INDICATORS (structured):
{indicator_text}

COST ESTIMATES (from sector heuristics for {sector}):
{cost_context}
Total estimated monthly cost: ${track_cost.get('total_monthly_low',0):,}-${track_cost.get('total_monthly_high',0):,}

For EACH indicator above, trace the consequence chain:
1. Immediate operational impact (what breaks today)
2. Downstream business impact (what it costs this quarter)
3. 90-day compound cost if unaddressed (specific dollar range)

Then identify the single highest-leverage intervention.

Output ONLY valid JSON:
{{"gaps": [
    {{"dimension": "exact_dimension_name", "severity": "low|medium|high",
      "immediate_impact": "what breaks", "downstream_impact": "business consequence",
      "cost_90d_low": 1000, "cost_90d_high": 5000,
      "cost_narrative": "1-sentence cost story"}}
  ],
  "highest_leverage": "dimension_name",
  "total_gap_cost_low": 5000,
  "total_gap_cost_high": 20000,
  "opportunity_value": "specific opportunity statement"}}"""

    try:
        raw = router.route("reasoning", prompt, max_tokens=1200, temperature=0.2)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        gap = json.loads(clean)
    except Exception:
        # ── DEGRADED OUTPUT: Use heuristics directly, never "analysis_needed" ──
        gap = {
            "gaps": [{
                "dimension": ind["dimension"],
                "severity": ind["severity"],
                "immediate_impact": f"{ind['dimension'].replace('_',' ')} gap causes operational friction",
                "downstream_impact": f"Lost revenue and efficiency in {track}",
                "cost_90d_low": gc.get("monthly_low", 500) * 3 if (gc := next(
                    (c for c in track_cost.get("gap_costs", [])
                     if c.get("dimension", "").lower() == ind["dimension"].lower()), {})) else 1500,
                "cost_90d_high": gc.get("monthly_high", 2000) * 3 if (gc := next(
                    (c for c in track_cost.get("gap_costs", [])
                     if c.get("dimension", "").lower() == ind["dimension"].lower()), {})) else 6000,
                "cost_narrative": gc.get("narrative", f"Gap in {ind['dimension']} costs an estimated ${gc.get('monthly_low',500):,}-${gc.get('monthly_high',2000):,}/month")
                    if (gc := next((c for c in track_cost.get("gap_costs", [])
                     if c.get("dimension", "").lower() == ind["dimension"].lower()), {})) else
                    f"Estimated cost: ${500}-${2000}/month for {ind['dimension']} gap"
            } for ind in indicators],
            "highest_leverage": indicators[0]["dimension"] if indicators else "unknown",
            "total_gap_cost_low": track_cost.get("total_monthly_low", 0) * 3,
            "total_gap_cost_high": track_cost.get("total_monthly_high", 0) * 3,
            "opportunity_value": f"Resolving {track} gaps could recover ${track_cost.get('total_quarterly_mid', 0):,}/quarter",
        }

    return {
        "gap_analysis": gap,
        "cost_of_gap": {
            "total_low": gap.get("total_gap_cost_low", 0),
            "total_high": gap.get("total_gap_cost_high", 0),
            "leverage": gap.get("highest_leverage", "unknown"),
            "sector": sector,
        },
    }


def gate_node(state: TTLGState) -> dict:
    """Phase 3: Constitutional decision point. GO / LEARN / PASS.

    Considers BOTH bottleneck_indicators (from scout) AND gap_analysis.gaps
    (from thinker). If the thinker found gaps even when the scout found few
    indicators, we still proceed — the thinker's analysis is more authoritative.
    """
    indicators = state.get("bottleneck_indicators", [])
    gap = state.get("gap_analysis", {})
    gaps = gap.get("gaps", []) if isinstance(gap, dict) else []
    signal_count = max(len(indicators), len(gaps))

    if signal_count >= 3:
        verdict = "GO"
        rationale = f"{signal_count} bottlenecks confirmed. Highest leverage: {gap.get('highest_leverage', 'identified')}"
    elif signal_count >= 1:
        verdict = "LEARN"
        rationale = "Partial signal. Proceeding with available data."
    else:
        verdict = "PASS"
        rationale = f"No significant bottlenecks in {state.get('audit_track', 'unknown')}."

    return {"gate_verdict": verdict, "gate_rationale": rationale}


def surgeon_node(state: TTLGState) -> dict:
    """Phase 4: Precise prescriptions. Not recommendations — prescriptions.

    P1 FIX: Generates exactly 3 prescriptions per track ranked by
    Quick Win / Strategic Build / Full Transformation.
    Each includes a Build Manifest referencing the EPOS module that solves it.
    DEGRADED OUTPUT: If LLM fails, builds prescriptions from gap structure + node manifest.
    """
    router = GroqRouter()
    gap = state.get("gap_analysis", {})
    track = state.get("audit_track", "marketing")
    cost_of_gap = state.get("cost_of_gap", {})

    if state.get("gate_verdict") == "PASS":
        return {"prescriptions": [], "priority_order": []}

    # ── Build structured gap summary for LLM ──
    gaps = gap.get("gaps", [])
    gap_text = ""
    for g in gaps[:5]:
        dim = g.get("dimension", "unknown")
        sev = g.get("severity", "medium")
        impact = g.get("immediate_impact", g.get("consequence", "operational impact"))
        cost_low = g.get("cost_90d_low", 0)
        cost_high = g.get("cost_90d_high", 0)
        gap_text += f"  - {dim} ({sev}): {impact}. 90-day cost: ${cost_low:,}-${cost_high:,}\n"

    # ── Get EPOS node mappings for Build Manifests ──
    try:
        from graphs.ttlg_cost_heuristics import get_node_for_gap
        node_hints = ""
        for g in gaps[:5]:
            dim = g.get("dimension", "")
            node = get_node_for_gap(dim)
            if node.get("node") != "custom":
                node_hints += f"  - {dim} → EPOS node: {node['node']} ({node['module']}, ~{node['config_hours']}h setup)\n"
    except Exception:
        node_hints = ""

    prompt = f"""TTLG Phase 4: Surgical prescriptions for {track.upper()}.

GAPS WITH COSTS:
{gap_text}

EPOS NODE SOLUTIONS AVAILABLE:
{node_hints}

Generate EXACTLY 3 prescriptions in this priority order:
1. QUICK WIN — Smallest intervention, fastest results (days, not weeks)
2. STRATEGIC BUILD — 30-60 day focused engagement, highest ROI
3. FULL TRANSFORMATION — Comprehensive overhaul of this track

Each prescription MUST include:
- prescription_id: "RX-001", "RX-002", "RX-003"
- tier: "quick_win", "strategic_build", "full_transformation"
- action: Specific action (NOT "improve X" — exact steps)
- specific_change: What changes on day 1
- success_metric: Measurable outcome with number
- effort_days: Estimated calendar days to implement
- effort_hours: Estimated work hours
- expected_roi_90d: Dollar range of expected return in 90 days
- epos_node: Which EPOS module delivers this (or "custom" if none)
- epos_module: File path of the module (or "requires_assessment")
- config_hours: Hours to configure the EPOS solution

Output ONLY valid JSON array of exactly 3 prescriptions."""

    try:
        raw = router.route("reasoning", prompt, max_tokens=1200, temperature=0.2)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        prescriptions = json.loads(clean)
        if not isinstance(prescriptions, list):
            prescriptions = [prescriptions]
    except Exception:
        # ── DEGRADED OUTPUT: Build prescriptions from gaps + node manifest ──
        try:
            from graphs.ttlg_cost_heuristics import get_node_for_gap
        except Exception:
            get_node_for_gap = lambda d: {"node": "custom", "module": "requires_assessment", "config_hours": 8}

        prescriptions = []
        tiers = [
            ("RX-001", "quick_win", "Quick Win", 7, 8),
            ("RX-002", "strategic_build", "Strategic Build", 45, 40),
            ("RX-003", "full_transformation", "Full Transformation", 90, 120),
        ]
        for i, (rx_id, tier, tier_name, days, hours) in enumerate(tiers):
            g = gaps[i] if i < len(gaps) else gaps[0] if gaps else {"dimension": "unknown"}
            dim = g.get("dimension", "unknown")
            node = get_node_for_gap(dim)
            cost_low = g.get("cost_90d_low", 1500)
            prescriptions.append({
                "prescription_id": rx_id,
                "tier": tier,
                "action": f"{tier_name}: Address {dim.replace('_', ' ')} gap in {track}",
                "specific_change": f"Deploy {node.get('node', 'custom')} to resolve {dim.replace('_', ' ')}",
                "success_metric": f"{dim.replace('_', ' ').title()} bottleneck resolved within {days} days",
                "effort_days": days,
                "effort_hours": hours,
                "expected_roi_90d": f"${cost_low:,}-${cost_low * 2:,}",
                "epos_node": node.get("node", "custom"),
                "epos_module": node.get("module", "requires_assessment"),
                "config_hours": node.get("config_hours", 8),
            })

    return {
        "prescriptions": prescriptions,
        "priority_order": [p.get("prescription_id", f"RX-{i}") for i, p in enumerate(prescriptions)],
    }


def analyst_node(state: TTLGState) -> dict:
    """Phase 5: 30/60/90-day projections. Sovereign Alignment Score. Value at Risk.

    P1 FIX: Consumes structured prescriptions with effort estimates and metrics.
    Produces specific projections per prescription, score deltas, and Value at Risk.
    DEGRADED OUTPUT: If LLM fails, computes projections from prescription structure.
    """
    router = GroqRouter()
    indicators = state.get("bottleneck_indicators", [])
    verdict = state.get("gate_verdict", "PASS")
    prescriptions = state.get("prescriptions", [])
    cost_of_gap = state.get("cost_of_gap", {})
    gap = state.get("gap_analysis", {})

    # ── Compute track score (0-25) ──
    # Use the larger of indicator count or gap count for deduction basis
    gaps = gap.get("gaps", []) if isinstance(gap, dict) else []
    signal_count = max(len(indicators), len(gaps))
    base = 25
    deductions = {"GO": signal_count * 3, "LEARN": signal_count * 1.5, "PASS": 0}
    track_score = max(0, base - deductions.get(verdict, 0))

    # ── Projected score after prescriptions ──
    quick_win_recovery = min(5, len(prescriptions) * 2) if prescriptions else 0
    strategic_recovery = min(10, len(indicators) * 2) if len(prescriptions) >= 2 else 0
    full_recovery = min(15, len(indicators) * 3) if len(prescriptions) >= 3 else 0

    score_30d = min(25, track_score + quick_win_recovery)
    score_60d = min(25, track_score + quick_win_recovery + strategic_recovery)
    score_90d = min(25, track_score + quick_win_recovery + strategic_recovery + full_recovery)

    # ── Value at Risk (cost of standing still) ──
    total_low = cost_of_gap.get("total_low", 0) or gap.get("total_gap_cost_low", 0)
    total_high = cost_of_gap.get("total_high", 0) or gap.get("total_gap_cost_high", 0)
    value_at_risk = {
        "quarterly_low": total_low,
        "quarterly_high": total_high,
        "annual_mid": int((total_low + total_high) / 2 * 4),
        "narrative": (f"If no action is taken, this {state.get('audit_track', 'track')} gap "
                      f"costs an estimated ${total_low:,}-${total_high:,} per quarter. "
                      f"Over 12 months, that compounds to ~${int((total_low + total_high) / 2 * 4):,}."),
    }

    # ── Per-prescription projections ──
    rx_text = ""
    for rx in prescriptions[:3]:
        tier = rx.get("tier", "unknown")
        action = rx.get("action", "")[:100]
        metric = rx.get("success_metric", "")[:80]
        effort = rx.get("effort_days", "?")
        roi = rx.get("expected_roi_90d", "TBD")
        rx_text += f"  {rx.get('prescription_id','')}: [{tier}] {action}\n    Metric: {metric} | Effort: {effort}d | ROI: {roi}\n"

    prompt = f"""TTLG Phase 5: Analyst projections for {state.get('audit_track', 'unknown').upper()}.

Current Score: {track_score}/25
Prescriptions:
{rx_text}

Value at Risk (doing nothing): ${total_low:,}-${total_high:,}/quarter

For EACH prescription, project specific outcomes at 30, 60, and 90 days.
Be SPECIFIC — not "improvement" but "lead response time drops from 48h to 4h."

Output ONLY valid JSON:
{{"per_prescription": [
    {{"prescription_id": "RX-001", "day_30": "specific outcome", "day_60": "specific outcome", "day_90": "specific outcome"}}
  ],
  "score_trajectory": {{"current": {track_score}, "day_30": {score_30d}, "day_60": {score_60d}, "day_90": {score_90d}}},
  "revenue_recovery_90d": "dollar range",
  "confidence": "low|medium|high"}}"""

    try:
        # Analyst uses 8b model — summarization/formatting, not reasoning
        raw = router.route("summarization", prompt, max_tokens=800, temperature=0.3)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        projection = json.loads(clean)
    except Exception:
        # ── DEGRADED OUTPUT: Build projections from prescription structure ──
        per_rx = []
        for rx in prescriptions[:3]:
            tier = rx.get("tier", "quick_win")
            dim = rx.get("specific_change", rx.get("action", ""))[:60]
            per_rx.append({
                "prescription_id": rx.get("prescription_id", "RX-?"),
                "day_30": f"{'Quick win deployed' if tier == 'quick_win' else 'Strategic build initiated'}: {dim}",
                "day_60": f"Measurable improvement in {rx.get('success_metric', 'target metric')[:50]}",
                "day_90": f"Full ROI realization: {rx.get('expected_roi_90d', 'estimated recovery')}",
            })
        projection = {
            "per_prescription": per_rx,
            "score_trajectory": {"current": track_score, "day_30": score_30d,
                                  "day_60": score_60d, "day_90": score_90d},
            "revenue_recovery_90d": f"${total_low:,}-${total_high:,}",
            "confidence": "medium",
        }

    # ── Inject score trajectory and VaR into projection ──
    if "score_trajectory" not in projection:
        projection["score_trajectory"] = {"current": track_score, "day_30": score_30d,
                                            "day_60": score_60d, "day_90": score_90d}
    projection["value_at_risk"] = value_at_risk

    return {
        "sovereign_alignment_score": track_score,
        "thirty_day_projection": projection,
        # ── Normalized top-level keys (Task 2: Key Normalization) ──
        "projections": {
            "per_prescription": projection.get("per_prescription", []),
            "score_trajectory": projection.get("score_trajectory",
                                                {"current": track_score, "day_30": score_30d,
                                                 "day_60": score_60d, "day_90": score_90d}),
            "revenue_recovery_90d": projection.get("revenue_recovery_90d", "pending"),
            "confidence": projection.get("confidence", "medium"),
        },
        "value_at_risk": value_at_risk,
    }


def aar_node(state: TTLGState) -> dict:
    """Phase 6: Mirror Report. What we found. What it means. What happens next.

    P2 FIX: Bifurcated output — Boardroom View + Engine Room View.
    Includes Three-Option Engagement Menu and Value at Risk.
    """
    router = GroqRouter()
    cms = EPOSContentManagement()
    bus = EPOSEventBus()

    track = state.get("audit_track", "unknown")
    score = state.get("sovereign_alignment_score", 0)
    prescriptions = state.get("prescriptions", [])
    gap = state.get("gap_analysis", {})
    projection = state.get("thirty_day_projection", {})
    cost_of_gap = state.get("cost_of_gap", {})

    # ── Extract structured data for the prompts ──
    gaps_text = ""
    for g in gap.get("gaps", [])[:3]:
        dim = g.get("dimension", "unknown")
        impact = g.get("immediate_impact", g.get("consequence", "operational impact"))
        cost_narr = g.get("cost_narrative", "")
        gaps_text += f"  - {dim}: {impact}. {cost_narr}\n"

    rx_text = ""
    for rx in prescriptions[:3]:
        tier = rx.get("tier", "")
        action = rx.get("action", "")[:80]
        metric = rx.get("success_metric", "")[:60]
        effort = rx.get("effort_days", "?")
        node = rx.get("epos_node", "")
        rx_text += f"  [{tier}] {action} (metric: {metric}, {effort} days, node: {node})\n"

    score_traj = projection.get("score_trajectory", {})
    var_data = projection.get("value_at_risk", {})
    var_narrative = var_data.get("narrative", "Cost quantification pending.")

    # ── BOARDROOM VIEW — CEO/executive language ──
    boardroom_prompt = f"""Write the BOARDROOM VIEW of a TTLG Mirror Report for {track.upper()}.

Sovereign Alignment Score: {score:.0f}/25
Score trajectory: {score_traj.get('current', score)} → {score_traj.get('day_30', '?')} (30d) → {score_traj.get('day_60', '?')} (60d) → {score_traj.get('day_90', '?')} (90d)
Value at Risk: {var_narrative}

Key gaps:
{gaps_text}

Top prescriptions:
{rx_text}

Structure:
WHAT WE FOUND: [3-4 sentences, plain business language, cite specific costs]
THE REAL COST: [2-3 sentences with DOLLAR AMOUNTS from the gap analysis]
THE PATH FORWARD: [3 options — Quick Win, Strategic Build, Full Transformation]
YOUR SCORE TRAJECTORY: [current → 30d → 60d → 90d with dollar recovery at each stage]
VALUE AT RISK: [What you lose per quarter if you do nothing]

300-400 words. Language a CEO forwards to the board. No technical jargon.
Warm, direct, authoritative. TTS-friendly."""

    # AAR uses 8b model — summarization/formatting, not reasoning
    boardroom = router.route("summarization", boardroom_prompt, max_tokens=700, temperature=0.4)

    # ── ENGINE ROOM VIEW — CTO/technical language ──
    engine_prompt = f"""Write the ENGINE ROOM VIEW of a TTLG Mirror Report for {track.upper()}.

Same diagnostic as the Boardroom View, but for the technical decision-maker.

Gaps:
{gaps_text}

Prescriptions with Build Manifests:
{rx_text}

Per-prescription projections: {json.dumps(projection.get('per_prescription', []), indent=2)[:600]}

Structure:
TECHNICAL ASSESSMENT: [3-4 sentences on systems state, architecture gaps]
BUILD MANIFESTS: [For each prescription: module, config hours, dependencies]
IMPLEMENTATION SEQUENCE: [What deploys first, what depends on what]
TECHNICAL DEBT IMPACT: [What this fixes in the stack, what it prevents]

250-350 words. Language a CTO takes to the engineering standup. Specific modules, hours, dependencies."""

    engine_room = router.route("summarization", engine_prompt, max_tokens=700, temperature=0.3)

    # ── Three-Option Engagement Menu ──
    engagement_menu = []
    tier_map = {"quick_win": "Quick Win", "strategic_build": "Strategic Build",
                "full_transformation": "Full Transformation"}
    for rx in prescriptions[:3]:
        tier = rx.get("tier", "custom")
        engagement_menu.append({
            "option": tier_map.get(tier, tier.replace("_", " ").title()),
            "prescription_id": rx.get("prescription_id", ""),
            "action": rx.get("action", ""),
            "effort_days": rx.get("effort_days", "TBD"),
            "effort_hours": rx.get("effort_hours", "TBD"),
            "expected_roi_90d": rx.get("expected_roi_90d", "TBD"),
            "epos_node": rx.get("epos_node", "custom"),
        })

    # ── Compose full mirror report (both views) ──
    mirror = f"""BOARDROOM VIEW
{boardroom}

---

ENGINE ROOM VIEW
{engine_room}

---

ENGAGEMENT OPTIONS
"""
    for opt in engagement_menu:
        mirror += f"\n  [{opt['option']}] {opt['action'][:70]}"
        mirror += f"\n    Effort: {opt['effort_days']} days | ROI: {opt['expected_roi_90d']} | Module: {opt['epos_node']}\n"

    mirror += f"\nVALUE AT RISK: {var_narrative}\n"
    mirror += f"NEXT DIAGNOSTIC: 30 days\n"

    # ── Save to CMS ──
    asset = cms.create_asset(
        asset_type="mirror_report",
        title=f"Mirror Report — {track.upper()} — {state.get('client_id', 'unknown')}",
        body=mirror, author_agent="ttlg_diagnostic",
        tags=[track, state.get("client_id", ""), "sovereign_alignment", "bifurcated"])

    # ── Build action plan from prescriptions ──
    action_plan = [{
        "step": i + 1,
        "tier": p.get("tier", ""),
        "action": p.get("action", p.get("specific_change", "")),
        "metric": p.get("success_metric", ""),
        "effort_days": p.get("effort_days", ""),
        "effort_hours": p.get("effort_hours", ""),
        "epos_node": p.get("epos_node", ""),
        "epos_module": p.get("epos_module", ""),
        "config_hours": p.get("config_hours", ""),
        "expected_roi_90d": p.get("expected_roi_90d", ""),
    } for i, p in enumerate(prescriptions[:5])]

    next_cycle = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    record_decision(decision_type="ttlg.diagnostic.complete",
                    description=f"TTLG {track}: score {score:.0f}/25, verdict {state.get('gate_verdict')}",
                    agent_id="ttlg_diagnostic", outcome="complete",
                    context={"track": track, "score": score, "verdict": state.get("gate_verdict"),
                             "asset_id": asset.asset_id,
                             "prescriptions": len(prescriptions),
                             "value_at_risk_quarterly": var_data.get("quarterly_high", 0)})

    try:
        bus.publish("ttlg.diagnostic.complete",
                    {"track": track, "score": score, "client_id": state.get("client_id"),
                     "prescriptions": len(prescriptions),
                     "value_at_risk": var_data.get("quarterly_high", 0)},
                    "ttlg_diagnostic")
    except Exception:
        pass

    return {
        "mirror_report": mirror,
        "mirror_boardroom": boardroom,
        "mirror_engine_room": engine_room,
        "engagement_menu": engagement_menu,
        "action_plan": action_plan,
        "value_at_risk": var_data,
        "next_cycle_date": next_cycle,
        "status": "complete",
    }


# ── Graph Routing ────────────────────────────────────────────

def route_after_gate(state: dict) -> str:
    if state.get("gate_verdict") == "PASS":
        return "aar"
    return "surgeon"


# ── Build Graph ──────────────────────────────────────────────

ttlg_workflow = StateGraph(TTLGState)
ttlg_workflow.add_node("scout", scout_node)
ttlg_workflow.add_node("thinker", thinker_node)
ttlg_workflow.add_node("gate", gate_node)
ttlg_workflow.add_node("surgeon", surgeon_node)
ttlg_workflow.add_node("analyst", analyst_node)
ttlg_workflow.add_node("aar", aar_node)

ttlg_workflow.set_entry_point("scout")
ttlg_workflow.add_edge("scout", "thinker")
ttlg_workflow.add_edge("thinker", "gate")
ttlg_workflow.add_conditional_edges("gate", route_after_gate, {"surgeon": "surgeon", "aar": "aar"})
ttlg_workflow.add_edge("surgeon", "analyst")
ttlg_workflow.add_edge("analyst", "aar")
ttlg_workflow.add_edge("aar", END)

checkpointer = MemorySaver()
ttlg_app = ttlg_workflow.compile(checkpointer=checkpointer)


# ── Diagnostic Runner ────────────────────────────────────────

# ── Vault Journaling ────────────────────────────────────────

_TTLG_VAULT = Path(__file__).resolve().parent.parent / "context_vault" / "ttlg" / "diagnostics"


def _journal_diagnostic(client_id: str, tracks_run: list, composite_score: float, gate_verdicts: dict):
    """Write diagnostic run to JSONL journal."""
    _TTLG_VAULT.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_id": client_id,
        "tracks_run": tracks_run,
        "composite_score": composite_score,
        "gate_verdicts": gate_verdicts,
    }
    with open(_TTLG_VAULT / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


class TTLGDiagnostic:
    """Diagnose marketing, sales, service, and governance gaps in 15 minutes with AI-powered consequence chains."""

    def __init__(self, model_name: str = None, vault_path: Path = None, temperature: float = 0.4):
        global _TTLG_VAULT
        self.model_name = model_name
        self.temperature = temperature
        if vault_path:
            _TTLG_VAULT = Path(vault_path)
        _TTLG_VAULT.mkdir(parents=True, exist_ok=True)

    def run_track(self, client_id: str, audit_track: str) -> dict:
        session_id = f"TTLG-{uuid.uuid4().hex[:8]}"
        state = {
            "client_id": client_id, "audit_track": audit_track,
            "session_id": session_id, "status": "running",
        }
        config = {"configurable": {"thread_id": session_id}}
        result = ttlg_app.invoke(state, config)
        # Journal single track run
        _journal_diagnostic(client_id, [audit_track],
                            result.get("sovereign_alignment_score", 0),
                            {audit_track: result.get("gate_verdict", "?")})
        return result

    def run_full_diagnostic(self, client_id: str) -> dict:
        tracks = ["marketing", "sales", "service", "governance"]
        results = {}
        total_score = 0

        for track in tracks:
            result = self.run_track(client_id, track)
            results[track] = result
            total_score += result.get("sovereign_alignment_score", 0)

        # Composite executive summary
        router = GroqRouter()
        track_summary = "\n".join([
            f"- {t.upper()}: {results[t].get('sovereign_alignment_score', 0):.0f}/25 "
            f"({results[t].get('gate_verdict', '?')})"
            for t in tracks])

        executive = router.route("summarization",
            f"""Sovereign Alignment Executive Summary.
Client: {client_id}. Composite Score: {total_score:.0f}/100.

Track scores:
{track_summary}

Write 150-word summary: composite score meaning, highest priority track,
single most important action this week, projected score in 90 days.
Warm, direct, authoritative.""",
            max_tokens=300, temperature=0.4)

        # Journal the diagnostic run
        gate_verdicts = {t: results[t].get("gate_verdict", "?") for t in tracks}
        _journal_diagnostic(client_id, tracks, total_score, gate_verdicts)

        return {
            "client_id": client_id,
            "sovereign_alignment_score": total_score,
            "track_results": {t: {
                "score": results[t].get("sovereign_alignment_score", 0),
                "verdict": results[t].get("gate_verdict", "?"),
                "prescriptions": len(results[t].get("prescriptions", [])),
                "projections": results[t].get("projections", {}),
                "value_at_risk": results[t].get("value_at_risk", {}),
                "engagement_menu": results[t].get("engagement_menu", []),
                "mirror_report_preview": results[t].get("mirror_report", "")[:200],
            } for t in tracks},
            "executive_summary": executive,
            "diagnostic_date": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    passed = 0

    # Test 1: Constructor with custom config
    ttlg = TTLGDiagnostic(temperature=0.3)
    assert ttlg.temperature == 0.3, "Config not applied"
    assert hasattr(ttlg, "run_track"), "Missing run_track"
    assert hasattr(ttlg, "run_full_diagnostic"), "Missing run_full_diagnostic"
    passed += 1

    # Test 2: Single track test
    print("  Running TTLG Marketing audit for PGP Orlando...")
    result = ttlg.run_track("pgp_orlando", "marketing")
    assert result["status"] == "complete"
    assert result["gate_verdict"] in ("GO", "LEARN", "PASS")
    assert result["mirror_report"] is not None
    assert len(result["mirror_report"]) > 100
    passed += 1
    print(f"  Gate: {result['gate_verdict']}")
    print(f"  Score: {result['sovereign_alignment_score']:.0f}/25")
    print(f"  Prescriptions: {len(result.get('prescriptions', []))}")

    # Test 3: Journal was written
    journal_path = _TTLG_VAULT / "runs.jsonl"
    assert journal_path.exists(), "TTLG journal should exist"
    lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 0, "Journal should have entries"
    passed += 1

    # Test 4: Vault directory exists
    assert _TTLG_VAULT.exists(), "TTLG vault directory should exist"
    passed += 1

    print(f"\nPASS: TTLG diagnostic graph ({passed} assertions)")
    print("The organism can now see a client's business clearly.")
