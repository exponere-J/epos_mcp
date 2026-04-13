#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/vision.py — M-VISION-01 Interface (Screen Description Skeleton)
===========================================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Phase 1: Skeleton with mock responses.
Phase 2: Wire to UI-I2E-VLM-7B on Ollama for real screen grounding.
"""

import json
from pathlib import Path
from datetime import datetime


def describe_screen(screenshot_bytes: bytes = None, screenshot_path: str = None) -> dict:
    """Describe what's on screen. Returns hierarchical element map.

    Phase 1: Returns mock/skeleton structure.
    Phase 2: Sends screenshot to vision model for real analysis.
    """
    # Phase 1: Skeleton response (replace with vision model call in Phase 2)
    return {
        "status": "skeleton",
        "note": "Vision model (UI-I2E-VLM-7B) not yet seated. This is a placeholder.",
        "description": "Screen content not analyzed — vision model pending.",
        "elements": [],
        "model": "M-VISION-01 (pending)",
        "phase": 1
    }


def resolve_conflict(user_said: str, vision_found: list) -> dict:
    """Handle conflicts between voice intent and visual interpretation.

    When user says 'blue button' but vision sees 'cyan' and 'navy':
    - Present both options with context
    - Wait for user decision
    - Log decision as training pair
    """
    labels = [v.get("label", str(v)) for v in vision_found]
    return {
        "conflict_type": "visual_label_mismatch",
        "user_said": user_said,
        "vision_found": vision_found,
        "action": "ask_user",
        "prompt": (
            f"I heard '{user_said}'. "
            f"The screen shows: {', '.join(labels)}. "
            "Which did you mean?"
        )
    }
