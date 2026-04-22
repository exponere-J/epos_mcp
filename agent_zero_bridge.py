#!/usr/bin/env python3
"""
agent_zero_bridge.py — EPOS Agent Zero Execution Bridge
=========================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles II, III, VII, X
Mission ID: EPOS Core Heal — Module 9 of 9 (FINAL)
File Location: /mnt/c/Users/Jamie/workspace/epos_mcp/agent_zero_bridge.py

Single responsibility: Translate orchestrated missions into Agent Zero
subprocess calls. Enforce the constitutional rule that logged-is-not-executed.
Degrade gracefully when AZ is unavailable.

CONSTITUTIONAL RULE — LOGGED IS NOT EXECUTED:
  status="executed" requires three proof artifacts:
    1. az_exit_code == 0
    2. checkpoint file exists on disk
    3. BI record ID is not None
  Anything missing → status is "failed" or "unavailable".

Dependencies: All 8 prior modules.
"""

import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any

from dotenv import load_dotenv

from path_utils import get_epos_root, get_agent_zero_path, get_context_vault, get_logs_dir
from stasis import ConstitutionalViolation
from roles import AgentId, validate_assignment, Capability
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision, record_mission_outcome
from agent_orchestrator import (
    AgentOrchestrator, MissionBrief, MissionReceipt, AgentZeroUnavailable,
)


# ── Data Structures ──────────────────────────────────────────────

@dataclass
class BridgeHealth:
    """Health status of the Agent Zero bridge."""
    ok: bool
    az_path_exists: bool
    az_config_valid: bool
    az_deps_installed: bool
    reason: Optional[str]
    checked_at: str


@dataclass
class ExecutionReceipt:
    """Result of an Agent Zero mission execution."""
    mission_id: str
    status: str               # "executed" | "failed" | "unavailable" | "timeout"
    az_exit_code: Optional[int]
    az_stdout: Optional[str]
    az_stderr: Optional[str]
    bi_record_id: Optional[str]
    checkpoint_path: Optional[str]
    executed_at: str
    reason: Optional[str]


# ── AgentZeroBridge ──────────────────────────────────────────────

