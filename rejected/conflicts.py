import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "out"

EVENT_EXTENSIONS = {".json", ".jsonl"}


def _load_event_file(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    try:
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    events.append(json.loads(line))
        elif path.suffix == ".json":
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    events.extend(data)
                else:
                    events.append(data)
    except Exception:
        # Fail-soft: conflicts shouldn't crash the router
        pass
    return events


def load_existing_events() -> List[Dict[str, Any]]:
    """
    Load all events previously written to OUT_DIR.
    This is intentionally simple and can be optimized later.
    """
    if not OUT_DIR.exists():
        return []

    all_events: List[Dict[str, Any]] = []
    for path in OUT_DIR.iterdir():
        if path.is_file() and path.suffix in EVENT_EXTENSIONS:
            all_events.extend(_load_event_file(path))
    return all_events


def detect_conflict(new_event: Dict[str, Any], existing_events: List[Dict[str, Any]]) -> bool:
    """
    Basic conflict: same type + same project.
    You can extend this later to include:
    - same file
    - same pipeline
    - overlapping time windows
    """
    n_type = new_event.get("type")
    n_payload = new_event.get("payload", {})
    n_project = n_payload.get("project")

    for e in existing_events:
        if e.get("id") == new_event.get("id"):
            continue
        if e.get("type") != n_type:
            continue

        payload = e.get("payload", {})
        if n_project and payload.get("project") == n_project:
            return True

    return False
