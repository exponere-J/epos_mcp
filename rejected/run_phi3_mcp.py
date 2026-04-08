import asyncio
from epos_hq.agents.mcp_worker import MCPWorker

async def research_logic(task):
    await asyncio.sleep(2) # Simulate thinking
    return "Research Complete: Market is hungry for sovereign AI."

async def main():
    worker = MCPWorker("phi3_scout", "SCOUT", ["research.icp"])
    await worker.connect()
    await worker.run_loop(research_logic)

if __name__ == "__main__":
    asyncio.run(main())
