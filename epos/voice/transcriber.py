#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/transcriber.py — Groq Whisper STT + Raw Capture
===========================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Accepts audio bytes, transcribes via Groq Whisper-large-v3-turbo,
saves raw capture with full fidelity to context_vault/raw_captures/.
"""

import os
import httpx
import json
from datetime import datetime
from pathlib import Path

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
VAULT_PATH = EPOS_ROOT / "context_vault" / "raw_captures"


async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Send audio to Groq Whisper API. Returns transcript dict.

    Returns:
        {"text": str, ...}  — Groq Whisper response
    """
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers=headers,
            files={"file": (filename, audio_bytes, "audio/webm")},
            data={"model": "whisper-large-v3-turbo", "response_format": "json"}
        )
        response.raise_for_status()
        return response.json()


def save_raw_capture(transcript: str, audio_bytes: bytes) -> str:
    """Save raw audio + metadata to immutable vault. Full fidelity.

    Returns:
        capture_id — format: CAP-YYYYMMDDTHHMMSSZ
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    capture_id = f"CAP-{timestamp}"

    audio_dir = VAULT_PATH / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{capture_id}.webm"
    audio_path.write_bytes(audio_bytes)

    capture_data = {
        "capture_id": capture_id,
        "source_type": "voice_dictation",
        "raw_transcript": transcript,
        "audio_path": str(audio_path),
        "audio_size_bytes": len(audio_bytes),
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "processed": False
    }

    VAULT_PATH.mkdir(parents=True, exist_ok=True)
    meta_path = VAULT_PATH / f"{capture_id}.json"
    meta_path.write_text(json.dumps(capture_data, indent=2))

    return capture_id
