@echo off
setlocal
cd /d "%~dp0"

echo [Next Steps] Activating environment...
if exist ".venv_epos\Scripts\activate.bat" (
    call .venv_epos\Scripts\activate.bat
) else (
    python -m venv .venv_epos
    call .venv_epos\Scripts\activate.bat
)

echo [Next Steps] Installing Streamlit and Playwright (first run may take a minute)...
pip install -q streamlit playwright requests

playwright install chromium

echo [Next Steps] Launching GUI...
streamlit run tools\next_steps\gui\suite_ui.py
