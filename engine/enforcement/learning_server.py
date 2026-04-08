# EPOS GOVERNANCE WATERMARK
# File: ${EPOS_ROOT}/engine/enforcement/learning_server.py
"""
EPOS Learning Server - Autonomous Learning and Remediation
Constitutional Authority: Article VI (Autonomous Evolution) + Article VII (Context Vault)

This server subscribes to governance violation events and generates
educational remediation lessons that are stored in the Context Vault.

Usage:
    from engine.enforcement.learning_server import LearningServer
    
    server = LearningServer()
    server.start()  # Starts listening for events
"""

from pathlib import Path
from datetime import datetime
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Import the event bus
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from event_bus import get_event_bus, EventType
except ImportError:
    get_event_bus = None
    EventType = None


@dataclass
class RemediationLesson:
    """A remediation lesson for an agent."""
    lesson_id: str
    agent_id: str
    violations: List[str]
    lesson_path: str
    exercise_path: Optional[str]
    created_at: str
    estimated_time_minutes: int


@dataclass
class AgentPerformance:
    """Performance record for an agent."""
    agent_id: str
    total_violations: int
    total_successes: int
    violations_by_code: Dict[str, int]
    recent_violations: List[Dict[str, Any]]
    compliance_rate: float
    trend: str  # "improving", "stable", "declining"


