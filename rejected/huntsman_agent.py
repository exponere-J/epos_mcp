from epos_hq.agents.base_agent import BaseAgent
from epos_hq.workflows.browser.huntsman import run_browser

class Huntsman(BaseAgent):
    def __init__(self):
        super().__init__("huntsman", "HUNTSMAN", "tool:playwright")

    async def execute_task(self, task):
        return await run_browser(task.get("inputs", {}))
