# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/event_bus.py
"""
EPOS Unified Event Bus - The Nervous System
Constitutional Authority: Article VII (Context Governance)

This is the core integration layer that enables event-driven communication
between all EPOS components without tight coupling.

Usage:
    from engine.event_bus import get_event_bus
    
    bus = get_event_bus()
    
    # Publish an event
    event_id = bus.publish(
        event_type="governance.violation_detected",
        payload={"file_path": "...", "violations": [...]},
        metadata={"trace_id": "TRACE_001"}
    )
    
    # Subscribe to events
    def handle_violation(event):
        print(f"Violation detected: {event['payload']}")
    
    bus.subscribe("governance.*", handle_violation)
    bus.start_polling()
"""

from pathlib import Path
from datetime import datetime
import json
import os
import threading
import time
try:
    import fcntl
except ImportError:
    fcntl = None  # Windows — file locking handled via threading lock
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class EventType(Enum):
    """Standard event types in EPOS system."""
    
    # Governance events
    GOVERNANCE_VIOLATION_DETECTED = "governance.violation_detected"
    GOVERNANCE_VALIDATION_PASSED = "governance.validation_passed"
    GOVERNANCE_RECEIPT_GENERATED = "governance.receipt_generated"
    
    # Learning events
    LEARNING_REMEDIATION_GENERATED = "learning.remediation_generated"
    LEARNING_EXERCISE_ASSIGNED = "learning.exercise_assigned"
    LEARNING_EXERCISE_COMPLETED = "learning.exercise_completed"
    LEARNING_IMPROVEMENT_DETECTED = "learning.improvement_detected"
    
    # Context events
    CONTEXT_INJECTED = "context.injected"
    CONTEXT_STORED = "context.stored"
    CONTEXT_SEARCHED = "context.searched"
    
    # Diagnostic events
    DIAGNOSTIC_STARTED = "diagnostic.started"
    DIAGNOSTIC_ENGAGEMENT_CREATED = "diagnostic.engagement_created"
    DIAGNOSTIC_PRICING_CALCULATED = "diagnostic.pricing_calculated"
    
    # Agent events
    AGENT_MISSION_STARTED = "agent.mission_started"
    AGENT_MISSION_COMPLETED = "agent.mission_completed"
    AGENT_MISSION_FAILED = "agent.mission_failed"
    AGENT_LEARNING_APPLIED = "agent.learning_applied"


@dataclass
class EPOSEvent:
    """Standard event structure for EPOS system."""
    
    event_id: str
    event_type: str
    timestamp: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    source_server: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EPOSEvent':
        return cls(**data)


