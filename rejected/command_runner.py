import subprocess
from pathlib import Path

BLOCKLIST = [
    "rm -rf",
    "del /s",
    "format",
    "diskpart",
    "shutdown",
    "reboot",
    "sudo"
]

def run_commands(commands: list[str], cwd: str) -> dict:
    cwd_path = Path(cwd)
    cwd_path.mkdir(parents=True, exist_ok=True)

    results = []

    for cmd in commands:
        lowered = cmd.lower()
        if any(bad in lowered for bad in BLOCKLIST):
            return {
                "ok": False,
                "error": f"Blocked command: {cmd}",
                "results": results
            }

        proc = subprocess.run(
            cmd,
            cwd=str(cwd_path),
            shell=True,
            capture_output=True,
            text=True
        )

        results.append({
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:]
        })

        if proc.returncode != 0:
            break

    return {
        "ok": results and results[-1]["returncode"] == 0,
        "results": results
    }
