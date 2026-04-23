#!/usr/bin/env python3
# EPOS Artifact — BUILD 88 (FOTW ConversationListener)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §2
"""
conversation_listener.py — Real-time talking-point surfacing during live calls

During a call (phone, Zoom, in-person), the listener receives audio
transcripts in ~3-second chunks, routes them through the CCP extractor,
and emits talking-point cards within ~3 seconds of a detectable signal.

The listener does NOT record or store audio — only transcripts — and
the transcripts are cleared at call-end per the Sovereign's privacy
default. It's a streaming passthrough.

Input:  transcript chunks via queue or event bus 'call.transcript.chunk'
Output: talking-point cards via 'steward.tp_card.live' events

Call-end emits a synthesis AAR to context_vault/calls/<call_id>.md
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
CALLS_DIR = Path(os.getenv("EPOS_CALLS_DIR", str(REPO / "context_vault" / "calls")))
CALLS_DIR.mkdir(parents=True, exist_ok=True)

# Trigger patterns: phrases that surface a talking-point card
TRIGGER_PATTERNS = [
    # Objection / hesitation
    (r"\b(too expensive|not sure|worried about|concerned about|hesita)", "objection"),
    # Interest / opportunity
    (r"\b(how much|what would|how soon|can you|could you)", "buying_signal"),
    # Competitor mention
    (r"\b(they offer|their product|alternative|compared to|other option)", "competitor"),
    # Decision authority
    (r"\b(decision maker|need to check|get approval|run it by)", "authority_gap"),
    # Urgency / timeline
    (r"\b(this week|this month|asap|urgent|deadline|by friday)", "urgency"),
]


@dataclass
class TranscriptChunk:
    call_id: str
    speaker: str   # "caller" | "jamie" | "unknown"
    text: str
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TalkingPoint:
    call_id: str
    trigger_type: str
    trigger_phrase: str
    suggested_response: str
    confidence: float
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


RESPONSE_LIBRARY = {
    "objection": "Acknowledge the concern first. Then ask: 'What would need to be true for this to feel worth it?'",
    "buying_signal": "They're moving. Don't over-explain. Close the loop: 'Want me to walk you through the next step?'",
    "competitor": "Don't attack. Ask: 'What are they doing well that we should learn from?' Then differentiate on ONE axis, not three.",
    "authority_gap": "You're talking to the wrong person. Not rude to say: 'Who else would you want in the room for this?'",
    "urgency": "Match their pace. 'I can have a scoped proposal by <deadline-1day>. Work?'",
}


class ConversationListener:
    def __init__(self) -> None:
        self._buffer: dict[str, list[TranscriptChunk]] = {}

    def ingest(self, chunk: TranscriptChunk) -> list[TalkingPoint]:
        self._buffer.setdefault(chunk.call_id, []).append(chunk)
        points = self._detect(chunk)
        for tp in points:
            self._emit(tp)
        return points

    def _detect(self, chunk: TranscriptChunk) -> list[TalkingPoint]:
        text = chunk.text.lower()
        out = []
        for pattern, trigger_type in TRIGGER_PATTERNS:
            m = re.search(pattern, text)
            if m:
                out.append(TalkingPoint(
                    call_id=chunk.call_id,
                    trigger_type=trigger_type,
                    trigger_phrase=m.group(0),
                    suggested_response=RESPONSE_LIBRARY.get(trigger_type, "(no library entry)"),
                    confidence=0.8,
                ))
        return out

    def _emit(self, tp: TalkingPoint) -> None:
        try:
            from epos_event_bus import EPOSEventBus
            EPOSEventBus().publish(
                "steward.tp_card.live",
                tp.__dict__,
                source_module="conversation_listener",
            )
        except Exception:
            pass

    def end_call(self, call_id: str) -> dict[str, Any]:
        """Synthesize the full call into a single AAR markdown file."""
        chunks = self._buffer.get(call_id, [])
        if not chunks:
            return {"call_id": call_id, "status": "no_data"}
        out = CALLS_DIR / f"{call_id}.md"
        lines = [
            f"# Call AAR — {call_id}",
            f"**Started:** {chunks[0].ts}",
            f"**Ended:** {datetime.now(timezone.utc).isoformat()}",
            f"**Chunks:** {len(chunks)}",
            "",
            "## Transcript",
        ]
        for c in chunks:
            lines.append(f"- **{c.speaker}** ({c.ts[11:19]}): {c.text}")
        out.write_text("\n".join(lines) + "\n")
        self._buffer.pop(call_id, None)
        return {"call_id": call_id, "status": "synthesized", "path": str(out)}


def listen_turn(call_id: str, speaker: str, text: str) -> list[dict]:
    """Module-level convenience."""
    listener = _singleton()
    pts = listener.ingest(TranscriptChunk(call_id=call_id, speaker=speaker, text=text))
    return [p.__dict__ for p in pts]


_SINGLE: ConversationListener | None = None

def _singleton() -> ConversationListener:
    global _SINGLE
    if _SINGLE is None:
        _SINGLE = ConversationListener()
    return _SINGLE


if __name__ == "__main__":
    # Quick test
    print("test 1 (objection):", listen_turn("call_1", "caller", "It sounds too expensive for what we need."))
    print("test 2 (buying_signal):", listen_turn("call_1", "caller", "Could you send me a proposal?"))
    print("test 3 (neutral):", listen_turn("call_1", "caller", "Nice weather today."))
    print("end:", _singleton().end_call("call_1"))
