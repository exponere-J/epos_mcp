from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("engine/contracts/build_contract.schema.json")

def load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def validate_contract(contract: Dict[str, Any]) -> None:
    schema = load_schema()
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(contract), key=lambda e: e.path)
    if errors:
        msgs = []
        for e in errors[:10]:
            loc = ".".join([str(x) for x in e.path]) or "(root)"
            msgs.append(f"{loc}: {e.message}")
        raise ValueError("Contract schema invalid:\n" + "\n".join(msgs))
