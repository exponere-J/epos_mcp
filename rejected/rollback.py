# File: C:\Users\Jamie\workspace\epos_mcp\engine\rollback.py
# ═══════════════════════════════════════════════════════════════
# EPOS GOVERNANCE WATERMARK
# ───────────────────────────────────────────────────────────────
# Triage ID:      TRG-20260218-ROLLBACK-V1
# First Submitted: 2026-02-18T07:00:00Z
# Triage Result:   PROMOTED (attempt 1 of 1)
# Promoted At:     2026-02-18T07:00:00Z
# Destination:     engine/rollback.py
# Constitutional:  Article II, V, VI compliant
# Violations:      None
# Watermark Hash:  PENDING_FIRST_TRIAGE
# ═══════════════════════════════════════════════════════════════

"""
EPOS Rollback Authority v1.0 — Snapshot & Restore System

Constitutional Authority: EPOS_CONSTITUTION_v3.1 Article V, VI
Purpose: Any operation can be rolled back within 24 hours.
         Snapshots capture file state before mutations.
         Retention: 30 days.

Usage:
    python rollback.py --snapshot                      # Create system snapshot
    python rollback.py --snapshot --component engine    # Snapshot one component
    python rollback.py --list                          # List available snapshots
    python rollback.py --restore SNAP-20260218-001     # Restore a snapshot
    python rollback.py --restore-file engine/meta_orchestrator.py SNAP-20260218-001
    python rollback.py --prune                         # Remove snapshots > 30 days
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
SNAPSHOT_DIR = EPOS_ROOT / "backups" / "snapshots"
SNAPSHOT_INDEX = SNAPSHOT_DIR / "index.jsonl"
RETENTION_DAYS = 30

# Components that can be individually snapshot/restored
COMPONENTS = {
    "engine": EPOS_ROOT / "engine",
    "content_lab": EPOS_ROOT / "content" / "lab",
    "context_vault": EPOS_ROOT / "context_vault",
    "missions": EPOS_ROOT / "missions",
    "governance": EPOS_ROOT,  # root-level governance files
}

# Files to include when snapshotting root/governance
GOVERNANCE_FILES = [
    "epos_doctor.py", "governance_gate.py", "epos_snapshot.py",
    "EPOS_CONSTITUTION_v3.1.md", "ENVIRONMENT_SPEC.md",
    "COMPONENT_INTERACTION_MATRIX.md", "FAILURE_SCENARIOS.md",
    "PATH_CLARITY_RULES.md", "PRE_FLIGHT_CHECKLIST.md",
    ".env", "requirements.txt", "epos_start.ps1",
]


def _file_hash(filepath: Path) -> str:
    h = hashlib.sha256()
    h.update(filepath.read_bytes())
    return h.hexdigest()[:16]


def _next_snapshot_id() -> str:
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    # Count today's snapshots
    count = 0
    if SNAPSHOT_INDEX.exists():
        for line in SNAPSHOT_INDEX.read_text().splitlines():
            try:
                entry = json.loads(line)
                if entry.get("snapshot_id", "").startswith(f"SNAP-{date_str}"):
                    count += 1
            except json.JSONDecodeError:
                pass
    return f"SNAP-{date_str}-{count + 1:03d}"


# ═══════════════════════════════════════════════════════════════
# SNAPSHOT CREATION
# ═══════════════════════════════════════════════════════════════

def create_snapshot(
    component: Optional[str] = None,
    reason: str = "manual",
) -> Dict[str, Any]:
    """Create a snapshot of specified component or full system.

    Copies files into backups/snapshots/{snapshot_id}/
    Records manifest with file hashes for integrity verification.
    """
    snap_id = _next_snapshot_id()
    snap_dir = SNAPSHOT_DIR / snap_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, str]] = []
    files_copied = 0
    total_bytes = 0

    if component:
        # Single component snapshot
        if component not in COMPONENTS:
            return {"error": f"Unknown component: {component}. Valid: {list(COMPONENTS.keys())}"}

        if component == "governance":
            # Special case: root-level files
            for fname in GOVERNANCE_FILES:
                src = EPOS_ROOT / fname
                if src.exists() and src.is_file():
                    dest = snap_dir / fname
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    manifest.append({
                        "path": fname,
                        "hash": _file_hash(src),
                        "size": src.stat().st_size,
                    })
                    files_copied += 1
                    total_bytes += src.stat().st_size
        else:
            comp_dir = COMPONENTS[component]
            if comp_dir.exists():
                for fp in comp_dir.rglob("*"):
                    if fp.is_file() and not fp.name.startswith(".") and "__pycache__" not in str(fp):
                        rel = fp.relative_to(EPOS_ROOT)
                        dest = snap_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fp, dest)
                        manifest.append({
                            "path": str(rel),
                            "hash": _file_hash(fp),
                            "size": fp.stat().st_size,
                        })
                        files_copied += 1
                        total_bytes += fp.stat().st_size
    else:
        # Full system snapshot
        for comp_name, comp_dir in COMPONENTS.items():
            if comp_name == "governance":
                for fname in GOVERNANCE_FILES:
                    src = EPOS_ROOT / fname
                    if src.exists() and src.is_file():
                        dest = snap_dir / fname
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dest)
                        manifest.append({
                            "path": fname,
                            "hash": _file_hash(src),
                            "size": src.stat().st_size,
                        })
                        files_copied += 1
                        total_bytes += src.stat().st_size
            elif comp_dir.exists():
                for fp in comp_dir.rglob("*"):
                    if fp.is_file() and not fp.name.startswith(".") and "__pycache__" not in str(fp):
                        rel = fp.relative_to(EPOS_ROOT)
                        dest = snap_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fp, dest)
                        manifest.append({
                            "path": str(rel),
                            "hash": _file_hash(fp),
                            "size": fp.stat().st_size,
                        })
                        files_copied += 1
                        total_bytes += fp.stat().st_size

    # Write manifest
    manifest_path = snap_dir / "MANIFEST.json"
    manifest_path.write_text(json.dumps({
        "snapshot_id": snap_id,
        "created_at": datetime.now().isoformat(),
        "component": component or "full_system",
        "reason": reason,
        "files": files_copied,
        "total_bytes": total_bytes,
        "manifest": manifest,
    }, indent=2), encoding="utf-8")

    # Append to index
    SNAPSHOT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_INDEX, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "snapshot_id": snap_id,
            "created_at": datetime.now().isoformat(),
            "component": component or "full_system",
            "reason": reason,
            "files": files_copied,
            "total_bytes": total_bytes,
        }) + "\n")

    return {
        "snapshot_id": snap_id,
        "files": files_copied,
        "total_bytes": total_bytes,
        "location": str(snap_dir),
    }


# ═══════════════════════════════════════════════════════════════
# SNAPSHOT LISTING
# ═══════════════════════════════════════════════════════════════

def list_snapshots() -> List[Dict[str, Any]]:
    """List all available snapshots."""
    if not SNAPSHOT_INDEX.exists():
        return []
    snapshots = []
    for line in SNAPSHOT_INDEX.read_text().splitlines():
        try:
            snapshots.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return sorted(snapshots, key=lambda s: s.get("created_at", ""), reverse=True)


# ═══════════════════════════════════════════════════════════════
# RESTORATION
# ═══════════════════════════════════════════════════════════════

def restore_snapshot(
    snapshot_id: str,
    confirm: bool = False,
) -> Dict[str, Any]:
    """Restore all files from a snapshot.

    Article V: No destructive operations without confirmation.
    """
    snap_dir = SNAPSHOT_DIR / snapshot_id
    manifest_path = snap_dir / "MANIFEST.json"

    if not manifest_path.exists():
        return {"error": f"Snapshot not found: {snapshot_id}"}

    manifest = json.loads(manifest_path.read_text())

    if not confirm:
        return {
            "action": "restore_preview",
            "snapshot_id": snapshot_id,
            "files_to_restore": manifest["files"],
            "created_at": manifest["created_at"],
            "component": manifest["component"],
            "message": "Pass confirm=True or --confirm to execute restore.",
        }

    # Create a pre-restore snapshot first (safety net)
    pre_snap = create_snapshot(
        component=manifest["component"] if manifest["component"] != "full_system" else None,
        reason=f"pre_restore_of_{snapshot_id}",
    )

    restored = 0
    errors = []
    for entry in manifest["manifest"]:
        src = snap_dir / entry["path"]
        dest = EPOS_ROOT / entry["path"]
        if src.exists():
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                restored += 1
            except OSError as exc:
                errors.append({"path": entry["path"], "error": str(exc)})
        else:
            errors.append({"path": entry["path"], "error": "Source missing in snapshot"})

    return {
        "action": "restored",
        "snapshot_id": snapshot_id,
        "files_restored": restored,
        "errors": errors,
        "pre_restore_snapshot": pre_snap["snapshot_id"],
        "message": f"Restored {restored} files. Pre-restore backup: {pre_snap['snapshot_id']}",
    }


def restore_file(
    file_path: str,
    snapshot_id: str,
    confirm: bool = False,
) -> Dict[str, Any]:
    """Restore a single file from a snapshot."""
    snap_dir = SNAPSHOT_DIR / snapshot_id
    src = snap_dir / file_path
    dest = EPOS_ROOT / file_path

    if not src.exists():
        return {"error": f"File {file_path} not found in snapshot {snapshot_id}"}

    if not confirm:
        return {
            "action": "restore_file_preview",
            "file": file_path,
            "snapshot_id": snapshot_id,
            "snapshot_size": src.stat().st_size,
            "current_exists": dest.exists(),
            "current_size": dest.stat().st_size if dest.exists() else 0,
            "message": "Pass confirm=True or --confirm to execute.",
        }

    # Backup current version
    if dest.exists():
        backup = dest.with_suffix(dest.suffix + ".pre_restore")
        shutil.copy2(dest, backup)

    shutil.copy2(src, dest)
    return {
        "action": "file_restored",
        "file": file_path,
        "snapshot_id": snapshot_id,
        "size": dest.stat().st_size,
    }


# ═══════════════════════════════════════════════════════════════
# PRUNING (30-day retention)
# ═══════════════════════════════════════════════════════════════

def prune_old_snapshots() -> Dict[str, Any]:
    """Remove snapshots older than RETENTION_DAYS."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    snapshots = list_snapshots()
    pruned = 0

    for snap in snapshots:
        created = datetime.fromisoformat(snap["created_at"])
        if created < cutoff:
            snap_dir = SNAPSHOT_DIR / snap["snapshot_id"]
            if snap_dir.exists():
                shutil.rmtree(snap_dir)
                pruned += 1

    # Rebuild index without pruned entries
    remaining = [s for s in snapshots if datetime.fromisoformat(s["created_at"]) >= cutoff]
    with open(SNAPSHOT_INDEX, "w", encoding="utf-8") as f:
        for s in remaining:
            f.write(json.dumps(s) + "\n")

    return {"pruned": pruned, "remaining": len(remaining)}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    pa = argparse.ArgumentParser(description="EPOS Rollback Authority v1.0")
    pa.add_argument("--snapshot", action="store_true", help="Create a snapshot")
    pa.add_argument("--component", type=str, help="Component to snapshot (engine, content_lab, context_vault, missions, governance)")
    pa.add_argument("--reason", type=str, default="manual", help="Reason for snapshot")
    pa.add_argument("--list", action="store_true", help="List snapshots")
    pa.add_argument("--restore", type=str, help="Restore snapshot by ID")
    pa.add_argument("--restore-file", nargs=2, metavar=("FILE", "SNAP_ID"), help="Restore single file")
    pa.add_argument("--prune", action="store_true", help="Remove old snapshots")
    pa.add_argument("--confirm", action="store_true", help="Confirm destructive operations")

    a = pa.parse_args()

    if a.snapshot:
        r = create_snapshot(component=a.component, reason=a.reason)
        print(json.dumps(r, indent=2))
    elif a.list:
        snaps = list_snapshots()
        if not snaps:
            print("No snapshots found.")
        else:
            print(f"{'ID':<25} {'Created':<25} {'Component':<15} {'Files':<8} {'Reason'}")
            print("-" * 90)
            for s in snaps:
                print(f"{s['snapshot_id']:<25} {s['created_at'][:19]:<25} {s.get('component','?'):<15} {s['files']:<8} {s.get('reason','')}")
    elif a.restore:
        r = restore_snapshot(a.restore, confirm=a.confirm)
        print(json.dumps(r, indent=2))
    elif a.restore_file:
        r = restore_file(a.restore_file[0], a.restore_file[1], confirm=a.confirm)
        print(json.dumps(r, indent=2))
    elif a.prune:
        r = prune_old_snapshots()
        print(f"Pruned {r['pruned']} snapshots. {r['remaining']} remaining.")
    else:
        pa.print_help()
