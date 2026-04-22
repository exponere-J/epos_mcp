# File: /mnt/c/Users/Jamie/workspace/epos_mcp/az_mission_executor.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
"""
AGENT ZERO MISSION EXECUTOR â€” EPOS Integration Wrapper
=======================================================
File: az_mission_executor.py
Purpose: Feed EPOS missions to Agent Zero for deterministic execution
Authority: Agent Zero as Execution Spine, Phi-3 as Strategic Cortex

ARCHITECTURE:
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚          Phi-3 Command Center (Strategic)           â”‚
â”‚         Reasons, decides, generates missions        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
             â”‚  Mission Executor  â”‚
             â”‚  (This Script)     â”‚
             â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
             â”‚    Agent Zero      â”‚
             â”‚  (Deterministic    â”‚
             â”‚   Execution)       â”‚
             â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚              â”‚              â”‚
   â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”
   â”‚Context â”‚   â”‚Event Bus â”‚   â”‚MCP      â”‚
   â”‚ Vault  â”‚   â”‚          â”‚   â”‚Servers  â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

USAGE:
python az_mission_executor.py --mission AZ-001-NERVOUS-SYSTEM
python az_mission_executor.py --mission AZ-002-AIRTABLE-BASES --dry-run
python az_mission_executor.py --list  # Show all available missions
"""

import os
from dotenv import load_dotenv
load_dotenv()
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SETUP
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

WORKSPACE_ROOT = Path(os.getenv("EPOS_ROOT", Path.cwd()))
CONTEXT_VAULT = WORKSPACE_ROOT / "context_vault"
MISSIONS_DIR = CONTEXT_VAULT / "missions"
AZ_LOGS = WORKSPACE_ROOT / "logs" / "az"
AZ_LOGS.mkdir(parents=True, exist_ok=True)

AGENT_ZERO_PATH = Path(os.getenv("AGENT_ZERO_PATH", WORKSPACE_ROOT / "agent-zero"))

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
EXECUTION_LOG = AZ_LOGS / f"az_execution_{TIMESTAMP}.jsonl"


