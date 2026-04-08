# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/content/lab/automation/tributary_worker.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
EPOS Content Lab - Tributary Worker (Radar + Analyst automation)
Component: C10_CONTENT_LAB / Automation
Path: epos_mcp/content/lab/automation/tributary_worker.py

Automated pipeline:
  1. Scan captured content in tributaries/x/captured and tributaries/tiktok/captured
  2. Run echolocation scoring on each
  3. Route high-scoring content to cascade or production
  4. Log all decisions

PERMISSION GATES:
  - Publishing: GATED (requires human approval or brand validation pass)
  - Scoring: AUTONOMOUS (let lil Essa walk)
  - Archiving: AUTONOMOUS
  - Expansion triggers (score > 85): GATED (notifies human)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Sibling imports (adjust if running from different working directory)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tributaries.echolocation_algorithm import EcholocationAlgorithm
from validation.brand_validator import BrandValidator


EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent.parent)))
CONTENT_LAB = EPOS_ROOT / "content" / "lab"
VAULT_PATH = EPOS_ROOT / "context_vault"
EVENT_LOG = VAULT_PATH / "events" / "system_events.jsonl"

# Directories
CAPTURED_X = CONTENT_LAB / "tributaries" / "x" / "captured"
CAPTURED_TIKTOK = CONTENT_LAB / "tributaries" / "tiktok" / "captured"
PRODUCTION = CONTENT_LAB / "production"
ARCHIVE = CONTENT_LAB / "archive"
EXPANSION_QUEUE = CONTENT_LAB / "expansion_queue"


class TributaryWorker:
    """
    Automated worker that processes captured tributary content.

    Runs as a scheduled task or on-demand mission.
    Fully autonomous for scoring and archiving.
    Permission-gated for publishing and expansion.
    """

    def __init__(self):
        self.algo = EcholocationAlgorithm()
        self.validator = BrandValidator()
        self._ensure_directories()

    def _ensure_directories(self):
        """Create required directories if they don't exist."""
        for d in [CAPTURED_X, CAPTURED_TIKTOK, PRODUCTION, ARCHIVE, EXPANSION_QUEUE]:
            d.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        """
        Execute the full tributary processing pipeline.

        Returns summary of actions taken.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        results = {
            "worker": "tributary_worker",
            "run_timestamp": timestamp,
            "processed": [],
            "promoted": [],
            "archived": [],
            "expansion_flagged": [],
            "errors": [],
        }

        # Process X captures
        for file_path in self._scan_captured(CAPTURED_X, "x"):
            try:
                outcome = self._process_capture(file_path, "x")
                results["processed"].append(outcome)
                if outcome["action"] == "expand":
                    results["expansion_flagged"].append(outcome)
                elif outcome["action"] == "promote":
                    results["promoted"].append(outcome)
                elif outcome["action"] == "kill":
                    results["archived"].append(outcome)
            except Exception as e:
                results["errors"].append({"file": str(file_path), "error": str(e)})

        # Process TikTok captures
        for file_path in self._scan_captured(CAPTURED_TIKTOK, "tiktok"):
            try:
                outcome = self._process_capture(file_path, "tiktok")
                results["processed"].append(outcome)
                if outcome["action"] == "expand":
                    results["expansion_flagged"].append(outcome)
                elif outcome["action"] == "promote":
                    results["promoted"].append(outcome)
                elif outcome["action"] == "kill":
                    results["archived"].append(outcome)
            except Exception as e:
                results["errors"].append({"file": str(file_path), "error": str(e)})

        # Summary
        results["summary"] = {
            "total_processed": len(results["processed"]),
            "promoted": len(results["promoted"]),
            "archived": len(results["archived"]),
            "expansion_flagged": len(results["expansion_flagged"]),
            "errors": len(results["errors"]),
        }

        self._emit_event("tributary.batch.completed", results["summary"], timestamp)
        return results

    def _scan_captured(self, directory: Path, platform: str) -> list[Path]:
        """Scan a captured directory for unprocessed JSON files."""
        if not directory.exists():
            return []
        return sorted(directory.glob("*.json"))

    def _process_capture(self, file_path: Path, platform: str) -> dict:
        """Process a single captured content file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content_data = json.load(f)

        content_data["platform"] = platform
        if "content_id" not in content_data:
            content_data["content_id"] = file_path.stem

        # AUTONOMOUS: Score it
        echo_result = self.algo.analyze(content_data)
        action = echo_result["action"]

        # Route based on action
        if action == "expand":
            # PERMISSION GATE: flag for human review, do not auto-execute
            dest = EXPANSION_QUEUE / file_path.name
            self._move_with_metadata(file_path, dest, echo_result)
            self._emit_event("tributary.expansion.flagged", {
                "content_id": echo_result["content_id"],
                "score": echo_result["score"],
                "REQUIRES_HUMAN_APPROVAL": True,
            }, echo_result["timestamp"])

        elif action == "promote":
            # AUTONOMOUS: move to production queue (still needs brand validation before publish)
            dest = PRODUCTION / file_path.name
            self._move_with_metadata(file_path, dest, echo_result)

        elif action == "kill":
            # AUTONOMOUS: archive
            dest = ARCHIVE / file_path.name
            self._move_with_metadata(file_path, dest, echo_result)

        else:
            # hold: leave in place, will re-process next run
            pass

        return {
            "content_id": echo_result["content_id"],
            "score": echo_result["score"],
            "action": action,
            "file": str(file_path.name),
        }

    def _move_with_metadata(self, src: Path, dest: Path, echo_result: dict):
        """Move file and attach echolocation metadata."""
        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["_echolocation"] = {
            "score": echo_result["score"],
            "action": echo_result["action"],
            "components": echo_result["components"],
            "transformations": echo_result["transformations"],
            "scored_at": echo_result["timestamp"],
        }

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Remove from captured
        try:
            src.unlink()
        except OSError:
            pass

    def _emit_event(self, event_type: str, payload: dict, timestamp: str):
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": timestamp,
            "source": "tributary_worker",
        }
        try:
            with open(EVENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass


def health_check() -> dict:
    checks = {
        "worker_importable": True,
        "captured_x_exists": CAPTURED_X.exists(),
        "captured_tiktok_exists": CAPTURED_TIKTOK.exists(),
        "production_exists": PRODUCTION.exists(),
        "archive_exists": ARCHIVE.exists(),
    }
    return {"component": "tributary_worker", "status": "healthy" if all(checks.values()) else "degraded", "checks": checks}


if __name__ == "__main__":
    worker = TributaryWorker()
    results = worker.run()
    print(json.dumps(results, indent=2))