class RemediationGenerator:
    """
    Generates educational remediation lessons from violations.
    
    Constitutional Authority: Article VII (Context Vault)
    """
    
    DEFAULT_EPOS_ROOT = Path(os.getenv("EPOS_ROOT") or str(Path(__file__).resolve().parent.parent.parent))
    
    # Lesson templates for each violation type
    LESSON_TEMPLATES = {
        "ERR-HEADER-001": {
            "title": "File Header Requirements",
            "content": """# Remediation Lesson: File Headers

## The Violation
Your code is missing the mandatory file header that specifies the absolute path.

## Why This Matters
The file header serves multiple purposes:
1. **IDE Navigation**: Cursor and VS Code use this to reliably locate files
2. **Import Resolution**: Python's import system needs clear path references
3. **Audit Trail**: Constitutional compliance requires knowing where code lives

## The Fix
Add this header as the FIRST line of your Python file:

```python
# File: ${EPOS_ROOT}/{relative_path}
```

## Constitutional Reference
- **Article II.2**: "Every file MUST have a header comment with absolute path"
- **PATH_CLARITY_RULES.md**: Full specification of path requirements

## Exercise
Create a new Python file with the correct header format.
""",
            "exercise": """# Exercise: File Header Practice

## Task
Create a file called `test_header.py` in the `inbox/` directory with:

1. Correct file header on line 1
2. A simple function that prints "Hello, EPOS!"
3. An `if __name__ == "__main__":` block

## Validation
Run `python governance_gate.py --file inbox/test_header.py` to check your work.

## Success Criteria
- No ERR-HEADER-001 violation
- File promoted to `engine/`
"""
        },
        "ERR-PATH-001": {
            "title": "Windows Absolute Paths",
            "content": """# Remediation Lesson: Path Handling

## The Violation
Your code uses relative or POSIX-style paths instead of Windows absolute paths.

## Why This Matters
EPOS runs on Windows 11 and requires consistent path handling:
1. **Cross-Shell Compatibility**: Git Bash and PowerShell interpret paths differently
2. **Reproducibility**: Relative paths break when working directory changes
3. **Constitutional Compliance**: Article II.1 mandates absolute paths

## The Problem Patterns
```python
# ❌ WRONG - Relative paths
path = "../config/settings.json"
path = "./data/output.txt"
path = "~/documents/file.txt"

# ❌ WRONG - POSIX-style paths
path = "/c/Users/Jamie/workspace"
path = "/mnt/c/data"
```

## The Fix
```python
# ✅ CORRECT - Windows absolute paths with pathlib
from pathlib import Path

path = Path(os.environ["EPOS_ROOT"]) / "config" / "settings.json"
# or
path = EPOS_ROOT / "config" / "settings.json"
```

## Best Practices
1. Always use `pathlib.Path` for path operations
2. Use forward slashes in Path() - Python normalizes them
3. Define base paths in environment variables or config

## Constitutional Reference
- **Article II.1**: "All paths MUST be Windows-style absolute paths"
- **PATH_CLARITY_RULES.md**: Complete specification
""",
            "exercise": """# Exercise: Path Refactoring

## Task
Refactor this code to use proper Windows absolute paths:

```python
import os

config_path = "../config/settings.json"
output_dir = "./outputs"
data_file = "~/data/input.csv"

def load_config():
    with open(config_path) as f:
        return json.load(f)
```

## Validation
Submit your refactored code to `inbox/` and run governance gate.

## Success Criteria
- No ERR-PATH-001 violations
- Uses pathlib.Path throughout
- All paths are Windows absolute
"""
        },
        "ERR-IMPORT-001": {
            "title": "Event-Driven Architecture",
            "content": """# Remediation Lesson: Event Bus Integration

## The Violation
Your code directly imports RewardBus or RemediationGenerator instead of using the event bus.

## Why This Matters
EPOS uses event-driven architecture for component communication:
1. **Node Sovereignty**: Direct imports create tight coupling
2. **Scalability**: Event bus allows async, decoupled communication
3. **Observability**: Events provide audit trail for learning cycles

## The Problem Pattern
```python
# ❌ WRONG - Direct imports create coupling
from engine.enforcement.reward_bus import RewardBus
from engine.enforcement.remediation_generator import RemediationGenerator

def handle_violation(violations):
    bus = RewardBus()
    bus.generate_remediation(violations)  # Tight coupling!
```

## The Fix
```python
# ✅ CORRECT - Use event bus for communication
from event_bus import get_event_bus

def handle_violation(violations):
    bus = get_event_bus()
    bus.publish(
        event_type="governance.violation_detected",
        payload={"violations": violations},
        metadata={"trace_id": trace_id}
    )
    # Learning server subscribes and handles remediation asynchronously
```

## Constitutional Reference
- **Article VII**: "Context Governance via Event-Driven Communication"
- **MICROSYSTEM_ARCHITECTURE.md**: Event bus patterns
- **NODE_SOVEREIGNTY_CONSTITUTION.md**: Independence requirements
""",
            "exercise": """# Exercise: Event Bus Migration

## Task
Refactor this component to use event bus instead of direct imports:

```python
from engine.enforcement.reward_bus import RewardBus

class MyComponent:
    def __init__(self):
        self.reward_bus = RewardBus()
    
    def process(self, data):
        result = self.validate(data)
        if not result.valid:
            self.reward_bus.log_failure(result.errors)
```

## Validation
- No ERR-IMPORT-001 violations
- Component publishes events instead of calling methods directly
"""
        },
        "ERR-ENTRYPOINT-001": {
            "title": "Pre-Flight Validation",
            "content": """# Remediation Lesson: Entrypoint Validation

## The Violation
Your entrypoint (main function) doesn't call epos_doctor.py for pre-flight checks.

## Why This Matters
Pre-flight validation catches environment issues BEFORE execution:
1. **Python Version**: Ensures 3.11.x compatibility
2. **Service Availability**: Checks Ollama, paths, ports
3. **Constitutional Compliance**: Required by Article II.3

## The Problem Pattern
```python
# ❌ WRONG - No pre-flight check
if __name__ == "__main__":
    main()  # Might fail due to environment issues
```

## The Fix
```python
# ✅ CORRECT - Pre-flight validation
from engine.epos_doctor import EPOSDoctor

if __name__ == "__main__":
    # Run pre-flight checks
    doctor = EPOSDoctor()
    if not doctor.run():
        print("Pre-flight checks failed. Fix issues before proceeding.")
        sys.exit(1)
    
    # Now safe to run
    main()
```

## Constitutional Reference
- **Article II.3**: "Entrypoints MUST call epos_doctor.py"
- **PRE_FLIGHT_CHECKLIST.md**: Complete validation list
""",
            "exercise": """# Exercise: Add Pre-Flight Checks

## Task
Add proper pre-flight validation to this entrypoint:

```python
def main():
    print("Starting application...")
    # ... application code ...

if __name__ == "__main__":
    main()
```
"""
        },
    }
    
    def __init__(self, vault_path: Path = None):
        """
        Initialize the remediation generator.
        
        Args:
            vault_path: Path to context vault (defaults to standard location)
        """
        self.epos_root = Path(os.getenv("EPOS_ROOT", str(self.DEFAULT_EPOS_ROOT)))
        self.vault_path = vault_path or (self.epos_root / "context_vault")
        
        # Learning directories
        self.learning_dir = self.vault_path / "learning"
        self.remediation_library = self.learning_dir / "remediation_library"
        self.exercise_templates = self.remediation_library / "exercise_templates"
        self.agent_performance = self.learning_dir / "agent_performance"
        
        # Ensure directories exist
        for dir_path in [self.remediation_library, self.exercise_templates, self.agent_performance]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def generate_lesson(
        self,
        violations: List[str],
        agent_id: str,
        file_path: str = None,
        trace_id: str = None
    ) -> RemediationLesson:
        """
        Generate a remediation lesson for the given violations.
        
        Args:
            violations: List of violation codes
            agent_id: ID of the agent that needs remediation
            file_path: Path to the file that was rejected
            trace_id: Trace ID for correlation
        
        Returns:
            RemediationLesson object with paths to generated content
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lesson_id = f"LESSON_{agent_id}_{timestamp}"
        
        # Build lesson content
        lesson_content = self._build_lesson_content(violations, file_path)
        
        # Save lesson
        lesson_filename = f"{lesson_id}.md"
        lesson_path = self.remediation_library / lesson_filename
        lesson_path.write_text(lesson_content, encoding="utf-8")
        
        # Build and save exercise
        exercise_content = self._build_exercise_content(violations)
        exercise_path = None
        if exercise_content:
            exercise_filename = f"{lesson_id}_exercise.md"
            exercise_path = self.exercise_templates / exercise_filename
            exercise_path.write_text(exercise_content, encoding="utf-8")
        
        # Create lesson record
        lesson = RemediationLesson(
            lesson_id=lesson_id,
            agent_id=agent_id,
            violations=violations,
            lesson_path=str(lesson_path),
            exercise_path=str(exercise_path) if exercise_path else None,
            created_at=datetime.now().isoformat(),
            estimated_time_minutes=len(violations) * 10  # 10 min per violation
        )
        
        return lesson
    
    def _build_lesson_content(self, violations: List[str], file_path: str = None) -> str:
        """Build the lesson markdown content."""
        lines = [
            "# EPOS Remediation Lesson",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**File:** {file_path or 'N/A'}",
            f"**Violations:** {', '.join(violations)}",
            "",
            "---",
            ""
        ]
        
        for v_code in violations:
            template = self.LESSON_TEMPLATES.get(v_code)
            if template:
                lines.append(f"## {template['title']}")
                lines.append("")
                lines.append(template["content"])
                lines.append("")
                lines.append("---")
                lines.append("")
            else:
                lines.append(f"## {v_code}")
                lines.append("")
                lines.append(f"No specific lesson available for {v_code}.")
                lines.append("Please refer to EPOS_CONSTITUTION_v3.1.md for details.")
                lines.append("")
        
        return "\n".join(lines)
    
    def _build_exercise_content(self, violations: List[str]) -> Optional[str]:
        """Build the exercise markdown content."""
        exercises = []
        
        for v_code in violations:
            template = self.LESSON_TEMPLATES.get(v_code)
            if template and template.get("exercise"):
                exercises.append(template["exercise"])
        
        if not exercises:
            return None
        
        lines = [
            "# EPOS Remediation Exercises",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "Complete these exercises to reinforce your learning.",
            "",
            "---",
            ""
        ]
        
        for i, exercise in enumerate(exercises, 1):
            lines.append(f"## Exercise {i}")
            lines.append("")
            lines.append(exercise)
            lines.append("")
        
        return "\n".join(lines)


class ComplianceTracker:
    """
    Tracks agent performance and compliance over time.
    
    Constitutional Authority: Article V (Agent Performance)
    """
    
    DEFAULT_EPOS_ROOT = Path(os.getenv("EPOS_ROOT") or str(Path(__file__).resolve().parent.parent.parent))
    
    def __init__(self, ledger_path: Path = None):
        """
        Initialize the compliance tracker.
        
        Args:
            ledger_path: Path to agent performance ledgers
        """
        self.epos_root = Path(os.getenv("EPOS_ROOT", str(self.DEFAULT_EPOS_ROOT)))
        self.ledger_path = ledger_path or (
            self.epos_root / "context_vault" / "learning" / "agent_performance"
        )
        self.ledger_path.mkdir(parents=True, exist_ok=True)
    
    def record_violation(self, agent_id: str, violation: Dict[str, Any]):
        """
        Record a violation event for an agent.
        
        Args:
            agent_id: ID of the agent
            violation: Violation details
        """
        record = {
            "type": "violation",
            "timestamp": datetime.now().isoformat(),
            "violations": violation.get("violations", []),
            "file_path": violation.get("file_path"),
            "trace_id": violation.get("trace_id")
        }
        
        self._append_to_ledger(agent_id, record)
    
    def record_success(self, agent_id: str, success: Dict[str, Any]):
        """
        Record a successful validation for an agent.
        
        Args:
            agent_id: ID of the agent
            success: Success details
        """
        record = {
            "type": "success",
            "timestamp": datetime.now().isoformat(),
            "file_path": success.get("file_path"),
            "trace_id": success.get("trace_id")
        }
        
        self._append_to_ledger(agent_id, record)
    
    def record_exercise_completion(self, agent_id: str, exercise: Dict[str, Any]):
        """
        Record exercise completion for an agent.
        
        Args:
            agent_id: ID of the agent
            exercise: Exercise completion details
        """
        record = {
            "type": "exercise_completed",
            "timestamp": datetime.now().isoformat(),
            "lesson_id": exercise.get("lesson_id"),
            "passed": exercise.get("passed", True),
            "trace_id": exercise.get("trace_id")
        }
        
        self._append_to_ledger(agent_id, record)
    
    def _append_to_ledger(self, agent_id: str, record: Dict[str, Any]):
        """Append a record to an agent's ledger."""
        ledger_file = self.ledger_path / f"{agent_id}.jsonl"
        
        with open(ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def get_agent_performance(self, agent_id: str, window_days: int = 30) -> AgentPerformance:
        """
        Calculate performance metrics for an agent.
        
        Args:
            agent_id: ID of the agent
            window_days: Number of days to consider
        
        Returns:
            AgentPerformance object with metrics
        """
        ledger_file = self.ledger_path / f"{agent_id}.jsonl"
        
        records = []
        if ledger_file.exists():
            with open(ledger_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        
        # Calculate metrics
        total_violations = sum(1 for r in records if r.get("type") == "violation")
        total_successes = sum(1 for r in records if r.get("type") == "success")
        
        violations_by_code = {}
        recent_violations = []
        
        for r in records:
            if r.get("type") == "violation":
                for v_code in r.get("violations", []):
                    violations_by_code[v_code] = violations_by_code.get(v_code, 0) + 1
                recent_violations.append(r)
        
        # Keep only last 10 violations
        recent_violations = recent_violations[-10:]
        
        # Calculate compliance rate
        total = total_violations + total_successes
        compliance_rate = total_successes / total if total > 0 else 1.0
        
        # Calculate trend (simplified)
        if len(records) < 5:
            trend = "stable"
        else:
            recent_violations_count = sum(
                1 for r in records[-5:] if r.get("type") == "violation"
            )
            older_violations_count = sum(
                1 for r in records[-10:-5] if r.get("type") == "violation"
            )
            
            if recent_violations_count < older_violations_count:
                trend = "improving"
            elif recent_violations_count > older_violations_count:
                trend = "declining"
            else:
                trend = "stable"
        
        return AgentPerformance(
            agent_id=agent_id,
            total_violations=total_violations,
            total_successes=total_successes,
            violations_by_code=violations_by_code,
            recent_violations=recent_violations,
            compliance_rate=compliance_rate,
            trend=trend
        )
    
    def get_compliance_score(self, agent_id: str, window_days: int = 30) -> float:
        """
        Calculate compliance score for an agent.
        
        Args:
            agent_id: ID of the agent
            window_days: Number of days to consider
        
        Returns:
            Float 0.0-1.0 where 1.0 = 100% compliant
        """
        performance = self.get_agent_performance(agent_id, window_days)
        return performance.compliance_rate


class LearningServer:
    """
    Main learning server that orchestrates remediation generation.
    
    Subscribes to governance events and generates educational content.
    
    Constitutional Authority: Article VI (Autonomous Evolution)
    """
    
    def __init__(self):
        """Initialize the learning server."""
        self.event_bus = get_event_bus() if get_event_bus else None
        self.generator = RemediationGenerator()
        self.tracker = ComplianceTracker()
        self._running = False
    
    def start(self):
        """Start the learning server."""
        if not self.event_bus:
            print("[LearningServer] Warning: Event bus not available")
            return
        
        # Subscribe to governance events
        self.event_bus.subscribe("governance.violation_detected", self._handle_violation)
        self.event_bus.subscribe("governance.validation_passed", self._handle_success)
        
        # Start polling
        self.event_bus.start_polling()
        self._running = True
        
        print("[LearningServer] Started and listening for events")
    
    def stop(self):
        """Stop the learning server."""
        self._running = False
        if self.event_bus:
            self.event_bus.stop_polling()
        print("[LearningServer] Stopped")
    
    def _handle_violation(self, event: Dict[str, Any]):
        """
        Handle a governance violation event.
        
        Generates remediation and publishes completion event.
        """
        payload = event.get("payload", {})
        metadata = event.get("metadata", {})
        
        violations = payload.get("violations", [])
        agent_id = payload.get("agent_id", "unknown")
        file_path = payload.get("file_path")
        trace_id = metadata.get("trace_id")
        
        print(f"[LearningServer] Processing violation for {agent_id}: {violations}")
        
        # Record violation in tracker
        self.tracker.record_violation(agent_id, {
            "violations": violations,
            "file_path": file_path,
            "trace_id": trace_id
        })
        
        # Generate remediation lesson
        lesson = self.generator.generate_lesson(
            violations=violations,
            agent_id=agent_id,
            file_path=file_path,
            trace_id=trace_id
        )
        
        # Publish remediation generated event
        if self.event_bus:
            self.event_bus.publish(
                event_type="learning.remediation_generated",
                payload={
                    "lesson_id": lesson.lesson_id,
                    "lesson_path": lesson.lesson_path,
                    "exercise_path": lesson.exercise_path,
                    "agent_id": agent_id,
                    "violations": violations,
                    "estimated_time_minutes": lesson.estimated_time_minutes
                },
                metadata={"trace_id": trace_id},
                source_server="learning_server"
            )
        
        print(f"[LearningServer] Generated lesson: {lesson.lesson_id}")
    
    def _handle_success(self, event: Dict[str, Any]):
        """Handle a successful validation event."""
        payload = event.get("payload", {})
        metadata = event.get("metadata", {})
        
        agent_id = payload.get("agent_id", "unknown")
        file_path = payload.get("file_path")
        trace_id = metadata.get("trace_id")
        
        # Record success in tracker
        self.tracker.record_success(agent_id, {
            "file_path": file_path,
            "trace_id": trace_id
        })
        
        print(f"[LearningServer] Recorded success for {agent_id}")


if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="EPOS Learning Server")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    
    args = parser.parse_args()
    
    if args.test:
        print("\n📚 Learning Server Self-Test")
        print("=" * 40)
        
        # Test generator
        gen = RemediationGenerator()
        lesson = gen.generate_lesson(
            violations=["ERR-HEADER-001", "ERR-PATH-001"],
            agent_id="test_agent",
            file_path="inbox/test.py"
        )
        
        print(f"  Generated lesson: {lesson.lesson_id}")
        print(f"  Lesson path: {lesson.lesson_path}")
        print(f"  Exercise path: {lesson.exercise_path}")
        
        # Test tracker
        tracker = ComplianceTracker()
        tracker.record_violation("test_agent", {
            "violations": ["ERR-HEADER-001"],
            "file_path": "test.py"
        })
        tracker.record_success("test_agent", {
            "file_path": "test2.py"
        })
        
        perf = tracker.get_agent_performance("test_agent")
        print(f"\n  Agent performance:")
        print(f"    Violations: {perf.total_violations}")
        print(f"    Successes: {perf.total_successes}")
        print(f"    Compliance: {perf.compliance_rate:.0%}")
        print(f"    Trend: {perf.trend}")
        
        print("\n✅ Self-test complete!")
    
    elif args.daemon:
        server = LearningServer()
        server.start()
        
        print("\n📚 Learning Server Running")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
    
    else:
        print("Use --daemon to run server or --test for self-test")
