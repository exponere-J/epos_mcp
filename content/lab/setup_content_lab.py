# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/content/lab/setup_content_lab.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
EPOS Content Lab - Directory Setup (Hell Week Sprint 1)
Path: epos_mcp/content/lab/setup_content_lab.py

Run this ONCE to create the full Content Lab directory tree.
Safe to re-run (uses exist_ok=True on all paths).
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone


EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
CONTENT_LAB = EPOS_ROOT / "content" / "lab"

DIRECTORIES = [
    # Tributary (bottom-up)
    "tributaries/x/captured",
    "tributaries/x/scored",
    "tributaries/tiktok/captured",
    "tributaries/tiktok/scored",
    # Cascade (top-down)
    "cascades/youtube/sources",
    "cascades/youtube/sources/processed",
    "cascades/linkedin/sources",
    "cascades/linkedin/sources/processed",
    "cascades/derivatives",
    # Automation
    "automation",
    # Validation
    "validation",
    "validation_failures",
    # Production pipeline
    "production",
    "publish_queue",
    "published",
    "ready_to_post/x",
    "ready_to_post/linkedin",
    "ready_to_post/tiktok",
    "ready_to_post/youtube",
    "ready_to_post/instagram",
    "ready_to_post/email",
    # Expansion and archive
    "expansion_queue",
    "archive",
    # Intelligence / BI
    "intelligence",
]

# Context Vault subdirectories needed
VAULT_DIRS = [
    "bi_history",
    "events",
    "market_sentiment",
    "mission_data",
    "agent_logs",
]


def setup():
    print(f"[*] Setting up Content Lab at: {CONTENT_LAB}")
    print(f"[*] EPOS Root: {EPOS_ROOT}")

    # Create Content Lab directories
    for d in DIRECTORIES:
        path = CONTENT_LAB / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {path}")

    # Ensure Context Vault directories
    vault = EPOS_ROOT / "context_vault"
    for d in VAULT_DIRS:
        path = vault / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {path}")

    # Create __init__.py files for Python imports
    init_dirs = [
        CONTENT_LAB,
        CONTENT_LAB / "tributaries",
        CONTENT_LAB / "cascades",
        CONTENT_LAB / "automation",
        CONTENT_LAB / "validation",
    ]
    for d in init_dirs:
        init_file = d / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# EPOS Content Lab\n")
            print(f"  [OK] {init_file}")

    # Write component registration
    registration = {
        "id": "C10_CONTENT_LAB",
        "name": "Content Lab - Algorithmic Echolocation & Cascading",
        "version": "1.0.0",
        "status": "operational",
        "dependencies": ["C01_META_ORCHESTRATOR", "C05_GOVERNANCE_GATE", "C09_CONTEXT_VAULT"],
        "nodes": {
            "R1_radar": {"status": "staged", "file": "tributaries/echolocation_algorithm.py"},
            "A1_architect": {"status": "planned", "file": "TODO"},
            "P1_producer": {"status": "planned", "file": "TODO"},
            "V1_validator": {"status": "staged", "file": "validation/brand_validator.py"},
            "M1_marshall": {"status": "staged", "file": "automation/publish_orchestrator.py"},
            "AN1_analyst": {"status": "staged", "file": "tributaries/echolocation_algorithm.py"},
        },
        "health_check": "/content/lab/health",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    reg_file = CONTENT_LAB / "component_registration.json"
    with open(reg_file, "w", encoding="utf-8") as f:
        json.dump(registration, f, indent=2)
    print(f"  [OK] {reg_file}")

    print(f"\n[COMPLETE] Content Lab directory structure created.")
    print(f"[NEXT] Copy Python files into their directories and run test missions.")


if __name__ == "__main__":
    setup()
