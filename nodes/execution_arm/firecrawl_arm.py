#!/usr/bin/env python3
# EPOS Artifact — Tool Chain Transfer (2026-04-22)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §2
"""
firecrawl_arm.py — Firecrawl Arm (web scraping, API-based)
===========================================================
Market-awareness execution for Article XVI §2: "The organism MUST maintain
continuous market surveillance through FOTW sensors, Firecrawl, and Oracle
research."

Thin, callable wrapper around the Firecrawl HTTP API:
    - scrape(url)     — single-URL extraction
    - crawl(url)      — spider under same origin
    - search(query)   — web search (where supported)
    - map(url)        — enumerate reachable URLs from a seed

Deletion gate: not applicable (read-only scraper). Credit gate IS applied
— every call logs cost estimate to context_vault/bi/firecrawl_spend.jsonl
so Steward can surface spend in the morning briefing.

Universal call surface via nodes/execution_arm/callable.py when the
selector's arm == 'firecrawl' (not yet default; invoke explicitly via
mode_hint until reasoner is taught the signal).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_DIR = Path(os.getenv("EPOS_ARM_LOG_DIR", "context_vault/execution_arm"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "firecrawl.jsonl"
_SPEND_LOG = Path(os.getenv("EPOS_FIRECRAWL_SPEND",
                             "context_vault/bi/firecrawl_spend.jsonl"))

_API_BASE = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev")


@dataclass
class ArmResult:
    success: bool
    arm: str = "firecrawl"
    action: str = ""
    task: str = ""
    output: Any = None
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class FirecrawlArm:
    """Read-only web intelligence arm."""

    def __init__(self) -> None:
        self._api_key = os.getenv("FIRECRAWL_API_KEY", "")
        self._reason = ""
        try:
            import requests  # noqa: F401
            self._available = True
        except ImportError as e:
            self._available = False
            self._reason = f"requests not installed: {e}"

    def health(self) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "reason": self._reason}
        if not self._api_key:
            return {"status": "degraded", "reason": "FIRECRAWL_API_KEY not set"}
        return {
            "status": "operational",
            "api_base": _API_BASE,
            "log": str(_LOG_FILE),
            "spend_log": str(_SPEND_LOG),
        }

    # ── Public methods ─────────────────────────────────────────

    def scrape(self, url: str, formats: list[str] | None = None,
               context: dict[str, Any] | None = None) -> ArmResult:
        return self._call("scrape", {
            "url": url,
            "formats": formats or ["markdown"],
        }, task=f"scrape {url}", context=context)

    def crawl(self, url: str, limit: int = 20,
              context: dict[str, Any] | None = None) -> ArmResult:
        return self._call("crawl", {
            "url": url, "limit": limit,
        }, task=f"crawl {url} (limit={limit})", context=context)

    def search(self, query: str, limit: int = 10,
               context: dict[str, Any] | None = None) -> ArmResult:
        return self._call("search", {
            "query": query, "limit": limit,
        }, task=f"search '{query}' (limit={limit})", context=context)

    def map(self, url: str, context: dict[str, Any] | None = None) -> ArmResult:
        return self._call("map", {"url": url},
                          task=f"map {url}", context=context)

    # ── Internals ──────────────────────────────────────────────

    def _call(self, endpoint: str, payload: dict,
              task: str, context: dict[str, Any] | None) -> ArmResult:
        started = datetime.now(timezone.utc).isoformat()
        if not self._available or not self._api_key:
            return self._fail(endpoint, task, started,
                              self._reason or "FIRECRAWL_API_KEY not set")
        try:
            import requests
            r = requests.post(
                f"{_API_BASE}/v1/{endpoint}",
                headers={"Authorization": f"Bearer {self._api_key}",
                         "Content-Type": "application/json"},
                json=payload,
                timeout=int(os.getenv("FIRECRAWL_TIMEOUT", "90")),
            )
            if r.status_code in (200, 201, 202):
                data = r.json() if r.text else {}
                out = ArmResult(
                    success=True, arm="firecrawl", action=endpoint,
                    task=task, output=data,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    extras={"mission_id": (context or {}).get("mission_id", "")},
                )
                self._log(out)
                self._log_spend(endpoint, payload, out)
                return out
            return self._fail(endpoint, task, started,
                              f"HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:  # noqa: BLE001
            return self._fail(endpoint, task, started,
                              f"{type(e).__name__}: {e}")

    def _fail(self, endpoint: str, task: str, started: str, error: str) -> ArmResult:
        out = ArmResult(
            success=False, arm="firecrawl", action=endpoint, task=task,
            error=error, started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        self._log(out)
        return out

    def _log(self, result: ArmResult) -> None:
        try:
            with _LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result.to_dict(), default=str) + "\n")
        except Exception:
            pass

    def _log_spend(self, endpoint: str, payload: dict, result: ArmResult) -> None:
        # Rough cost estimate — refine when Firecrawl returns billing metadata
        estimates = {"scrape": 0.002, "crawl": 0.050, "search": 0.010, "map": 0.010}
        cost_usd = estimates.get(endpoint, 0.0)
        rec = {
            "timestamp": result.finished_at,
            "endpoint": endpoint,
            "task": result.task[:120],
            "estimated_cost_usd": cost_usd,
            "mission_id": result.extras.get("mission_id", ""),
        }
        try:
            _SPEND_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _SPEND_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass


if __name__ == "__main__":
    arm = FirecrawlArm()
    h = arm.health()
    print(f"firecrawl: {h['status']}" +
          (f" ({h.get('reason', '')})" if h.get('reason') else ""))
    print("PASS: firecrawl_arm (structural)")
