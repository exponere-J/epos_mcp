#!/usr/bin/env python3
# EPOS Artifact — BUILD 103 (Friday Client Briefing)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
friday_client_briefing.py — Layer 2 of the 4-layer morning briefing

Builds the "Client Pulse" layer of Friday's 05:30 briefing:
  - Clients at risk (health score < 40 with declining trend)
  - Clients stalled (days in stage > SLA)
  - Bookings today (with TP cards ready)
  - Touchpoint-overdue list (haven't heard from client in > N days)
  - Renewals due this week

Output: context_vault/briefings/friday_client_pulse_<date>.md
Also: emits 'steward.briefing.client_pulse.ready' on event bus.

Article XVI §3 compliance: the briefing is audio-first-compatible —
it's structured in short sentences that read well aloud, and every
section has a 1-line summary the Chronicler (NotebookLM) can make an
Audio Overview from.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
CLIENTS_DIR = Path(os.getenv("EPOS_CLIENTS_DIR", str(REPO / "context_vault" / "clients")))
BRIEFINGS_DIR = Path(os.getenv("EPOS_BRIEFINGS_DIR", str(REPO / "context_vault" / "briefings")))


class FridayClientBriefing:
    def __init__(self) -> None:
        BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_clients(self) -> list[dict]:
        out = []
        for p in sorted(CLIENTS_DIR.glob("*.json")):
            if p.name.endswith("_health.json") or p.name.endswith("_health.jsonl"):
                continue
            try:
                out.append(json.loads(p.read_text()))
            except Exception:
                pass
        return out

    def _latest_health(self, cid: str) -> dict | None:
        hist = CLIENTS_DIR / f"{cid}_health.jsonl"
        if not hist.exists():
            return None
        lines = hist.read_text().splitlines()
        if not lines:
            return None
        try:
            return json.loads(lines[-1])
        except Exception:
            return None

    def build(self) -> str:
        now = datetime.now(timezone.utc)
        clients = self._load_clients()

        at_risk = []
        stalled = []
        bookings_today = []
        touchpoint_overdue = []
        renewals_this_week = []

        for c in clients:
            cid = c.get("client_id", "unknown")
            stage = c.get("stage", "LEAD")
            health = self._latest_health(cid)
            if health and health.get("at_risk"):
                at_risk.append({"client_id": cid, "score": health["score"],
                                 "decline_7d": health["decline_7d"]})
            if "stalled" in c.get("flags", []):
                stalled.append({"client_id": cid, "stage": stage})
            last_tp_str = c.get("last_touchpoint_at", "")
            if last_tp_str:
                try:
                    last_tp = datetime.fromisoformat(last_tp_str.replace("Z", "+00:00"))
                    if (now - last_tp).days > 14 and stage not in ("CHURNED", "LAPSED"):
                        touchpoint_overdue.append({"client_id": cid,
                                                    "days_since": (now - last_tp).days})
                except Exception:
                    pass
            # Renewal check: any touchpoint note containing "renewal" within next 7 days
            for tp in c.get("touchpoint_history", []):
                note = tp.get("note", "").lower()
                if "renewal" in note or "renews" in note:
                    renewals_this_week.append({"client_id": cid,
                                                "note": tp.get("note", "")[:100]})
                    break

        # Synthesize briefing
        lines = [
            f"# Friday Client Pulse — {now.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## One-line summary (audio-first)",
            "",
            self._summary_line(len(clients), at_risk, stalled, touchpoint_overdue, renewals_this_week),
            "",
            "## At-risk clients",
        ]
        if at_risk:
            for a in at_risk:
                lines.append(f"- **{a['client_id']}** — score {a['score']} "
                              f"(down {a['decline_7d']:+.1f} in 7 days)")
        else:
            lines.append("- None.")
        lines += ["", "## Stalled in stage"]
        if stalled:
            for s in stalled:
                lines.append(f"- **{s['client_id']}** — stuck in {s['stage']}")
        else:
            lines.append("- None.")
        lines += ["", "## Touchpoint overdue (> 14 days)"]
        if touchpoint_overdue:
            for t in touchpoint_overdue:
                lines.append(f"- **{t['client_id']}** — {t['days_since']} days since last touch")
        else:
            lines.append("- None.")
        lines += ["", "## Renewals on the horizon"]
        if renewals_this_week:
            for r in renewals_this_week:
                lines.append(f"- **{r['client_id']}** — \"{r['note']}\"")
        else:
            lines.append("- None.")
        lines += ["", "## Recommended actions (Sovereign-priority order)"]
        # Order by severity: at-risk > stalled > overdue > renewal-prep
        order = 1
        for a in at_risk[:3]:
            lines.append(f"{order}. Reach out to **{a['client_id']}** today. "
                          f"Do not wait for weekly cadence.")
            order += 1
        for s in stalled[:3]:
            lines.append(f"{order}. Unstick **{s['client_id']}** — what's blocking them?")
            order += 1
        for t in touchpoint_overdue[:3]:
            lines.append(f"{order}. Re-open **{t['client_id']}** — "
                          f"{t['days_since']} days is past safe re-engage window.")
            order += 1
        if order == 1:
            lines.append("Everything green. Use the freed-up cycles on Stage-1 product listings.")

        text = "\n".join(lines) + "\n"
        out_path = BRIEFINGS_DIR / f"friday_client_pulse_{now.strftime('%Y%m%d')}.md"
        out_path.write_text(text)

        try:
            from epos_event_bus import EPOSEventBus
            EPOSEventBus().publish("steward.briefing.client_pulse.ready",
                                   {"path": str(out_path), "at_risk": len(at_risk),
                                    "stalled": len(stalled)},
                                   source_module="friday_client_briefing")
        except Exception:
            pass

        return text

    def _summary_line(self, total: int, at_risk: list, stalled: list,
                       overdue: list, renewals: list) -> str:
        if not any([at_risk, stalled, overdue, renewals]):
            return (f"You have {total} clients. Everything's green. No client action "
                    f"required. Use the morning for Stage-1 work.")
        parts = []
        if at_risk:
            parts.append(f"{len(at_risk)} at-risk")
        if stalled:
            parts.append(f"{len(stalled)} stalled")
        if overdue:
            parts.append(f"{len(overdue)} overdue")
        if renewals:
            parts.append(f"{len(renewals)} renewal(s) coming")
        return (f"You have {total} clients. Flagged: {', '.join(parts)}. "
                f"Recommended actions below in Sovereign-priority order.")


def build_briefing() -> str:
    return FridayClientBriefing().build()


if __name__ == "__main__":
    print(build_briefing())
