#!/usr/bin/env python3
"""
flywheel_scheduler.py — EPOS Flywheel Scheduled Reporting
==========================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/flywheel_scheduler.py
# EPOS GOVERNANCE WATERMARK

Runs flywheel health checks and vault index rebuilds.
Checks SOP review cadence (14-day cycle).
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from flywheel_analyst import FlywheelAnalyst, FlywheelReport
from vault_indexer import VaultIndexer
from epos_intelligence import get_decision_analytics
from path_utils import get_context_vault


class FlywheelScheduler:
    """Scheduled flywheel health and SOP review runner."""

    SOP_REVIEW_INTERVAL_DAYS = 14

    def run_once(self) -> FlywheelReport:
        """Run a single flywheel health check and rebuild vault index."""
        analyst = FlywheelAnalyst()
        report = analyst.session_health()
        VaultIndexer().rebuild_index()
        return report

    def should_run_sop_review(self) -> bool:
        """
        Returns True if 14+ days since last SOP review.
        Reads from bi_decisions — never from memory.
        """
        analytics = get_decision_analytics()
        recent = analytics.get("recent_decisions", [])

        for d in recent:
            if d.get("decision_type") == "governance.sop_review":
                review_time = datetime.fromisoformat(d["timestamp"])
                if review_time.tzinfo is None:
                    review_time = review_time.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - review_time
                if age < timedelta(days=self.SOP_REVIEW_INTERVAL_DAYS):
                    return False
        return True

    def run_with_sop_check(self) -> dict:
        """Run flywheel + check if SOP review is due."""
        report = self.run_once()
        sop_due = self.should_run_sop_review()
        return {
            "health": report.health,
            "compliance": report.compliance_score,
            "total_decisions": report.total_decisions,
            "sop_review_due": sop_due,
            "report_path": report.report_path,
        }


if __name__ == "__main__":
    scheduler = FlywheelScheduler()
    result = scheduler.run_with_sop_check()
    assert result["health"] in ("healthy", "degraded", "insufficient_data")
    print(f"  Health: {result['health']}")
    print(f"  Compliance: {result['compliance']:.1f}%")
    print(f"  Decisions: {result['total_decisions']}")
    print(f"  SOP review due: {result['sop_review_due']}")
    print(f"  Report: {result['report_path']}")
    print("PASS: flywheel_scheduler self-test passed")
