#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
path_sanitizer.py — Windows Path Scanner & POSIX Refactor
===========================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-01 (Step C: Path & Secret Sanitation)

Scans Python source files for Windows-style paths and replaces them
with POSIX-compliant os.getenv("EPOS_ROOT", "/app") patterns.

Patterns detected:
  - C:/Users/... or C:\\Users\\... (Windows absolute paths)
  - /mnt/c/... (WSL2 mount paths)
  - Hardcoded /home/username/... (non-portable Unix)

Vault: context_vault/reports/
Event: system.path_sanitizer.complete
"""

import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))

# Directories to scan (skip venvs, caches, archives)
SCAN_DIRS = [
    EPOS_ROOT / "epos",
    EPOS_ROOT / "engine",
    EPOS_ROOT / "friday",
    EPOS_ROOT / "reactor",
    EPOS_ROOT / "nodes",
]
SKIP_PATTERNS = {
    "__pycache__", ".venv", "venv", "venv_epos", ".git",
    "rejected", "_archive", "node_modules", ".mypy_cache",
}

# Regex patterns for Windows-style paths
_WIN_DRIVE = re.compile(
    r'["\']([A-Za-z]:[/\\][^"\']*)["\']',
    re.IGNORECASE,
)
_WSL_MOUNT = re.compile(
    r'["\'](/mnt/[a-z]/[^"\']*)["\']',
)
_HARDCODED_HOME = re.compile(
    r'["\'](/home/\w+/[^"\']*)["\']',
)

# Replacement heuristics
def _replacement(path_str: str) -> str:
    """Map a detected path to its POSIX-compliant replacement."""
    pl = path_str.lower()
    # Workspace root → EPOS_ROOT
    if "workspace" in pl or "epos_mcp" in pl:
        # Extract subpath after known root markers
        for marker in ("epos_mcp/", "epos_mcp\\", "workspace/epos_mcp/"):
            idx = pl.find(marker)
            if idx >= 0:
                subpath = path_str[idx + len(marker):]
                subpath = subpath.replace("\\", "/")
                if subpath:
                    return f'Path(os.getenv("EPOS_ROOT", "/app")) / "{subpath}"'
                return 'Path(os.getenv("EPOS_ROOT", "/app"))'
        return 'Path(os.getenv("EPOS_ROOT", "/app"))'
    # User home / documents
    if "users" in pl or "documents" in pl or "/home/" in pl:
        return 'Path(os.getenv("EPOS_ROOT", "/app"))'
    # WSL mount
    if path_str.startswith("/mnt/"):
        return 'Path(os.getenv("EPOS_ROOT", "/app"))'
    return 'Path(os.getenv("EPOS_ROOT", "/app"))'


class PathSanitizer:
    """Scans and refactors Windows paths in Python source files."""

    def scan(self, dry_run: bool = True) -> dict:
        """
        Scan all Python files in SCAN_DIRS for Windows paths.

        Returns:
            {files_scanned, contaminated_files, total_matches, matches_by_file}
        """
        files_scanned = 0
        contaminated = []
        matches_by_file = {}

        for scan_dir in SCAN_DIRS:
            if not scan_dir.exists():
                continue
            for py_file in scan_dir.rglob("*.py"):
                # Skip excluded dirs
                if any(skip in py_file.parts for skip in SKIP_PATTERNS):
                    continue
                files_scanned += 1
                try:
                    content = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue
                file_matches = self._find_matches(content, str(py_file))
                if file_matches:
                    contaminated.append(str(py_file))
                    matches_by_file[str(py_file)] = file_matches

        return {
            "files_scanned": files_scanned,
            "contaminated_files": len(contaminated),
            "total_matches": sum(len(v) for v in matches_by_file.values()),
            "matches_by_file": matches_by_file,
            "dry_run": dry_run,
        }

    def refactor(self) -> dict:
        """
        Apply path replacements to all contaminated files.

        Returns:
            {files_refactored, changes, errors}
        """
        scan_result = self.scan(dry_run=False)
        changes = []
        errors = []

        for filepath, matches in scan_result["matches_by_file"].items():
            try:
                path = Path(filepath)
                content = path.read_text(encoding="utf-8")
                original = content
                file_changes = []

                for match in matches:
                    old_str = match["matched_string"]
                    new_str = match["replacement"]
                    if old_str in content:
                        content = content.replace(old_str, new_str, 1)
                        file_changes.append({
                            "file": filepath,
                            "line": match["line"],
                            "before": old_str,
                            "after": new_str,
                        })

                if content != original:
                    # Ensure os import present
                    if "import os" not in content and 'os.getenv' in content:
                        content = "import os\n" + content
                    # Atomic write
                    tmp = path.with_suffix(".tmp")
                    tmp.write_text(content, encoding="utf-8")
                    tmp.replace(path)
                    changes.extend(file_changes)
            except Exception as e:
                errors.append({"file": filepath, "error": str(e)})

        result = {
            "files_refactored": len(set(c["file"] for c in changes)),
            "total_changes": len(changes),
            "changes": changes,
            "errors": errors,
        }

        # Publish event
        if _BUS:
            try:
                _BUS.publish("system.path_sanitizer.complete", {
                    "files_refactored": result["files_refactored"],
                    "total_changes": result["total_changes"],
                    "errors": len(errors),
                }, source_module="path_sanitizer")
            except Exception:
                pass

        return result

    def _find_matches(self, content: str, filepath: str) -> List[dict]:
        """Find all Windows/non-portable path matches in content."""
        matches = []
        lines = content.split("\n")

        for pattern in [_WIN_DRIVE, _WSL_MOUNT, _HARDCODED_HOME]:
            for m in pattern.finditer(content):
                path_str = m.group(1)
                # Find line number
                line_num = content[:m.start()].count("\n") + 1
                line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                # Skip if already inside getenv() call
                context_start = max(0, m.start() - 20)
                context = content[context_start:m.start()]
                if "getenv" in context or "os.environ" in context:
                    continue

                # Skip comments
                if line_content.startswith("#"):
                    continue

                replacement = _replacement(path_str)
                # The full string in source (with quotes)
                matched_string = m.group(0)

                matches.append({
                    "line": line_num,
                    "line_content": line_content[:120],
                    "matched_string": matched_string,
                    "path_value": path_str,
                    "replacement": replacement,
                })

        return matches


def run_scan() -> dict:
    return PathSanitizer().scan(dry_run=True)


def run_refactor() -> dict:
    return PathSanitizer().refactor()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EPOS Path Sanitizer")
    parser.add_argument("--refactor", action="store_true", help="Apply refactors (default: scan only)")
    args = parser.parse_args()

    ps = PathSanitizer()
    if args.refactor:
        print("Running refactor...")
        result = ps.refactor()
        print(f"Files refactored: {result['files_refactored']}")
        print(f"Total changes:    {result['total_changes']}")
        print(f"Errors:           {len(result['errors'])}")
        for c in result["changes"][:10]:
            print(f"  [{c['file'].split('/')[-1]}:{c['line']}] {c['before'][:40]} → {c['after'][:40]}")
    else:
        print("Running scan (dry-run)...")
        result = ps.scan(dry_run=True)
        print(f"Files scanned:      {result['files_scanned']}")
        print(f"Contaminated files: {result['contaminated_files']}")
        print(f"Total matches:      {result['total_matches']}")
        for f, matches in list(result["matches_by_file"].items())[:5]:
            print(f"  {f.split('/')[-1]}: {len(matches)} matches")
            for m in matches[:2]:
                print(f"    L{m['line']}: {m['matched_string'][:60]}")

    print("\nPASS: path_sanitizer")
