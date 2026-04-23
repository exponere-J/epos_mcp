#!/usr/bin/env python3
# EPOS Artifact — BUILD 4 (MiroFish Stage 1)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §2
"""
seed_builder.py — Build MiroFish Simulation Seeds From Brand DNA

Reads `context_vault/brand/brand_dna.json` and the 5 persona configs
under `nodes/simulation/personas/`, then constructs Scenario objects
ready to feed the local MiroFish kernel (containers/mirofish/simulator.py)
or the upstream MiroFish API (external/mirofish/backend/run.py).

Output structure:
    context_vault/simulation/seeds/<seed_id>.json

Each seed carries: scenario, personas, model_pool selection, expected
report shape. Seeds are idempotent: same brand_dna + same personas →
identical seed_id.

Usage:
    python -m nodes.simulation.seed_builder
        — builds all seeds for all stage_1_products × all price points
    python -m nodes.simulation.seed_builder --product ccp_prompt_pack --price 29
        — builds one seed for one product at one price
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BRAND_DNA = REPO / "context_vault" / "brand" / "brand_dna.json"
PERSONA_DIR = HERE / "personas"
SEED_DIR = REPO / "context_vault" / "simulation" / "seeds"

DEFAULT_MODEL_POOL = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
]


def load_brand() -> dict:
    if not BRAND_DNA.exists():
        raise FileNotFoundError(f"brand_dna missing at {BRAND_DNA}")
    return json.loads(BRAND_DNA.read_text())


def load_personas() -> list[dict]:
    out = []
    for p in sorted(PERSONA_DIR.glob("*.json")):
        out.append(json.loads(p.read_text()))
    return out


def build_seed(product: dict, price_usd: float, brand: dict,
               personas: list[dict]) -> dict:
    pid = product["id"]
    seed_id = f"{pid}_${int(price_usd)}"
    cycle_count = 60
    agents_per_cycle = 1000
    seed = {
        "seed_id": seed_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brand_id": brand["brand_id"],
        "brand_version": brand["version"],
        "product": {
            "id": pid,
            "title": product["title"],
            "platform": product["platform"],
            "price_usd": price_usd,
            "price_test_index": product["price_test_points_usd"].index(price_usd),
        },
        "scenario": {
            "scenario_id": f"stage1_{pid}_at_${int(price_usd)}",
            "cycles": cycle_count,
            "agents_per_cycle": agents_per_cycle,
        },
        "personas": [
            {"persona_id": p["persona_id"], "label": p["label"],
             "system_prompt": p["system_prompt"],
             "weight": 1.0 / len(personas)} for p in personas
        ],
        "model_pool": DEFAULT_MODEL_POOL,
        "litellm_endpoint": os.getenv("LITELLM_ENDPOINT", "http://localhost:4000/v1"),
        "expected_report_keys": [
            "conversion_rate", "median_willingness_usd",
            "top_objections", "avatar_breakdown", "cycle_trend",
        ],
        "voice": {
            "tone": brand["voice"]["tone"],
            "vocabulary_preferences": brand["voice"]["vocabulary_preferences"],
            "vocabulary_avoidances": brand["voice"]["vocabulary_avoidances"],
        },
    }
    seed["seed_sha256"] = hashlib.sha256(
        json.dumps(seed, sort_keys=True).encode()
    ).hexdigest()[:16]
    return seed


def write_seed(seed: dict) -> Path:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    out = SEED_DIR / f"{seed['seed_id']}.json"
    out.write_text(json.dumps(seed, indent=2) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", help="Product id to seed (default: all)")
    ap.add_argument("--price", type=float, help="Price USD (default: all in test_points)")
    args = ap.parse_args(argv)

    brand = load_brand()
    personas = load_personas()
    if not personas:
        print(f"no personas in {PERSONA_DIR}", file=sys.stderr)
        return 1

    products = brand.get("stage_1_products", [])
    if args.product:
        products = [p for p in products if p["id"] == args.product]
        if not products:
            print(f"unknown product: {args.product}", file=sys.stderr)
            return 1

    written = []
    for prod in products:
        prices = [args.price] if args.price else prod["price_test_points_usd"]
        for px in prices:
            if px not in prod["price_test_points_usd"] and not args.price:
                continue
            seed = build_seed(prod, float(px), brand, personas)
            path = write_seed(seed)
            written.append({"seed_id": seed["seed_id"],
                            "path": str(path),
                            "sha": seed["seed_sha256"]})

    print(json.dumps({"seeds_written": len(written), "seeds": written}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
