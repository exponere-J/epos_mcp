import asyncio
import sys
import json
import os
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

from epos_hq.agents.phi4_agent import Phi4Builder
from epos_hq.agents.phi3_agent import Phi3Scout
from epos_hq.agents.mistral_agent import MistralCreator
from epos_hq.agents.huntsman_agent import Huntsman
from epos_hq.agents.computeruse_agent import ComputerUse
from epos_hq.succession.monitor import monitor
from epos_hq.core.mcp_hub import hub

TRIGGER_DIR = Path("epos_hq/data/triggers")

async def watch_triggers():
    """Watches for UI commands"""
    TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    print("👀 Watching for UI Triggers...")
    
    while True:
        for trigger_file in TRIGGER_DIR.glob("*.json"):
            try:
                with open(trigger_file, "r") as f:
                    data = json.load(f)
                
                print(f"⚡ UI Trigger Received: {data['intent']}")
                
                # Convert UI intent to Agent Role Enum if needed
                role_map = {"CREATOR": "CREATOR", "BUILDER": "BUILDER", "SCOUT": "SCOUT"}
                role = role_map.get(data['role'], "SCOUT")
                
                await hub.create_task(data['intent'], role, data['inputs'])
                
                # Delete trigger after consumption
                os.remove(trigger_file)
                
            except Exception as e:
                print(f"❌ Trigger Error: {e}")
        
        await asyncio.sleep(1)

async def main():
    print("🦅 STARTING EPOS HQ (Full Swarm + UI Link)...")

    # 1. Initialize Agents
    agents = [
        Phi4Builder(), 
        Phi3Scout(), 
        MistralCreator(), 
        Huntsman(), 
        ComputerUse()
    ]

    # 2. Connect
    for agent in agents:
        await agent.connect()

    # 3. Launch Loops
    print("🚀 SYSTEMS GO. HQ OPERATIONAL.")
    
    tasks = [agent.run_loop() for agent in agents]
    tasks.append(monitor.run_loop())
    tasks.append(watch_triggers()) # Add the watcher
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 HQ Shutdown.")
