import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# Import the Architecture
from architect.mcp_hub import MCPHub

# Import the Agents
from workers.phi4_builder import Phi4Builder
from workers.phi3_scout import Phi3Scout
from workers.mistral_creator import MistralCreator
from workers.phi3_commander import Phi3Commander

async def main():
    print("🦅 EPOS NEURAL LINK: Bridging Minds in Shared Memory...")

    # 1. Create the SHARED BRAIN (The Hub)
    shared_hub = MCPHub(redis_url=None) # Force memory mode
    await shared_hub.connect()
    
    # 2. Initialize Agents
    builder = Phi4Builder()
    scout = Phi3Scout()
    creator = MistralCreator()
    commander = Phi3Commander()
    
    # 3. PERFOM THE NEURAL LINK (Inject Shared Hub)
    # This overrides the separate hubs they would normally create
    builder.hub = shared_hub
    scout.hub = shared_hub
    creator.hub = shared_hub
    commander.hub = shared_hub
    
    print("✅ Neural Link Established. All agents sharing context.")

    # 4. Connect Agents (Register capabilities)
    # We call connect() but it will use the shared hub we just injected
    await builder.connect()
    await scout.connect()
    await creator.connect()
    await commander.connect()

    # 5. Run the Swarm Concurrently
    print("🚀 SWARM LAUNCHING...")
    
    await asyncio.gather(
        builder.run(),
        scout.run(),
        creator.run(),
        commander.run_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Neural Link Severed.")
