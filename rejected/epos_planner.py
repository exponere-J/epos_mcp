import json
from openrouter_client import call_openrouter

SYSTEM = """
You are EPOS.Local.Planner.

Your job:
- Turn a natural language user request into a JSON action plan.
- Each step has an 'action' type.

Allowed actions:
- "shell": execute a shell command.
- "type": type text to active window.
- "key": press a single keyboard key.
- "mouse_move": move mouse to coordinates.
- "mouse_click": click the mouse.
- "screenshot": take screenshot.

JSON format:
[
  {"action": "shell", "command": "ls"},
  {"action": "mouse_move", "x": 300, "y": 600},
  {"action": "mouse_click", "button": "left"},
  {"action": "type", "text": "hello world"}
]

Do NOT write anything except pure JSON.
"""

def plan(task: str):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task}
    ]

    raw = call_openrouter(messages)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("[")
        end = raw.rfind("]")
        return json.loads(raw[start:end+1])
