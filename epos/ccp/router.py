#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/ccp/router.py — CCP Situational Routing Engine
====================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

Routes extracted elements to their destination PM JSON files.
Every routing decision is logged as a training pair for SCC curriculum.

Routing flow:
  1. score_element → determines confidence band
  2. HIGH confidence → auto-route directly to destination
  3. MEDIUM confidence → present suggestion, await Jamie confirmation
  4. LOW confidence → present for manual classification

Confirmation states:
  auto       — routed without human input (high confidence)
  confirmed  — Jamie confirmed the suggestion
  overridden — Jamie changed type or destination
  discarded  — Jamie discarded this element

Every confirmation/override/discard is logged to:
  context_vault/training/pairs/routing_decisions.jsonl
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from epos.ccp.extractor import ExtractedElement, ElementType, SUGGESTED_DESTINATIONS
from epos.ccp.scorer import confidence_band, BAND_HIGH, BAND_MEDIUM, BAND_LOW

# ── Reward bus (Directive 20260414-02) ────────────────────────────────────────
try:
    from epos.rewards.publish_reward import publish_reward as _pub_reward
    def _reward(signal_name: str, value: float, signal_type: str = "outcome",
                context: str = "", needs_review: bool = False) -> None:
        try:
            _pub_reward(signal_name=signal_name, value=value,
                        signal_type=signal_type, source="ccp_router",
                        context=context, needs_review=needs_review)
        except Exception:
            pass
except ImportError:
    def _reward(*a, **kw): pass

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
PM_ROOT = EPOS_ROOT / "context_vault" / "pm"
TRAINING_PAIRS = EPOS_ROOT / "context_vault" / "training" / "pairs" / "routing_decisions.jsonl"

# PM file map
PM_FILES = {
    ElementType.ACTION_ITEM:             PM_ROOT / "action_items.json",
    ElementType.DECISION:                PM_ROOT / "decisions.json",
    ElementType.RESEARCH_QUESTION:       PM_ROOT / "research_queue.json",
    ElementType.IDEA:                    PM_ROOT / "idea_pipeline.json",
    ElementType.CLIENT_INSIGHT:          PM_ROOT / "client_insights.json",
    ElementType.CONTENT_SEED:            PM_ROOT / "idea_pipeline.json",  # content seeds go to idea pipeline
    ElementType.LEARNING_MOMENT:         EPOS_ROOT / "context_vault" / "training" / "learning_moments.jsonl",
    ElementType.CONSTITUTIONAL_PROPOSAL: EPOS_ROOT / "context_vault" / "governance" / "proposals.json",
    ElementType.BLOCKER:                 PM_ROOT / "blockers.json",
}

# Confirmation state values
CONFIRM_AUTO       = "auto"
CONFIRM_CONFIRMED  = "confirmed"
CONFIRM_OVERRIDDEN = "overridden"
CONFIRM_DISCARDED  = "discarded"
CONFIRM_PENDING    = "pending"


# ──────────────────────────────────────────────────────────────────────────────
# Routing result model
# ──────────────────────────────────────────────────────────────────────────────

class RoutingResult:
    """Result of a single element routing decision."""

    def __init__(self, element: ExtractedElement, action: str):
        self.routing_id = f"ROUTE-{uuid.uuid4().hex[:10].upper()}"
        self.element = element
        self.action = action            # auto / pending_confirmation
        self.confirmation_state = CONFIRM_AUTO if action == "auto" else CONFIRM_PENDING
        self.destination_path: Optional[str] = None
        self.written: bool = False
        self.routed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "routing_id": self.routing_id,
            "element_id": self.element.element_id,
            "element_type": self.element.type.value,
            "content": self.element.content,
            "confidence": self.element.confidence,
            "confidence_band": confidence_band(self.element.confidence),
            "action": self.action,
            "confirmation_state": self.confirmation_state,
            "suggested_destination": self.element.suggested_destination,
            "destination_path": self.destination_path,
            "written": self.written,
            "routed_at": self.routed_at,
        }


# ──────────────────────────────────────────────────────────────────────────────
# PM store helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_pm_file(path: Path) -> list:
    """Load PM JSON file, return list of items."""
    if path.suffix == ".jsonl":
        if not path.exists():
            return []
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else data.get("items", [])
    except (json.JSONDecodeError, Exception):
        return []


