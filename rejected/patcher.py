import subprocess
import tempfile
from pathlib import Path

def apply_unified_diff(patch: str, cwd: str) -> dict:
    """
    Apply a unified diff safely.
    Returns status + stdout/stderr.
    """
    if not patch.strip():
        return {"ok": True, "skipped": True, "stdout": "", "stderr": ""}

    cwd_path = Path(cwd)
    cwd_path.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".diff") as f:
        f.write(patch)
        patch_file = f.name

    try:
        proc = subprocess.run(
            ["git", "apply", "--unsafe-paths", patch_file],
            cwd=str(cwd_path),
            capture_output=True,
            text=True
        )

        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }
    finally:
        Path(patch_file).unlink(missing_ok=True)
