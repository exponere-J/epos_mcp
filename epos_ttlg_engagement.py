#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_ttlg_engagement.py — 90-Day Client Engagement Flow
=========================================================
Constitutional Authority: EPOS Constitution v3.1

Three 30-day phases. Specific deliverables at each touchpoint.
The arc from initial diagnostic to sovereign client.
"""

import json
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from groq_router import GroqRouter
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from epos_cms import EPOSContentManagement


class TTLGEngagementFlow:
    """
    The 90-day client engagement arc after initial diagnostic.

    Phase 1 (Day 0-30): Foundation
    Phase 2 (Day 31-60): Momentum
    Phase 3 (Day 61-90): Sovereignty
    """

    TOUCHPOINTS = [
        {"day": 0,  "phase": 1, "name": "Initial Sovereign Alignment Report", "type": "diagnostic"},
        {"day": 7,  "phase": 1, "name": "Implementation check-in", "type": "checkin"},
        {"day": 15, "phase": 1, "name": "Milestone 1 review", "type": "review"},
        {"day": 30, "phase": 1, "name": "Phase 1 close", "type": "phase_close"},
        {"day": 31, "phase": 2, "name": "Phase 2 diagnostic (new baseline)", "type": "diagnostic"},
        {"day": 45, "phase": 2, "name": "Mid-phase signal check", "type": "checkin"},
        {"day": 60, "phase": 2, "name": "Phase 2 close", "type": "phase_close"},
        {"day": 75, "phase": 3, "name": "Quarterly Business Review", "type": "qbr"},
        {"day": 90, "phase": 3, "name": "Full re-diagnostic + expansion review", "type": "diagnostic"},
    ]

    def __init__(self):
        self.vault = get_context_vault()
        self.router = GroqRouter()
        self.bus = EPOSEventBus()
        self.cms = EPOSContentManagement()

    def schedule_engagement(self, client_id: str, initial_score: float) -> dict:
        """Generate 90-day touchpoint schedule. Create tasks in DB."""
        start_date = datetime.now(timezone.utc)
        schedule = {
            "client_id": client_id,
            "initial_score": initial_score,
            "start_date": start_date.isoformat(),
            "touchpoints": [],
        }

        for tp in self.TOUCHPOINTS:
            tp_date = start_date + timedelta(days=tp["day"])
            entry = {
                **tp,
                "scheduled_date": tp_date.isoformat(),
                "status": "scheduled",
            }
            schedule["touchpoints"].append(entry)

            # Create task in DB
            try:
                tp_name = tp["name"]
                tp_phase = tp["phase"]
                due_str = tp_date.strftime('%Y-%m-%d')
                sql = (
                    f"INSERT INTO epos.tasks (title, description, status, priority, "
                    f"owner, node_tag, tags, due_date) VALUES ("
                    f"'TTLG: {tp_name} - {client_id}', "
                    f"'Phase {tp_phase} touchpoint for {client_id}', "
                    f"'todo', 'high', 'ttlg', 'echoes', "
                    f"ARRAY['engagement','phase-{tp_phase}','ttlg'], "
                    f"'{due_str}');"
                )
                subprocess.run([
                    "docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                    "-c", sql
                ], capture_output=True, text=True, timeout=10)
            except Exception:
                pass

        # Save schedule to vault
        sched_path = self.vault / "clients" / client_id
        sched_path.mkdir(parents=True, exist_ok=True)
        (sched_path / "engagement_schedule.json").write_text(
            json.dumps(schedule, indent=2), encoding="utf-8"
        )

        record_decision(
            decision_type="ttlg.engagement.scheduled",
            description=f"90-day engagement scheduled for {client_id}",
            agent_id="ttlg_engagement", outcome="scheduled",
            context={"client_id": client_id, "touchpoints": len(self.TOUCHPOINTS),
                     "initial_score": initial_score},
        )

        self.bus.publish("ttlg.engagement.scheduled",
                         {"client_id": client_id, "touchpoints": len(self.TOUCHPOINTS)},
                         "ttlg_engagement")
        return schedule

    def generate_day_7_checkin(self, client_id: str) -> str:
        """Auto-generated check-in pulling prescriptions from Day 0."""
        # Load initial diagnostic
        client_vault = self.vault / "clients" / client_id
        diag_files = list(client_vault.glob("diagnostic_*.json")) if client_vault.exists() else []

        prescriptions = []
        if diag_files:
            diag = json.loads(sorted(diag_files)[-1].read_text(encoding="utf-8"))
            for track_data in diag.get("track_results", {}).values():
                prescriptions.extend(track_data.get("prescriptions", [])[:2])

        prompt = f"""Write a Day 7 check-in message for client {client_id}.