def _save_pm_file(path: Path, items: list):
    """Save PM JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".jsonl":
        with open(path, "a") as f:
            f.write(json.dumps(items[-1]) + "\n")
        return
    path.write_text(json.dumps({"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}, indent=2))


def _write_element_to_pm(element: ExtractedElement) -> str:
    """Write element to its destination PM file. Returns path written."""
    dest_path = PM_FILES.get(element.type)
    if not dest_path:
        dest_path = PM_ROOT / "misc.json"

    # Build PM entry
    pm_entry = {
        "id": element.element_id,
        "content": element.content,
        "type": element.type.value,
        "confidence": element.confidence,
        "source_capture_id": element.source_capture_id,
        "status": "pending",
        "priority": "normal",
        "assigned_to": None,
        "due_date": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_directive": None,
        "context_refs": element.context_refs,
    }

    if dest_path.suffix == ".jsonl":
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "a") as f:
            f.write(json.dumps(pm_entry) + "\n")
    else:
        items = _load_pm_file(dest_path)
        items.append(pm_entry)
        _save_pm_file(dest_path, items)

    return str(dest_path)


# ──────────────────────────────────────────────────────────────────────────────
# Training pair logging
# ──────────────────────────────────────────────────────────────────────────────

def _log_routing_decision(result: RoutingResult, original_type: Optional[str] = None):
    """Append routing decision to training pairs log."""
    TRAINING_PAIRS.parent.mkdir(parents=True, exist_ok=True)
    pair = {
        "routing_id": result.routing_id,
        "element_id": result.element.element_id,
        "content": result.element.content[:300],
        "heuristic_type": original_type or result.element.type.value,
        "final_type": result.element.type.value,
        "confidence": result.element.confidence,
        "confirmation_state": result.confirmation_state,
        "destination": result.destination_path,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(TRAINING_PAIRS, "a") as f:
        f.write(json.dumps(pair) + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# Core routing
# ──────────────────────────────────────────────────────────────────────────────

def route_element(element: ExtractedElement, auto_threshold: float = 0.90) -> RoutingResult:
    """
    Route a single scored element.

    High confidence (≥ auto_threshold) → auto-write to PM file.
    Medium/Low → return pending result for human confirmation.

    Args:
        element: Scored ExtractedElement
        auto_threshold: Confidence above which to auto-route

    Returns:
        RoutingResult with action and written state
    """
    if element.confidence >= auto_threshold and not element.needs_llm_review:
        # Auto-route
        result = RoutingResult(element, action="auto")
        dest = _write_element_to_pm(element)
        result.destination_path = dest
        result.written = True
        result.confirmation_state = CONFIRM_AUTO
        _log_routing_decision(result)
        return result
    else:
        # Needs confirmation
        result = RoutingResult(element, action="pending_confirmation")
        result.confirmation_state = CONFIRM_PENDING
        return result


def route_elements(
    elements: List[ExtractedElement],
    auto_threshold: float = 0.90,
) -> dict:
    """
    Route a batch of scored elements.

    Returns:
        {
            "auto_routed": [RoutingResult, ...],
            "pending_confirmation": [RoutingResult, ...],
            "summary": {...},
        }
    """
    auto_routed = []
    pending = []

    for element in elements:
        result = route_element(element, auto_threshold=auto_threshold)
        if result.action == "auto":
            auto_routed.append(result)
        else:
            pending.append(result)

    return {
        "auto_routed": auto_routed,
        "pending_confirmation": pending,
        "summary": {
            "total": len(elements),
            "auto_routed": len(auto_routed),
            "pending_confirmation": len(pending),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Human confirmation handler
# ──────────────────────────────────────────────────────────────────────────────

def confirm_routing(
    result: RoutingResult,
    action: str,                        # "confirm" | "override" | "discard"
    override_type: Optional[str] = None,
    override_destination: Optional[str] = None,
) -> RoutingResult:
    """
    Apply Jamie's confirmation decision to a pending routing result.

    Args:
        result: Pending RoutingResult
        action: "confirm" | "override" | "discard"
        override_type: New element type if overriding
        override_destination: New destination path if overriding

    Returns:
        Updated RoutingResult (written if confirmed/overridden)
    """
    original_type = result.element.type.value

    if action == "discard":
        result.confirmation_state = CONFIRM_DISCARDED
        result.written = False
        _reward("ccp_routing_discarded", -0.1, signal_type="negative",
                context=f"Element {result.element.element_id} [{result.element.type.value}] discarded")
        _log_routing_decision(result, original_type=original_type)
        return result

    if action == "override" and override_type:
        try:
            result.element.type = ElementType(override_type)
            from epos.ccp.extractor import SUGGESTED_DESTINATIONS
            result.element.suggested_destination = SUGGESTED_DESTINATIONS.get(
                result.element.type, result.element.suggested_destination
            )
            result.confirmation_state = CONFIRM_OVERRIDDEN
        except ValueError:
            pass

    # Outcome signals for confirmation decisions
    if action == "confirm":
        _reward("ccp_routing_confirmed", 0.2, signal_type="outcome",
                context=f"Element {result.element.element_id} [{result.element.type.value}] confirmed → {result.element.suggested_destination}")
    elif action == "override":
        _reward("ccp_routing_overridden", 0.1, signal_type="outcome",
                context=f"Element {result.element.element_id} heuristic={original_type} → override={result.element.type.value}",
                needs_review=True)

    if action in ("confirm", "override"):
        if override_destination:
            # Write to custom destination
            dest_path = Path(override_destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            pm_entry = {
                "id": result.element.element_id,
                "content": result.element.content,
                "type": result.element.type.value,
                "confidence": result.element.confidence,
                "source_capture_id": result.element.source_capture_id,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(dest_path, "a") as f:
                f.write(json.dumps(pm_entry) + "\n")
            result.destination_path = str(dest_path)
        else:
            dest = _write_element_to_pm(result.element)
            result.destination_path = dest

        result.written = True
        if result.confirmation_state == CONFIRM_PENDING:
            result.confirmation_state = CONFIRM_CONFIRMED

    _log_routing_decision(result, original_type=original_type)
    return result
