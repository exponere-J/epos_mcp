from __future__ import annotations

import json
from typing import Any, Dict

from engine.llm_client import try_parse_json, repair_to_json

def parse_or_repair_json(*, model: str, system_prompt: str, raw_text: str) -> Dict[str, Any]:
    try:
        obj = try_parse_json(raw_text)
        if not isinstance(obj, dict):
            raise ValueError("JSON must be an object at top-level.")
        return obj
    except Exception:
        repaired = repair_to_json(model, system_prompt, raw_text)
        obj = json.loads(repaired)
        if not isinstance(obj, dict):
            raise ValueError("Repaired JSON must be an object at top-level.")
        return obj
