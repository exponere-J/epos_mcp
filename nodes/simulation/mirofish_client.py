#!/usr/bin/env python3
# EPOS Artifact — MiroFish Stage 1
# Constitutional Authority: Articles V, X, XVI §2
"""
mirofish_client.py — Python Client for the MiroFish Sidecar

Lightweight HTTP client. Submits scenarios to the MiroFish container,
polls for results, returns the report dict.

Usage (in-process):
    from nodes.simulation import MiroFishClient, submit
    client = MiroFishClient()
    run_id = client.submit(scenario)
    report = client.await_report(run_id, timeout_s=900)

    # Or shortcut:
    report = submit(scenario, blocking=True, timeout_s=900)
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .scenario import Scenario

_MIROFISH_URL = os.getenv("MIROFISH_URL", "http://mirofish:8110")
_RESULTS_DIR = Path(os.getenv("MIROFISH_RESULTS",
                                "context_vault/simulation"))


class MiroFishClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or _MIROFISH_URL).rstrip("/")

    def health(self) -> dict[str, Any]:
        try:
            import requests
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                return r.json()
            return {"status": "degraded", "code": r.status_code}
        except Exception as e:
            return {"status": "unavailable", "error": f"{type(e).__name__}: {e}"}

    def submit(self, scenario: Scenario) -> str:
        import requests
        r = requests.post(
            f"{self.base_url}/simulate",
            data=scenario.to_json(),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["run_id"]

    def poll(self, run_id: str) -> dict[str, Any]:
        import requests
        r = requests.get(f"{self.base_url}/runs/{run_id}", timeout=10)
        r.raise_for_status()
        return r.json()

    def await_report(self, run_id: str, timeout_s: int = 900,
                     poll_s: int = 5) -> dict[str, Any]:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            state = self.poll(run_id)
            if state.get("status") in ("complete", "failed"):
                return state
            time.sleep(poll_s)
        return {"status": "timeout", "run_id": run_id, "timeout_s": timeout_s}


def submit(scenario: Scenario, blocking: bool = False,
           timeout_s: int = 900) -> dict[str, Any] | str:
    client = MiroFishClient()
    run_id = client.submit(scenario)
    if not blocking:
        return run_id
    return client.await_report(run_id, timeout_s)


def health() -> dict[str, Any]:
    return MiroFishClient().health()


if __name__ == "__main__":
    print("MiroFish client health:", health())
