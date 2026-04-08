import asyncio
import httpx
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from architect.mcp_hub import MCPHub, AgentRole, TaskStatus

class Phi4Builder:
    def __init__(self, agent_id="phi4_1"):
        self.agent_id = agent_id
        self.hub = MCPHub()
        self.ollama_url = "http://localhost:11434"
        self.model = "phi4"

    async def connect(self):
        await self.hub.connect()
        await self.hub.register_agent(self.agent_id, AgentRole.BUILDER, self.model, ["code"])

    async def generate(self, prompt):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                res = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": "You are an expert Python developer. Output ONLY valid code blocks.",
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )
                if res.status_code == 200:
                    return res.json().get("response", "")
                else:
                    return f"# Error: Ollama status {res.status_code}"
            except Exception as e:
                return f"# Error: {str(e)}"

    async def run(self):
        print(f"🚀 {self.agent_id} ready...")
        while True:
            try:
                task = await self.hub.claim_task(self.agent_id, AgentRole.BUILDER, [])
                if task:
                    print(f"🔨 Building: {task.intent}")
                    code = await self.generate(f"Write code for: {task.intent}\nDetails: {task.inputs}")
                    
                    # Log the output (In a real system, we save to file)
                    print(f"   -> Generated {len(code)} bytes of code.")
                    
                    await self.hub.update_task_status(task.task_id, TaskStatus.COMPLETED, outputs={"code": code})
                else:
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Error in loop: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    worker = Phi4Builder()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker.connect())
    loop.run_until_complete(worker.run())
