#!/usr/bin/env python3
# EPOS Artifact — MiroFish Simulation Kernel (Stage 1)
# Constitutional Authority: Articles V, X, XIV, XVI §2
"""
MiroFish Simulation Kernel.

Exposes:
    GET  /health
    POST /simulate            (body: Scenario JSON)  → {run_id}
    GET  /runs/{run_id}       → {status, report?}

Runs scenarios asynchronously against the OpenRouter free-model pool,
writing partial progress + final report to /app/results/<run_id>.json.

Deletion: kernel never deletes. Results accumulate; rotation is a
Sovereign-driven Directive.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path
from statistics import median
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from avatars import AVATARS, BY_ID  # copied into image
    from scenario import Product, Scenario
except Exception:  # when running outside the container
    from nodes.simulation.avatars import AVATARS, BY_ID  # type: ignore
    from nodes.simulation.scenario import Product, Scenario  # type: ignore

RESULTS_DIR = Path(os.getenv("MIROFISH_RESULTS", "/app/results"))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

DEFAULT_MODEL_POOL = [
    # OpenRouter free-tier identifiers; Sovereign extends via MIROFISH_MODEL_POOL
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-7b:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.1-8b-instruct:free",
]


def model_pool() -> list[str]:
    env = os.getenv("MIROFISH_MODEL_POOL", "").strip()
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_MODEL_POOL


# ── HTTP API ──────────────────────────────────────────────────

RUNS: dict[str, dict[str, Any]] = {}


class ProductIn(BaseModel):
    title: str
    price_usd: float
    copy: str = ""
    copy_path: str = ""
    audio_overview_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScenarioIn(BaseModel):
    scenario_id: str
    product: ProductIn
    avatars: list[str]
    cycles: int = 60
    agents_per_cycle: int = 1000
    decision_prompt_template: str = ""
    model_pool: list[str] | None = None
    cycle_length_label: str = "month"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load existing runs on startup for idempotency
    for p in RESULTS_DIR.glob("*.json"):
        try:
            RUNS[p.stem] = json.loads(p.read_text())
        except Exception:
            pass
    yield


app = FastAPI(title="MiroFish", version="1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "operational" if OPENROUTER_KEY else "degraded",
        "reason": "" if OPENROUTER_KEY else "OPENROUTER_API_KEY not set",
        "model_pool": model_pool(),
        "runs_known": len(RUNS),
    }


@app.post("/simulate")
async def simulate(scn: ScenarioIn, bg: BackgroundTasks):
    run_id = f"{scn.scenario_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    record = {
        "run_id": run_id,
        "scenario_id": scn.scenario_id,
        "status": "running",
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cycles_planned": scn.cycles,
        "agents_per_cycle": scn.agents_per_cycle,
        "progress": 0.0,
    }
    RUNS[run_id] = record
    _persist(run_id)
    bg.add_task(_run_simulation, run_id, scn.model_dump())
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in RUNS:
        # Try to load from disk
        fp = RESULTS_DIR / f"{run_id}.json"
        if fp.exists():
            RUNS[run_id] = json.loads(fp.read_text())
        else:
            raise HTTPException(404, "unknown run_id")
    return RUNS[run_id]


# ── Kernel ────────────────────────────────────────────────────

async def _run_simulation(run_id: str, scn: dict[str, Any]) -> None:
    try:
        rep = await _simulate_full(scn)
        RUNS[run_id].update({"status": "complete", "report": rep,
                              "progress": 1.0,
                              "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    except Exception as e:  # noqa: BLE001
        RUNS[run_id].update({"status": "failed",
                              "error": f"{type(e).__name__}: {e}"})
    _persist(run_id)


async def _simulate_full(scn: dict[str, Any]) -> dict[str, Any]:
    pool = scn.get("model_pool") or model_pool()
    cycles = int(scn["cycles"])
    per = int(scn["agents_per_cycle"])
    avatars = [a for a in scn["avatars"] if a in BY_ID] or list(BY_ID)
    template = scn.get("decision_prompt_template") or _default_template()

    # Concurrency cap — keep the free-tier polite.
    sem = asyncio.Semaphore(int(os.getenv("MIROFISH_CONCURRENCY", "12")))
    decisions: list[dict[str, Any]] = []
    cycle_trend: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=60) as client:
        for cycle in range(cycles):
            tasks = []
            for i in range(per):
                avatar = avatars[i % len(avatars)]
                model = pool[(cycle * per + i) % len(pool)]
                tasks.append(_one_agent(client, sem, template, avatar, scn["product"], model))
            batch = await asyncio.gather(*tasks, return_exceptions=True)
            for d in batch:
                if isinstance(d, dict):
                    decisions.append(d)
            buyers = [d for d in batch if isinstance(d, dict) and d.get("buy")]
            cycle_trend.append({"cycle": cycle,
                                 "conversion_rate": len(buyers) / max(1, per)})

    return _report(decisions, cycle_trend, avatars)


def _default_template() -> str:
    return (
        "You are evaluating a product for purchase.\n\n"
        "{avatar_block}\n\n"
        "PRODUCT:\n"
        "Title: {product_title}\n"
        "Price: ${price_usd}\n"
        "Copy: {product_copy}\n\n"
        "Respond ONLY with a JSON object: "
        "{{\"buy\": bool, \"price_willingness_usd\": number, "
        "\"top_objection\": string, \"confidence\": 1-10}}"
    )


async def _one_agent(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                     template: str, avatar_id: str, product: dict,
                     model: str) -> dict[str, Any]:
    avatar = BY_ID[avatar_id]
    prompt = template.format(
        avatar_block=avatar.to_prompt_chunk(),
        product_title=product["title"],
        price_usd=product["price_usd"],
        product_copy=product.get("copy", "")[:1200],
    )

    async with sem:
        try:
            r = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://epos.local",
                    "X-Title": "MiroFish",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 160,
                    "temperature": 0.6,
                },
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            return {"avatar": avatar_id, "model": model,
                    "buy": False, "price_willingness_usd": 0.0,
                    "top_objection": "simulator_error",
                    "confidence": 1, "error": str(e)[:120]}

    return {"avatar": avatar_id, "model": model, **_parse_decision(text)}


_JSON_RX = re.compile(r"\{[\s\S]*?\}")


def _parse_decision(text: str) -> dict[str, Any]:
    m = _JSON_RX.search(text)
    if not m:
        return {"buy": False, "price_willingness_usd": 0.0,
                "top_objection": "unparseable", "confidence": 1}
    try:
        d = json.loads(m.group(0))
    except Exception:
        return {"buy": False, "price_willingness_usd": 0.0,
                "top_objection": "unparseable", "confidence": 1}
    return {
        "buy": bool(d.get("buy", False)),
        "price_willingness_usd": float(d.get("price_willingness_usd", 0) or 0),
        "top_objection": str(d.get("top_objection", "") or "")[:120],
        "confidence": int(d.get("confidence", 1)),
    }


def _report(decisions: list[dict], cycle_trend: list[dict],
            avatars: list[str]) -> dict[str, Any]:
    if not decisions:
        return {"conversion_rate": 0, "decisions": 0, "error": "no decisions"}
    total = len(decisions)
    buyers = [d for d in decisions if d.get("buy")]
    willingness = [d["price_willingness_usd"] for d in decisions
                   if isinstance(d.get("price_willingness_usd"), (int, float))]
    objections = Counter(d.get("top_objection", "") for d in decisions
                         if d.get("top_objection"))
    per_avatar = {}
    for a in avatars:
        subset = [d for d in decisions if d.get("avatar") == a]
        if not subset:
            continue
        per_avatar[a] = {
            "n": len(subset),
            "conversion_rate": sum(1 for d in subset if d.get("buy")) / len(subset),
            "median_willingness_usd": median(
                [d["price_willingness_usd"] for d in subset
                 if isinstance(d.get("price_willingness_usd"), (int, float))] or [0]
            ),
        }
    return {
        "decisions": total,
        "conversion_rate": len(buyers) / total,
        "median_willingness_usd": median(willingness) if willingness else 0.0,
        "top_objections": [{"objection": o, "count": c}
                           for o, c in objections.most_common(5)],
        "avatar_breakdown": per_avatar,
        "cycle_trend": cycle_trend,
    }


def _persist(run_id: str) -> None:
    try:
        (RESULTS_DIR / f"{run_id}.json").write_text(json.dumps(RUNS[run_id], indent=2))
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MIROFISH_PORT", "8110")))
