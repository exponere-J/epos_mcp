import time
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List

# --- Config ---
SIDECAR_URL = "http://localhost:8010"
WORKER_ID = "analyst_beta_02"
CAPABILITIES = ["rules.synthesize", "shadow.predict"]

DATA_ROOT = Path("epos_hq/data/growth_engine")
DECISIONS_PATH = DATA_ROOT / "decisions/decisions.jsonl"
LEADS_PATH = DATA_ROOT / "leads/leads.jsonl"
RULES_PATH = DATA_ROOT / "rules/decision_graph.json"
REF_PATH = DATA_ROOT / "rules/latest_graph_ref.json"

# --- Logic ---

def _load_lead(lead_id: str) -> Dict[str, Any]:
    if not LEADS_PATH.exists(): return {}
    with LEADS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                lead = json.loads(line)
                if lead.get("lead_id") == lead_id: return lead
            except: continue
    return {}

def synthesize_rules(run_id: str, min_samples: int = 1) -> Dict[str, Any]:
    if not DECISIONS_PATH.exists(): return {"status": "no_data"}

    decisions = []
    with DECISIONS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): 
                try: decisions.append(json.loads(line))
                except: continue
    
    relevant = [d for d in decisions if d.get("run_id") == run_id]
    if not relevant: return {"status": "insufficient_data"}

    reasons = {}
    for d in relevant:
        if "reject" in d.get("outcome", "").lower():
            code = d.get("reason_code", "0")
            reasons[code] = reasons.get(code, 0) + 1

    graph = {
        "version": "2.0",
        "generated_at": time.time(),
        "policy": {
            "reject_budget_low": reasons.get("1", 0) > 0,
            "reject_bad_timing": reasons.get("2", 0) > 0,
            "reject_wrong_geo": reasons.get("3", 0) > 0
        }
    }

    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RULES_PATH.open("w", encoding="utf-8") as f: json.dump(graph, f, indent=2)
    with REF_PATH.open("w", encoding="utf-8") as f: json.dump({"run_id": run_id, "ref": str(RULES_PATH)}, f)
    
    return {"status": "success", "graph": graph}

def shadow_predict(lead_id: str, run_id: str) -> Dict[str, Any]:
    if not RULES_PATH.exists(): return {"prediction": "Unknown", "reason": "No Brain"}
    
    lead = _load_lead(lead_id)
    if not lead: return {"prediction": "Error", "reason": "Lead not found"}
    
    try:
        graph = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        policy = graph.get("policy", {})
    except: return {"prediction": "Error", "reason": "Corrupt Brain"}

    # Simulation Logic
    if policy.get("reject_budget_low"):
        return {"prediction": "Caution", "reason": "Active Rule: Low Budget Check"}
        
    return {"prediction": "Qualified", "confidence": 0.8, "reason": "No negative rules found"}

# --- Worker Loop ---

def work_loop():
    print(f"🧠 [ANALYST V2] Connected to {SIDECAR_URL}")
    while True:
        try:
            resp = httpx.post(f"{SIDECAR_URL}/mcp/request_task", json={"worker_id": WORKER_ID, "capabilities": CAPABILITIES}, timeout=5)
            
            if resp.status_code != 200:
                print(f"⚠️ Sidecar error: {resp.status_code}")
                time.sleep(5)
                continue

            task = resp.json()
            
            if task.get("status") != "no_work":
                print(f"⚡ [TASK] {task['type']}")
                
                if task["type"] == "rules.synthesize":
                    res = synthesize_rules(task["run_id"])
                    print(f"   ↳ Rule Created: {res.get('status')}")
                    
                elif task["type"] == "shadow.predict":
                    inputs = task.get("inputs", {})
                    res = shadow_predict(inputs.get("lead_id"), task["run_id"])
                    print(f"   ↳ 🔮 PREDICTION: {res['prediction']} ({res.get('reason')})")
            else:
                time.sleep(2)
        except Exception as e:
            print(f"⚠️ Connection Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    work_loop()

