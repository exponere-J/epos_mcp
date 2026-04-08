"""Agent Zero Bridge - EPOS Integration Layer"""
from __future__ import annotations

import json
import subprocess
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows Git Bash path handling
if os.path.basename(os.getcwd()) == "epos_mcp":
    BASE_DIR = Path.cwd()
else:
    BASE_DIR = Path.cwd()
    if not (BASE_DIR / "agents").exists():
        BASE_DIR = BASE_DIR.parent / "epos_mcp"

# Agent Zero is sibling to epos_mcp
AGENT_ZERO_PATH = BASE_DIR.parent / "agent-zero"

# Detect Windows vs Unix venv
if sys.platform == "win32" or "MINGW" in sys.platform:
    VENV_PYTHON = AGENT_ZERO_PATH / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = AGENT_ZERO_PATH / ".venv" / "bin" / "python"


class AgentZeroBridge:
    """Bridge between EPOS and Agent Zero for local + browser operations."""
    
    def __init__(self, workspace: Optional[str] = None):
        self.workspace = Path(workspace).resolve() if workspace else BASE_DIR.parent.resolve()
        self.agent_zero_path = AGENT_ZERO_PATH.resolve()
        self.venv_python = VENV_PYTHON.resolve()
        
        # Paths
        self.task_queue = BASE_DIR / "queue" / "agent_zero"
        self.task_queue.mkdir(parents=True, exist_ok=True)
        
        self.log_dir = BASE_DIR / "ops" / "logs" / "agent_zero"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def _log(self, level: str, message: str, metadata: Optional[Dict] = None):
        """Write structured log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "metadata": metadata or {}
        }
        
        log_file = self.log_dir / f"bridge_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        try:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[{level}] {message}", file=sys.stderr)
    
    def execute_task(
        self,
        task: str,
        mode: str = "local",
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Execute task via Agent Zero."""
        
        task_id = f"az_{int(time.time())}_{mode}"
        
        payload = {
            "task_id": task_id,
            "task": task,
            "mode": mode,
            "workspace": str(self.workspace),
            "context": context or {},
            "config": {"timeout": timeout},
            "created_at": datetime.now().isoformat()
        }
        
        self._log("INFO", f"Task {mode}", {"task_id": task_id, "task": task[:80]})
        
        # Write task
        task_file = self.task_queue / f"{task_id}.json"
        try:
            task_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            return {"ok": False, "task_id": task_id, "error": str(e)}
        
        try:
            # Build command
            cmd = [
                str(self.venv_python),
                str(self.agent_zero_path / "agent.py"),
                "--task", task,
                "--mode", mode,
            ]
            
            # Windows needs shell=True
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.agent_zero_path),
                shell=(sys.platform == "win32" or "MINGW" in sys.platform)
            )
            
            result = {
                "ok": proc.returncode == 0,
                "task_id": task_id,
                "mode": mode,
                "stdout": proc.stdout[:2000],
                "stderr": proc.stderr[:2000],
                "returncode": proc.returncode,
            }
            
            # Try parse output
            try:
                output = json.loads(proc.stdout)
                result["agent_zero_output"] = output
                result["extracted_content"] = output.get("content", "")
            except json.JSONDecodeError:
                result["raw_output"] = proc.stdout
                
            self._log("INFO" if result["ok"] else "ERROR", f"Task complete", {"task_id": task_id})
            return result
            
        except subprocess.TimeoutExpired:
            self._log("ERROR", f"Timeout {timeout}s", {"task_id": task_id})
            return {"ok": False, "task_id": task_id, "error": f"Timeout after {timeout}s"}
        except Exception as e:
            self._log("ERROR", f"Error: {str(e)}", {"task_id": task_id})
            return {"ok": False, "task_id": task_id, "error": str(e)}
    
    def execute_browser_task(
        self,
        url: str,
        actions: List[str],
        extract_selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute browser task."""
        
        task_parts = [f"Navigate to: {url}"]
        
        if extract_selectors:
            task_parts.append(f"Wait for: {extract_selectors.get('wait_for', 'body')}")
            task_parts.append(f"Extract from: {extract_selectors.get('container', 'main')}")
        
        task_parts.extend(actions)
        task = "\n".join(task_parts)
        
        context = {
            "url": url,
            "selectors": extract_selectors,
            "browser_config": {"headless": True, "timeout": 30000}
        }
        
        return self.execute_task(task, mode="browser", context=context)
    
    def execute_local_task(
        self,
        commands: List[str],
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute local task."""
        
        task = f"Execute: {'; '.join(commands)}"
        context = {"commands": commands, "cwd": cwd or str(self.workspace)}
        
        return self.execute_task(task, mode="local", context=context)


def create_bridge(workspace: Optional[str] = None) -> AgentZeroBridge:
    """Create bridge instance."""
    return AgentZeroBridge(workspace)


if __name__ == "__main__":
    try:
        bridge = AgentZeroBridge()
        print(f"✓ Bridge: {bridge.workspace}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
