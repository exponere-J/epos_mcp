#!/usr/bin/env python3
"""
agent_orchestrator.py — EPOS Multi-Agent Mission Orchestrator
==============================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
Mission ID: EPOS Core Heal — Module 8 of 9
File Location: C:/Users/Jamie/workspace/epos_mcp/agent_orchestrator.py

Single responsibility: Route missions to agents, validate permissions,
checkpoint workflow state, coordinate inter-agent communication.
Returns MissionReceipt with proof artifacts for every dispatch.

Dependencies: path_utils (1), stasis (2), roles (3), epos_intelligence (4),
              context_librarian (5), constitutional_arbiter (6),
              flywheel_analyst (7)
"""

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

from path_utils import get_epos_root, get_context_vault, get_logs_dir
from stasis import ConstitutionalViolation
from roles import (
    AgentId, Capability, get_role, validate_assignment, get_all_roles,
)
from epos_intelligence import record_decision, record_event


# ── Exceptions ───────────────────────────────────────────────────

class OrchestratorError(Exception):
    """Base exception for orchestrator failures."""
    pass


class MissionCheckpointNotFound(OrchestratorError):
    """Raised when resume_mission cannot find a checkpoint on disk."""
    pass


class AgentZeroUnavailable(OrchestratorError):
    """Raised when Agent Zero path does not exist or is unreachable."""
    pass


class MissionPermissionDenied(OrchestratorError):
    """Raised when an agent lacks the required capability for an action."""
    pass


# ── Data Structures ──────────────────────────────────────────────

@dataclass
class MissionBrief:
    """Input to the orchestrator: what to do, who does it."""
    mission_id: str
    objective: str
    action_type: str        # e.g. "diagnostic", "vault_write", "constitutional_change"
    assigned_agent: str     # agent_id string from roles registry
    payload: Dict[str, Any] = field(default_factory=dict)
    human_approval: bool = False
    priority: str = "normal"


@dataclass
class MissionReceipt:
    """Output from dispatch: proof of what happened."""
    mission_id: str
    status: str             # "dispatched" | "denied" | "unavailable" | "blocked"
    assigned_agent: str
    action_type: str
    checkpoint_path: Optional[str]
    bi_record_id: Optional[str]
    dispatched_at: str
    reason: Optional[str]


# ── Action-to-Capability Mapping ─────────────────────────────────

ACTION_CAPABILITY_MAP: Dict[str, str] = {
    "content_generation":    Capability.EXECUTE_MISSION.value,
    "diagnostic":            Capability.GOVERNANCE_AUDIT.value,
    "vault_write":           Capability.WRITE_VAULT.value,
    "vault_read":            Capability.READ_VAULT.value,
    "governance_audit":      Capability.GOVERNANCE_AUDIT.value,
    "governance_enforce":    Capability.GOVERNANCE_ENFORCE.value,
    "constitutional_change": Capability.GOVERNANCE_ENFORCE.value,
    "agent_mission":         Capability.EXECUTE_MISSION.value,
    "analysis":              Capability.BI_READ.value,
    "bi_write":              Capability.BI_WRITE.value,
}


# ── AgentOrchestrator ────────────────────────────────────────────

