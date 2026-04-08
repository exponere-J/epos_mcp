import subprocess
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

# --- Config ---
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "ops" / "runner_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="EPOS Runner",
    description="Local execution arm for EPOS / Orchestrator bridge.",
    version="1.0.0",
)

class Command(BaseModel):
    cmd: str

class TaskRequest(BaseModel):
    goal: str
    commands: List[Command]
    dry_run: bool = False

class TaskResult(BaseModel):
    task_id: str
    goal: str
    dry_run: bool
    commands: List[str]
    outputs: List[str]
    return_codes: List[int]

TASK_CACHE: dict[str, TaskResult] = {}

def run_command(cmd: str) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    out = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, out

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run-task", response_model=TaskResult)
def run_task(task: TaskRequest):
    task_id = str(uuid.uuid4())
    outputs: list[str] = []
    codes: list[int] = []

    log_file = LOG_DIR / f"{task_id}.log"
    with log_file.open("w", encoding="utf-8") as f:
        f.write(f"GOAL: {task.goal}\n")
        f.write(f"DRY_RUN: {task.dry_run}\n\n")

        for c in task.commands:
            f.write(f"$ {c.cmd}\n")
            if task.dry_run:
                outputs.append("[DRY RUN] Not executed.")
                codes.append(0)
                f.write("[DRY RUN] Not executed.\n\n")
            else:
                code, output = run_command(c.cmd)
                outputs.append(output)
                codes.append(code)
                f.write(output + "\n\n")

    result = TaskResult(
        task_id=task_id,
        goal=task.goal,
        dry_run=task.dry_run,
        commands=[c.cmd for c in task.commands],
        outputs=outputs,
        return_codes=codes,
    )
    TASK_CACHE[task_id] = result
    return result
