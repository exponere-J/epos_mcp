#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/api.py — FastAPI Voice Endpoints
============================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

FastAPI router mounted on epos-core.
Provides REST endpoints for the full voice pipeline.

Mount in command_center.py or app.py:
    from epos.voice.api import router as voice_router
    app.include_router(voice_router)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from epos.voice.pipeline import process_voice_input
from epos.voice.vault_search import search_vault, build_index
from epos.voice.vocabulary import add_correction, load_vocabulary
from epos.voice.training_logger import get_training_stats

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/session")
async def voice_session(audio: UploadFile = File(...)):
    """Full voice pipeline. Audio in → reformulated directive + elements out.

    Accepts: audio/webm, audio/wav, audio/mp4
    Returns: {session_id, raw_transcript, corrected_transcript, reformulated,
               coaching_cue, elements, vault_citations, tts_status}
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    result = await process_voice_input(audio_bytes, audio.filename or "audio.webm")
    return result


@router.post("/search")
async def vault_query(query: str, top_k: int = 5):
    """Semantic search across Context Vault using nomic-embed-text.

    Returns: {results: [{path, content_preview, relevance}]}
    """
    try:
        results = search_vault(query, top_k=top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vault search unavailable: {e}")


@router.post("/index")
async def rebuild_index(force: bool = False):
    """Rebuild or update vault embedding index.

    Returns: {total, new}
    """
    try:
        result = build_index(force_rebuild=force)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Index build failed: {e}")


@router.get("/vocabulary")
async def get_vocabulary():
    """Get current EPOS vocabulary corrections.

    Returns: dict of {heard: correct} pairs
    """
    return load_vocabulary()


@router.post("/vocabulary")
async def add_vocab_correction(heard: str, correct: str):
    """Add a new vocabulary correction (persisted to vault).

    Returns: {status, heard, correct}
    """
    add_correction(heard, correct)
    return {"status": "added", "heard": heard, "correct": correct}


@router.get("/training/stats")
async def training_stats():
    """Get stats on accumulated QLoRA training pairs.

    Returns: {total_pairs, accepted, rejected, pending}
    """
    return get_training_stats()


@router.get("/audio/{session_id}")
async def get_audio(session_id: str):
    """Retrieve TTS audio for a session.

    Returns: WAV file stream
    """
    audio_path = Path(f"/app/context_vault/voice/sessions/{session_id}_response.wav")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found for session")
    return FileResponse(str(audio_path), media_type="audio/wav")
