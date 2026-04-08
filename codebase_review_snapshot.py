#!/usr/bin/env python3
# File: C:\Users\Jamie\workspace\epos_mcp\codebase_review_snapshot.py

from pathlib import Path
from datetime import datetime, timezone
import os

EPOS_ROOT = Path("/mnt/c/Users/Jamie/workspace/epos_mcp")
OUTPUT_NAME = "EPOS_CODEBASE_REVIEW.txt"

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", "venvepos", "venvaz",
    ".venv", "dist", "build", "out", ".pytest_cache", ".mypy_cache"
}

EXCLUDED_FILES = {
    OUTPUT_NAME, ".DS_Store", "Thumbs.db"
}

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".sh", ".bat", ".ps1", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".sql", ".csv"
}

MAX_FILE_SIZE = 512 * 1024  # 512 KB per file

def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".env"}

def should_skip_dir(name: str) -> bool:
    return name in EXCLUDED_DIRS

def should_skip_file(name: str) -> bool:
    return name in EXCLUDED_FILES

def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"

def build_tree(root: Path) -> list[str]:
    lines = [f"{root.name}/"]
    for current_root, dirs, files in os.walk(root):
        dirs[:] = sorted([d for d in dirs if not should_skip_dir(d)])
        files = sorted([f for f in files if not should_skip_file(f)])

        rel = Path(current_root).relative_to(root)
        depth = len(rel.parts)

        if str(rel) != ".":
            indent = "    " * depth
            lines.append(f"{indent}{Path(current_root).name}/")

        file_indent = "    " * (depth + 1)
        for f in files:
            fpath = Path(current_root) / f
            try:
                size = format_size(fpath.stat().st_size)
            except Exception:
                size = "ERR"
            lines.append(f"{file_indent}{f} [{size}]")
    return lines

def build_manifest(root: Path) -> list[str]:
    lines = []
    for current_root, dirs, files in os.walk(root):
        dirs[:] = sorted([d for d in dirs if not should_skip_dir(d)])
        files = sorted([f for f in files if not should_skip_file(f)])

        for f in files:
            fpath = Path(current_root) / f
            try:
                stat = fpath.stat()
                rel = fpath.relative_to(root)
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                lines.append(
                    f"{str(rel):<90} | {format_size(stat.st_size):>10} | {mtime}"
                )
            except Exception as e:
                lines.append(f"{fpath} | ERROR | {e}")
    return lines

def dump_contents(root: Path) -> list[str]:
    lines = []
    for current_root, dirs, files in os.walk(root):
        dirs[:] = sorted([d for d in dirs if not should_skip_dir(d)])
        files = sorted([f for f in files if not should_skip_file(f)])

        for f in files:
            fpath = Path(current_root) / f
            if not is_text_file(fpath):
                continue

            try:
                size = fpath.stat().st_size
                if size > MAX_FILE_SIZE:
                    lines.append("\n" + "=" * 100)
                    lines.append(f"FILE: {fpath.relative_to(root)}")
                    lines.append(f"SKIPPED: file too large ({format_size(size)})")
                    lines.append("=" * 100)
                    continue

                content = fpath.read_text(encoding="utf-8", errors="replace")
                lines.append("\n" + "=" * 100)
                lines.append(f"FILE: {fpath.relative_to(root)}")
                lines.append(f"SIZE: {format_size(size)}")
                lines.append("=" * 100)
                lines.append(content)
            except Exception as e:
                lines.append("\n" + "=" * 100)
                lines.append(f"FILE: {fpath.relative_to(root)}")
                lines.append(f"ERROR: {e}")
                lines.append("=" * 100)
    return lines

def main():
    if not EPOS_ROOT.exists():
        raise SystemExit(f"EPOS root not found: {EPOS_ROOT}")

    output_path = EPOS_ROOT / OUTPUT_NAME
    timestamp = datetime.now(timezone.utc).isoformat()

    tree = build_tree(EPOS_ROOT)
    manifest = build_manifest(EPOS_ROOT)
    contents = dump_contents(EPOS_ROOT)

    report = []
    report.append("=" * 100)
    report.append("EPOS CODEBASE REVIEW SNAPSHOT")
    report.append("=" * 100)
    report.append(f"Generated: {timestamp}")
    report.append(f"Root: {EPOS_ROOT}")
    report.append(f"Output: {output_path}")
    report.append("")

    report.append("=" * 100)
    report.append("DIRECTORY TREE")
    report.append("=" * 100)
    report.extend(tree)
    report.append("")

    report.append("=" * 100)
    report.append("FILE MANIFEST")
    report.append("=" * 100)
    report.extend(manifest)
    report.append("")

    report.append("=" * 100)
    report.append("FILE CONTENTS")
    report.append("=" * 100)
    report.extend(contents)
    report.append("")

    output_path.write_text("\n".join(report), encoding="utf-8")

    print(f"Saved codebase review to: {output_path}")

if __name__ == "__main__":
    main()