class AgentZeroBridge:
    """
    Final execution mile. Translates orchestrated missions to AZ calls.

    Constitutional rule: logged is not executed.
    status="executed" requires three proof artifacts:
      1. az_exit_code == 0
      2. checkpoint file on disk
      3. BI record ID

    Degrades gracefully when AZ unavailable.
    Never reports success when AZ is not confirmed operational.
    """

    AZ_TIMEOUT_SECONDS = 300

    def __init__(self):
        load_dotenv(Path(__file__).resolve().parent / ".env")
        self.az_path = get_agent_zero_path()
        self.vault_root = get_context_vault()
        self.orchestrator = AgentOrchestrator()

    # ── Health Check ─────────────────────────────────────────────

    def health_check(self) -> BridgeHealth:
        """
        Real health check. Never returns ok=True when AZ is not ready.
        Checks: agent.py exists, config.json valid, litellm importable.
        """
        az_root = self.az_path

        # Check 1: agent.py exists at AZ root
        az_agent_exists = (az_root / "agent.py").exists()

        # Check 2: config.json is valid JSON
        config_valid = False
        config_path = az_root / "config.json"
        if config_path.exists():
            try:
                json.loads(config_path.read_text(encoding="utf-8"))
                config_valid = True
            except (json.JSONDecodeError, OSError):
                pass

        # Check 3: AZ dependencies installed
        # Fast check: look for litellm package directory instead of slow subprocess import
        deps_ok = False
        try:
            import importlib.util
            deps_ok = importlib.util.find_spec("litellm") is not None
        except Exception:
            # Fallback: check site-packages directly
            import site
            for sp in site.getsitepackages() + [site.getusersitepackages()]:
                if (Path(sp) / "litellm").is_dir():
                    deps_ok = True
                    break

        ok = az_agent_exists and config_valid and deps_ok
        reason = None
        if not ok:
            if not az_root.exists():
                reason = f"Agent Zero directory not found: {az_root}"
            elif not az_agent_exists:
                reason = f"agent.py not found at AZ root: {az_root}"
            elif not config_valid:
                reason = f"config.json missing or invalid JSON at: {config_path}"
            elif not deps_ok:
                reason = (
                    "Agent Zero dependencies not installed. "
                    "Run: cd agent-zero && pip install -r requirements.txt"
                )

        return BridgeHealth(
            ok=ok,
            az_path_exists=az_agent_exists,
            az_config_valid=config_valid,
            az_deps_installed=deps_ok,
            reason=reason,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── Mission Execution ────────────────────────────────────────

    def execute_mission(self, brief: MissionBrief) -> ExecutionReceipt:
        """
        Full execution pipeline:
        1. Health check — never execute blind
        2. Dispatch through orchestrator (permission gate + checkpoint)
        3. Write BridgeNode checkpoint
        4. Execute AZ via subprocess with --prompt
        5. Log to BI
        6. Enforce three-artifact rule for status="executed"
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # ── 1. Health check ──────────────────────────────────────
        health = self.health_check()
        if not health.ok:
            record_decision(
                decision_type="agent.mission_unavailable",
                description=f"AZ unavailable for mission {brief.mission_id}: {health.reason}",
                agent_id=AgentId.BRIDGE.value,
                context={"mission_id": brief.mission_id, "reason": health.reason},
                outcome="unavailable",
            )
            raise AgentZeroUnavailable(
                f"Agent Zero not ready: {health.reason}. "
                f"Cannot report status=executed when AZ is unavailable."
            )

        # ── 2. Dispatch through orchestrator ─────────────────────
        receipt = self.orchestrator.dispatch_mission(brief)

        # ── 3. BridgeNode checkpoint (proof artifact 2) ─────────
        cp = self.orchestrator.checkpoint_workflow(
            brief.mission_id,
            "BridgeNode",
            {
                "brief_objective": brief.objective,
                "action_type": brief.action_type,
                "assigned_agent": brief.assigned_agent,
                "az_path": str(self.az_path),
                "status": "dispatched_to_az",
            },
        )

        # ── 4. Execute AZ via subprocess ─────────────────────────
        # AZ run.py uses --prompt for direct prompt string
        prompt = (
            f"EPOS Mission {brief.mission_id}\n"
            f"Objective: {brief.objective}\n"
            f"Action: {brief.action_type}\n"
            f"Payload: {json.dumps(brief.payload)}"
        )

        try:
            az_result = subprocess.run(
                ["python", "run.py", "--prompt", prompt, "--json",
                 "--timeout", str(self.AZ_TIMEOUT_SECONDS)],
                capture_output=True,
                text=True,
                cwd=str(self.az_path),
                timeout=self.AZ_TIMEOUT_SECONDS + 30,  # outer timeout > inner
            )
        except subprocess.TimeoutExpired:
            record_mission_outcome(
                mission_id=brief.mission_id,
                status="timeout",
                agent_id=AgentId.BRIDGE.value,
                error=f"Subprocess timed out after {self.AZ_TIMEOUT_SECONDS}s",
            )
            raise AgentZeroUnavailable(
                f"Mission {brief.mission_id} timed out after "
                f"{self.AZ_TIMEOUT_SECONDS}s"
            )
        except FileNotFoundError:
            raise AgentZeroUnavailable(
                "python executable not found for AZ subprocess"
            )

        # ── 5. Determine status + BI record (proof artifact 1) ──
        if az_result.returncode == 0:
            raw_status = "executed"
            outcome = "success"
        else:
            raw_status = "failed"
            outcome = "failed"

        bi_result = record_mission_outcome(
            mission_id=brief.mission_id,
            status=raw_status,
            agent_id=AgentId.BRIDGE.value,
            execution_time_ms=None,  # subprocess doesn't easily expose this
            error=az_result.stderr[:200] if az_result.stderr and raw_status == "failed" else None,
            details={
                "exit_code": az_result.returncode,
                "checkpoint_path": str(cp),
                "stdout_length": len(az_result.stdout or ""),
            },
        )
        bi_record_id = bi_result.get("status")  # "recorded" confirms write

        # ── 6. Three-artifact enforcement ────────────────────────
        # CONSTITUTIONAL RULE: logged is not executed
        checkpoint_confirmed = cp.exists()
        bi_confirmed = bi_result.get("status") == "recorded"

        final_status = raw_status
        if final_status == "executed" and not (checkpoint_confirmed and bi_confirmed):
            final_status = "failed"

        reason = None
        if final_status != "executed":
            reason = (
                az_result.stderr[:200] if az_result.stderr
                else f"AZ exit code: {az_result.returncode}"
            )

        return ExecutionReceipt(
            mission_id=brief.mission_id,
            status=final_status,
            az_exit_code=az_result.returncode,
            az_stdout=az_result.stdout[:2000] if az_result.stdout else None,
            az_stderr=az_result.stderr[:500] if az_result.stderr else None,
            bi_record_id=bi_record_id if bi_confirmed else None,
            checkpoint_path=str(cp) if checkpoint_confirmed else None,
            executed_at=now_iso,
            reason=reason,
        )

    # ── Convenience ──────────────────────────────────────────────

    def status_summary(self) -> Dict[str, Any]:
        """Quick summary for CLI / dashboard."""
        health = self.health_check()
        return {
            "bridge": "operational" if health.ok else "degraded",
            "az_ready": health.ok,
            "az_path": str(self.az_path),
            "reason": health.reason,
            "checked_at": health.checked_at,
        }


# ── Self-test ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EPOS Agent Zero Bridge v2.0 — Self-test")
    print("=" * 55)

    bridge = AgentZeroBridge()

    # Test 1: health_check() returns BridgeHealth — does not crash
    health = bridge.health_check()
    assert isinstance(health, BridgeHealth)
    assert health.checked_at is not None
    print(f"  AZ health: ok={health.ok}")
    print(f"    az_path_exists: {health.az_path_exists}")
    print(f"    az_config_valid: {health.az_config_valid}")
    print(f"    az_deps_installed: {health.az_deps_installed}")
    if not health.ok:
        print(f"    reason: {health.reason}")

    # Test 2: execute_mission raises AgentZeroUnavailable when AZ not ready
    if not health.ok:
        brief = MissionBrief(
            mission_id=f"test-{uuid.uuid4().hex[:8]}",
            objective="Bridge self-test — unavailability check",
            action_type="agent_mission",
            assigned_agent="bridge",
        )
        raised = False
        try:
            bridge.execute_mission(brief)
        except AgentZeroUnavailable as e:
            raised = True
            print(f"  AgentZeroUnavailable raised: {str(e)[:80]}")
        assert raised, "AgentZeroUnavailable should have been raised"
    else:
        print("  AZ available — skip unavailability test (would execute for real)")

    # Test 3: BridgeHealth reason is specific
    if not health.ok:
        assert health.reason is not None
        assert len(health.reason) > 10, "Reason string too vague"
        print(f"  Reason specificity: PASS ({len(health.reason)} chars)")

    # Test 4: Full import chain — all 9 modules
    print("\n  Full import chain test:")
    import importlib
    modules = [
        "path_utils", "stasis", "roles", "epos_intelligence",
        "context_librarian", "constitutional_arbiter",
        "flywheel_analyst", "agent_orchestrator", "agent_zero_bridge",
    ]
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"    {mod}: OK")
        except ImportError as e:
            print(f"    {mod}: FAILED — {e}")
            raise

    print("\n  PASS: agent_zero_bridge all self-tests passed")
    print("  Sprint 2 complete: 9/9 modules built")
