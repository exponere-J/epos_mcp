# EPOS GOVERNANCE WATERMARK
"""
File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/enforcement/reward_bus.py
Purpose: Orchestrates the failure→lesson→improvement cycle
Constitutional Authority: EPOS_CONSTITUTION_v3.1.md Article III

The Reward Bus transforms constitutional violations into learning opportunities.
Instead of terminal failures, violations trigger:
1. Educational remediation content generation
2. Compliance tracking for improvement measurement
3. Context injection for agent learning
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from event_bus import get_event_bus
except ImportError:
    get_event_bus = None

from engine.enforcement.remediation_generator import RemediationGenerator
from engine.enforcement.compliance_tracker import ComplianceTracker


class RewardBus:
    """
    Orchestrates the recursive learning cycle.
    
    Flow:
    1. Receives governance.violation_detected event
    2. Triggers remediation_generator to create lesson
    3. Logs violation to compliance_tracker
    4. Publishes learning.remediation_generated event
    5. On success, updates compliance score
    """
    
    def __init__(self, epos_root: Path = None):
        """Initialize Reward Bus with optional root override."""
        self.epos_root = epos_root or Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
        self.event_bus = get_event_bus() if get_event_bus else None
        
        # Initialize subsystems
        self.remediation_gen = RemediationGenerator(epos_root=self.epos_root)
        self.compliance = ComplianceTracker(epos_root=self.epos_root)
        
        # Subscribe to governance events
        if self.event_bus:
            self.event_bus.subscribe("governance.violation_detected", self.handle_violation)
            self.event_bus.subscribe("governance.validation_passed", self.handle_success)
            print(f"✅ Reward Bus initialized - subscribed to governance events")
    
    def handle_violation(self, event: Dict[str, Any]):
        """
        Process violation event and trigger learning cycle.
        
        Called automatically when governance.violation_detected is published.
        """
        try:
            payload = event["payload"]
            agent_id = payload.get("agent_id", "unknown")
            violations = payload.get("violations", [])
            file_path = payload.get("file_path", "")
            trace_id = event.get("metadata", {}).get("trace_id", "")
            
            if not violations:
                print(f"⚠️ Violation event has no violation codes - skipping")
                return
            
            print(f"\n🔄 Reward Bus: Processing violation for {agent_id}")
            print(f"   Violations: {violations}")
            print(f"   Trace ID: {trace_id}")
            
            # Generate remediation lesson for primary violation
            primary_violation = violations[0]
            lesson = self.remediation_gen.generate_lesson(
                violation_code=primary_violation,
                file_path=file_path,
                agent_id=agent_id
            )
            
            print(f"   ✅ Lesson generated: {lesson['lesson_id']}")
            
            # Log to compliance tracker
            self.compliance.record_violation(
                agent_id=agent_id,
                violation_code=primary_violation,
                mission_id=payload.get("mission_id")
            )
            
            print(f"   ✅ Violation logged to compliance tracker")
            
            # Publish remediation event
            if self.event_bus:
                self.event_bus.publish(
                    event_type="learning.remediation_generated",
                    payload={
                        "agent_id": agent_id,
                        "lesson_path": str(lesson["lesson_path"]),
                        "lesson_id": lesson["lesson_id"],
                        "violation_code": primary_violation
                    },
                    metadata={"trace_id": trace_id, "source_server": "reward_bus"}
                )
                
                print(f"   ✅ Published learning.remediation_generated event")
            
        except Exception as e:
            print(f"❌ Reward Bus error processing violation: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_success(self, event: Dict[str, Any]):
        """
        Record successful validation as agent improvement.
        
        Called automatically when governance.validation_passed is published.
        """
        try:
            payload = event["payload"]
            agent_id = payload.get("agent_id", "unknown")
            trace_id = event.get("metadata", {}).get("trace_id", "")
            
            print(f"\n✅ Reward Bus: Recording success for {agent_id}")
            print(f"   Trace ID: {trace_id}")
            
            # Record success in compliance tracker
            self.compliance.record_success(
                agent_id=agent_id,
                mission_id=payload.get("mission_id")
            )
            
            # Get updated compliance score
            score = self.compliance.get_compliance_score(agent_id)
            print(f"   📊 Compliance score: {score:.1%}")
            
        except Exception as e:
            print(f"❌ Reward Bus error processing success: {e}")
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive status for an agent."""
        return {
            "agent_id": agent_id,
            "compliance_score": self.compliance.get_compliance_score(agent_id),
            "improvement_trend": self.compliance.get_improvement_trend(agent_id),
            "total_violations": self.compliance.get_violation_count(agent_id),
            "total_successes": self.compliance.get_success_count(agent_id)
        }


# Singleton instance
_reward_bus = None

def get_reward_bus(epos_root: Path = None) -> RewardBus:
    """Get global Reward Bus instance."""
    global _reward_bus
    if _reward_bus is None:
        _reward_bus = RewardBus(epos_root=epos_root)
    return _reward_bus


if __name__ == "__main__":
    # Test the Reward Bus
    print("Testing Reward Bus...")
    
    bus = get_reward_bus()
    
    # Simulate violation event
    test_event = {
        "event_type": "governance.violation_detected",
        "payload": {
            "agent_id": "agent_zero",
            "violations": ["ERR-PATH-001"],
            "file_path": "/mnt/c/Users/Jamie/workspace/epos_mcp/inbox/test.py",
            "mission_id": "TEST_001"
        },
        "metadata": {
            "trace_id": "TEST_TRACE_001"
        }
    }
    
    bus.handle_violation(test_event)
    
    # Check status
    status = bus.get_agent_status("agent_zero")
    print(f"\nAgent Status:")
    print(f"  Compliance Score: {status['compliance_score']:.1%}")
    print(f"  Total Violations: {status['total_violations']}")
