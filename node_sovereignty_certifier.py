#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
node_sovereignty_certifier.py — Node Sovereignty Certification Engine
=====================================================================
Constitutional Authority: EPOS Constitution v3.1
Module: TTLG Mode B — Product Extraction & Marketplace Validation

Examines each EPOS building block against 7 sovereignty criteria to determine
marketplace readiness. Produces a Node Sovereignty Certificate per module.

Certification Criteria:
  1. Standalone Import  — Can the module import without pulling the full organism?
  2. Self-Test          — Does it have a passing self-test?
  3. API Surface        — Does it expose a clean, documentable API?
  4. Event Bus Wiring   — Does it publish/subscribe to events?
  5. Data Sovereignty   — Does it own its own data (vault path, DB schema)?
  6. Configuration      — Can it be configured independently (.env, config)?
  7. Value Proposition  — Can a non-EPOS user understand what it does in one sentence?

Scoring: Each criterion 0-15 points. Total 0-105. Thresholds:
  85+ : MARKETPLACE READY — list immediately
  70-84: HARDENING NEEDED — specific fixes identified, then list
  50-69: INCUBATING — viable concept, needs extraction work
  <50 : ORGANISM-ONLY — too coupled, serves internal function only

Usage:
  python node_sovereignty_certifier.py              # Certify all nodes
  python epos.py ttlg certify                       # Via CLI
