#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/pm/store.py — PM Surface JSON Store
=========================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

CRUD interface for 6 local JSON PM tabs:
  action_items.json    — tasks to be done
  decisions.json       — choices made/to be made
  research_queue.json  — open questions
  blockers.json        — impediments to progress
  idea_pipeline.json   — concepts to explore (includes content_seed)
  client_insights.json — client/prospect intelligence

Each entry schema:
  id              — ELM- or manual UUID
  content         — the actual text
  source_directive — originating directive (if known)
  created_at      — ISO timestamp
  status          — pending | in_progress | blocked | complete
  priority        — critical | high | normal | low
  assigned_to     — person/agent string or null
  due_date        — ISO date string or null
  confidence      — 0.0–1.0 (from CCP extractor)
  source_capture_id — links to raw capture

Status lifecycle:
  pending → in_progress → complete
  pending → blocked → in_progress → complete
  any → (discarded via DELETE)
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
PM_ROOT = EPOS_ROOT / "context_vault" / "pm"


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class PMTab(str, Enum):
    ACTION_ITEMS    = "action_items"
    DECISIONS       = "decisions"
    RESEARCH_QUEUE  = "research_queue"
    BLOCKERS        = "blockers"
    IDEA_PIPELINE   = "idea_pipeline"
    CLIENT_INSIGHTS = "client_insights"


