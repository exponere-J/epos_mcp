#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_advocacy.py — Advocacy Engine
====================================
Constitutional Authority: EPOS Constitution v3.1

Referral detection, case study pipeline, NPS capture.
Satisfied clients become the most efficient lead source.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from epos_cms import EPOSContentManagement
from path_utils import get_context_vault


class EPOSAdvocacy:
    """Referral activation, case study generation, NPS tracking."""

    def __init__(self):
        self.bus = EPOSEventBus()
        self.vault = get_context_vault()
        self.cms = EPOSContentManagement()

    def capture_nps(self, client_id: str, score: int, comment: str = "") -> dict:
        """NPS 0-10. Promoter (9-10) triggers referral. Detractor (0-6) triggers alert."""
        category = "promoter" if score >= 9 else "passive" if score >= 7 else "detractor"

        result = {"client_id": client_id, "nps_score": score,
                  "category": category, "comment": comment,
                  "captured_at": datetime.now(timezone.utc).isoformat()}

        record_decision(decision_type="advocacy.nps_captured",
                        description=f"NPS {score} ({category}) from {client_id}",
                        agent_id="epos_advocacy", outcome=category, context=result)

        if category == "promoter":
            self._trigger_referral_sequence(client_id)
        elif category == "detractor":
            try:
                self.bus.publish("client.detractor_alert",
                                 {"client_id": client_id, "nps": score, "comment": comment},
                                 "epos_advocacy")
            except Exception:
                pass

        return result

    def _trigger_referral_sequence(self, client_id: str) -> None:
        record_decision(decision_type="advocacy.referral_sequence_triggered",
                        description=f"Referral sequence for promoter {client_id}",
                        agent_id="epos_advocacy", outcome="triggered",
                        context={"client_id": client_id})

    def generate_referral_ask(self, client_id: str) -> str:
        from groq_router import GroqRouter
        router = GroqRouter()
        prompt = f"""Write a personal referral ask message for a satisfied client.
Client ID: {client_id}. They are a promoter (NPS 9-10).
Keep it warm, specific, and under 100 words. Include a referral link placeholder.
Voice: grateful, direct, professional."""
        return router.route("scripting", prompt, max_tokens=200)

    def build_case_study_brief(self, client_id: str) -> dict:
        from groq_router import GroqRouter
        router = GroqRouter()

        prompt = f"""Generate a case study brief for client {client_id}.
Structure: Challenge (before EPOS), Solution (what we did), Results (measurable outcomes).
200 words. Professional. Specific where possible."""
        brief_text = router.route("reasoning", prompt, max_tokens=400)

        asset = self.cms.create_asset(
            asset_type="case_study",
            title=f"Case Study Brief — {client_id}",
            body=brief_text, author_agent="epos_advocacy",
            tags=["case_study", client_id])

        record_decision(decision_type="advocacy.case_study_brief_generated",
                        description=f"Case study brief for {client_id}",
                        agent_id="epos_advocacy", outcome="draft",
                        context={"asset_id": asset.asset_id})
        return {"client_id": client_id, "asset_id": asset.asset_id, "status": "draft"}

    def track_referral(self, referral_token: str, new_lead_id: str) -> dict:
        result = {"referral_token": referral_token, "new_lead_id": new_lead_id,
                  "tracked_at": datetime.now(timezone.utc).isoformat()}
        record_decision(decision_type="advocacy.referral_converted",
                        description=f"Referral converted: {referral_token} → {new_lead_id}",
                        agent_id="epos_advocacy", outcome="converted", context=result)
        return result


if __name__ == "__main__":
    adv = EPOSAdvocacy()
    nps = adv.capture_nps("pgp_orlando", 9, "Great service, would recommend")
    assert nps["category"] == "promoter"
    print(f"  NPS captured: {nps['nps_score']} ({nps['category']})")

    brief = adv.build_case_study_brief("pgp_orlando")
    assert brief["status"] == "draft"
    print(f"  Case study brief: {brief['asset_id']}")
    print("PASS: EPOSAdvocacy operational")
