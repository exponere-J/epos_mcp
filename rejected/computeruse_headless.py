from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

# Keep this conservative.
BLOCKLIST = [
    "rm -rf", "rm -r", "del /s", "format", "diskpart", "shutdown", "reboot", "sudo",
    ":(){:|:&};:",  # fork bomb
]

def _is_blocked(cmd: str) -> bool:
    c = cmd.lower().strip()
    return any(b in c for b in BLOCKLIST)

@dataclass
class ShellResult:
    cmd: str
    returncode: int
    stdout: str
    stderr: str

def run_shell(commands: List[str], cwd: str = ".", env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    cwd_path = Path(cwd)
    cwd_path.mkdir(parents=True, exist_ok=True)

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    results: List[ShellResult] = []
    for cmd in commands:
        if _is_blocked(cmd):
            raise RuntimeError(f"Blocked command detected: {cmd}")

        proc = subprocess.run(
            cmd,
            cwd=str(cwd_path),
            shell=True,
            capture_output=True,
            text=True,
            env=merged_env,
        )
        results.append(ShellResult(
            cmd=cmd,
            returncode=proc.returncode,
            stdout=(proc.stdout or "")[-6000:],
            stderr=(proc.stderr or "")[-6000:],
        ))
        if proc.returncode != 0:
            break

    return {
        "cwd": str(cwd_path),
        "results": [r.__dict__ for r in results],
        "ok": (len(results) > 0 and results[-1].returncode == 0),
    }

def write_file(path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and not overwrite:
        return {"ok": True, "skipped": True, "path": str(p), "reason": "exists"}
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "skipped": False, "path": str(p)}

def apply_unified_diff(diff_text: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Apply a unified diff using 'git apply'. Requires git installed.
    Safer than raw shell edits and easy to rollback with git.
    """
    tmp = Path(cwd) / ".epos_patch.diff"
    tmp.write_text(diff_text, encoding="utf-8")

    # --reject leaves .rej files instead of partially applying silently
    res = run_shell(
        commands=[
            "git status --porcelain",
            "git apply --reject --whitespace=fix .epos_patch.diff",
            "git status --porcelain",
        ],
        cwd=cwd
    )
    return {"ok": res["ok"], "details": res, "patch_file": str(tmp)}
