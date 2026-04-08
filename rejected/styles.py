import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background-color: #050505;
            color: #E0E0E0;
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0A0A0A;
            border-right: 1px solid #333;
        }
        
        /* Cards */
        div[data-testid="metric-container"] {
            background-color: #111;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        /* Buttons */
        .stButton>button {
            background: linear-gradient(45deg, #764ba2, #667eea);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(118, 75, 162, 0.5);
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #fff;
            letter-spacing: -0.5px;
        }
        
        /* Success Message */
        .stSuccess {
            background-color: rgba(0, 255, 157, 0.1);
            border-left: 4px solid #00FF9D;
            color: #00FF9D;
        }
    </style>
    """, unsafe_allow_html=True)
