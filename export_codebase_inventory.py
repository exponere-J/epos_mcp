# File: /mnt/c/Users/Jamie/workspace/epos_mcp/export_codebase_inventory.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
EPOS Codebase Inventory Export
Writes a complete tree + file manifest to epos_codebase_inventory.txt

Usage (from repo root):
    python export_codebase_inventory.py
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

# Configure root and output
ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "epos_codebase_inventory.txt"

# File extensions to treat as "code / config"
CODE_EXTENSIONS = {
    ".py", ".json", ".jsonl", ".md", ".toml", ".yaml", ".yml",
    ".txt", ".html", ".css", ".js"
}

# Directories to skip (caches, venvs, heavy logs, etc.)
SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "venv_az", "venv_epos",
    ".mypy_cache", ".pytest_cache", ".idea", ".vscode",
    "node_modules", ".cache"
}

def is_skipped_dir(path: Path) -> bool:
    parts = set(path.parts)
    return any(skip in parts for skip in SKIP_DIRS)

def main() -> None:
    lines = []
    ts = datetime.now().isoformat(timespec="seconds")
    lines.append(f"EPOS CODEBASE INVENTORY")
    lines.append(f"Root: {ROOT}")
    lines.append(f"Generated: {ts}")
    lines.append("")
    lines.append("Legend: [type] size_bytes  rel_path")
    lines.append("        type=DIR/FILE      ext shown for files")
    lines.append("")
    lines.append("=== DIRECTORY TREE + FILE MANIFEST ===")
    lines.append("")

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dir_path = Path(dirpath)

        # Skip unwanted directories
        if is_skipped_dir(dir_path):
            dirnames[:] = []  # stop descending
            continue

        rel_dir = dir_path.relative_to(ROOT)
        if str(rel_dir) == ".":
            rel_dir_str = "."
        else:
            rel_dir_str = str(rel_dir).replace("\\", "/")

        # Directory header
        lines.append(f"[DIR]  {rel_dir_str}")
        # Sort files for stability
        for name in sorted(filenames):
            file_path = dir_path / name
            rel_file = file_path.relative_to(ROOT)
            rel_file_str = str(rel_file).replace("\\", "/")
            try:
                size = file_path.stat().st_size
            except OSError:
                size = -1

            ext = file_path.suffix.lower()
            kind = "FILE"
            # Mark if it looks like code/config vs other
            marker = "code" if ext in CODE_EXTENSIONS else "other"
            lines.append(f"  [{kind}|{marker}] {size:8d}  {rel_file_str}")
        lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nInventory written to: {OUTPUT_PATH}\n")

if __name__ == "__main__":
    main()
