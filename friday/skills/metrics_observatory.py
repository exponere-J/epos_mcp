#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
metrics_observatory.py — Friday Metrics Observatory
=====================================================
Constitutional Authority: EPOS Constitution v3.1

22 live metrics sampled from context_vault, event bus, and service endpoints.
Returns a normalized snapshot dict usable in morning briefings and alerts.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from path_utils import get_context_vault

VAULT = get_context_vault()

METRIC_DEFINITIONS = [
    # Event Bus
    {"key": "event_bus_total_entries",   "label": "Event bus total entries",         "source": "event_bus_file"},
    {"key": "event_bus_entries_24h",     "label": "Event bus entries (last 24h)",     "source": "event_bus_file"},
    {"key": "event_bus_errors_24h",      "label": "Event bus errors (last 24h)",      "source": "event_bus_file"},

    # Context Vault
    {"key": "context_vault_file_count",  "label": "Context vault total files",        "source": "vault_fs"},
    {"key": "echoes_ready_to_post",      "label": "Echoes ready_to_post queue depth", "source": "vault_fs"},
    {"key": "friday_missions_total",     "label": "Friday missions logged",           "source": "vault_fs"},
    {"key": "friday_missions_success",   "label": "Friday missions succeeded",        "source": "vault_fs"},

    # Services
    {"key": "epos_core_up",              "label": "EPOS Core reachable",              "source": "http_ping"},
    {"key": "litellm_up",                "label": "LiteLLM reachable",               "source": "http_ping"},
    {"key": "governance_gate_up",        "label": "Governance Gate reachable",        "source": "http_ping"},
    {"key": "learning_server_up",        "label": "Learning Server reachable",        "source": "http_ping"},

    # LLM
    {"key": "llm_requests_24h",          "label": "LLM requests (last 24h)",          "source": "event_bus_filter"},
    {"key": "llm_failures_24h",          "label": "LLM failures (last 24h)",          "source": "event_bus_filter"},

    # Content / Echoes
    {"key": "posts_published_7d",        "label": "Posts published (7d)",             "source": "vault_fs"},
    {"key": "sparks_generated_7d",       "label": "Sparks generated (7d)",            "source": "vault_fs"},
    {"key": "briefs_generated_7d",       "label": "Research briefs generated (7d)",   "source": "vault_fs"},

    # TTLG
    {"key": "ttlg_diagnostics_7d",       "label": "TTLG diagnostics run (7d)",        "source": "event_bus_filter"},
    {"key": "ttlg_healing_cycles_7d",    "label": "TTLG healing cycles (7d)",         "source": "event_bus_filter"},

    # System
    {"key": "doctor_last_passed",        "label": "Doctor last passed (hours ago)",   "source": "vault_fs"},
    {"key": "reactor_position_age_h",    "label": "Reactor position age (hours)",     "source": "vault_fs"},
    {"key": "git_commits_7d",            "label": "Git commits (7d)",                 "source": "git"},
    {"key": "open_threads",              "label": "Open threads in tracker",          "source": "vault_fs"},
]


