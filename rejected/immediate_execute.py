#!/usr/bin/env python3
"""EPOS Bootstrap for Agent Zero Integration."""

import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
GREEN = '\033[92m'
RESET = '\033[0m'

print(f"{GREEN}EPOS + Agent Zero Bootstrap{RESET}")
print(f"Root: {ROOT}")

# 1. Check prerequisites
print("\n1. Prerequisites:")
if sys.version_info < (3, 10):
    print("❌ Python 3.10+ required")
    sys.exit(1)

if not (ROOT / "engine").exists():
    print("❌ engine/ directory missing")
    sys.exit(1)

az_path = Path.home() / "workspace" / "agent-zero"
if not az_path.exists():
    print("❌ agent-zero not found at ~/workspace/agent-zero")
    sys.exit(1)

print("✅ Prerequisites OK")

# 2. Create directories
dirs = ["api", "ops/logs/orchestrator", "ops/logs/agent_zero", "content/lab"]
for d in dirs:
    (ROOT / d).mkdir(parents=True, exist_ok=True)
print("✅ Directories created")

# 3. Create .env
env_content = """# EPOS + Agent Zero
EPOS_API_TOKEN=local-dev-token
AGENT_ZERO_PATH=/c/Users/Jamie/workspace/agent-zero
OLLAMA_URL=http://localhost:11434
"""
(ROOT / ".env").write_text(env_content)
print("✅ .env created")

# 4. Test Docker
try:
    r = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        print("✅ Docker healthy")
    else:
        print("⚠️ Docker warning:", r.stderr.strip())
except:
    print("⚠️ Docker test failed")

print("\n🎉 BOOTSTRAP COMPLETE")
print("\nNext (copy these files):")
print("1. engine/agent_zero_bridge.py")
print("2. api/epos_api.py")
print("3. python -m pip install fastapi uvicorn")
print("4. python -m uvicorn api.epos_api:app --port 8001")
