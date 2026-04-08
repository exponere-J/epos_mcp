@echo off
REM EPOS Daily Startup Script (Windows)
REM Launches all EPOS services in correct order

echo ╔════════════════════════════════════════════════════════╗
echo ║         EPOS STARTUP — Initializing Services          ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo ▶ Starting Ollama...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo ✓ Ollama already running
)

REM Launch Phi-3 Command Center
echo ▶ Launching Phi-3 Command Center...
echo    Opening browser at http://localhost:8501
echo.
python -m streamlit run phi3_command_center.py --server.port 8501
