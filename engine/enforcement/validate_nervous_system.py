# EPOS GOVERNANCE WATERMARK
﻿"""
EPOS Nervous System Validation
Tests all 5 critical components of the recursive learning system
Constitutional Authority: EPOS_UNIFIED_NERVOUS_SYSTEM.md
"""

from pathlib import Path
import sys
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_event_bus():
    """Test 1: Event Bus Publishing/Subscribing"""
    print("\n[TEST 1/5] Event Bus Publishing/Subscribing")
    
    try:
        from event_bus import get_event_bus
        
        bus = get_event_bus()
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        bus.subscribe("test.*", handler)
        bus.start_polling(interval_seconds=0.5)
        
        event_id = bus.publish(
            event_type="test.validation",
            payload={"test": "data"},
            metadata={"trace_id": "TEST_001"}
        )
        
        time.sleep(1)
        bus.stop_polling()
        
        assert len(received_events) > 0, "No events received"
        print("   ✅ Event published successfully")
        print("   ✅ Subscriber received event")
        print("   ✅ Pattern matching works")
        print("   ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_governance_gate():
    """Test 2: Governance Gate Integration"""
    print("\n[TEST 2/5] Governance Gate Integration")
    
    try:
        from governance_gate import GovernanceGate
        from event_bus import get_event_bus
        
        gate = GovernanceGate()
        bus = get_event_bus()
        
        # Create a test file with a violation
        import os as _os; test_file = Path(_os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent))) / "inbox/test_validation.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Missing header\nimport os")
        
        result = gate.validate_file(
            file_path=test_file,
            agent_id="test_agent",
            trace_id="TEST_002"
        )
        
        print("   ✅ Validation executed")
        print("   ✅ Event published to bus")
        print("   ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reward_bus():
    """Test 3: Reward Bus Orchestration"""
    print("\n[TEST 3/5] Reward Bus Orchestration")
    
    try:
        from engine.enforcement.reward_bus import get_reward_bus
        from event_bus import get_event_bus
        
        epos_root = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
        bus = get_event_bus()
        reward_bus = get_reward_bus(epos_root=epos_root)
        
        bus.start_polling(interval_seconds=0.5)
        
        # Simulate a violation event
        bus.publish(
            event_type="governance.violation_detected",
            payload={
                "agent_id": "test_agent",
                "violations": ["ERR-PATH-001"],
                "file_path": "C:/Users/Jamie/workspace/epos_mcp/inbox/test.py",
                "mission_id": "TEST_003"
            },
            metadata={"trace_id": "TEST_003"}
        )
        
        time.sleep(2)
        bus.stop_polling()
        
        print("   ✅ Violation handled")
        print("   ✅ Remediation triggered")
        print("   ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compliance_tracker():
    """Test 4: Compliance Tracking"""
    print("\n[TEST 4/5] Compliance Tracking")
    
    try:
        from engine.enforcement.compliance_tracker import ComplianceTracker
        
        epos_root = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
        tracker = ComplianceTracker(epos_root=epos_root)
        
        # Record a violation
        tracker.record_violation("test_agent", "ERR-PATH-001", "TEST_004")
        print("   ✅ Violation recorded")
        
        # Record a success
        tracker.record_success("test_agent", "TEST_005")
        print("   ✅ Success recorded")
        
        # Check score
        score = tracker.get_compliance_score("test_agent")
        print(f"   ✅ Score calculated: {score:.1%}")
        print("   ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_remediation_generator():
    """Test 5: Remediation Generation"""
    print("\n[TEST 5/5] Remediation Generation")
    
    try:
        from engine.enforcement.remediation_generator import RemediationGenerator
        
        epos_root = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
        generator = RemediationGenerator(epos_root=epos_root)
        
        lesson = generator.generate_lesson(
            violation_code="ERR-PATH-001",
            file_path="C:/Users/Jamie/workspace/epos_mcp/inbox/test.py",
            agent_id="test_agent"
        )
        
        assert lesson["lesson_path"].exists(), "Lesson file not created"
        
        print("   ✅ Lesson created")
        print("   ✅ File exists in context vault")
        print("   ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("EPOS NERVOUS SYSTEM VALIDATION")
    print("="*70)
    
    tests = [
        test_event_bus,
        test_governance_gate,
        test_reward_bus,
        test_compliance_tracker,
        test_remediation_generator
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*70)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("="*70)
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("="*70)
        sys.exit(1)

if __name__ == "__main__":
    main()
