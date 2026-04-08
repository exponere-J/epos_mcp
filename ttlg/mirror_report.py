#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
mirror_report.py — TTLG Mirror Report Generator (Mission 7)
=============================================================
Constitutional Authority: EPOS Constitution v3.1

Produces the consumable output from TTLG v2 diagnostics:
  - Boardroom View (CEO): revenue leakage, ROI, timeline
  - Engine Room View (CTO): Build Manifests, deployment specs
  - Three-Option Engagement Menu: Quick Win / Strategic / Full
  - Score Trajectory: 30/60/90 day projections
  - Value at Risk: dollarized cost of inaction

Three output formats: Markdown, JSON, plain text (for TTS/Audio Overview).
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

VAULT = get_context_vault()
REPORTS_DIR = VAULT / "ttlg" / "reports"


class MirrorReportGenerator:
    """
    Transforms diagnostic results into consumable Mirror Reports.
    Boardroom + Engine Room + Three-Option Menu + Score Trajectory.
    """

    def __init__(self, diagnostic_state: dict):
        self.state = diagnostic_state
        self.diag_id = diagnostic_state.get("diagnostic_id", "UNKNOWN")
        self.report_dir = REPORTS_DIR / self.diag_id
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> dict:
        """Generate all 3 formats and return paths."""
        md = self._generate_markdown()
        js = self._generate_json()
        txt = self._generate_summary_text()

        md_path = self.report_dir / "mirror_report.md"
        json_path = self.report_dir / "mirror_report.json"
        txt_path = self.report_dir / "mirror_report_summary.txt"

        md_path.write_text(md, encoding="utf-8")
        json_path.write_text(json.dumps(js, indent=2), encoding="utf-8")
        txt_path.write_text(txt, encoding="utf-8")

        # Save manifests individually
        manifests_dir = self.report_dir / "manifests"
        manifests_dir.mkdir(exist_ok=True)
        for m in self.state.get("manifests", []):
            rx_id = m.get("prescription_id", "unknown")
            (manifests_dir / f"{rx_id}.json").write_text(json.dumps(m, indent=2), encoding="utf-8")

        if _BUS:
            try:
                _BUS.publish("ttlg.report.generated", {
                    "diagnostic_id": self.diag_id,
                    "gap_count": len(self.state.get("consequence_chains", [])),
                    "total_var": self.state.get("value_at_risk", 0),
                }, source_module="mirror_report")
            except Exception:
                pass

        return {
            "markdown": str(md_path),
            "json": str(json_path),
            "summary": str(txt_path),
            "manifests_dir": str(manifests_dir),
        }

    def _generate_markdown(self) -> str:
        """Full Mirror Report in Markdown."""
        verdict = self.state.get("gate_verdict", "?")
        findings = self.state.get("scout_findings", [])
        chains = self.state.get("consequence_chains", [])
        manifests = self.state.get("manifests", [])
        trajectory = self.state.get("score_trajectory", {})
        var = self.state.get("value_at_risk", 0)
        props_name = self.state.get("props_name", "standard")

        # Separate manifests by tier
        quick = [m for m in manifests if m.get("type") == "quick_win"]
        strategic = [m for m in manifests if m.get("type") == "strategic_build"]
        full = [m for m in manifests if m.get("type") == "full_transformation"]

        qw_cost = sum(m.get("monthly_cost", 0) for m in quick)
        sb_cost = sum(m.get("monthly_cost", 0) for m in strategic)
        ft_cost = sum(m.get("monthly_cost", 0) for m in full)

        lines = [
            f"# MIRROR REPORT: {self.diag_id}",
            f"**Diagnostic:** {props_name} | **Verdict:** {verdict} | **Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"This diagnostic identified {len(chains)} gaps with a combined Value at Risk of **${var:,.0f}** per quarter. "
            f"The gate verdict is **{verdict}**. "
            f"{'Prescriptive Build Manifests have been generated for each gap.' if verdict == 'GO' else 'Further analysis recommended.'}",
            "",
            "---",
            "",
            "## 2. Boardroom View",
            "",
            f"**Total Revenue at Risk:** ${var:,.0f}/quarter",
            "",
            "### Top Gaps by Impact",
            "",
            "| Gap | Quarterly Impact | Severity |",
            "|-----|-----------------|----------|",
        ]

        for c in sorted(chains, key=lambda x: x.get("estimated_quarterly_impact", 0), reverse=True)[:5]:
            lines.append(f"| {c['scope']} | ${c.get('estimated_quarterly_impact', 0):,.0f} | {c.get('finding', '')[:40]} |")

        lines.extend([
            "",
            "### ROI by Engagement Tier",
            "",
            "| Tier | Monthly Investment | 90-Day ROI | Timeline |",
            "|------|-------------------|-----------|----------|",
            f"| Quick Win | ${qw_cost:,.0f}/mo | {quick[0].get('projected_roi_90d', 0):.0f}% | Days | " if quick else "| Quick Win | - | - | - |",
            f"| Strategic Build | ${sb_cost:,.0f}/mo | {strategic[0].get('projected_roi_90d', 0):.0f}% | Weeks | " if strategic else "| Strategic Build | - | - | - |",
            f"| Full Transformation | ${ft_cost:,.0f}/mo | {full[0].get('projected_roi_90d', 0):.0f}% | Months | " if full else "| Full Transformation | - | - | - |",
            "",
            "---",
            "",
            "## 3. Engine Room View",
            "",
        ])

        for m in manifests:
            lines.extend([
                f"### [{m.get('type', '?').upper()}] {m.get('prescription_id', '?')}",
                f"**Gap:** {m.get('gap_addressed', '?')}",
                f"**Nodes:** {', '.join(m.get('nodes_required', []))}",
                f"**Monthly Cost:** ${m.get('monthly_cost', 0):,.2f}",
                f"**ROI (90d):** {m.get('projected_roi_90d', 0):.0f}%",
                f"**Deployment:**",
            ])
            for step in m.get("deployment_sequence", []):
                lines.append(f"  - {step}")
            lines.extend([
                f"**Success Criteria:**",
            ])
            for sc in m.get("success_criteria", []):
                lines.append(f"  - {sc}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 4. Three-Option Engagement Menu",
            "",
        ])

        if quick:
            lines.extend([
                f"### Option A: Quick Win",
                f"- **Investment:** ${qw_cost:,.0f}/month",
                f"- **Addresses:** Top 1 gap",
                f"- **ROI:** {quick[0].get('projected_roi_90d', 0):.0f}% in 90 days",
                f"- **Timeline:** Days to deploy",
                "",
            ])
        if strategic:
            lines.extend([
                f"### Option B: Strategic Build",
                f"- **Investment:** ${sb_cost:,.0f}/month",
                f"- **Addresses:** Top 3-5 gaps",
                f"- **ROI:** {strategic[0].get('projected_roi_90d', 0):.0f}% in 90 days",
                f"- **Timeline:** Weeks to deploy",
                "",
            ])
        if full:
            lines.extend([
                f"### Option C: Full Transformation",
                f"- **Investment:** ${ft_cost:,.0f}/month",
                f"- **Addresses:** All identified gaps",
                f"- **ROI:** {full[0].get('projected_roi_90d', 0):.0f}% in 90 days",
                f"- **Timeline:** 1-3 months",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 5. Score Trajectory",
            "",
            f"- **Current:** {trajectory.get('current_score', 0)}%",
            f"- **30 days:** {trajectory.get('30_day', 0):.0f}%",
            f"- **60 days:** {trajectory.get('60_day', 0):.0f}%",
            f"- **90 days:** {trajectory.get('90_day', 0):.0f}%",
            "",
            "---",
            "",
            "## 6. Value at Risk",
            "",
            f"**Total cost of inaction over 90 days: ${var * 1:,.0f}**",
            "",
            "Per-gap breakdown:",
            "",
        ])

        for c in chains:
            lines.append(f"- {c['scope']}: ${c.get('estimated_quarterly_impact', 0):,.0f}/quarter")

        lines.extend([
            "",
            "---",
            "",
            "> *1% daily. 37x annually.*",
            "",
            f"*Mirror Report generated by TTLG v2 | {self.diag_id} | EXPONERE / EPOS*",
        ])

        return "\n".join(lines)

    def _generate_json(self) -> dict:
        """Structured JSON for Command Center and programmatic use."""
        chains = self.state.get("consequence_chains", [])
        manifests = self.state.get("manifests", [])
        trajectory = self.state.get("score_trajectory", {})
        var = self.state.get("value_at_risk", 0)

        quick = [m for m in manifests if m.get("type") == "quick_win"]
        strategic = [m for m in manifests if m.get("type") == "strategic_build"]
        full = [m for m in manifests if m.get("type") == "full_transformation"]

        return {
            "diagnostic_id": self.diag_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "verdict": self.state.get("gate_verdict"),
            "total_gaps": len(chains),
            "total_manifests": len(manifests),
            "value_at_risk_quarterly": var,
            "engagement_menu": {
                "quick_win": {"monthly_cost": sum(m.get("monthly_cost", 0) for m in quick),
                              "manifests": len(quick)},
                "strategic_build": {"monthly_cost": sum(m.get("monthly_cost", 0) for m in strategic),
                                    "manifests": len(strategic)},
                "full_transformation": {"monthly_cost": sum(m.get("monthly_cost", 0) for m in full),
                                        "manifests": len(full)},
            },
            "score_trajectory": trajectory,
            "gaps": [{"scope": c["scope"], "impact": c.get("estimated_quarterly_impact", 0)} for c in chains],
            "manifests": manifests,
        }

    def _generate_summary_text(self) -> str:
        """500-word plain text for TTS/Audio Overview via NotebookLM."""
        verdict = self.state.get("gate_verdict", "?")
        chains = self.state.get("consequence_chains", [])
        manifests = self.state.get("manifests", [])
        trajectory = self.state.get("score_trajectory", {})
        var = self.state.get("value_at_risk", 0)
        props_name = self.state.get("props_name", "standard")

        top_gaps = sorted(chains, key=lambda x: x.get("estimated_quarterly_impact", 0), reverse=True)[:3]
        quick = [m for m in manifests if m.get("type") == "quick_win"]

        lines = [
            f"TTLG Diagnostic Summary for {props_name}.",
            "",
            f"This assessment identified {len(chains)} operational gaps with a combined quarterly value at risk of {var:,.0f} dollars.",
            f"The diagnostic verdict is {verdict}.",
            "",
        ]

        if top_gaps:
            lines.append("The highest-impact gaps are:")
            for i, g in enumerate(top_gaps, 1):
                lines.append(f"{i}. {g['scope']}, estimated at {g.get('estimated_quarterly_impact', 0):,.0f} dollars per quarter.")
            lines.append("")

        if quick:
            lines.append(f"The Quick Win prescription addresses the most immediate gap at {quick[0].get('monthly_cost', 0):,.0f} dollars per month "
                         f"with a projected 90-day return of {quick[0].get('projected_roi_90d', 0):.0f} percent.")
            lines.append("")

        if trajectory:
            lines.append(f"Current alignment score is {trajectory.get('current_score', 0)} percent. "
                         f"With prescriptions implemented, projected scores are "
                         f"{trajectory.get('30_day', 0):.0f} at 30 days, "
                         f"{trajectory.get('60_day', 0):.0f} at 60 days, "
                         f"and {trajectory.get('90_day', 0):.0f} at 90 days.")
            lines.append("")

        lines.append(f"The cost of inaction over the next 90 days is {var:,.0f} dollars in accumulated operational debt.")
        lines.append("")
        lines.append("Three engagement tiers are available. Option A is the Quick Win for immediate impact. "
                     "Option B is a Strategic Build addressing the top gaps over weeks. "
                     "Option C is a Full Transformation addressing all identified gaps over one to three months.")
        lines.append("")
        lines.append("1 percent daily. 37 times annually. Every day the system gets stronger.")

        return "\n".join(lines)


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    from ttlg.pipeline_graph import run_diagnostic

    passed = 0

    # Run diagnostic to get state
    print("Running diagnostic for Mirror Report test...")
    state = run_diagnostic("ecosystem_architecture")
    assert state["status"] == "complete"
    passed += 1

    # Generate Mirror Report
    gen = MirrorReportGenerator(state)
    paths = gen.generate_all()
    passed += 1

    # Verify all 3 formats exist
    assert Path(paths["markdown"]).exists(), "Markdown report missing"
    assert Path(paths["json"]).exists(), "JSON report missing"
    assert Path(paths["summary"]).exists(), "Summary text missing"
    passed += 1

    # Verify JSON structure
    with open(paths["json"]) as f:
        report_json = json.load(f)
    assert "engagement_menu" in report_json
    assert "score_trajectory" in report_json
    assert "manifests" in report_json
    passed += 1

    # Verify summary is under 500 words
    summary = Path(paths["summary"]).read_text(encoding="utf-8")
    word_count = len(summary.split())
    assert word_count < 500, f"Summary too long: {word_count} words"
    passed += 1

    print(f"\nPASS: mirror_report ({passed} assertions)")
    print(f"Report: {paths['markdown']}")
    print(f"Summary: {word_count} words (under 500 limit)")
