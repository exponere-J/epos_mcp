import streamlit as st
from streamlit_option_menu import option_menu
import json
import os
import subprocess
from datetime import datetime

st.set_page_config(page_title="EPOS Master Bridge", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    div.stButton > button { width: 100%; border-radius: 8px; }
    .beacon-box { padding: 10px; border-radius: 5px; text-align: center; color: white; margin-bottom: 10px; }
    .beacon-red { background-color: #ff4b4b; }
    .beacon-amber { background-color: #ffa421; }
    .beacon-green { background-color: #21c354; }
    .idea-box { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #ffa421; }
</style>
""", unsafe_allow_html=True)

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_void_entry(content, tags):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    entry = {
        "timestamp": timestamp,
        "content": content,
        "tags": tags,
        "status": "raw"
    }
    log_path = "content/ideas/void_log.json"
    data = load_json(log_path)
    if not isinstance(data, list):
        data = []
    data.insert(0, entry)
    save_json(log_path, data)
    return timestamp

def render_beacons():
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown('<div class="beacon-box beacon-green">🟢 SYSTEM: NOMINAL</div>', unsafe_allow_html=True)

    inbox_count = len(os.listdir("content/knowledge/inbox")) if os.path.exists("content/knowledge/inbox") else 0
    color = "beacon-red" if inbox_count > 5 else "beacon-green"
    msg = f"📥 INBOX: {inbox_count} ITEMS"
    with c2:
        st.markdown(f'<div class="beacon-box {color}">{msg}</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="beacon-box beacon-amber">⚠️ PGP: QUOTE PENDING</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="beacon-box beacon-green">🤖 PHI-4: STANDBY</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("🧬 EPOS")
    st.caption("Exponere Project Orchestration System")

    selected = option_menu(
        menu_title="Command Deck",
        options=["Dashboard", "Kanban", "Chronos", "Archivist", "StoryEngine", "The Void"],
        icons=["speedometer2", "kanban", "calendar-week", "archive", "megaphone", "lightbulb"],
        menu_icon="cast",
        default_index=0,
    )

    st.divider()
    st.info("🌊 Water Mind Active")
    st.caption("v1.2.0 | Sanford, FL")

if selected == "Dashboard":
    render_beacons()
    st.subheader("👋 Welcome back, Commander.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📢 Active Initiatives")
        st.info("**StoryBrand Layer:** Research phase complete. Blueprints for PGP & Exponere defined.")
        st.info("**Archivist:** External threads ready for ingestion via CLI or dedicated tools.")

    with col2:
        st.markdown("### 📊 Metrics")
        inbox = len(os.listdir("content/knowledge/inbox")) if os.path.exists("content/knowledge/inbox") else 0
        st.metric("Knowledge Base", f"{inbox} Files")
        st.metric("Ideas Captured", "—")
        st.metric("System Uptime", "N/A")

elif selected == "Kanban":
    render_beacons()
    st.subheader("📋 Orchestration Board")

    kanban_path = "content/projects/kanban.json"
    if not os.path.exists(kanban_path):
        save_json(kanban_path, {"todo": [], "doing": [], "done": []})

    data = load_json(kanban_path)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 🛑 To Do")
        new_task = st.text_input("New Task", key="new_task")
        if st.button("Add", key="add_task"):
            if new_task:
                data["todo"].append(new_task)
                save_json(kanban_path, data)
                st.experimental_rerun()
        for i, item in enumerate(data["todo"]):
            st.warning(item)
            if st.button("Start", key=f"start_{i}"):
                data["todo"].pop(i)
                data["doing"].append(item)
                save_json(kanban_path, data)
                st.experimental_rerun()

    with c2:
        st.markdown("### 🏃 Doing")
        for i, item in enumerate(data["doing"]):
            st.info(item)
            if st.button("Complete", key=f"done_{i}"):
                data["doing"].pop(i)
                data["done"].append(item)
                save_json(kanban_path, data)
                st.experimental_rerun()

    with c3:
        st.markdown("### ✅ Done")
        for item in data["done"]:
            st.success(f"~~{item}~~")
        if st.button("Clear Done"):
            data["done"] = []
            save_json(kanban_path, data)
            st.experimental_rerun()

elif selected == "Chronos":
    render_beacons()
    st.subheader("📅 Operational Calendar")

    agenda_path = "content/projects/agenda.json"
    if not os.path.exists(agenda_path):
        save_json(agenda_path, [])

    agenda = load_json(agenda_path)

    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("add_event"):
            st.markdown("#### Add Event")
            d = st.date_input("Date")
            e = st.text_input("Event Name")
            t = st.selectbox("Type", ["Ops", "Strategy", "Client", "Personal"])
            if st.form_submit_button("Add to Chronos"):
                agenda.append({"date": str(d), "event": e, "type": t})
                agenda = sorted(agenda, key=lambda x: x["date"])
                save_json(agenda_path, agenda)
                st.experimental_rerun()

    with c2:
        for item in agenda:
            icon = "🛠️" if item["type"] == "Ops" else "♟️" if item["type"] == "Strategy" else "💰"
            st.markdown(f"**{item['date']}** | {icon} {item['event']} `[{item['type']}]`")

elif selected == "Archivist":
    render_beacons()
    st.subheader("📥 Knowledge Ingestion (stub)")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.info("The Archivist will ingest external threads via CLI / dedicated tools.")
        st.caption("For now, manually drop files into content/knowledge/inbox.")

    with c2:
        st.markdown("#### 📚 Inbox")
        inbox = "content/knowledge/inbox"
        if os.path.exists(inbox):
            files = sorted(os.listdir(inbox), reverse=True)
            sel = st.selectbox("Select Thread", files) if files else None
            if sel:
                with open(os.path.join(inbox, sel), "r", encoding="utf-8") as f:
                    st.text_area("Content", f.read(), height=400)
        else:
            st.write("No inbox directory found.")

elif selected == "StoryEngine":
    render_beacons()
    st.subheader("📣 StoryBrand Architecture")

    tab1, tab2 = st.tabs(["PGP (Clean)", "Exponere (Sovereign)"])

    with tab1:
        st.markdown("### PGP Property Solutions")
        st.markdown("""
* **Hero:** Homeowner / Property Manager  
* **Villain:** Green Algae, HOA Fines, Liability  
* **Guide:** PGP (Specialist, Licensed, \"Eye for Detail\")  
* **Plan:** Quote → Wash → Shine  
* **Success:** Pride, Value, Compliance
        """)
        st.button("Generate PGP Ad (Simulated)")

    with tab2:
        st.markdown("### Exponere")
        st.markdown("""
* **Hero:** Visionary Business Owner  
* **Villain:** \"Jagged Edges\", Manual Chaos  
* **Guide:** Jamie (The Architect / Water Mind)  
* **Plan:** Audit → Automate → Scale  
* **Success:** Autonomy, Freedom
        """)
        st.button("Generate Exponere Pitch (Simulated)")

elif selected == "The Void":
    render_beacons()
    st.subheader("🧠 The Void")
    st.caption("Stream of consciousness capture.")

    col1, col2 = st.columns([2, 1])

    with col1:
        thought = st.text_area("What is on your mind?", height=200, placeholder="Type freely...")
        tags = st.multiselect("Tags", ["Strategy", "Content", "System", "Personal"], default=["Strategy"])
        if st.button("Crystallize Thought"):
            if thought:
                save_void_entry(thought, tags)
                st.success("Captured in the Void.")
                st.experimental_rerun()

    with col2:
        st.markdown("#### Recent Thoughts")
        log_path = "content/ideas/void_log.json"
        if os.path.exists(log_path):
            entries = load_json(log_path)
            for e in entries[:5]:
                st.markdown(f"""
                <div class="idea-box">
                    <small>{e.get('timestamp')}</small><br>
                    {e.get('content')}<br>
                    <small>🏷️ {', '.join(e.get('tags', []))}</small>
                </div>
                """, unsafe_allow_html=True)
