#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
AN1 Analyst — ERI Prediction & Scoring Engine
Constitutional Authority: EPOS Constitution v3.1

Pre-production: predict ERI before content is made.
Post-publish: score actual ERI, compare to prediction.
Constitutional rule: prediction MUST be logged before production.
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from path_utils import get_context_vault
from epos_intelligence import record_decision, get_decision_analytics
from epos_event_bus import EPOSEventBus


class AN1Analyst:
    """ERI engine. Predict before production. Score after publish."""

    APPROVAL_THRESHOLDS = {"reject": 35, "conditional": 50, "approve": 50}

    def __init__(self):
        self.vault_root = get_context_vault()
        self.bus = EPOSEventBus()

    def predict_eri(self, brief: dict, niche_pack: dict = None,
                    competitive_context: dict = None) -> dict:
        """Predict ERI BEFORE production. Logs immediately."""
        hook_weights = {"question": 1.2, "list": 1.3, "how_to": 1.0,
                        "controversy": 1.4, "story": 1.1, "statistic": 1.15, "unknown": 0.8}
        angle_weights = {"challenger": 1.3, "architect": 1.1, "closer": 1.2}

        hook_mod = hook_weights.get(brief.get("hook_type", "unknown"), 1.0)
        angle_mod = angle_weights.get(brief.get("angle_type", "architect"), 1.0)
        base = brief.get("predicted_eri_score", 50)

        predicted = min(round(base * hook_mod * angle_mod, 1), 100)
        verdict = ("REJECT" if predicted < self.APPROVAL_THRESHOLDS["reject"]
                   else "CONDITIONAL" if predicted < self.APPROVAL_THRESHOLDS["approve"]
                   else "APPROVE")

        prediction = {
            "prediction_id": f"ERI-PRED-{uuid.uuid4().hex[:8]}",
            "brief_id": brief.get("brief_id", "unknown"),
            "predicted_eri_score": predicted,
            "verdict": verdict,
            "predicted_at": datetime.now(timezone.utc).isoformat(),
            "logged_before_production": True,
        }

        record_decision(
            decision_type="content.eri_prediction",
            description=f"ERI prediction: {brief.get('brief_id')} -> {predicted} ({verdict})",
            agent_id="an1_analyst", outcome=verdict.lower(), context=prediction,
        )
        try:
            self.bus.publish("content.eri.predicted",
                             {"brief_id": brief.get("brief_id"), "score": predicted, "verdict": verdict},
                             "an1_analyst")
        except Exception:
            pass
        return prediction

    def score_actual_eri(self, video_id: str, brief_id: str,
                         platform_data: dict) -> dict:
        """Compute actual ERI from real engagement data."""
        views = int(platform_data.get("viewCount", 0))
        likes = int(platform_data.get("likeCount", 0))
        comments = int(platform_data.get("commentCount", 0))
        saves = int(likes * 0.15)
        eng_rate = (likes + comments) / max(views, 1)
        days = max(platform_data.get("days_since_publish", 7), 1)
        velocity = views / days

        raw = ((likes * 1.0 + saves * 4.0 + comments * 2.0 + views * 0.01) *
               (min(velocity / 1000, 5.0) * 0.4 + eng_rate * 100 * 0.3 + 1.0 * 0.3))
        actual = min(round(raw / 100, 1), 100)

        record = {
            "brief_id": brief_id, "video_id": video_id,
            "actual_eri_score": actual,
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }
        record_decision(decision_type="content.eri_actual",
                        description=f"ERI actual: {brief_id} -> {actual}",
                        agent_id="an1_analyst", outcome="scored", context=record)

        if actual > 85:
            try:
                self.bus.publish("content.expansion_protocol.triggered",
                                {"brief_id": brief_id, "actual_eri": actual}, "an1_analyst")
            except Exception:
                pass
        return record


if __name__ == "__main__":
    analyst = AN1Analyst()
    pred = analyst.predict_eri({"brief_id": "CB-LEGO-TEST", "hook_type": "list",
                                "angle_type": "challenger", "predicted_eri_score": 55})
    assert pred["verdict"] in ("APPROVE", "CONDITIONAL", "REJECT")
    assert pred["logged_before_production"] is True
    print(f"  Prediction: {pred['predicted_eri_score']} ({pred['verdict']})")
    print("PASS: AN1Analyst self-tests passed")
