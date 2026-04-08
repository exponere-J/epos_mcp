# File: C:/Users/Jamie/workspace/epos_mcp/config.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# ============================================================
# FILE:    C:/Users/Jamie/workspace/epos_mcp/config.py
# PURPOSE: Single Source of Truth for all EPOS paths and
#          constants. Every module imports from here.
#          No module may hardcode a path. Ever.
# ARTICLE: Constitution v3.1, Article II, Rule 1 (Path Absolutism)
#          Constitution v3.1, Article II, Rule 6 (Config Explicitness)
# ============================================================

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- Environment Enforcement ---
MIN_PYTHON = (3, 11)
if sys.version_info[:2] < MIN_PYTHON:
    raise EnvironmentError(
        f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required. "
        f"Found: {sys.version_info[0]}.{sys.version_info[1]}"
    )

# --- Root ---
# EPOS_ROOT env var is set to /app in Docker; falls back to the repo root on the host.
EPOS_ROOT        = Path(os.getenv("EPOS_ROOT", Path(__file__).resolve().parent))
AZ_ROOT          = Path(os.getenv("AGENT_ZERO_PATH", EPOS_ROOT.parent / "agent-zero"))

# --- Core Directories ---
ENGINE_DIR       = EPOS_ROOT / "engine"
INBOX_DIR        = EPOS_ROOT / "inbox"
QUARANTINE_DIR   = EPOS_ROOT / "quarantine"
LOGS_DIR         = EPOS_ROOT / "logs"
OPS_DIR          = EPOS_ROOT / "ops"
QUEUE_DIR        = EPOS_ROOT / "queue"
CONTEXT_VAULT    = EPOS_ROOT / "context_vault"
MISSIONS_DIR     = EPOS_ROOT / "engine" / "missions"
RECEIPTS_DIR     = CONTEXT_VAULT / "receipts"
EVENTS_LOG       = OPS_DIR / "events.jsonl"
COMPLIANCE_LOG   = OPS_DIR / "compliance_report.json"
OVERRIDE_LOG     = OPS_DIR / "override_log.json"

# --- Agent Zero Integration ---
AZ_API_URL       = os.getenv("AGENT_ZERO_URL", "http://agent-zero:50080")
AZ_HEALTH_URL    = f"{AZ_API_URL}/health"
AZ_RUN_URL       = f"{AZ_API_URL}/run-task"
AZ_RUNNER_LOG    = LOGS_DIR / "az_runner.log"

# --- Constitutional Documents (must exist) ---
CONSTITUTIONAL_DOCS = [
    EPOS_ROOT / "ENVIRONMENT_SPEC.md",
    EPOS_ROOT / "COMPONENT_INTERACTION_MATRIX.md",
    EPOS_ROOT / "FAILURE_SCENARIOS.md",
    EPOS_ROOT / "PATH_CLARITY_RULES.md",
    EPOS_ROOT / "PRE_FLIGHT_CHECKLIST.md",
]

# --- Load Environment ---
_env_path = EPOS_ROOT / ".env"
load_dotenv(_env_path)

# --- Ensure Critical Directories Exist ---
for _d in [ENGINE_DIR, INBOX_DIR, QUARANTINE_DIR, LOGS_DIR,
           OPS_DIR, QUEUE_DIR, CONTEXT_VAULT, MISSIONS_DIR, RECEIPTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
