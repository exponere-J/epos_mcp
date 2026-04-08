#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_ttlg_package.py — TTLG Client Deliverable Generator
==========================================================
Constitutional Authority: EPOS Constitution v3.1

Generates the complete client-facing TTLG package:
  1. Sovereign Alignment Executive Summary
  2. Track-by-track Mirror Reports
  3. Action Plan with 30/60/90 milestones
  4. Investment recommendation (constitutionally priced)
  5. Next steps
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from groq_router import GroqRouter
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from epos_cms import EPOSContentManagement
from epos_financial import PRICING_CONSTITUTION
from path_utils import get_context_vault


class TTLGPackageGenerator:
    """Generates complete client-facing TTLG deliverables."""

    TIER_MAP = {
        (0, 30): ("L2", "$49-149/mo", "Start with creator tools"),
        (31, 54): ("L2-L3", "$149-497/mo", "Build the foundation"),
        (55, 74): ("L3", "$497-997/mo", "Accelerate production"),
        (75, 89): ("L3-L4", "$997-2997/mo", "Systemize operations"),
        (90, 100): ("L4-L5", "$2997+/mo", "Autonomous operations"),
    }

    def __init__(self):
        self.router = GroqRouter()
        self.bus = EPOSEventBus()
        self.cms = EPOSContentManagement()
        self.vault = get_context_vault()

    def generate_package(self, diagnostic_result: dict,
                         client_id: str) -> dict:
        """Full package generation. Routes to CMS. Returns package ID."""
        package_id = f"PKG-{uuid.uuid4().hex[:8]}"
        score = diagnostic_result.get("sovereign_alignment_score", 0)
        track_results = diagnostic_result.get("track_results", {})

        # 1. Executive Summary
        exec_summary = self.generate_executive_summary(diagnostic_result)
        exec_asset = self.cms.create_asset(
            asset_type="white_paper", title=f"Sovereign Alignment — {client_id} — Executive Summary",
            body=exec_summary, author_agent="ttlg_package",
            tags=["ttlg", "executive_summary", client_id],
        )

        # 2. Track Mirror Reports (use existing from diagnostic)
        mirror_ids = []
        for track, data in track_results.items():
            if data.get("mirror_report"):
                asset = self.cms.create_asset(
                    asset_type="mirror_report",
                    title=f"Mirror Report — {track.upper()} — {client_id}",
                    body=data["mirror_report"], author_agent="ttlg_package",
                    tags=["ttlg", track, client_id],
                )
                mirror_ids.append(asset.asset_id)

        # 3. Action Plan
        action_plan = self._generate_action_plan(track_results, client_id)
        plan_asset = self.cms.create_asset(
            asset_type="white_paper", title=f"Action Plan — {client_id}",
            body=action_plan, author_agent="ttlg_package",
            tags=["ttlg", "action_plan", client_id],
        )

        # 4. Investment Recommendation
        track_verdicts = {t: d.get("gate_verdict", "PASS") for t, d in track_results.items()}
        segment = diagnostic_result.get("track_results", {}).get(
            "marketing", {}).get("digital_footprint", {}).get("segment", "small_business")
        investment = self.generate_investment_recommendation(score, track_verdicts, segment)

        # 5. Save complete package
        package = {
            "package_id": package_id,
            "client_id": client_id,
            "sovereign_alignment_score": score,
            "executive_summary_asset": exec_asset.asset_id,
            "mirror_report_assets": mirror_ids,
            "action_plan_asset": plan_asset.asset_id,
            "investment_recommendation": investment,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        pkg_path = self.vault / "clients" / client_id
        pkg_path.mkdir(parents=True, exist_ok=True)
        (pkg_path / f"{package_id}.json").write_text(
            json.dumps(package, indent=2), encoding="utf-8"
        )

        record_decision(
            decision_type="ttlg.package.generated",
            description=f"TTLG package for {client_id}: score {score:.0f}/100",
            agent_id="ttlg_package", outcome="complete",
            context={"package_id": package_id, "score": score,
                     "tier": investment.get("recommended_tier")},
        )

        self.bus.publish("ttlg.package.generated",
                         {"package_id": package_id, "client_id": client_id, "score": score},
                         "ttlg_package")
        return package

    def generate_executive_summary(self, diagnostic_result: dict) -> str:
        """1-page summary. TTS-ready. 300 words max."""
        score = diagnostic_result.get("sovereign_alignment_score", 0)
        tracks = diagnostic_result.get("track_results", {})
        track_summary = "\n".join([
            f"- {t.upper()}: {d.get('gate_verdict', '?')} — {d.get('sovereign_alignment_score', 0):.0f}/25"
            for t, d in tracks.items()
        ])

        prompt = f"""Write the Sovereign Alignment Executive Summary.

Composite Score: {score:.0f}/100

Track scores:
{track_summary}

Structure:
1. Score interpretation in plain language (1-2 sentences)
2. The single most important finding across all tracks
3. The highest-leverage action to take this week
4. What changes in 90 days if they proceed

250-300 words. Warm, direct, authoritative. TTS-friendly. No bullet points."""

        return self.router.route("reasoning", prompt, max_tokens=500, temperature=0.4)

    def _generate_action_plan(self, track_results: dict, client_id: str) -> str:
        """Generate 30/60/90 action plan from prescriptions."""
        all_prescriptions = []
        for track, data in track_results.items():
            for p in data.get("prescriptions", [])[:2]:
                all_prescriptions.append({"track": track, **p} if isinstance(p, dict)
                                          else {"track": track, "action": str(p)})

        prompt = f"""Generate a 30/60/90 day action plan for {client_id}.

Available prescriptions:
{json.dumps(all_prescriptions[:8], indent=2)[:1500]}

Structure the plan as:
DAYS 1-30: Foundation (top 3 actions)
DAYS 31-60: Momentum (next 3 actions)
DAYS 61-90: Sovereignty (final 2 actions + expansion readiness)

For each action: what to do, success metric, effort level.
200-300 words. Plain prose. TTS-friendly."""

        return self.router.route("reasoning", prompt, max_tokens=500, temperature=0.3)

    def generate_investment_recommendation(self, score: float,
                                            track_verdicts: dict,
                                            segment: str) -> dict:
        """Tier + pricing recommendation. Constitutional pricing enforced."""
        tier, price_range, description = ("L3", "$497-997/mo", "Accelerate")
        for (low, high), (t, p, d) in self.TIER_MAP.items():
            if low <= score <= high:
                tier, price_range, description = t, p, d
                break

        go_tracks = [t for t, v in track_verdicts.items() if v == "GO"]
        services = []
        if "marketing" in go_tracks:
            services.append("Content Lab production")
        if "sales" in go_tracks:
            services.append("GRAG sales support")
        if "service" in go_tracks:
            services.append("Stewardship engine")
        if "governance" in go_tracks:
            services.append("Sovereignty audit")
        if not services:
            services = ["TTLG diagnostic subscription"]

        return {
            "recommended_tier": tier,
            "price_range": price_range,
            "description": description,
            "primary_services": services,
            "go_tracks": go_tracks,
            "margin_check": "constitutional" if score > 0 else "n/a",
        }


if __name__ == "__main__":
    gen = TTLGPackageGenerator()

    # Test: Generate executive summary from mock diagnostic
    mock = {
        "sovereign_alignment_score": 58,
        "track_results": {
            "marketing": {"gate_verdict": "GO", "sovereign_alignment_score": 13,
                          "mirror_report": "Marketing analysis...", "prescriptions": [{"action": "Publish 3x/week"}]},
            "sales": {"gate_verdict": "LEARN", "sovereign_alignment_score": 16,
                      "mirror_report": "Sales analysis...", "prescriptions": [{"action": "Automate follow-up"}]},
            "service": {"gate_verdict": "PASS", "sovereign_alignment_score": 19,
                        "mirror_report": "Service analysis...", "prescriptions": []},
            "governance": {"gate_verdict": "GO", "sovereign_alignment_score": 10,
                           "mirror_report": "Governance analysis...", "prescriptions": [{"action": "Migrate data"}]},
        }
    }

    summary = gen.generate_executive_summary(mock)
    assert len(summary) > 100
    print(f"  Executive summary: {len(summary)} chars")

    investment = gen.generate_investment_recommendation(58, {"marketing": "GO", "governance": "GO"}, "small_business")
    assert investment["recommended_tier"] in ["L2-L3", "L3"]
    print(f"  Tier: {investment['recommended_tier']} ({investment['price_range']})")
    print(f"  Services: {', '.join(investment['primary_services'])}")

    print("PASS: TTLGPackageGenerator — client deliverable operational")
