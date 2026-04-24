#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §1
# File: /mnt/c/Users/Jamie/workspace/epos_mcp/epos/state/registry_reconciler.py
# Directive: FORGE-ORCH-20260423 Stage 0A
"""
registry_reconciler.py — Single-Writer Merger for organism_state.json

Purpose
-------
Parallel Forge subagents write proposed registry entries to
    /tmp/registry_proposals/*.json
Rather than each subagent racing to write organism_state.json directly
(unsafe — corrupts the registry), the Reconciler is the ONE process
authorized to merge proposals into the canonical registry.

Contract
--------
- Subagents write proposal JSON files with shape `{proposal_id,
  subagent_id, proposed_component_id, entry}`. `proposed_component_id`
  may be the literal string "E-NEXT" to request the next available ID.
- Reconciler acquires exclusive fcntl lock on the registry, loads all
  pending proposals, validates each against the schema, detects
  conflicts (same resolved component_id with different content), merges
  non-conflicting entries atomically (.partial → fsync → rename), logs
  every merge, and emits `registry.reconciled`.

Failure modes
-------------
- Lock held by another process → back off, retry with exponential delay
  (4 attempts; give up and queue for next tick)
- Malformed proposal → skip, log to reconciler_log.jsonl, leave file in
  /tmp/registry_proposals/rejected/ for Architect review
- Schema violation → same treatment as malformed
- Content conflict → flag, leave both proposals, do NOT auto-resolve

Public API
----------
    reconcile_once() -> ReconcileResult
    reconcile_daemon(interval_s: int = 60) -> NoReturn
    MIN_REQUIRED_FIELDS  — per-entry schema
"""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ── Paths ───────────────────────────────────────────────────────

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
REGISTRY = Path(os.getenv(
    "EPOS_ORGANISM_STATE",
    str(REPO / "context_vault" / "state" / "organism_state.json"),
))
PROPOSALS_DIR = Path(os.getenv(
    "EPOS_REGISTRY_PROPOSALS",
    "/tmp/registry_proposals",
))
PROCESSED_DIR = PROPOSALS_DIR / "processed"
REJECTED_DIR = PROPOSALS_DIR / "rejected"
CONFLICTS_DIR = PROPOSALS_DIR / "conflicts"
RECONCILER_LOG = Path(os.getenv(
    "EPOS_RECONCILER_LOG",
    str(REPO / "context_vault" / "state" / "reconciler_log.jsonl"),
))
LOCK_FILE = REGISTRY.with_suffix(".json.reconciler.lock")
PARTIAL = REGISTRY.with_suffix(".json.reconciler.partial")
BACKUP = REGISTRY.with_suffix(".json.reconciler.bak")

# ── Schema ──────────────────────────────────────────────────────

MIN_REQUIRED_FIELDS: tuple[str, ...] = (
    "component_id",   # E-NNNN (or "E-NEXT" in proposals, resolved by reconciler)
    "path",           # repo-relative path
    "capability_tags",
    "gate_verdict",   # REGISTER | REVISE | REJECT | LEGACY_AUDIT
    "version",        # {"major": int, "minor": int}
)


@dataclass
class ReconcileResult:
    started_at: str
    finished_at: str
    proposals_scanned: int = 0
    merged: int = 0
    rejected: int = 0
    conflicts: int = 0
    lock_contentions: int = 0
    next_component_id: str = ""
    merge_ids: list[str] = field(default_factory=list)
    reject_reasons: list[dict[str, str]] = field(default_factory=list)
    conflict_ids: list[dict[str, str]] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Lock helpers ────────────────────────────────────────────────

