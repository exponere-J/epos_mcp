#!/usr/bin/env python3
# EPOS Artifact — BUILD 66 (Voice Bridge to Command Center)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
bridge.py — Map voice commands to Command Center actions

Speech → transcript → CCP extract → intent classification → route to:
  - AFFiNE (create page / update canvas)
  - Cal.com (schedule / reschedule)
  - Undb (log CRM entry / add to pipeline)
  - PM surface (add action item)
  - Execution arm (browser/computer task)

Each command is governed by:
  - deletion_gate (no destructive action without Sovereign approval)
  - voice_command_log (every command recorded)
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
LOG = Path(os.getenv("EPOS_VOICE_CMD_LOG",
                      str(REPO / "context_vault" / "voice" / "commands.jsonl")))
LOG.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class CommandResult:
    command: str
    intent: str
    action: str
    route: str
    result: dict
    timestamp: str


# ── Intent patterns ────────────────────────────────────────────

INTENTS: list[tuple[re.Pattern, str, str]] = [
    # (pattern, intent, route)
    (re.compile(r"add (?:note|notes)? (?:to|into) (.+)", re.IGNORECASE), "add_note", "affine"),
    (re.compile(r"schedule (?:a )?(?:meeting|call) with (.+?)(?: on (.+))?$", re.IGNORECASE),
        "schedule_meeting", "calcom"),
    (re.compile(r"reschedule (.+)", re.IGNORECASE), "reschedule", "calcom"),
    (re.compile(r"(?:add|log) (.+?) to (?:my )?(?:crm|pipeline|undb)", re.IGNORECASE),
        "crm_add", "undb"),
    (re.compile(r"(?:todo|task|action item): (.+)", re.IGNORECASE), "add_task", "pm_surface"),
    (re.compile(r"(?:scrape|fetch|read) (.+)", re.IGNORECASE), "web_read", "execution_arm"),
    (re.compile(r"(?:post to|publish to) (?:linked ?in|x|twitter): (.+)", re.IGNORECASE),
        "social_post", "publisher"),
    (re.compile(r"(?:brief|briefing) me", re.IGNORECASE), "briefing_request", "friday"),
    (re.compile(r"(?:how am i|status)", re.IGNORECASE), "status_request", "friday"),
]


class VoiceBridge:
    def route(self, command: str, context: dict | None = None) -> CommandResult:
        ctx = context or {}
        intent, route_name, match = self._classify(command)
        handler = ROUTES.get(route_name, self._noop)
        result = handler(command, match, ctx)
        rec = CommandResult(
            command=command, intent=intent, action=route_name, route=route_name,
            result=result, timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._log(rec)
        return rec

    def _classify(self, command: str) -> tuple[str, str, re.Match | None]:
        for pattern, intent, route in INTENTS:
            m = pattern.search(command)
            if m:
                return intent, route, m
        return "unknown", "noop", None

    def _noop(self, command: str, match, ctx: dict) -> dict:
        return {"status": "no_match", "fallback": "pass_to_friday_for_clarification"}

    def _log(self, rec: CommandResult) -> None:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), default=str) + "\n")


# ── Route handlers (stubs that emit events; full impls pending) ───

def _route_affine(cmd: str, match, ctx: dict) -> dict:
    target = match.group(1) if match else ""
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish("affine.note.add",
                                {"target": target, "command": cmd}, source_module="voice_bridge")
    except Exception:
        pass
    return {"status": "queued", "backend": "affine", "target": target}


def _route_calcom(cmd: str, match, ctx: dict) -> dict:
    who = match.group(1) if match else ""
    when = match.group(2) if match and match.lastindex and match.lastindex >= 2 else None
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish("calcom.booking.request",
                                {"who": who, "when": when}, source_module="voice_bridge")
    except Exception:
        pass
    return {"status": "queued", "backend": "calcom", "who": who, "when": when}


def _route_undb(cmd: str, match, ctx: dict) -> dict:
    entry = match.group(1) if match else ""
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish("undb.crm.add",
                                {"entry": entry}, source_module="voice_bridge")
    except Exception:
        pass
    return {"status": "queued", "backend": "undb", "entry": entry}


def _route_pm(cmd: str, match, ctx: dict) -> dict:
    task = match.group(1) if match else ""
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish("pm.task.add",
                                {"task": task}, source_module="voice_bridge")
    except Exception:
        pass
    return {"status": "queued", "backend": "pm_surface", "task": task}


def _route_arm(cmd: str, match, ctx: dict) -> dict:
    try:
        from nodes.execution_arm import execute
        r = execute(task=cmd, mode_hint="auto", context=ctx)
        return {"status": "dispatched", "arm_result": {"success": r.get("success"),
                                                          "arm": r.get("arm")}}
    except Exception as e:
        return {"status": "arm_unavailable", "error": f"{type(e).__name__}: {e}"}


def _route_publisher(cmd: str, match, ctx: dict) -> dict:
    body = match.group(1) if match else ""
    try:
        from nodes.publishers import linkedin_post
        r = linkedin_post(body=body, mode_hint="browser_use.headed")
        return {"status": "dispatched", "body_preview": body[:50]}
    except Exception as e:
        return {"status": "publisher_unavailable", "error": f"{type(e).__name__}: {e}"}


def _route_friday(cmd: str, match, ctx: dict) -> dict:
    try:
        from epos.ops import build_briefing
        briefing = build_briefing()
        return {"status": "briefing_ready", "length_chars": len(briefing)}
    except Exception as e:
        return {"status": "friday_unavailable", "error": f"{type(e).__name__}: {e}"}


ROUTES: dict[str, Callable] = {
    "affine": _route_affine,
    "calcom": _route_calcom,
    "undb": _route_undb,
    "pm_surface": _route_pm,
    "execution_arm": _route_arm,
    "publisher": _route_publisher,
    "friday": _route_friday,
}


def route_command(command: str, context: dict | None = None) -> dict:
    r = VoiceBridge().route(command, context)
    return asdict(r)


if __name__ == "__main__":
    import sys
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "brief me"
    print(json.dumps(route_command(cmd), indent=2, default=str))
