# File: C:/Users/Jamie/workspace/epos_mcp/meta_orchestrator.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# ==============================================================================
# FILE: C:/Users/Jamie/workspace/epos_mcp/meta_orchestrator.py
# ROLE: META-ORCHESTRATOR / CENTRAL NERVOUS SYSTEM ROUTER
# ==============================================================================

import os
import json
from pathlib import Path

from fastapi import FastAPI
import httpx
from dotenv import load_dotenv

app = FastAPI(title="EPOS CNS Router")

# Load environment from project root
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

AZ_URL = f"{os.getenv('AZ_HOST', 'http://localhost')}:{os.getenv('AZ_PORT', '8001')}{os.getenv('AZ_ENDPOINT', '/run-task')}"
OLLAMA_URL = f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/generate"
MODEL = os.getenv('REASONING_MODEL', 'phi4')


async def route_mission(mission: dict):
    engine = mission.get("engine", "auto")
    mission_id = mission.get("id", "UNKNOWN")

    print(f"[*] [CNS] ROUTING MISSION {mission_id} -> {engine.upper()}")

    if engine == "agentzero":
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(AZ_URL, json=mission)
            return resp.json()

    elif engine == "phi3":
        payload = {
            "model": MODEL,
            "prompt": f"SYSTEM: You are the EPOS Reasoning Engine. MISSION: {mission['prompt']}",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            return {"response": resp.json()['response'], "engine": "phi3"}

    elif engine == "auto":
        # Step 1: Reasoning (Phi-3)
        plan_mission = {**mission, "engine": "phi3", "prompt": f"Decompose this mission into executable steps for Agent Zero: {mission['prompt']}"}
        plan_resp = await route_mission(plan_mission)

        # Step 2: Execution (AZ)
        exec_mission = {**mission, "engine": "agentzero", "prompt": plan_resp['response']}
        return await route_mission(exec_mission)

    else:
        return {"error": f"Unknown engine: {engine}", "mission_id": mission_id}