class PMStatus(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED     = "blocked"
    COMPLETE    = "complete"


class PMPriority(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    NORMAL   = "normal"
    LOW      = "low"


# ──────────────────────────────────────────────────────────────────────────────
# PMEntry dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PMEntry:
    """A single PM surface item."""
    id: str = field(default_factory=lambda: f"PM-{uuid.uuid4().hex[:10].upper()}")
    content: str = ""
    source_directive: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    status: str = PMStatus.PENDING.value
    priority: str = PMPriority.NORMAL.value
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    confidence: float = 1.0
    source_capture_id: Optional[str] = None
    element_type: Optional[str] = None  # original CCP element type
    context_refs: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None or k in (
            "assigned_to", "due_date", "source_directive", "source_capture_id", "notes"
        )}


# ──────────────────────────────────────────────────────────────────────────────
# PMStore
# ──────────────────────────────────────────────────────────────────────────────

class PMStore:
    """
    CRUD interface for the local JSON PM surface.

    All writes are atomic: load → modify → write.
    All tabs are initialized on first access.
    """

    def __init__(self, pm_root: Optional[Path] = None):
        self.pm_root = pm_root or PM_ROOT
        self.pm_root.mkdir(parents=True, exist_ok=True)
        self._ensure_tabs()

    # ── Tab file management ───────────────────────────────────────────────────

    def _tab_path(self, tab: PMTab) -> Path:
        return self.pm_root / f"{tab.value}.json"

    def _ensure_tabs(self):
        """Initialize all tab files if they don't exist."""
        for tab in PMTab:
            path = self._tab_path(tab)
            if not path.exists():
                path.write_text(json.dumps({
                    "tab": tab.value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "items": [],
                }, indent=2))

    def _load(self, tab: PMTab) -> dict:
        path = self._tab_path(tab)
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {"tab": tab.value, "items": []}

    def _save(self, tab: PMTab, data: dict):
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._tab_path(tab).write_text(json.dumps(data, indent=2, default=str))

    # ── CRUD operations ───────────────────────────────────────────────────────

    def list_items(
        self,
        tab: PMTab,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[dict]:
        """
        List all items in a tab, with optional status/priority filters.

        Args:
            tab: PMTab enum
            status: Filter by status (pending, in_progress, blocked, complete)
            priority: Filter by priority (critical, high, normal, low)

        Returns:
            List of item dicts, newest first
        """
        data = self._load(tab)
        items = data.get("items", [])

        if status:
            items = [i for i in items if i.get("status") == status]
        if priority:
            items = [i for i in items if i.get("priority") == priority]

        # Sort: newest first
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items

    def add_item(self, tab: PMTab, entry: PMEntry) -> PMEntry:
        """
        Add a new item to a tab.

        Args:
            tab: PMTab enum
            entry: PMEntry to add

        Returns:
            The saved PMEntry (with assigned ID)
        """
        data = self._load(tab)
        items = data.get("items", [])
        item_dict = entry.to_dict()
        items.append(item_dict)
        data["items"] = items
        self._save(tab, data)
        return entry

    def add_from_dict(self, tab: PMTab, item: dict) -> dict:
        """
        Add an item from a plain dict (e.g. from CCP router output).
        Assigns ID if not present.
        """
        if "id" not in item:
            item["id"] = f"PM-{uuid.uuid4().hex[:10].upper()}"
        if "created_at" not in item:
            item["created_at"] = datetime.now(timezone.utc).isoformat()
        if "status" not in item:
            item["status"] = PMStatus.PENDING.value

        data = self._load(tab)
        data.setdefault("items", []).append(item)
        self._save(tab, data)
        return item

    def get_item(self, tab: PMTab, item_id: str) -> Optional[dict]:
        """Get a single item by ID."""
        items = self.list_items(tab)
        return next((i for i in items if i.get("id") == item_id), None)

    def update_item(self, tab: PMTab, item_id: str, updates: dict) -> Optional[dict]:
        """
        Update fields on an existing item.

        Args:
            tab: PMTab enum
            item_id: item ID string
            updates: dict of fields to update (status, priority, assigned_to, etc.)

        Returns:
            Updated item dict, or None if not found
        """
        data = self._load(tab)
        items = data.get("items", [])

        for i, item in enumerate(items):
            if item.get("id") == item_id:
                # Apply updates
                allowed_fields = {
                    "status", "priority", "assigned_to", "due_date",
                    "notes", "content", "context_refs"
                }
                for k, v in updates.items():
                    if k in allowed_fields:
                        items[i][k] = v
                items[i]["updated_at"] = datetime.now(timezone.utc).isoformat()
                data["items"] = items
                self._save(tab, data)
                return items[i]

        return None

    def delete_item(self, tab: PMTab, item_id: str) -> bool:
        """Delete an item by ID. Returns True if deleted."""
        data = self._load(tab)
        items = data.get("items", [])
        original_len = len(items)
        data["items"] = [i for i in items if i.get("id") != item_id]

        if len(data["items"]) < original_len:
            self._save(tab, data)
            return True
        return False

    # ── Summary ───────────────────────────────────────────────────────────────

    def get_summary(self) -> dict:
        """
        Return counts per tab per status.
        Used by Friday morning briefing and GET /pm/summary.

        Returns:
            {
                "action_items": {"total": N, "pending": N, "in_progress": N, ...},
                ...
                "total_pending": N,
                "total_items": N,
                "generated_at": ISO str,
            }
        """
        summary: Dict[str, Any] = {}
        total_pending = 0
        total_items = 0

        for tab in PMTab:
            data = self._load(tab)
            items = data.get("items", [])
            status_counts: dict = {}

            for item in items:
                s = item.get("status", "pending")
                status_counts[s] = status_counts.get(s, 0) + 1

            tab_total = len(items)
            summary[tab.value] = {"total": tab_total, **status_counts}
            total_pending += status_counts.get("pending", 0)
            total_items += tab_total

        summary["total_pending"] = total_pending
        summary["total_items"] = total_items
        summary["generated_at"] = datetime.now(timezone.utc).isoformat()
        return summary

    # ── Bulk intake from CCP ──────────────────────────────────────────────────

    def ingest_ccp_result(self, routing_result: dict) -> dict:
        """
        Ingest all auto-routed elements from a CCP pipeline run.

        Args:
            routing_result: Output from CCPPipeline.process_text()

        Returns:
            {"written": N, "tabs_touched": [str, ...]}
        """
        from epos.ccp.extractor import ElementType

        # Map element types to PM tabs
        type_to_tab = {
            "action_item":             PMTab.ACTION_ITEMS,
            "decision":                PMTab.DECISIONS,
            "research_question":       PMTab.RESEARCH_QUEUE,
            "idea":                    PMTab.IDEA_PIPELINE,
            "client_insight":          PMTab.CLIENT_INSIGHTS,
            "content_seed":            PMTab.IDEA_PIPELINE,
            "learning_moment":         None,  # goes to training/, not PM
            "constitutional_proposal": None,  # goes to governance
            "blocker":                 PMTab.BLOCKERS,
        }

        written = 0
        tabs_touched = set()

        auto_routed = routing_result.get("routing", {}).get("auto_routed", [])
        for route in auto_routed:
            tab = type_to_tab.get(route.get("element_type"))
            if not tab:
                continue

            entry = {
                "id": route.get("element_id"),
                "content": route.get("content"),
                "status": "pending",
                "priority": "normal",
                "confidence": route.get("confidence"),
                "source_capture_id": route.get("source_capture_id"),
                "element_type": route.get("element_type"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.add_from_dict(tab, entry)
            written += 1
            tabs_touched.add(tab.value)

        return {"written": written, "tabs_touched": sorted(tabs_touched)}
