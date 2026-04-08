from epos_hq.agents.base_agent import BaseAgent

class MistralCreator(BaseAgent):
    def __init__(self):
        super().__init__("mistral_creator", "CREATOR", "mistral:7b")

    async def execute_task(self, task):
        prompt = f"Write content for: {task['intent']}\nDetails: {task['inputs']}"
        return await self.generate(prompt, system="You are a creative copywriter.")
