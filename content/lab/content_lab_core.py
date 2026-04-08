#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
ContentLab Core — C10 Coordinator
Constitutional Authority: EPOS Constitution v3.1

Single entry point for production requests.
Sequences: R1 -> AN1(predict) -> A1 -> V1 -> M1 -> AN1(score)
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision


class ContentLab:
    """C10 coordinator. Sequences all nodes. Single entry point."""

    def __init__(self):
        self.vault_root = get_context_vault()
        self.bus = EPOSEventBus()

    def get_status(self) -> dict:
        """Current production state from event bus."""
        recent = self.bus.get_recent(minutes=1440)  # last 24h
        return {
            "sparks_created": len([e for e in recent if e.event_type == "content.spark.created"]),
            "eri_predictions": len([e for e in recent if e.event_type == "content.eri.predicted"]),
            "scripts_generated": len([e for e in recent if e.event_type == "content.script.generated"]),
            "validations_passed": len([e for e in recent if "governance.validation.pass" in e.event_type]),
            "assets_scheduled": len([e for e in recent if e.event_type == "content.scheduled"]),
            "cascades_released": len([e for e in recent if e.event_type == "content.cascade.released"]),
            "total_events_24h": len(recent),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def run_production_cycle(self, brief_id: str = None,
                              spark_id: str = None) -> dict:
        """
        Full production loop. Input: brief_id or spark_id.
        Each node publishes to event bus before next runs.
        Returns status dict with all proof artifacts.
        """
        from content.lab.nodes.r1_radar import R1Radar
        from content.lab.nodes.an1_analyst import AN1Analyst
        from content_lab_producer import ContentLabProducer
        from content.lab.nodes.v1_validation_engine import V1ValidationEngine
        from content.lab.nodes.m1_marshall import M1Marshall

        trace_id = f"PROD-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        result = {"trace_id": trace_id, "stages": {}, "status": "in_progress"}

        try:
            # Stage 1: If spark_id, find it; if brief_id, load brief
            if brief_id:
                brief_path = self.vault_root / "missions" / "lego_affiliate" / f"{brief_id}.json"
                if not brief_path.exists():
                    result["status"] = "failed"
                    result["error"] = f"Brief not found: {brief_id}"
                    return result
                brief = json.loads(brief_path.read_text(encoding="utf-8"))
            else:
                result["status"] = "failed"
                result["error"] = "brief_id required"
                return result

            # Stage 2: AN1 predict
            analyst = AN1Analyst()
            prediction = analyst.predict_eri(brief)
            result["stages"]["an1_predict"] = prediction

            if prediction["verdict"] == "REJECT":
                result["status"] = "rejected"
                result["reason"] = f"ERI prediction {prediction['predicted_eri_score']} below threshold"
                return result

            # Stage 3: A1 Architect (produce script)
            producer = ContentLabProducer()
            script_result = producer.generate_script(brief_path)
            result["stages"]["a1_produce"] = script_result

            # Stage 4: V1 Validate
            validator = V1ValidationEngine()
            script_data = {
                "brief_id": brief_id,
                "script_text": Path(script_result["script_path"]).read_text(encoding="utf-8"),
                "description": Path(script_result["description_path"]).read_text(encoding="utf-8"),
            }
            receipt = validator.validate_script(script_data, "lego_affiliate", is_affiliate=True)
            result["stages"]["v1_validate"] = receipt

            if receipt["verdict"] == "FAIL":
                result["status"] = "validation_failed"
                result["failed_checks"] = receipt["failed_checks"]
                return result

            # Stage 5: M1 Schedule
            marshall = M1Marshall()
            schedule = marshall.generate_week_schedule(
                "lego_affiliate", 1,
                [{"asset_id": brief_id, "validated": True}]
            )
            result["stages"]["m1_schedule"] = {"asset_count": len(schedule["assets"])}

            result["status"] = "complete"
            record_decision(
                decision_type="content.production_cycle_complete",
                description=f"Production cycle complete for {brief_id}",
                agent_id="content_lab", outcome="success",
                context={"trace_id": trace_id, "brief_id": brief_id},
            )

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result


if __name__ == "__main__":
    lab = ContentLab()
    status = lab.get_status()
    assert isinstance(status, dict)
    assert "sparks_created" in status
    print(f"  Content Lab status:")
    for k, v in status.items():
        if k != "checked_at":
            print(f"    {k}: {v}")
    print("PASS: ContentLab status check passed")