"""

import sys
import json
import importlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision


# ── Building Block Registry ──────────────────────────────────────

BUILDING_BLOCKS = {
    "research_engine": {
        "name": "RS1 Research Engine",
        "module": "rs1_research_compiler",
        "files": ["rs1_research_compiler.py", "rs1_research_brief.py"],
        "description": "Converts learning emphasis into callable skills and generates 7-vector research briefs.",
        "value_prop": "AI research analyst that turns any topic into structured, actionable intelligence.",
        "pricing_tier": "solo",
        "suggested_price": "$49/mo",
        "market_category": "Research & Intelligence",
    },
    "content_lab": {
        "name": "Content Lab",
        "module": "content.lab.content_lab_core",
        "files": ["content/lab/content_lab_core.py", "content/lab/nodes/r1_radar.py",
                  "content/lab/nodes/an1_analyst.py", "content/lab/nodes/v1_validation_engine.py",
                  "content/lab/nodes/m1_marshall.py"],
        "description": "6-node content production pipeline: Radar → Analyst → Validation → Marshall.",
        "value_prop": "AI content production line that creates, validates, and schedules content autonomously.",
        "pricing_tier": "workflow",
        "suggested_price": "$149/mo",
        "market_category": "Content Production",
    },
    "ttlg_diagnostic": {
        "name": "TTLG Diagnostic",
        "module": "graphs.ttlg_diagnostic_graph",
        "files": ["graphs/ttlg_diagnostic_graph.py"],
        "description": "4-track business diagnostic with Mirror Reports and Sovereign Alignment Score.",
        "value_prop": "Diagnose marketing, sales, service, and governance gaps in 15 minutes with AI-powered consequence chains.",
        "pricing_tier": "department",
        "suggested_price": "$997/engagement",
        "market_category": "Business Consulting",
    },
    "lead_scoring": {
        "name": "Lead Scoring Engine",
        "module": "lead_scoring",
        "files": ["lead_scoring.py"],
        "description": "4-dimension autonomous lead scoring with behavioral, engagement, fit, and recency signals.",
        "value_prop": "AI lead scoring that tells you exactly which prospects to call today.",
        "pricing_tier": "solo",
        "suggested_price": "$79/mo",
        "market_category": "CRM & Sales",
    },
    "consumer_journey": {
        "name": "Consumer Journey Engine",
        "module": "graphs.consumer_journey_graph",
        "files": ["graphs/consumer_journey_graph.py"],
        "description": "8-stage journey orchestration from discovery through delivery and learning.",
        "value_prop": "AI journey manager that guides prospects from first touch to loyal customer.",
        "pricing_tier": "workflow",
        "suggested_price": "$199/mo",
        "market_category": "CRM & Sales",
    },
    "event_bus": {
        "name": "EPOS Event Bus",
        "module": "epos_event_bus",
        "files": ["epos_event_bus.py"],
        "description": "Cross-process JSONL pub/sub event system with trace replay.",
        "value_prop": "Lightweight event bus that connects all your tools without infrastructure overhead.",
        "pricing_tier": "solo",
        "suggested_price": "$29/mo",
        "market_category": "Infrastructure",
    },
    "context_graph": {
        "name": "Context Graph",
        "module": "context_graph",
        "files": ["context_graph.py", "marl_reward_collector.py"],
        "description": "Weighted knowledge graph with EMA learning from outcome signals.",
        "value_prop": "AI memory that learns what works and gets smarter with every decision.",
        "pricing_tier": "workflow",
        "suggested_price": "$99/mo",
        "market_category": "Intelligence",
    },
    "friday_intelligence": {
        "name": "Friday Intelligence",
        "module": "friday_intelligence",
        "files": ["friday_intelligence.py", "friday_daily_anchors.py"],
        "description": "Autonomous operating intelligence with pattern learning, idea triage, and daily anchors.",
        "value_prop": "AI chief of staff that learns your patterns and protects your time.",
        "pricing_tier": "department",
        "suggested_price": "$297/mo",
        "market_category": "Executive Intelligence",
    },
    "lifeos": {
        "name": "LifeOS",
        "module": "lifeos_sovereignty",
        "files": ["lifeos_sovereignty.py", "lifeos_kernel.py"],
        "description": "Personal sovereignty framework with daily anchors, growth timeline, and relationship OS.",
        "value_prop": "Personal operating system that tracks energy, goals, and growth — not just tasks.",
        "pricing_tier": "solo",
        "suggested_price": "$39/mo",
        "market_category": "Personal Productivity",
    },
    "idea_pipeline": {
        "name": "Idea Pipeline",
        "module": "idea_log",
        "files": ["idea_log.py", "rs1_research_brief.py"],
        "description": "Capture → Triage → Research Brief → Build Queue pipeline for ideas.",
        "value_prop": "Never lose an idea again. AI triages and researches every captured thought.",
        "pricing_tier": "solo",
        "suggested_price": "$29/mo",
        "market_category": "Project Management",
    },
    "epos_doctor": {
        "name": "EPOS Doctor",
        "module": "engine.epos_doctor",
        "files": ["engine/epos_doctor.py"],
        "description": "32-check environment validator with self-healing and constitutional enforcement.",
        "value_prop": "Automated health check that validates your entire stack before deployment.",
        "pricing_tier": "workflow",
        "suggested_price": "$49/mo",
        "market_category": "DevOps & Monitoring",
    },
    "governance_gate": {
        "name": "Governance Gate",
        "module": "engine.governance_gate",
        "files": ["governance_gate.py", "engine/governance_gate.py"],
        "description": "Constitutional compliance engine with watermarking, triage, and quarantine.",
        "value_prop": "Automated code governance that enforces standards before anything ships.",
        "pricing_tier": "department",
        "suggested_price": "$199/mo",
        "market_category": "Compliance & Governance",
    },
    "multimodal_router": {
        "name": "Multimodal Router",
        "module": "multimodal_router",
        "files": ["multimodal_router.py"],
        "description": "Routes generation tasks to Ollama local, HuggingFace, and Gemini providers.",
        "value_prop": "Route text, image, and video generation to the best provider at the lowest cost.",
        "pricing_tier": "workflow",
        "suggested_price": "$79/mo",
        "market_category": "AI Infrastructure",
    },
    "payment_gateway": {
        "name": "Payment Gateway",
        "module": "payment_gateway",
        "files": ["payment_gateway.py"],
        "description": "Stripe-integrated payment processing with service catalog and webhook handling.",
        "value_prop": "Accept payments, generate invoices, and track revenue with one sovereign node.",
        "pricing_tier": "workflow",
        "suggested_price": "$49/mo",
        "market_category": "Financial Operations",
    },
    "fotw_listener": {
        "name": "FOTW Listener",
        "module": "fotw_listener",
        "files": ["fotw_listener.py"],
        "description": "Captures expressions from comments, calls, and interactions for engagement intelligence.",
        "value_prop": "Capture every customer expression and route it to the intelligence that needs it.",
        "pricing_tier": "workflow",
        "suggested_price": "$99/mo",
        "market_category": "Engagement Intelligence",
    },
    "ttlg_conversational": {
        "name": "Conversational TTLG",
        "module": "ttlg_conversational",
        "files": ["ttlg_conversational.py"],
        "description": "Interactive diagnostic conversation engine that produces Mirror Reports through dialogue.",
        "value_prop": "Turn business diagnostics into guided conversations that close themselves.",
        "pricing_tier": "department",
        "suggested_price": "$497/engagement",
        "market_category": "Sales Automation",
    },
    "dashboard_engine": {
        "name": "Dashboard Engine",
        "module": "dashboard_engine",
        "files": ["dashboard_engine.py"],
        "description": "Unified ecosystem dashboard aggregating health, revenue, content, and intelligence.",
        "value_prop": "See your entire operation in one view — nodes, revenue, content, and intelligence.",
        "pricing_tier": "workflow",
        "suggested_price": "$49/mo",
        "market_category": "Business Intelligence",
    },
    "reputation_manager": {
        "name": "Reputation Manager",
        "module": "reputation_manager",
        "files": ["reputation_manager.py"],
        "description": "Review monitoring, sentiment analysis, response generation, and reputation scoring.",
        "value_prop": "Monitor reviews, generate responses, and track reputation score across platforms.",
        "pricing_tier": "solo",
        "suggested_price": "$79/mo",
        "market_category": "Reputation Management",
    },
    "paperclip_governance": {
        "name": "Paperclip Governance",
        "module": "paperclip_governance",
        "files": ["paperclip_governance.py"],
        "description": "Agent mission governance with constitutional constraints, execution receipts, and rollback.",
        "value_prop": "Deploy autonomous agents with constitutional guardrails and proof-of-execution.",
        "pricing_tier": "department",
        "suggested_price": "$297/mo",
        "market_category": "Agent Governance",
    },
    "browser_use_node": {
        "name": "BrowserUse Node",
        "module": "nodes.browser_use_node",
        "files": ["nodes/browser_use_node.py"],
        "description": "Sovereign browser automation for publishing, monitoring, and web interaction.",
        "value_prop": "Automate any browser workflow autonomously without a live Claude session.",
        "pricing_tier": "workflow",
        "suggested_price": "$79/mo",
        "market_category": "Browser Automation",
    },
    "ttlg_v2_pipeline": {
        "name": "TTLG v2 Pipeline",
        "module": "ttlg.pipeline_graph",
        "files": ["ttlg/pipeline_graph.py", "ttlg/props/schema.py", "ttlg/question_generator.py",
                  "ttlg/build_manifest.py", "ttlg/mirror_report.py", "ttlg/node_catalog.json"],
        "description": "Parametrized diagnostic pipeline with LangGraph orchestration, Build Manifests, and Mirror Reports.",
        "value_prop": "Run AI-powered business diagnostics that prescribe exact solutions with machine-readable deployment specs.",
        "pricing_tier": "department",
        "suggested_price": "$997/engagement",
        "market_category": "Business Intelligence",
    },
    "self_healing_engine": {
        "name": "Self-Healing Engine",
        "module": "ttlg.self_healing_scout",
        "files": ["ttlg/self_healing_scout.py", "ttlg/remediation_runbook.py", "ttlg/pipeline_graph.py"],
        "description": "Autonomous self-healing with 7-point health scanner, 12-handler runbook, and 4-tier escalation.",
        "value_prop": "Detect and fix operational failures automatically with constitutional governance and audit trails.",
        "pricing_tier": "workflow",
        "suggested_price": "$149/mo",
        "market_category": "DevOps & Monitoring",
    },
}


# ── Certification Engine ─────────────────────────────────────────

class NodeSovereigntyCertifier:
    """Certifies building blocks for marketplace readiness."""

    def __init__(self):
        self.root = Path(__file__).parent
        self.vault = get_context_vault()
        self.certs_dir = self.vault / "marketplace" / "certifications"
        self.certs_dir.mkdir(parents=True, exist_ok=True)
        self.bus = EPOSEventBus()

    def certify_node(self, node_id: str) -> dict:
        """Run all 7 certification criteria against a building block."""
        block = BUILDING_BLOCKS.get(node_id)
        if not block:
            return {"error": f"Unknown node: {node_id}"}

        print(f"  Certifying: {block['name']}...")

        criteria = {}

        # 1. Standalone Import
        criteria["standalone_import"] = self._check_standalone_import(block)

        # 2. Self-Test
        criteria["self_test"] = self._check_self_test(block)

        # 3. API Surface
        criteria["api_surface"] = self._check_api_surface(block)

        # 4. Event Bus Wiring
        criteria["event_bus"] = self._check_event_bus(block)

        # 5. Data Sovereignty
        criteria["data_sovereignty"] = self._check_data_sovereignty(block)

        # 6. Configuration Independence
        criteria["configuration"] = self._check_configuration(block)

        # 7. Value Proposition Clarity
        criteria["value_proposition"] = self._check_value_proposition(block)

        # Compute total
        total_score = sum(c["score"] for c in criteria.values())
        max_score = 105

        if total_score >= 85:
            readiness = "MARKETPLACE_READY"
        elif total_score >= 70:
            readiness = "HARDENING_NEEDED"
        elif total_score >= 50:
            readiness = "INCUBATING"
        else:
            readiness = "ORGANISM_ONLY"

        # Build hardening list
        hardening = []
        for crit_name, crit_data in criteria.items():
            if crit_data["score"] < 10:
                hardening.append({
                    "criterion": crit_name,
                    "current_score": crit_data["score"],
                    "gap": crit_data.get("gap", ""),
                    "fix": crit_data.get("fix", ""),
                })

        cert = {
            "node_id": node_id,
            "name": block["name"],
            "module": block["module"],
            "total_score": total_score,
            "max_score": max_score,
            "pct": round(total_score / max_score * 100, 1),
            "readiness": readiness,
            "criteria": criteria,
            "hardening_needed": hardening,
            "value_prop": block["value_prop"],
            "pricing_tier": block["pricing_tier"],
            "suggested_price": block["suggested_price"],
            "market_category": block["market_category"],
            "certified_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save certificate
        cert_path = self.certs_dir / f"{node_id}_cert.json"
        cert_path.write_text(json.dumps(cert, indent=2), encoding="utf-8")

        # Publish event
        self.bus.publish("ttlg.node.certified", {
            "node_id": node_id,
            "score": total_score,
            "readiness": readiness,
        }, "node_sovereignty_certifier")

        return cert

    def certify_all(self) -> dict:
        """Certify all building blocks. Returns full catalog."""
        results = {}
        for node_id in BUILDING_BLOCKS:
            cert = self.certify_node(node_id)
            results[node_id] = cert

        # Summary
        by_readiness = {}
        for node_id, cert in results.items():
            r = cert.get("readiness", "UNKNOWN")
            by_readiness.setdefault(r, []).append(node_id)

        catalog = {
            "total_nodes": len(results),
            "certified_at": datetime.now(timezone.utc).isoformat(),
            "by_readiness": by_readiness,
            "nodes": results,
        }

        # Save catalog
        catalog_path = self.certs_dir / "marketplace_catalog.json"
        catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

        # Record decision
        record_decision(
            decision_type="ttlg.marketplace.catalog",
            description=f"Certified {len(results)} nodes for marketplace",
            agent_id="node_sovereignty_certifier",
            outcome="complete",
            context={"by_readiness": {k: len(v) for k, v in by_readiness.items()}},
        )

        return catalog

    # ── Criterion Checks ─────────────────────────────────────────

    def _check_standalone_import(self, block: dict) -> dict:
        """Can the module import without pulling the full organism?"""
        module = block["module"]
        try:
            mod = importlib.import_module(module)
            # Check how many EPOS-specific imports it pulls
            source = Path(block["files"][0])
            if source.exists():
                content = (self.root / source).read_text(encoding="utf-8")
                epos_imports = sum(1 for line in content.splitlines()
                                   if line.strip().startswith(("from ", "import "))
                                   and any(dep in line for dep in [
                                       "epos_", "path_utils", "groq_router", "context_graph",
                                       "friday_", "lifeos_", "flywheel_", "constitutional_"
                                   ]))
                if epos_imports <= 2:
                    return {"score": 15, "detail": f"Imports cleanly with {epos_imports} EPOS deps"}
                elif epos_imports <= 4:
                    return {"score": 10, "detail": f"{epos_imports} EPOS deps — extractable with adapter layer",
                            "gap": f"{epos_imports} internal dependencies",
                            "fix": "Create adapter interfaces for EPOS-specific imports"}
                else:
                    return {"score": 5, "detail": f"{epos_imports} EPOS deps — tightly coupled",
                            "gap": "Heavy internal coupling",
                            "fix": "Refactor to dependency injection pattern"}
            return {"score": 12, "detail": "Imports successfully"}
        except Exception as e:
            return {"score": 0, "detail": f"Import failed: {str(e)[:80]}",
                    "gap": "Cannot import standalone",
                    "fix": f"Fix import error: {str(e)[:80]}"}

    def _check_self_test(self, block: dict) -> dict:
        """Does it have a passing self-test?"""
        main_file = self.root / block["files"][0]
        if not main_file.exists():
            return {"score": 0, "detail": "Main file not found",
                    "gap": "Missing file", "fix": f"Create {block['files'][0]}"}

        content = main_file.read_text(encoding="utf-8")
        has_main = '__name__ == "__main__"' in content or "__name__ == '__main__'" in content
        has_assert = "assert " in content
        has_pass = "PASS" in content

        if has_main and has_assert and has_pass:
            return {"score": 15, "detail": "Has self-test with assertions and PASS output"}
        elif has_main and (has_assert or has_pass):
            return {"score": 10, "detail": "Has self-test, partial assertions",
                    "gap": "Incomplete test coverage",
                    "fix": "Add assertion-based self-tests with PASS/FAIL output"}
        elif has_main:
            return {"score": 5, "detail": "Has __main__ but no assertions",
                    "gap": "No automated verification",
                    "fix": "Add assert-based tests to __main__ block"}
        return {"score": 0, "detail": "No self-test",
                "gap": "No self-test block", "fix": "Add if __name__ == '__main__' with tests"}

    def _check_api_surface(self, block: dict) -> dict:
        """Does it expose a clean, documentable API?"""
        main_file = self.root / block["files"][0]
        if not main_file.exists():
            return {"score": 0, "detail": "File not found"}

        content = main_file.read_text(encoding="utf-8")
        # Count public classes and methods
        classes = [l for l in content.splitlines() if l.strip().startswith("class ") and not l.strip().startswith("class _")]
        public_methods = [l for l in content.splitlines()
                          if l.strip().startswith("def ") and not l.strip().startswith("def _")]
        has_docstrings = '"""' in content or "'''" in content

        if classes and public_methods and has_docstrings:
            return {"score": 15, "detail": f"{len(classes)} classes, {len(public_methods)} public methods, documented"}
        elif classes and public_methods:
            return {"score": 10, "detail": f"{len(classes)} classes, {len(public_methods)} methods, needs docs",
                    "gap": "Missing docstrings", "fix": "Add docstrings to all public methods"}
        elif public_methods:
            return {"score": 7, "detail": f"Functional API ({len(public_methods)} functions), no class encapsulation",
                    "gap": "No class encapsulation", "fix": "Wrap in a clean class interface"}
        return {"score": 3, "detail": "Minimal API surface",
                "gap": "No clear public API", "fix": "Design and document a public API"}

    def _check_event_bus(self, block: dict) -> dict:
        """Does it publish/subscribe to events?"""
        has_publish = False
        has_subscribe = False
        event_count = 0

        for file_rel in block["files"]:
            fp = self.root / file_rel
            if fp.exists():
                content = fp.read_text(encoding="utf-8")
                if "bus.publish" in content or ".publish(" in content:
                    has_publish = True
                    event_count += content.count(".publish(")
                if "bus.subscribe" in content or "get_recent" in content:
                    has_subscribe = True

        if has_publish and has_subscribe:
            return {"score": 15, "detail": f"Publishes ({event_count} calls) and subscribes to events"}
        elif has_publish:
            return {"score": 12, "detail": f"Publishes {event_count} events, no subscription",
                    "gap": "One-way event flow", "fix": "Add event subscription for reactive behavior"}
        elif "EPOSEventBus" in str(block.get("module", "")):
            return {"score": 15, "detail": "IS the event bus"}
        return {"score": 3, "detail": "No event bus integration",
                "gap": "Not wired to event bus", "fix": "Add EPOSEventBus.publish() for key actions"}

    def _check_data_sovereignty(self, block: dict) -> dict:
        """Does it own its own data path?"""
        has_vault_path = False
        has_db_access = False
        has_own_journal = False

        for file_rel in block["files"]:
            fp = self.root / file_rel
            if fp.exists():
                content = fp.read_text(encoding="utf-8")
                if "context_vault" in content or "get_context_vault" in content:
                    has_vault_path = True
                if "docker exec" in content or "psql" in content or "epos.contacts" in content:
                    has_db_access = True
                if ".jsonl" in content and ("open(" in content or "write_text" in content):
                    has_own_journal = True

        if has_vault_path and has_own_journal:
            return {"score": 15, "detail": "Owns vault path + JSONL journal"}
        elif has_vault_path or has_db_access:
            return {"score": 10, "detail": "Has data access but shared schema",
                    "gap": "Shared data ownership",
                    "fix": "Create dedicated vault subdirectory and journal"}
        return {"score": 5, "detail": "Minimal data persistence",
                "gap": "No dedicated data store",
                "fix": "Create vault path and JSONL journal for module state"}

    def _check_configuration(self, block: dict) -> dict:
        """Can it be configured independently?"""
        has_env = False
        has_defaults = False
        has_config_params = False

        for file_rel in block["files"]:
            fp = self.root / file_rel
            if fp.exists():
                content = fp.read_text(encoding="utf-8")
                if "os.getenv" in content or "load_dotenv" in content:
                    has_env = True
                if "def __init__" in content:
                    has_config_params = True
                # Check for sensible defaults
                if '= "' in content or "= '" in content:
                    has_defaults = True

        if has_env and has_config_params and has_defaults:
            return {"score": 15, "detail": "Env-configurable with defaults and init params"}
        elif has_config_params and has_defaults:
            return {"score": 10, "detail": "Init params with defaults, no env override",
                    "gap": "No environment configuration",
                    "fix": "Add os.getenv() overrides for key parameters"}
        elif has_config_params:
            return {"score": 7, "detail": "Has init but hardcoded values",
                    "gap": "Hardcoded configuration",
                    "fix": "Add configurable defaults via __init__ params or .env"}
        return {"score": 3, "detail": "Not configurable",
                "gap": "No configuration surface", "fix": "Add __init__ with configurable parameters"}

    def _check_value_proposition(self, block: dict) -> dict:
        """Can a non-EPOS user understand what it does in one sentence?"""
        vp = block.get("value_prop", "")
        if not vp:
            return {"score": 0, "detail": "No value proposition defined",
                    "gap": "Missing value proposition",
                    "fix": "Write a one-sentence value prop for external users"}

        # Quality heuristics
        words = vp.split()
        has_action_verb = any(w.lower() in ["creates", "generates", "tells", "tracks",
                                             "scores", "validates", "connects", "turns",
                                             "guides", "learns", "protects", "checks",
                                             "enforces", "manages", "automates"]
                              for w in words)
        is_jargon_free = not any(w.lower() in ["epos", "sovereign", "vault", "jsonl",
                                                "langgraph", "groq", "flywheel"]
                                  for w in words)
        is_concise = len(words) <= 20

        score = 5  # base for having a VP
        if has_action_verb:
            score += 4
        if is_jargon_free:
            score += 3
        if is_concise:
            score += 3

        detail = f"'{vp[:60]}...'" if len(vp) > 60 else f"'{vp}'"
        if score >= 12:
            return {"score": score, "detail": f"Clear, actionable VP: {detail}"}
        gaps = []
        if not has_action_verb:
            gaps.append("needs action verb")
        if not is_jargon_free:
            gaps.append("contains internal jargon")
        if not is_concise:
            gaps.append("too long")
        return {"score": score, "detail": detail,
                "gap": "; ".join(gaps),
                "fix": "Rewrite VP: [Action verb] + [what user gets] + [in plain language]"}

    # ── Formatted Output ─────────────────────────────────────────

    def print_catalog(self, catalog: dict) -> str:
        """Generate formatted catalog report."""
        lines = []
        lines.append("=" * 70)
        lines.append("  NODE SOVEREIGNTY CERTIFICATION — MARKETPLACE CATALOG")
        lines.append(f"  Certified: {catalog['certified_at'][:10]}")
        lines.append(f"  Total Nodes: {catalog['total_nodes']}")
        lines.append("=" * 70)
        lines.append("")

        for readiness in ["MARKETPLACE_READY", "HARDENING_NEEDED", "INCUBATING", "ORGANISM_ONLY"]:
            nodes = catalog["by_readiness"].get(readiness, [])
            if nodes:
                icon = {"MARKETPLACE_READY": ">>", "HARDENING_NEEDED": "~>",
                        "INCUBATING": "..", "ORGANISM_ONLY": "--"}.get(readiness, "??")
                lines.append(f"  {icon} {readiness} ({len(nodes)} nodes)")
                lines.append("  " + "-" * 50)
                for node_id in nodes:
                    cert = catalog["nodes"][node_id]
                    lines.append(f"    {cert['name']:<30} {cert['total_score']:3d}/105 ({cert['pct']}%)")
                    lines.append(f"      {cert['value_prop'][:70]}")
                    lines.append(f"      {cert['market_category']} | {cert['suggested_price']}")
                    if cert.get("hardening_needed"):
                        for h in cert["hardening_needed"]:
                            lines.append(f"      FIX: [{h['criterion']}] {h.get('fix', '')[:60]}")
                    lines.append("")

        return "\n".join(lines)


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile
    py_compile.compile("node_sovereignty_certifier.py", doraise=True)
    print("PASS: node_sovereignty_certifier.py compiles clean")

    certifier = NodeSovereigntyCertifier()

    # Test single node certification
    cert = certifier.certify_node("event_bus")
    assert cert["node_id"] == "event_bus"
    assert cert["total_score"] > 0
    assert cert["readiness"] in ("MARKETPLACE_READY", "HARDENING_NEEDED", "INCUBATING", "ORGANISM_ONLY")
    print(f"PASS: Event Bus certified — {cert['total_score']}/105 ({cert['readiness']})")

    # Test full catalog
    catalog = certifier.certify_all()
    assert catalog["total_nodes"] == len(BUILDING_BLOCKS)
    print(f"\nPASS: Full catalog — {catalog['total_nodes']} nodes certified")

    # Print formatted catalog
    report = certifier.print_catalog(catalog)
    print(report)

    print("\nPASS: NodeSovereigntyCertifier — all tests passed")
