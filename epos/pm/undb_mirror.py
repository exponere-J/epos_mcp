#!/usr/bin/env python3
# EPOS Artifact — BUILD 68 (PM Surface Bidirectional Mirror)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X
"""
undb_mirror.py — Bidirectional sync: epos/pm/store.py ↔ Undb

PMStore is the single writer inside EPOS (Article VII); this mirror
reflects PMStore rows into Undb tables and accepts Undb changes as
read-only signals routed through PMStore, preserving single-writer
discipline.

Pattern:
  PM → Undb:  periodic diff; apply adds/updates via Undb REST
  Undb → PM:  webhook → event bus → PMStore.apply_external_signal
              (which validates then writes — never a direct write)

Runs as a daemon OR a cron tick. Idempotent via row-level SHA.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
STATE_FILE = Path(os.getenv("EPOS_PM_UNDB_STATE",
                              str(REPO / "context_vault" / "pm" / "undb_sync_state.json")))
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

UNDB_URL = os.getenv("UNDB_URL", "http://undb:3000")
UNDB_TOKEN = os.getenv("UNDB_TOKEN", "")


def _row_sha(row: dict) -> str:
    return hashlib.sha256(
        json.dumps(row, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def _load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_sync": "", "row_shas": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def sync_pm_to_undb() -> dict[str, Any]:
    """Read PMStore rows, diff against last-known SHAs, push deltas."""
    state = _load_state()
    shas = state.get("row_shas", {})

    try:
        from epos.pm.store import PMStore  # type: ignore
        store = PMStore()
        rows = store.list_all()
    except Exception as e:
        return {"status": "pm_store_unavailable", "error": f"{type(e).__name__}: {e}"}

    added = 0
    updated = 0
    for row in rows:
        rid = str(row.get("id", ""))
        if not rid:
            continue
        sha = _row_sha(row)
        if shas.get(rid) != sha:
            try:
                import requests
                headers = {"Authorization": f"Bearer {UNDB_TOKEN}"} if UNDB_TOKEN else {}
                r = requests.post(f"{UNDB_URL}/api/rows", json=row,
                                    headers=headers, timeout=10)
                if r.status_code in (200, 201, 204):
                    if rid in shas: updated += 1
                    else: added += 1
                    shas[rid] = sha
            except Exception:
                pass  # Undb may not be running yet

    state["row_shas"] = shas
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)
    return {"status": "complete", "rows_added": added, "rows_updated": updated,
            "total_tracked": len(shas)}


def ingest_undb_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """Undb → PMStore: route webhook through single-writer path."""
    try:
        from epos.pm.store import PMStore
        store = PMStore()
        if hasattr(store, "apply_external_signal"):
            return store.apply_external_signal("undb", payload)
        # If apply_external_signal doesn't exist yet, log for later
    except Exception:
        pass
    # Log the incoming signal for Architect review
    LOG = STATE_FILE.parent / "undb_incoming.jsonl"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                             "payload": payload}) + "\n")
    return {"status": "logged_pending_pm_writer", "log": str(LOG)}


if __name__ == "__main__":
    print(json.dumps(sync_pm_to_undb(), indent=2))