class EPOSEventBus:
    """
    Shared Event Log implementation for inter-component communication.
    
    Uses JSONL file as persistent event store.
    Components publish events, subscribers poll for new events.
    
    Constitutional Authority: Article VII (Context Governance)
    """
    
    # Default paths (Windows absolute per PATH_CLARITY_RULES.md)
    DEFAULT_EVENT_LOG = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent))) / "context_vault/events/system_events.jsonl"
    DEFAULT_EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent)))
    
    def __init__(self, event_log_path: Path = None):
        """
        Initialize the event bus.
        
        Args:
            event_log_path: Optional custom path for event log.
                           Defaults to context_vault/events/system_events.jsonl
        """
        # Use environment variable or default
        epos_root = Path(os.getenv("EPOS_ROOT", str(self.DEFAULT_EPOS_ROOT)))
        
        self.event_log = event_log_path or (epos_root / "context_vault" / "events" / "system_events.jsonl")
        self.event_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Subscriber registry: pattern -> list of handlers
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # Position tracking for polling
        self._last_position = 0
        self._running = False
        self._poll_thread: Optional[threading.Thread] = None
        
        # Lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Event ID counter for uniqueness
        self._event_counter = 0
    
    def publish(
        self, 
        event_type: str, 
        payload: Dict[str, Any], 
        metadata: Dict[str, Any] = None,
        source_server: str = None
    ) -> str:
        """
        Publish event to shared log.
        
        Args:
            event_type: Type of event (e.g., "governance.violation_detected")
            payload: Event data
            metadata: Optional metadata (trace_id, correlation_id, etc.)
            source_server: Optional identifier for publishing server
        
        Returns:
            event_id for correlation
        """
        with self._lock:
            self._event_counter += 1
            event_id = f"EVT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._event_counter:04d}"
        
        event = EPOSEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            payload=payload,
            metadata=metadata or {},
            source_server=source_server
        )
        
        # Atomic append with file locking (prevents FM-NS-001)
        self._write_event(event)
        
        return event_id
    
    def _write_event(self, event: EPOSEvent):
        """
        Write event to log file with atomic append.
        
        Uses file locking to prevent concurrent write issues (FM-NS-001).
        """
        try:
            with self._lock:
                with open(self.event_log, "a", encoding="utf-8") as f:
                    if fcntl is not None:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        except OSError:
                            pass

                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
                    f.flush()

                    if fcntl is not None:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        except OSError:
                            pass
                    
        except Exception as e:
            # Log error but don't crash - event bus must be resilient
            print(f"[EventBus] Error writing event: {e}")
    
    def subscribe(self, event_pattern: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to events matching pattern.
        
        Pattern examples:
        - "governance.*" - All governance events
        - "governance.violation_detected" - Specific event
        - "*" - All events
        
        Args:
            event_pattern: Pattern to match event types
            handler: Callback function that receives the event dict
        """
        with self._lock:
            if event_pattern not in self.subscribers:
                self.subscribers[event_pattern] = []
            self.subscribers[event_pattern].append(handler)
    
    def unsubscribe(self, event_pattern: str, handler: Callable = None):
        """
        Unsubscribe from events.
        
        Args:
            event_pattern: Pattern to unsubscribe from
            handler: Specific handler to remove (or None for all handlers)
        """
        with self._lock:
            if event_pattern in self.subscribers:
                if handler is None:
                    del self.subscribers[event_pattern]
                else:
                    self.subscribers[event_pattern] = [
                        h for h in self.subscribers[event_pattern] if h != handler
                    ]
    
    def start_polling(self, interval_seconds: float = 1.0):
        """
        Start background polling for new events.
        
        Args:
            interval_seconds: How often to poll (default 1 second)
        """
        if self._running:
            return
        
        self._running = True
        
        # Initialize position to end of file (don't replay old events)
        if self.event_log.exists():
            self._last_position = self.event_log.stat().st_size
        
        def poll_loop():
            while self._running:
                try:
                    self._process_new_events()
                except Exception as e:
                    print(f"[EventBus] Error in poll loop: {e}")
                time.sleep(interval_seconds)
        
        self._poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop_polling(self):
        """Stop background polling."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5.0)
            self._poll_thread = None
    
    def _process_new_events(self):
        """Process events added since last poll."""
        if not self.event_log.exists():
            return
        
        with open(self.event_log, "r", encoding="utf-8") as f:
            f.seek(self._last_position)
            new_lines = f.readlines()
            self._last_position = f.tell()
        
        for line in new_lines:
            line = line.strip()
            if line:
                try:
                    event = json.loads(line)
                    self._dispatch_event(event)
                except json.JSONDecodeError as e:
                    print(f"[EventBus] Invalid JSON in event log: {e}")
    
    def _dispatch_event(self, event: Dict[str, Any]):
        """Dispatch event to matching subscribers."""
        event_type = event.get("event_type", "")
        
        with self._lock:
            patterns = list(self.subscribers.keys())
        
        for pattern in patterns:
            if self._pattern_matches(pattern, event_type):
                with self._lock:
                    handlers = list(self.subscribers.get(pattern, []))
                
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        # Log but don't crash on handler errors
                        print(f"[EventBus] Handler error for {event_type}: {e}")
    
    def _pattern_matches(self, pattern: str, event_type: str) -> bool:
        """
        Check if event type matches subscription pattern.
        
        Args:
            pattern: Subscription pattern (e.g., "governance.*")
            event_type: Actual event type (e.g., "governance.violation_detected")
        
        Returns:
            True if pattern matches event type
        """
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + ".")
        return pattern == event_type
    
    def get_events_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a specific trace ID.
        
        Useful for debugging and correlation.
        
        Args:
            trace_id: The trace ID to search for
        
        Returns:
            List of events with matching trace_id
        """
        events = []
        
        if not self.event_log.exists():
            return events
        
        with open(self.event_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        if event.get("metadata", {}).get("trace_id") == trace_id:
                            events.append(event)
                    except json.JSONDecodeError:
                        pass
        
        return events
    
    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent events.
        
        Args:
            count: Number of events to return
        
        Returns:
            List of most recent events
        """
        events = []
        
        if not self.event_log.exists():
            return events
        
        with open(self.event_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for line in lines[-count:]:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        return events
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check event bus health.
        
        Returns:
            Health status dict
        """
        return {
            "status": "healthy",
            "event_log_path": str(self.event_log),
            "event_log_exists": self.event_log.exists(),
            "event_log_size_bytes": self.event_log.stat().st_size if self.event_log.exists() else 0,
            "subscriber_count": sum(len(h) for h in self.subscribers.values()),
            "polling_active": self._running
        }


# Singleton instance
_event_bus: Optional[EPOSEventBus] = None
_event_bus_lock = threading.Lock()


def get_event_bus(event_log_path: Path = None) -> EPOSEventBus:
    """
    Get global event bus instance (singleton).
    
    Args:
        event_log_path: Optional custom path (only used on first call)
    
    Returns:
        EPOSEventBus instance
    """
    global _event_bus
    
    with _event_bus_lock:
        if _event_bus is None:
            _event_bus = EPOSEventBus(event_log_path)
        return _event_bus


def reset_event_bus():
    """Reset the singleton (useful for testing)."""
    global _event_bus
    
    with _event_bus_lock:
        if _event_bus:
            _event_bus.stop_polling()
        _event_bus = None


# Convenience functions for common event types
def publish_violation(
    file_path: str,
    violations: List[str],
    agent_id: str = None,
    mission_id: str = None,
    trace_id: str = None
) -> str:
    """Convenience function to publish a governance violation event."""
    bus = get_event_bus()
    return bus.publish(
        event_type=EventType.GOVERNANCE_VIOLATION_DETECTED.value,
        payload={
            "file_path": file_path,
            "violations": violations,
            "agent_id": agent_id,
            "mission_id": mission_id
        },
        metadata={"trace_id": trace_id} if trace_id else {},
        source_server="governance_server"
    )


def publish_remediation(
    lesson_path: str,
    lesson_id: str,
    agent_id: str,
    violations: List[str],
    trace_id: str = None
) -> str:
    """Convenience function to publish a remediation generated event."""
    bus = get_event_bus()
    return bus.publish(
        event_type=EventType.LEARNING_REMEDIATION_GENERATED.value,
        payload={
            "lesson_path": lesson_path,
            "lesson_id": lesson_id,
            "agent_id": agent_id,
            "violations": violations
        },
        metadata={"trace_id": trace_id} if trace_id else {},
        source_server="learning_server"
    )


def publish_context_injected(
    agent_id: str,
    context_type: str,
    content_summary: str,
    trace_id: str = None
) -> str:
    """Convenience function to publish a context injected event."""
    bus = get_event_bus()
    return bus.publish(
        event_type=EventType.CONTEXT_INJECTED.value,
        payload={
            "agent_id": agent_id,
            "context_type": context_type,
            "content_summary": content_summary
        },
        metadata={"trace_id": trace_id} if trace_id else {},
        source_server="context_server"
    )


if __name__ == "__main__":
    # Self-test
    import sys
    
    print("EPOS Event Bus Self-Test")
    print("=" * 50)
    
    # Create test bus
    test_log = Path("/tmp/epos_test_events.jsonl")
    if test_log.exists():
        test_log.unlink()
    
    bus = EPOSEventBus(test_log)
    
    # Test 1: Publish event
    print("\n1. Testing publish...")
    event_id = bus.publish(
        event_type="test.event",
        payload={"message": "Hello from test"},
        metadata={"trace_id": "TEST_TRACE_001"}
    )
    print(f"   Published event: {event_id}")
    
    # Test 2: Subscribe and receive
    print("\n2. Testing subscribe...")
    received_events = []
    
    def test_handler(event):
        received_events.append(event)
        print(f"   Received: {event['event_type']}")
    
    bus.subscribe("test.*", test_handler)
    bus.start_polling(interval_seconds=0.5)
    
    # Publish another event
    bus.publish(
        event_type="test.second",
        payload={"message": "Second event"},
        metadata={"trace_id": "TEST_TRACE_001"}
    )
    
    # Wait for poll
    time.sleep(1)
    
    print(f"   Received {len(received_events)} events via subscription")
    
    # Test 3: Trace correlation
    print("\n3. Testing trace correlation...")
    trace_events = bus.get_events_by_trace("TEST_TRACE_001")
    print(f"   Found {len(trace_events)} events for trace TEST_TRACE_001")
    
    # Test 4: Health check
    print("\n4. Testing health check...")
    health = bus.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Subscribers: {health['subscriber_count']}")
    print(f"   Polling: {health['polling_active']}")
    
    # Cleanup
    bus.stop_polling()
    
    print("\n" + "=" * 50)
    print("Self-test complete!")
    
    sys.exit(0)
