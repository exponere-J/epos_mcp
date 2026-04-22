#!/usr/bin/env python3
# EPOS Artifact — Bridge Protocol (2026-04-22)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
persona_reloader.py — SCC Persona Hot-Swap
===========================================
Invalidates SCC's cached persona when the persona file changes on disk,
so the next SCC run picks up the new text without a process restart.

Designed for the SCC Architect persona at nodes/scc/personas/architect.md
but applies to any persona under nodes/scc/personas/.

The reloader does NOT execute code or prompt LLMs — it only bumps a
version stamp and emits an event. SCC consumers observe the version and
refresh their in-memory prompt on next invocation.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_STATE_DIR = Path(os.getenv("SCC_PERSONA_STATE",
                             "context_vault/state/scc_personas"))


def reload_architect_persona(path: str) -> dict:
    """Bump persona version, hash its content, emit event, return receipt."""
    p = Path(path)
    if not p.exists():
        return {"status": "error", "reason": f"persona not found: {path}"}

    content = p.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    name = p.stem  # "architect" for architect.md
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = _STATE_DIR / f"{name}.json"

    prior = {}
    if state_file.exists():
        try:
            prior = json.loads(state_file.read_text())
        except Exception:
            prior = {}

    version = int(prior.get("version", 0)) + 1
    record = {
        "name": name,
        "path": str(p),
        "version": version,
        "sha256_16": sha,
        "reloaded_at": datetime.now(timezone.utc).isoformat(),
        "previous_sha256_16": prior.get("sha256_16"),
    }
    state_file.write_text(json.dumps(record, indent=2))

    try:
        from epos_event_bus import EPOSEventBus  # type: ignore
        EPOSEventBus().publish(
            f"scc.persona.reloaded.{name}",
            record,
            source_module="bridge.persona_reloader",
        )
    except Exception:
        pass

    return {"status": "reloaded", **record}


if __name__ == "__main__":
    target = "nodes/scc/personas/architect.md"
    if Path(target).exists():
        print(reload_architect_persona(target))
    else:
        print(f"skip: {target} not present")
