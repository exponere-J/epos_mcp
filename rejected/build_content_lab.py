import asyncio
import sys
import uuid
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from architect.mcp_hub import MCPHub, Task, AgentRole
from workers.phi4_builder import Phi4Builder
from workers.phi3_scout import Phi3Scout
from workers.mistral_creator import MistralCreator

async def main():
    print("🦅 EPOS CONTENT LAB: Commencing Build...")

    # 1. Setup Neural Link
    shared_hub = MCPHub(redis_url=None)
    await shared_hub.connect()
    
    builder = Phi4Builder(); builder.hub = shared_hub
    scout = Phi3Scout(); scout.hub = shared_hub
    creator = MistralCreator(); creator.hub = shared_hub
    
    await builder.connect(); await scout.connect(); await creator.connect()

    # 2. Inject The Product Spec
    print("📋 Injecting Product Spec...")
    
    # Task 1: Build the UI (Phi-4)
    ui_task = Task(str(uuid.uuid4()), "content_lab", "Create Streamlit UI for Content Generator", 
                   {"framework": "streamlit", "features": ["input_form", "generate_btn"]}, [], [], AgentRole.BUILDER)
    
    # Task 2: Write the Sales Copy (Mistral)
    copy_task = Task(str(uuid.uuid4()), "content_lab", "Write Landing Page Headlines", 
                     {"product": "AI Content Lab", "benefit": "Save 10 hours/week"}, [], [], AgentRole.CREATOR)
    
    # Task 3: Research Viral Hooks (Phi-3)
    research_task = Task(str(uuid.uuid4()), "content_lab", "Analyze Top 3 LinkedIn Hook Styles", 
                         {"platform": "linkedin"}, [], [], AgentRole.SCOUT)

    await shared_hub.create_task(ui_task)
    await shared_hub.create_task(copy_task)
    await shared_hub.create_task(research_task)

    # 3. Execute
    print("🚀 BUILDING PRODUCT...")
    await asyncio.gather(builder.run(), scout.run(), creator.run())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Build Complete.")
