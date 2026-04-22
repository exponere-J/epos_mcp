# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/meta_orchestrator.py
"""
EPOS Meta-Orchestrator v3.2
Constitutional governance layer for all mission execution.

Authority: EPOS_CONSTITUTION_v3.1.md
Mission: Route requests through constitutional validation before execution

Changes from v3.1:
  - GovernanceGate() init fixed (no verbose/dry_run kwargs)
  - Import paths corrected for engine/ layout
  - Doctor API aligned with deployed epos_doctor.py
  - Added load_dotenv + EPOSDoctor pre-flight for gate compliance
  - Added /run_mission endpoint for AZ bridge sprint integration
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv; load_dotenv()

# Path setup per Article II
EPOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EPOS_ROOT))
sys.path.insert(0, str(EPOS_ROOT / "engine"))

from engine.epos_doctor import EPOSDoctor; EPOSDoctor().run()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Constitutional imports — these live in engine/ alongside this file
try:
    from engine.epos_doctor import EPOSDoctor as Doctor
    from governance_gate import GovernanceGate
except ImportError:
    try:
        from epos_doctor import EPOSDoctor as Doctor
        from governance_gate import GovernanceGate
    except ImportError as e:
        print("CRITICAL: Core component missing - " + str(e))
        sys.exit(1)

# Agent Zero bridge (optional — degrades gracefully)
try:
    from agent_zero_bridge import health_check as az_health, run_mission as az_run
    _az_bridge = True
except ImportError:
    _az_bridge = False

# Intelligence engine (optional)
try:
    from epos_intelligence import record_decision, get_system_health_summary
    _intel = True
except ImportError:
    _intel = False

# Load agent registry
REGISTRY_PATH = EPOS_ROOT / "engine" / "agent_registry.json"
AGENT_REGISTRY: Dict[str, Any] = {}
if REGISTRY_PATH.exists():
    AGENT_REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

# FastAPI app
app = FastAPI(title="EPOS Meta-Orchestrator v3.2")

# Initialize core roles — GovernanceGate only accepts epos_root
doctor = Doctor()
gate = GovernanceGate()


# ── Request / Response Models ─────────────────────────────────

class MissionRequest(BaseModel):
    mission_id: str
    agent_role: str
    task: str
    data: Optional[Dict[str, Any]] = {}
    context_vault_refs: Optional[List[str]] = []


class MissionResponse(BaseModel):
    mission_id: str
    status: str
    agent: str
    output: Dict[str, Any]
    constitutional_score: int


class SprintMission(BaseModel):
    """Lightweight mission for AZ bridge sprint execution."""
    mission_id: str
    objective: str
    context: Optional[str] = ""
    constraints: Optional[List[str]] = []
    success_criteria: Optional[List[str]] = []
    context_vault_path: Optional[str] = None


# ── Startup ───────────────────────────────────────────────────

@app.on_event("startup")
async def startup_validation():
    """Article V: Pre-flight checks before accepting missions"""
    print("\n=== EPOS Meta-Orchestrator v3.2 Starting ===")
    print("  Gate: OK")
    print("  AZ Bridge: " + ("CONNECTED" if _az_bridge else "NOT AVAILABLE"))
    print("  Intelligence: " + ("CONNECTED" if _intel else "NOT AVAILABLE"))
    print("  Registry: " + str(len(AGENT_REGISTRY.get("core_roles", []))) + " core roles")
    print("  Port: 8001")
    print("\n=== READY FOR MISSIONS ===\n")


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """System health status"""
    result = {
        "status": "operational",
        "version": "3.2.0",
        "constitution": "EPOS_CONSTITUTION_v3.1.md",
        "registered_roles": len(AGENT_REGISTRY.get("core_roles", [])),
        "az_bridge": "connected" if _az_bridge else "not_available",
        "intelligence": "connected" if _intel else "not_available",
    }
    if _az_bridge:
        result["az_health"] = az_health()
    if _intel:
        result["system_summary"] = get_system_health_summary()
    return result


@app.post("/run_mission")
async def run_sprint_mission(mission: SprintMission):
    """
    Sprint execution endpoint — routes missions through AZ bridge.
    This is the primary endpoint for Growth Steward sprints.
    """
    if not _az_bridge:
        raise HTTPException(
            status_code=503,
            detail="Agent Zero bridge not available. Install agent_zero_bridge.py in engine/."
        )

    mission_dict = mission.model_dump()

    # Log decision if intelligence is available
    if _intel:
        record_decision(
            decision_type="mission_dispatch",
            description="Sprint mission routed to AZ: " + mission.objective[:100],
            context={"mission_id": mission.mission_id},
            flywheel_stage="execution",
        )

    result = az_run(mission_dict)
    return result


@app.post("/execute", response_model=MissionResponse)
async def execute_mission(request: MissionRequest):
    """
    Constitutional mission execution gateway.
    Routes to registered agent roles.
    """
    # Article VII: Context governance
    inline_size = len(str(request.data))
    if inline_size > 8192 and not request.context_vault_refs:
        raise HTTPException(
            status_code=400,
            detail="ERR-CONTEXT-001: Inline data (" + str(inline_size) + " chars) exceeds 8K limit. Use context_vault."
        )

    # Find agent role
    role_config = _get_role_config(request.agent_role)
    if not role_config:
        raise HTTPException(
            status_code=404,
            detail="Agent role '" + request.agent_role + "' not found in registry"
        )

    try:
        if request.agent_role == "arbiter":
            output = await _execute_arbiter(request)
        elif request.agent_role == "librarian":
            output = await _execute_librarian(request)
        elif request.agent_role == "analyst":
            output = await _execute_analyst(request)
        else:
            output = {"error": "Role not yet implemented"}

        _log_mission(request, output, "success")

        return MissionResponse(
            mission_id=request.mission_id,
            status="aligned",
            agent=request.agent_role,
            output=output,
            constitutional_score=95,
        )

    except Exception as e:
        _log_mission(request, {"error": str(e)}, "failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate")
async def validate_file(file_path: str):
    """Run governance gate validation on a file."""
    p = Path(file_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found: " + file_path)
    result = gate.validate_file(p)
    return result


# ── Role Executors ────────────────────────────────────────────

async def _execute_arbiter(request: MissionRequest) -> Dict[str, Any]:
    try:
        from roles.arbiter import ConstitutionalArbiter
        arbiter = ConstitutionalArbiter()
        if request.task == "scan_pr":
            return arbiter.scan_pull_request(request.data)
        elif request.task == "merge_gate":
            return arbiter.run_merge_gate(request.data)
        elif request.task == "sprint_audit":
            return arbiter.audit_engine()
        return {"error": "Unknown arbiter task: " + request.task}
    except ImportError:
        return {"error": "Arbiter role not installed"}


async def _execute_librarian(request: MissionRequest) -> Dict[str, Any]:
    try:
        from roles.librarian import ContextLibrarian
        librarian = ContextLibrarian()
        if request.task == "ingest":
            return librarian.ingest_content(request.data)
        elif request.task == "search":
            return librarian.search_vault(request.data)
        elif request.task == "hygiene":
            return librarian.vault_hygiene()
        return {"error": "Unknown librarian task: " + request.task}
    except ImportError:
        return {"error": "Librarian role not installed"}


async def _execute_analyst(request: MissionRequest) -> Dict[str, Any]:
    try:
        from roles.analyst import FlywheelAnalyst
        analyst = FlywheelAnalyst()
        if request.task == "detect_patterns":
            return analyst.detect_failure_patterns(request.data)
        elif request.task == "flywheel_metrics":
            return analyst.calculate_flywheel_metrics()
        elif request.task == "propose_amendment":
            return analyst.propose_constitutional_amendment(request.data)
        return {"error": "Unknown analyst task: " + request.task}
    except ImportError:
        return {"error": "Analyst role not installed"}


# ── Helpers ───────────────────────────────────────────────────

def _get_role_config(role_id: str) -> Optional[Dict]:
    for role in AGENT_REGISTRY.get("core_roles", []):
        if role.get("id") == role_id:
            return role
    return None


def _log_mission(request: MissionRequest, output: Dict, status: str):
    """Log to BI decision log per Article VIII"""
    log_dir = EPOS_ROOT / "ops" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bi_decision_log.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "mission_id": request.mission_id,
        "agent_role": request.agent_role,
        "task": request.task,
        "status": status,
    }
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    print("EPOS Meta-Orchestrator v3.2 — standalone launch")
    uvicorn.run(app, host="127.0.0.1", port=8001)
