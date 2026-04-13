#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/router.py — Voice Element Router
============================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Routes extracted pipeline elements to their destinations:
PM surface, inbox, vault, event bus.
"""

import json
import os
from pathlib import Path
from datetime import datetime

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
PM_SURFACE = EPOS_ROOT / "context_vault" / "pm_surface.jsonl"
INBOX = EPOS_ROOT / "context_vault" / "inbox"

# ── Reward bus (Directive 20260414-02) ────────────────────────────────────────
try:
    from epos.rewards.publish_reward import publish_reward as _pub_reward
    def _reward(signal_name: str, value: float, signal_type: str = "outcome",
                context: str = "", needs_review: bool = False) -> None:
        try:
            _pub_reward(signal_name=signal_name, value=value,
                        signal_type=signal_type, source="voice_pipeline",
                        context=context, needs_review=needs_review)
        except Exception:
            pass
except ImportError:
    def _reward(*a, **kw): pass

# ── PM Surface reward hook points (Directive 20260414-01, activate when PM live) ──
# When element routed to PM:
#   created:    _reward("pm_item_created",    +0.1, signal_type="process")
#   completed:  _reward("pm_item_completed",  +0.3, signal_type="outcome")
#   blocked:    _reward("pm_item_blocked",    -0.1, signal_type="negative")
#   stale(7d):  _reward("pm_item_stale",      -0.2, needs_review=True)
# Decision lifecycle:
#   recorded:    _reward("decision_recorded",    +0.1, signal_type="process")
#   implemented: _reward("decision_implemented", +0.3, signal_type="outcome")
#   reversed:    _reward("decision_reversed",    -0.2, needs_review=True)

DESTINATION_MAP = {
    "action_item": str(PM_SURFACE),
    "decision": "context_vault/aar/",
    "research_question": "context_vault/knowledge/",
    "idea": "context_vault/inbox/",
    "directive": "context_vault/directives/",
}


def route_elements(elements: list, session_id: str) -> dict:
    """Route extracted elements to their designated destinations.

    Args:
        elements: List of {type, content, confidence, destination} dicts
        session_id: Voice session ID for traceability

    Returns:
        {"routed": int, "destinations": {dest: count}}
    """
    routed = 0
    destinations = {}

    for element in elements:
        element_type = element.get("type", "idea")
        content = element.get("content", "")
        confidence = element.get("confidence", 0.5)
        destination = element.get("destination", DESTINATION_MAP.get(element_type, "context_vault/inbox/"))

        if confidence < 0.5:
            continue  # Skip low-confidence elements

        record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": element_type,
            "content": content,
            "confidence": confidence,
            "destination": destination,
            "source": "voice_pipeline"
        }

        try:
            if "pm_surface" in destination or element_type == "action_item":
                PM_SURFACE.parent.mkdir(parents=True, exist_ok=True)
                with open(PM_SURFACE, "a") as f:
                    f.write(json.dumps(record) + "\n")
            else:
                inbox_file = INBOX / f"{session_id}_{element_type}.json"
                INBOX.mkdir(parents=True, exist_ok=True)
                inbox_file.write_text(json.dumps(record, indent=2))

            destinations[destination] = destinations.get(destination, 0) + 1
            routed += 1

            # Outcome: element routed successfully
            _reward("routing_confirmed", 0.3, signal_type="outcome",
                    context=f"Element '{element_type}' routed to {destination}")

        except Exception:
            pass

    return {"routed": routed, "destinations": destinations}


def record_routing_override(
    element_type: str,
    suggested_destination: str,
    actual_destination: str,
    session_id: str = "",
) -> None:
    """
    Call when Jamie overrides a routing suggestion.
    Publishes outcome + needs_review signal for training.
    """
    _reward("routing_overridden", -0.2, signal_type="outcome",
            context=f"Suggested {suggested_destination}, Jamie chose {actual_destination}",
            needs_review=True)


def record_reformulation_outcome(
    session_id: str,
    outcome: str,  # "accepted" | "edited" | "discarded"
) -> None:
    """
    Call when Jamie accepts, edits, or discards a reformulation.
    Publishes outcome signal for training.
    """
    signals = {
        "accepted":  ("reformulation_accepted",  1.0, False),
        "edited":    ("reformulation_edited",     0.5, False),
        "discarded": ("reformulation_discarded", -0.5, True),
    }
    name, value, review = signals.get(outcome, ("reformulation_unknown", 0.0, False))
    _reward(name, value, signal_type="outcome",
            context=f"Session {session_id} {outcome}",
            needs_review=review)
