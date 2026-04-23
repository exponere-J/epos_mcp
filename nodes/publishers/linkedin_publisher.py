#!/usr/bin/env python3
# EPOS Artifact — BUILD 80 (LinkedIn Publisher)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XVI §2, §3
"""
linkedin_publisher.py — Post + monitor LinkedIn via execution arm

Uses the BrowserUse (headed or headless) arm to:
  - Publish a post to LinkedIn
  - Monitor engagement (likes/comments/shares) over 24/48h windows
  - Parse comments into CCP → route to PM surface

Path:
  nodes.execution_arm.execute(task, mode_hint="browser_use.headed", context={
      "linkedin_session_state": "/mnt/c/.../state.json",
      "deletion_approved": [],  # never approved for posts
  })

LinkedIn requires an authenticated session. We use a stored
storage_state.json obtained from a one-time Sovereign-supervised login,
same pattern as notebooklm-py. The state file lives at
context_vault/secrets/linkedin_state.json (gitignored).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
POSTS_LOG = Path(os.getenv("EPOS_LINKEDIN_LOG",
                             str(REPO / "context_vault" / "publishers" / "linkedin.jsonl")))
POSTS_LOG.parent.mkdir(parents=True, exist_ok=True)

SESSION_STATE = os.getenv(
    "LINKEDIN_SESSION_STATE",
    str(REPO / "context_vault" / "secrets" / "linkedin_state.json"),
)


@dataclass
class PostRequest:
    body: str
    hashtags: list[str]
    media_paths: list[str]
    schedule_for: str | None = None   # ISO timestamp; None = post now
    mode_hint: str = "browser_use.headed"


class LinkedInPublisher:
    def post(self, req: PostRequest, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = {**(context or {}), "mission_id": f"linkedin_post_{int(datetime.now().timestamp())}"}
        ctx["linkedin_session_state"] = SESSION_STATE
        task = self._compose_task(req)
        try:
            from nodes.execution_arm import execute
            result = execute(task=task, mode_hint=req.mode_hint,
                              max_steps=8, context=ctx)
        except Exception as e:
            result = {"success": False, "error": f"arm_unavailable: {e}"}

        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "body_preview": req.body[:100],
            "hashtags": req.hashtags,
            "media_count": len(req.media_paths),
            "scheduled_for": req.schedule_for,
            "result": result,
        }
        with POSTS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec

    def monitor(self, post_url: str, window_hours: int = 24) -> dict[str, Any]:
        """Scrape post engagement at T+window_hours."""
        task = (
            f"Navigate to {post_url}. Report the current like count, "
            f"comment count, share count, and the text of the top 5 comments. "
            f"Return structured JSON."
        )
        try:
            from nodes.execution_arm import execute
            result = execute(task=task, mode_hint="browser_use.headless",
                              max_steps=5, context={
                                  "linkedin_session_state": SESSION_STATE,
                              })
        except Exception as e:
            result = {"success": False, "error": f"arm_unavailable: {e}"}
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": post_url, "window_hours": window_hours, "result": result,
        }
        with POSTS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": "monitor", **rec}, default=str) + "\n")
        return rec

    def _compose_task(self, req: PostRequest) -> str:
        tags = " ".join(f"#{t}" for t in req.hashtags) if req.hashtags else ""
        media = (f" Attach these media files: {', '.join(req.media_paths)}"
                  if req.media_paths else "")
        sched = (f" Schedule for {req.schedule_for}."
                  if req.schedule_for else " Post immediately.")
        return (
            f"Post to LinkedIn with the following body (keep exact formatting):\n\n"
            f"{req.body}\n\n{tags}{media}{sched}"
        )


def post(body: str, hashtags: list[str] | None = None,
         media_paths: list[str] | None = None,
         schedule_for: str | None = None,
         mode_hint: str = "browser_use.headed") -> dict[str, Any]:
    return LinkedInPublisher().post(
        PostRequest(body=body, hashtags=hashtags or [],
                     media_paths=media_paths or [],
                     schedule_for=schedule_for, mode_hint=mode_hint)
    )


if __name__ == "__main__":
    r = post(body="Test from EPOS LinkedIn Publisher.",
              hashtags=["epos", "test"], mode_hint="browser_use.headless")
    print(json.dumps(r, indent=2, default=str))
