# EPOS GOVERNANCE WATERMARK
"""
EPOS Content Lab - Cascade Worker (Marshall automation)
Component: C10_CONTENT_LAB / Automation
Path: epos_mcp/content/lab/automation/cascade_worker.py

Automated pipeline:
  1. Scan long-form sources (YouTube transcripts, LinkedIn articles)
  2. Check stabilization period (24hr constitutional requirement)
  3. Generate derivatives via CascadeOptimizer
  4. Run brand validation on each derivative
  5. Route validated derivatives to publish queue

PERMISSION GATES:
  - Derivative generation: AUTONOMOUS
  - Brand validation: AUTONOMOUS
  - Publishing to external platforms: GATED (requires approval or auto-pass score >= 85)
  - Overriding stabilization period: GATED (human only)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cascades.cascade_optimizer import CascadeOptimizer
from validation.brand_validator import BrandValidator


EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
CONTENT_LAB = EPOS_ROOT / "content" / "lab"
VAULT_PATH = EPOS_ROOT / "context_vault"
EVENT_LOG = VAULT_PATH / "events" / "system_events.jsonl"

# Directories
SOURCES_YT = CONTENT_LAB / "cascades" / "youtube" / "sources"
SOURCES_LI = CONTENT_LAB / "cascades" / "linkedin" / "sources"
DERIVATIVES = CONTENT_LAB / "cascades" / "derivatives"
PUBLISH_QUEUE = CONTENT_LAB / "publish_queue"
VALIDATION_FAILURES = CONTENT_LAB / "validation_failures"

# Auto-publish threshold: derivatives from sources scoring this high skip human gate
AUTO_PUBLISH_SCORE = 85


class CascadeWorker:
    """
    Automated worker that processes long-form sources into derivatives.
    """

    def __init__(self):
        self.optimizer = CascadeOptimizer()
        self.validator = BrandValidator()
        self._ensure_directories()

    def _ensure_directories(self):
        for d in [SOURCES_YT, SOURCES_LI, DERIVATIVES, PUBLISH_QUEUE, VALIDATION_FAILURES]:
            d.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        results = {
            "worker": "cascade_worker",
            "run_timestamp": timestamp,
            "sources_processed": 0,
            "derivatives_generated": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "auto_publish_queued": 0,
            "human_review_queued": 0,
            "stabilization_blocked": 0,
            "errors": [],
        }

        # Process YouTube sources
        for source_file in sorted(SOURCES_YT.glob("*.json")):
            self._process_source(source_file, "youtube", results)

        # Process LinkedIn sources
        for source_file in sorted(SOURCES_LI.glob("*.json")):
            self._process_source(source_file, "linkedin_article", results)

        self._emit_event("cascade.batch.completed", {
            "sources": results["sources_processed"],
            "derivatives": results["derivatives_generated"],
            "validated": results["validation_passed"],
        }, timestamp)

        return results

    def _process_source(self, source_file: Path, source_type: str, results: dict):
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                source_data = json.load(f)

            source_data["source_type"] = source_type
            if "source_id" not in source_data:
                source_data["source_id"] = source_file.stem

            # Generate derivatives
            cascade_result = self.optimizer.generate_derivatives(source_data)
            results["sources_processed"] += 1

            if not cascade_result["stabilization_ok"]:
                results["stabilization_blocked"] += 1
                return  # Leave source in place, will retry next run

            # Validate and route each derivative
            for deriv in cascade_result["derivatives"]:
                results["derivatives_generated"] += 1

                # Build validation payload
                val_content = {
                    "content_id": deriv["derivative_id"],
                    "platform": self._infer_platform(deriv["type"]),
                    "text": self._extract_text(deriv),
                    "cta_token": "CTA-CONTENT-LAB-CASCADE",
                    "is_derivative": True,
                    "source_attribution": deriv["source_attribution"],
                }

                val_result = self.validator.validate(val_content)

                if val_result["passed"]:
                    results["validation_passed"] += 1

                    # Write derivative to appropriate queue
                    deriv["_validation"] = val_result
                    deriv_file = DERIVATIVES / f"{deriv['derivative_id']}.json"
                    with open(deriv_file, "w", encoding="utf-8") as f:
                        json.dump(deriv, f, indent=2)

                    # Auto-publish gate check
                    source_score = source_data.get("_echolocation", {}).get("score", 0)
                    if source_score >= AUTO_PUBLISH_SCORE:
                        # AUTONOMOUS: high-confidence source, auto-queue
                        pub_file = PUBLISH_QUEUE / f"{deriv['derivative_id']}.json"
                        with open(pub_file, "w", encoding="utf-8") as f:
                            json.dump(deriv, f, indent=2)
                        results["auto_publish_queued"] += 1
                    else:
                        # PERMISSION GATE: needs human review before publish
                        results["human_review_queued"] += 1

                else:
                    results["validation_failed"] += 1
                    fail_file = VALIDATION_FAILURES / f"{deriv['derivative_id']}.json"
                    deriv["_validation"] = val_result
                    with open(fail_file, "w", encoding="utf-8") as f:
                        json.dump(deriv, f, indent=2)

            # Move processed source to avoid reprocessing
            processed_dir = source_file.parent / "processed"
            processed_dir.mkdir(exist_ok=True)
            source_file.rename(processed_dir / source_file.name)

        except Exception as e:
            results["errors"].append({"file": str(source_file), "error": str(e)})

    def _infer_platform(self, derivative_type: str) -> str:
        mapping = {
            "youtube_short": "youtube",
            "linkedin_post": "linkedin",
            "x_thread": "x",
            "instagram_carousel": "instagram",
            "tiktok_script": "tiktok",
            "newsletter_section": "email",
            "email_excerpt": "email",
        }
        return mapping.get(derivative_type, "x")

    def _extract_text(self, deriv: dict) -> str:
        spec = deriv.get("content_spec", {})
        if isinstance(spec, dict):
            return spec.get("text", spec.get("text_excerpt", spec.get("hook", "")))
        return str(spec)[:500]

    def _emit_event(self, event_type: str, payload: dict, timestamp: str):
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        event = {"event_type": event_type, "payload": payload,
                 "timestamp": timestamp, "source": "cascade_worker"}
        try:
            with open(EVENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass


def health_check() -> dict:
    checks = {
        "worker_importable": True,
        "sources_yt_exists": SOURCES_YT.exists(),
        "sources_li_exists": SOURCES_LI.exists(),
        "derivatives_exists": DERIVATIVES.exists(),
        "publish_queue_exists": PUBLISH_QUEUE.exists(),
    }
    return {"component": "cascade_worker", "status": "healthy" if all(checks.values()) else "degraded", "checks": checks}


if __name__ == "__main__":
    worker = CascadeWorker()
    results = worker.run()
    print(json.dumps(results, indent=2))
