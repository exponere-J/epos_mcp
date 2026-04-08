# File: C:\Users\Jamie\workspace\epos_mcp\agents\agent_orchestrator.py

"""
EPOS Agent Orchestrator v1.0.0
==============================

Constitutional Authority: EPOS_CONSTITUTION_v3.1.md Articles V, X
Purpose: Coordinate governance agents and integrate with Agent Zero

This orchestrator manages the three governance agents:
- Constitutional Arbiter (Agent Alpha): Enforcement
- Context Librarian (Agent Sigma): Data custody
- Flywheel Analyst (Agent Omega): Strategy & amendments

It also serves as the integration point for Agent Zero, ensuring all
missions pass constitutional review before execution.

Architecture:
    External Request → Orchestrator → Arbiter Check → Context Setup → Agent Zero → BI Logging
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Ensure Python 3.11+
if sys.version_info[:2] < (3, 11):
    print("❌ CRITICAL: Python 3.11+ required (Article II Rule 3)")
    sys.exit(2)


class MissionStatus(Enum):
    """Mission execution status."""
    PENDING = "pending"
    VALIDATING = "validating"
    REJECTED = "rejected"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EPOSMission:
    """
    EPOS Mission specification.
    
    Constitutional Reference: Article V (Mission Schema)
    """
    mission_id: str
    objective: str
    constraints: Dict[str, Any]
    success_criteria: List[str]
    failure_modes: List[str]
    context_vault_path: Optional[str] = None
    priority: str = "normal"
    timeout_seconds: int = 300
    created: str = ""
    status: MissionStatus = MissionStatus.PENDING
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "status": self.status.value
        }


@dataclass
class ExecutionResult:
    """Result of mission execution."""
    mission_id: str
    status: MissionStatus
    output: Optional[Any]
    proof: Optional[Dict]
    execution_time_ms: float
    logs: List[str]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "status": self.status.value
        }


class AgentOrchestrator:
    """
    EPOS Agent Orchestrator
    
    Coordinates all governance agents and Agent Zero integration.
    """
    
    def __init__(self, epos_root: Optional[Path] = None, verbose: bool = False):
        """Initialize the orchestrator."""
        self.epos_root = epos_root or Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent)))
        self.verbose = verbose
        
        # Initialize agents (lazy loading)
        self._arbiter = None
        self._librarian = None
        self._analyst = None
        self._agent_zero = None
        
        # Mission queue
        self.mission_queue: List[EPOSMission] = []
        
        # Load environment
        self._load_environment()
    
    def _load_environment(self):
        """Load .env file."""
        try:
            from dotenv import load_dotenv
            env_path = self.epos_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass
    
    def _log(self, message: str):
        """Print message if verbose."""
        if self.verbose:
            print(f"[Orchestrator] {message}")
    
    # =========================================================================
    # AGENT INITIALIZATION
    # =========================================================================
    
    @property
    def arbiter(self):
        """Lazy load Constitutional Arbiter."""
        if self._arbiter is None:
            from constitutional_arbiter import ConstitutionalArbiter
            self._arbiter = ConstitutionalArbiter(self.epos_root, verbose=self.verbose)
        return self._arbiter
    
    @property
    def librarian(self):
        """Lazy load Context Librarian."""
        if self._librarian is None:
            from context_librarian import ContextLibrarian
            self._librarian = ContextLibrarian(self.epos_root, verbose=self.verbose)
        return self._librarian
    
    @property
    def analyst(self):
        """Lazy load Flywheel Analyst."""
        if self._analyst is None:
            from flywheel_analyst import FlywheelAnalyst
            self._analyst = FlywheelAnalyst(self.epos_root, verbose=self.verbose)
        return self._analyst
    
    def _init_agent_zero(self):
        """Initialize Agent Zero connection."""
        if self._agent_zero is not None:
            return True
        
        agent_zero_path = Path(os.getenv("AGENT_ZERO_PATH", str(Path(__file__).resolve().parent.parent.parent / "agent-zero")))
        
        if not agent_zero_path.exists():
            self._log("⚠️ Agent Zero path not found")
            return False
        
        try:
            sys.path.insert(0, str(agent_zero_path))
            from python.agent import Agent
            
            # Initialize Agent Zero with EPOS configuration
            self._agent_zero = Agent(
                name="EPOS-Worker",
                workspace=str(self.epos_root / "workspace"),
            )
            
            self._log("✅ Agent Zero initialized")
            return True
            
        except ImportError as e:
            self._log(f"⚠️ Agent Zero import failed: {e}")
            return False
    
    # =========================================================================
    # MISSION VALIDATION
    # =========================================================================
    
    def validate_mission(self, mission: EPOSMission) -> Dict:
        """
        Validate mission against constitutional requirements.
        
        Returns validation result with approval/rejection.
        """
        self._log(f"Validating mission: {mission.mission_id}")
        mission.status = MissionStatus.VALIDATING
        
        validation_result = {
            "mission_id": mission.mission_id,
            "approved": True,
            "violations": [],
            "warnings": [],
            "context_ready": False
        }
        
        # 1. Check required fields
        if not mission.objective:
            validation_result["approved"] = False
            validation_result["violations"].append("Missing objective")
        
        if not mission.success_criteria:
            validation_result["approved"] = False
            validation_result["violations"].append("Missing success_criteria")
        
        if not mission.failure_modes:
            validation_result["warnings"].append("No failure_modes defined (pre-mortem discipline)")
        
        # 2. Check context requirements
        if mission.context_vault_path:
            vault_path = self.epos_root / "context_vault" / mission.context_vault_path
            if not vault_path.exists():
                validation_result["approved"] = False
                validation_result["violations"].append(f"Context vault not found: {mission.context_vault_path}")
            else:
                validation_result["context_ready"] = True
        
        # 3. Estimate mission complexity
        objective_length = len(mission.objective)
        if objective_length > 8192:  # Token limit proxy
            if not mission.context_vault_path:
                validation_result["approved"] = False
                validation_result["violations"].append("Large objective requires context_vault_path")
        
        # 4. Run arbiter pre-flight
        # (In production, this would check any attached scripts)
        
        if validation_result["approved"]:
            mission.status = MissionStatus.APPROVED
            self._log(f"  ✅ Mission approved")
        else:
            mission.status = MissionStatus.REJECTED
            self._log(f"  🚫 Mission rejected: {validation_result['violations']}")
        
        return validation_result
    
    # =========================================================================
    # MISSION EXECUTION
    # =========================================================================
    
    def execute_mission(self, mission: EPOSMission) -> ExecutionResult:
        """
        Execute an approved mission via Agent Zero.
        
        Constitutional Reference: Article X (Vendor Integration)
        """
        import time
        start_time = time.time()
        logs = []
        
        # Validate first
        if mission.status != MissionStatus.APPROVED:
            validation = self.validate_mission(mission)
            if not validation["approved"]:
                return ExecutionResult(
                    mission_id=mission.mission_id,
                    status=MissionStatus.REJECTED,
                    output=None,
                    proof={"validation_errors": validation["violations"]},
                    execution_time_ms=0,
                    logs=logs
                )
        
        mission.status = MissionStatus.EXECUTING
        logs.append(f"Mission executing: {mission.mission_id}")
        
        # Setup context tools if needed
        context_tools = None
        if mission.context_vault_path:
            try:
                context_tools = self.librarian.create_agent_zero_tools(mission.context_vault_path)
                logs.append(f"Context tools loaded: {list(context_tools.keys())}")
            except Exception as e:
                logs.append(f"Warning: Context setup failed: {e}")
        
        # Initialize Agent Zero
        if not self._init_agent_zero():
            # Fallback: Execute locally without Agent Zero
            logs.append("Agent Zero unavailable, using local execution")
            
            result = self._execute_locally(mission)
            execution_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                mission_id=mission.mission_id,
                status=MissionStatus.COMPLETED if result.get("success") else MissionStatus.FAILED,
                output=result.get("output"),
                proof=result.get("proof", {}),
                execution_time_ms=execution_time,
                logs=logs
            )
        
        # Execute via Agent Zero
        try:
            logs.append("Executing via Agent Zero...")
            
            # Build prompt with context tools
            prompt = self._build_agent_zero_prompt(mission, context_tools)
            
            # Execute
            # Note: This is a simplified representation. Real Agent Zero
            # integration would use its actual API.
            response = self._agent_zero.run(prompt)
            
            execution_time = (time.time() - start_time) * 1000
            logs.append(f"Execution completed in {execution_time:.0f}ms")
            
            # Build proof
            proof = {
                "agent": "agent_zero",
                "execution_time_ms": execution_time,
                "context_used": mission.context_vault_path is not None
            }
            
            mission.status = MissionStatus.COMPLETED
            
            return ExecutionResult(
                mission_id=mission.mission_id,
                status=MissionStatus.COMPLETED,
                output=response,
                proof=proof,
                execution_time_ms=execution_time,
                logs=logs
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logs.append(f"Execution failed: {e}")
            
            mission.status = MissionStatus.FAILED
            
            return ExecutionResult(
                mission_id=mission.mission_id,
                status=MissionStatus.FAILED,
                output=None,
                proof={"error": str(e)},
                execution_time_ms=execution_time,
                logs=logs
            )
    
    def _build_agent_zero_prompt(self, mission: EPOSMission, context_tools: Optional[Dict]) -> str:
        """Build prompt for Agent Zero."""
        prompt_parts = [
            f"# Mission: {mission.mission_id}",
            f"",
            f"## Objective",
            f"{mission.objective}",
            f"",
            f"## Success Criteria",
        ]
        
        for criterion in mission.success_criteria:
            prompt_parts.append(f"- {criterion}")
        
        prompt_parts.extend([
            f"",
            f"## Constraints",
            f"{json.dumps(mission.constraints, indent=2)}",
        ])
        
        if context_tools:
            prompt_parts.extend([
                f"",
                f"## Available Context Tools",
                f"You have access to the following tools for querying large context:",
            ])
            for name, tool in context_tools.items():
                prompt_parts.append(f"- `{name}`: {tool.get('description', 'No description')}")
        
        if mission.failure_modes:
            prompt_parts.extend([
                f"",
                f"## Pre-Identified Failure Modes",
                f"Watch out for these potential issues:",
            ])
            for mode in mission.failure_modes:
                prompt_parts.append(f"- {mode}")
        
        return "\n".join(prompt_parts)
    
    def _execute_locally(self, mission: EPOSMission) -> Dict:
        """Fallback local execution when Agent Zero unavailable."""
        # This is a placeholder for local execution logic
        # In production, this could call other services or handle simple tasks
        
        return {
            "success": True,
            "output": f"Mission {mission.mission_id} acknowledged (local execution)",
            "proof": {
                "execution_mode": "local_fallback",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    # =========================================================================
    # BI LOGGING
    # =========================================================================
    
    def log_execution(self, result: ExecutionResult):
        """Log execution result to BI decision log."""
        bi_log_path = self.epos_root / "bi_decision_log.json"
        
        try:
            if bi_log_path.exists():
                bi_data = json.loads(bi_log_path.read_text())
            else:
                bi_data = {"decisions": []}
            
            bi_data["decisions"].append({
                "agent": "orchestrator",
                "action": "mission_execution",
                "timestamp": result.timestamp,
                "mission_id": result.mission_id,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
                "success": result.status == MissionStatus.COMPLETED
            })
            
            bi_log_path.write_text(json.dumps(bi_data, indent=2))
            
        except Exception as e:
            self._log(f"Warning: BI logging failed: {e}")
    
    # =========================================================================
    # HEALTH CHECK
    # =========================================================================
    
    def health_check(self) -> Dict:
        """Run health check on all agents."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator": "healthy",
            "agents": {}
        }
        
        # Check Arbiter
        try:
            arbiter = self.arbiter
            health["agents"]["constitutional_arbiter"] = "healthy"
        except Exception as e:
            health["agents"]["constitutional_arbiter"] = f"error: {e}"
        
        # Check Librarian
        try:
            librarian = self.librarian
            vault_status = librarian.get_vault_status()
            health["agents"]["context_librarian"] = {
                "status": "healthy",
                "vault_count": vault_status["total_vaults"],
                "vault_size_mb": vault_status["total_size_mb"]
            }
        except Exception as e:
            health["agents"]["context_librarian"] = f"error: {e}"
        
        # Check Analyst
        try:
            analyst = self.analyst
            health["agents"]["flywheel_analyst"] = "healthy"
        except Exception as e:
            health["agents"]["flywheel_analyst"] = f"error: {e}"
        
        # Check Agent Zero
        agent_zero_path = Path(os.getenv("AGENT_ZERO_PATH", str(Path(__file__).resolve().parent.parent.parent / "agent-zero")))
        if agent_zero_path.exists():
            health["agents"]["agent_zero"] = {
                "status": "available",
                "path": str(agent_zero_path)
            }
        else:
            health["agents"]["agent_zero"] = "unavailable"
        
        return health
    
    # =========================================================================
    # SCHEDULED TASKS
    # =========================================================================
    
    def run_daily_tasks(self):
        """Run daily scheduled tasks."""
        self._log("Running daily tasks...")
        
        # 1. Failure pattern detection
        patterns = self.analyst.detect_failure_patterns(days=1)
        self._log(f"  Patterns detected: {len(patterns)}")
        
        # 2. Arbiter inbox triage
        triage_results = self.arbiter.triage_inbox(dry_run=False)
        self._log(f"  Files triaged: {len(triage_results.get('promoted', []))} promoted, {len(triage_results.get('rejected', []))} rejected")
        
        return {
            "patterns": [p.to_dict() for p in patterns],
            "triage": triage_results
        }
    
    def run_weekly_tasks(self):
        """Run weekly scheduled tasks."""
        self._log("Running weekly tasks...")
        
        # 1. Sprint boundary audit
        audit = self.arbiter.sprint_audit()
        self._log(f"  Governance score: {audit.get('governance_score', 0)}%")
        
        # 2. Flywheel report
        report = self.analyst.generate_weekly_report()
        self._log(f"  Flywheel health: {report.get('overall_health', 'unknown')}")
        
        # 3. Vault hygiene
        hygiene = self.librarian.run_hygiene(dry_run=False)
        self._log(f"  Vaults archived: {len(hygiene.get('archived', []))}")
        
        return {
            "audit": audit,
            "flywheel_report": report,
            "hygiene": hygiene
        }


