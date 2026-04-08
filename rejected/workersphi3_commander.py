import asyncio
import httpx
import json
import sys
import uuid
from pathlib import Path

# Add architect to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from architect.mcp_hub import MCPHub, Task, AgentRole, TaskStatus

class Phi3Commander:
    """
    The Local Team Lead.
    Operates on CrewAI principles:
    1. Decompose Goal -> Tasks
    2. Assign Tasks -> Agents
    3. Review Output -> Iteration
    """
    
    def __init__(self):
        self.agent_id = "phi3_commander"
        self.hub = MCPHub()
        self.ollama_url = "http://localhost:11434"
        self.model = "phi3:mini"
        
        # The "Crew" Definition
        self.crew_manifest = {
            "builder": {"role": AgentRole.BUILDER, "model": "phi4", "desc": "Writes code, DB schemas, APIs"},
            "creative": {"role": AgentRole.CREATOR, "model": "mistral", "desc": "Writes copy, marketing, emails"},
            "scout": {"role": AgentRole.SCOUT, "model": "phi3", "desc": "Research and analysis"}
        }

    async def connect(self):
        await self.hub.connect()
        # Register self as PLANNER (taking Claude's spot)
        await self.hub.register_agent(
            self.agent_id, 
            AgentRole.PLANNER, 
            self.model, 
            ["orchestration", "planning", "delegation"]
        )
        print(f"🫡 Commander {self.agent_id} reporting for duty.")

    async def decompose_goal(self, goal):
        """
        Uses Phi-3 to break a high-level goal into actionable tasks.
        """
        system_prompt = """
        You are the Crew Commander.
        Your goal is to break a project objective into specific tasks for your agents.
        
        AGENTS:
        - BUILDER (Phi-4): Code, Python, SQL.
        - CREATOR (Mistral): Content, Text, Marketing.
        - SCOUT (Phi-3): Research, Summary.
        
        OUTPUT FORMAT: JSON List of tasks.
        Example: [{"role": "BUILDER", "intent": "create_api.py", "inputs": "..."}]
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
                        "format": "json" # Force JSON output
                    }
                )
                plan = res.json().get("response", "[]")
                return json.loads(plan)
        except Exception as e:
            print(f"❌ Planning failed: {e}")
            return []

    async def execute_plan(self, project_id, task_list):
        """
        Dispatches tasks to the MCP Hub for workers to pick up.
        """
        print(f"📋 Dispatching {len(task_list)} tasks for Project: {project_id}")
        
        for item in task_list:
            # Map string role to Enum
            role_str = item.get("role", "SCOUT").upper()
            role_enum = AgentRole[role_str] if role_str in AgentRole.__members__ else AgentRole.SCOUT
            
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
        Main Commander Loop:
        1. Check for 'PLANNING' requests.
        2. Decompose and Dispatch.
        3. Monitor progress.
        """
        print("🧠 Commander Logic Active. Waiting for directives...")
        
        # In a real scenario, this would listen for "PLANNER" tasks.
        # For this demo, we will inject a test goal manually on startup.
        
        test_goal = "Build a FastAPI backend for the Calendar OS with a PostgreSQL database."
        print(f"\n🧪 TEST INJECTION: {test_goal}\n")
        
        tasks = await self.decompose_goal(test_goal)
        if tasks:
            await self.execute_plan("demo_project_01", tasks)
        else:
            print("⚠️ Failed to generate plan.")

        # Keep alive
        while True:
            await asyncio.sleep(10)

if __name__ == "__main__":
    commander = Phi3Commander()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(commander.connect())
    loop.run_until_complete(commander.run_loop())