def _acquire_lock(retries: int = 4, base_delay_s: float = 0.25) -> int | None:
    """Return open fd on success; None if we gave up."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries):
        fd = os.open(str(LOCK_FILE), os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            os.close(fd)
            time.sleep(base_delay_s * (2 ** attempt))
    return None


def _release_lock(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


# ── Registry I/O ────────────────────────────────────────────────

def _load_registry() -> dict[str, Any]:
    if not REGISTRY.exists():
        return {
            "registry_version": "1.0",
            "process_registry": [],
            "component_id_scheme": {"format": "E-NNNN"},
            "totals": {},
        }
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _write_registry_atomic(reg: dict[str, Any]) -> None:
    data = json.dumps(reg, indent=2) + "\n"
    if REGISTRY.exists():
        BACKUP.write_bytes(REGISTRY.read_bytes())
    with open(PARTIAL, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(PARTIAL, REGISTRY)


def _next_component_id(reg: dict[str, Any],
                        reserved: set[str] | None = None) -> str:
    """Next available E-NNNN, accounting for registry entries AND in-pass reservations."""
    reserved = reserved or set()
    ids_from_reg = [
        int(e.get("component_id", "E-0000").split("-")[1])
        for e in reg.get("process_registry", [])
        if isinstance(e.get("component_id"), str)
        and e["component_id"].startswith("E-")
    ]
    ids_from_reserved = [int(r.split("-")[1]) for r in reserved
                          if r.startswith("E-")]
    max_id = max(ids_from_reg + ids_from_reserved) if (ids_from_reg or ids_from_reserved) else 0
    return f"E-{max_id + 1:04d}"


def _index_by_path(reg: dict[str, Any]) -> dict[str, dict]:
    return {e.get("path", ""): e for e in reg.get("process_registry", [])
            if e.get("path")}


def _index_by_component_id(reg: dict[str, Any]) -> dict[str, dict]:
    return {e.get("component_id", ""): e for e in reg.get("process_registry", [])
            if e.get("component_id")}


# ── Schema validation ──────────────────────────────────────────

def _validate_entry(entry: dict[str, Any]) -> tuple[bool, str]:
    for field_name in MIN_REQUIRED_FIELDS:
        if field_name not in entry:
            return False, f"missing required field: {field_name}"
    cid = entry.get("component_id", "")
    if cid != "E-NEXT" and not (isinstance(cid, str)
                                 and cid.startswith("E-")
                                 and len(cid) == 6):
        return False, f"component_id must be E-NNNN or 'E-NEXT' (got {cid!r})"
    verdict = entry.get("gate_verdict", "")
    if verdict not in ("REGISTER", "REVISE", "REJECT", "LEGACY_AUDIT"):
        return False, f"gate_verdict must be REGISTER/REVISE/REJECT/LEGACY_AUDIT (got {verdict!r})"
    ver = entry.get("version", {})
    if not (isinstance(ver, dict) and "major" in ver and "minor" in ver):
        return False, "version must be {'major': int, 'minor': int}"
    tags = entry.get("capability_tags")
    if not (isinstance(tags, list) and all(isinstance(t, str) for t in tags)):
        return False, "capability_tags must be list[str]"
    return True, ""


# ── Content-equivalence for conflict detection ─────────────────

def _content_hash(entry: dict[str, Any]) -> str:
    """SHA over the content-defining fields, excluding volatile ones."""
    excluded = {"mtime", "validated_at", "version_history", "ttlg"}
    filtered = {k: v for k, v in sorted(entry.items()) if k not in excluded}
    return hashlib.sha256(
        json.dumps(filtered, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


# ── Log writer ─────────────────────────────────────────────────

def _log(record: dict[str, Any]) -> None:
    RECONCILER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RECONCILER_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


# ── Proposal I/O ───────────────────────────────────────────────

def _list_proposals() -> list[Path]:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([p for p in PROPOSALS_DIR.glob("*.json") if p.is_file()])


def _move_to(proposal: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / proposal.name
    # If collision, append timestamp
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        dest = dest_dir / f"{proposal.stem}.{ts}{proposal.suffix}"
    shutil.move(str(proposal), str(dest))


# ── Core reconcile ─────────────────────────────────────────────

def reconcile_once() -> ReconcileResult:
    """One reconciliation pass. Atomic; idempotent; safe under parallel subagent writes."""
    started = datetime.now(timezone.utc).isoformat()
    result = ReconcileResult(started_at=started, finished_at="")

    fd = _acquire_lock()
    if fd is None:
        result.lock_contentions = 1
        result.error = "lock held; retry next tick"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        _log({"kind": "reconcile.skipped", **result.to_dict()})
        return result

    try:
        proposals = _list_proposals()
        result.proposals_scanned = len(proposals)
        if not proposals:
            result.finished_at = datetime.now(timezone.utc).isoformat()
            return result

        reg = _load_registry()
        by_path = _index_by_path(reg)
        by_cid = _index_by_component_id(reg)
        reserved_ids: set[str] = set()  # E-NEXT resolutions within this pass

        for pfile in proposals:
            outcome = _process_proposal(pfile, reg, by_path, by_cid,
                                          reserved_ids, result)
            if outcome == "merged":
                _move_to(pfile, PROCESSED_DIR)
            elif outcome == "conflict":
                _move_to(pfile, CONFLICTS_DIR)
            else:
                _move_to(pfile, REJECTED_DIR)

        # Recompute totals
        _recompute_totals(reg)
        _write_registry_atomic(reg)
        result.next_component_id = _next_component_id(reg)

    except Exception as e:  # noqa: BLE001
        result.error = f"{type(e).__name__}: {e}"
        _log({"kind": "reconcile.error", **result.to_dict()})
    finally:
        _release_lock(fd)

    result.finished_at = datetime.now(timezone.utc).isoformat()
    _log({"kind": "reconcile.complete", **result.to_dict()})
    _emit_event(result)
    return result


def _process_proposal(
    pfile: Path, reg: dict[str, Any],
    by_path: dict[str, dict], by_cid: dict[str, dict],
    reserved_ids: set[str],
    result: ReconcileResult,
) -> str:
    """Return 'merged' | 'conflict' | 'rejected'."""
    try:
        proposal = json.loads(pfile.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        reason = f"invalid json: {e}"
        result.rejected += 1
        result.reject_reasons.append({"file": pfile.name, "reason": reason})
        _log({"kind": "proposal.rejected", "file": pfile.name, "reason": reason})
        return "rejected"

    entry = proposal.get("entry") if "entry" in proposal else proposal
    if not isinstance(entry, dict):
        reason = "proposal missing 'entry' dict"
        result.rejected += 1
        result.reject_reasons.append({"file": pfile.name, "reason": reason})
        return "rejected"

    ok, reason = _validate_entry(entry)
    if not ok:
        result.rejected += 1
        result.reject_reasons.append({"file": pfile.name, "reason": reason})
        _log({"kind": "proposal.rejected", "file": pfile.name, "reason": reason})
        return "rejected"

    # Resolve E-NEXT sentinel (accounts for in-pass reservations)
    if entry["component_id"] == "E-NEXT":
        new_id = _next_component_id(reg, reserved_ids)
        entry["component_id"] = new_id
        reserved_ids.add(new_id)
        # Do NOT pre-register in by_cid; the merge block below handles it.

    cid = entry["component_id"]
    path = entry.get("path", "")

    # Conflict detection
    existing_by_path = by_path.get(path)
    existing_by_cid = by_cid.get(cid) if cid in by_cid else None

    # Case A: cid already in registry with DIFFERENT content
    if existing_by_cid and _content_hash(existing_by_cid) != _content_hash(entry):
        result.conflicts += 1
        result.conflict_ids.append({
            "component_id": cid, "file": pfile.name,
            "reason": "component_id exists with different content",
        })
        _log({"kind": "proposal.conflict", "file": pfile.name,
              "component_id": cid, "reason": "cid reuse with different content"})
        return "conflict"

    # Case B: path already registered under a DIFFERENT cid
    if existing_by_path and existing_by_path.get("component_id") != cid:
        result.conflicts += 1
        result.conflict_ids.append({
            "path": path, "file": pfile.name,
            "existing_cid": existing_by_path.get("component_id"),
            "proposed_cid": cid,
            "reason": "path already registered under different component_id",
        })
        _log({"kind": "proposal.conflict", "file": pfile.name,
              "path": path, "reason": "path reuse with different cid"})
        return "conflict"

    # Merge
    if existing_by_cid:
        # Idempotent — proposed matches existing; just refresh validated_at
        existing_by_cid.setdefault("ttlg", {})["validated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )
    else:
        reg.setdefault("process_registry", []).append(entry)
        by_path[path] = entry
        by_cid[cid] = entry

    result.merged += 1
    result.merge_ids.append(cid)
    _log({"kind": "proposal.merged", "file": pfile.name, "component_id": cid})
    return "merged"


def _recompute_totals(reg: dict[str, Any]) -> None:
    entries = reg.get("process_registry", [])
    verdict_counts = {"REGISTER": 0, "REVISE": 0, "REJECT": 0, "LEGACY_AUDIT": 0}
    comp = {"COMPLIANT": 0, "RETROFIT_REQUIRED": 0, "UNKNOWN": 0, "LEGACY_AUDIT": 0}
    for e in entries:
        verdict_counts[e.get("gate_verdict", "LEGACY_AUDIT")] = (
            verdict_counts.get(e.get("gate_verdict", "LEGACY_AUDIT"), 0) + 1
        )
        comp[e.get("amendment_compliance", "UNKNOWN")] = (
            comp.get(e.get("amendment_compliance", "UNKNOWN"), 0) + 1
        )
    max_id_num = max(
        [int(e.get("component_id", "E-0000").split("-")[1])
         for e in entries if e.get("component_id", "").startswith("E-")] + [0]
    )
    reg["totals"] = {
        "registered": verdict_counts["REGISTER"],
        "revise_pending": verdict_counts["REVISE"],
        "rejected": verdict_counts["REJECT"],
        "legacy_audit": verdict_counts["LEGACY_AUDIT"],
        "compliance": comp,
        "total_components": len(entries),
        "component_id_range": f"E-0001 to E-{max_id_num:04d}",
    }
    entries.sort(key=lambda e: e.get("path", ""))


def _emit_event(result: ReconcileResult) -> None:
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish(
            "registry.reconciled", result.to_dict(),
            source_module="registry_reconciler",
        )
    except Exception:
        pass


def reconcile_daemon(interval_s: int = 60) -> None:
    """Forever loop for systemd/cron-managed invocation."""
    import sys
    print(f"[reconciler] starting daemon; interval={interval_s}s; "
          f"proposals={PROPOSALS_DIR}; registry={REGISTRY}")
    while True:
        try:
            r = reconcile_once()
            if r.proposals_scanned:
                print(f"[reconciler] merged={r.merged} "
                      f"conflicts={r.conflicts} rejected={r.rejected} "
                      f"next_id={r.next_component_id}")
        except Exception as e:  # noqa: BLE001
            print(f"[reconciler] ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        time.sleep(interval_s)


# ── CLI ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--daemon" in sys.argv:
        reconcile_daemon()
    else:
        r = reconcile_once()
        print(json.dumps(r.to_dict(), indent=2))
