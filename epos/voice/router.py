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
from pathlib import Path
from datetime import datetime

EPOS_ROOT = Path("/app")
PM_SURFACE = EPOS_ROOT / "context_vault" / "pm_surface.jsonl"
INBOX = EPOS_ROOT / "context_vault" / "inbox"

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
        except Exception:
            pass

    return {"routed": routed, "destinations": destinations}
