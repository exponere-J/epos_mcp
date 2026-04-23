#!/usr/bin/env python3
# EPOS Artifact — BUILD 100 (Supervisory Monitor)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §1
"""
supervisory_monitor.py — Client state machine + cadence enforcement

Runs a per-client state machine across 5 stages:
    LEAD → DISCOVERY → PROPOSAL → ACTIVE → RETAINED
(or terminal: LAPSED, CHURNED)

On each pass (every 60 min by default), for each client:
  - Compute stage from touchpoint history
  - Compare stage-advancement cadence vs SLAs
  - Emit 'client.stage.advanced' / 'client.stage.stalled' events
  - Write per-client state snapshot to context_vault/clients/<id>.json

The LuLu archetype (price-sensitive, slow-decide) gets a longer SLA.
Other archetypes get shorter ones.

This is the health half of proprioception for the client surface.
Combine with client_health_scoring.py for rollup + Friday briefing.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
CLIENTS_DIR = Path(os.getenv("EPOS_CLIENTS_DIR", str(REPO / "context_vault" / "clients")))
LOG = Path(os.getenv("EPOS_MONITOR_LOG", str(REPO / "context_vault" / "bi" / "supervisory_monitor.jsonl")))

STAGES = ["LEAD", "DISCOVERY", "PROPOSAL", "ACTIVE", "RETAINED", "LAPSED", "CHURNED"]

# SLA (max days in stage before stall flag) per archetype
SLA_DAYS: dict[str, dict[str, int]] = {
    "default":              {"LEAD": 7, "DISCOVERY": 5, "PROPOSAL": 7, "ACTIVE": 30, "RETAINED": 90},
    "small_service_owner":  {"LEAD": 14, "DISCOVERY": 10, "PROPOSAL": 14, "ACTIVE": 45, "RETAINED": 120},
    "enterprise_innovation":{"LEAD": 30, "DISCOVERY": 30, "PROPOSAL": 60, "ACTIVE": 90, "RETAINED": 180},
    "growth_hacker":        {"LEAD": 3, "DISCOVERY": 2, "PROPOSAL": 5, "ACTIVE": 14, "RETAINED": 60},
}


@dataclass
class ClientState:
    client_id: str
    archetype: str = "default"
    stage: str = "LEAD"
    entered_stage_at: str = ""
    last_touchpoint_at: str = ""
    touchpoint_history: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def days_in_stage(self) -> int:
        if not self.entered_stage_at:
            return 0
        try:
            dt = datetime.fromisoformat(self.entered_stage_at.replace("Z", "+00:00"))
        except Exception:
            return 0
        return (datetime.now(timezone.utc) - dt).days

    def sla(self) -> int:
        return SLA_DAYS.get(self.archetype, SLA_DAYS["default"]).get(self.stage, 30)

    def is_stalled(self) -> bool:
        return self.days_in_stage() > self.sla() and self.stage not in ("RETAINED", "LAPSED", "CHURNED")


class SupervisoryMonitor:
    def __init__(self) -> None:
        CLIENTS_DIR.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> list[ClientState]:
        states = []
        for p in sorted(CLIENTS_DIR.glob("*.json")):
            try:
                data = json.loads(p.read_text())
                states.append(ClientState(**data))
            except Exception:
                pass
        return states

    def save(self, state: ClientState) -> None:
        (CLIENTS_DIR / f"{state.client_id}.json").write_text(
            json.dumps(asdict(state), indent=2) + "\n"
        )

    def advance(self, state: ClientState, next_stage: str, note: str = "") -> None:
        if next_stage not in STAGES:
            raise ValueError(f"unknown stage: {next_stage}")
        now = datetime.now(timezone.utc).isoformat()
        state.touchpoint_history.append({
            "timestamp": now, "from_stage": state.stage, "to_stage": next_stage,
            "note": note,
        })
        state.stage = next_stage
        state.entered_stage_at = now
        state.last_touchpoint_at = now
        if "stalled" in state.flags: state.flags.remove("stalled")
        self.save(state)
        self._emit("client.stage.advanced", {
            "client_id": state.client_id, "to_stage": next_stage, "note": note,
        })

    def audit_all(self) -> dict[str, Any]:
        states = self.load_all()
        stalled: list[dict] = []
        fresh: list[dict] = []
        terminal: list[dict] = []
        for s in states:
            if s.stage in ("CHURNED", "LAPSED"):
                terminal.append({"client_id": s.client_id, "stage": s.stage})
                continue
            if s.is_stalled():
                if "stalled" not in s.flags:
                    s.flags.append("stalled")
                    self.save(s)
                    self._emit("client.stage.stalled", {
                        "client_id": s.client_id, "stage": s.stage,
                        "days_in_stage": s.days_in_stage(), "sla": s.sla(),
                    })
                stalled.append({"client_id": s.client_id, "stage": s.stage,
                                 "days": s.days_in_stage(), "sla": s.sla()})
            else:
                fresh.append({"client_id": s.client_id, "stage": s.stage,
                               "days": s.days_in_stage()})
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_clients": len(states),
            "fresh": len(fresh), "stalled": len(stalled), "terminal": len(terminal),
            "stalled_details": stalled,
        }
        self._log(summary)
        return summary

    def _emit(self, event: str, payload: dict) -> None:
        try:
            from epos_event_bus import EPOSEventBus
            EPOSEventBus().publish(event, payload, source_module="supervisory_monitor")
        except Exception:
            pass

    def _log(self, entry: dict) -> None:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def run_pass() -> dict[str, Any]:
    return SupervisoryMonitor().audit_all()


if __name__ == "__main__":
    print(json.dumps(run_pass(), indent=2))
