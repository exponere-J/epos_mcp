# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/content/lab/automation/publish_orchestrator.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
EPOS Content Lab - Publish Orchestrator (Node M1 - Marshall)
Component: C10_CONTENT_LAB / Automation
Path: epos_mcp/content/lab/automation/publish_orchestrator.py

Multi-platform publishing with staggered saturation.

PERMISSION GATES:
  - Reading publish queue: AUTONOMOUS
  - Scheduling posts: AUTONOMOUS (internal scheduling only)
  - ACTUAL EXTERNAL PUBLISHING: GATED
    - Auto-approved if validation score >= 85 AND source echolocation score >= 85
    - Otherwise requires human approval
  - Deleting published content: GATED (human only)
  - Rate limit override: GATED (human only)

Uses BrowserUse or platform APIs when available.
Falls back to generating ready-to-paste content files when APIs are unavailable.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path


EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
CONTENT_LAB = EPOS_ROOT / "content" / "lab"
VAULT_PATH = EPOS_ROOT / "context_vault"
EVENT_LOG = VAULT_PATH / "events" / "system_events.jsonl"

PUBLISH_QUEUE = CONTENT_LAB / "publish_queue"
PUBLISHED = CONTENT_LAB / "published"
READY_TO_POST = CONTENT_LAB / "ready_to_post"  # Fallback: human-pasteable files
SCHEDULE_LOG = CONTENT_LAB / "intelligence" / "publish_schedule.jsonl"

# Stagger configuration (minutes between posts per platform)
STAGGER_MINUTES = {
    "x": 90,
    "linkedin": 240,
    "tiktok": 120,
    "youtube": 480,
    "instagram": 180,
}

# Daily limits per platform (constitutional: avoid spam/shadowban)
DAILY_LIMITS = {
    "x": 10,
    "linkedin": 3,
    "tiktok": 5,
    "youtube": 2,
    "instagram": 5,
}

# Auto-publish threshold
AUTO_PUBLISH_THRESHOLD = 85


class PublishOrchestrator:
    """
    Manages multi-platform content distribution.

    For Hell Week: generates ready-to-post files since API integrations
    are not yet live. Once BrowserUse is connected, this orchestrator
    will drive actual posting through Agent Zero.
    """

    def __init__(self):
        self._ensure_directories()
        self._daily_counts = {}

    def _ensure_directories(self):
        for d in [PUBLISH_QUEUE, PUBLISHED, READY_TO_POST, SCHEDULE_LOG.parent]:
            d.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        """
        Process publish queue and generate scheduled outputs.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        results = {
            "worker": "publish_orchestrator",
            "run_timestamp": timestamp,
            "queued": 0,
            "scheduled": 0,
            "auto_approved": 0,
            "needs_human_approval": 0,
            "rate_limited": 0,
            "errors": [],
        }

        queue_files = sorted(PUBLISH_QUEUE.glob("*.json"))
        results["queued"] = len(queue_files)

        for qf in queue_files:
            try:
                with open(qf, "r", encoding="utf-8") as f:
                    content = json.load(f)

                platform = self._infer_platform(content)
                content_id = content.get("derivative_id", content.get("content_id", qf.stem))

                # Rate limit check
                if self._is_rate_limited(platform):
                    results["rate_limited"] += 1
                    continue

                # Permission gate check
                val_score = content.get("_validation", {}).get("score", 0)
                echo_score = content.get("_echolocation", {}).get("score", 0)
                auto_approved = val_score >= AUTO_PUBLISH_THRESHOLD and echo_score >= AUTO_PUBLISH_THRESHOLD

                if auto_approved:
                    results["auto_approved"] += 1
                else:
                    results["needs_human_approval"] += 1

                # Generate the ready-to-post file
                post = self._format_for_platform(content, platform)
                post["auto_approved"] = auto_approved
                post["permission_status"] = "approved" if auto_approved else "AWAITING_HUMAN_APPROVAL"
                post["scheduled_time"] = self._next_slot(platform)

                # Write to ready_to_post
                platform_dir = READY_TO_POST / platform
                platform_dir.mkdir(parents=True, exist_ok=True)
                out_file = platform_dir / f"{content_id}.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(post, f, indent=2)

                # Log schedule
                self._log_schedule(content_id, platform, post["scheduled_time"], auto_approved)

                # Move from queue to published tracking
                published_file = PUBLISHED / qf.name
                qf.rename(published_file)

                results["scheduled"] += 1
                self._increment_daily_count(platform)

            except Exception as e:
                results["errors"].append({"file": str(qf), "error": str(e)})

        self._emit_event("publish.batch.completed", {
            "scheduled": results["scheduled"],
            "auto_approved": results["auto_approved"],
            "needs_approval": results["needs_human_approval"],
        }, timestamp)

        return results

    def _infer_platform(self, content: dict) -> str:
        # Try explicit platform field first
        if "platform" in content:
            return content["platform"]
        # Infer from derivative type
        dtype = content.get("type", "")
        mapping = {
            "youtube_short": "youtube", "linkedin_post": "linkedin",
            "x_thread": "x", "instagram_carousel": "instagram",
            "tiktok_script": "tiktok", "newsletter_section": "email",
        }
        return mapping.get(dtype, "x")

    def _is_rate_limited(self, platform: str) -> bool:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{platform}_{today}"
        count = self._daily_counts.get(key, 0)
        return count >= DAILY_LIMITS.get(platform, 5)

    def _increment_daily_count(self, platform: str):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{platform}_{today}"
        self._daily_counts[key] = self._daily_counts.get(key, 0) + 1

    def _next_slot(self, platform: str) -> str:
        stagger = STAGGER_MINUTES.get(platform, 120)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{platform}_{today}"
        count = self._daily_counts.get(key, 0)
        base = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
        slot = base + timedelta(minutes=stagger * count)
        return slot.isoformat()

    def _format_for_platform(self, content: dict, platform: str) -> dict:
        """Format content into platform-ready structure."""
        spec = content.get("content_spec", {})
        text = ""
        if isinstance(spec, dict):
            text = spec.get("text", spec.get("text_excerpt", spec.get("hook", "")))
        elif isinstance(spec, str):
            text = spec

        return {
            "content_id": content.get("derivative_id", content.get("content_id", "unknown")),
            "platform": platform,
            "type": content.get("type", "post"),
            "text": text,
            "source_attribution": content.get("source_attribution", ""),
            "cta_token": "CTA-CONTENT-LAB-CASCADE",
            "format": content.get("format", "text"),
        }

    def _log_schedule(self, content_id: str, platform: str, scheduled: str, auto: bool):
        entry = {
            "content_id": content_id, "platform": platform,
            "scheduled_time": scheduled, "auto_approved": auto,
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with open(SCHEDULE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass

    def _emit_event(self, event_type: str, payload: dict, timestamp: str):
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        event = {"event_type": event_type, "payload": payload,
                 "timestamp": timestamp, "source": "publish_orchestrator"}
        try:
            with open(EVENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass


def health_check() -> dict:
    checks = {
        "orchestrator_importable": True,
        "publish_queue_exists": PUBLISH_QUEUE.exists(),
        "ready_to_post_exists": READY_TO_POST.exists(),
    }
    return {"component": "publish_orchestrator", "status": "healthy" if all(checks.values()) else "degraded", "checks": checks}


if __name__ == "__main__":
    orch = PublishOrchestrator()
    results = orch.run()
    print(json.dumps(results, indent=2))
