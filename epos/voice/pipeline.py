#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/pipeline.py — EPOS Voice Pipeline (Full Flow)
=========================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

The complete voice pipeline:
  Audio → STT (Groq Whisper) → Vocabulary Correction → Vault Search
  → Reasoning (Qwen3-32B) → TTS (Piper) → Training Log

Each step publishes to Event Bus. Full session logged for QLoRA training.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from epos.voice.transcriber import transcribe, save_raw_capture
from epos.voice.vocabulary import correct_transcript
from epos.voice.vault_search import search_vault
from epos.voice.reformulator import reformulate
from epos.voice.speaker import speak
from epos.voice.training_logger import log_session
from epos.rewards.publish_reward import publish_reward

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))

# Wire Event Bus lazily
_BUS = None
try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    pass


def _publish(event_type: str, payload: dict) -> None:
    if _BUS:
        try:
            _BUS.publish(event_type, payload, source_module="voice_pipeline")
        except Exception:
            pass


def _reward(signal_name: str, value: float, signal_type: str = "process",
            context: str = "", needs_review: bool = False) -> None:
    """Publish reward signal from voice pipeline. Non-fatal."""
    try:
        publish_reward(
            signal_name=signal_name,
            value=value,
            signal_type=signal_type,
            source="voice_pipeline",
            context=context,
            needs_review=needs_review,
        )
    except Exception:
        pass


async def process_voice_input(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Full voice pipeline. Audio in → reformulated directive out.

    Returns:
        Full pipeline result dict with session_id, transcripts, reformulation,
        vault citations, TTS status, and extracted elements.
    """
    session_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    session_log = {"session_id": session_id, "steps": []}

    _publish("voice.session.start", {"session_id": session_id})

    # Step 1: Transcribe (Groq Whisper)
    stt_result = await transcribe(audio_bytes, filename)
    raw_transcript = stt_result.get("text", "")
    session_log["steps"].append({"step": "stt", "output": raw_transcript[:200]})
    _publish("voice.stt.complete", {"session_id": session_id, "length": len(raw_transcript)})

    # Step 2: Save raw capture (full fidelity — immutable)
    capture_id = save_raw_capture(raw_transcript, audio_bytes)
    session_log["steps"].append({"step": "raw_capture", "capture_id": capture_id})
    _reward("raw_capture_saved", 0.2,
            context=f"Audio + metadata saved: {capture_id}")

    # Step 3: Vocabulary correction
    corrected, vocab_changes = correct_transcript(raw_transcript)
    session_log["steps"].append({"step": "vocabulary", "changes": vocab_changes})
    _reward("vocabulary_correction_applied", 0.1,
            context=f"Applied {len(vocab_changes)} corrections")

    # Step 4: Vault semantic search
    try:
        vault_docs = search_vault(corrected, top_k=5)
    except Exception:
        vault_docs = []  # Ollama may not be available — non-fatal
    session_log["steps"].append({
        "step": "vault_search",
        "docs_found": len(vault_docs),
        "top_doc": vault_docs[0]["path"] if vault_docs else "none"
    })
    _reward("vault_search_executed", 0.2,
            context=f"Found {len(vault_docs)} relevant documents")

    # Step 5: Reasoning + reformulation (Qwen3-32B via LiteLLM)
    state_path = EPOS_ROOT / "context_vault" / "state" / "organism_state.json"
    organism_state = {}
    if state_path.exists():
        try:
            organism_state = json.loads(state_path.read_text())
        except Exception:
            pass

    reformulation = reformulate(corrected, vault_docs, organism_state)
    elements = reformulation.get("elements", [])
    session_log["steps"].append({
        "step": "reformulation",
        "reformulated": reformulation.get("reformulated", "")[:200],
        "elements_extracted": len(elements)
    })
    _publish("voice.reformulation.complete", {
        "session_id": session_id,
        "elements_count": len(elements)
    })
    _reward("reformulation_generated", 0.2,
            context=f"Extracted {len(elements)} elements")

    # Step 5.5: CCP Element Extraction (after reformulation, before TTS — M1 of 20260414-03)
    try:
        from epos.ccp.pipeline import CCPPipeline
        ccp = CCPPipeline()
        ccp_result = ccp.process_text(
            text=corrected,
            source_type="voice_capture",
            source_capture_id=capture_id,
        )
        session_log["steps"].append({
            "step": "ccp_extraction",
            "elements_extracted": ccp_result.get("elements_extracted", 0),
            "auto_routed": ccp_result.get("routing", {}).get("summary", {}).get("auto_routed", 0),
            "pending_confirmation": ccp_result.get("routing", {}).get("summary", {}).get("pending_confirmation", 0),
            "pm_written": ccp_result.get("pm_written", 0),
        })
        _reward("voice_ccp_extraction",
                min(ccp_result.get("elements_extracted", 0) * 0.1, 0.5),
                signal_type="process",
                context=f"Extracted {ccp_result.get('elements_extracted', 0)} elements from voice session {capture_id}")
    except Exception as e:
        session_log["steps"].append({
            "step": "ccp_extraction",
            "error": str(e)[:200],
            "note": "CCP extraction non-fatal — session continues",
        })
        ccp_result = {"elements_extracted": 0, "routing": {"auto_routed": [], "pending_confirmation": []}}

    # Step 6: TTS (Piper) — graceful fallback
    tts_text = reformulation.get("coaching_cue", "") or reformulation.get("reformulated", "")
    tts_result = speak(tts_text, session_id)
    session_log["steps"].append({"step": "tts", "status": tts_result["status"]})
    _reward("tts_attempted", 0.1,
            context=f"TTS status: {tts_result['status']}")

    # Step 7: Log session for training
    log_session(session_id, session_log, reformulation)

    _publish("voice.session.complete", {
        "session_id": session_id,
        "capture_id": capture_id,
        "tts_status": tts_result["status"]
    })

    return {
        "session_id": session_id,
        "capture_id": capture_id,
        "raw_transcript": raw_transcript,
        "corrected_transcript": corrected,
        "vocabulary_changes": vocab_changes,
        "vault_citations": [
            {"path": d["path"], "relevance": d["relevance"]}
            for d in vault_docs[:3]
        ],
        "reformulated": reformulation.get("reformulated", ""),
        "coaching_cue": reformulation.get("coaching_cue", ""),
        "elements": reformulation.get("elements", []),
        "citations": reformulation.get("citations", []),
        "tts_audio": tts_result.get("audio_path"),
        "tts_status": tts_result["status"],
        "ccp_elements_extracted": ccp_result.get("elements_extracted", 0),
        "ccp_auto_routed": ccp_result.get("routing", {}).get("summary", {}).get("auto_routed", 0),
        "ccp_pending": ccp_result.get("routing", {}).get("summary", {}).get("pending_confirmation", 0),
        "ccp_pending_elements": ccp_result.get("routing", {}).get("pending_confirmation", []),
    }
