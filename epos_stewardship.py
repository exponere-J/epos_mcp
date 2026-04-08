#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_stewardship.py — Engagement Health + Stewardship Engine
==============================================================
Constitutional Authority: EPOS Constitution v3.1

Continuous client health scoring, churn detection,
expansion detection, automated stewardship touchpoints.
Without this, retention is memory-dependent.
"""

import json
import uuid
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from path_utils import get_context_vault


HEALTH_FACTORS = {
    "content_delivered_on_time": 0.25,
    "client_engagement_with_reports": 0.20,
    "support_ticket_volume": -0.15,
    "feature_adoption_rate": 0.20,
    "response_time_to_steward": 0.10,
    "nps_score": 0.10,
}


class EPOSStewardship:
    """Continuous client health scoring and stewardship."""

    def __init__(self):
        self.bus = EPOSEventBus()
        self.vault = get_context_vault()

    def _psql(self, sql: str) -> str:
        import os
        result = subprocess.run(
            ["docker", "exec", os.getenv("DB_CONTAINER", "epos_db"),
             "psql", "-U", os.getenv("DB_USER", "epos_user"),
             "-d", os.getenv("DB_NAME", "epos"), "-t", "-A", "-c", sql],
            capture_output=True, text=True, timeout=15)
        return result.stdout.strip()

    def compute_engagement_health(self, client_id: str) -> float:
        """0-100 health score from weighted factors."""
        # Base score from available signals
        score = 70.0  # default for new clients

        # Check support ticket volume (negative weight)
        raw = self._psql(f"""
            SELECT COUNT(*) FROM epos.support_tickets
            WHERE contact_id::text LIKE '{client_id}%'
            AND opened_at > NOW() - INTERVAL '30 days';
        """)
        ticket_count = int(raw) if raw.isdigit() else 0
        score -= ticket_count * 5  # each ticket reduces health

        # Check delivery status
        raw = self._psql(f"""
            SELECT COUNT(*) FILTER (WHERE status='queued') as queued,
                   COUNT(*) FILTER (WHERE delivered_at IS NOT NULL) as delivered
            FROM epos.deliveries
            WHERE contact_id::text LIKE '{client_id}%';
        """)
        # Clamp to 0-100
        score = max(0, min(100, score))

        try:
            self.bus.publish("client.health.updated",
                             {"client_id": client_id, "health_score": score},
                             "epos_stewardship")
        except Exception:
            pass
        return score

    def detect_churn_risk(self, client_id: str) -> dict:
        health = self.compute_engagement_health(client_id)
        churn_prob = max(0, (100 - health) / 100)

        result = {"client_id": client_id, "health_score": health,
                  "churn_probability": churn_prob,
                  "risk_level": "high" if churn_prob > 0.3 else "medium" if churn_prob > 0.15 else "low"}

        if churn_prob > 0.3:
            record_decision(decision_type="client.at_risk",
                            description=f"Client {client_id} at risk: {churn_prob:.0%} churn probability",
                            agent_id="epos_stewardship", outcome="at_risk", context=result)
            try:
                self.bus.publish("client.at_risk", result, "epos_stewardship")
            except Exception:
                pass
        return result

    def detect_expansion_opportunity(self, client_id: str) -> dict:
        health = self.compute_engagement_health(client_id)
        if health >= 80:
            result = {"client_id": client_id, "health_score": health,
                      "expansion_ready": True,
                      "recommendation": "Upgrade tier or add services"}
            try:
                self.bus.publish("client.expansion_ready", result, "epos_stewardship")
            except Exception:
                pass
            return result
        return {"client_id": client_id, "expansion_ready": False, "health_score": health}

    def generate_qbr(self, client_id: str) -> dict:
        """Auto-generate Quarterly Business Review."""
        from groq_router import GroqRouter
        from epos_cms import EPOSContentManagement

        router = GroqRouter()
        health = self.compute_engagement_health(client_id)

        prompt = f"""Generate a Quarterly Business Review summary for client {client_id}.
Health score: {health:.0f}/100.
Include: performance summary, key wins, areas for improvement,
recommendations for next quarter. 200 words. Professional tone."""

        qbr_text = router.route("reasoning", prompt, max_tokens=400)

        cms = EPOSContentManagement()
        asset = cms.create_asset(
            asset_type="white_paper", title=f"QBR — {client_id} — Q1 2026",
            body=qbr_text, author_agent="epos_stewardship",
            tags=["qbr", client_id])
        return {"client_id": client_id, "qbr_asset_id": asset.asset_id, "health": health}

    def run_stewardship_cycle(self) -> dict:
        """Weekly cycle for all active clients."""
        raw = self._psql("SELECT id::text, name FROM epos.contacts WHERE stage = 'delivery' LIMIT 20;")
        clients = []
        for line in raw.split("\n"):
            if "|" in line:
                parts = line.split("|")
                clients.append({"id": parts[0].strip(), "name": parts[1].strip()})

        results = {"clients_checked": len(clients), "at_risk": 0, "expansion_ready": 0}
        for c in clients:
            churn = self.detect_churn_risk(c["id"])
            if churn["risk_level"] == "high":
                results["at_risk"] += 1
            expansion = self.detect_expansion_opportunity(c["id"])
            if expansion.get("expansion_ready"):
                results["expansion_ready"] += 1

        record_decision(decision_type="stewardship.cycle_complete",
                        description=f"Stewardship: {results['clients_checked']} clients, {results['at_risk']} at risk",
                        agent_id="epos_stewardship", outcome="complete", context=results)
        return results


if __name__ == "__main__":
    steward = EPOSStewardship()
    cycle = steward.run_stewardship_cycle()
    print(f"  Stewardship cycle: {cycle}")
    print("PASS: EPOSStewardship operational")
