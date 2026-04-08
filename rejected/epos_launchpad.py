import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Setup Colors for Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(status, message):
    if status == "SUCCESS":
        print(f"{GREEN}[✓] {message}{RESET}")
    elif status == "ERROR":
        print(f"{RED}[X] {message}{RESET}")
    elif status == "INFO":
        print(f"{YELLOW}[i] {message}{RESET}")

def get_claude_path():
    """Find Claude executable on Windows"""
    user_home = Path.home()
    # Common installation paths for Claude
    paths = [
        user_home / "AppData" / "Local" / "AnthropicClaude" / "Claude.exe",
        user_home / "AppData" / "Local" / "Programs" / "Claude" / "Claude.exe"
    ]
    for p in paths:
        if p.exists():
            return p
    return None

def check_ollama():
    """Ensure Ollama is running and Phi-3 is loaded"""
    try:
        import ollama
        log("INFO", "Pinging Neural Core (Ollama)...")
        
        # 1. Check Model List (Robust Method)
        try:
            list_response = ollama.list()
            # Handle different API response structures
            models = list_response.get('models', [])
            
            # Check for phi3 in either 'name' or 'model' keys
            has_phi3 = False
            for m in models:
                name = m.get('name', m.get('model', ''))
                if 'phi3:mini' in name:
                    has_phi3 = True
                    break
            
            if not has_phi3:
                log("INFO", "Phi-3 Mini not found in list. Attempting to pull...")
                subprocess.run(["ollama", "pull", "phi3:mini"], check=True)
                
        except Exception as e:
            log("INFO", f"Model check skipped ({e}), proceeding to direct inference test...")

        # 2. Test Inference (The Real Test)
        log("INFO", "Requesting Pre-Flight Check from Phi-3...")
        response = ollama.chat(model='phi3:mini', messages=[{
            'role': 'user',
            'content': 'Reply with JSON: {"status": "ONLINE"}'
        }])
        
        content = response['message']['content']
        log("SUCCESS", f"Phi-3 Engineer reports: {content}")
        return True

    except ImportError:
        log("ERROR", "Ollama library not installed. Run: pip install ollama")
        return False
    except Exception as e:
        log("ERROR", f"Connection to Brain failed: {e}")
        log("INFO", "TROUBLESHOOTING: Ensure Ollama is running in the system tray.")
        return False

def check_config():
    """Verify MCP Config exists"""
    app_data = os.getenv("APPDATA")
    config_path = Path(app_data) / "Claude" / "claude_desktop_config.json"
    
    if config_path.exists():
        log("SUCCESS", "MCP Bridge Configuration found.")
        return True
    else:
        log("ERROR", "Config missing. Run 'bootstrap_bridge.py' first.")
        return False

def launch_sequence():
    print(f"\n{YELLOW}🦅 EPOS LAUNCH SEQUENCE INITIATED{RESET}")
    print("="*40)
    
    # 1. Check Config
    if not check_config(): return

    # 2. Check Intelligence
    if not check_ollama(): return

    # 3. Locate Claude
    claude_exe = get_claude_path()
    if not claude_exe:
        log("ERROR", "Claude Desktop executable not found in standard paths.")
        print("Please open Claude Desktop manually.")
        return

    # 4. Launch
    print("="*40)
    log("SUCCESS", "ALL SYSTEMS GREEN.")
    log("INFO", "Phi-3 is delegating start command to Huntsman...")
    time.sleep(1)
    
    try:
        subprocess.Popen([str(claude_exe)])
        log("SUCCESS", "Claude Desktop Launched.")
        print(f"\n{GREEN}💡 INSTRUCTION:{RESET} When Claude opens, look for the 🔌 icon and type: 'Check system status'")
    except Exception as e:
        log("ERROR", f"Failed to launch process: {e}")

if __name__ == "__main__":
    launch_sequence()