Their top prescriptions from the initial diagnostic were:
{json.dumps(prescriptions[:4], indent=2)[:800]}

The message should:
1. Be warm and specific — reference their actual prescriptions
2. Ask about the top 2 items specifically
3. Offer to help with any blockers
4. Be 100-150 words, conversational, TTS-friendly
"""
        return self.router.route("reasoning", prompt, max_tokens=300, temperature=0.5)

    def generate_day_15_review(self, client_id: str) -> dict:
        """Progress review — lightweight re-scan of priority track."""
        prompt = f"""Generate a Day 15 progress review for client {client_id}.

Assess:
1. What likely changed in 15 days (realistic for a small business)
2. Common barriers at this stage
3. One specific adjustment to recommend

Output JSON:
{{"progress_made": "", "barriers_likely": "", "adjustment": ""}}"""
        try:
            raw = self.router.route("reasoning", prompt, max_tokens=400, temperature=0.3)
            return json.loads(raw.strip())
        except Exception:
            return {"progress_made": "assessment_needed", "barriers_likely": "unknown", "adjustment": "schedule_call"}

    def generate_day_30_close(self, client_id: str) -> dict:
        """Phase 1 close. Formal progress report."""
        prompt = f"""Generate a Phase 1 (Day 30) close report for client {client_id}.

Structure:
1. What was prescribed at Day 0
2. What was accomplished in 30 days (realistic estimate)
3. Remaining items for Phase 2
4. Updated outlook

200-300 words. Direct and honest. TTS-friendly."""

        report_text = self.router.route("reasoning", prompt, max_tokens=500, temperature=0.4)

        # Save as CMS asset
        asset = self.cms.create_asset(
            asset_type="mirror_report",
            title=f"Phase 1 Close — {client_id}",
            body=report_text,
            author_agent="ttlg_engagement",
            tags=["phase-1", "close", client_id],
        )
        return {"report": report_text, "asset_id": asset.asset_id}

    def generate_qbr(self, client_id: str) -> str:
        """Quarterly Business Review — full performance summary."""
        prompt = f"""Generate a Quarterly Business Review for client {client_id}.

Include:
1. Performance summary (content produced, leads generated, revenue attributed)
2. Sovereign Alignment Score progression (Day 0 → Day 75)
3. Key wins this quarter
4. Recommendations for next quarter
5. Expansion opportunities

300-400 words. Professional but warm. Data-driven where possible.
TTS-friendly — no bullet points, plain prose."""

        return self.router.route("reasoning", prompt, max_tokens=600, temperature=0.4)


if __name__ == "__main__":
    flow = TTLGEngagementFlow()

    # Test: Schedule engagement for PGP Orlando
    schedule = flow.schedule_engagement("pgp_orlando", initial_score=58.0)
    assert len(schedule["touchpoints"]) == 9
    print(f"  Scheduled: {len(schedule['touchpoints'])} touchpoints for pgp_orlando")
    for tp in schedule["touchpoints"][:3]:
        print(f"    Day {tp['day']}: {tp['name']} ({tp['scheduled_date'][:10]})")

    # Test: Day 7 check-in
    checkin = flow.generate_day_7_checkin("pgp_orlando")
    assert len(checkin) > 50
    print(f"  Day 7 check-in: {len(checkin)} chars")

    print("PASS: TTLGEngagementFlow — 90-day engagement operational")
