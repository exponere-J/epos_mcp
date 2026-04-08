import asyncio
import httpx
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from architect.mcp_hub import MCPHub, AgentRole, TaskStatus

class MistralCreator:
    def __init__(self, agent_id="mistral_1"):
        self.agent_id = agent_id
        self.hub = MCPHub()
        self.ollama_url = "http://localhost:11434"
        self.model = "mistral:7b"

    async def connect(self):
        await self.hub.connect()
        await self.hub.register_agent(self.agent_id, AgentRole.CREATOR, self.model, ["copy"])

    async def run(self):
        print(f"🎨 {self.agent_id} ready...")
        while True:
            try:
                task = await self.hub.claim_task(self.agent_id, AgentRole.CREATOR, [])
                if task:
                    print(f"✍️ Writing: {task.intent}")
                    # Simulation
                    await asyncio.sleep(1)
                    await self.hub.update_task_status(task.task_id, TaskStatus.COMPLETED, outputs={"copy": "Draft Content"})
                else:
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    worker = MistralCreator()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker.connect())
    loop.run_until_complete(worker.run())
