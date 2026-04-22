#!/usr/bin/env python3
"""
echoes_lead_scorer.py — Echoes Marketing Lead Scoring Engine
==============================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/echoes_lead_scorer.py
# EPOS GOVERNANCE WATERMARK

Scores every lead interaction and routes to correct nurture sequence.
Triggers TTLG diagnostic at threshold. Generates Mirror Reports.
"""

import json
import subprocess
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from path_utils import get_context_vault

DB_CONTAINER = "epos_db"
DB_USER = "epos_user"
DB_NAME = "epos"


def _psql(sql: str) -> str:
    """Execute SQL via docker exec and return raw output."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME,
         "-t", "-A", "-F", "\t", "-c", sql],
        capture_output=True, text=True, timeout=15,
    )
    return result.stdout.strip()


class EchoesLeadScorer:
    """
    Scores every lead interaction and routes to correct nurture sequence.

    Score thresholds:
      0-30:   Cold. Newsletter only.
      31-60:  Warm. Nurture sequence active.
      61-84:  Hot. TTLG diagnostic triggered.
      85+:    Qualified. Human alert + personal outreach.
    """

    SCORE_WEIGHTS = {
        "email_captured": 10,
        "white_paper_download": 15,
        "free_tool_used": 20,
        "video_watched_50pct": 5,
        "video_watched_100pct": 10,
        "email_opened": 3,
        "email_clicked": 8,
        "contact_form_submitted": 25,
        "discovery_call_booked": 40,
        "business_email_domain": 10,
        "repeated_visit": 5,
        "social_share": 12,
    }

    THRESHOLD_WARM = 31
    THRESHOLD_HOT = 61
    THRESHOLD_QUALIFIED = 85

    def score_interaction(self, contact_id: str, interaction_type: str,
                          channel: str = "web", content_id: str = None) -> int:
        """Add score delta to contact. Return new total score."""
        delta = self.SCORE_WEIGHTS.get(interaction_type, 0)

        # Log interaction
        _psql(f"""
            INSERT INTO epos.interactions (contact_id, type, channel, content_id, signal, score_delta)
            VALUES ('{contact_id}', '{interaction_type}', '{channel}',
                    {f"'{content_id}'" if content_id else 'NULL'},
                    '{interaction_type}', {delta});
        """)

        # Update lead score
        _psql(f"""
            UPDATE epos.contacts
            SET lead_score = lead_score + {delta}, updated_at = NOW()
            WHERE id = '{contact_id}';
        """)

        # Get new score
        new_score_str = _psql(f"SELECT lead_score FROM epos.contacts WHERE id = '{contact_id}';")
        new_score = int(new_score_str) if new_score_str else 0

        # Update stage based on score
        if new_score >= self.THRESHOLD_QUALIFIED:
            stage = "offer"
            _psql(f"UPDATE epos.contacts SET stage = 'offer' WHERE id = '{contact_id}';")
            record_decision(
                decision_type="lead.qualified",
                description=f"Lead qualified: score {new_score}",
                agent_id="lead_scorer",
                outcome="qualified",
                context={"contact_id": contact_id, "score": new_score},
            )
        elif new_score >= self.THRESHOLD_HOT:
            _psql(f"UPDATE epos.contacts SET stage = 'diagnostic' WHERE id = '{contact_id}';")
            self.trigger_ttlg(contact_id)
        elif new_score >= self.THRESHOLD_WARM:
            _psql(f"UPDATE epos.contacts SET stage = 'nurture' WHERE id = '{contact_id}';")

        return new_score

    def classify_segment(self, contact: dict) -> str:
        """Assign segment based on contact attributes and score."""
        company = str(contact.get("company", "")).lower()
        score = contact.get("lead_score", 0)

        if "agency" in company:
            return "agency"
        if score > 80 and contact.get("company"):
            return "enterprise"
        if contact.get("company") and score < 70:
            return "small_business"
        return "individual_creator"

    def trigger_ttlg(self, contact_id: str) -> None:
        """Fire TTLG diagnostic for a contact that crossed threshold."""
        record_decision(
            decision_type="ttlg.diagnostic_triggered",
            description=f"TTLG diagnostic triggered for contact {contact_id[:8]}",
            agent_id="lead_scorer",
            outcome="triggered",
            context={"contact_id": contact_id},
        )
        # Write draft mirror report placeholder
        _psql(f"""
            INSERT INTO epos.mirror_reports (contact_id, status)
            VALUES ('{contact_id}', 'draft');
        """)

    def generate_mirror_report(self, contact: dict, ttlg_output: dict) -> str:
        """Generate personalized Mirror Report via Groq 70B."""
        from groq_router import GroqRouter
        router = GroqRouter()

        prompt = f"""
You are the diagnostic voice of Echoes Marketing.
Write a Mirror Report for this prospect.

Contact profile:
  Segment: {contact.get('segment_id', 'unknown')}
  Company: {contact.get('company', 'individual')}
  Current stage: {contact.get('stage', 'discovery')}
  Score: {contact.get('lead_score', 0)}

TTLG findings:
{json.dumps(ttlg_output, indent=2)[:2000]}

The Mirror Report:
1. Reflects their current state back to them honestly
2. Names the gap between where they are and where they could be
3. Shows exactly where Echoes fits
4. Makes ONE clear recommendation
5. Ends with ONE clear next step

Voice: Direct. Warm. Authoritative. No hype. No pressure.
Length: 400-600 words. Complete sentences, no bullet points.
"""
        return router.route("reasoning", prompt, max_tokens=1000)

    def get_pipeline_stats(self) -> Dict:
        """Get current pipeline statistics."""
        raw = _psql("""
            SELECT stage, COUNT(*), AVG(lead_score)::int
            FROM epos.contacts
            GROUP BY stage ORDER BY stage;
        """)
        stages = {}
        for line in raw.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 3:
                    stages[parts[0]] = {"count": int(parts[1]), "avg_score": int(parts[2])}
        return stages


if __name__ == "__main__":
    scorer = EchoesLeadScorer()

    # Test 1: Pipeline stats
    stats = scorer.get_pipeline_stats()
    print(f"  Pipeline stages: {len(stats)}")
    for stage, data in stats.items():
        print(f"    {stage}: {data['count']} contacts, avg score {data['avg_score']}")

    # Test 2: Segment classification
    assert scorer.classify_segment({"company": "Big Agency LLC", "lead_score": 50}) == "agency"
    assert scorer.classify_segment({"company": "", "lead_score": 20}) == "individual_creator"
    assert scorer.classify_segment({"company": "Acme Corp", "lead_score": 90}) == "enterprise"
    print("  Segment classification: PASS")

    # Test 3: Score weights loaded
    assert scorer.SCORE_WEIGHTS["discovery_call_booked"] == 40
    assert scorer.THRESHOLD_QUALIFIED == 85
    print("  Score weights: PASS")

    print("PASS: echoes_lead_scorer self-tests passed")
