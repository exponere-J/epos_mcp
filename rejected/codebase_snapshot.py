#!/usr/bin/env python3
r"""
Codebase Printer for EPOS/Exponere Projects
==========================================
Run this script from your project root to generate a complete snapshot
of your codebase that you can share with Claude.

Usage:
    python codebase_snapshot.py [project_path] [output_file]

Examples:
    python codebase_snapshot.py .
    python codebase_snapshot.py C:/Users/Jamie/workspace/exponere-seed
    python codebase_snapshot.py . codebase_snapshot.txt
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION - Adjust these to match your project
# =============================================================================

# File extensions to include
INCLUDE_EXTENSIONS = {
    # Python
    ".py",
    # JavaScript/TypeScript
    ".js", ".ts", ".jsx", ".tsx",
    # Web
    ".html", ".css", ".scss",
    # Config
    ".json", ".yaml", ".yml", ".toml", ".ini",
    # Environment (be careful with secrets!)
    ".env.example", ".env.template",
    # Documentation
    ".md", ".txt", ".rst",
    # Shell
    ".sh", ".bash", ".ps1",
    # Data
    ".sql", ".graphql",
}

# Directories to skip entirely
SKIP_DIRECTORIES = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "eggs",
    "*.egg-info",
    ".idea",
    ".vscode",
    "snapshots",      # Huntsman screenshots
    "browser_state",  # Playwright state
    "sprint_logs",    # May contain lots of logs
}

# Files to skip
SKIP_FILES = {
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    ".DS_Store",
    "Thumbs.db",
}

# Maximum file size to include (in bytes) - skip huge files
MAX_FILE_SIZE = 100_000  # 100KB

# Files that might contain secrets - warn but don't print contents
SENSITIVE_PATTERNS = {".env", "secrets", "credentials", "api_key", "token"}


# =============================================================================
# SCRIPT LOGIC
# =============================================================================

def should_skip_directory(dir_name: str) -> bool:
    """Check if a directory should be skipped."""
    return dir_name in SKIP_DIRECTORIES or dir_name.startswith(".")


def should_include_file(file_path: Path) -> bool:
    """Check if a file should be included in output."""
    if file_path.name in SKIP_FILES:
        return False

    # Check extension
    if file_path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True

    # Include extensionless files that are likely config (Dockerfile, Makefile, etc.)
    if file_path.suffix == "" and file_path.name in {"Dockerfile", "Makefile", "Procfile", "Brewfile"}:
        return True

    return False


def is_sensitive_file(file_path: Path) -> bool:
    """Check if file might contain secrets."""
    name_lower = file_path.name.lower()

    # .env files (but not .env.example)
    if name_lower == ".env":
        return True

    # Other sensitive patterns
    for pattern in SENSITIVE_PATTERNS:
        if pattern in name_lower and "example" not in name_lower and "template" not in name_lower:
            return True

    return False


def get_file_content(file_path: Path) -> tuple[str, str]:
    """
    Read file content. Returns (content, status).
    Status can be: 'ok', 'sensitive', 'too_large', 'binary', 'error'
    """
    try:
        size = file_path.stat().st_size

        if size > MAX_FILE_SIZE:
            return f"[FILE TOO LARGE: {size:,} bytes - skipped]", "too_large"

        if is_sensitive_file(file_path):
            return "[SENSITIVE FILE - contents hidden. Check for secrets before sharing]", "sensitive"

        # Try to read as text
        try:
            content = file_path.read_text(encoding="utf-8")
            return content, "ok"
        except UnicodeDecodeError:
            return "[BINARY FILE - skipped]", "binary"

    except Exception as e:
        return f"[ERROR reading file: {e}]", "error"


def scan_directory(root_path: Path) -> list[tuple[Path, str, str]]:
    """
    Scan directory and return list of (relative_path, content, status) tuples.
    """
    results: list[tuple[Path, str, str]] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out directories we want to skip (modifies dirnames in-place)
        dirnames[:] = [d for d in dirnames if not should_skip_directory(d)]

        current_dir = Path(dirpath)

        for filename in sorted(filenames):
            file_path = current_dir / filename

            if should_include_file(file_path):
                relative_path = file_path.relative_to(root_path)
                content, status = get_file_content(file_path)
                results.append((relative_path, content, status))

    return results


def generate_tree(root_path: Path) -> str:
    """Generate a directory tree structure."""
    lines = [f"{root_path.name}/"]

    def walk_tree(current_path: Path, prefix: str = ""):
        entries = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

        # Filter entries
        entries = [e for e in entries if not (e.is_dir() and should_skip_directory(e.name))]

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                walk_tree(entry, prefix + extension)
            else:
                if should_include_file(entry):
                    lines.append(f"{prefix}{connector}{entry.name}")

    walk_tree(root_path)
    return "\n".join(lines)


def format_output(root_path: Path, files: list[tuple[Path, str, str]]) -> str:
    """Format the complete output."""
    output_lines: list[str] = []

    # Header
    output_lines.append("=" * 80)
    output_lines.append(f"CODEBASE SNAPSHOT: {root_path.name}")
    output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"Root Path: {root_path.absolute()}")
    output_lines.append("=" * 80)
    output_lines.append("")

    # Statistics
    stats = {"ok": 0, "sensitive": 0, "too_large": 0, "binary": 0, "error": 0}
    for _, _, status in files:
        stats[status] += 1

    output_lines.append("STATISTICS:")
    output_lines.append(f"  Files included: {stats['ok']}")
    output_lines.append(f"  Sensitive (hidden): {stats['sensitive']}")
    output_lines.append(f"  Too large (skipped): {stats['too_large']}")
    output_lines.append(f"  Binary (skipped): {stats['binary']}")
    output_lines.append(f"  Errors: {stats['error']}")
    output_lines.append("")

    # Directory tree
    output_lines.append("-" * 80)
    output_lines.append("DIRECTORY STRUCTURE:")
    output_lines.append("-" * 80)
    output_lines.append(generate_tree(root_path))
    output_lines.append("")

    # File contents
    output_lines.append("-" * 80)
    output_lines.append("FILE CONTENTS:")
    output_lines.append("-" * 80)
    output_lines.append("")

    for relative_path, content, _status in files:
        output_lines.append("=" * 80)
        output_lines.append(f"FILE: {relative_path}")
        output_lines.append("=" * 80)
        output_lines.append(content)
        output_lines.append("")

    # Footer
    output_lines.append("=" * 80)
    output_lines.append("END OF CODEBASE SNAPSHOT")
    output_lines.append("=" * 80)

    return "\n".join(output_lines)


def main() -> None:
    # Parse arguments
    if len(sys.argv) < 2:
        project_path = Path(".")
    else:
        project_path = Path(sys.argv[1])

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = None

    # Validate path
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    if not project_path.is_dir():
        print(f"Error: Path is not a directory: {project_path}")
        sys.exit(1)

    project_path = project_path.resolve()

    print(f"Scanning: {project_path}")
    print("This may take a moment for large projects...")
    print()

    # Scan and format
    files = scan_directory(project_path)
    output = format_output(project_path, files)

    # Output
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(output, encoding="utf-8")
        print(f"Snapshot saved to: {output_path.absolute()}")
        print(f"Size: {len(output):,} characters")
    else:
        print(output)

    print()
    print("Done! Copy the output above (or the file contents) and paste into Claude.")


if __name__ == "__main__":
    main()
