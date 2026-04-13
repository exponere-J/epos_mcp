#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/speaker.py — Piper TTS Text-to-Speech
=================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Converts text to speech locally via Piper TTS.
Gracefully falls back to text-only if Piper not installed.

Install:
    pip install piper-tts
    piper --model en_US-lessac-medium --download-dir /app/models/piper/
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
OUTPUT_DIR = EPOS_ROOT / "context_vault" / "voice" / "sessions"


def speak(text: str, session_id: str = None) -> dict:
    """Convert text to speech using Piper TTS. Returns audio result dict.

    Returns:
        On success:  {"status": "complete", "audio_path": str, "text_length": int, "audio_size": int}
        On failure:  {"status": "not_installed"|"failed"|"timeout", "error": str, "fallback": "text_only"}
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not session_id:
        session_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    output_path = OUTPUT_DIR / f"{session_id}_response.wav"

    try:
        process = subprocess.run(
            ["piper", "--model", "en_US-lessac-medium", "--output_file", str(output_path)],
            input=text.encode(),
            capture_output=True,
            timeout=30
        )

        if process.returncode == 0 and output_path.exists():
            return {
                "status": "complete",
                "audio_path": str(output_path),
                "text_length": len(text),
                "audio_size": output_path.stat().st_size
            }
        else:
            return {
                "status": "failed",
                "error": process.stderr.decode()[:500],
                "fallback": "text_only"
            }

    except FileNotFoundError:
        return {
            "status": "not_installed",
            "error": "Piper TTS not found. Install: pip install piper-tts",
            "fallback": "text_only"
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": "TTS generation exceeded 30 second limit",
            "fallback": "text_only"
        }
