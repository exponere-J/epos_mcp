import time
import json
import httpx
from pathlib import Path

# --- Config ---
SIDECAR_URL = "http://localhost:8010"
DAG_PATH = Path("epos_hq/growth_engine/diagnostic_sprint.dag.json")

def load_dag():
    if not DAG_PATH.exists():
        print("❌ DAG file not found.")
        return None
    return json.loads(DAG_PATH.read_text())

def run_day(day_number: int, run_id: str):
    dag = load_dag()
    if not dag: return

    print(f"📅 [SPRINT RUNNER] Initiating Day {day_number} for {run_id}...")
    day_plan = next((d for d in dag.get("schedule", []) if d["day"] == day_number), None)
    
    if not day_plan:
        print(f"⚠️ No specific plan for Day {day_number}. Standing by.")
        return

    print(f"   Phase: {day_plan.get('phase')}")
    
    for task_def in day_plan.get("tasks", []):
        try:
            print(f"   » Queuing: {task_def['type']}")
            httpx.post(f"{SIDECAR_URL}/mcp/submit_task", json={
                "type": task_def["type"],
                "run_id": run_id,
                "required_capability": task_def["type"].split(".")[0],
                "inputs": task_def.get("inputs", {})
            }, timeout=2)
        except Exception as e:
            print(f"   ❌ Failed to queue {task_def['type']}: {e}")
    
    print("✅ Day execution cycle initiated.")

if __name__ == "__main__":
    # Test Run: Execute Day 1 immediately
    run_day(1, "node_alpha")
