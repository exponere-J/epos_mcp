# File: /mnt/c/Users/Jamie/workspace/epos_mcp/az_dispatch.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# ============================================================
# FILE:    /mnt/c/Users/Jamie/workspace/epos_mcp/az_dispatch.py
# PURPOSE: The single entry point for dispatching all missions
#          to Agent Zero. This file is the nervous system
#          bridge between EPOS governance and AZ execution.
#          It enforces: pre-flight → governance gate →
#          dispatch → receipt → event log.
# ARTICLE: Constitution v3.1, Article II (All Rules)
#          Constitution v3.1, Article X (Vendor Integration)
#          Constitution v3.1, Article III (Quality Gates)
# 9TH ORDER NOTE: This file IS the frictionless path.
#          Jamie writes a mission brief. This file does
#          the rest. No skill debt is owed downstream.
# ============================================================

import sys
from pathlib import Path
from dotenv import load_dotenv

REQUIRED_PYTHON = (3, 11)
if sys.version_info[:2] < REQUIRED_PYTHON:
    raise EnvironmentError(f"Python 3.11+ required. Found: {sys.version_info[:2]}")

load_dotenv(Path(__file__).parent / ".env")

import json
import uuid
import logging
import requests
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from config import (
    EPOS_ROOT, AZ_RUN_URL, AZ_HEALTH_URL,
    LOGS_DIR, MISSIONS_DIR, RECEIPTS_DIR,
    EVENTS_LOG, AZ_RUNNER_LOG
)
from engine.command_validator import validate, CommandViolation

# --- Logging ---
logger = logging.getLogger("az_dispatch")
logging.basicConfig(
    filename=str(AZ_RUNNER_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ─────────────────────────────────────────────
# MISSION BRIEF SCHEMA (Constitution Art. III)
# ─────────────────────────────────────────────
class MissionBrief(BaseModel):
    mission_id:       str = Field(default_factory=lambda: f"MISS-{uuid.uuid4().hex[:8].upper()}")
    intent:           str                    # What you want to achieve (plain English)
    execution_arm:    str = "terminal"       # "terminal" | "browser" | "computer"
    how:              List[str]              # Step-by-step instructions for Agent Zero
    constraints:      List[str] = []        # Safety, idempotency rules
    success_criteria: str = ""              # Verifiable outcome
    failure_modes:    List[str] = []        # Pre-imagined failure scenarios
    dry_run:          bool = False          # True = plan only, no execution
    context_vault_path: Optional[str] = None  # Required if data > 8K tokens


# ─────────────────────────────────────────────
# STEP 1: PRE-FLIGHT CHECK
# ─────────────────────────────────────────────
def _preflight_check() -> bool:
    """Verify AZ is online and EPOS environment is healthy."""
    logger.info("PREFLIGHT: Checking Agent Zero health...")
    try:
        r = requests.get(AZ_HEALTH_URL, timeout=5)
        assert r.status_code == 200, f"AZ health check failed: {r.status_code}"
        logger.info("PREFLIGHT: Agent Zero ONLINE ✓")
    except Exception as e:
        logger.error(f"PREFLIGHT FAILED — Agent Zero unreachable: {e}")
        raise RuntimeError(
            f"Agent Zero is not running at {AZ_HEALTH_URL}.\n"
            f"Start it with: uvicorn eposrunner:app --port 8001\n"
            f"Error: {e}"
        )
    return True


# ─────────────────────────────────────────────
# STEP 2: GOVERNANCE GATE
# ─────────────────────────────────────────────
def _governance_gate(brief: MissionBrief) -> bool:
    """
    Constitutional validation before any mission executes.
    Validates all 'how' steps against the command allowlist.
    Rejects inline data > 8K tokens (Article II, Rule 7).
    """
    logger.info(f"GOVERNANCE GATE: Auditing mission {brief.mission_id}...")

    # Rule 7: Context Vault Mandate
    combined_size = sum(len(step) for step in brief.how)
    if combined_size > 8192 and not brief.context_vault_path:
        raise ValueError(
            f"GOVERNANCE REJECTION\n"
            f"Mission: {brief.mission_id}\n"
            f"Violation: how[] payload exceeds 8,192 chars ({combined_size}) "
            f"without a context_vault_path.\n"
            f"Article: Constitution v3.1, Article II, Rule 7\n"
            f"Remediation: Write data to context_vault/ and set context_vault_path."
        )

    # Rule 5: Validate commands for terminal arm
    if brief.execution_arm == "terminal":
        for step in brief.how:
            try:
                validate(step)
            except CommandViolation as e:
                raise ValueError(str(e))

    logger.info(f"GOVERNANCE GATE: Mission {brief.mission_id} PROMOTED ✓")
    return True


# ─────────────────────────────────────────────
# STEP 3: DISPATCH TO AGENT ZERO
# ─────────────────────────────────────────────
def _dispatch(brief: MissionBrief) -> dict:
    """Send the mission to Agent Zero's execution API."""
    payload = {
        "goal": brief.intent,
        "commands": [{"cmd": step} for step in brief.how],
        "dryrun": brief.dry_run
    }

    logger.info(f"DISPATCHING: {brief.mission_id} → {AZ_RUN_URL}")

    try:
        r = requests.post(AZ_RUN_URL, json=payload, timeout=300)
        r.raise_for_status()
        result = r.json()
        logger.info(f"DISPATCH SUCCESS: {brief.mission_id} task_id={result.get('taskid')}")
        return result
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Agent Zero timed out on mission {brief.mission_id}")
    except Exception as e:
        raise RuntimeError(f"Dispatch failed for {brief.mission_id}: {e}")


# ─────────────────────────────────────────────
# STEP 4: WRITE AUDIT RECEIPT
# ─────────────────────────────────────────────
def _write_receipt(brief: MissionBrief, result: dict) -> Path:
    """
    Write a signed audit receipt to context_vault/receipts/.
    This is the 'proof' that distinguishes execution from logging.
    Article II, Rule 2: No Silent Failures.
    Article II, Rule 4: Separation of Concerns.
    """
    receipt = {
        "mission_id":      brief.mission_id,
        "intent":          brief.intent,
        "execution_arm":   brief.execution_arm,
        "dispatched_at":   datetime.now(timezone.utc).isoformat(),
        "dry_run":         brief.dry_run,
        "success_criteria": brief.success_criteria,
        "az_task_id":      result.get("taskid"),
        "az_return_codes": result.get("returncodes", []),
        "az_outputs":      result.get("outputs", []),
        "status":          "executed" if not brief.dry_run else "dry_run",
        "proof":           str(RECEIPTS_DIR / f"{brief.mission_id}.json")
    }

    receipt_path = RECEIPTS_DIR / f"{brief.mission_id}.json"
    try:
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        logger.info(f"RECEIPT WRITTEN: {receipt_path}")
        assert receipt_path.exists(), "Receipt file not created — silent failure detected"
    except Exception as e:
        logger.error(f"RECEIPT WRITE FAILED: {e}")
        raise

    # Append to global event log
    with EVENTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt) + "\n")
    logger.info(f"EVENT LOGGED: {EVENTS_LOG}")

    return receipt_path


