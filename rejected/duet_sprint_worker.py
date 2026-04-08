from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from engine.duet_orchestrator import duet_build_contract, save_run

QUEUE = Path("queue/duet_sprints")
DONE  = Path("out/duet_runs")
QUEUE.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

def process_once(event_path: Path):
    event = json.loads(event_path.read_text(encoding="utf-8"))
    payload = event.get("payload", {})

    task = payload.get("task", "")
    cwd = payload.get("cwd", ".")
    os_hint = payload.get("os_hint", "gitbash")
    extra_context = payload.get("extra_context", "")

    contract = duet_build_contract(task=task, cwd=cwd, os_hint=os_hint, extra_context=extra_context)
    out_path = save_run(contract, out_dir=str(DONE))

    event["status"] = "completed"
    event["completed_at"] = datetime.now().isoformat(timespec="seconds")
    event["output_contract_path"] = str(out_path)

    # write a completion marker file alongside
    done_path = DONE / (event_path.stem + ".done.json")
    done_path.write_text(json.dumps(event, indent=2), encoding="utf-8")

    event_path.unlink(missing_ok=True)

def main():
    for p in sorted(QUEUE.glob("*.json")):
        process_once(p)

if __name__ == "__main__":
    main()
