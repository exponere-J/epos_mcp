import json
from pathlib import Path
from datetime import datetime

from .intent_chain import analyze_intent
from .software_engineer_agent import generate_engineering_output
from .patcher import apply_unified_diff
from .command_runner import run_commands

QUEUE = Path("queue/software_sprints")
DONE  = Path("out/software_sprints")

QUEUE.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

def process_once(event_path: Path):
    event = json.loads(event_path.read_text(encoding="utf-8"))
    payload = event.get("payload", {})

    task = payload.get("task", "")
    cwd = payload.get("cwd", ".")
    extra_context = payload.get("context", "")

    intent = analyze_intent(task, extra_context)

    engineering = generate_engineering_output(
        task=task,
        cwd=cwd,
        intent_category=intent.category,
        extra_context=extra_context
    )

    patch_result = apply_unified_diff(
        engineering.get("patch_unified_diff", ""),
        cwd=cwd
    )

    command_result = run_commands(
        engineering.get("commands", []),
        cwd=cwd
    )

    ok = patch_result.get("ok", False) and command_result.get("ok", False)

    event["status"] = "completed" if ok else "error"
    event["execution"] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "intent": intent.__dict__,
        "engineering": engineering,
        "patch_result": patch_result,
        "command_result": command_result
    }

    out_path = DONE / event_path.name
    out_path.write_text(json.dumps(event, indent=2), encoding="utf-8")
    event_path.unlink(missing_ok=True)

def main():
    for p in sorted(QUEUE.glob("*.json")):
        process_once(p)

if __name__ == "__main__":
    main()
