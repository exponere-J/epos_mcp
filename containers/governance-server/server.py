# File: ${EPOS_ROOT}/containers/governance-server/server.py
# Constitutional Authority: Article XI (Agent Zero Supremacy)

import sys
from pathlib import Path
REQUIRED_PYTHON = (3, 11)
if sys.version_info[:2] < REQUIRED_PYTHON:
    raise EnvironmentError(f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required")

import re
import logging
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("governance-gate")

app = FastAPI(title="EPOS Governance Gate", version="1.0.0")

class Action(BaseModel):
    action_id: str
    action_type: str
    target: str
    reason: str
    constitutional_authority: str = ""

class ConstitutionalEnforcer:
    def __init__(self):
        self.violations = []
    
    def validate(self, action: dict) -> dict:
        violations = []
        
        # Rule 1: Path Absolutism (Article II, Rule 1)
        if "path" in action.get("target", "").lower():
            if ".." in action["target"] or action["target"].startswith("./"):
                violations.append({
                    "rule": "Article II, Rule 1 (Path Absolutism)",
                    "reason": "Relative path detected",
                    "remediation": "Use absolute paths rooted at ${EPOS_ROOT}"
                })
        
        # Rule 2: No Silent Failures (Article II, Rule 2)
        if "try" in action.get("reason", "").lower() and "except" not in action.get("reason", "").lower():
            violations.append({
                "rule": "Article II, Rule 2 (No Silent Failures)",
                "reason": "Exception handling without logging detected",
                "remediation": "All exceptions must log to Event Bus"
            })
        
        # Rule 3: Constitutional Authority Required
        if not action.get("constitutional_authority"):
            violations.append({
                "rule": "Article XI, Section 2 (Command Authority)",
                "reason": "Missing constitutional authority reference",
                "remediation": "Specify which Article authorizes this action"
            })
        
        approved = len(violations) == 0
        
        result = {
            "approved": approved,
            "action_id": action.get("action_id"),
            "violations": violations,
            "retry_allowed": len(violations) == 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if approved:
            logger.info(f"✅ Action approved: {action.get('action_id')}")
        else:
            logger.warning(f"❌ Action rejected: {action.get('action_id')} - {len(violations)} violations")
        
        return result

enforcer = ConstitutionalEnforcer()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "governance-gate",
        "constitution": "EPOS_CONSTITUTION_v3_1.md",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/validate")
async def validate_action(action: Action):
    return enforcer.validate(action.dict())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8101, log_level="info")
