#!/usr/bin/env python3
# EPOS Artifact — BUILD 4 (MiroFish Stage 1)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §2
"""
run_pricing_sim.py — CCP Pack Pricing Sweep

Drives a 4-price MiroFish run for the CCP Pack (or any other Stage-1 product)
across persona segments. Submits to either:

  - the local MiroFish kernel  (containers/mirofish/simulator.py on port 8110)
  - the upstream MiroFish backend (external/mirofish/backend/run.py)

via the LiteLLM router at $LITELLM_ENDPOINT (default http://localhost:4000/v1).

Outputs:
    context_vault/simulation/runs/<seed_id>_<run_ts>.json   (per price)
    context_vault/simulation/reports/pricing_sweep_<product>_<ts>.md (rollup)

Usage:
    python -m nodes.simulation.run_pricing_sim --product ccp_prompt_pack
    python -m nodes.simulation.run_pricing_sim --product premortem_kit --target upstream
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SEED_DIR = REPO / "context_vault" / "simulation" / "seeds"
RUN_DIR = REPO / "context_vault" / "simulation" / "runs"
REPORT_DIR = REPO / "context_vault" / "simulation" / "reports"

LOCAL_TARGET = os.getenv("MIROFISH_LOCAL_URL", "http://localhost:8110")
UPSTREAM_TARGET = os.getenv("MIROFISH_UPSTREAM_URL", "http://localhost:5001")


def load_seeds_for(product_id: str) -> list[dict]:
    seeds = []
    for p in sorted(SEED_DIR.glob(f"{product_id}_*.json")):
        seeds.append(json.loads(p.read_text()))
    return seeds


def submit_local(seed: dict) -> dict:
    """Hit the local MiroFish kernel built in containers/mirofish/simulator.py."""
    import requests
    payload = {
        "scenario_id": seed["scenario"]["scenario_id"],
        "product": {
            "title": seed["product"]["title"],
            "price_usd": seed["product"]["price_usd"],
            "copy": "",
            "metadata": {"platform": seed["product"]["platform"]},
        },
        "avatars": [p["persona_id"] for p in seed["personas"]],
        "cycles": seed["scenario"]["cycles"],
        "agents_per_cycle": seed["scenario"]["agents_per_cycle"],
        "model_pool": seed["model_pool"],
    }
    r = requests.post(f"{LOCAL_TARGET}/simulate", json=payload, timeout=30)
    r.raise_for_status()
    run_id = r.json()["run_id"]
    return {"run_id": run_id, "submitted_at": _ts()}


def poll_local(run_id: str, timeout_s: int = 1800, interval_s: int = 10) -> dict:
    import requests
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.get(f"{LOCAL_TARGET}/runs/{run_id}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") in ("complete", "failed"):
                return data
        time.sleep(interval_s)
    return {"status": "timeout", "run_id": run_id}


def submit_upstream(seed: dict) -> dict:
    """Hit the upstream MiroFish Flask backend (different API surface)."""
    # Upstream MiroFish expects a different payload shape; this is a stub
    # that the Forge fills out once Jamie's WSL has the upstream running.
    return {"status": "upstream_target_not_yet_implemented",
            "seed_id": seed["seed_id"],
            "next": "Forge Directive FORGE_DIR_MIROFISH_UPSTREAM_BRIDGE pending"}


def write_run(seed: dict, result: dict) -> Path:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{seed['seed_id']}_{int(time.time())}.json"
    out = RUN_DIR / fname
    out.write_text(json.dumps({"seed": seed, "result": result}, indent=2) + "\n")
    return out


def write_report(product_id: str, runs: list[tuple[dict, dict]]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPORT_DIR / f"pricing_sweep_{product_id}_{ts}.md"

    lines = [
        f"# Pricing Sweep — {product_id}",
        f"\n**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Runs:** {len(runs)}",
        f"\n## Results by price\n",
        "| Price | Conversion | Median willingness | Top objection |",
        "|---|---|---|---|",
    ]
    for seed, result in runs:
        rep = (result.get("report") or {})
        price = seed["product"]["price_usd"]
        conv = rep.get("conversion_rate", "—")
        will = rep.get("median_willingness_usd", "—")
        obj = (rep.get("top_objections") or [{}])[0].get("objection", "—") if rep.get("top_objections") else "—"
        lines.append(f"| ${price:.0f} | {conv} | {will} | {obj} |")

    lines.append("\n## Recommendation\n")
    lines.append("(Inferred from highest expected revenue: conversion × price)")

    out.write_text("\n".join(lines) + "\n")
    return out


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", required=True, help="Product id (e.g. ccp_prompt_pack)")
    ap.add_argument("--target", choices=["local", "upstream"], default="local",
                     help="MiroFish target (local kernel or upstream backend)")
    ap.add_argument("--blocking", action="store_true",
                     help="Block until each run completes (default async)")
    args = ap.parse_args(argv)

    seeds = load_seeds_for(args.product)
    if not seeds:
        print(f"No seeds for product {args.product!r}. Run seed_builder first.", file=sys.stderr)
        return 1

    print(f"Found {len(seeds)} seeds for {args.product} "
          f"(prices: {sorted(s['product']['price_usd'] for s in seeds)})")

    runs = []
    for seed in sorted(seeds, key=lambda s: s["product"]["price_usd"]):
        try:
            if args.target == "local":
                submit = submit_local(seed)
                if args.blocking:
                    result = poll_local(submit["run_id"])
                else:
                    result = submit
            else:
                result = submit_upstream(seed)
        except Exception as e:  # noqa: BLE001
            result = {"status": "submit_error", "error": f"{type(e).__name__}: {e}"}

        path = write_run(seed, result)
        print(f"  ${seed['product']['price_usd']:.0f}: {result.get('status', '?')}  → {path}")
        runs.append((seed, result))

    if args.blocking and args.target == "local":
        report = write_report(args.product, runs)
        print(f"\nReport: {report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
