import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class EventQueue:
    """
    Very simple JSONL-backed event queue.

    Each event is a dict with at least:
      - id
      - type
      - payload
      - created_at
      - status
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def enqueue(self, event_type: str, payload: Dict[str, Any], status: str = "pending") -> Dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "payload": payload,
            "created_at": self._now(),
            "status": status,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def read_all(self) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [e for e in self.read_all() if e.get("status") == status]
