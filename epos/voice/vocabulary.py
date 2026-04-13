#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/vocabulary.py — EPOS Term Correction Post-Processor
==============================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Corrects known transcription errors for EPOS technical vocabulary.
Corrections stored in context_vault/voice/vocabulary.json (editable, grows with use).
"""

import json
import re
from pathlib import Path

VOCAB_PATH = Path("/app/context_vault/voice/vocabulary.json")

DEFAULT_CORRECTIONS = {
    "epochs": "EPOS",
    "e-pos": "EPOS",
    "epos": "EPOS",
    "s.t.t.": "STT",
    "s t t": "STT",
    "t.t.s.": "TTS",
    "t t s": "TTS",
    "see see pee": "CCP",
    "c.c.p.": "CCP",
    "c c p": "CCP",
    "t.t.l.g.": "TTLG",
    "t t l g": "TTLG",
    "s.c.c.": "SCC",
    "s c c": "SCC",
    "kew laura": "QLoRA",
    "q laura": "QLoRA",
    "qlora": "QLoRA",
    "a.a.r.": "AAR",
    "a a r": "AAR",
    "que when": "Qwen",
    "kwen": "Qwen",
    "hey gen": "HeyGen",
    "f.o.t.w.": "FOTW",
    "fly on the wall": "FOTW",
    "browser use": "BrowserUse",
    "computer use": "ComputerUse",
    "lite llm": "LiteLLM",
    "open router": "OpenRouter",
    "hetzner": "Hetzner",
    "piper": "Piper"
}


def load_vocabulary() -> dict:
    """Load corrections from vault. Falls back to defaults if not present."""
    if VOCAB_PATH.exists():
        return json.loads(VOCAB_PATH.read_text())
    return DEFAULT_CORRECTIONS


def save_vocabulary(vocab: dict) -> None:
    """Persist updated vocabulary to vault."""
    VOCAB_PATH.parent.mkdir(parents=True, exist_ok=True)
    VOCAB_PATH.write_text(json.dumps(vocab, indent=2))


def correct_transcript(raw_transcript: str) -> tuple:
    """Apply vocabulary corrections. Returns (corrected_str, changes_list)."""
    vocab = load_vocabulary()
    corrected = raw_transcript
    changes = []

    # Apply longest matches first to avoid partial substitutions
    for wrong, right in sorted(vocab.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        if pattern.search(corrected):
            corrected = pattern.sub(right, corrected)
            changes.append({"from": wrong, "to": right})

    return corrected, changes


def add_correction(heard: str, correct: str) -> None:
    """Add a new correction. Called when Jamie overrides a transcription."""
    vocab = load_vocabulary()
    vocab[heard.lower()] = correct
    save_vocabulary(vocab)
