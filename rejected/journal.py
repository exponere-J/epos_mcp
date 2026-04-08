import streamlit as st
from datetime import datetime
import json
from pathlib import Path

JOURNAL_DIR = Path("epos_hq/data/journal")
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

def save_entry(text, mood, tags):
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "mood": mood,
        "tags": tags
    }
    with open(JOURNAL_DIR / filename, "w") as f:
        json.dump(entry, f, indent=2)
    st.success("Entry Logged.")

def render_journal():
    st.title("📓 Sovereign Journal")
    
    with st.form("daily_log"):
        mood = st.select_slider("Energy Level", options=["Drained", "Low", "Neutral", "High", "Sovereign"])
        text = st.text_area("Reflection", height=150, placeholder="What did you build today? Where was the friction?")
        tags = st.multiselect("Tags", ["Strategy", "Code", "Family", "Health", "Crisis"])
        
        if st.form_submit_button("Log Entry"):
            save_entry(text, mood, tags)
            
    # History View
    st.subheader("Recent Entries")
    files = sorted(JOURNAL_DIR.glob("*.json"), reverse=True)[:5]
    for f in files:
        data = json.loads(f.read_text())
        with st.expander(f"{data['timestamp'][:16]} - {data['mood']}"):
            st.write(data['text'])
            st.caption(f"Tags: {', '.join(data['tags'])}")
