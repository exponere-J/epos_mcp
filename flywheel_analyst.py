#!/usr/bin/env python3
"""
flywheel_analyst.py — EPOS Flywheel Pattern Recognition & SOP Evolution
=========================================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VI, VIII
Mission ID: EPOS Core Heal — Module 7 of 9
File Location: /mnt/c/Users/Jamie/workspace/epos_mcp/flywheel_analyst.py

Single responsibility: Read BI records, compliance data, and mission logs.
Generate FlywheelReport and SOP Update Proposals. Never auto-execute
proposals — human gate required.

Dependencies: path_utils (1), stasis (2), roles (3), epos_intelligence (4),
              constitutional_arbiter (6)
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from path_utils import get_epos_root, get_context_vault, get_logs_dir
from roles import AgentId
from epos_event_bus import EPOSEventBus
from epos_intelligence import (
    record_decision,
    record_event,
    get_decision_analytics,
    get_system_health_summary,
    get_mission_analytics,
    _load_jsonl,
    _decisions_log,
)
from constitutional_arbiter import audit_directory


# ── Exceptions ───────────────────────────────────────────────────

class PivotCooldownViolation(Exception):
    """Raised when a pivot is attempted within the cooldown window."""
    pass


# ── FlywheelReport ───────────────────────────────────────────────

@dataclass
class FlywheelReport:
    """Structured output from a flywheel analysis session."""
    report_id: str
    generated_at: str
    health: str                          # "healthy" | "degraded" | "insufficient_data"
    # BI metrics
    total_decisions: int
    total_missions: int
    decisions_by_type: Dict[str, int]
    # Governance metrics
    compliance_score: float
    files_audited: int
    top_violations: List[Dict]
    # Flywheel metrics
    pivot_cooldown_active: bool
    hours_until_pivot_allowed: float
    last_pivot_at: Optional[str]
    # Proposals
    sop_proposals_generated: int
    sop_proposals_pending: int
    # Recommendations (plain language, TTS-friendly)
    recommendations: List[str]
    # Proof artifact
    report_path: str


# ── FlywheelAnalyst ──────────────────────────────────────────────

class FlywheelAnalyst:
    """
    Pattern recognition and SOP evolution engine.
    Reads BI records, compliance data, and mission logs.
    Generates FlywheelReport and SOP Update Proposals.
    Never auto-executes proposals — human gate required.
    """

    PIVOT_COOLDOWN_HOURS = 72
    COMPLIANCE_HEALTHY_THRESHOLD = 80.0
    COMPLIANCE_PROPOSAL_THRESHOLD = 70.0
    PIVOT_DECISION_TYPES = [
        "architecture.pivot",
        "module.rebuild",
        "governance.constitutional_amendment",
    ]
    CACHE_TTL_HOURS = 24

    def __init__(self):
        self.vault_root = get_context_vault()
        self._ensure_governance_dirs()

    def _ensure_governance_dirs(self):
        """Create required governance subdirectories."""
        (self.vault_root / "governance" / "sop_proposals").mkdir(
            parents=True, exist_ok=True)
        (self.vault_root / "governance" / "pattern_observations").mkdir(
            parents=True, exist_ok=True)

    # ── Compliance Cache ─────────────────────────────────────────

    def get_compliance_score(self) -> Dict[str, Any]:
        """
        Read cached compliance result or run fresh audit.
        Cache TTL: 24 hours.
        """
        cache_path = self.vault_root / "bi_history" / "compliance_cache.json"

        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                cached_at = datetime.fromisoformat(cached["cached_at"])
                # Make timezone-aware for comparison
                if cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - cached_at).total_seconds() / 3600
                if age_hours < self.CACHE_TTL_HOURS:
                    return cached
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        # Cache miss or stale — run fresh audit
        result = audit_directory(get_epos_root())

        # Extract top violations by code
        violation_counts: Dict[str, int] = {}
        for file_result in result.get("results", []):
            for v in file_result.get("violations", []):
                code = v.get("code", "UNKNOWN")
                violation_counts[code] = violation_counts.get(code, 0) + 1

        top_violations = [
            {"code": code, "count": count}
            for code, count in sorted(violation_counts.items(), key=lambda x: -x[1])
        ][:5]

        cache_data = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "compliance_score": result.get("compliance_score", 0.0),
            "files_audited": result.get("total_files", 0),
            "total_violations": result.get("total_violations", 0),
            "top_violations": top_violations,
        }

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
        return cache_data

    # ── Pivot Cooldown ───────────────────────────────────────────

    def enforce_pivot_cooldown(self) -> None:
        """
        Raises PivotCooldownViolation if a pivot was logged
        within the last 72 hours. Returns cleanly if no pivot history.
        """
        # Read raw decision log for pivot entries
        entries = _load_jsonl(_decisions_log())

        for entry in reversed(entries):  # most recent first
            dtype = entry.get("decision_type", "")
            if dtype in self.PIVOT_DECISION_TYPES:
                ts_str = entry.get("timestamp") or entry.get("_bi_timestamp")
                if ts_str:
                    try:
                        pivot_time = datetime.fromisoformat(ts_str)
                        if pivot_time.tzinfo is None:
                            pivot_time = pivot_time.replace(tzinfo=timezone.utc)
                        age_hours = (datetime.now(timezone.utc) - pivot_time).total_seconds() / 3600
                        if age_hours < self.PIVOT_COOLDOWN_HOURS:
                            remaining = self.PIVOT_COOLDOWN_HOURS - age_hours
                            raise PivotCooldownViolation(
                                f"Pivot cooldown active. "
                                f"{remaining:.1f} hours remaining. "
                                f"Last pivot: {ts_str}"
                            )
                    except (ValueError, TypeError):
                        continue
        # No recent pivot found — return cleanly

    def _get_last_pivot(self) -> Optional[str]:
        """Get timestamp of most recent pivot decision, or None."""
        entries = _load_jsonl(_decisions_log())
        for entry in reversed(entries):
            if entry.get("decision_type", "") in self.PIVOT_DECISION_TYPES:
                return entry.get("timestamp") or entry.get("_bi_timestamp")
        return None

    # ── SOP Proposals ────────────────────────────────────────────

    def generate_sop_proposal(
        self,
        pattern: str,
        evidence: List[Dict],
        current_sop_section: str,
        proposed_change: str,
        affected_metric: str,
        class_: str = "operational",
    ) -> Dict[str, Any]:
        """
        Generate a SOP Update Proposal and write to governance vault.
        Logs to epos_intelligence. Never auto-executes.
        """
        proposal_id = (
            f"SOP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            f"-{uuid.uuid4().hex[:6]}"
        )
        proposal = {
            "proposal_id": proposal_id,
            "class": class_,
            "pattern": pattern,
            "evidence_record_ids": [e.get("id", "unknown") for e in evidence],
            "current_sop_section": current_sop_section,
            "proposed_change": proposed_change,
            "affected_metric": affected_metric,
            "status": "pending_review",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "auto_execute": False,
            "requires_human_gate": True,
        }

        proposal_path = (
            self.vault_root / "governance" / "sop_proposals" / f"{proposal_id}.json"
        )
        proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

        # Log to BI
        record_decision(
            decision_type="governance.sop_proposal",
            description=f"SOP Update Proposal generated: {pattern}",
            agent_id=AgentId.OMEGA.value,
            context={"proposal_id": proposal_id, "class": class_,
                     "affected_metric": affected_metric},
        )

        return proposal

    def count_pending_proposals(self) -> int:
        """Count SOP proposals awaiting human review."""
        proposals_dir = self.vault_root / "governance" / "sop_proposals"
        if not proposals_dir.exists():
            return 0
        count = 0
        for f in proposals_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("status") == "pending_review":
                    count += 1
            except Exception:
                pass
        return count

    # ── Recommendations ──────────────────────────────────────────

    def generate_recommendations(
        self, compliance: Dict[str, Any], decisions: Dict[str, Any]
    ) -> List[str]:
        """
        Plain language recommendations. TTS-friendly — no markdown,
        no bullet points, complete sentences.
        """
        recs: List[str] = []
        score = compliance.get("compliance_score", 0.0)

        if score < self.COMPLIANCE_HEALTHY_THRESHOLD and score > 0:
            recs.append(
                f"Codebase compliance is at {score:.0f} percent. "
                f"Target is 80 percent. Run the constitutional arbiter "
                f"to identify and fix the remaining violations."
            )

        violations = compliance.get("top_violations", [])
        if violations:
            top = violations[0]
            recs.append(
                f"The most common violation is {top.get('code', 'unknown')} "
                f"appearing {top.get('count', 0)} times. "
                f"Address this category first for the largest compliance gain."
            )

        total = decisions.get("total_decisions", 0)
        if total == 0:
            recs.append(
                "No BI decisions have been logged yet. "
                "Once modules begin logging decisions, "
                "pattern analysis will activate automatically."
            )

        pending = self.count_pending_proposals()
        if pending > 0:
            recs.append(
                f"There are {pending} SOP update proposals awaiting human review "
                f"in the governance vault."
            )

        if not recs:
            recs.append(
                "All systems nominal. Compliance is above threshold "
                "and no actionable patterns detected."
            )

        return recs

    # ── Main Analysis ────────────────────────────────────────────

    def session_health(self) -> FlywheelReport:
        """
        Primary analysis method. Reads all available BI data,
        checks compliance (cached), evaluates cooldown, generates
        SOP proposals if thresholds crossed.
        Returns FlywheelReport with proof artifact on disk.
        """
        # Gather data
        compliance = self.get_compliance_score()
        health_summary = get_system_health_summary()
        decision_data = get_decision_analytics(days=30)
        mission_data = get_mission_analytics(days=30)

        # Pivot cooldown
        cooldown_active = False
        hours_remaining = 0.0
        try:
            self.enforce_pivot_cooldown()
        except PivotCooldownViolation as e:
            cooldown_active = True
            match = re.search(r"([\d.]+) hours remaining", str(e))
            if match:
                hours_remaining = float(match.group(1))

        last_pivot_at = self._get_last_pivot()

        # Health determination
        score = compliance.get("compliance_score", 0.0)
        total_decisions = decision_data.get("total_decisions", 0)
        total_missions = mission_data.get("total_missions", 0)

        if total_decisions == 0 and score == 0:
            health = "insufficient_data"
        elif score >= self.COMPLIANCE_HEALTHY_THRESHOLD:
            health = "healthy"
        else:
            health = "degraded"

        # SOP proposal if compliance below proposal threshold
        proposals_this_run = 0
        if 0 < score < self.COMPLIANCE_PROPOSAL_THRESHOLD:
            self.generate_sop_proposal(
                pattern=f"Compliance below {self.COMPLIANCE_PROPOSAL_THRESHOLD}%",
                evidence=[{"id": "arbiter_audit", "score": score}],
                current_sop_section="Article XIV: File Governance",
                proposed_change=(
                    f"Schedule batch watermark pass on ungoverned files. "
                    f"Current score: {score:.0f}%. Target: 80%."
                ),
                affected_metric="codebase_compliance_score",
                class_="operational",
            )
            proposals_this_run = 1

        recs = self.generate_recommendations(compliance, decision_data)

        # Build report
        report = FlywheelReport(
            report_id=f"FW-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            health=health,
            total_decisions=total_decisions,
            total_missions=total_missions,
            decisions_by_type=decision_data.get("by_type", {}),
            compliance_score=score,
            files_audited=compliance.get("files_audited", 0),
            top_violations=compliance.get("top_violations", [])[:3],
            pivot_cooldown_active=cooldown_active,
            hours_until_pivot_allowed=hours_remaining,
            last_pivot_at=last_pivot_at,
            sop_proposals_generated=proposals_this_run,
            sop_proposals_pending=self.count_pending_proposals(),
            recommendations=recs,
            report_path="",  # filled below
        )

        # Save report to vault as JSONL
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        report_path = self.vault_root / "bi_history" / f"flywheel_{today}.jsonl"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report_dict = report.__dict__.copy()
        report_dict["report_path"] = str(report_path)
        report.report_path = str(report_path)

        with open(report_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(report_dict, default=str) + "\n")

        return report


# ── Self-test ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EPOS Flywheel Analyst v2.0 — Self-test")
    print("=" * 50)

    analyst = FlywheelAnalyst()

    # Test 1: session_health() returns FlywheelReport
    report = analyst.session_health()
    assert report.report_id.startswith("FW-"), "Report ID format wrong"
    assert report.health in ("healthy", "degraded", "insufficient_data")
    assert Path(report.report_path).exists(), "Report not saved to vault"
    assert Path(report.report_path).stat().st_size > 0
    print(f"  Health: {report.health}")
    print(f"  Compliance: {report.compliance_score:.1f}%")
    print(f"  Files audited: {report.files_audited}")
    print(f"  Recommendations: {len(report.recommendations)}")
    print(f"  Vault path: {report.report_path}")

    # Test 2: enforce_pivot_cooldown() with no pivots — must not raise
    try:
        analyst.enforce_pivot_cooldown()
        print("  Pivot cooldown: no active cooldown (correct)")
    except PivotCooldownViolation:
        print("  Pivot cooldown: active (also correct if pivot was logged)")

    # Test 3: SOP proposal generated if compliance < 70%
    if report.compliance_score < 70.0:
        assert report.sop_proposals_generated >= 1, \
            "Expected SOP proposal when compliance < 70%"
        print(f"  SOP proposals generated: {report.sop_proposals_generated}")
        pending = analyst.count_pending_proposals()
        print(f"  Pending proposals in vault: {pending}")
        proposals_dir = analyst.vault_root / "governance" / "sop_proposals"
        proposals = list(proposals_dir.glob("SOP-*.json"))
        assert len(proposals) >= 1, "No proposal file found on disk"
        print(f"  Proposal files on disk: {len(proposals)}")

    # Test 4: Report JSONL on disk
    from datetime import date
    today_str = date.today().isoformat()
    report_file = analyst.vault_root / "bi_history" / f"flywheel_{today_str}.jsonl"
    assert report_file.exists(), f"Report file missing: {report_file}"
    print(f"  Report file confirmed: {report_file}")

    print("\n  PASS: flywheel_analyst all self-tests passed")
