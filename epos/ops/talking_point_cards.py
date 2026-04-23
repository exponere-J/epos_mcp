#!/usr/bin/env python3
# EPOS Artifact — BUILD 101 (Talking Point Cards)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
talking_point_cards.py — Pre-call one-page briefing for the Sovereign

Given a client_id and an upcoming booking, generate a Talking Point
Card: avatar, last-3-touchpoints, open objections, recommended open,
recommended close, suggested ask, context anchors.

Card renders to:
    context_vault/briefings/tp_cards/<client_id>_<booking_ts>.md

Also emits 'steward.tp_card.ready' on the event bus so Friday can
surface it in the morning briefing.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
CLIENTS_DIR = Path(os.getenv("EPOS_CLIENTS_DIR", str(REPO / "context_vault" / "clients")))
CARDS_DIR = Path(os.getenv("EPOS_TP_CARDS_DIR", str(REPO / "context_vault" / "briefings" / "tp_cards")))

OPENING_TEMPLATES = {
    "default":              "Jamie: 'Appreciate the time. I want to use it for two things today: <X> and <Y>. Work for you?'",
    "small_service_owner":  "Jamie: 'Thanks for making the time. Before we dive in — how was your week?'",
    "enterprise_innovation":"Jamie: 'I know your cycle is long, so I want to be efficient. 3 things I want to cover today.'",
    "growth_hacker":        "Jamie: 'Quick one — can I show you the 60-second version first, then you tell me if we go deeper?'",
}

CLOSING_TEMPLATES = {
    "default":              "Jamie: 'Two things I want by end-of-call: <commitment> and <next-step>. Shall we?'",
    "small_service_owner":  "Jamie: 'Let's not decide today. How about I send a written recap and you sit with it?'",
    "enterprise_innovation":"Jamie: 'What does your procurement path look like from here?'",
    "growth_hacker":        "Jamie: 'Pilot tomorrow?'",
}


@dataclass
class TalkingPointCard:
    client_id: str
    booking_timestamp: str
    avatar: str
    stage: str
    last_touchpoints: list[dict] = field(default_factory=list)
    open_objections: list[str] = field(default_factory=list)
    recommended_open: str = ""
    recommended_close: str = ""
    suggested_ask: str = ""
    context_anchors: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"# Talking Point Card — {self.client_id}",
            f"**Booking:** {self.booking_timestamp}",
            f"**Avatar:** {self.avatar}",
            f"**Stage:** {self.stage}",
            "",
            "## Last 3 touchpoints",
        ]
        for tp in self.last_touchpoints[-3:]:
            lines.append(f"- {tp.get('timestamp', '?')} — {tp.get('note', '')}")
        lines.append("")
        lines.append("## Open objections")
        for o in self.open_objections:
            lines.append(f"- {o}")
        lines.append("")
        lines.append("## Recommended open")
        lines.append(self.recommended_open)
        lines.append("")
        lines.append("## Recommended close")
        lines.append(self.recommended_close)
        lines.append("")
        lines.append("## Suggested ask")
        lines.append(self.suggested_ask)
        if self.context_anchors:
            lines.append("")
            lines.append("## Context anchors")
            for a in self.context_anchors:
                lines.append(f"- {a}")
        if self.flags:
            lines.append("")
            lines.append(f"**Flags:** {', '.join(self.flags)}")
        return "\n".join(lines) + "\n"


class TalkingPointCardGenerator:
    def __init__(self) -> None:
        CARDS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_client(self, client_id: str) -> dict[str, Any]:
        p = CLIENTS_DIR / f"{client_id}.json"
        if not p.exists():
            return {"client_id": client_id, "archetype": "default",
                    "stage": "LEAD", "touchpoint_history": []}
        return json.loads(p.read_text())

    def generate(self, client_id: str, booking_ts: str,
                 suggested_ask: str | None = None) -> TalkingPointCard:
        client = self._load_client(client_id)
        archetype = client.get("archetype", "default")

        # Extract open objections from touchpoints where notes matched an objection pattern
        objections = []
        for tp in client.get("touchpoint_history", []):
            note = tp.get("note", "").lower()
            if any(k in note for k in ("objection", "concern", "pushback", "too expensive", "not now")):
                objections.append(tp.get("note", ""))

        card = TalkingPointCard(
            client_id=client_id,
            booking_timestamp=booking_ts,
            avatar=archetype,
            stage=client.get("stage", "LEAD"),
            last_touchpoints=client.get("touchpoint_history", [])[-3:],
            open_objections=objections[-3:],
            recommended_open=OPENING_TEMPLATES.get(archetype, OPENING_TEMPLATES["default"]),
            recommended_close=CLOSING_TEMPLATES.get(archetype, CLOSING_TEMPLATES["default"]),
            suggested_ask=suggested_ask or "Confirm next concrete step + date.",
            context_anchors=client.get("notes", [])[-5:],
            flags=client.get("flags", []),
        )

        out = CARDS_DIR / f"{client_id}_{booking_ts.replace(':', '-')}.md"
        out.write_text(card.render())

        try:
            from epos_event_bus import EPOSEventBus
            EPOSEventBus().publish("steward.tp_card.ready",
                                   {"client_id": client_id, "path": str(out)},
                                   source_module="talking_point_cards")
        except Exception:
            pass

        return card


def generate_card(client_id: str, booking_ts: str | None = None,
                   suggested_ask: str | None = None) -> str:
    ts = booking_ts or datetime.now(timezone.utc).isoformat()
    card = TalkingPointCardGenerator().generate(client_id, ts, suggested_ask)
    return card.render()


if __name__ == "__main__":
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else "demo_client"
    print(generate_card(cid))
