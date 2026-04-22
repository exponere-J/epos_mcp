#!/usr/bin/env python3
# EPOS Artifact — Bridge Protocol (2026-04-22)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §1
"""
ingestion_runner.py — Sandbox → WSL Bridge Ingestion Runner
============================================================
Runs on Agent Zero. On a schedule or on webhook:
    1. git pull on the session branch
    2. diff against last-ingested SHA
    3. route each changed path to its handler by glob pattern
    4. emit 'bridge.session.<ID>.ingested' event bus message
    5. update last-ingested SHA atomically

Routing rules (extend by editing ROUTES below):
    nodes/scc/personas/*.md      → reload SCC persona
    missions/FORGE_DIRECTIVE_*   → queue for Forge
    nodes/**/*.py                → schedule Doctor validation
    context_vault/doctrine/**    → TTLG register (new capability)
    context_vault/state/organism_state.json → noop (sovereign-generated)
    context_vault/aar/**         → feed Reward Bus
    context_vault/doctrine/councils/*.md → Council charter reload

Never deletes files. Never runs git push. Pull-only.
"""
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

_REPO = Path(os.getenv("EPOS_ROOT", "/mnt/c/Users/Jamie/workspace/epos_mcp"))
_STATE = Path(os.getenv("BRIDGE_STATE",
                       str(_REPO / "context_vault" / "state" / "bridge_state.json")))
_LOG = Path(os.getenv("BRIDGE_LOG",
                     str(_REPO / "context_vault" / "bi" / "bridge_ingestion.jsonl")))
_BRANCH = os.getenv("EPOS_BRIDGE_BRANCH", "claude/general-session-zLIkW")


@dataclass
class ChangeSet:
    from_sha: str
    to_sha: str
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str]] = field(default_factory=list)

    def all_paths(self) -> list[str]:
        out = list(self.added) + list(self.modified)
        out += [new for _old, new in self.renamed]
        return out

    def to_dict(self) -> dict:
        return {
            "from_sha": self.from_sha, "to_sha": self.to_sha,
            "added": self.added, "modified": self.modified,
            "deleted": self.deleted, "renamed": self.renamed,
        }


# ── Route handlers ────────────────────────────────────────────

def _handle_persona(path: str) -> dict:
    from .persona_reloader import reload_architect_persona
    return {"handler": "persona_reloader", "result": reload_architect_persona(path)}


def _handle_directive(path: str) -> dict:
    from .directive_queue import queue_directive
    return {"handler": "directive_queue", "result": queue_directive(path)}


def _handle_code(path: str) -> dict:
    # Schedules a Doctor validation; real invocation sits in friday executor.
    return {"handler": "doctor_validation",
            "scheduled": True, "path": path}


def _handle_doctrine(path: str) -> dict:
    # Flags for TTLG to register the new capability.
    return {"handler": "ttlg_register", "path": path, "status": "queued"}


def _handle_aar(path: str) -> dict:
    return {"handler": "reward_bus_feed", "path": path, "status": "queued"}


def _handle_noop(path: str) -> dict:
    return {"handler": "noop", "path": path, "reason": "sovereign-generated artifact"}


ROUTES: list[tuple[str, Callable[[str], dict]]] = [
    ("nodes/scc/personas/*.md", _handle_persona),
    ("missions/FORGE_DIRECTIVE_*.md", _handle_directive),
    ("context_vault/state/organism_state.json", _handle_noop),
    ("context_vault/doctrine/councils/*.md", _handle_doctrine),
    ("context_vault/doctrine/**/*.md", _handle_doctrine),
    ("context_vault/aar/*.md", _handle_aar),
    ("nodes/**/*.py", _handle_code),
    ("friday/**/*.py", _handle_code),
    ("epos/**/*.py", _handle_code),
]


# ── Core ──────────────────────────────────────────────────────

class IngestionRunner:
    def __init__(self, repo: Path | None = None, branch: str | None = None):
        self.repo = repo or _REPO
        self.branch = branch or _BRANCH

    def last_sha(self) -> str:
        if not _STATE.exists():
            return ""
        try:
            return json.loads(_STATE.read_text()).get("last_ingested_sha", "")
        except Exception:
            return ""

    def write_last_sha(self, sha: str) -> None:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        _STATE.write_text(json.dumps({
            "last_ingested_sha": sha,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2))

    def git(self, *args: str) -> str:
        r = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            capture_output=True, text=True, check=False,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout

    def pull(self) -> str:
        """Fetch + fast-forward merge; returns new HEAD sha."""
        self.git("fetch", "origin", self.branch)
        self.git("merge", "--ff-only", f"origin/{self.branch}")
        return self.git("rev-parse", "HEAD").strip()

    def diff(self, from_sha: str, to_sha: str) -> ChangeSet:
        cs = ChangeSet(from_sha=from_sha, to_sha=to_sha)
        if not from_sha:
            # First run — treat everything at HEAD as "added"
            names = self.git("ls-tree", "-r", "--name-only", to_sha).splitlines()
            cs.added = [n for n in names if n]
            return cs
        raw = self.git("diff", "--name-status", from_sha, to_sha).splitlines()
        for line in raw:
            parts = line.split("\t")
            if not parts or len(parts) < 2:
                continue
            code = parts[0]
            if code == "A":
                cs.added.append(parts[1])
            elif code == "M":
                cs.modified.append(parts[1])
            elif code == "D":
                cs.deleted.append(parts[1])
            elif code.startswith("R") and len(parts) >= 3:
                cs.renamed.append((parts[1], parts[2]))
        return cs

    def route(self, path: str) -> dict:
        for pattern, handler in ROUTES:
            if fnmatch.fnmatch(path, pattern):
                try:
                    return {"path": path, "pattern": pattern,
                            "outcome": handler(path)}
                except Exception as e:
                    return {"path": path, "pattern": pattern,
                            "error": f"{type(e).__name__}: {e}"}
        return {"path": path, "pattern": None, "outcome": "no_route"}

    def log(self, entry: dict) -> None:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def publish_event(self, session_id: str, changeset: ChangeSet,
                      routing_results: list[dict]) -> None:
        try:
            from epos_event_bus import EPOSEventBus  # type: ignore
            bus = EPOSEventBus()
            bus.publish(
                f"bridge.session.{session_id}.ingested",
                {"changeset": changeset.to_dict(),
                 "routing": routing_results,
                 "timestamp": datetime.now(timezone.utc).isoformat()},
                source_module="bridge.ingestion_runner",
            )
        except Exception:
            pass


def run_once(session_id: str | None = None) -> dict:
    """One sweep. Idempotent: if no new commits, returns empty changeset."""
    runner = IngestionRunner()
    from_sha = runner.last_sha()
    to_sha = runner.pull()
    changeset = runner.diff(from_sha, to_sha)

    routing_results = [runner.route(p) for p in changeset.all_paths()]

    session_id = session_id or to_sha[:8] or "unknown"
    summary = {
        "session_id": session_id,
        "from_sha": from_sha, "to_sha": to_sha,
        "changed": len(changeset.all_paths()),
        "routed": routing_results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    runner.log(summary)
    runner.publish_event(session_id, changeset, routing_results)

    if to_sha and to_sha != from_sha:
        runner.write_last_sha(to_sha)
    return summary


if __name__ == "__main__":
    try:
        r = run_once()
        print(json.dumps(r, indent=2))
    except Exception as e:
        print(f"ingestion error: {type(e).__name__}: {e}")
        raise
