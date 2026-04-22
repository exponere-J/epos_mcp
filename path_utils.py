#!/usr/bin/env python3
"""
path_utils.py — EPOS Canonical Path Resolution
================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Article II (Path Discipline)
Mission ID: EPOS Core Heal — Module 1 of 9
File Location: /mnt/c/Users/Jamie/workspace/epos_mcp/path_utils.py

Single responsibility: resolve all EPOS paths from EPOS_ROOT.
Never from cwd. Handles Windows, WSL, and Linux automatically.

Dependencies: stdlib + python-dotenv (zero external deps)

Exports:
    get_epos_root()          -> Path
    get_workspace_root()     -> Path
    get_agent_zero_path()    -> Path
    resolve_epos_path(rel)   -> Path
    get_engine_dir()         -> Path
    get_context_vault()      -> Path
    get_logs_dir()           -> Path
    detect_platform()        -> str   ("windows" | "wsl" | "linux" | "darwin")
    validate_path(path_str)  -> bool  (constitutional path format check)
"""

import os
import platform
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from dotenv import load_dotenv

# ── Load .env from same directory as this file ───────────────────
_THIS_DIR = Path(__file__).resolve().parent
load_dotenv(_THIS_DIR / ".env")


# ── Exceptions ───────────────────────────────────────────────────

class ConstitutionalPathError(RuntimeError):
    """Raised when EPOS path discipline (Article II) is violated."""
    pass


# ── Platform Detection ───────────────────────────────────────────

def detect_platform() -> str:
    """
    Detect runtime platform.

    Returns:
        "windows" — native Windows (cmd, PowerShell, Git Bash)
        "wsl"     — Windows Subsystem for Linux
        "linux"   — native Linux
        "darwin"  — macOS
    """
    system = platform.system().lower()

    if system == "linux":
        # Distinguish WSL from native Linux
        try:
            with open("/proc/version", "r") as f:
                version_info = f.read().lower()
            if "microsoft" in version_info or "wsl" in version_info:
                return "wsl"
        except (FileNotFoundError, PermissionError):
            pass
        return "linux"

    if system == "windows":
        return "windows"

    if system == "darwin":
        return "darwin"

    return system


# ── Path Normalization ───────────────────────────────────────────

def _normalize_path(raw: str) -> Path:
    """
    Normalize a path string to a valid Path for the current platform.

    Handles cross-platform conversions:
        /mnt/c/Users/...  → C:/Users/...     (WSL → Windows)
        C:\\Users\\...     → C:/Users/...     (backslash → forward)
        ~/workspace/...   → expanded          (tilde expansion)
    """
    if not raw:
        raise ConstitutionalPathError(
            "Empty path string. Article II requires absolute paths."
        )

    raw = raw.strip()

    # Tilde expansion
    if raw.startswith("~"):
        raw = str(Path(raw).expanduser())

    plat = detect_platform()

    # WSL path on Windows host: /mnt/c/... → C:/...
    if plat == "windows" and raw.startswith("/mnt/"):
        parts = raw.split("/")
        if len(parts) >= 3 and len(parts[2]) == 1:
            drive = parts[2].upper()
            rest = "/".join(parts[3:])
            raw = f"{drive}:/{rest}"

    # Backslash normalization
    raw = raw.replace("\\", "/")

    return Path(raw).resolve()


# ── Core Exports ─────────────────────────────────────────────────

def get_epos_root() -> Path:
    """
    Return the absolute path to the EPOS root directory.

    Resolution order:
        1. EPOS_ROOT environment variable (from .env or shell)
        2. Directory containing this file (fallback)

    Raises:
        ConstitutionalPathError if the resolved path doesn't exist.
    """
    raw = os.getenv("EPOS_ROOT")

    if raw:
        root = _normalize_path(raw)
    else:
        # Fallback: this file lives at epos_mcp root
        root = _THIS_DIR

    if not root.exists():
        raise ConstitutionalPathError(
            f"EPOS_ROOT resolves to '{root}' which does not exist. "
            f"Set EPOS_ROOT in .env or environment. (Article II Rule 1)"
        )

    return root


def get_workspace_root() -> Path:
    """
    Return the workspace root (parent of EPOS root).

    Uses WORKSPACE_ROOT env var if set, otherwise derives from EPOS_ROOT.
    """
    raw = os.getenv("WORKSPACE_ROOT")
    if raw:
        return _normalize_path(raw)
    return get_epos_root().parent


def get_agent_zero_path() -> Path:
    """
    Return the path to the Agent Zero repository.

    Uses AGENT_ZERO_PATH env var if set, otherwise assumes
    it's a sibling directory of EPOS root.
    """
    raw = os.getenv("AGENT_ZERO_PATH")
    if raw:
        return _normalize_path(raw)
    return get_workspace_root() / "agent-zero"


def resolve_epos_path(relative: str) -> Path:
    """
    Resolve a relative path against EPOS_ROOT.

    Args:
        relative: Path relative to EPOS root (e.g., "engine/stasis.py")

    Returns:
        Absolute Path object.

    Raises:
        ConstitutionalPathError if relative path escapes EPOS_ROOT.
    """
    if not relative:
        raise ConstitutionalPathError(
            "Empty relative path. Provide a path relative to EPOS_ROOT."
        )

    root = get_epos_root()
    resolved = (root / relative).resolve()

    # Prevent directory traversal outside EPOS_ROOT
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ConstitutionalPathError(
            f"Path '{relative}' resolves to '{resolved}' which escapes "
            f"EPOS_ROOT '{root}'. Directory traversal blocked. (Article II)"
        )

    return resolved


# ── Convenience Exports ──────────────────────────────────────────

def get_engine_dir() -> Path:
    """Return path to the governed engine directory."""
    return get_epos_root() / "engine"


def get_context_vault() -> Path:
    """Return path to the Context Vault."""
    return get_epos_root() / "context_vault"


def get_logs_dir() -> Path:
    """Return path to the logs directory, creating it if needed."""
    logs = get_epos_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs


def validate_path(path_str: str) -> bool:
    """
    Constitutional validation for path formatting (Article II Rule 1).

    On Windows/WSL: path must contain a drive letter (e.g., C:/).
    On Linux/macOS: path must be absolute (starts with /).

    Args:
        path_str: Path string to validate.

    Returns:
        True if the path format is valid for the current platform.
    """
    if not path_str or not path_str.strip():
        return False
    plat = detect_platform()
    if plat in ("windows", "wsl"):
        # Must contain drive letter
        return ":" in path_str and not path_str.startswith("/mnt/") or path_str.startswith("/mnt/")
    # Linux/macOS: must be absolute
    return path_str.startswith("/")


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EPOS Path Utils — Self-Test")
    print("=" * 50)
    print(f"  Platform:        {detect_platform()}")
    print(f"  EPOS_ROOT:       {get_epos_root()}")
    print(f"  WORKSPACE_ROOT:  {get_workspace_root()}")
    print(f"  AGENT_ZERO_PATH: {get_agent_zero_path()}")
    print(f"  Engine dir:      {get_engine_dir()}")
    print(f"  Context Vault:   {get_context_vault()}")
    print(f"  Logs dir:        {get_logs_dir()}")
    print(f"  resolve('engine/stasis.py'): {resolve_epos_path('engine/stasis.py')}")

    # Test traversal guard
    try:
        resolve_epos_path("../../etc/passwd")
        print("  FAIL: traversal guard did not fire")
        sys.exit(1)
    except ConstitutionalPathError:
        print("  Traversal guard: PASS")

    print("\nAll checks passed.")
    sys.exit(0)
