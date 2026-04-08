import json
from pathlib import Path

STATE_FILE = Path("epos_hq/data/state.json")
OUTPUT_DIR = Path("epos_hq/data/artifacts/content_lab")

def export():
    if not STATE_FILE.exists():
        print("❌ No state found.")
        return

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for tid, task in state["tasks"].items():
        if task["status"] == "COMPLETED" and task["output"]:
            # Sanitize filename from intent
            safe_name = "".join([c if c.isalnum() else "_" for c in task["intent"]])[:30]
            filename = OUTPUT_DIR / f"{safe_name}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(task["output"])
            
            print(f"💾 Saved: {filename}")

if __name__ == "__main__":
    export()
