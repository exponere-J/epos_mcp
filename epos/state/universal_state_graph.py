#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/state/universal_state_graph.py — EPOS Universal State Graph
=================================================================
Constitutional Authority: EPOS Constitution v3.1

The organism's bloodstream. Every EPOS node reads and writes to a shared
state document (organism_state.json) that represents the complete current
condition of the organism. State changes propagate to the Event Bus so
downstream nodes react in real time.

One stimulus, full-body response.

Public API:
    state = OrganismState()
    state.update("health.overall", "nominal")
    val = state.query("health.overall")        # → "nominal"
    state.subscribe("health.overall", fn)      # → called on each update
    state.snapshot()                           # → full dict
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ── Paths ──────────────────────────────────────────────────────
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
STATE_FILE = EPOS_ROOT / "context_vault" / "state" / "organism_state.json"

# ── Default initial state ──────────────────────────────────────
DEFAULT_STATE: Dict[str, Any] = {
    "meta": {
        "schema_version": "1.0",
        "created_at": None,
        "last_updated": None,
        "session_count": 0,
    },
    "health": {
        "overall": "nominal",
        "doctor_last_run": None,
        "checks_passed": 0,
        "checks_warned": 0,
        "checks_failed": 0,
        "nodes": {},
    },
    "intelligence_layer": {
        "models_seated": [],
        "models_pending": [],
        "last_upskill": None,
        "upskill_phases_complete": 0,
        "research_scanner_last_run": None,
    },
    "content_lab": {
        "echolocation_score": 67.3,
        "avatars_active": 0,
        "content_queued": 0,
        "content_published_today": 0,
        "fotw_signals_today": 0,
    },
    "pipeline": {
        "missions_active": [],
        "missions_completed_today": 0,
        "missions_blocked": [],
        "daemon_jobs": 0,
        "last_daemon_heartbeat": None,
    },
    "sovereignty": {
        "nodes_marketplace_ready": 9,
        "nodes_total": 0,
        "certifier_last_run": None,
        "governance_gate_blocks_today": 0,
        "governance_gate_approvals_today": 0,
    },
    "training": {
        "qlora_queue_depth": 0,
        "last_training_cycle": None,
        "reward_signals_today": 0,
        "models_in_training": [],
    },
    "event_bus": {
        "total_events": 0,
        "events_today": 0,
        "last_event_at": None,
        "bus_size_kb": 0.0,
    },
}


class OrganismState:
    """
    Thread-safe shared state layer for the EPOS organism.

    State is persisted to organism_state.json on every update.
    Every update publishes an event to the EPOS Event Bus so
    subscribers and downstream reactors can respond.
    """

    _lock = threading.Lock()

    def __init__(self, state_file: Optional[Path] = None):
        self._path = state_file or STATE_FILE
        self._subscribers: Dict[str, List[Callable]] = {}
        self._state = self._load_or_init()

        # Wire Event Bus lazily (avoid import-time crash if bus unavailable)
        self._bus = None
        try:
            from epos_event_bus import EPOSEventBus
            self._bus = EPOSEventBus()
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────

    def load(self) -> Dict[str, Any]:
        """Read current organism state from disk."""
        with self._lock:
            self._state = self._read_file()
            return dict(self._state)

    def update(self, path: str, value: Any) -> None:
        """
        Atomically update a nested key and persist + publish the change.

        path: dot-notation key, e.g. "health.overall" or "meta.session_count"
        value: any JSON-serialisable value
        """
        with self._lock:
            self._set_nested(self._state, path, value)
            self._state["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._write_file(self._state)

        self._notify_subscribers(path, value)
        self._publish_event(path, value)
        # Redundancy: snapshot after every write (lazy import to avoid circular)
        try:
            from epos.state.state_redundancy import snapshot_state
            snapshot_state()
        except Exception:
            pass  # Redundancy layer absent — non-fatal

    def query(self, path: str) -> Any:
        """Read any nested key. Returns None if the path does not exist."""
        with self._lock:
            return self._get_nested(self._state, path)

    def subscribe(self, path: str, callback: Callable[[str, Any], None]) -> None:
        """
        Register a callback that fires whenever a path (or sub-path) is updated.

        callback signature: fn(path: str, new_value: Any)

        Note: callbacks are called from the thread that called update().
        For heavy work, dispatch to a background thread inside the callback.
        """
        if path not in self._subscribers:
            self._subscribers[path] = []
        self._subscribers[path].append(callback)

    def snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of the full state."""
        with self._lock:
            return json.loads(json.dumps(self._state))

    def increment(self, path: str, by: int = 1) -> int:
        """Increment an integer counter at path. Returns new value."""
        with self._lock:
            current = self._get_nested(self._state, path) or 0
            new_val = current + by
            self._set_nested(self._state, path, new_val)
            self._state["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._write_file(self._state)
        self._notify_subscribers(path, new_val)
        self._publish_event(path, new_val)
        return new_val

    # ── Internals ─────────────────────────────────────────────

    def _load_or_init(self) -> Dict[str, Any]:
        if self._path.exists():
            try:
                data = self._read_file()
                # Merge any new DEFAULT_STATE keys not yet in the file
                merged = _deep_merge(DEFAULT_STATE, data)
                return merged
            except Exception:
                pass
        # First-time init
        state = json.loads(json.dumps(DEFAULT_STATE))
        state["meta"]["created_at"] = datetime.now(timezone.utc).isoformat()
        state["meta"]["last_updated"] = state["meta"]["created_at"]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._write_file(state)
        return state

    def _read_file(self) -> Dict[str, Any]:
        return json.loads(self._path.read_text())

    def _write_file(self, state: Dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2))
        tmp.replace(self._path)  # atomic rename

    def _get_nested(self, d: Dict, path: str) -> Any:
        keys = path.split(".")
        cur = d
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

    def _set_nested(self, d: Dict, path: str, value: Any) -> None:
        keys = path.split(".")
        cur = d
        for k in keys[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]
        cur[keys[-1]] = value

    def _notify_subscribers(self, path: str, value: Any) -> None:
        for sub_path, callbacks in self._subscribers.items():
            if path == sub_path or path.startswith(sub_path + "."):
                for cb in callbacks:
                    try:
                        cb(path, value)
                    except Exception:
                        pass

    def _publish_event(self, path: str, value: Any) -> None:
        if self._bus is None:
            return
        try:
            self._bus.publish(
                f"organism.state.updated",
                {"path": path, "value": value},
                source_module="universal_state_graph",
            )
        except Exception:
            pass


# ── Helpers ───────────────────────────────────────────────────

def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Merge override into base, preserving nested structure."""
    result = json.loads(json.dumps(base))
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ── Self-test ─────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        test_file = Path(tmp) / "state" / "organism_state.json"
        state = OrganismState(state_file=test_file)

        # Test update + query
        state.update("health.overall", "nominal")
        assert state.query("health.overall") == "nominal", "update/query failed"

        # Test nested creation
        state.update("health.nodes.epos_core", "healthy")
        assert state.query("health.nodes.epos_core") == "healthy"

        # Test subscribe
        received = []
        state.subscribe("health.overall", lambda p, v: received.append(v))
        state.update("health.overall", "degraded")
        assert received == ["degraded"], f"subscribe failed: {received}"

        # Test increment
        state.update("meta.session_count", 0)
        new_val = state.increment("meta.session_count")
        assert new_val == 1

        # Test persistence
        state2 = OrganismState(state_file=test_file)
        assert state2.query("health.overall") == "degraded"

        print("PASS: OrganismState — all assertions passed")
