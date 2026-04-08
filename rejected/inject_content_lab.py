import asyncio
import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from epos_hq.core.mcp_hub import hub

async def inject():
    print("💉 Injecting Content Lab Build Tasks...")
    
    # 1. UI Build Task (Phi-4)
    await hub.create_task(
        intent="Create Streamlit UI for Content Lab",
        role="BUILDER",
        inputs="Features: Topic Input, Archetype Selector, Generate Button. Use st.columns for layout."
    )
    
    # 2. Sales Copy Task (Mistral)
    await hub.create_task(
        intent="Write Landing Page Copy",
        role="CREATOR",
        inputs="Product: EPOS Content Lab. Audience: Solo Founders. Benefit: Automate content strategy."
    )
    
    # 3. Research Task (Phi-3)
    await hub.create_task(
        intent="Analyze Content Marketing Trends 2025",
        role="SCOUT",
        inputs="Focus on AI content tools and sovereignty."
    )
    
    print("✅ Tasks Injected into Queue.")

if __name__ == "__main__":
    asyncio.run(inject())
