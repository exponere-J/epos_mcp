import subprocess
from pathlib import Path

BLOCKLIST = ["rm -rf", "del /s", "format", "diskpart", "shutdown", "reboot", "sudo"]

def _is_blocked(cmd: str) -> bool:
    c = cmd.lower().strip()
    return any(b in c for b in BLOCKLIST)

def run_commands(commands: list[str], cwd: str) -> dict:
    cwd_path = Path(cwd)
    cwd_path.mkdir(parents=True, exist_ok=True)

    outputs = []
    for cmd in commands:
        if _is_blocked(cmd):
            raise RuntimeError(f"Blocked command detected: {cmd}")

        proc = subprocess.run(
            cmd,
            cwd=str(cwd_path),
            shell=True,
            capture_output=True,
            text=True
        )
        outputs.append({
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-4000:],
        })
        if proc.returncode != 0:
            break

    return {"cwd": str(cwd_path), "results": outputs}
