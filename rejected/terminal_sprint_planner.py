import json
from .llm_client import call_llm

SYSTEM = """You are EPOS.TerminalSprintPlanner.

You convert a TASK into SAFE, idempotent terminal commands.

HARD RULES:
- Output ONLY valid JSON. No markdown. No commentary.
- No destructive commands: rm -rf, del /s, format, diskpart, shutdown, reboot, sudo.
- Prefer creating new files/folders over overwriting.
- Assume Git Bash on Windows (Unix-like). Use mkdir -p, printf, test, cat, python -c, etc.
- Include "checks" the operator can verify.

Return EXACT schema:
{
  "plan": ["step 1", "step 2"],
  "commands": ["cmd 1", "cmd 2"],
  "checks": ["check 1", "check 2"],
  "notes": "short caveats"
}
"""

def _try_parse_json(raw: str) -> dict:
    raw = raw.strip()
    return json.loads(raw)

def propose_terminal_sprint(task: str, cwd: str, os_hint: str = "gitbash", model: str | None = None) -> dict:
    user = f"""CWD: {cwd}
OS_HINT: {os_hint}

TASK:
{task}

Return ONLY JSON in the required schema. No other text."""
    # Attempt 1
    raw = call_llm(SYSTEM, user, temperature=0.2, model=model)
    try:
        return _try_parse_json(raw)
    except Exception:
        # Attempt 2: force correction
        fixer_system = SYSTEM + "\n\nYOU MUST RETURN ONLY JSON. DO NOT WRAP IN MARKDOWN."
        fixer_user = f"""Your previous output was invalid JSON.

Fix it and return ONLY valid JSON for the same task.

INVALID_OUTPUT:
{raw}
"""
        raw2 = call_llm(fixer_system, user + "\n\n" + fixer_user, temperature=0.0, model=model)
        return _try_parse_json(raw2)
