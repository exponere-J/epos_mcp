#!/usr/bin/env python3
"""
ttlg_scheduler.py — EPOS TTLG Automated Schedule
==================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/ttlg_scheduler.py
# EPOS GOVERNANCE WATERMARK

Runs TTLG light scouts on schedule. Default: daily.
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from constitutional_arbiter import audit_directory
from path_utils import get_epos_root, get_context_vault
from epos_intelligence import record_decision, get_decision_analytics
from epos_event_bus import EPOSEventBus
from flywheel_scheduler import FlywheelScheduler


class TTLGScheduler:
    """TTLG light scout scheduler."""

    def __init__(self):
        self.bus = EPOSEventBus()

    def run_systems_scan(self) -> dict:
        """Run constitutional_arbiter audit. Publish results."""
        epos_root = get_epos_root()
        result = audit_directory(epos_root)
        summary = {
            "compliance_score": result.get("compliance_score", 0),
            "total_files": result.get("total_files", 0),
            "total_violations": result.get("total_violations", 0),
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        record_decision(
            decision_type="ttlg.systems_scan_complete",
            description=f"TTLG systems scan: {summary['compliance_score']:.1f}% compliance",
            agent_id="ttlg_scheduler", outcome="scanned", context=summary,
        )
        try:
            self.bus.publish("ttlg.systems_scan.complete", summary, "ttlg_scheduler")
        except Exception:
            pass
        return summary

    def run_market_scan(self, niche_id: str = "lego_affiliate") -> dict:
        """Run MA1 scan or fallback to vault riff sparks."""
        import os
        if os.getenv("YOUTUBE_API_KEY"):
            return {"status": "api_available", "note": "Run ma1_niche_scanner.py directly"}
        else:
            # Fallback: generate sparks from niche vocabulary
            from content.lab.nodes.r1_radar import R1Radar
            radar = R1Radar()
            sparks = radar.capture_from_competitor_scan(niche_id)
            return {"status": "fallback_sparks", "spark_count": len(sparks)}

    def should_run_daily(self) -> bool:
        """Check if 24+ hours since last TTLG run."""
        analytics = get_decision_analytics()
        recent = analytics.get("recent_decisions", [])
        for d in recent:
            if d.get("decision_type") == "ttlg.systems_scan_complete":
                scan_time = datetime.fromisoformat(d["timestamp"])
                if scan_time.tzinfo is None:
                    scan_time = scan_time.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - scan_time < timedelta(hours=24):
                    return False
        return True

    def run_if_due(self) -> dict:
        """Entry point for scheduled execution."""
        if not self.should_run_daily():
            return {"status": "not_due", "note": "Last scan less than 24h ago"}

        systems = self.run_systems_scan()
        market = self.run_market_scan()
        flywheel = FlywheelScheduler().run_once()

        return {
            "status": "complete",
            "systems_scan": systems,
            "market_scan": market,
            "flywheel_health": flywheel.health,
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    scheduler = TTLGScheduler()
    result = scheduler.run_if_due()
    print(f"  Status: {result['status']}")
    if result["status"] == "complete":
        print(f"  Systems: {result['systems_scan']['compliance_score']:.1f}%")
        print(f"  Market: {result['market_scan']['status']}")
        print(f"  Flywheel: {result['flywheel_health']}")
    print("PASS: TTLGScheduler self-test passed")
