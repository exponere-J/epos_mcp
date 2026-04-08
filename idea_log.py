#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
idea_log.py — EPOS Idea Capture and Triage System
===================================================
Constitutional Authority: EPOS Constitution v3.1
Module: Idea Log (CODE DIRECTIVE Module 1)

Captures ideas instantly with minimal friction. Ideas flow through:
  Capture → Triage (Friday) → Research Brief → Build Queue

Vault journal: context_vault/ideas/idea_log.jsonl
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus


# ── Idea Schema ──────────────────────────────────────────────────

IDEA_STATUSES = ["captured", "triaged", "researching", "queued", "building", "completed", "parked"]
IDEA_CATEGORIES = [
    "feature", "module", "integration", "content", "business",
    "optimization", "experiment", "infrastructure", "lifeos", "creative"
]


class IdeaLog:
    """Fast idea capture and triage pipeline."""

    def __init__(self):
        self.vault = get_context_vault()
        self.ideas_dir = self.vault / "ideas"
        self.ideas_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.ideas_dir / "idea_log.jsonl"
        self.bus = EPOSEventBus()

    def capture(self, title: str, description: str = "",
                category: str = "feature", source: str = "cli",
                tags: Optional[List[str]] = None, priority: str = "medium") -> dict:
        """Capture an idea with minimal friction. Returns the idea record."""
        idea = {
            "idea_id": f"IDEA-{uuid.uuid4().hex[:8]}",
            "title": title,
            "description": description,
            "category": category if category in IDEA_CATEGORIES else "feature",
            "source": source,
            "tags": tags or [],
            "priority": priority,
            "status": "captured",
            "triage_result": None,
            "research_brief_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Append to JSONL
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(idea) + "\n")

        # Publish to event bus
        self.bus.publish("idea.captured", {
            "idea_id": idea["idea_id"],
            "title": title,
            "category": category,
            "priority": priority,
        }, "idea_log")

        return idea

    def list_ideas(self, status: Optional[str] = None, limit: int = 20) -> List[dict]:
        """List ideas, optionally filtered by status."""
        if not self.log_path.exists():
            return []
        ideas = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    idea = json.loads(line)
                    if status is None or idea.get("status") == status:
                        ideas.append(idea)
                except Exception:
                    pass
        # Most recent first
        ideas.reverse()
        return ideas[:limit]

    def update_status(self, idea_id: str, new_status: str, note: str = "") -> Optional[dict]:
        """Update an idea's status. Rewrites the log with the update."""
        if new_status not in IDEA_STATUSES:
            return None
        if not self.log_path.exists():
            return None

        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        updated = None
        new_lines = []
        for line in lines:
            if not line.strip():
                continue
            try:
                idea = json.loads(line)
                if idea.get("idea_id") == idea_id:
                    idea["status"] = new_status
                    idea["updated_at"] = datetime.now(timezone.utc).isoformat()
                    if note:
                        idea.setdefault("notes", [])
                        idea["notes"].append({"note": note, "at": idea["updated_at"]})
                    updated = idea
                new_lines.append(json.dumps(idea))
            except Exception:
                new_lines.append(line)

        if updated:
            self.log_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            self.bus.publish("idea.status_changed", {
                "idea_id": idea_id,
                "new_status": new_status,
            }, "idea_log")

        return updated

    def triage(self, idea_id: str, verdict: str, reasoning: str = "",
               priority_override: Optional[str] = None) -> Optional[dict]:
        """Apply triage result to an idea (typically called by Friday)."""
        if not self.log_path.exists():
            return None

        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        updated = None
        new_lines = []
        for line in lines:
            if not line.strip():
                continue
            try:
                idea = json.loads(line)
                if idea.get("idea_id") == idea_id:
                    idea["status"] = "triaged"
                    idea["triage_result"] = {
                        "verdict": verdict,  # build, research, park, defer
                        "reasoning": reasoning,
                        "triaged_at": datetime.now(timezone.utc).isoformat(),
                    }
                    if priority_override:
                        idea["priority"] = priority_override
                    idea["updated_at"] = datetime.now(timezone.utc).isoformat()
                    updated = idea
                new_lines.append(json.dumps(idea))
            except Exception:
                new_lines.append(line)

        if updated:
            self.log_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            self.bus.publish("idea.triaged", {
                "idea_id": idea_id,
                "verdict": verdict,
                "priority": updated.get("priority"),
            }, "idea_log")

        return updated

    def get_idea(self, idea_id: str) -> Optional[dict]:
        """Get a single idea by ID."""
        if not self.log_path.exists():
            return None
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    idea = json.loads(line)
                    if idea.get("idea_id") == idea_id:
                        return idea
                except Exception:
                    pass
        return None

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """Search ideas by title/description/tags."""
        q = query.lower()
        results = []
        for idea in self.list_ideas(limit=100):
            text = f"{idea.get('title','')} {idea.get('description','')} {' '.join(idea.get('tags',[]))}".lower()
            if q in text:
                results.append(idea)
            if len(results) >= limit:
                break
        return results

    def stats(self) -> dict:
        """Get idea log statistics."""
        all_ideas = self.list_ideas(limit=1000)
        by_status = {}
        by_category = {}
        for idea in all_ideas:
            s = idea.get("status", "unknown")
            c = idea.get("category", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
            by_category[c] = by_category.get(c, 0) + 1
        return {
            "total": len(all_ideas),
            "by_status": by_status,
            "by_category": by_category,
        }


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile

    py_compile.compile("idea_log.py", doraise=True)
    print("PASS: idea_log.py compiles clean")

    log = IdeaLog()

    # Test capture
    idea = log.capture(
        "Add Google Sheets sync for project tracking",
        description="Bi-directional sync between EPOS DB and Google Sheets",
        category="integration",
        tags=["google", "sync", "projects"],
        priority="high",
    )
    assert idea["idea_id"].startswith("IDEA-")
    assert idea["status"] == "captured"
    print(f"PASS: Idea captured — {idea['idea_id']}")

    # Test list
    ideas = log.list_ideas()
    assert len(ideas) >= 1
    print(f"PASS: Listed {len(ideas)} ideas")

    # Test triage
    triaged = log.triage(idea["idea_id"], "research", "Needs API scope assessment first")
    assert triaged["status"] == "triaged"
    assert triaged["triage_result"]["verdict"] == "research"
    print(f"PASS: Idea triaged — verdict: research")

    # Test status update
    updated = log.update_status(idea["idea_id"], "researching", "Starting API review")
    assert updated["status"] == "researching"
    print(f"PASS: Status updated to researching")

    # Test search
    results = log.search("google")
    assert len(results) >= 1
    print(f"PASS: Search found {len(results)} results")

    # Test stats
    s = log.stats()
    assert s["total"] >= 1
    print(f"PASS: Stats — {s['total']} total ideas")

    print("\nPASS: IdeaLog — all 6 tests passed")
