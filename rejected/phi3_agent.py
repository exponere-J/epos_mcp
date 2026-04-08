from epos_hq.agents.base_agent import BaseAgent

class Phi3Scout(BaseAgent):
    def __init__(self):
        super().__init__("phi3_scout", "SCOUT", "phi3:mini")

    async def execute_task(self, task):
        prompt = f"Analyze: {task['inputs']}\nGoal: {task['intent']}"
        return await self.generate(prompt, system="You are a research analyst.")
