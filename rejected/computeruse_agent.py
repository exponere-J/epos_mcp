from epos_hq.agents.base_agent import BaseAgent
from epos_hq.workflows.computeruse.runner import run_computeruse

class ComputerUse(BaseAgent):
    def __init__(self):
        super().__init__("computeruse", "COMPUTERUSE", "tool:pyautogui")

    async def execute_task(self, task):
        return run_computeruse(task.get("inputs", {}))