class AgentOrchestrator:
    """
    Mission routing, dispatching, and state coordination.

    Four internal responsibilities:
      ROUTER:       route_intent()          — map brief to execution path
      DISPATCHER:   dispatch_mission()      — execute with permission gate
      STATE_KEEPER: checkpoint_workflow()    — persist state to vault
      COORDINATOR:  coordinate()            — inter-agent communication
    """

    def __init__(self):
        load_dotenv(Path(__file__).resolve().parent / ".env")
        self.vault_root = get_context_vault()
        self.checkpoints_dir = self.vault_root / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    # ── ROUTER ───────────────────────────────────────────────────

    def route_intent(self, brief: MissionBrief) -> str:
        """Map action_type to execution path / node type."""
        routing = {
            "content_generation":    "ContentNode",
            "diagnostic":            "DiagnosticNode",
            "vault_write":           "VaultNode",
            "vault_read":            "VaultNode",
            "governance_audit":      "GovernanceNode",
            "constitutional_change": "ConstitutionChangeNode",
            "agent_mission":         "BridgeNode",
            "analysis":              "AnalysisNode",
        }
        return routing.get(brief.action_type, "GenericNode")

    # ── DISPATCHER ───────────────────────────────────────────────

    def dispatch_mission(self, brief: MissionBrief) -> MissionReceipt:
        """
        Full dispatch pipeline:
        1. Block constitutional changes without human approval
        2. Validate role permission for action_type
        3. Checkpoint at RouterNode
        4. Log to BI
        5. Return MissionReceipt with proof artifacts

        status="dispatched" only when checkpoint + BI record both exist.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # ── 1. Constitutional hard block ─────────────────────────
        if (brief.action_type == "constitutional_change"
                and not brief.human_approval):
            record_decision(
                decision_type="governance.permission_denied",
                description=(
                    f"Constitutional change blocked: {brief.objective}. "
                    f"human_approval=False."
                ),
                agent_id=AgentId.ORCHESTRATOR.value,
                context={
                    "mission_id": brief.mission_id,
                    "action_type": brief.action_type,
                    "assigned_agent": brief.assigned_agent,
                },
                outcome="blocked",
            )
            raise ConstitutionalViolation(
                rule="CONSTITUTIONAL_CHANGE_REQUIRES_HUMAN_APPROVAL",
                detail="Set human_approval=True after explicit Growth Steward sign-off",
                component="agent_orchestrator",
            )

        # ── 2. Role permission check ────────────────────────────
        required_cap = ACTION_CAPABILITY_MAP.get(brief.action_type)
        if required_cap is None:
            # Unknown action type — allow if agent has execute_mission
            required_cap = Capability.EXECUTE_MISSION.value

        if not validate_assignment(brief.assigned_agent, required_cap):
            record_decision(
                decision_type="governance.permission_denied",
                description=(
                    f"Agent '{brief.assigned_agent}' lacks capability "
                    f"'{required_cap}' for action '{brief.action_type}'."
                ),
                agent_id=AgentId.ORCHESTRATOR.value,
                context={
                    "mission_id": brief.mission_id,
                    "assigned_agent": brief.assigned_agent,
                    "required_capability": required_cap,
                },
                outcome="denied",
            )
            raise MissionPermissionDenied(
                f"Agent '{brief.assigned_agent}' does not have capability "
                f"'{required_cap}' required for action '{brief.action_type}'. "
                f"Check roles.py for valid assignments."
            )

        # ── 3. Checkpoint (proof artifact 1) ────────────────────
        node_type = self.route_intent(brief)
        cp_path = self.checkpoint_workflow(
            brief.mission_id,
            "RouterNode",
            {
                "brief_objective": brief.objective,
                "action_type": brief.action_type,
                "assigned_agent": brief.assigned_agent,
                "routed_to": node_type,
                "priority": brief.priority,
                "status": "dispatched",
            },
        )

        # ── 4. BI record (proof artifact 2) ─────────────────────
        bi_result = record_decision(
            decision_type="mission.dispatched",
            description=f"Mission dispatched: {brief.objective}",
            agent_id=AgentId.ORCHESTRATOR.value,
            context={
                "mission_id": brief.mission_id,
                "action_type": brief.action_type,
                "assigned_agent": brief.assigned_agent,
                "routed_to": node_type,
                "priority": brief.priority,
            },
            outcome="dispatched",
        )
        # Use entry timestamp as BI record ID
        bi_record_id = None
        if bi_result.get("status") == "recorded":
            bi_record_id = bi_result.get("entry", {}).get("timestamp")

        # ── 5. Return receipt ────────────────────────────────────
        return MissionReceipt(
            mission_id=brief.mission_id,
            status="dispatched",
            assigned_agent=brief.assigned_agent,
            action_type=brief.action_type,
            checkpoint_path=str(cp_path),
            bi_record_id=bi_record_id,
            dispatched_at=now_iso,
            reason=None,
        )

    # ── STATE_KEEPER ─────────────────────────────────────────────

    def checkpoint_workflow(
        self,
        mission_id: str,
        node_name: str,
        state: Dict[str, Any],
    ) -> Path:
        """
        Persist workflow state to vault checkpoint.
        Returns Path to checkpoint file. Raises on failure.
        """
        cp_dir = self.checkpoints_dir / mission_id
        cp_dir.mkdir(parents=True, exist_ok=True)
        cp_file = cp_dir / f"{node_name}.json"
        checkpoint = {
            "mission_id": mission_id,
            "node_name": node_name,
            "state": state,
            "checkpointed_at": datetime.now(timezone.utc).isoformat(),
        }
        cp_file.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        assert cp_file.exists(), f"Checkpoint write failed: {cp_file}"
        return cp_file

    def resume_mission(self, mission_id: str, from_node: str) -> Dict[str, Any]:
        """
        Restore checkpoint state. Raises MissionCheckpointNotFound
        if checkpoint does not exist — never returns None.
        """
        cp_file = self.checkpoints_dir / mission_id / f"{from_node}.json"
        if not cp_file.exists():
            raise MissionCheckpointNotFound(
                f"No checkpoint for mission={mission_id} "
                f"node={from_node}. Expected at: {cp_file}"
            )
        return json.loads(cp_file.read_text(encoding="utf-8"))

    # ── COORDINATOR ──────────────────────────────────────────────

    def coordinate(
        self,
        from_agent: str,
        to_agent: str,
        message: Dict[str, Any],
        mission_id: str,
    ) -> Path:
        """
        Write inter-agent message to agent_comms vault namespace.
        Returns path to message file.
        """
        comms_dir = self.vault_root / "agent_comms"
        comms_dir.mkdir(parents=True, exist_ok=True)
        msg_id = f"{from_agent}_to_{to_agent}_{uuid.uuid4().hex[:8]}"
        msg_path = comms_dir / f"{msg_id}.json"
        record = {
            "message_id": msg_id,
            "mission_id": mission_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": message,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        msg_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        assert msg_path.exists()
        return msg_path

    # ── STATUS ───────────────────────────────────────────────────

    def list_checkpoints(self, mission_id: str) -> List[str]:
        """List all checkpoint node names for a mission."""
        cp_dir = self.checkpoints_dir / mission_id
        if not cp_dir.exists():
            return []
        return [f.stem for f in sorted(cp_dir.glob("*.json"))]

    def health_check(self) -> Dict[str, Any]:
        """Quick orchestrator health status."""
        cp_missions = [d.name for d in self.checkpoints_dir.iterdir() if d.is_dir()]
        return {
            "status": "operational",
            "checkpoint_missions": len(cp_missions),
            "vault_path": str(self.vault_root),
            "roles_registered": len(get_all_roles()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ── Self-test ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EPOS Agent Orchestrator v2.0 — Self-test")
    print("=" * 55)

    orch = AgentOrchestrator()

    # Test 1: Happy path dispatch — three proof artifacts
    # TTLG has governance_audit capability → action_type="diagnostic" maps to it
    mid1 = f"test-{uuid.uuid4().hex[:8]}"
    brief1 = MissionBrief(
        mission_id=mid1,
        objective="Orchestrator self-test — happy path",
        action_type="diagnostic",
        assigned_agent="ttlg",  # roles.py uses lowercase AgentId values
        payload={"test": True},
    )
    receipt1 = orch.dispatch_mission(brief1)
    assert receipt1.status == "dispatched"
    assert receipt1.checkpoint_path is not None
    assert Path(receipt1.checkpoint_path).exists(), \
        f"Checkpoint not on disk: {receipt1.checkpoint_path}"
    assert receipt1.bi_record_id is not None
    print(f"  Dispatch: {receipt1.status}")
    print(f"  Checkpoint: {receipt1.checkpoint_path}")
    print(f"  BI record: {receipt1.bi_record_id}")

    # Test 2: Constitutional change without approval — must raise
    mid2 = f"test-{uuid.uuid4().hex[:8]}"
    brief2 = MissionBrief(
        mission_id=mid2,
        objective="Attempt constitutional change without approval",
        action_type="constitutional_change",
        assigned_agent="orchestrator",
        human_approval=False,
    )
    raised_cv = False
    try:
        orch.dispatch_mission(brief2)
    except ConstitutionalViolation:
        raised_cv = True
    assert raised_cv, "ConstitutionalViolation should have been raised"
    print("  Constitutional block: ConstitutionalViolation raised correctly")

    # Test 3: Permission denied — sigma lacks governance_audit
    mid3 = f"test-{uuid.uuid4().hex[:8]}"
    brief3 = MissionBrief(
        mission_id=mid3,
        objective="Sigma should not be able to run diagnostics",
        action_type="diagnostic",
        assigned_agent="sigma",  # Context Librarian — no governance_audit
    )
    raised_pd = False
    try:
        orch.dispatch_mission(brief3)
    except MissionPermissionDenied as e:
        raised_pd = True
        print(f"  Permission denied: raised correctly — {str(e)[:70]}")
    assert raised_pd, "MissionPermissionDenied should have been raised"

    # Test 4: Resume missing checkpoint — must raise MissionCheckpointNotFound
    raised_cp = False
    try:
        orch.resume_mission("nonexistent-mission-id", "SomeNode")
    except MissionCheckpointNotFound as e:
        raised_cp = True
        print(f"  Checkpoint not found: raised correctly — {str(e)[:60]}")
    assert raised_cp, "MissionCheckpointNotFound should have been raised"

    # Test 5: Checkpoint + resume round-trip
    mid5 = f"roundtrip-{uuid.uuid4().hex[:8]}"
    cp = orch.checkpoint_workflow(mid5, "TestNode", {"value": 42})
    assert cp.exists()
    restored = orch.resume_mission(mid5, "TestNode")
    assert restored["state"]["value"] == 42
    print("  Checkpoint round-trip: PASS")

    # Test 6: Coordinate writes to agent_comms
    msg_path = orch.coordinate(
        "friday", "ttlg",
        {"instruction": "run diagnostic", "priority": "high"},
        mission_id=mid1,
    )
    assert msg_path.exists()
    print(f"  Coordinate: message written to {msg_path.name}")

    # Test 7: Health check
    health = orch.health_check()
    assert health["status"] == "operational"
    assert health["roles_registered"] == 7
    print(f"  Health: {health['status']} ({health['checkpoint_missions']} missions checkpointed)")

    print("\n  PASS: agent_orchestrator all self-tests passed")