# ─────────────────────────────────────────────
# PUBLIC API: The One Function Jamie Calls
# ─────────────────────────────────────────────
def dispatch(brief: MissionBrief) -> dict:
    """
    The frictionless path.

    Jamie provides a MissionBrief. This function:
      1. Validates the environment (preflight)
      2. Audits the mission (governance gate)
      3. Dispatches to Agent Zero (execution)
      4. Writes a signed receipt (audit trail)
      5. Returns the full outcome

    No step is skipped. No failure is silent.
    """
    logger.info(f"═══ MISSION BEGIN: {brief.mission_id} ═══")

    _preflight_check()
    _governance_gate(brief)
    result = _dispatch(brief)
    receipt_path = _write_receipt(brief, result)

    outcome = {
        "mission_id":   brief.mission_id,
        "status":       "executed" if not brief.dry_run else "dry_run",
        "receipt":      str(receipt_path),
        "az_task_id":   result.get("taskid"),
        "outputs":      result.get("outputs", []),
        "return_codes": result.get("returncodes", [])
    }

    logger.info(f"═══ MISSION COMPLETE: {brief.mission_id} ═══")
    return outcome


# ─────────────────────────────────────────────
# CLI: Run a mission from the terminal
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # EXAMPLE: Self-building mission — AZ scaffolds the rest of EPOS
    first_mission = MissionBrief(
        mission_id="MISS-AZ-BOOTSTRAP-001",
        intent="Scaffold the remaining EPOS system using Agent Zero as the execution arm",
        execution_arm="terminal",
        how=[
            f"python {EPOS_ROOT}/epos_doctor.py",
            f"mkdir -p {EPOS_ROOT}/engine/missions",
            f"mkdir -p {EPOS_ROOT}/queue/email",
            f"mkdir -p {EPOS_ROOT}/context_vault/receipts",
            f"echo 'EPOS AZ Bootstrap complete' >> {EPOS_ROOT}/logs/bootstrap.log",
        ],
        constraints=[
            "All paths must be absolute paths rooted at EPOS_ROOT",
            "Idempotent — safe to re-run (mkdir -p)",
            "No destructive commands",
            "Log every step"
        ],
        success_criteria=(
            "epos_doctor.py exits with code 0 AND "
            "bootstrap.log exists in logs/"
        ),
        failure_modes=[
            "AZ not running — start with: docker compose up -d agent-zero",
            "Python not 3.11 — verify container image",
            "EPOS_ROOT not set — set env var or check Docker compose"
        ],
        dry_run=False
    )

    result = dispatch(first_mission)
    print(json.dumps(result, indent=2))
