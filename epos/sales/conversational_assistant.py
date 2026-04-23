#!/usr/bin/env python3
# EPOS Artifact — BUILD 55 (Conversational Sales Assistant)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §2, §3
"""
conversational_assistant.py — Pre/live/post call sales substrate

Three phases per call:

  PRE-CALL:  30 min before, build TP card (using ops.talking_point_cards),
             load CCP from client's prior touchpoints + Brand DNA,
             surface open objections, suggest opening + close

  LIVE:      During the call, the FOTW ConversationListener (build 88)
             streams talking-point cards; this module's live endpoint
             merges live TPs with the pre-call TP card into a rolling
             view Sovereign can glance at

  POST-CALL: synthesize transcript → decisions, open questions, next
             actions, commitment level (1–10). Write AAR to
             context_vault/calls/<call_id>_aar.md. Route action items
             to PM surface.
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


@dataclass
class PreCallContext:
    call_id: str
    client_id: str
    tp_card_path: str
    open_objections: list[str] = field(default_factory=list)
    suggested_open: str = ""
    suggested_close: str = ""
    brand_dna_summary: str = ""


def pre_call(call_id: str, client_id: str) -> PreCallContext:
    # Generate TP card via ops.talking_point_cards
    try:
        from epos.ops.talking_point_cards import TalkingPointCardGenerator
        gen = TalkingPointCardGenerator()
        card = gen.generate(client_id, datetime.now(timezone.utc).isoformat())
    except Exception:
        class _Stub:
            open_objections = []
            recommended_open = "(TP card unavailable)"
            recommended_close = ""
        card = _Stub()

    # Load brand DNA summary
    brand_file = REPO / "context_vault" / "brand" / "brand_dna.json"
    brand_summary = ""
    if brand_file.exists():
        try:
            brand = json.loads(brand_file.read_text())
            brand_summary = f"{brand.get('name', '')}: {brand.get('promise', '')[:200]}"
        except Exception:
            pass

    ctx = PreCallContext(
        call_id=call_id,
        client_id=client_id,
        tp_card_path=f"context_vault/briefings/tp_cards/{client_id}_*.md",
        open_objections=getattr(card, "open_objections", []),
        suggested_open=getattr(card, "recommended_open", ""),
        suggested_close=getattr(card, "recommended_close", ""),
        brand_dna_summary=brand_summary,
    )

    # Emit event for Friday to include in briefing
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish("sales.pre_call.ready",
                                {"call_id": call_id, "client_id": client_id},
                                source_module="conversational_assistant")
    except Exception:
        pass
    return ctx


def post_call_synthesis(call_id: str, transcript: str,
                         client_id: str = "") -> dict[str, Any]:
    """Parse transcript into decisions, questions, actions, commitment score."""
    decisions = []
    questions = []
    actions = []
    commitment_signals = 0

    sentences = re.split(r"(?<=[.!?])\s+", transcript)
    for s in sentences:
        low = s.lower().strip()
        if not low:
            continue
        if any(k in low for k in ("we decided", "we'll go with", "let's do",
                                     "yes", "agreed", "let's proceed")):
            decisions.append(s.strip())
            commitment_signals += 1
        if re.search(r"\?$", s) or low.startswith(("what", "how", "when", "can", "would")):
            questions.append(s.strip())
        if any(k in low for k in ("i'll", "you'll", "we'll", "next step",
                                     "follow up", "send you", "get back")):
            actions.append(s.strip())
            commitment_signals += 1

    # Commitment 1–10 based on decision + action density
    commitment = min(10, max(1, 3 + commitment_signals * 2))

    aar = {
        "call_id": call_id,
        "client_id": client_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decisions": decisions[:10],
        "open_questions": questions[:10],
        "action_items": actions[:10],
        "commitment_score": commitment,
        "transcript_chars": len(transcript),
    }

    # Write markdown AAR
    out = CALLS_DIR / f"{call_id}_aar.md"
    decisions_block = [f"- {d}" for d in decisions[:10]] or ["- (none)"]
    questions_block = [f"- {q}" for q in questions[:10]] or ["- (none)"]
    actions_block = [f"- [ ] {a}" for a in actions[:10]] or ["- (none)"]
    lines = [
        f"# Call AAR — {call_id}",
        f"**Client:** {client_id}",
        f"**Generated:** {aar['generated_at']}",
        f"**Commitment score:** {commitment}/10",
        "",
        "## Decisions made",
        *decisions_block,
        "",
        "## Open questions",
        *questions_block,
        "",
        "## Action items",
        *actions_block,
    ]
    out.write_text("\n".join(lines) + "\n")
    aar["aar_path"] = str(out)

    # Route actions to PM surface
    try:
        from epos_event_bus import EPOSEventBus
        bus = EPOSEventBus()
        for a in actions[:10]:
            bus.publish("pm.task.add",
                         {"title": a, "source": "call", "call_id": call_id},
                         source_module="conversational_assistant")
        bus.publish("sales.post_call.ready", aar, source_module="conversational_assistant")
    except Exception:
        pass

    return aar


class ConversationalSalesAssistant:
    """Container class for the three phases."""

    def pre(self, call_id: str, client_id: str) -> PreCallContext:
        return pre_call(call_id, client_id)

    def synthesize(self, call_id: str, transcript: str, client_id: str = "") -> dict[str, Any]:
        return post_call_synthesis(call_id, transcript, client_id)


if __name__ == "__main__":
    ctx = pre_call("demo_call_1", "demo_client")
    print(f"pre-call ready for {ctx.client_id}")
    demo_transcript = (
        "We'd like to start with the diagnostic tier. Let's do it. "
        "Can you send me a proposal by Friday? I'll review over the weekend. "
        "We decided to go with the $497 option for now."
    )
    r = post_call_synthesis("demo_call_1", demo_transcript, "demo_client")
    print(json.dumps(r, indent=2))
