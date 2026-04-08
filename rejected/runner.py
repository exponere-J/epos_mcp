import os
import json
import uuid
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Optional Playwright (do NOT hard-fail boot)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ---------------------------------------------------------------------
# CONFIG LOADING
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RUNNER_TOKEN = os.getenv("RUNNER_TOKEN", "change-me-immediately")

ALLOWED_COMMANDS = {
    cmd.strip()
    for cmd in os.getenv("ALLOWED_COMMANDS", "git,python,pip").split(",")
    if cmd.strip()
}

ALLOWED_WORKDIRS = {
    str(BASE_DIR)
}

# ---------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------

app = FastAPI(
    title="EPOS Huntsman Runner",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # OK for dev; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------

class CommandRequest(BaseModel):
    command: str = Field(..., example="python --version")
    workdir: Optional[str] = None


class CommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    snapshot_path: Optional[str] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _validate_token(token: Optional[str]):
    if token != RUNNER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid runner token")


def _validate_command(cmd: str):
    parsed = shlex.split(cmd)
    if not parsed:
        raise HTTPException(status_code=400, detail="Empty command")

    if parsed[0] not in ALLOWED_COMMANDS:
        raise HTTPException(
            status_code=403,
            detail=f"Command '{parsed[0]}' not allowed"
        )


def _validate_workdir(workdir: Optional[str]) -> str:
    wd = workdir or str(BASE_DIR)
    wd = str(Path(wd).resolve())

    if not any(wd.startswith(allowed) for allowed in ALLOWED_WORKDIRS):
        raise HTTPException(status_code=403, detail="Working directory not allowed")

    return wd


# ---------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "playwright_available": PLAYWRIGHT_AVAILABLE,
    }


@app.post("/run", response_model=CommandResponse)
def run_command(
    req: CommandRequest,
    x_runner_token: Optional[str] = Header(None),
):
    _validate_token(x_runner_token)
    _validate_command(req.command)
    workdir = _validate_workdir(req.workdir)

    proc = subprocess.run(
        req.command,
        shell=True,
        cwd=workdir,
        capture_output=True,
        text=True,
    )

    return CommandResponse(
        stdout=proc.stdout,
        stderr=proc.stderr,
        exit_code=proc.returncode,
        notes="Executed via EPOS Huntsman Runner",
    )


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "runner.runner:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
