import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from architect.mcp_hub import MCPHub, Task, AgentRole
from workers.phi4_builder import Phi4Builder
from workers.phi3_scout import Phi3Scout
from workers.mistral_creator import MistralCreator
import uuid

async def main():
    print("🦅 EPOS ARCHITECT: Initializing Swarm...")

    # 1. Shared Brain
    shared_hub = MCPHub(redis_url=None)
    await shared_hub.connect()
    
    # 2. Agents
    builder = Phi4Builder()
    scout = Phi3Scout()
    creator = MistralCreator()
    
    # 3. Neural Link (Inject Shared Hub)
    builder.hub = shared_hub
    scout.hub = shared_hub
    creator.hub = shared_hub
    
    # 4. Connect
    await builder.connect()
    await scout.connect()
    await creator.connect()

    # 5. Inject Initial Tasks (The Build Plan)
    print("📋 Injecting Build Tasks...")
    tasks = [
        ("Create Calendar API Schema", AgentRole.BUILDER),
        ("Draft Landing Page Copy", AgentRole.CREATOR),
        ("Analyze Competitor Pricing", AgentRole.SCOUT)
    ]
    
    for intent, role in tasks:
        task = Task(str(uuid.uuid4()), "epos_launch", intent, {"spec": "v1"}, [], [], role)
        await shared_hub.create_task(task)

    # 6. Run Swarm
    print("🚀 SWARM LAUNCHING...")
    await asyncio.gather(
        builder.run(),
        scout.run(),
        creator.run()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Swarm Shutdown.")