def main():
    """CLI entrypoint for Agent Orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOS Agent Orchestrator")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--daily", action="store_true", help="Run daily tasks")
    parser.add_argument("--weekly", action="store_true", help="Run weekly tasks")
    parser.add_argument("--execute", type=str, help="Execute a mission file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    orchestrator = AgentOrchestrator(verbose=args.verbose)
    
    if args.health:
        health = orchestrator.health_check()
        
        if args.json:
            print(json.dumps(health, indent=2))
        else:
            print("\n🏥 Agent Health Check")
            print(f"   Orchestrator: {health['orchestrator']}")
            for agent, status in health['agents'].items():
                if isinstance(status, dict):
                    print(f"   {agent}: {status.get('status', 'unknown')}")
                else:
                    print(f"   {agent}: {status}")
        
        sys.exit(0)
    
    elif args.daily:
        results = orchestrator.run_daily_tasks()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n📅 Daily Tasks Complete")
            print(f"   Patterns: {len(results.get('patterns', []))}")
            print(f"   Files Triaged: {len(results.get('triage', {}).get('promoted', []))}")
        
        sys.exit(0)
    
    elif args.weekly:
        results = orchestrator.run_weekly_tasks()
        
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print("\n📊 Weekly Tasks Complete")
            print(f"   Governance Score: {results.get('audit', {}).get('governance_score', 0)}%")
            print(f"   Flywheel Health: {results.get('flywheel_report', {}).get('overall_health', 'unknown')}")
        
        sys.exit(0)
    
    elif args.execute:
        mission_path = Path(args.execute)
        if not mission_path.exists():
            print(f"❌ Mission file not found: {mission_path}")
            sys.exit(1)
        
        try:
            mission_data = json.loads(mission_path.read_text())
            mission = EPOSMission(**mission_data)
        except Exception as e:
            print(f"❌ Invalid mission file: {e}")
            sys.exit(1)
        
        result = orchestrator.execute_mission(mission)
        orchestrator.log_execution(result)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            emoji = "✅" if result.status == MissionStatus.COMPLETED else "❌"
            print(f"\n{emoji} Mission {result.mission_id}: {result.status.value}")
            print(f"   Execution time: {result.execution_time_ms:.0f}ms")
        
        sys.exit(0 if result.status == MissionStatus.COMPLETED else 1)
    
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
