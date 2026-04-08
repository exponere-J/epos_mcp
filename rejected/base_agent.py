import asyncio
import httpx
from epos_hq.core.mcp_hub import hub

class BaseAgent:
    def __init__(self, agent_id, role, model, ollama_url="http://localhost:11434"):
        self.agent_id = agent_id
        self.role = role
        self.model = model
        self.ollama_url = ollama_url

    async def connect(self):
        await hub.register_agent(self.agent_id, self.role, self.model)

    async def generate(self, prompt, system="You are a helpful assistant."):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                res = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )
                if res.status_code != 200:
                    raise Exception(f"Ollama Error: {res.status_code}")
                return res.json().get("response", "")
            except Exception as e:
                raise e

    async def run_loop(self):
        print(f"🚀 {self.agent_id} online.")
        while True:
            # Heartbeat
            await hub.heartbeat(self.agent_id)
            
            # Claim
            task = await hub.claim_task(self.agent_id, self.role)
            if task:
                print(f"🔨 {self.agent_id} working on: {task['intent']}")
                try:
                    output = await self.execute_task(task)
                    await hub.complete_task(task['id'], output)
                except Exception as e:
                    print(f"❌ Error executing task: {e}")
                    await hub.fail_task(task['id'], str(e))
            else:
                await asyncio.sleep(2)

    async def execute_task(self, task):
        raise NotImplementedError
