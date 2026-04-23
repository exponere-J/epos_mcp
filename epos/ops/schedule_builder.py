#!/usr/bin/env python3
# EPOS Artifact — BUILD 69 (Schedule Builder)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
schedule_builder.py — Daily 06:00 schedule from Cal.com + PM surface

Pulls:
  - Cal.com bookings for today (via Cal.com API OR local webhook-log)
  - PM surface open action items due today
  - Friday's client-pulse flags (at-risk clients)

Synthesizes a single daily schedule at:
    context_vault/briefings/daily_schedule_<YYYYMMDD>.md

Structure:
  - Fixed blocks (meetings)
  - Focus blocks (deep work — 2×90 min windows by default)
  - Admin block (30 min)
  - Flex time

Emits 'steward.schedule.ready' for Friday's 05:30 briefing.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
BRIEFINGS_DIR = Path(os.getenv("EPOS_BRIEFINGS_DIR", str(REPO / "context_vault" / "briefings")))
CALCOM_LOG = Path(os.getenv("EPOS_CALCOM_LOG",
                              str(REPO / "context_vault" / "calcom" / "bookings.jsonl")))

DEEP_WORK_WINDOW_A = ("07:00", "08:30")
DEEP_WORK_WINDOW_B = ("14:00", "15:30")
ADMIN_BLOCK = ("12:00", "12:30")


def _today_bookings() -> list[dict]:
    if not CALCOM_LOG.exists():
        return []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = []
    for line in CALCOM_LOG.read_text().splitlines():
        try:
            b = json.loads(line)
            if b.get("start", "").startswith(today):
                out.append(b)
        except Exception:
            pass
    return sorted(out, key=lambda b: b.get("start", ""))


def _open_tasks() -> list[dict]:
    try:
        from epos.pm.store import PMStore  # type: ignore
        store = PMStore()
        rows = store.list_all() if hasattr(store, "list_all") else []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return [r for r in rows
                if r.get("status") in ("open", "pending")
                and (r.get("due_date") or "").startswith(today)]
    except Exception:
        return []


def _at_risk_clients() -> list[dict]:
    try:
        from epos.ops.client_health_scoring import score_all
        scored = score_all()
        return [s for s in scored if isinstance(s, dict) and s.get("at_risk")]
    except Exception:
        return []


def build_schedule() -> str:
    now = datetime.now(timezone.utc)
    bookings = _today_bookings()
    tasks = _open_tasks()
    at_risk = _at_risk_clients()

    lines = [
        f"# Daily Schedule — {now.strftime('%Y-%m-%d')}",
        f"*Generated {now.strftime('%H:%M UTC')} · Schedule Builder v1*",
        "",
        "## Fixed blocks (meetings)",
    ]
    if bookings:
        for b in bookings:
            lines.append(f"- {b.get('start', '?')} — **{b.get('title', 'Meeting')}** with "
                          f"{b.get('attendee_name', 'unknown')}")
    else:
        lines.append("- *No bookings today.*")

    lines += ["", "## Deep-work windows (protected)"]
    lines.append(f"- **{DEEP_WORK_WINDOW_A[0]}–{DEEP_WORK_WINDOW_A[1]}** — Morning deep work")
    lines.append(f"- **{DEEP_WORK_WINDOW_B[0]}–{DEEP_WORK_WINDOW_B[1]}** — Afternoon deep work")

    lines += ["", f"## Admin block", f"- **{ADMIN_BLOCK[0]}–{ADMIN_BLOCK[1]}** — Inbox / invoices"]

    lines += ["", "## Today's action items (from PM surface)"]
    if tasks:
        for t in tasks[:7]:
            lines.append(f"- [ ] {t.get('title', '?')} (priority: {t.get('priority', 'n/a')})")
        if len(tasks) > 7:
            lines.append(f"- … + {len(tasks) - 7} more in the PM surface")
    else:
        lines.append("- *No action items due today.*")

    lines += ["", "## At-risk clients to touch today"]
    if at_risk:
        for c in at_risk[:3]:
            lines.append(f"- **{c.get('client_id', '?')}** — score {c.get('score', 0):.0f} "
                          f"(down {c.get('decline_7d', 0):+.1f} in 7d)")
    else:
        lines.append("- *None flagged.*")

    lines += ["", "## Today's recommended cadence"]
    lines.append("1. 07:00 — Deep work (finish highest-leverage task)")
    lines.append("2. 09:00 — Morning briefing review (Friday)")
    if bookings:
        lines.append("3. Meetings as scheduled")
    if at_risk:
        lines.append(f"4. Touch at-risk clients before noon")
    lines.append("5. 14:00 — Second deep-work window")
    lines.append("6. End-of-day: decision journal + tomorrow's one-thing-to-move")

    out = BRIEFINGS_DIR / f"daily_schedule_{now.strftime('%Y%m%d')}.md"
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    out.write_text(text)

    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish("steward.schedule.ready",
                                {"path": str(out), "bookings": len(bookings),
                                 "tasks": len(tasks), "at_risk": len(at_risk)},
                                source_module="schedule_builder")
    except Exception:
        pass

    return text


if __name__ == "__main__":
    print(build_schedule())
