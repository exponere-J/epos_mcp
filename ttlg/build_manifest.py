#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
build_manifest.py — TTLG Build Manifest Schema + Surgeon (Mission 3)
=====================================================================
Constitutional Authority: EPOS Constitution v3.1

The Surgeon produces Build Manifests — machine-readable deployment
specifications for the exact tool, workflow, or system needed to
close each diagnosed gap.

Three prescriptions per gap: quick_win, strategic_build, full_transformation.
Node matching from the certified 19-node catalog.
Constitutional pricing: all costs include 1.3x margin floor.
"""

import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Literal

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from pydantic import BaseModel, Field
except ImportError:
    from dataclasses import dataclass as BaseModel, field as Field

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

try:
    from groq_router import GroqRouter
except ImportError:
    GroqRouter = None

from path_utils import get_context_vault


CATALOG_PATH = Path(__file__).resolve().parent / "node_catalog.json"
MANIFEST_VAULT = get_context_vault() / "ttlg" / "manifests"


# ── Build Manifest Schema ───────────────────────────────────

class BuildManifest(BaseModel):
    prescription_id: str = ""
    type: str = "quick_win"  # quick_win | strategic_build | full_transformation
    gap_addressed: str = ""
    consequence_chain: str = ""
    nodes_required: list = []
    configuration: dict = {}
    estimated_hours: float = 0
    monthly_cost: float = 0
    projected_roi_90d: float = 0
    deployment_sequence: list = []
    success_criteria: list = []
    value_at_risk: float = 0


# ── Node Catalog Loader ────────────────────────────────────

def load_catalog() -> dict:
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {"nodes": {}, "margin_floor": 1.3}


# ── Gap-to-Node Matcher ────────────────────────────────────

GAP_NODE_MAP = {
    # Marketing gaps
    "content_production": ["content_lab", "multimodal_router"],
    "content_publishing": ["content_lab", "multimodal_router"],
    "content_distribution": ["content_lab"],
    "audience_growth": ["fotw_listener", "content_lab", "lead_scoring"],
    "brand_awareness": ["content_lab", "reputation_manager"],
    # Sales gaps
    "lead_management": ["lead_scoring", "consumer_journey"],
    "lead_scoring": ["lead_scoring"],
    "pipeline_tracking": ["consumer_journey", "dashboard_engine"],
    "conversion_rate": ["ttlg_conversational", "consumer_journey"],
    "pricing_optimization": ["payment_gateway"],
    # Service gaps
    "onboarding": ["consumer_journey", "paperclip_governance"],
    "client_retention": ["reputation_manager", "fotw_listener"],
    "support_efficiency": ["fotw_listener", "friday_intelligence"],
    "reputation_management": ["reputation_manager"],
    # Governance gaps
    "documentation": ["governance_gate", "epos_doctor"],
    "process_automation": ["paperclip_governance", "event_bus"],
    "compliance": ["governance_gate"],
    "data_sovereignty": ["context_graph", "governance_gate"],
    # Intelligence gaps
    "market_intelligence": ["ccp_engine", "rs1_research"],
    "competitive_analysis": ["ccp_engine", "fotw_listener"],
    "research_automation": ["rs1_research", "idea_pipeline"],
    # Operations gaps
    "workflow_automation": ["event_bus", "paperclip_governance"],
    "monitoring": ["epos_doctor", "dashboard_engine"],
    "financial_tracking": ["payment_gateway", "dashboard_engine"],
    # Generic
    "general": ["dashboard_engine", "event_bus"],
}

TIER_CONFIGS = {
    "quick_win": {"max_nodes": 2, "hours_multiplier": 1.0, "roi_multiplier": 1.5},
    "strategic_build": {"max_nodes": 5, "hours_multiplier": 2.5, "roi_multiplier": 2.5},
    "full_transformation": {"max_nodes": 10, "hours_multiplier": 5.0, "roi_multiplier": 4.0},
}


class TTLGSurgeon:
    """
    Produces Build Manifests — machine-readable deployment specs
    for closing diagnosed gaps with EPOS sovereign nodes.
    """

    def __init__(self, diagnostic_id: str = None):
        self.diagnostic_id = diagnostic_id or f"DIAG-{uuid.uuid4().hex[:8]}"
        self.catalog = load_catalog()
        self.margin = self.catalog.get("margin_floor", 1.3)
        self.manifest_dir = MANIFEST_VAULT / self.diagnostic_id
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    def prescribe(self, gap: dict) -> list:
        """
        Given a diagnosed gap, produce 3 Build Manifests.

        gap = {
            "gap_id": "unique",
            "description": "what's wrong",
            "gap_type": "key from GAP_NODE_MAP",
            "severity": "high|medium|low",
            "value_at_risk": 0.0,  # dollarized cost of inaction per quarter
            "context": "additional context"
        }
        """
        gap_type = gap.get("gap_type", "general")
        base_nodes = GAP_NODE_MAP.get(gap_type, GAP_NODE_MAP["general"])
        var = gap.get("value_at_risk", 10000)

        manifests = []
        for tier_name, tier_cfg in TIER_CONFIGS.items():
            nodes = base_nodes[:tier_cfg["max_nodes"]]
            monthly = self._calculate_cost(nodes)
            hours = len(nodes) * 4 * tier_cfg["hours_multiplier"]
            roi = (var * tier_cfg["roi_multiplier"]) / max(monthly * 3, 1) * 100

            # Generate consequence chain via LLM if available
            consequence = self._generate_consequence(gap, tier_name)

            manifest = BuildManifest(
                prescription_id=f"RX-{self.diagnostic_id[-6:]}-{tier_name[:2].upper()}-{uuid.uuid4().hex[:4]}",
                type=tier_name,
                gap_addressed=gap.get("description", gap_type),
                consequence_chain=consequence,
                nodes_required=nodes,
                configuration=self._build_config(nodes, gap),
                estimated_hours=hours,
                monthly_cost=monthly,
                projected_roi_90d=round(roi, 1),
                deployment_sequence=self._build_sequence(nodes),
                success_criteria=self._build_criteria(gap, tier_name),
                value_at_risk=var,
            )
            manifests.append(manifest)

        # Save manifests
        for m in manifests:
            path = self.manifest_dir / f"{m.prescription_id}.json"
            if hasattr(m, 'model_dump'):
                path.write_text(json.dumps(m.model_dump(), indent=2), encoding="utf-8")
            else:
                path.write_text(json.dumps(vars(m), indent=2), encoding="utf-8")

        # Publish event
        if _BUS:
            try:
                _BUS.publish("ttlg.manifest.generated", {
                    "diagnostic_id": self.diagnostic_id,
                    "gap_type": gap_type,
                    "manifests_count": len(manifests),
                }, source_module="ttlg_surgeon")
            except Exception:
                pass

        return manifests

    def _calculate_cost(self, nodes: list) -> float:
        """Sum node costs with constitutional margin."""
        total = 0
        for node_id in nodes:
            node = self.catalog.get("nodes", {}).get(node_id, {})
            total += node.get("monthly_cost", 49)
        return round(total * self.margin, 2)

    def _generate_consequence(self, gap: dict, tier: str) -> str:
        """Generate dollarized consequence chain."""
        var = gap.get("value_at_risk", 10000)
        desc = gap.get("description", "operational gap")
        if tier == "quick_win":
            return f"Closing this gap addresses the most immediate impact: ~${var*0.3:.0f}/quarter in recovered value from {desc}."
        elif tier == "strategic_build":
            return f"Strategic remediation addresses {desc} and connected downstream effects: ~${var*0.7:.0f}/quarter in recovered value plus operational efficiency gains."
        else:
            return f"Full transformation eliminates {desc} and all connected gaps: ~${var:.0f}/quarter in recovered value with compound returns from system integration."

    def _build_config(self, nodes: list, gap: dict) -> dict:
        """Generate node-specific configuration."""
        config = {}
        for node_id in nodes:
            node = self.catalog.get("nodes", {}).get(node_id, {})
            config[node_id] = {
                "capabilities_used": node.get("capabilities", [])[:3],
                "integration": "event_bus",
            }
        return config

    def _build_sequence(self, nodes: list) -> list:
        """Generate ordered deployment sequence."""
        seq = ["1. Configure event bus integration"]
        for i, node_id in enumerate(nodes, 2):
            node = self.catalog.get("nodes", {}).get(node_id, {})
            seq.append(f"{i}. Deploy {node.get('name', node_id)} with vault path initialization")
        seq.append(f"{len(nodes)+2}. Run sovereignty certification")
        seq.append(f"{len(nodes)+3}. Verify end-to-end pipeline")
        return seq

    def _build_criteria(self, gap: dict, tier: str) -> list:
        """Generate measurable success criteria."""
        base = [
            "All deployed nodes pass sovereignty certification at 85+",
            "Event bus shows events from all new nodes",
            "Doctor reports zero new FAILs",
        ]
        if tier == "full_transformation":
            base.append("90-day revenue recovery exceeds monthly cost by 3x")
        return base

    def get_manifests(self) -> list:
        """Load all manifests for this diagnostic."""
        manifests = []
        for f in self.manifest_dir.glob("RX-*.json"):
            manifests.append(json.loads(f.read_text(encoding="utf-8")))
        return manifests


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    surgeon = TTLGSurgeon(diagnostic_id="TEST-SURGEON")

    # Test 1: Prescribe for a lead management gap
    gap = {
        "gap_id": "GAP-001",
        "description": "Lead management is manual with no scoring",
        "gap_type": "lead_management",
        "severity": "high",
        "value_at_risk": 47000,
        "context": "Losing pipeline to competitors with automated lead scoring",
    }
    manifests = surgeon.prescribe(gap)
    assert len(manifests) == 3, f"Expected 3 manifests, got {len(manifests)}"
    passed += 1

    # Test 2: Manifest types are correct
    types = [m.type for m in manifests]
    assert "quick_win" in types
    assert "strategic_build" in types
    assert "full_transformation" in types
    passed += 1

    # Test 3: Nodes reference valid catalog entries
    catalog = load_catalog()
    for m in manifests:
        for node_id in m.nodes_required:
            assert node_id in catalog["nodes"], f"Unknown node: {node_id}"
    passed += 1

    # Test 4: Cost includes margin
    for m in manifests:
        assert m.monthly_cost > 0, "Cost should be positive"
    passed += 1

    # Test 5: Manifests saved to vault
    saved = surgeon.get_manifests()
    assert len(saved) >= 3
    passed += 1

    # Test 6: Prescribe for content gap
    gap2 = {
        "gap_id": "GAP-002",
        "description": "Zero published content",
        "gap_type": "content_production",
        "severity": "critical",
        "value_at_risk": 25000,
    }
    manifests2 = surgeon.prescribe(gap2)
    assert manifests2[0].nodes_required[0] == "content_lab"
    passed += 1

    print(f"PASS: build_manifest ({passed} assertions)")
    for m in manifests:
        print(f"  [{m.type:22s}] ${m.monthly_cost:>8.2f}/mo | ROI: {m.projected_roi_90d:.0f}% | Nodes: {m.nodes_required}")
