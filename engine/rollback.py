# EPOS GOVERNANCE WATERMARK
# File: C:\Users\Jamie\workspace\epos_mcp\engine\rollback.py
"""
EPOS Rollback Authority v1.2 — Snapshot & Restore System

Constitutional Authority: EPOS_CONSTITUTION_v3.1 Article V, VI
Purpose: Any operation can be rolled back within 24 hours.

Usage:
    python rollback.py --snapshot
    python rollback.py --snapshot --component engine
    python rollback.py --list
    python rollback.py --restore SNAP-20260219-001
    python rollback.py --prune
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv; load_dotenv()

# NOTE: EPOSDoctor pre-flight moved to runtime (was crashing at import time)
# Call _preflight() before snapshot/restore operations instead.

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", r"C:\Users\Jamie\workspace\epos_mcp"))
SNAPSHOT_DIR = EPOS_ROOT / "backups" / "snapshots"
SNAPSHOT_INDEX = SNAPSHOT_DIR / "index.jsonl"
RETENTION_DAYS = 30

COMPONENTS = {
    "engine": EPOS_ROOT / "engine",
    "content_lab": EPOS_ROOT / "content" / "lab",
    "context_vault": EPOS_ROOT / "context_vault",
    "missions": EPOS_ROOT / "missions",
    "governance": EPOS_ROOT,
}

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
    count = 0
    if SNAPSHOT_INDEX.exists():
        for line in SNAPSHOT_INDEX.read_text().splitlines():
            try:
                entry = json.loads(line)
                if entry.get("snapshot_id", "").startswith("SNAP-" + date_str):
                    count += 1
            except json.JSONDecodeError:
                pass
    return "SNAP-" + date_str + "-" + str(count + 1).zfill(3)


def create_snapshot(component: Optional[str] = None, reason: str = "manual") -> Dict[str, Any]:
    """Create a snapshot of specified component or full system."""
    snap_id = _next_snapshot_id()
    snap_dir = SNAPSHOT_DIR / snap_id
    snap_dir.mkdir(parents=True, exist_ok=True)
    manifest: List[Dict[str, str]] = []
    files_copied = 0
    total_bytes = 0

    def _copy_file(src: Path, rel_str: str) -> None:
        nonlocal files_copied, total_bytes
        dest = snap_dir / rel_str
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        manifest.append({"path": rel_str, "hash": _file_hash(src), "size": src.stat().st_size})
        files_copied += 1
        total_bytes += src.stat().st_size

    def _copy_dir(comp_dir: Path) -> None:
        if not comp_dir.exists():
            return
        for fp in comp_dir.rglob("*"):
            if fp.is_file() and not fp.name.startswith(".") and "__pycache__" not in str(fp):
                rel = str(fp.relative_to(EPOS_ROOT))
                _copy_file(fp, rel)

    if component:
        if component not in COMPONENTS:
            return {"error": "Unknown component: " + component}
        if component == "governance":
            for fname in GOVERNANCE_FILES:
                src = EPOS_ROOT / fname
                if src.exists() and src.is_file():
                    _copy_file(src, fname)
        else:
            _copy_dir(COMPONENTS[component])
    else:
        for comp_name, comp_dir in COMPONENTS.items():
            if comp_name == "governance":
                for fname in GOVERNANCE_FILES:
                    src = EPOS_ROOT / fname
                    if src.exists() and src.is_file():
                        _copy_file(src, fname)
            else:
                _copy_dir(comp_dir)

    manifest_path = snap_dir / "MANIFEST.json"
    manifest_path.write_text(json.dumps({
        "snapshot_id": snap_id, "created_at": datetime.now().isoformat(),
        "component": component or "full_system", "reason": reason,
        "files": files_copied, "total_bytes": total_bytes, "manifest": manifest,
    }, indent=2), encoding="utf-8")

    SNAPSHOT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_INDEX, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "snapshot_id": snap_id, "created_at": datetime.now().isoformat(),
            "component": component or "full_system", "reason": reason,
            "files": files_copied, "total_bytes": total_bytes,
        }) + "\n")

    return {"snapshot_id": snap_id, "files": files_copied, "total_bytes": total_bytes, "location": str(snap_dir)}


def list_snapshots() -> List[Dict[str, Any]]:
    if not SNAPSHOT_INDEX.exists():
        return []
    snapshots = []
    for line in SNAPSHOT_INDEX.read_text().splitlines():
        try:
            snapshots.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return sorted(snapshots, key=lambda s: s.get("created_at", ""), reverse=True)


def restore_snapshot(snapshot_id: str, confirm: bool = False) -> Dict[str, Any]:
    """Restore all files from a snapshot. Article V: no destructive ops without confirmation."""
    snap_dir = SNAPSHOT_DIR / snapshot_id
    manifest_path = snap_dir / "MANIFEST.json"
    if not manifest_path.exists():
        return {"error": "Snapshot not found: " + snapshot_id}
    manifest = json.loads(manifest_path.read_text())
    if not confirm:
        return {
            "action": "restore_preview", "snapshot_id": snapshot_id,
            "files_to_restore": manifest["files"], "created_at": manifest["created_at"],
            "message": "Pass --confirm to execute restore.",
        }
    pre_snap = create_snapshot(
        component=manifest["component"] if manifest["component"] != "full_system" else None,
        reason="pre_restore_of_" + snapshot_id,
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
        "action": "restored", "snapshot_id": snapshot_id,
        "files_restored": restored, "errors": errors,
        "pre_restore_snapshot": pre_snap.get("snapshot_id"),
    }


def restore_file(file_path: str, snapshot_id: str, confirm: bool = False) -> Dict[str, Any]:
    snap_dir = SNAPSHOT_DIR / snapshot_id
    src = snap_dir / file_path
    dest = EPOS_ROOT / file_path
    if not src.exists():
        return {"error": "File " + file_path + " not found in snapshot " + snapshot_id}
    if not confirm:
        return {"action": "preview", "file": file_path, "snapshot_id": snapshot_id, "message": "Pass --confirm to execute."}
    if dest.exists():
        shutil.copy2(dest, dest.with_suffix(dest.suffix + ".pre_restore"))
    shutil.copy2(src, dest)
    return {"action": "file_restored", "file": file_path, "size": dest.stat().st_size}


def prune_old_snapshots() -> Dict[str, Any]:
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
    remaining = [s for s in snapshots if datetime.fromisoformat(s["created_at"]) >= cutoff]
    with open(SNAPSHOT_INDEX, "w", encoding="utf-8") as f:
        for s in remaining:
            f.write(json.dumps(s) + "\n")
    return {"pruned": pruned, "remaining": len(remaining)}


if __name__ == "__main__":
    import argparse
    pa = argparse.ArgumentParser(description="EPOS Rollback Authority v1.2")
    pa.add_argument("--snapshot", action="store_true")
    pa.add_argument("--component", type=str)
    pa.add_argument("--reason", type=str, default="manual")
    pa.add_argument("--list", action="store_true")
    pa.add_argument("--restore", type=str)
    pa.add_argument("--restore-file", nargs=2, metavar=("FILE", "SNAP_ID"))
    pa.add_argument("--prune", action="store_true")
    pa.add_argument("--confirm", action="store_true")
    a = pa.parse_args()

    if a.snapshot:
        print(json.dumps(create_snapshot(component=a.component, reason=a.reason), indent=2))
    elif a.list:
        snaps = list_snapshots()
        if not snaps:
            print("No snapshots found.")
        else:
            for s in snaps:
                print(s["snapshot_id"] + "  " + s["created_at"][:19] + "  " + s.get("component", "?") + "  " + str(s["files"]) + " files")
    elif a.restore:
        print(json.dumps(restore_snapshot(a.restore, confirm=a.confirm), indent=2))
    elif a.restore_file:
        print(json.dumps(restore_file(a.restore_file[0], a.restore_file[1], confirm=a.confirm), indent=2))
    elif a.prune:
        r = prune_old_snapshots()
        print("Pruned " + str(r["pruned"]) + " snapshots. " + str(r["remaining"]) + " remaining.")
    else:
        pa.print_help()
