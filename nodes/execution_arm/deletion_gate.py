#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §3
"""
deletion_gate.py — Sovereign-Approved Deletion Guard
=====================================================
Hard rule (Sovereign directive, 2026-04-21):
    "Deletion only upon approval."

Every destructive operation (file unlink, directory removal, record delete,
table drop, tab close-with-unsaved-state) performed by any execution-arm
agent MUST pass through `guard()` first. Unapproved deletions are escalated,
logged, and NEVER silently executed.

Approval semantics:
    context["deletion_approved"] = ["/path/to/file", "db:users/42", ...]
        — explicit targets the Sovereign approved for this mission
    context["deletion_approved"] = "*"
        — BLANKET approval. Logs a SEVERE warning. Should be rare.
    context["deletion_approved"] absent or empty
        — all deletions blocked

Every attempt (approved or blocked) is logged to
    context_vault/bi/deletion_attempts.jsonl
for Reward Bus scoring and audit.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_PATH = Path(
    os.getenv("EPOS_DELETION_LOG", "context_vault/bi/deletion_attempts.jsonl")
)


@dataclass(frozen=True)
class GuardResult:
    approved: bool
    target: str
    reason: str
    blanket: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "target": self.target,
            "reason": self.reason,
            "blanket": self.blanket,
        }


def guard(target: str, context: dict[str, Any] | None) -> GuardResult:
    """Authoritative approval check for any deletion attempt.

    Args:
        target: canonical identifier of what would be deleted
                (absolute path, db row key, URL, etc.)
        context: per-mission context dict. May contain 'deletion_approved'.

    Returns:
        GuardResult describing the outcome. Callers MUST honor .approved.
    """
    ctx = context or {}
    approved_list = ctx.get("deletion_approved")

    result: GuardResult
    if approved_list == "*":
        result = GuardResult(
            approved=True,
            target=target,
            reason="blanket Sovereign override",
            blanket=True,
        )
    elif isinstance(approved_list, (list, tuple, set)) and target in approved_list:
        result = GuardResult(
            approved=True,
            target=target,
            reason="explicit target approval",
        )
    else:
        result = GuardResult(
            approved=False,
            target=target,
            reason="no Sovereign approval for this target",
        )

    _log_attempt(result, ctx)
    return result


def _log_attempt(result: GuardResult, context: dict[str, Any]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mission_id": context.get("mission_id", "unknown"),
        "arm": context.get("arm", "unknown"),
        "target": result.target,
        "approved": result.approved,
        "blanket": result.blanket,
        "reason": result.reason,
    }
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


class DeletionRefused(PermissionError):
    """Raised when an arm attempts deletion without Sovereign approval."""


def enforce(target: str, context: dict[str, Any] | None) -> None:
    """Raise if deletion is not approved. Arms call this at the destructive step."""
    r = guard(target, context)
    if not r.approved:
        raise DeletionRefused(
            f"Deletion refused for '{target}': {r.reason}. "
            f"Add target to context['deletion_approved'] to authorize."
        )


if __name__ == "__main__":
    r = guard("/tmp/test.txt", {"mission_id": "T1"})
    assert not r.approved
    print("unapproved block OK")

    r = guard("/tmp/test.txt", {"mission_id": "T2", "deletion_approved": ["/tmp/test.txt"]})
    assert r.approved and not r.blanket
    print("explicit approval OK")

    r = guard("/tmp/test.txt", {"mission_id": "T3", "deletion_approved": "*"})
    assert r.approved and r.blanket
    print("blanket approval OK (flagged)")

    try:
        enforce("/tmp/x", {"mission_id": "T4"})
    except DeletionRefused as e:
        print(f"enforce raised OK: {e}")

    print("PASS: deletion_gate")
