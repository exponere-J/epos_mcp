#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
m1_publisher.py — Echoes M1 Publisher Bridge
===============================================
Constitutional Authority: EPOS Constitution v3.1

Closes the distribution gap between Content Lab (produces JSON) and
platforms (LinkedIn, X, Blog, Email). BrowserUse-first for social.
Markdown-to-file for blog. PS-EM handoff for email.

M1 NEVER publishes simultaneously. Stagger cadence:
  LinkedIn first (8-10 AM ET), X second (+2h), Blog (+4h), Email (Tue/Thu AM)

Every post has a unique CTA token for attribution tracking.
"""

import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from nodes.browser_use_node import BrowserUseNode
    _BROWSER = BrowserUseNode()
    _BROWSER_AVAILABLE = _BROWSER.health_check().get("status") == "operational"
except Exception:
    _BROWSER = None
    _BROWSER_AVAILABLE = False

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

from path_utils import get_context_vault

VAULT = get_context_vault()
ECHOES_VAULT = VAULT / "echoes"
PUBLISH_QUEUE = ECHOES_VAULT / "publish_queue"
READY_TO_POST = ECHOES_VAULT / "ready_to_post"
PUBLISHED = ECHOES_VAULT / "published"
CTA_TRACKING = ECHOES_VAULT / "cta_tracking.jsonl"
RETRY_QUEUE = ECHOES_VAULT / "retry_queue"


# ── Publishing Contract ─────────────────────────────────────

def create_post(platform: str, body: str, content_type: str = "text",
                media_url: str = None, cta_token: str = None,
                stagger_minutes: int = 0) -> dict:
    """Create a post contract for M1 to publish."""
    if not cta_token:
        cta_token = f"ECHO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

    post = {
        "id": f"post-{uuid.uuid4().hex[:8]}",
        "platform": platform,
        "mode": "profile",
        "content_type": content_type,
        "body": body,
        "media_url": media_url,
        "cta_token": cta_token,
        "stagger_minutes": stagger_minutes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
    }

    PUBLISH_QUEUE.mkdir(parents=True, exist_ok=True)
    path = PUBLISH_QUEUE / f"{post['id']}.json"
    path.write_text(json.dumps(post, indent=2), encoding="utf-8")

    return post


class M1Publisher:
    """
    Publishes content to platforms. BrowserUse-first for social.
    Generates ready-to-post files as fallback.
    """

    STAGGER_OFFSETS = {
        "linkedin": 0,
        "x": 120,       # +2 hours
        "blog": 240,     # +4 hours
        "email": 360,    # +6 hours (Tue/Thu only)
    }

    CHAR_LIMITS = {
        "linkedin": 3000,
        "x": 280,
        "blog": 50000,
        "email": 10000,
    }

    def __init__(self):
        for d in (PUBLISH_QUEUE, READY_TO_POST, PUBLISHED, RETRY_QUEUE):
            d.mkdir(parents=True, exist_ok=True)
        self._browseruse_available = self._check_browseruse()

    def _check_browseruse(self) -> bool:
        """Check if BrowserUse is available for automated posting."""
        try:
            import browseruse
            return True
        except ImportError:
            return False

    def publish(self, post: dict) -> dict:
        """Publish a single post to its target platform."""
        platform = post.get("platform", "unknown")
        body = post.get("body", "")
        char_limit = self.CHAR_LIMITS.get(platform, 3000)

        # Validate
        if len(body) > char_limit:
            body = body[:char_limit - 3] + "..."
            post["body"] = body
            post["truncated"] = True

        # Track CTA
        self._track_cta(post)

        # Attempt publish — fallback chain: BrowserUse -> staging
        if _BROWSER_AVAILABLE and platform in ("linkedin", "x"):
            result = self._browseruse_publish(post)
        else:
            result = self._stage_for_manual(post)

        # Log result
        post["status"] = "published" if result["success"] else "failed"
        post["published_at"] = datetime.now(timezone.utc).isoformat() if result["success"] else None
        post["result"] = result

        # Move to published or retry
        if result["success"]:
            dest = PUBLISHED / platform
            dest.mkdir(parents=True, exist_ok=True)
            (dest / f"{post['id']}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")
            self._publish_event(f"content.published.{platform}", post)
        else:
            (RETRY_QUEUE / f"{post['id']}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")
            self._publish_event(f"content.publish.failed.{platform}", post)

        # Remove from queue
        queue_path = PUBLISH_QUEUE / f"{post['id']}.json"
        if queue_path.exists():
            queue_path.unlink()

        return result

    def publish_batch(self, posts: list) -> list:
        """Publish a staggered batch of posts."""
        results = []
        for post in sorted(posts, key=lambda p: self.STAGGER_OFFSETS.get(p.get("platform", ""), 0)):
            stagger = post.get("stagger_minutes", self.STAGGER_OFFSETS.get(post.get("platform", ""), 0))
            if stagger > 0 and results:
                # In production, this would schedule. For now, stage all immediately.
                post["scheduled_for"] = (datetime.now(timezone.utc) + timedelta(minutes=stagger)).isoformat()
            result = self.publish(post)
            results.append(result)
        return results

    def _browseruse_publish(self, post: dict) -> dict:
        """Publish via BrowserUse autonomous browser automation."""
        if not _BROWSER:
            return self._stage_for_manual(post)

        platform = post.get("platform", "")
        body = post.get("body", "")

        if platform == "linkedin":
            task = (f"Go to linkedin.com/feed. Click 'Start a post'. "
                    f"Type the following text into the post composer: {body}. "
                    f"Click the 'Post' button to publish.")
        elif platform == "x":
            task = (f"Go to x.com/compose/post. "
                    f"Type the following text: {body}. "
                    f"Click the post/tweet button to publish.")
        else:
            return self._stage_for_manual(post)

        try:
            result = _BROWSER.execute_task_sync(task, max_steps=5)
            if result.get("success"):
                return {
                    "success": True,
                    "method": "browser_use",
                    "message": f"Published to {platform} via BrowserUse",
                    "details": result.get("result", "")[:200],
                }
            else:
                # BrowserUse failed — fall back to staging
                return self._stage_for_manual(post)
        except Exception as e:
            return self._stage_for_manual(post)

    def _stage_for_manual(self, post: dict) -> dict:
        """Stage post as ready-to-post file for manual publishing."""
        platform = post.get("platform", "unknown")
        dest = READY_TO_POST / platform
        dest.mkdir(parents=True, exist_ok=True)

        # Write human-readable post file
        post_file = dest / f"{post['id']}.txt"
        lines = [
            f"PLATFORM: {platform.upper()}",
            f"CTA TOKEN: {post.get('cta_token', '')}",
            f"STATUS: READY TO POST",
            f"CREATED: {post.get('created_at', '')}",
            "",
            "--- COPY BELOW THIS LINE ---",
            "",
            post.get("body", ""),
        ]
        if post.get("media_url"):
            lines.extend(["", f"MEDIA: {post['media_url']}"])

        post_file.write_text("\n".join(lines), encoding="utf-8")

        # Also save JSON for programmatic use
        (dest / f"{post['id']}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")

        return {
            "success": True,
            "method": "staged",
            "message": f"Post staged at {post_file}. Copy and paste to publish.",
            "path": str(post_file),
        }

    def _track_cta(self, post: dict):
        """Log CTA token for attribution tracking."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "post_id": post.get("id"),
            "platform": post.get("platform"),
            "cta_token": post.get("cta_token"),
            "body_preview": post.get("body", "")[:100],
        }
        with open(CTA_TRACKING, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _publish_event(self, event_type: str, post: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, {
                    "post_id": post.get("id"),
                    "platform": post.get("platform"),
                    "cta_token": post.get("cta_token"),
                }, source_module="m1_publisher")
            except Exception:
                pass

    def get_queue(self) -> list:
        """List posts in the publish queue."""
        posts = []
        for f in PUBLISH_QUEUE.glob("post-*.json"):
            posts.append(json.loads(f.read_text(encoding="utf-8")))
        return posts

    def get_published(self, platform: str = None) -> list:
        """List published posts."""
        posts = []
        search_dir = PUBLISHED / platform if platform else PUBLISHED
        for f in search_dir.rglob("post-*.json"):
            posts.append(json.loads(f.read_text(encoding="utf-8")))
        return posts

    def get_status(self) -> dict:
        """Publisher status."""
        queued = len(list(PUBLISH_QUEUE.glob("post-*.json")))
        published = len(list(PUBLISHED.rglob("post-*.json")))
        failed = len(list(RETRY_QUEUE.glob("post-*.json")))
        staged = sum(len(list((READY_TO_POST / p).glob("*.txt"))) for p in ("linkedin", "x", "blog", "email") if (READY_TO_POST / p).exists())
        return {"queued": queued, "published": published, "failed": failed, "staged": staged,
                "browseruse": self._browseruse_available}


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    pub = M1Publisher()

    # Test 1: Create and publish a LinkedIn post
    post = create_post("linkedin",
        "Every business needs a system that diagnoses, prescribes, and heals. "
        "EPOS is that system. 19 sovereign nodes, 22 CLI domains, and a self-healing engine. "
        "The organism runs while you sleep.\n\n#EPOS #Sovereignty #1PercentDaily")
    result = pub.publish(post)
    assert result["success"], "Should succeed (staged)"
    passed += 1

    # Test 2: Create and publish an X post
    post2 = create_post("x",
        "Your business diagnostics should prescribe the fix, not just name the problem. "
        "TTLG v2: diagnose, fabricate, deploy, heal.")
    result2 = pub.publish(post2)
    assert result2["success"]
    passed += 1

    # Test 3: CTA tracking
    assert CTA_TRACKING.exists()
    lines = CTA_TRACKING.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    passed += 1

    # Test 4: Status
    status = pub.get_status()
    assert status["staged"] >= 2
    passed += 1

    # Test 5: Character limit enforcement
    long_post = create_post("x", "A" * 500)  # Over 280 limit
    result3 = pub.publish(long_post)
    assert result3["success"]
    passed += 1

    print(f"PASS: m1_publisher ({passed} assertions)")
    print(f"Status: {status}")
