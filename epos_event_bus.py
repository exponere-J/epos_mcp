#!/usr/bin/env python3
"""
epos_event_bus.py — EPOS Canonical Cross-Process Event Bus
============================================================
Constitutional Authority: EPOS Constitution v3.1
File: C:/Users/Jamie/workspace/epos_mcp/epos_event_bus.py
# EPOS GOVERNANCE WATERMARK

The nervous system. One JSONL file. All modules publish here.
Any module can subscribe to patterns and react.
No Docker ports. No network. One file. One truth.
"""

import json
import uuid
import re
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault

EVENT_LOG_PATH = get_context_vault() / "events" / "system" / "events.jsonl"
EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


@dataclass
class EPOSEvent:
    event_id: str
    event_type: str
    source_module: str
    trace_id: str
    payload: Dict[str, Any]
    published_at: str
    correlation_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EPOSEvent":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class EPOSEventBus:
    """
    Flat file pub/sub event bus.
    Publish: append event to events.jsonl
    Subscribe: read events.jsonl, filter by pattern
    No ports. No network. Survives restarts.
    """

    def __init__(self, event_log: Path = None):
        self.event_log = event_log or EVENT_LOG_PATH
        self.event_log.parent.mkdir(parents=True, exist_ok=True)

    def publish(self, event_type: str, payload: dict,
                source_module: str,
                trace_id: str = None,
                correlation_id: str = None) -> EPOSEvent:
        """
        Append event to canonical JSONL log.
        Returns the event. Never raises — bus failure
        must not block the publishing module.
        """
        event = EPOSEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            source_module=source_module,
            trace_id=trace_id or f"TRACE-{uuid.uuid4().hex[:8]}",
            payload=payload,
            published_at=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id,
        )
        try:
            with _lock:
                with open(self.event_log, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
                    f.flush()
        except Exception as e:
            # Bus failure must not block publisher
            print(f"[EventBus] Write error (non-fatal): {e}")
        return event

    def subscribe(self, pattern: str,
                  handler: Callable = None,
                  since_minutes: int = 5) -> List[EPOSEvent]:
        """
        Read recent events matching pattern.
        pattern supports wildcard: "content.*" matches all content events.
        Returns list of matching EPOSEvent objects.
        Calls handler(event) for each match if provided.
        """
        events = self._read_recent(since_minutes)
        matched = [e for e in events if self._pattern_match(pattern, e.event_type)]
        if handler:
            for e in matched:
                try:
                    handler(e)
                except Exception:
                    pass
        return matched

    def get_recent(self, event_type: str = None,
                   minutes: int = 60) -> List[EPOSEvent]:
        """
        Pull recent events for dashboard display.
        If event_type provided, filters by pattern.
        """
        events = self._read_recent(minutes)
        if event_type:
            events = [e for e in events if self._pattern_match(event_type, e.event_type)]
        return events

    def replay_from(self, trace_id: str) -> List[EPOSEvent]:
        """
        Replay all events with a given trace_id.
        Complete audit trail for any operation.
        """
        if not self.event_log.exists():
            return []
        events = []
        with open(self.event_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("trace_id") == trace_id:
                        events.append(EPOSEvent.from_dict(data))
                except (json.JSONDecodeError, TypeError):
                    pass
        return events

    def _read_recent(self, minutes: int) -> List[EPOSEvent]:
        """Read events from the last N minutes."""
        if not self.event_log.exists():
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        events = []
        try:
            with open(self.event_log, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        pub_time = datetime.fromisoformat(data["published_at"])
                        if pub_time.tzinfo is None:
                            pub_time = pub_time.replace(tzinfo=timezone.utc)
                        if pub_time >= cutoff:
                            events.append(EPOSEvent.from_dict(data))
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                        pass
        except Exception:
            pass
        return events

    @staticmethod
    def _pattern_match(pattern: str, event_type: str) -> bool:
        """Wildcard pattern matching. 'content.*' matches 'content.spark.created'."""
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + ".")
        return pattern == event_type

    def event_count(self) -> int:
        """Total events in log."""
        if not self.event_log.exists():
            return 0
        with open(self.event_log, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())


if __name__ == "__main__":
    bus = EPOSEventBus()

    # Test 1: Publish 3 events with shared trace
    e1 = bus.publish("content.spark.created",
                     {"niche": "lego_affiliate", "test": True},
                     "test_module")
    e2 = bus.publish("content.script.generated",
                     {"brief_id": "CB-LEGO-001"},
                     "content_lab",
                     trace_id=e1.trace_id)
    e3 = bus.publish("governance.validation.passed",
                     {"script_id": "CB-LEGO-001"},
                     "v1_validation",
                     trace_id=e1.trace_id)

    assert e1.event_id.startswith("EVT-")
    assert e1.trace_id == e2.trace_id == e3.trace_id
    print(f"  Published 3 events, trace: {e1.trace_id}")

    # Test 2: Subscribe to content events
    content_events = bus.get_recent("content.*", minutes=1)
    assert len(content_events) >= 2
    print(f"  Content events (last 1min): {len(content_events)}")

    # Test 3: Replay trace
    trace = bus.replay_from(e1.trace_id)
    assert len(trace) == 3, f"Expected 3, got {len(trace)}"
    print(f"  Trace replay: {len(trace)} events in sequence")

    # Test 4: Total event count
    total = bus.event_count()
    print(f"  Total events in log: {total}")

    print("PASS: EPOSEventBus — 3 events published, trace replay works")
