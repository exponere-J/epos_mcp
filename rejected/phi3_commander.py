# workers/phi3_commander.py

import asyncio
import httpx
import json
import sys
import uuid
from pathlib import Path
from typing import List, Dict

# Add architect to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from architect.mcp_hub import MCPHub, Task, AgentRole, TaskStatus

class Phi3Commander:
    """
    Phi-3 Commander Agent
    
    Role: Local Team Lead / Orchestrator
    Responsibilities:
    1. Decompose high-level goals into tasks
    2. Assign tasks to agents (Builder, Creator, Scout)
    3. Monitor progress
    """
    
    def __init__(
        self,
        agent_id: str = "phi3_commander",
        ollama_url: str = "http://localhost:11434"
    ):
        self.agent_id = agent_id
        self.ollama_url = ollama_url
        self.model = "phi3:mini"
        self.role = AgentRole.PLANNER # Taking the planner role locally
        
        self.hub = None
        self.running = False
        
        # Manifest of available agents for planning
        self.crew_manifest = {
            "builder": {"role": AgentRole.BUILDER, "model": "phi4", "desc": "Writes code, DB schemas, APIs"},
            "creative": {"role": AgentRole.CREATOR, "model": "mistral", "desc": "Writes copy, marketing, emails"},
            "scout": {"role": AgentRole.SCOUT, "model": "phi3", "desc": "Research and analysis"}
        }

    async def connect(self):
        """Connect to MCP Hub"""
        self.hub = MCPHub()
        await self.hub.connect()
        
        # Register self
        await self.hub.register_agent(
            self.agent_id, 
            self.role, 
            self.model, 
            ["orchestration", "planning", "delegation"]
        )
        print(f"🫡 Commander {self.agent_id} reporting for duty.")

    async def decompose_goal(self, goal: str) -> List[Dict]:
        """
        Uses Phi-3 to break a high-level goal into actionable tasks.
        """
        system_prompt = """
        You are the Crew Commander.
        Your goal is to break a project objective into specific tasks for your agents.
        
        AGENTS:
        - BUILDER (Phi-4): Code, Python, SQL, API endpoints.
        - CREATOR (Mistral): Content, Text, Marketing, Documentation.
        - SCOUT (Phi-3): Research, Summary, Data extraction.
        
        OUTPUT FORMAT: JSON List of tasks.
        Example: [{"role": "BUILDER", "intent": "create_api.py", "inputs": "spec details..."}]
        
        Return ONLY valid JSON.
        """
        
        prompt = f"GOAL: {goal}\n\nCreate the task list."
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False,
                        "options": {"temperature": 0.1},
                        "format": "json" # Force JSON output if supported (newer Ollama versions)
                    }
                )
                
                response_text = res.json().get("response", "[]")
                # Basic cleanup if model outputs markdown
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                    
                return json.loads(response_text)
        except Exception as e:
            print(f"❌ Planning failed: {e}")
            return []

    async def execute_plan(self, project_id: str, task_list: List[Dict]):
        """
        Dispatches tasks to the MCP Hub for workers to pick up.
        """
        print(f"📋 Dispatching {len(task_list)} tasks for Project: {project_id}")
        
        for item in task_list:
            # Map string role to Enum
            role_str = item.get("role", "SCOUT").upper()
            try:
                role_enum = AgentRole[role_str]
            except KeyError:
                role_enum = AgentRole.SCOUT
            
            task = Task(
                task_id=str(uuid.uuid4()),
                project_id=project_id,
                intent=item.get("intent", "unknown_task"),
                inputs={"spec": item.get("inputs", "")},
                required_outputs=["result"],
                acceptance_tests=[],
                assigned_role=role_enum
            )
            
            await self.hub.create_task(task)
            print(f"  -> Task Sent: {task.intent} -> {role_enum.name}")

    async def run_loop(self):
        """
        Main Commander Loop
        """
        self.running = True
        print("🧠 Commander Logic Active. Waiting for directives...")
        
        # Test injection for demonstration
        # In production, this would listen for triggers or user input via a CLI/API
        await asyncio.sleep(2)
        test_goal = "Build a FastAPI backend for the Calendar OS with a PostgreSQL database schema."
        print(f"\n🧪 TEST INJECTION: {test_goal}\n")
        
        tasks = await self.decompose_goal(test_goal)
        if tasks:
            await self.execute_plan("demo_project_01", tasks)
        else:
            print("⚠️ Failed to generate plan.")

        while self.running:
            await asyncio.sleep(10)
    
    async def stop(self):
        self.running = False
        if self.hub:
            await self.hub.unregister_agent(self.agent_id)
            await self.hub.close()
        print(f"👋 {self.agent_id} stopped")

if __name__ == "__main__":
    commander = Phi3Commander()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(commander.connect())
        loop.run_until_complete(commander.run_loop())
    finally:
        loop.run_until_complete(commander.stop())
        loop.close()
