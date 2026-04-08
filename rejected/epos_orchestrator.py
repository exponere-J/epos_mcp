import streamlit as st
import ollama
import json
import time
import threading
import pyttsx3
import speech_recognition as sr
from io import StringIO

# --- CONFIGURATION ---
st.set_page_config(page_title="EPOS Command v2", page_icon="🦅", layout="wide")

# --- CUSTOM CSS (The Sovereign Aesthetic) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Courier New', monospace; }
    .stTextInput > div > div > input { background-color: #1E1E1E; color: #00FF9D; border: 1px solid #333; }
    .stButton > button { background-color: #1E1E1E; color: #00FF9D; border: 1px solid #00FF9D; }
    .chat-message { padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; border-left: 4px solid #333; }
    .user-message { background-color: #111; border-left-color: #00FF9D; }
    .bot-message { background-color: #1A1A1A; border-left-color: #00BFFF; }
    .json-block { background-color: #000; padding: 10px; border-radius: 5px; font-size: 0.8em; color: #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- VOICE ENGINE INITIALIZATION ---
if "voice_engine" not in st.session_state:
    try:
        st.session_state.voice_engine = pyttsx3.init()
        st.session_state.voice_engine.setProperty('rate', 170)
    except:
        st.session_state.voice_engine = None

def speak_text(text):
    """Non-blocking text-to-speech"""
    if st.session_state.get("voice_active", False) and st.session_state.voice_engine:
        try:
            # Run in a thread to prevent UI freezing
            t = threading.Thread(target=lambda: (st.session_state.voice_engine.say(text), st.session_state.voice_engine.runAndWait()))
            t.start()
        except:
            pass

def listen_mic():
    """Capture audio from microphone"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("🎤 Listening...")
        try:
            audio = r.listen(source, timeout=5)
            text = r.recognize_google(audio)
            return text
        except:
            st.toast("❌ Audio capture failed.")
            return None

# --- SESSION STATE ---
if "history" not in st.session_state:
    st.session_state.history = []
if "system_prompt" not in st.session_state:
    # UPDATED PROMPT: Hybrid Natural Language + JSON
    st.session_state.system_prompt = """
    IDENTITY: You are EPOS (Phi-3-Sovereign).
    GOAL: Assist the operator with high-level reasoning and execution.
    
    OUTPUT FORMAT:
    1. First, respond in concise, natural language to the user.
    2. If a technical action is needed (code, file save, research), append a JSON block at the end wrapped in ```json ``` tags.
    
    EXAMPLE:
    "I will research that for you. Deploying the Scout agent now.
    ```json
    {"tool": "scout", "query": "latest AI trends"}
    ```"
    """

# --- SIDEBAR: SENSORS & INPUTS ---
st.sidebar.title("🦅 EPOS COMMAND")
st.sidebar.caption("Sovereign Operating System")

# 1. Voice Toggle
st.session_state.voice_active = st.sidebar.toggle("🔊 Voice Response", value=False)

# 2. File Ingestion (The Eyes)
uploaded_file = st.sidebar.file_uploader("📂 Ingest Context", type=['txt', 'md', 'py', 'json'])
file_context = ""
if uploaded_file is not None:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    file_content = stringio.read()
    file_context = f"\n\n[ATTACHED FILE: {uploaded_file.name}]\n{file_content[:4000]}" # Limit context
    st.sidebar.success(f"Ingested {uploaded_file.name}")

# 3. Quick Actions
st.sidebar.markdown("---")
if st.sidebar.button("🎤 PUSH TO TALK"):
    voice_input = listen_mic()
    if voice_input:
        st.session_state.prompt_input = voice_input # Queue for processing

# --- MAIN INTERFACE ---
st.title("Orchestrator V2")

# Display Chat
for chat in st.session_state.history:
    role_class = "user-message" if chat["role"] == "user" else "bot-message"
    with st.container():
        st.markdown(f"""
        <div class="chat-message {role_class}">
            <strong>{chat["role"].upper()}:</strong><br>{chat["content"]}
        </div>
        """, unsafe_allow_html=True)

# Input Handling
user_input = st.chat_input("Direct the System...")

# Check if we have voice input queued or typed input
final_input = st.session_state.get("prompt_input", None) or user_input

if final_input:
    # Clear queue
    if "prompt_input" in st.session_state: del st.session_state.prompt_input
    
    # 1. Append User Msg
    st.session_state.history.append({"role": "user", "content": final_input})
    
    # 2. Process
    with st.spinner("Processing..."):
        full_prompt = final_input + file_context
        
        try:
            response = ollama.chat(
                model='phi3:mini',
                messages=[
                    {'role': 'system', 'content': st.session_state.system_prompt},
                    {'role': 'user', 'content': full_prompt}
                ]
            )
            raw_reply = response['message']['content']
            
            # 3. Clean UI (Separate JSON from Text)
            display_text = raw_reply
            if "```json" in raw_reply:
                parts = raw_reply.split("```json")
                display_text = parts[0] # The natural language part
                # You could parse parts[1] here to actually trigger the python function
            
            st.session_state.history.append({"role": "epos", "content": raw_reply})
            
            # 4. Speak
            speak_text(display_text)
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Neural Link Severed: {e}")
