#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/pm/api.py — PM Surface FastAPI Router
===========================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

FastAPI router mounted at /pm in the main EPOS API.

Endpoints:
  GET  /pm/summary                — counts per tab per status
  GET  /pm/{tab}                  — list all items in a tab
  POST /pm/{tab}                  — add item to a tab
  PATCH /pm/{tab}/{id}            — update item status/fields
  DELETE /pm/{tab}/{id}           — remove item
  POST /pm/ingest                 — run text through CCP and route to PM
  POST /pm/confirm/{routing_id}   — confirm/override/discard pending element

Mount in main API:
    from epos.pm.api import pm_router
    app.include_router(pm_router)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from epos.pm.store import PMStore, PMEntry, PMTab, PMStatus, PMPriority

pm_router = APIRouter(prefix="/pm", tags=["PM Surface"])
_store = PMStore()


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────────────

class PMEntryCreate(BaseModel):
    content: str
    source_directive: Optional[str] = None
    priority: str = PMPriority.NORMAL.value
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    confidence: float = 1.0
    source_capture_id: Optional[str] = None
    element_type: Optional[str] = None
    notes: Optional[str] = None


class PMEntryUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    content: Optional[str] = None


class IngestRequest(BaseModel):
    text: str = Field(..., description="Raw text to run through CCP pipeline")
    source_capture_id: Optional[str] = None
    source_type: str = "direct_paste"
    use_llm: bool = False  # default off for speed; enable for ambiguous cases


class ConfirmRequest(BaseModel):
    action: str = Field(..., description="confirm | override | discard")
    element_id: str
    run_result: dict
    override_type: Optional[str] = None
    override_destination: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_tab(tab: str) -> PMTab:
    """Resolve tab name string to PMTab enum."""
    try:
        return PMTab(tab)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown PM tab: '{tab}'. Valid: {[t.value for t in PMTab]}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@pm_router.get("/summary")
def get_pm_summary() -> dict:
    """
    Return counts per tab per status.
    Feeds Friday morning briefing and dashboard.

    Returns:
        {"action_items": {"total": N, "pending": N, ...}, ..., "total_pending": N}
    """
    return _store.get_summary()


@pm_router.post("/_ingest")
def ingest_text(body: IngestRequest) -> dict:
    """
    Run raw text through CCP pipeline and route extracted elements to PM tabs.

    This is the primary intake endpoint. Voice captures, FOTW sessions,
    and direct pastes all flow through here.

    Args:
        body.text: Raw text to process
        body.source_type: "voice_capture" | "direct_paste" | "fotw" | "reader"
        body.use_llm: Whether to use LLM for medium-confidence elements

    Returns:
        {
            "run_id": str,
            "elements_extracted": N,
            "routing": {"auto_routed": [...], "pending_confirmation": [...], ...},
            "pm_written": N,
            "tabs_touched": [str, ...],
        }
    """
    from epos.ccp.pipeline import CCPPipeline
    pipeline = CCPPipeline(use_llm=body.use_llm)

    result = pipeline.process_text(
        body.text,
        source_capture_id=body.source_capture_id,
        source_type=body.source_type,
    )

    # Also ingest to PM store
    pm_result = _store.ingest_ccp_result(result)

    return {
        "run_id": result["run_id"],
        "elements_extracted": result["elements_extracted"],
        "score_summary": result.get("score_summary", {}),
        "routing": result["routing"],
        "pm_written": pm_result["written"],
        "tabs_touched": pm_result["tabs_touched"],
        "processed_at": result["processed_at"],
    }


@pm_router.post("/_confirm")
def confirm_element(body: ConfirmRequest) -> dict:
    """
    Confirm, override, or discard a pending routing decision.

    After POST /pm/_ingest returns pending_confirmation items,
    call this endpoint for each pending element with Jamie's decision.

    Args:
        body.action: "confirm" | "override" | "discard"
        body.element_id: element_id from pending_confirmation list
        body.run_result: full result dict from /pm/_ingest
        body.override_type: new element type string (if overriding)
        body.override_destination: new destination path (if overriding)
    """
    from epos.ccp.pipeline import CCPPipeline
    pipeline = CCPPipeline()

    result = pipeline.confirm_element(
        run_result=body.run_result,
        element_id=body.element_id,
        action=body.action,
        override_type=body.override_type,
        override_destination=body.override_destination,
    )

    # If confirmed/overridden, sync to PM store
    if result.get("written") and body.action in ("confirm", "override"):
        element_type = result.get("element_type", "")
        type_to_tab = {
            "action_item":    PMTab.ACTION_ITEMS,
            "decision":       PMTab.DECISIONS,
            "research_question": PMTab.RESEARCH_QUEUE,
            "idea":           PMTab.IDEA_PIPELINE,
            "client_insight": PMTab.CLIENT_INSIGHTS,
            "content_seed":   PMTab.IDEA_PIPELINE,
            "blocker":        PMTab.BLOCKERS,
        }
        tab = type_to_tab.get(element_type)
        if tab:
            _store.add_from_dict(tab, {
                "id": result.get("element_id"),
                "content": result.get("content", ""),
                "element_type": element_type,
                "confidence": result.get("confidence"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    return {"confirmed": True, "result": result}


@pm_router.get("/{tab}")
def list_tab_items(
    tab: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> dict:
    """
    List all items in a PM tab.

    Args:
        tab: One of: action_items, decisions, research_queue, blockers,
             idea_pipeline, client_insights
        status: Filter by status (pending, in_progress, blocked, complete)
        priority: Filter by priority (critical, high, normal, low)
    """
    pm_tab = _resolve_tab(tab)
    items = _store.list_items(pm_tab, status=status, priority=priority)
    return {
        "tab": tab,
        "count": len(items),
        "items": items,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@pm_router.post("/{tab}")
def add_item(tab: str, body: PMEntryCreate) -> dict:
    """
    Add a new item to a PM tab.

    Args:
        tab: PM tab name
        body: PMEntryCreate payload
    """
    pm_tab = _resolve_tab(tab)
    entry = PMEntry(
        content=body.content,
        source_directive=body.source_directive,
        priority=body.priority,
        assigned_to=body.assigned_to,
        due_date=body.due_date,
        confidence=body.confidence,
        source_capture_id=body.source_capture_id,
        element_type=body.element_type,
        notes=body.notes,
    )
    saved = _store.add_item(pm_tab, entry)
    return {"added": True, "item": saved.to_dict()}


@pm_router.patch("/{tab}/{item_id}")
def update_item(tab: str, item_id: str, body: PMEntryUpdate) -> dict:
    """
    Update an item's status, priority, assignment, or notes.

    Args:
        tab: PM tab name
        item_id: Item ID string (e.g. PM-XXXXXXXXXXXX)
        body: Fields to update
    """
    pm_tab = _resolve_tab(tab)
    updates = {k: v for k, v in body.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updated = _store.update_item(pm_tab, item_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found in {tab}")

    return {"updated": True, "item": updated}


@pm_router.delete("/{tab}/{item_id}")
def delete_item(tab: str, item_id: str) -> dict:
    """
    Remove an item from a PM tab.

    Args:
        tab: PM tab name
        item_id: Item ID to delete
    """
    pm_tab = _resolve_tab(tab)
    deleted = _store.delete_item(pm_tab, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found in {tab}")
    return {"deleted": True, "item_id": item_id}


