import asyncio
import sys
import uuid
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

from epos_hq.core.mcp_hub import hub

async def inject_bootstrap_tasks():
    print("🦅 INJECTING SWARM BOOTSTRAP PROTOCOLS...")

    # --- KERNEL TYPES (The DNA) ---
    kernel_tasks = [
        ("kernel/types/base.py", "Define Entity class with Pydantic. Fields: id, tenant_id, user_id, created_at, updated_at."),
        ("kernel/types/identity.py", "Define CaptainEthos, IdentityProfile, BehaviorRule, MasterProtocol."),
        ("kernel/types/schedule.py", "Define TimeBlock, TemporalRef, ExternalRef."),
        ("kernel/types/canvas.py", "Define CanvasNode, CanvasEdge, Pipeline."),
        ("kernel/types/execution.py", "Define Task, Artifact."),
        ("kernel/types/life_os.py", "Define JournalEntry, Nudge."),
        ("kernel/types/telemetry.py", "Define ActionAfterActionReport."),
        ("kernel/types/ingest.py", "Define IngestJob.")
    ]

    for path, desc in kernel_tasks:
        await hub.create_task(
            intent=f"Create {path}",
            role="BUILDER",
            inputs=f"Path: {path}\nSpec: {desc}\nConstraint: Use Pydantic v2."
        )

    # --- EVENT BUS (The Nervous System) ---
    await hub.create_task(
        intent="Create kernel/events/base.py",
        role="BUILDER",
        inputs="Define EPOSEvent class. Fields: event_id, correlation_id, type, payload."
    )
    await hub.create_task(
        intent="Create kernel/events/topics.py",
        role="BUILDER",
        inputs="Define constants: CANVAS, SCHEDULE, LIFE, EXEC, TELEMETRY."
    )

    # --- REPOSITORIES (The Memory) ---
    await hub.create_task(
        intent="Create kernel/data/interfaces.py",
        role="BUILDER",
        inputs="Define abstract base Repository class and specific interfaces for Canvas, Schedule, Life, Exec."
    )
    await hub.create_task(
        intent="Create In-Memory Repos",
        role="BUILDER",
        inputs="Implement InMemoryCanvasRepository, InMemoryScheduleRepository, etc. in kernel/repos/."
    )

    # --- DOCUMENTATION (The Manual) ---
    docs = [
        ("docs/mvp/EXECUTION_BRIEF.md", "Write the Sprint A Execution Brief based on the 'One Loop Doctrine'."),
        ("docs/mvp/RUNBOOK.md", "Write the System Runbook for operators.")
    ]
    for path, desc in docs:
        await hub.create_task(
            intent=f"Write {path}",
            role="CREATOR",
            inputs=f"Path: {path}\nContent Goal: {desc}"
        )

    # --- VALIDATION (The Test) ---
    await hub.create_task(
        intent="Create Sentry Burst Harness",
        role="BUILDER",
        inputs="Create tests/sim/sentry_full_burst.py. Logic: Instantiate handlers, run 250 ops, assert 0 failures."
    )

    print(f"✅ {len(kernel_tasks) + 5} Tasks Injected into Swarm Queue.")

if __name__ == "__main__":
    asyncio.run(inject_bootstrap_tasks())
