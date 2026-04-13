#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/training_logger.py — QLoRA Training Data Logger
===========================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Saves voice sessions and reformulation pairs for nightly QLoRA training.
Every voice session is a training document.
"""

import json
from pathlib import Path
from datetime import datetime

TRAINING_FILE = Path("/app/context_vault/voice/training_pairs.jsonl")
SESSION_DIR = Path("/app/context_vault/voice/sessions")


def log_session(session_id: str, session_log: dict, reformulation: dict) -> str:
    """Save full session + extract training pair.

    Returns:
        Path to saved session file.
    """
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # Save full session log
    session_path = SESSION_DIR / f"{session_id}.json"
    session_path.write_text(json.dumps({
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "log": session_log,
        "reformulation": reformulation
    }, indent=2))

    # Extract training pair (raw → reformulated)
    TRAINING_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw_text = ""
    steps = session_log.get("steps", [])
    if steps:
        raw_text = steps[0].get("output", "")

    training_pair = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw": raw_text,
        "reformulated": reformulation.get("reformulated", ""),
        "accepted": None  # Set to True/False when Jamie confirms/rejects
    }
    with open(TRAINING_FILE, "a") as f:
        f.write(json.dumps(training_pair) + "\n")

    return str(session_path)


def get_training_stats() -> dict:
    """Return stats on accumulated training pairs."""
    if not TRAINING_FILE.exists():
        return {"total_pairs": 0, "accepted": 0, "rejected": 0, "pending": 0}

    pairs = [json.loads(line) for line in TRAINING_FILE.read_text().splitlines() if line.strip()]
    accepted = sum(1 for p in pairs if p.get("accepted") is True)
    rejected = sum(1 for p in pairs if p.get("accepted") is False)
    pending = sum(1 for p in pairs if p.get("accepted") is None)

    return {
        "total_pairs": len(pairs),
        "accepted": accepted,
        "rejected": rejected,
        "pending": pending
    }