def log(event: str, status: str, detail: str = ""):
    """Constitutional Article II: No silent failures"""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "status": status,
        "detail": detail
    }
    
    with open(EXECUTION_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    print(f"[{status}] {event} â€” {detail}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MISSION MANAGEMENT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def load_mission(mission_id: str) -> Optional[Dict]:
    """Load mission JSON file"""
    mission_file = MISSIONS_DIR / f"{mission_id}.json"
    
    if not mission_file.exists():
        log("MISSION_LOAD", "FAIL", f"Mission file not found: {mission_id}")
        return None
    
    try:
        with open(mission_file, "r") as f:
            mission = json.load(f)
        
        log("MISSION_LOAD", "SUCCESS", f"Loaded mission: {mission['title']}")
        return mission
    
    except Exception as e:
        log("MISSION_LOAD", "FAIL", f"Error loading mission: {str(e)}")
        return None


def list_available_missions() -> List[Dict]:
    """List all mission files in missions directory"""
    mission_files = list(MISSIONS_DIR.glob("AZ-*.json"))
    
    missions = []
    for file_path in sorted(mission_files):
        try:
            with open(file_path, "r") as f:
                mission = json.load(f)
            missions.append({
                "id": mission["mission_id"],
                "title": mission["title"],
                "week": mission.get("week", "?"),
                "priority": mission.get("priority", "NORMAL")
            })
        except:
            continue
    
    return missions


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# AGENT ZERO EXECUTION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def execute_with_agent_zero(mission: Dict, dry_run: bool = False) -> bool:
    """Execute mission tasks via Agent Zero"""
    
    mission_id = mission["mission_id"]
    title = mission["title"]
    tasks = mission.get("tasks", [])
    
    log("AZ_EXECUTION_START", "INFO", f"Mission: {title} ({len(tasks)} tasks)")
    
    if dry_run:
        log("AZ_EXECUTION", "DRY_RUN", "Simulating execution (no actual changes)")
        for idx, task in enumerate(tasks, 1):
            print(f"  [{idx}/{len(tasks)}] {task}")
        return True
    
    # Check Agent Zero availability
    if not AGENT_ZERO_PATH.exists():
        log("AZ_CHECK", "FAIL", f"Agent Zero not found at: {AGENT_ZERO_PATH}")
        print(f"\nâš ï¸  Agent Zero path not configured correctly.")
        print(f"    Expected: {AGENT_ZERO_PATH}")
        print(f"    Set AGENT_ZERO_PATH in .env or install Agent Zero")
        return False
    
    # Build Agent Zero prompt
    prompt = f"""MISSION: {title}

MISSION ID: {mission_id}
PRIORITY: {mission.get('priority', 'NORMAL')}
WEEK: {mission.get('week', 'TBD')}

DESCRIPTION:
{mission.get('description', 'No description')}

CONSTITUTIONAL COMPLIANCE REQUIRED:
{chr(10).join('- ' + item for item in mission.get('constitutional_compliance', []))}

TASKS TO EXECUTE:
{chr(10).join(f'{idx}. {task}' for idx, task in enumerate(tasks, 1))}

SUCCESS CRITERIA:
{chr(10).join('- ' + item for item in mission.get('success_criteria', []))}

FAILURE RECOVERY:
{mission.get('failure_recovery', 'Log failure and alert human operator')}

EXECUTION REQUIREMENTS:
- Log every action to context_vault/missions/az_executions/{mission_id}_{TIMESTAMP}.jsonl
- Publish completion event to Event Bus (if running)
- On failure: log error, do NOT proceed to next task
- On success: verify all success criteria before marking complete

Execute these tasks in order. Report status after each task.
"""
    
    # Save prompt to file for Agent Zero
    prompt_file = AZ_LOGS / f"{mission_id}_prompt.txt"
    prompt_file.write_text(prompt, encoding='utf-8')
    
    log("AZ_PROMPT", "SUCCESS", f"Prompt saved: {prompt_file.name}")
    
    # Execute via Agent Zero
    # NOTE: This assumes Agent Zero can be called via CLI
    # Adjust command based on your actual Agent Zero setup
    
    try:
        log("AZ_INVOKE", "INFO", "Invoking Agent Zero...")
        
        # Method 1: If Agent Zero has CLI interface
        cmd = [
            "python",
            str(AGENT_ZERO_PATH / "run.py"),
            "--prompt-file", str(prompt_file),
            "--output", str(AZ_LOGS / f"{mission_id}_output.txt")
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max per mission
        )
        
        if result.returncode == 0:
            log("AZ_EXECUTION", "SUCCESS", f"Mission completed: {mission_id}")
            
            # Save output
            output_file = AZ_LOGS / f"{mission_id}_output.txt"
            if result.stdout:
                output_file.write_text(result.stdout)
            
            return True
        else:
            log("AZ_EXECUTION", "FAIL", f"Exit code: {result.returncode}")
            if result.stderr:
                log("AZ_ERROR", "FAIL", result.stderr[:500])
            return False
    
    except FileNotFoundError:
        log("AZ_INVOKE", "FAIL", "Agent Zero run.py not found")
        print(f"\nâš ï¸  Agent Zero CLI not configured.")
        print(f"    Manual execution required:")
        print(f"    1. Open Agent Zero")
        print(f"    2. Load prompt from: {prompt_file}")
        print(f"    3. Execute mission manually")
        return False
    
    except subprocess.TimeoutExpired:
        log("AZ_EXECUTION", "FAIL", "Mission timeout after 1 hour")
        return False
    
    except Exception as e:
        log("AZ_EXECUTION", "FAIL", str(e))
        return False


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def main():
    parser = argparse.ArgumentParser(description="Agent Zero Mission Executor")
    parser.add_argument("--mission", help="Mission ID to execute (e.g., AZ-001-NERVOUS-SYSTEM)")
    parser.add_argument("--list", action="store_true", help="List all available missions")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without changes")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  AGENT ZERO MISSION EXECUTOR")
    print(f"  Workspace: {WORKSPACE_ROOT}")
    print(f"  Agent Zero: {AGENT_ZERO_PATH}")
    print("="*70 + "\n")
    
    # List missions
    if args.list:
        missions = list_available_missions()
        
        if not missions:
            print("âš ï¸  No missions found in context_vault/missions/\n")
            sys.exit(1)
        
        print(f"ðŸ“‹ Available Missions ({len(missions)}):\n")
        for m in missions:
            priority_icon = {"CRITICAL": "ðŸ”´", "HIGH": "ðŸŸ ", "NORMAL": "ðŸŸ¢"}.get(m["priority"], "âšª")
            print(f"  {priority_icon} {m['id']}")
            print(f"     Week {m['week']} â€” {m['title']}")
            print()
        
        sys.exit(0)
    
    # Execute mission
    if not args.mission:
        print("âŒ Error: --mission required (or use --list to see options)\n")
        sys.exit(1)
    
    mission = load_mission(args.mission)
    
    if not mission:
        print(f"\nâŒ Mission not found: {args.mission}\n")
        print("   Use --list to see available missions\n")
        sys.exit(1)
    
    # Display mission summary
    print(f"ðŸ“‹ Mission: {mission['title']}")
    print(f"   ID: {mission['mission_id']}")
    print(f"   Week: {mission.get('week', 'TBD')}")
    print(f"   Priority: {mission.get('priority', 'NORMAL')}")
    print(f"   Tasks: {len(mission.get('tasks', []))}")
    print(f"   Duration: {mission.get('estimated_duration', 'Unknown')}")
    print()
    
    # Check dependencies
    dependencies = mission.get("dependencies", [])
    if dependencies:
        print("ðŸ“¦ Dependencies:")
        for dep in dependencies:
            print(f"   - {dep}")
        print()
    
    # Confirm execution
    if not args.dry_run:
        confirm = input("â–¶ Execute mission with Agent Zero? (y/N): ")
        if confirm.lower() != 'y':
            print("\nâŒ Execution cancelled\n")
            sys.exit(0)
    
    # Execute
    print()
    success = execute_with_agent_zero(mission, dry_run=args.dry_run)
    
    # Summary
    print("\n" + "="*70)
    if success:
        print("  âœ… MISSION COMPLETE")
    else:
        print("  âŒ MISSION FAILED")
    print("="*70)
    
    print(f"\nðŸ“„ Log: {EXECUTION_LOG.relative_to(WORKSPACE_ROOT)}\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

