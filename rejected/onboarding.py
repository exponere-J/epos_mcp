import streamlit as st
import json
from pathlib import Path

def save_profile(data):
    # Save to disk (mocked for now)
    st.session_state["profile"] = data
    st.success("Identity Kernel Crystallized.")

def render_onboarding():
    st.title("🦅 EPOS Initiation")
    st.markdown("### Establishing Sovereign Profile")
    
    with st.form("identity_survey"):
        st.write(" **1. The Mantle**")
        st.caption("What is the one sentence that defines your mission?")
        mantle = st.text_input("I am...", placeholder="The architect of Stories for Zayne.")
        
        st.write("---")
        st.write("**2. The Archetypes**")
        col1, col2 = st.columns(2)
        with col1:
            primary = st.selectbox("Primary Mode (Default State)", ["Sovereign (Strategy)", "Warrior (Execution)", "Lover (Connection)", "Magician (Innovation)"])
        with col2:
            secondary = st.selectbox("Secondary Mode (Stress Response)", ["Sovereign", "Warrior", "Lover", "Magician"])
            
        st.write("---")
        st.write("**3. The Voice**")
        st.caption("How should the AI speak for you?")
        voice = st.text_area("Describe your tone", "Warm, empathetic, authoritative, visual.")
        
        submitted = st.form_submit_button("Crystallize Identity")
        
        if submitted:
            profile = {
                "mantle": mantle,
                "primary": primary,
                "secondary": secondary,
                "voice": voice
            }
            save_profile(profile)
            st.rerun()
