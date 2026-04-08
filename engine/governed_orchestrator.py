# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/engine\governed_orchestrator.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: C:\Users\Jamie\workspace\epos_mcp\engine\governed_orchestrator.py

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Constitutional Imports — ensure sibling + root modules importable
import sys
_ENGINE_DIR = Path(__file__).resolve().parent
_EPOS_ROOT = _ENGINE_DIR.parent
for _p in [str(_ENGINE_DIR), str(_EPOS_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from stasis import StasisEngine
from path_utils import get_epos_root, validate_path

app = FastAPI(title="EPOS Governed Orchestrator")
stasis = StasisEngine()

class MissionRequest(BaseModel):
    mission_id: str
    data: str
    context_vault_path: Optional[str] = None

@app.get("/health")
async def health_check():
    """Returns the combined status of the environment and engine purity."""
    stasis_achieved = stasis.is_stasis()
    return {
        "status": "ALIGNED" if stasis_achieved else "MISALIGNED",
        "stasis": stasis_achieved,
        "engine_purity": stasis.check_engine_purity(),
        "environment": stasis.check_environment()
    }

@app.post("/execute")
async def execute_mission(request: MissionRequest):
    """
    Governed mission execution gate.
    Requires Stasis before proceeding (Article V).
    """
    # 1. Check Stasis
    if not stasis.is_stasis():
        # Attempt one auto-correction before failing
        stasis.achieve_stasis()
        if not stasis.is_stasis():
            raise HTTPException(
                status_code=503, 
                detail="STASIS_REQUIRED: System is misaligned. Run autonomy.py for recovery."
            )

    # 2. Context Governance Check (Article VII.1.1)
    # Rejects mission if token limit is exceeded without vault usage
    if len(request.data.split()) > 8192 and not request.context_vault_path:
        raise HTTPException(
            status_code=400,
            detail="ERR-CONTEXT-001: Inline data exceeds token limit. Use context_vault."
        )

    # 3. Path Validation (Article II.1)
    if request.context_vault_path and not validate_path(request.context_vault_path):
         raise HTTPException(
            status_code=400,
            detail="ERR-PATH-001: Invalid path format. Windows-style required."
        )

    return {"status": "MISSION_STARTED", "mission_id": request.mission_id}

if __name__ == "__main__":
    import uvicorn
    # Enforce stasis on startup
    print(f"Startup Alignment: {stasis.achieve_stasis()}")
    uvicorn.run(app, host="127.0.0.1", port=8001)