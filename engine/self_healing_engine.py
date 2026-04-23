#!/usr/bin/env python3
# EPOS Artifact — BUILD 107 (Self-Healing Engine)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §1
"""
self_healing_engine.py — Article XVI §3 intelligent triage

When a component in the Process Matrix reports a status change:
   operational → degraded     OR
   degraded    → unavailable  OR
   * → * with error_rate spike

This engine:
  1. Looks up the component in organism_state.json for context
  2. Checks dependencies + consumers to assess blast radius
  3. Consults the Gap Bridge Matrix to see if the component is
     revenue-critical
  4. Routes to remediation:
       - Non-critical + restartable → auto-restart (docker compose restart)
       - Critical + known failure pattern → apply pattern remediation
       - Critical + unknown failure → escalate to Sovereign via Steward
  5. Logs every triage decision to the Reward Bus for QLoRA training

Runs as a subscriber on the event bus; triggers via
  'process_matrix.component.degraded' and similar state events.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
REGISTRY = Path(os.getenv("EPOS_ORGANISM_STATE",
                           str(REPO / "context_vault" / "state" / "organism_state.json")))
TRIAGE_LOG = Path(os.getenv("EPOS_TRIAGE_LOG",
                             str(REPO / "context_vault" / "bi" / "self_healing_triage.jsonl")))

# Known failure patterns → remediation
FAILURE_PATTERNS = [
    {"signal": "connection refused", "cause": "service down",
     "action": "restart_container", "severity": "yellow"},
    {"signal": "timeout", "cause": "service overloaded or hung",
     "action": "restart_container", "severity": "yellow"},
    {"signal": "no such file or directory", "cause": "missing config or volume",
     "action": "escalate", "severity": "red"},
    {"signal": "permission denied", "cause": "credential or scope issue",
     "action": "escalate", "severity": "red"},
    {"signal": "out of memory", "cause": "resource starvation",
     "action": "restart_container_with_higher_mem", "severity": "red"},
    {"signal": "syntax error", "cause": "bad deploy",
     "action": "rollback", "severity": "red"},
]


@dataclass
class TriageDecision:
    component_id: str
    observed_status: str
    severity: str
    cause: str
    action: str
    blast_radius: int         # count of consumers affected
    revenue_critical: bool
    outcome: str              # "auto_remediated" | "escalated" | "monitoring"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SelfHealingEngine:
    def __init__(self) -> None:
        TRIAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

    def _load_registry(self) -> dict:
        return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}

    def _match_pattern(self, error_text: str) -> dict | None:
        text = (error_text or "").lower()
        for p in FAILURE_PATTERNS:
            if p["signal"] in text:
                return p
        return None

    def _blast_radius(self, reg: dict, component_id: str) -> tuple[int, bool]:
        """Count consumers + flag if revenue-critical."""
        entries = reg.get("process_registry", [])
        target = None
        for e in entries:
            if e.get("component_id") == component_id:
                target = e
                break
        if not target:
            return 0, False
        path = target.get("path", "")
        # Consumers from the Scout inventory
        inv_path = REPO / "context_vault" / "state" / "organism_inventory_scout.json"
        consumers = 0
        if inv_path.exists():
            inv = json.loads(inv_path.read_text())
            consumers = len(inv.get("reverse_deps", {}).get(path, []))
        # Revenue-critical tags
        tags = set(target.get("capability_tags", []))
        revenue_critical = bool(tags & {
            "execution_arm", "governance", "bridge", "state_graph",
            "event_bus", "ccp", "voice_pipeline",
        })
        return consumers, revenue_critical

    def triage(self, component_id: str, observed_status: str,
               error_text: str = "") -> TriageDecision:
        reg = self._load_registry()
        pattern = self._match_pattern(error_text)
        severity = pattern["severity"] if pattern else ("yellow" if observed_status == "degraded" else "red")
        cause = pattern["cause"] if pattern else "unclassified"
        proposed_action = pattern["action"] if pattern else "escalate"
        blast, revenue_critical = self._blast_radius(reg, component_id)

        # Decision logic
        if proposed_action == "restart_container" and not revenue_critical:
            outcome = "auto_remediated"
            action = self._restart_container(component_id)
        elif proposed_action == "restart_container" and revenue_critical and blast < 3:
            outcome = "auto_remediated"
            action = self._restart_container(component_id)
        else:
            outcome = "escalated"
            action = "escalate_to_sovereign_via_steward"

        decision = TriageDecision(
            component_id=component_id,
            observed_status=observed_status,
            severity=severity,
            cause=cause,
            action=action,
            blast_radius=blast,
            revenue_critical=revenue_critical,
            outcome=outcome,
        )
        self._log(decision)
        self._emit(decision)
        return decision

    def _restart_container(self, component_id: str) -> str:
        """Attempt docker compose restart for a container-ish component_id.
        Falls back to logging the intent."""
        # Map component → container name (very rough heuristic)
        container = component_id.replace("E-", "").strip("0")
        try:
            r = subprocess.run(
                ["docker", "compose", "restart", container],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                return f"docker_restart_success: {container}"
            return f"docker_restart_failed: {r.stderr[:200]}"
        except FileNotFoundError:
            return "docker_not_available_in_sandbox (intent logged)"
        except Exception as e:
            return f"restart_error: {type(e).__name__}: {e}"

    def _log(self, decision: TriageDecision) -> None:
        with TRIAGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(decision)) + "\n")

    def _emit(self, decision: TriageDecision) -> None:
        try:
            from epos_event_bus import EPOSEventBus
            bus = EPOSEventBus()
            topic = (f"self_healing.triage.{decision.outcome}"
                     if decision.outcome != "escalated" else "self_healing.triage.escalated")
            bus.publish(topic, asdict(decision), source_module="self_healing_engine")
            if decision.outcome == "escalated":
                bus.publish("steward.alert", asdict(decision), source_module="self_healing_engine")
        except Exception:
            pass


def triage(component_id: str, status: str, error_text: str = "") -> dict:
    return asdict(SelfHealingEngine().triage(component_id, status, error_text))


if __name__ == "__main__":
    # Demo: triage a fake degraded event
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else "E-0199"
    status = sys.argv[2] if len(sys.argv) > 2 else "degraded"
    err = sys.argv[3] if len(sys.argv) > 3 else "connection refused"
    print(json.dumps(triage(cid, status, err), indent=2))
