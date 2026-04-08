import json
import time
import uuid
import httpx
import streamlit as st
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- Configuration ---
SIDECAR_URL = "http://localhost:8010"
DATA_ROOT = Path("epos_hq/data/growth_engine")

# Paths (Definitions that were missing)
LEADS_PATH = DATA_ROOT / "leads/leads.jsonl"
DECISIONS_PATH = DATA_ROOT / "decisions/decisions.jsonl"
RULES_REF_PATH = DATA_ROOT / "rules/latest_graph_ref.json"

# Ensure directories exist
LEADS_PATH.parent.mkdir(parents=True, exist_ok=True)
DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
RULES_REF_PATH.parent.mkdir(parents=True, exist_ok=True)

WHY_OPTIONS = {
    "1": "Too small (<$5k)",
    "2": "Bad timing (Not ready)",
    "3": "Wrong geo (Outside service area)",
    "4": "Intuition (Voice Memo Required)"
}

# --- Helpers ---

def _now() -> float:
    return time.time()

def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists(): return []
    data = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): 
                try: data.append(json.loads(line))
                except: continue
    return data

def _publish_event(topic: str, payload: Dict[str, Any]) -> None:
    try:
        httpx.post(f"{SIDECAR_URL}/mcp/publish_event", 
                   json={"topic": topic, "payload": payload, "source": "ui.lead_review"}, 
                   timeout=1.0)
    except: pass

def _submit_task(task_type: str, inputs: Dict[str, Any], run_id: str) -> None:
    try:
        httpx.post(f"{SIDECAR_URL}/mcp/submit_task", json={
            "type": task_type,
            "run_id": run_id,
            "required_capability": task_type,
            "inputs": inputs
        }, timeout=1.0)
    except: pass

def _unreviewed_leads(run_id: str) -> List[Dict[str, Any]]:
    leads = _read_jsonl(LEADS_PATH)
    decisions = _read_jsonl(DECISIONS_PATH)
    decided_ids = {d.get("lead_id") for d in decisions if d.get("run_id") == run_id}
    return [l for l in leads if l.get("run_id") == run_id and l.get("lead_id") not in decided_ids]

# --- Main Page ---

def page():
    st.title("🧠 Growth Engine: Cognitive Capture")
    
    # Session State
    if "run_id" not in st.session_state: st.session_state["run_id"] = "node_alpha"

    # --- Sidebar Operations ---
    st.sidebar.title("⚙️ Operations")
    run_id = st.sidebar.text_input("Active Node ID", value=st.session_state["run_id"])
    st.session_state["run_id"] = run_id
    
    if st.sidebar.button("🧠 Synthesize Rules"):
        _submit_task("rules.synthesize", {"min_samples": 1}, run_id)
        st.sidebar.success("Synthesis task queued!")

    if st.sidebar.button("🔮 Test Shadow Mode"):
        leads = _unreviewed_leads(run_id)
        if leads:
            _submit_task("shadow.predict", {"lead_id": leads[0]["lead_id"]}, run_id)
            st.sidebar.success(f"Predicting for {leads[0].get('company')}")
        else:
            st.sidebar.warning("Queue empty.")

    # Show Model Status
    if RULES_REF_PATH.exists():
        try:
            ref = json.loads(RULES_REF_PATH.read_text())
            st.sidebar.info(f"Model Active: {ref.get('run_id', 'Unknown')}")
        except: pass

    # --- Main Interface ---
    tab1, tab2 = st.tabs(["📥 Manual Intake", "👀 Review Queue"])

    with tab1:
        with st.form("intake", clear_on_submit=True):
            col1, col2 = st.columns(2)
            company = col1.text_input("Company Name")
            budget = col2.text_input("Est. Budget")
            source = st.selectbox("Source", ["Inbound", "Referral", "Cold Outbound"])
            raw_text = st.text_area("Raw Context")
            
            if st.form_submit_button("Ingest Lead"):
                lead_id = str(uuid.uuid4())[:8]
                lead = {
                    "lead_id": lead_id, "run_id": run_id, 
                    "company": company or "Unknown", "budget": budget, 
                    "source": source, "context": raw_text, "timestamp": _now()
                }
                _append_jsonl(LEADS_PATH, lead)
                _publish_event("lead.ingested", lead)
                st.success(f"Lead {lead_id} ingested.")

    with tab2:
        queue = _unreviewed_leads(run_id)
        if not queue:
            st.info("Queue empty. Good job.")
        else:
            lead = queue[0]
            st.subheader(f"Evaluate: {lead.get('company')}")
            st.json(lead)
            
            with st.form("decision"):
                outcome = st.radio("Decision", ["Qualified", "Rejected"], horizontal=True)
                reason = st.radio("Why?", list(WHY_OPTIONS.keys()), format_func=lambda x: f"{x}. {WHY_OPTIONS[x]}")
                
                if st.form_submit_button("Lock Decision 🔒"):
                    decision_data = {
                        "lead_id": lead["lead_id"], "run_id": run_id,
                        "outcome": outcome, "reason_code": reason,
                        "reason_text": WHY_OPTIONS[reason], "timestamp": _now()
                    }
                    _append_jsonl(DECISIONS_PATH, decision_data)
                    _publish_event("decision.captured", decision_data)
                    st.success("Decision mapped.")
                    time.sleep(0.5)
                    st.rerun()

if __name__ == "__main__":
    page()

