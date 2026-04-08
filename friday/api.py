#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
api.py — Friday FastAPI Endpoint
====================================
Constitutional Authority: EPOS Constitution v3.1

REST API for submitting directives to Friday.
Runs on port 8090 alongside the EPOS daemon.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from friday.friday_graph import friday_app, invoke_friday, MISSIONS_DIR
import json

app = FastAPI(title="EPOS Friday Orchestrator", version="2.0.0")


class DirectiveRequest(BaseModel):
    text: str


@app.post("/directive")
async def receive_directive(req: DirectiveRequest, background_tasks: BackgroundTasks):
    """Submit a directive to Friday."""
    background_tasks.add_task(invoke_friday, req.text)
    return {
        "status": "accepted",
        "directive": req.text[:200],
        "received_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/directive/sync")
async def receive_directive_sync(req: DirectiveRequest):
    """Submit a directive and wait for the result (blocking)."""
    result = invoke_friday(req.text)
    return result


@app.get("/health")
async def health():
    return {
        "status": "operational",
        "agent": "friday",
        "version": "2.0.0",
    }


@app.get("/status")
async def status():
    """Return last 5 mission results from vault."""
    if not MISSIONS_DIR.exists():
        return {"missions": [], "count": 0}

    files = sorted(MISSIONS_DIR.glob("DIR-*_aar.json"),
                   key=lambda f: f.stat().st_mtime, reverse=True)[:5]
    missions = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            missions.append({
                "directive_id": data.get("directive_id"),
                "directive": data.get("directive", "")[:150],
                "mission_type": data.get("mission_type"),
                "success": data.get("success"),
                "completed_at": data.get("completed_at"),
            })
        except Exception:
            pass
    return {"missions": missions, "count": len(missions)}


@app.get("/")
async def root():
    return {
        "service": "EPOS Friday Orchestrator",
        "endpoints": ["/directive (POST)", "/directive/sync (POST)", "/health", "/status"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8090)
