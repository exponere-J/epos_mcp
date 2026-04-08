# File: C:/Users/Jamie/workspace/epos_mcp/epos_runner.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# ============================================================
# FILE:    C:/Users/Jamie/workspace/epos_mcp/eposrunner.py
# PURPOSE: FastAPI execution server. This is Agent Zero's
#          Terminal arm. It receives commands from az_dispatch,
#          validates them, executes them, and logs receipts.
#          Replaces the unstubbed prior version with full
#          constitutional hardening.
# ARTICLE: Constitution v3.1, Article II, Rules 2, 4, 5
#          Constitution v3.1, Article X (AZ Contract)
# STARTS:  uvicorn eposrunner:app --host 127.0.0.1 --port 8001
# ============================================================

import sys
from pathlib import Path
from dotenv import load_dotenv

MIN_PYTHON = (3, 11)
if sys.version_info[:2] < MIN_PYTHON:
    raise EnvironmentError(f"Python 3.11+ required. Found: {sys.version_info[0]}.{sys.version_info[1]}")

load_dotenv(Path(__file__).parent / ".env")

import subprocess
import uuid
import logging
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import LOGS_DIR
from engine.command_validator import validate, CommandViolation

RUNNER_LOG = LOGS_DIR / "eposrunner.log"
logging.basicConfig(
    filename=str(RUNNER_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("eposrunner")

app = FastAPI(
    title="EPOS Runner",
    description="Constitutional Terminal Execution Arm for Agent Zero.",
    version="2.0.0"
)

TASK_CACHE: dict = {}


class Command(BaseModel):
    cmd: str


class TaskRequest(BaseModel):
    goal: str
    commands: List[Command]
    dryrun: bool = False


class TaskResult(BaseModel):
    taskid:      str
    goal:        str
    dryrun:      bool
    commands:    List[str]
    outputs:     List[str]
    returncodes: List[int]
    violations:  List[str] = []


def _run_command(cmd: str) -> tuple[int, str]:
    """Execute a validated shell command. Never silent."""
    logger.info(f"EXEC: {cmd}")
    try:
        completed = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        out = completed.stdout or completed.stderr or "(no output)"
        logger.info(f"OUTPUT [{completed.returncode}]: {out[:500]}")
        return completed.returncode, out
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {cmd}")
        return 124, f"TIMEOUT after 120s: {cmd}"
    except Exception as e:
        logger.error(f"EXECUTION ERROR: {cmd} → {e}")
        return 1, f"ERROR: {e}"


@app.get("/health")
def health():
    """Constitutional health check. Always honest."""
    logger.info("HEALTH CHECK: OK")
    return {"status": "ok", "runner": "eposrunner v2.0.0", "constitutional": True}


@app.post("/run-task", response_model=TaskResult)
def run_task(task: TaskRequest):
    """
    Execute a mission. Every step is validated, logged, and receipted.
    No silent failures. Status reflects actual work done.
    """
    taskid = str(uuid.uuid4())
    outputs, codes, violations = [], [], []
    logfile = LOGS_DIR / f"{taskid}.log"

    logger.info(f"TASK BEGIN: {taskid} | GOAL: {task.goal}")

    with logfile.open("w", encoding="utf-8") as f:
        f.write(f"TASK_ID: {taskid}\n")
        f.write(f"GOAL: {task.goal}\n")
        f.write(f"DRYRUN: {task.dryrun}\n\n")

        for c in task.commands:
            # Constitutional Validation (Article II, Rule 5)
            try:
                validate(c.cmd)
            except CommandViolation as e:
                violation_msg = str(e)
                violations.append(violation_msg)
                outputs.append(f"BLOCKED: {violation_msg}")
                codes.append(403)
                f.write(f"BLOCKED: {c.cmd}\n{violation_msg}\n")
                logger.warning(f"BLOCKED COMMAND: {c.cmd}")
                continue

            if task.dryrun:
                outputs.append(f"DRY RUN — Not executed: {c.cmd}")
                codes.append(0)
                f.write(f"DRY RUN: {c.cmd}\n")
            else:
                code, output = _run_command(c.cmd)
                outputs.append(output)
                codes.append(code)
                f.write(f"CMD: {c.cmd}\nCODE: {code}\nOUT: {output}\n\n")

    # Verify log was written (Article II, Rule 2)
    assert logfile.exists(), f"Log file not created for task {taskid}"

    result = TaskResult(
        taskid=taskid,
        goal=task.goal,
        dryrun=task.dryrun,
        commands=[c.cmd for c in task.commands],
        outputs=outputs,
        returncodes=codes,
        violations=violations
    )
    TASK_CACHE[taskid] = result
    logger.info(f"TASK COMPLETE: {taskid} | VIOLATIONS: {len(violations)}")
    return result


@app.get("/task/{taskid}", response_model=TaskResult)
def get_task(taskid: str):
    """Retrieve a task receipt by ID."""
    if taskid in TASK_CACHE:
        return TASK_CACHE[taskid]
    logpath = LOGS_DIR / f"{taskid}.log"
    if not logpath.exists():
        raise HTTPException(status_code=404, detail=f"Task {taskid} not found")
    text = logpath.read_text(encoding="utf-8")
    return TaskResult(
        taskid=taskid, goal="Recovered from log", dryrun=False,
        commands=[], outputs=[text], returncodes=[0]
    )
