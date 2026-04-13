#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
thread_tracker.py — Friday Thread Tracker
==========================================
Constitutional Authority: EPOS Constitution v3.1

Tracks open work threads in context_vault/friday/threads/.
A thread is any multi-step work item that spans sessions.

Operations:
  open(title, description, tags)  — create a new thread
  update(thread_id, note)         — append a progress note
  close(thread_id, resolution)    — mark complete
  stale()                         — list threads open > threshold hours
  summary()                       — all open threads as text
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from path_utils import get_context_vault

VAULT = get_context_vault()
THREADS_DIR = VAULT / "friday" / "threads"
THREADS_DIR.mkdir(parents=True, exist_ok=True)

STALE_THRESHOLD_HOURS = int(__import__("os").getenv("THREAD_STALE_HOURS", "48"))


def open_thread(title: str, description: str = "", tags: list = None) -> dict:
    """Create a new open thread."""
    thread_id = f"THR-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    thread = {
        "id": thread_id,
        "title": title,
        "description": description,
        "tags": tags or [],
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "notes": [],
        "resolution": None,
    }
    _save(thread_id, thread)
    return thread


def update_thread(thread_id: str, note: str) -> dict:
    """Append a progress note to an existing thread."""
    thread = _load(thread_id)
    if not thread:
        raise ValueError(f"Thread {thread_id} not found")
    thread["notes"].append({
        "text": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    thread["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save(thread_id, thread)
    return thread


def close_thread(thread_id: str, resolution: str = "") -> dict:
    """Mark a thread as closed."""
    thread = _load(thread_id)
    if not thread:
        raise ValueError(f"Thread {thread_id} not found")
    thread["status"] = "closed"
    thread["resolution"] = resolution
    thread["closed_at"] = datetime.now(timezone.utc).isoformat()
    thread["updated_at"] = thread["closed_at"]
    _save(thread_id, thread)
    return thread


def list_open() -> list:
    """Return all open threads."""
    return [t for t in _all() if t.get("status") == "open"]


def list_stale() -> list:
    """Return open threads not updated in > STALE_THRESHOLD_HOURS."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=STALE_THRESHOLD_HOURS)
    stale = []
    for t in list_open():
        updated = _parse_ts(t.get("updated_at", ""))
        if updated < cutoff:
            stale.append(t)
    return stale


def summary() -> str:
    """Return open threads as a compact text block."""
    threads = list_open()
    if not threads:
        return "No open threads."
    lines = [f"Open threads ({len(threads)}):"]
    for t in threads:
        age_h = _age_hours(t.get("updated_at", ""))
        stale_flag = " [STALE]" if age_h and age_h > STALE_THRESHOLD_HOURS else ""
        lines.append(f"  {t['id']}: {t['title']}{stale_flag} (updated {age_h:.0f}h ago)")
    return "\n".join(lines)


# ── Helpers ──────────────────────────────────────────────────

def _save(thread_id: str, thread: dict):
    path = THREADS_DIR / f"{thread_id}.json"
    path.write_text(json.dumps(thread, indent=2), encoding="utf-8")


def _load(thread_id: str) -> dict:
    path = THREADS_DIR / f"{thread_id}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _all() -> list:
    threads = []
    for p in THREADS_DIR.glob("THR-*.json"):
        try:
            threads.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return sorted(threads, key=lambda t: t.get("updated_at", ""), reverse=True)


def _parse_ts(ts: str) -> datetime:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _age_hours(ts: str) -> float:
    dt = _parse_ts(ts)
    if dt == datetime.min.replace(tzinfo=timezone.utc):
        return 9999.0
    return (datetime.now(timezone.utc) - dt).total_seconds() / 3600


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    t = open_thread("Test thread", description="Testing thread tracker", tags=["test"])
    assert t["status"] == "open"
    print(f"Opened: {t['id']}")
    passed += 1

    t2 = update_thread(t["id"], "Progress note 1")
    assert len(t2["notes"]) == 1
    passed += 1

    t3 = close_thread(t["id"], resolution="Test complete")
    assert t3["status"] == "closed"
    passed += 1

    print(summary())
    passed += 1

    print(f"\nPASS: thread_tracker ({passed} assertions)")
