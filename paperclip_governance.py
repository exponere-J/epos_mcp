#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
paperclip_governance.py — Paperclip Agent Governance Framework
================================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Agent Deployment, Mission Governance, Execution Receipts

Manages the lifecycle of autonomous agents (Paperclips):
  1. MISSION INTAKE — Validate mission against constitutional constraints
  2. GOVERNANCE GATE — Triage mission for risk, scope, and authorization
  3. EXECUTION SANDBOX — Deploy agent with bounded permissions
  4. RECEIPT GENERATION — Proof of execution (3-artifact requirement)
  5. AAR — After-action review for learning

Constitutional Rule: Logged != Executed. Every execution must produce:
  - Execution receipt (what was done)
  - Proof artifact (evidence it worked)
  - Rollback path (how to undo it)
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

from path_utils import get_context_vault


PAPERCLIP_VAULT = get_context_vault() / "paperclip"

# Mission risk levels
RISK_LEVELS = {
    "low":      {"max_duration_minutes": 60, "requires_approval": False, "auto_rollback": True},
    "medium":   {"max_duration_minutes": 30, "requires_approval": False, "auto_rollback": True},
    "high":     {"max_duration_minutes": 15, "requires_approval": True, "auto_rollback": True},
    "critical": {"max_duration_minutes": 5,  "requires_approval": True, "auto_rollback": False},
}

# Permitted agent actions (constitutional whitelist)
PERMITTED_ACTIONS = [
    "read_vault", "write_vault", "query_database", "call_api",
    "generate_content", "send_notification", "run_diagnostic",
    "score_lead", "schedule_content", "analyze_data",
]

# Prohibited actions (constitutional blacklist)
PROHIBITED_ACTIONS = [
    "delete_data", "modify_constitution", "send_payment",
    "access_credentials", "modify_permissions", "execute_shell",
]


@dataclass
class Mission:
    mission_id: str
    objective: str
    constraints: list
    success_criteria: list
    failure_modes: list
    risk_level: str
    assigned_agent: str
    status: str = "pending"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    receipt: Optional[dict] = None
    aar: Optional[dict] = None


