import asyncio
import json
import uuid
import sys
import os
import time
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    WORKING = "WORKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

class MCPHub:
    def __init__(self, persistence_path="epos_hq/data/state.json"):
        self.persistence_path = Path(persistence_path)
        self.state = {
            "tasks": {},
            "agents": {},
            "ceo": {"active": "Claude", "status": "PRIMARY"},
            "metrics": {
                "completed_tasks": 0,
                "failed_tasks": 0,
                "uptime_start": datetime.now().isoformat()
            }
        }
        self._load_state()

    def _load_state(self):
        if self.persistence_path.exists():
            try:
                with open(self.persistence_path, "r") as f:
                    self.state = json.load(f)
            except:
                print("⚠️ Corrupt state file. Starting fresh.")

    def _save_state(self):
        """Windows-safe atomic write"""
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp file first
        fd, temp_path = tempfile.mkstemp(dir=self.persistence_path.parent, delete=False)
        try:
            with os.fdopen(fd, 'w') as tmp:
                json.dump(self.state, tmp, indent=2)
            
            # Windows workaround for atomic replace
            max_retries = 5
            for i in range(max_retries):
                try:
                    if self.persistence_path.exists():
                        os.replace(temp_path, self.persistence_path)
                    else:
                        os.rename(temp_path, self.persistence_path)
                    break
                except PermissionError:
                    if i == max_retries - 1:
                        pass # Silent fail on lock
                    time.sleep(0.1) 
        except Exception as e:
            print(f"❌ Save Error: {e}")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    async def register_agent(self, agent_id, role, model):
        self.state["agents"][agent_id] = {
            "role": role,
            "model": model,
            "status": "IDLE",
            "last_heartbeat": datetime.now().isoformat(),
            "tasks_completed": 0,
            "tasks_failed": 0
        }
        self._save_state()
        print(f"🤖 Agent Registered: {agent_id}")

    async def heartbeat(self, agent_id):
        if agent_id in self.state["agents"]:
            self.state["agents"][agent_id]["last_heartbeat"] = datetime.now().isoformat()
            self._save_state()

    async def create_task(self, intent, role, inputs, priority=1):
        task_id = str(uuid.uuid4())
        self.state["tasks"][task_id] = {
            "id": task_id,
            "intent": intent,
            "role": role,
            "inputs": inputs,
            "priority": priority,
            "status": "PENDING",
            "retries": 0,
            "max_retries": 3,
            "created_at": datetime.now().isoformat()
        }
        self._save_state()
        print(f"📋 New Task: {intent}")
        return task_id

    async def claim_task(self, agent_id, role):
        for tid, task in self.state["tasks"].items():
            if task["status"] in ["PENDING", "RETRYING"] and task["role"] == role:
                task["status"] = "CLAIMED"
                task["claimed_by"] = agent_id
                task["started_at"] = datetime.now().isoformat()
                self.state["agents"][agent_id]["status"] = "WORKING"
                self._save_state()
                return task
        return None

    async def complete_task(self, task_id, output):
        if task_id in self.state["tasks"]:
            task = self.state["tasks"][task_id]
            task["status"] = "COMPLETED"
            task["output"] = output
            task["completed_at"] = datetime.now().isoformat()
            
            agent_id = task.get("claimed_by")
            if agent_id:
                self.state["agents"][agent_id]["status"] = "IDLE"
                self.state["agents"][agent_id]["tasks_completed"] += 1
            
            self.state["metrics"]["completed_tasks"] += 1
            self._save_state()
            print(f"✅ Task Completed: {task_id}")

    async def fail_task(self, task_id, error):
        if task_id in self.state["tasks"]:
            task = self.state["tasks"][task_id]
            agent_id = task.get("claimed_by")
            
            if agent_id:
                self.state["agents"][agent_id]["status"] = "IDLE"
                self.state["agents"][agent_id]["tasks_failed"] += 1

            if task["retries"] < task["max_retries"]:
                task["status"] = "RETRYING"
                task["retries"] += 1
                task["last_error"] = str(error)
                task["claimed_by"] = None
                print(f"⚠️ Task Failed (Retry {task['retries']}): {task_id}")
            else:
                task["status"] = "FAILED"
                task["error"] = str(error)
                self.state["metrics"]["failed_tasks"] += 1
                print(f"❌ Task FAILED Permanently: {task_id}")
            
            self._save_state()

    async def update_ceo_status(self, ceo_name, status):
        self.state["ceo"] = {"active": ceo_name, "status": status, "updated": datetime.now().isoformat()}
        self._save_state()

hub = MCPHub()
