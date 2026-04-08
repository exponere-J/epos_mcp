#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
ttlg_cost_heuristics.py — Sector-Specific Cost Model Library
=============================================================
Constitutional Authority: EPOS Constitution v3.1
Module: TTLG P2 Fix — Cost Quantification

Provides defensible cost ranges for common business gaps by sector.
Not precise — defensible. "This gap costs you approximately $X-$Y/quarter."

Three launch sectors:
  1. tech_saas      — SaaS / technology companies
  2. prof_services  — Professional services, consulting, agencies
  3. local_service  — Local service businesses (property mgmt, trades, retail)

Usage:
  from graphs.ttlg_cost_heuristics import estimate_gap_cost
  cost = estimate_gap_cost("lead_response_time", "high", "tech_saas", headcount=15)
"""

# ── Cost Models by Dimension and Sector ──────────────────────────

# Structure: dimension → sector → { base_monthly, severity_multiplier, headcount_factor }
# Monthly cost = base_monthly × severity_mult × (1 + headcount_factor × headcount/10)

COST_MODELS = {
    # ── MARKETING DIMENSIONS ──────────────────────────────
    "content_output": {
        "tech_saas": {"base_monthly": 3000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.15},
        "prof_services": {"base_monthly": 2000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.10},
        "local_service": {"base_monthly": 800, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.08},
    },
    "platform_presence": {
        "tech_saas": {"base_monthly": 2500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.10},
        "prof_services": {"base_monthly": 1500, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.08},
        "local_service": {"base_monthly": 600, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.05},
    },
    "content_quality": {
        "tech_saas": {"base_monthly": 4000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.12},
        "prof_services": {"base_monthly": 2500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.10},
        "local_service": {"base_monthly": 1000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.06},
    },
    "lead_generation": {
        "tech_saas": {"base_monthly": 8000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.2}, "headcount_factor": 0.20},
        "prof_services": {"base_monthly": 5000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.15},
        "local_service": {"base_monthly": 2000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.10},
    },
    "brand_consistency": {
        "tech_saas": {"base_monthly": 2000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.08},
        "prof_services": {"base_monthly": 1500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.06},
        "local_service": {"base_monthly": 500, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.04},
    },

    # ── SALES DIMENSIONS ─────────────────────────────────
    "lead_response_time": {
        "tech_saas": {"base_monthly": 6000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.5}, "headcount_factor": 0.25},
        "prof_services": {"base_monthly": 4000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.20},
        "local_service": {"base_monthly": 1500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.12},
    },
    "follow_up_consistency": {
        "tech_saas": {"base_monthly": 5000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.18},
        "prof_services": {"base_monthly": 3500, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.15},
        "local_service": {"base_monthly": 1200, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.10},
    },
    "proposal_process": {
        "tech_saas": {"base_monthly": 3000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.12},
        "prof_services": {"base_monthly": 2500, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.10},
        "local_service": {"base_monthly": 800, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.06},
    },
    "closing_mechanism": {
        "tech_saas": {"base_monthly": 7000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.2}, "headcount_factor": 0.22},
        "prof_services": {"base_monthly": 4500, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.18},
        "local_service": {"base_monthly": 1800, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.12},
    },
    "pipeline_visibility": {
        "tech_saas": {"base_monthly": 4000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.15},
        "prof_services": {"base_monthly": 3000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.12},
        "local_service": {"base_monthly": 1000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.08},
    },

    # ── SERVICE DIMENSIONS ────────────────────────────────
    "onboarding_process": {
        "tech_saas": {"base_monthly": 3500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.15},
        "prof_services": {"base_monthly": 2000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.12},
        "local_service": {"base_monthly": 800, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.08},
    },
    "delivery_consistency": {
        "tech_saas": {"base_monthly": 5000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.18},
        "prof_services": {"base_monthly": 3500, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.15},
        "local_service": {"base_monthly": 1500, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.10},
    },
    "communication": {
        "tech_saas": {"base_monthly": 2000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.10},
        "prof_services": {"base_monthly": 1500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.08},
        "local_service": {"base_monthly": 600, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.05},
    },
    "quality_control": {
        "tech_saas": {"base_monthly": 6000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.5}, "headcount_factor": 0.20},
        "prof_services": {"base_monthly": 3000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.15},
        "local_service": {"base_monthly": 1200, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.10},
    },
    "satisfaction_measurement": {
        "tech_saas": {"base_monthly": 2500, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.10},
        "prof_services": {"base_monthly": 1800, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.08},
        "local_service": {"base_monthly": 500, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.05},
    },

    # ── GOVERNANCE DIMENSIONS ─────────────────────────────
    "data_sovereignty": {
        "tech_saas": {"base_monthly": 5000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 3.0}, "headcount_factor": 0.20},
        "prof_services": {"base_monthly": 2500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.5}, "headcount_factor": 0.15},
        "local_service": {"base_monthly": 800, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.08},
    },
    "saas_dependency": {
        "tech_saas": {"base_monthly": 4000, "severity_mult": {"low": 0.5, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.18},
        "prof_services": {"base_monthly": 2000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.8}, "headcount_factor": 0.12},
        "local_service": {"base_monthly": 1000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.08},
    },
    "automation_reliability": {
        "tech_saas": {"base_monthly": 3500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 2.0}, "headcount_factor": 0.15},
        "prof_services": {"base_monthly": 2000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.10},
        "local_service": {"base_monthly": 600, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.05},
    },
    "documentation_sops": {
        "tech_saas": {"base_monthly": 2000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.12},
        "prof_services": {"base_monthly": 1500, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 1.6}, "headcount_factor": 0.10},
        "local_service": {"base_monthly": 400, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 1.5}, "headcount_factor": 0.06},
    },
    "backup_continuity": {
        "tech_saas": {"base_monthly": 8000, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 5.0}, "headcount_factor": 0.25},
        "prof_services": {"base_monthly": 3000, "severity_mult": {"low": 0.4, "medium": 1.0, "high": 3.0}, "headcount_factor": 0.15},
        "local_service": {"base_monthly": 1500, "severity_mult": {"low": 0.3, "medium": 1.0, "high": 2.5}, "headcount_factor": 0.10},
    },
}

# ── EPOS Node Mapping (which module solves which gap) ────────────

NODE_MANIFEST = {
    "content_output": {"node": "content_lab", "module": "content/lab/content_lab_core.py", "config_hours": 8},
    "platform_presence": {"node": "content_lab", "module": "content/lab/nodes/m1_marshall.py", "config_hours": 4},
    "content_quality": {"node": "content_lab", "module": "content/lab/nodes/v1_validation_engine.py", "config_hours": 6},
    "lead_generation": {"node": "lead_scoring", "module": "lead_scoring.py", "config_hours": 4},
    "brand_consistency": {"node": "governance_gate", "module": "content/lab/validation/brand_validator.py", "config_hours": 3},
    "lead_response_time": {"node": "friday_intelligence", "module": "friday_intelligence.py", "config_hours": 4},
    "follow_up_consistency": {"node": "consumer_journey", "module": "graphs/consumer_journey_graph.py", "config_hours": 8},
    "proposal_process": {"node": "content_lab", "module": "content_lab_producer.py", "config_hours": 6},
    "closing_mechanism": {"node": "consumer_journey", "module": "graphs/consumer_journey_graph.py", "config_hours": 8},
    "pipeline_visibility": {"node": "lead_scoring", "module": "lead_scoring.py", "config_hours": 4},
    "onboarding_process": {"node": "consumer_journey", "module": "graphs/consumer_journey_graph.py", "config_hours": 10},
    "delivery_consistency": {"node": "ttlg_diagnostic", "module": "graphs/ttlg_diagnostic_graph.py", "config_hours": 6},
    "communication": {"node": "friday_intelligence", "module": "friday_intelligence.py", "config_hours": 4},
    "quality_control": {"node": "epos_doctor", "module": "engine/epos_doctor.py", "config_hours": 4},
    "satisfaction_measurement": {"node": "ttlg_diagnostic", "module": "graphs/ttlg_diagnostic_graph.py", "config_hours": 6},
    "data_sovereignty": {"node": "governance_gate", "module": "engine/enforcement/governance_gate.py", "config_hours": 8},
    "saas_dependency": {"node": "event_bus", "module": "epos_event_bus.py", "config_hours": 6},
    "automation_reliability": {"node": "epos_doctor", "module": "engine/epos_doctor.py", "config_hours": 4},
    "documentation_sops": {"node": "governance_gate", "module": "engine/enforcement/governance_gate.py", "config_hours": 6},
    "backup_continuity": {"node": "epos_doctor", "module": "engine/epos_doctor.py", "config_hours": 4},
}


# ── Public API ───────────────────────────────────────────────────

def estimate_gap_cost(dimension: str, severity: str, sector: str = "prof_services",
                      headcount: int = 10) -> dict:
    """Estimate monthly cost of a gap. Returns range and narrative."""
    dim_key = dimension.lower().replace(" ", "_")
    model = COST_MODELS.get(dim_key, {}).get(sector)

    if not model:
        # Fallback: use prof_services or a default
        model = COST_MODELS.get(dim_key, {}).get("prof_services")
    if not model:
        return {"monthly_low": 500, "monthly_high": 2000, "quarterly_mid": 3750,
                "narrative": f"Estimated cost range for {dimension} gap: $500-$2,000/month.",
                "confidence": "low"}

    sev = severity.lower() if severity else "medium"
    mult = model["severity_mult"].get(sev, 1.0)
    hc_factor = 1 + model["headcount_factor"] * (headcount / 10)
    base = model["base_monthly"] * mult * hc_factor

    monthly_low = int(base * 0.7)
    monthly_high = int(base * 1.4)
    quarterly_mid = int(base * 3)

    narrative = (
        f"{dimension.replace('_', ' ').title()} gap ({severity} severity) "
        f"costs approximately ${monthly_low:,}-${monthly_high:,}/month "
        f"(~${quarterly_mid:,}/quarter) for a {sector.replace('_', ' ')} "
        f"business with ~{headcount} employees."
    )

    return {
        "monthly_low": monthly_low,
        "monthly_high": monthly_high,
        "quarterly_mid": quarterly_mid,
        "narrative": narrative,
        "confidence": "high" if sev in ("medium", "high") else "medium",
    }


def get_node_for_gap(dimension: str) -> dict:
    """Get the EPOS node that solves a specific gap."""
    dim_key = dimension.lower().replace(" ", "_")
    return NODE_MANIFEST.get(dim_key, {
        "node": "custom", "module": "requires_assessment", "config_hours": 8
    })


def estimate_total_track_cost(indicators: list, sector: str = "prof_services",
                               headcount: int = 10) -> dict:
    """Estimate total track cost from a list of bottleneck indicators."""
    total_low = 0
    total_high = 0
    gap_costs = []

    for ind in indicators:
        dim = ind.get("dimension", "") if isinstance(ind, dict) else str(ind)
        sev = ind.get("severity", "medium") if isinstance(ind, dict) else "medium"
        cost = estimate_gap_cost(dim, sev, sector, headcount)
        total_low += cost["monthly_low"]
        total_high += cost["monthly_high"]
        gap_costs.append({"dimension": dim, "severity": sev, **cost})

    return {
        "total_monthly_low": total_low,
        "total_monthly_high": total_high,
        "total_quarterly_mid": int((total_low + total_high) / 2 * 3),
        "gap_costs": gap_costs,
    }
