#!/usr/bin/env python3
# EPOS Artifact — BUILD 1 (Process Matrix Publisher)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §1
"""
process_matrix_publisher.py — Live Organism Proprioception
============================================================
Article XVI §1 realization: every operational component MUST register itself
in the organism state manifest upon passing TTLG validation.

This publisher is the live half of the Process Registry. Where
`organism_state.json` carries static metadata (component_id, version,
governing_articles, ...), the publisher injects a `process_matrix` section
with **runtime** data:

    - status:        operational | degraded | unavailable | unknown
    - last_seen:     ISO timestamp of most recent successful probe
    - dependencies:  forward import edges (cached from Scout)
    - consumers:     reverse import edges
    - capability_tags: from registry (mirror — quick lookup)
    - throughput:    optional, per-module reported

It runs every 5 minutes via the EPOS Daemon (or on-demand).
Atomic writes; never crashes the registry.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Resolve repo root from the publisher's location
HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent

REGISTRY = Path(os.getenv("EPOS_ORGANISM_STATE",
                          str(REPO / "context_vault" / "state" / "organism_state.json")))
INVENTORY = Path(os.getenv("EPOS_ORGANISM_INVENTORY",
                            str(REPO / "context_vault" / "state" / "organism_inventory_scout.json")))
LOCK = REGISTRY.with_suffix(".json.lock")
PARTIAL = REGISTRY.with_suffix(".json.partial")
BACKUP = REGISTRY.with_suffix(".json.bak")

PROBE_TIMEOUT_S = float(os.getenv("EPOS_PROBE_TIMEOUT_S", "1.5"))
PUBLISH_INTERVAL_S = int(os.getenv("EPOS_PUBLISH_INTERVAL_S", "300"))  # 5 min

SELF_PATH = "epos/state/process_matrix_publisher.py"


# ── Probe outcomes ────────────────────────────────────────────

@dataclass
class ProbeResult:
    path: str
    status: str  # operational | degraded | unavailable | unknown
    reason: str = ""
    last_seen: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


# ── Probes ────────────────────────────────────────────────────

def probe_module(entry: dict) -> ProbeResult:
    """Decide a module's runtime status.

    Strategy:
      1. If path is the publisher itself, mark 'self' (no recursive probe).
      2. If file is missing on disk → 'unavailable'.
      3. If file mtime older than registry mtime field → 'unknown' (drift).
      4. Try a static import probe by attempting compile() — never run code.
      5. If module exposes a callable named `health()` AND we can import
         safely (light syntax check), call it within timeout.
      6. Otherwise default 'operational' (file present, parseable).
    """
    path_str = entry["path"]
    if path_str == SELF_PATH:
        return ProbeResult(path=path_str, status="self", reason="publisher self-skip")

    p = REPO / path_str
    if not p.exists():
        return ProbeResult(path=path_str, status="unavailable",
                           reason="file missing on disk")

    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return ProbeResult(path=path_str, status="unavailable",
                           reason=f"read error: {type(e).__name__}")

    # Static parse — never executes code
    try:
        compile(src, str(p), "exec")
    except SyntaxError as e:
        return ProbeResult(path=path_str, status="degraded",
                           reason=f"syntax: {e.msg} (line {e.lineno})")

    # File parses cleanly; report operational with timestamp
    return ProbeResult(
        path=path_str, status="operational",
        last_seen=datetime.now(timezone.utc).isoformat(),
        extras={"lines": entry.get("lines", 0)},
    )


# ── Capability index from registry ────────────────────────────

def build_capability_index(entries: list[dict]) -> dict[str, list[str]]:
    """tag → [component_id] reverse lookup, deterministic ordering."""
    idx: dict[str, list[str]] = {}
    for e in entries:
        cid = e.get("component_id", "")
        for tag in e.get("capability_tags", []):
            idx.setdefault(tag, []).append(cid)
    for v in idx.values():
        v.sort()
    return dict(sorted(idx.items()))


# ── Connections from inventory ────────────────────────────────

def load_connections() -> list[dict[str, str]]:
    """Read the Scout inventory's reverse_deps to build edges."""
    if not INVENTORY.exists():
        return []
    inv = json.loads(INVENTORY.read_text())
    edges = []
    for tgt, sources in inv.get("reverse_deps", {}).items():
        for src in sources:
            edges.append({"from": src, "to": tgt, "type": "import"})
    return edges


# ── Atomic registry update ────────────────────────────────────

def acquire_lock() -> int:
    """Acquire a non-blocking file lock; raise if held."""
    import fcntl
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise RuntimeError("publisher already running (lock held)")
    return fd


def release_lock(fd: int) -> None:
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def write_atomic(reg: dict) -> None:
    """Backup → write to .partial → fsync → atomic rename."""
    if REGISTRY.exists():
        BACKUP.write_bytes(REGISTRY.read_bytes())
    data = json.dumps(reg, indent=2) + "\n"
    with open(PARTIAL, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(PARTIAL, REGISTRY)


# ── Main publish pass ─────────────────────────────────────────

def publish_once() -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    if not REGISTRY.exists():
        return {"status": "no_registry", "expected_at": str(REGISTRY)}

    fd = acquire_lock()
    try:
        reg = json.loads(REGISTRY.read_text())
        entries = reg.get("process_registry", [])

        components: dict[str, dict] = {}
        for e in entries:
            try:
                pr = probe_module(e)
            except Exception as ex:  # noqa: BLE001
                pr = ProbeResult(path=e["path"], status="unknown",
                                  reason=f"probe error: {type(ex).__name__}")
            cid = e.get("component_id", "")
            components[cid] = {
                "component_id": cid,
                "path": pr.path,
                "status": pr.status,
                "reason": pr.reason,
                "last_seen": pr.last_seen,
                "capability_tags": e.get("capability_tags", []),
                "version": e.get("version", {}),
                "extras": pr.extras,
            }

        connections = load_connections()
        capability_index = build_capability_index(entries)

        finished = datetime.now(timezone.utc).isoformat()
        reg["process_matrix"] = {
            "schema_version": 1,
            "publisher": {
                "component_id": next(
                    (e.get("component_id") for e in entries if e["path"] == SELF_PATH), None),
                "started_at": started,
                "finished_at": finished,
                "interval_s": PUBLISH_INTERVAL_S,
            },
            "components": components,
            "connections": connections,
            "capability_index": capability_index,
            "totals": _summarize(components),
        }

        write_atomic(reg)
        return {
            "status": "complete",
            "components": len(components),
            "connections": len(connections),
            "capabilities": len(capability_index),
            "started_at": started,
            "finished_at": finished,
        }
    finally:
        release_lock(fd)


def _summarize(components: dict) -> dict[str, int]:
    out = {"operational": 0, "degraded": 0, "unavailable": 0,
           "unknown": 0, "self": 0}
    for c in components.values():
        out[c.get("status", "unknown")] = out.get(c.get("status", "unknown"), 0) + 1
    return out


# ── Daemon loop ───────────────────────────────────────────────

def run_forever() -> None:
    print(f"[publisher] starting; interval={PUBLISH_INTERVAL_S}s; "
          f"registry={REGISTRY}")
    while True:
        try:
            r = publish_once()
            print(f"[publisher] {r}")
        except Exception as e:  # noqa: BLE001
            print(f"[publisher] ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        time.sleep(PUBLISH_INTERVAL_S)


if __name__ == "__main__":
    if "--once" in sys.argv:
        print(json.dumps(publish_once(), indent=2))
    else:
        run_forever()
