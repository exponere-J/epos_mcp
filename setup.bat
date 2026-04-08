@echo off
setlocal

REM Always run from the folder this script lives in
cd /d "%~dp0"

echo ==================================================
echo      NEXT STEPS(TM) - INITIAL SETUP WIZARD
echo ==================================================
echo.

echo [1/4] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not installed or not on PATH.
    echo Please install Python 3.10+ from python.org and try again.
    pause
    exit /b 1
)

echo.
echo [2/4] Creating virtual environment (.venv_epos)...
if not exist ".venv_epos" (
    python -m venv .venv_epos
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment in:
        echo   %cd%\.venv_epos
        pause
        exit /b 1
    )
) else (
    echo     - Existing venv found. Reusing.
)

echo.
echo [3/4] Installing core dependencies...
call ".venv_epos\Scripts\activate.bat"
pip install --upgrade pip >nul
pip install requests playwright rich questionary textblob streamlit >nul

echo.
echo     - Installing Playwright browsers (Chromium)...
playwright install chromium >nul 2>&1

echo.
echo [4/4] Setup complete.
echo.
echo Next:
echo   1) In Windows Explorer, double-click launch.bat
echo   2) Then use the menu to run Next Steps(TM) tools.
echo.
pause
endlocal
