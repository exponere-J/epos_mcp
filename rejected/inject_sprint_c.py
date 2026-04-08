import asyncio
import sys
import uuid
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

from epos_hq.core.mcp_hub import hub, Task, AgentRole

async def inject_sprint_c():
    print("🦅 INJECTING SPRINT C: THE CONTENT ENGINE...")

    # --- PHASE C1: CANONICAL CONTENT ENGINE ---
    await hub.create_task(
        intent="Create CCO Schema",
        role="BUILDER",
        inputs="Path: content/canonical/cco.schema.json\nContent: Define CCO structure (UUID, version, archetype, intent, core_message)."
    )
    await hub.create_task(
        intent="Implement CCO Enforcer",
        role="BUILDER",
        inputs="Path: content/canonical/cco_enforcer.py\nLogic: Validate CCOs, enforce lineage, log events."
    )
    await hub.create_task(
        intent="Create MCP Hooks",
        role="BUILDER",
        inputs="Path: content/canonical/mcp_hooks.py\nLogic: Bridge CCO creation to MCP tasks."
    )

    # --- PHASE C2: NATIVE SCRAPERS ---
    await hub.create_task(
        intent="Implement Scraper Adapter",
        role="BUILDER",
        inputs="Path: content/intake/scraper_adapter.py\nLogic: Normalize raw HTML into CCO structure."
    )
    await hub.create_task(
        intent="Create Native Scrapers",
        role="BUILDER",
        inputs="Path: content/intake/native_scrapers.py\nLogic: Use Huntsman to fetch content."
    )

    # --- PHASE C3: AUDIENCE DECOMPOSITION ---
    await hub.create_task(
        intent="Build Audience Engine",
        role="BUILDER",
        inputs="Path: content/decomposition/audience_engine.py\nLogic: Generate variants for Awareness/Sophistication levels."
    )
    await hub.create_task(
        intent="Implement Lineage Tracker",
        role="BUILDER",
        inputs="Path: content/decomposition/lineage_tracker.py\nLogic: Maintain graph of CCO -> Variants."
    )

    # --- PHASE C4: MULTI-FORMAT DISTILLATION ---
    await hub.create_task(
        intent="Create Format Engine",
        role="BUILDER",
        inputs="Path: content/artifacts/format_engine.py\nLogic: Convert variants to Twitter/LinkedIn/Email formats."
    )

    # --- PHASE C5: HUMAN GATES ---
    await hub.create_task(
        intent="Build Approval System",
        role="BUILDER",
        inputs="Path: content/review/approval_system.py\nLogic: Manage review queue and decisions."
    )

    # --- PHASE C6: DISTRIBUTION ---
    await hub.create_task(
        intent="Implement Deployment Engine",
        role="BUILDER",
        inputs="Path: content/distribution/deployment_engine.py\nLogic: Deploy artifacts and log signals."
    )

    # --- PHASE C7: REINFORCEMENT ---
    await hub.create_task(
        intent="Create Reinforcement Engine",
        role="BUILDER",
        inputs="Path: content/evolution/reinforcement_engine.py\nLogic: Score content performance."
    )
    
    print("✅ Sprint C Injected. Swarm is building the Engine.")

if __name__ == "__main__":
    asyncio.run(inject_sprint_c())
