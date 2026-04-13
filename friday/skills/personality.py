#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
personality.py — Friday System Prompt Assembler
================================================
Constitutional Authority: EPOS Constitution v3.1

Assembles Friday's system prompt from:
  1. identity.json (core archetype, voice, principles)
  2. Runtime context (current metrics, active threads, pending alerts)
  3. Operator profile (who Jamie is right now)

Used by any skill that needs to invoke an LLM as Friday.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

SOUL_DIR = Path(__file__).resolve().parent.parent / "soul"
IDENTITY_PATH = SOUL_DIR / "identity.json"


def get_identity() -> dict:
    if IDENTITY_PATH.exists():
        return json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
    return {}


def build_system_prompt(context: dict = None) -> str:
    """
    Assemble Friday's system prompt.

    context keys (all optional):
      active_threads   — list of thread summaries
      pending_alerts   — list of alert strings
      metric_snapshot  — dict of key metrics
      date_str         — override date string
    """
    identity = get_identity()
    ctx = context or {}

    date_str = ctx.get("date_str") or datetime.now(timezone.utc).strftime("%A %B %d, %Y %H:%M UTC")

    personality = identity.get("personality", {})
    principles = identity.get("principles", [])
    capabilities = identity.get("capabilities", [])

    lines = [
        f"You are {identity.get('name', 'Friday')}, {identity.get('role', 'EPOS orchestrator')}.",
        f"Archetype: {identity.get('archetype', 'Chief of Staff')}. Operator: {identity.get('operator', 'Jamie')}.",
        "",
        f"Voice: {personality.get('voice', '')}",
        f"Disposition: {personality.get('disposition', '')}",
        f"Commitment: {personality.get('commitment', '')}",
        "",
        "Principles:",
    ]
    for p in principles:
        lines.append(f"  - {p}")

    lines += [
        "",
        f"Capabilities: {', '.join(capabilities)}",
        f"Current time: {date_str}",
    ]

    if ctx.get("metric_snapshot"):
        lines += ["", "Current metrics:"]
        for k, v in list(ctx["metric_snapshot"].items())[:8]:
            lines.append(f"  {k}: {v}")

    if ctx.get("active_threads"):
        lines += ["", "Active threads (requiring attention):"]
        for t in ctx["active_threads"][:5]:
            lines.append(f"  - {t}")

    if ctx.get("pending_alerts"):
        lines += ["", "Pending alerts:"]
        for a in ctx["pending_alerts"][:5]:
            lines.append(f"  ⚠ {a}")

    return "\n".join(lines)


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    prompt = build_system_prompt({
        "metric_snapshot": {"event_bus_entries": 293, "active_missions": 0},
        "active_threads": ["Client: TTLG diagnostic pending since 2026-04-07"],
        "pending_alerts": ["governance-gate last seen 6h ago"],
    })
    print(prompt)
    assert "Friday" in prompt
    assert "Chief of Staff" in prompt
    print("\nPASS: personality")
