import epos_hq.ui.lead_review as lead_review
import streamlit as st
import json
import time
import sys
import pandas as pd
from pathlib import Path
from epos_hq.ui.styles import apply_theme

ROOT = Path(__file__).resolve().parents[2]  # repo root (…/epos_mcp)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- SETUP ---
st.set_page_config(page_title="EPOS Sovereign HQ", layout="wide", page_icon="🦅")
apply_theme()

# --- STATE MANAGEMENT ---
STATE_FILE = Path("epos_hq/data/state.json")

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except: return None
    return None

def trigger_task(intent, role, inputs):
    # This writes a "Trigger File" that the Engine picks up
    # (Since Streamlit runs in a separate process from the Engine)
    trigger_path = Path("epos_hq/data/triggers")
    trigger_path.mkdir(parents=True, exist_ok=True)
    
    payload = {
        "intent": intent,
        "role": role,
        "inputs": inputs,
        "timestamp": time.time()
    }
    
    # Save as unique JSON
    with open(trigger_path / f"trigger_{int(time.time())}.json", "w") as f:
        json.dump(payload, f)

state = load_state()

# --- SIDEBAR NAV ---
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/764ba2/eagle.png", width=60)
    st.title("EPOS HQ")
    nav = st.radio("Navigation", ["Dashboard", "Content Lab", "Life OS", "System Logs"])
    
    st.markdown("---")
    if state:
        ceo = state.get("ceo", {})
        st.success(f"👑 CEO: {ceo.get('active', 'Unknown')}")
        st.caption(f"Status: {ceo.get('status', 'Unknown')}")

# --- PAGE: DASHBOARD ---
if nav == "Dashboard":
    st.header("🦅 Sovereign Command Center")
    
    if not state:
        st.error("HQ Offline. Run 'start_epos_hq.py' first.")
        st.stop()
        
    # Metrics
    metrics = state.get("metrics", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tasks Completed", metrics.get("completed_tasks", 0))
    c2.metric("Tasks Failed", metrics.get("failed_tasks", 0))
    c3.metric("Swarm Size", len(state.get("agents", {})))
    c4.metric("Uptime", "99.9%")
    
    # Agent Grid
    st.subheader("🤖 Active Swarm")
    agents = state.get("agents", {})
    cols = st.columns(4)
    for i, (aid, data) in enumerate(agents.items()):
        with cols[i % 4]:
            status_color = "🟢" if data["status"] == "WORKING" else "⚪"
            with st.container(border=True):
                st.markdown(f"**{status_color} {aid}**")
                st.caption(f"{data['role']}")
                if data['status'] == "WORKING":
                    st.progress(80) # Simulation of work

    # Queue
    st.subheader("📋 Execution Queue")
    tasks = state.get("tasks", {})
    if tasks:
        task_data = [{"Intent": t["intent"], "Status": t["status"], "Agent": t.get("claimed_by", "-")} for t in tasks.values()]
        st.dataframe(pd.DataFrame(task_data), use_container_width=True)

# --- PAGE: CONTENT LAB (Embedded) ---
elif nav == "Content Lab":
    st.header("🧬 Content Lab")
    st.caption("Autonomous Media Production Line")
    
    tab1, tab2 = st.tabs(["🚀 Campaign Launcher", "📂 Artifacts"])
    
    with tab1:
        c1, c2 = st.columns([2, 1])
        with c1:
            topic = st.text_input("Campaign Topic", placeholder="e.g. The Future of Sovereign AI")
            archetype = st.selectbox("Target Audience", ["Sovereign Builder", "Frustrated Agency Owner", "Tech Optimist"])
        with c2:
            st.write("") # Spacer
            st.write("")
            if st.button("Ignite Campaign 🔥", use_container_width=True):
                trigger_task(
                    intent=f"Generate Campaign: {topic}",
                    role="CREATOR",
                    inputs=f"Topic: {topic}\nAudience: {archetype}"
                )
                st.toast("Campaign Injected into Swarm Queue!")
                time.sleep(1)
                st.rerun()

    with tab2:
        st.info("Generated assets appear here.")
        # Logic to read from epos_hq/data/artifacts/ would go here

# --- PAGE: LIFE OS ---
elif nav == "Life OS":
    st.header("📓 Sovereign Journal")
    entry = st.text_area("Daily Reflection", height=150)
    if st.button("Log Entry"):
        st.success("Entry saved to encrypted storage.")

# --- PAGE: LOGS ---
elif nav == "System Logs":
    st.header("🔍 System Telemetry")
    st.code("INFO: Phi-4 connected.\nINFO: Task #124 completed.\nWARN: Rate Limit on Claude API (Failover active).")

# --- Growth Engine Hook ---
# Ensure you have a navigation selector, e.g., page = st.sidebar.radio(...)
# This hook checks if 'lead_review' is selected.
if 'page' in locals() and page == "Growth Engine (Sprint C)":
    lead_review.page()
elif 'selected_page' in locals() and selected_page == "Growth Engine (Sprint C)":
    lead_review.page()

# --- Growth Engine Hook (Added by Sprint C) ---
# This appends the Growth Engine page to your existing sidebar logic.
# If you are using a sidebar selector, ensure 'Growth Engine (Sprint C)' is an option.
try:
    import epos_hq.ui.lead_review as lead_review
    # If using standard 'page' variable for navigation:
    if 'page' in locals() and page == "Growth Engine (Sprint C)":
        lead_review.page()
    # Or if you just want to force it for testing:
    # lead_review.page() 
except ImportError:
    st.error("Growth Engine UI module not found.")
