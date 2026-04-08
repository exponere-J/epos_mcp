@echo off
setlocal

REM Always run from the folder this script lives in
cd /d "%~dp0"

title Next Steps(TM) Launcher

if exist ".venv_epos\Scripts\activate.bat" (
    call ".venv_epos\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    REM Fallback if an older venv exists
    call ".venv\Scripts\activate.bat"
) else (
    echo [ERROR] No virtual environment found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

python tools\next_steps\unified_launcher.py
endlocal
