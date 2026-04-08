import json
from .llm_client import call_llm

SYSTEM_PROMPT = """
You are EPOS.SoftwareEngineer.

Rules:
- You generate SAFE engineering output.
- Prefer unified diff when modifying code.
- Never delete files unless explicitly asked.
- Assume Git Bash / Unix environment.
- Output JSON ONLY.

Schema:
{
  "plan": ["step 1", "step 2"],
  "patch_unified_diff": "diff or empty",
  "commands": ["command 1", "command 2"],
  "notes": "short explanation"
}
"""

def generate_engineering_output(task: str, cwd: str, intent_category: str, extra_context: str = "") -> dict:
    user_prompt = f"""
CWD: {cwd}
INTENT: {intent_category}

TASK:
{task}

CONTEXT:
{extra_context}

Return ONLY valid JSON.
"""

    raw = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.2)
    return json.loads(raw)
