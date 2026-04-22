#!/usr/bin/env python3
# EPOS Artifact — Bridge Protocol (2026-04-22)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
directive_queue.py — Directive Intake for the Forge
====================================================
When a new FORGE_DIRECTIVE_*.md lands via the bridge ingestion runner,
this handler:

  1. extracts the directive_id from the filename (e.g. FORGE_DIR_AZ_ARMS_20260421)
  2. writes a queue entry to context_vault/state/directive_queue.jsonl
  3. emits 'forge.directive.queued' on the event bus
  4. optionally fires a webhook for live Forge pickup

Does NOT parse directive content — that's the Forge's job. The queue
preserves arrival order + supports idempotent re-ingestion of the same
directive (returns already_queued=True without duplicating).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

_QUEUE = Path(os.getenv("FORGE_DIRECTIVE_QUEUE",
                        "context_vault/state/directive_queue.jsonl"))
_REPO = Path(os.getenv("EPOS_ROOT", "."))


def _extract_id(path: Path) -> str:
    # Prefer the explicit Directive ID line in the file body if present
    try:
        body = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*Directive ID:\*\*\s*`([^`]+)`", body)
        if m:
            return m.group(1)
    except Exception:
        pass
    return path.stem


def queue_directive(path: str) -> dict:
    p = (_REPO / path).resolve() if not Path(path).is_absolute() else Path(path)
    if not p.exists():
        return {"status": "error", "reason": f"missing: {path}"}

    directive_id = _extract_id(p)
    body = p.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]

    # Idempotency check — scan queue for same directive_id + sha
    if _QUEUE.exists():
        for line in _QUEUE.read_text().splitlines():
            if not line.strip():
                continue
            try:
                prev = json.loads(line)
            except Exception:
                continue
            if prev.get("directive_id") == directive_id and prev.get("sha256_16") == sha:
                return {"status": "already_queued",
                        "directive_id": directive_id,
                        "queued_at": prev.get("queued_at")}

    entry = {
        "directive_id": directive_id,
        "path": str(p),
        "sha256_16": sha,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }
    _QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with _QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    try:
        from epos_event_bus import EPOSEventBus  # type: ignore
        EPOSEventBus().publish(
            "forge.directive.queued", entry,
            source_module="bridge.directive_queue",
        )
    except Exception:
        pass

    return {"status": "queued", **entry}


if __name__ == "__main__":
    sample = next(Path("missions").glob("FORGE_DIRECTIVE_*.md"), None)
    if sample:
        print(queue_directive(str(sample)))
    else:
        print("no sample directive found")
