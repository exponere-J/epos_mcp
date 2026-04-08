from epos_hq.agents.base_agent import BaseAgent

class Phi4Builder(BaseAgent):
    def __init__(self):
        super().__init__("phi4_builder", "BUILDER", "phi4")

    async def execute_task(self, task):
        prompt = f"Write Python code for: {task['intent']}\nContext: {task['inputs']}\nOutput ONLY code."
        return await self.generate(prompt, system="You are an expert Python coder.")
