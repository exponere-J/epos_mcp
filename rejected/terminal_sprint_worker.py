import json
from pathlib import Path
from datetime import datetime

from .terminal_sprint_planner import propose_terminal_sprint
from .terminal_exec import run_commands

QUEUE = Path("queue/terminal_sprints")
DONE  = Path("out/terminal_sprints")
QUEUE.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

def process_once(event_path: Path):
    event = json.loads(event_path.read_text(encoding="utf-8"))

    payload = event.get("payload", {})
    task = payload.get("task", "")
    cwd = payload.get("cwd", ".")
    os_hint = payload.get("os_hint", "gitbash")

    plan = propose_terminal_sprint(task=task, cwd=cwd, os_hint=os_hint, retries=1)
    exec_log = run_commands(plan.get("commands", []), cwd=cwd)

    ok = bool(exec_log["results"]) and exec_log["results"][-1]["returncode"] == 0
    event["status"] = "completed" if ok else "error"
    event["execution"] = {
        "planned_at": datetime.now().isoformat(timespec="seconds"),
        "plan": plan,
        "exec": exec_log,
    }

    out_path = DONE / event_path.name
    out_path.write_text(json.dumps(event, indent=2), encoding="utf-8")
    event_path.unlink(missing_ok=True)

def main():
    for p in sorted(QUEUE.glob("*.json")):
        process_once(p)

if __name__ == "__main__":
    main()