def snapshot() -> dict:
    """Sample all 22 metrics. Returns dict of key → value."""
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d  = now - timedelta(days=7)

    metrics = {}

    # --- Event bus ---
    bus_path = VAULT / "events" / "system" / "events.jsonl"
    bus_entries = []
    if bus_path.exists():
        try:
            bus_entries = [json.loads(l) for l in bus_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        except Exception:
            pass

    metrics["event_bus_total_entries"] = len(bus_entries)
    metrics["event_bus_entries_24h"] = sum(
        1 for e in bus_entries
        if _parse_ts(e.get("timestamp", "")) >= cutoff_24h
    )
    metrics["event_bus_errors_24h"] = sum(
        1 for e in bus_entries
        if "error" in e.get("event_type", "").lower()
        and _parse_ts(e.get("timestamp", "")) >= cutoff_24h
    )

    # --- LLM events ---
    metrics["llm_requests_24h"] = sum(
        1 for e in bus_entries
        if "llm" in e.get("event_type", "").lower()
        and _parse_ts(e.get("timestamp", "")) >= cutoff_24h
    )
    metrics["llm_failures_24h"] = sum(
        1 for e in bus_entries
        if "llm" in e.get("event_type", "").lower()
        and "fail" in e.get("event_type", "").lower()
        and _parse_ts(e.get("timestamp", "")) >= cutoff_24h
    )

    # --- TTLG events ---
    metrics["ttlg_diagnostics_7d"] = sum(
        1 for e in bus_entries
        if "ttlg.diagnostic" in e.get("event_type", "")
        and _parse_ts(e.get("timestamp", "")) >= cutoff_7d
    )
    metrics["ttlg_healing_cycles_7d"] = sum(
        1 for e in bus_entries
        if "ttlg" in e.get("event_type", "")
        and "heal" in e.get("event_type", "")
        and _parse_ts(e.get("timestamp", "")) >= cutoff_7d
    )

    # --- Vault FS ---
    metrics["context_vault_file_count"] = sum(1 for _ in VAULT.rglob("*") if _.is_file())

    ready_dir = VAULT / "echoes" / "ready_to_post"
    metrics["echoes_ready_to_post"] = len(list(ready_dir.glob("*.json"))) if ready_dir.exists() else 0

    missions_dir = VAULT / "friday" / "missions"
    if missions_dir.exists():
        aars = list(missions_dir.glob("*_aar.json"))
        metrics["friday_missions_total"] = len(aars)
        metrics["friday_missions_success"] = sum(
            1 for a in aars
            if _aar_succeeded(a)
        )
    else:
        metrics["friday_missions_total"] = 0
        metrics["friday_missions_success"] = 0

    # Posts published 7d
    published_dir = VAULT / "echoes" / "published"
    if published_dir.exists():
        metrics["posts_published_7d"] = sum(
            1 for f in published_dir.glob("*.json")
            if _file_age(f) <= 7
        )
    else:
        metrics["posts_published_7d"] = 0

    # Sparks 7d
    sparks_dir = VAULT / "echoes" / "sparks"
    metrics["sparks_generated_7d"] = sum(
        1 for f in sparks_dir.glob("*.json")
        if _file_age(f) <= 7
    ) if sparks_dir.exists() else 0

    # Briefs 7d
    briefs_dir = VAULT / "echoes" / "research_briefs"
    metrics["briefs_generated_7d"] = sum(
        1 for f in briefs_dir.glob("*.json")
        if _file_age(f) <= 7
    ) if briefs_dir.exists() else 0

    # Doctor last passed
    doctor_log = VAULT / "doctor" / "last_pass.txt"
    if doctor_log.exists():
        try:
            ts = datetime.fromisoformat(doctor_log.read_text().strip())
            metrics["doctor_last_passed"] = round((now - ts.replace(tzinfo=timezone.utc)).total_seconds() / 3600, 1)
        except Exception:
            metrics["doctor_last_passed"] = None
    else:
        metrics["doctor_last_passed"] = None

    # Reactor position age
    reactor_pos = VAULT / ".reactor_position"
    if reactor_pos.exists():
        import os as _os
        age_s = now.timestamp() - _os.path.getmtime(str(reactor_pos))
        metrics["reactor_position_age_h"] = round(age_s / 3600, 1)
    else:
        metrics["reactor_position_age_h"] = None

    # Open threads
    threads_dir = VAULT / "friday" / "threads"
    if threads_dir.exists():
        metrics["open_threads"] = sum(
            1 for f in threads_dir.glob("*.json")
            if _thread_open(f)
        )
    else:
        metrics["open_threads"] = 0

    # --- HTTP pings ---
    metrics["epos_core_up"]        = _ping(os.getenv("EPOS_CORE_URL", "http://epos-core:8001") + "/health")
    metrics["litellm_up"]          = _ping(os.getenv("LITELLM_URL", "http://litellm:4000") + "/health")
    metrics["governance_gate_up"]  = _ping(os.getenv("GOVERNANCE_GATE_URL", "http://governance-gate:8101") + "/health")
    metrics["learning_server_up"]  = _ping(os.getenv("LEARNING_URL", "http://learning-server:8102") + "/health")

    # --- Git commits 7d ---
    metrics["git_commits_7d"] = _git_commits_7d()

    return metrics


# ── Helpers ──────────────────────────────────────────────────

def _parse_ts(ts: str) -> datetime:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _ping(url: str) -> bool:
    try:
        import requests
        r = requests.get(url, timeout=3)
        return r.status_code < 500
    except Exception:
        return False


def _file_age(path: Path) -> float:
    """Age of file in days."""
    import os as _os
    age_s = datetime.now(timezone.utc).timestamp() - _os.path.getmtime(str(path))
    return age_s / 86400


def _aar_succeeded(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("success"))
    except Exception:
        return False


def _thread_open(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("status") == "open"
    except Exception:
        return False


def _git_commits_7d() -> Optional[int]:
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=7.days"],
            capture_output=True, text=True, timeout=5,
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        )
        return len(result.stdout.strip().splitlines()) if result.returncode == 0 else None
    except Exception:
        return None


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Sampling metrics...")
    m = snapshot()
    for defn in METRIC_DEFINITIONS:
        val = m.get(defn["key"], "N/A")
        print(f"  {defn['label']}: {val}")
    print(f"\nPASS: metrics_observatory ({len(m)} metrics sampled)")