class PaperclipGovernance:
    """
    Governs the lifecycle of autonomous agent missions.
    Enforces constitutional constraints on execution.
    """

    def __init__(self, vault_path: Path = None):
        self.vault = vault_path or PAPERCLIP_VAULT
        self.missions_dir = self.vault / "missions"
        self.receipts_dir = self.vault / "receipts"
        self.aar_dir = self.vault / "aar"
        for d in (self.missions_dir, self.receipts_dir, self.aar_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._journal_path = self.vault / "paperclip_journal.jsonl"

    # ── Mission Intake ──────────────────────────────────────

    def create_mission(self, objective: str, constraints: list,
                       success_criteria: list, failure_modes: list,
                       risk_level: str = "medium",
                       assigned_agent: str = "agent_zero") -> Mission:
        """Create a governed mission for agent execution."""
        if risk_level not in RISK_LEVELS:
            raise ValueError(f"Invalid risk level: {risk_level}. Use: {list(RISK_LEVELS.keys())}")

        mission_id = f"MISSION-{uuid.uuid4().hex[:8]}"
        mission = Mission(
            mission_id=mission_id,
            objective=objective,
            constraints=constraints,
            success_criteria=success_criteria,
            failure_modes=failure_modes,
            risk_level=risk_level,
            assigned_agent=assigned_agent,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Constitutional validation
        validation = self._validate_mission(mission)
        if not validation["approved"]:
            mission.status = "rejected"
            self._save_mission(mission)
            self._journal("mission.rejected", {
                "mission_id": mission_id, "reason": validation["reason"]})
            return mission

        mission.status = "approved"
        self._save_mission(mission)
        self._journal("mission.created", {"mission_id": mission_id, "risk": risk_level})
        self._publish("paperclip.mission.created", {
            "mission_id": mission_id, "objective": objective[:100],
            "risk_level": risk_level, "agent": assigned_agent})

        return mission

    def _validate_mission(self, mission: Mission) -> dict:
        """Validate mission against constitutional constraints."""
        # Check for prohibited actions in objective/constraints
        obj_lower = mission.objective.lower()
        for prohibited in PROHIBITED_ACTIONS:
            if prohibited.replace("_", " ") in obj_lower:
                return {"approved": False,
                        "reason": f"Prohibited action detected: {prohibited}"}

        # High/critical missions require explicit failure modes
        if mission.risk_level in ("high", "critical") and not mission.failure_modes:
            return {"approved": False,
                    "reason": "High/critical missions require explicit failure modes"}

        # Must have success criteria
        if not mission.success_criteria:
            return {"approved": False,
                    "reason": "Mission must define success criteria"}

        return {"approved": True, "reason": "Constitutional checks passed"}

    # ── Execution Lifecycle ─────────────────────────────────

    def start_mission(self, mission_id: str) -> dict:
        """Mark mission as started. Returns execution constraints."""
        mission = self._load_mission(mission_id)
        if not mission:
            return {"error": f"Mission not found: {mission_id}"}
        if mission.status != "approved":
            return {"error": f"Mission not approved. Status: {mission.status}"}

        risk_config = RISK_LEVELS[mission.risk_level]
        if risk_config["requires_approval"]:
            mission.status = "awaiting_approval"
            self._save_mission(mission)
            self._publish("paperclip.mission.needs_approval", {
                "mission_id": mission_id})
            return {"status": "awaiting_approval",
                    "message": "High-risk mission requires human approval"}

        mission.status = "running"
        mission.started_at = datetime.now(timezone.utc).isoformat()
        self._save_mission(mission)
        self._journal("mission.started", {"mission_id": mission_id})
        self._publish("paperclip.mission.started", {"mission_id": mission_id})

        return {
            "status": "running",
            "mission_id": mission_id,
            "max_duration_minutes": risk_config["max_duration_minutes"],
            "auto_rollback": risk_config["auto_rollback"],
            "permitted_actions": PERMITTED_ACTIONS,
        }

    def complete_mission(self, mission_id: str,
                         execution_receipt: dict,
                         proof_artifact: str,
                         rollback_path: str) -> dict:
        """Complete a mission with required proof artifacts."""
        mission = self._load_mission(mission_id)
        if not mission:
            return {"error": f"Mission not found: {mission_id}"}

        # Constitutional requirement: 3 proof artifacts
        if not execution_receipt:
            return {"error": "Missing execution receipt"}
        if not proof_artifact:
            return {"error": "Missing proof artifact"}
        if not rollback_path:
            return {"error": "Missing rollback path"}

        mission.status = "complete"
        mission.completed_at = datetime.now(timezone.utc).isoformat()
        mission.receipt = {
            "execution_receipt": execution_receipt,
            "proof_artifact": proof_artifact,
            "rollback_path": rollback_path,
            "completed_at": mission.completed_at,
        }

        # Save receipt separately
        receipt_path = self.receipts_dir / f"{mission_id}_receipt.json"
        receipt_path.write_text(json.dumps(mission.receipt, indent=2), encoding="utf-8")

        self._save_mission(mission)
        self._journal("mission.completed", {"mission_id": mission_id})
        self._publish("paperclip.mission.completed", {
            "mission_id": mission_id,
            "has_receipt": True, "has_proof": True, "has_rollback": True})

        return {"status": "complete", "receipt_path": str(receipt_path)}

    def fail_mission(self, mission_id: str, reason: str,
                     rollback_applied: bool = False) -> dict:
        """Record mission failure with reason."""
        mission = self._load_mission(mission_id)
        if not mission:
            return {"error": f"Mission not found: {mission_id}"}

        mission.status = "failed"
        mission.completed_at = datetime.now(timezone.utc).isoformat()
        mission.aar = {
            "failure_reason": reason,
            "rollback_applied": rollback_applied,
            "failed_at": mission.completed_at,
        }

        self._save_mission(mission)
        self._journal("mission.failed", {"mission_id": mission_id, "reason": reason})
        self._publish("paperclip.mission.failed", {
            "mission_id": mission_id, "reason": reason[:200]})

        return {"status": "failed", "reason": reason}

    # ── Status & Queries ────────────────────────────────────

    def list_missions(self, status: str = None) -> list:
        missions = []
        for f in self.missions_dir.glob("MISSION-*.json"):
            m = json.loads(f.read_text(encoding="utf-8"))
            if status and m.get("status") != status:
                continue
            missions.append({
                "mission_id": m["mission_id"],
                "objective": m["objective"][:80],
                "status": m["status"],
                "risk_level": m["risk_level"],
                "agent": m["assigned_agent"],
            })
        return missions

    def get_status(self) -> dict:
        all_missions = list(self.missions_dir.glob("MISSION-*.json"))
        statuses = {}
        for f in all_missions:
            m = json.loads(f.read_text(encoding="utf-8"))
            s = m.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total_missions": len(all_missions),
            "by_status": statuses,
            "receipts": len(list(self.receipts_dir.glob("*_receipt.json"))),
        }

    # ── Persistence ─────────────────────────────────────────

    def _save_mission(self, mission: Mission):
        path = self.missions_dir / f"{mission.mission_id}.json"
        path.write_text(json.dumps(asdict(mission), indent=2), encoding="utf-8")

    def _load_mission(self, mission_id: str) -> Optional[Mission]:
        path = self.missions_dir / f"{mission_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Mission(**data)

    def _journal(self, event_type: str, payload: dict):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "event_type": event_type, "payload": payload}
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _publish(self, event_type: str, payload: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="paperclip_governance")
            except Exception:
                pass
        record_decision(decision_type=event_type, description=f"Paperclip: {event_type}",
                        agent_id="paperclip_governance", outcome="success", context=payload)


if __name__ == "__main__":
    passed = 0
    gov = PaperclipGovernance()

    # Test 1: Create valid mission
    m = gov.create_mission(
        objective="Generate weekly content schedule for lego_affiliate niche",
        constraints=["Only read vault data", "No external API calls"],
        success_criteria=["Schedule JSON produced", "5+ content slots filled"],
        failure_modes=["Vault read failure", "Insufficient sparks"],
        risk_level="low", assigned_agent="content_agent")
    assert m.status == "approved"
    passed += 1

    # Test 2: Start mission
    result = gov.start_mission(m.mission_id)
    assert result["status"] == "running"
    assert "max_duration_minutes" in result
    passed += 1

    # Test 3: Complete mission with receipts
    result = gov.complete_mission(
        m.mission_id,
        execution_receipt={"slots_filled": 5, "duration_seconds": 12},
        proof_artifact="context_vault/schedules/week_15.json",
        rollback_path="context_vault/schedules/week_15.json.bak")
    assert result["status"] == "complete"
    passed += 1

    # Test 4: Reject prohibited mission
    m2 = gov.create_mission(
        objective="Delete data from the client database",
        constraints=[], success_criteria=["Data removed"],
        failure_modes=[], risk_level="critical")
    assert m2.status == "rejected"
    passed += 1

    # Test 5: Status
    status = gov.get_status()
    assert status["total_missions"] >= 2
    assert status["receipts"] >= 1
    passed += 1

    print(f"PASS: paperclip_governance ({passed} assertions)")
    print(f"Missions: {status['total_missions']} | Receipts: {status['receipts']}")
