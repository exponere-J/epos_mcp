import os
import sys
import json
from pathlib import Path

def setup_claude_config():
    print("🦅 EPOS BRIDGE: Initializing...")

    # 1. Detect Current EPOS Location
    current_dir = Path.cwd().resolve()
    server_script = current_dir / "epos_mcp_server.py"
    
    print(f"📍 Detected EPOS Root: {current_dir}")

    # 2. Detect Python Executable (Use the current venv)
    python_exe = sys.executable
    print(f"🐍 Using Python: {python_exe}")

    # 3. Locate Claude Config Directory (Windows/Mac/Linux)
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")
        claude_dir = Path(app_data) / "Claude"
    elif sys.platform == "darwin":
        claude_dir = Path.home() / "Library" / "Application Support" / "Claude"
    else:
        # Linux (Standard XDG)
        claude_dir = Path.home() / ".config" / "Claude"

    # Ensure directory exists
    if not claude_dir.exists():
        print(f"⚠️ Claude directory not found at {claude_dir}")
        print("   Creating it now...")
        claude_dir.mkdir(parents=True, exist_ok=True)

    config_file = claude_dir / "claude_desktop_config.json"

    # 4. Construct the Config Data
    config_data = {
        "mcpServers": {
            "epos": {
                "command": str(python_exe),
                "args": [str(server_script)],
                "env": {
                    "PYTHONPATH": str(current_dir),
                    "EPOS_ROOT": str(current_dir)
                }
            }
        }
    }

    # 5. Write the File
    try:
        # If file exists, read it to preserve other servers if any
        if config_file.exists():
            with open(config_file, 'r') as f:
                try:
                    existing = json.load(f)
                    if "mcpServers" in existing:
                        existing["mcpServers"].update(config_data["mcpServers"])
                        config_data = existing
                except json.JSONDecodeError:
                    pass # File was corrupt, overwriting

        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        print(f"✅ SUCCESS: Configuration written to:")
        print(f"   {config_file}")
        print("\n🔄 ACTION REQUIRED: Completely Quit and Restart Claude Desktop.")
        
    except Exception as e:
        print(f"❌ ERROR: Could not write config: {e}")

if __name__ == "__main__":
    setup_claude_config()
