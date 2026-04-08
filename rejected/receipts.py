from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Dict


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# Backward-compatible alias (some modules import _utc_now)
def _utc_now() -> str:
    return utc_now()


def payload_hash(payload: Any) -> str:
    try:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    except Exception:
        raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_error(e: Exception) -> Dict[str, Any]:
    return {
        "type": e.__class__.__name__,
        "message": str(e),
    }


@dataclass
class Receipt:
    run_id: str
    task_id: str
    task_type: str

