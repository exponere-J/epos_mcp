import json
import time
from datetime import datetime
from pathlib import Path
import streamlit as st

LOG_PATH = Path("kernel/state/a2_context.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def _append(event: dict) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def render():
    st.header("🪰 A2: Fly-on-the-Wall")
    st.caption("Expansion Card // Passive Context Stream (Local-First)")

    st.markdown("**Output:** `kernel/state/a2_context.jsonl`  \n**Format:** JSONL  \n**Mode:** MVP sensor stub (hooks come next)")

    if "a2_active" not in st.session_state:
        st.session_state.a2_active = False

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("TOGGLE SENSOR"):
            st.session_state.a2_active = not st.session_state.a2_active
            st.toast("SENSOR ACTIVE" if st.session_state.a2_active else "SENSOR PAUSED")

    with col2:
        if st.button("WRITE TEST EVENT"):
            _append({
                "ts": datetime.utcnow().isoformat(),
                "type": "test",
                "note": "manual_event",
            })
            st.success("Wrote test event.")

    st.divider()

    if st.session_state.a2_active:
        st.info("Sensor running (UI loop). This simulates a passive stream.")
        # Simulated capture tick (you’ll replace this with Playwright listeners / clipboard hooks)
        _append({
            "ts": datetime.utcnow().isoformat(),
            "type": "tick",
            "url": "https://example.local/session",
            "signal": "dom_mutation_stub",
        })
        time.sleep(0.2)

    if LOG_PATH.exists():
        raw = LOG_PATH.read_text(encoding="utf-8")[-4000:]  # tail
        st.code(raw if raw.strip() else "(empty)", language="json")

        st.download_button(
            "Download A2 Logs",
            data=LOG_PATH.read_text(encoding="utf-8"),
            file_name="a2_context.jsonl"
        )
