# FORGE DIRECTIVE — MIROFISH SIMULATION ENGINE STAGE 1 (2026-04-22)

**Issued by:** The Architect
**Assigned to:** The Forge (Desktop Code) → Agent Zero
**Constitutional Authority:** Articles V, VII, X, XIV, XVI §1–§2
**Directive ID:** `FORGE_DIR_MIROFISH_STAGE1_20260422`
**Council growth-path activation:** The Simulator (MiroFish) — Tier 3, Week 2

---

## Sovereign mandate (verbatim, EPAS Mission 4)

> "Deploy the MiroFish Swarm Intelligence Engine to simulate market
> resonance before real-world deployment. Deploy MiroFish as a sidecar
> Docker container on the epos-net network. Configure the OpenRouter
> Free Model Roster (17+ models) for high-throughput, zero-cost
> simulation. Seed the environment with the 8 Content Lab avatars to
> simulate prospect behavior."

Impact: 5-year market stress test in a single afternoon. 1,000 virtual
buyers × 60 cycles = compression of real-market exposure into compute time.

---

## Sovereignty Clause

Jamie is the Sovereign. MiroFish operates under Sovereign ratification
of the EPAS Mission 4 scope. It does not ship real offers, does not
send real messages, does not spend real marketing budget. **It only
simulates.** Real-world deployment remains gated on Sovereign approval
after Reward Bus scoring at T+24h, T+48h, T+90d.

## Scope

Stage 1 = the minimum viable simulation engine:
- Sidecar Docker container on `epos-net`.
- HTTP surface for scenario submission + result retrieval.
- OpenRouter free-model rotation (batch callable, zero-cost target).
- 8 Content Lab avatars seeded.
- Scenario spec (product, pricing, content, ask) → simulation run →
  structured report (conversion rate, median willingness, objection
  taxonomy, avatar breakdown, cycle trend).
- Registration in organism state per Article XVI §1.

## Artifacts (delivered this session; Forge picks up from disk)

| File | Purpose |
|---|---|
| `nodes/simulation/__init__.py` | Package entrypoint |
| `nodes/simulation/avatars.py` | 8 Content Lab avatar definitions |
| `nodes/simulation/scenario.py` | Scenario schema + validator |
| `nodes/simulation/mirofish_client.py` | Python client for the MiroFish container |
| `containers/mirofish/Dockerfile` | Container image spec |
| `containers/mirofish/simulator.py` | Simulation kernel (OpenRouter, async loop) |
| `containers/mirofish/requirements.txt` | Python deps |
| `docker-compose.yml` addendum | Service entry for `mirofish` on `epos-net` |

## OpenRouter free-model roster (rotation pool)

Baseline 10 models shipped in `simulator.py`. Sovereign can extend via
`MIROFISH_MODEL_POOL` env var (comma-separated OpenRouter IDs).

The rotation strategy: round-robin per agent, so a scenario tested with
1,000 agents × 10 models = 100 agents per model. Reduces single-model
bias; exposes prompt robustness.

## 8 Content Lab avatars

Seeded in `nodes/simulation/avatars.py`:
1. **founder_solo** — $0–$2M ARR, wears every hat, time-poor
2. **vp_marketing** — mid-market, team of 3–10, budget-constrained
3. **consultant_indie** — 1–3 clients, reputation-sensitive
4. **agency_ops_lead** — client-facing, retention-focused
5. **growth_hacker** — experiment-hungry, short attention
6. **enterprise_innovation** — big-co innovation team, long cycle
7. **creator_studio** — content-first, brand-careful
8. **small_service_owner** — local or niche service, price-sensitive (LuLu archetype)

Each carries: name, psychographic, objections, price sensitivity,
time-to-decision, decision authority, content preferences.

## Scenario schema

```json
{
  "scenario_id": "stage1_gumroad_ccp_pack",
  "product": {
    "title": "...", "price_usd": 29, "copy_path": "...",
    "audio_overview_path": "..."
  },
  "avatars": ["founder_solo", "..."],
  "cycles": 60,
  "agents_per_cycle": 1000,
  "decision_prompt_template": "...",
  "model_pool": null
}
```

## Deletion governance

MiroFish never deletes production artifacts. Its simulation runs are
stored under `context_vault/simulation/<scenario_id>/<run_ts>.json`.
Cleanup of stale runs passes through `deletion_gate.enforce` like any
other arm.

## Verification

1. `docker compose build mirofish` — image builds clean.
2. `docker compose up -d mirofish` — container healthy.
3. `curl -X POST localhost:${MIROFISH_PORT:-8110}/simulate
       -H "Content-Type: application/json"
       -d @scenarios/stage1_gumroad_ccp_pack.json`
   → returns a `run_id`; full report materializes under
   `context_vault/simulation/<scenario_id>/<run_id>.json` within
   ≤ 15 minutes for 1,000 agents × 60 cycles on the free-model pool.
4. Report contains: conversion_rate, median_willingness, top_objections
   (≥ 3), avatar_breakdown (8 entries), cycle_trend (60 points).
5. Register MiroFish in organism state with capability tags
   `[simulation, swarm_intelligence, market_validation, pricing,
     openrouter_rotation]`.
6. AAR to `context_vault/aar/MIROFISH_STAGE1_AAR.md`.

## Research-to-Merge Protocol unblock

Stage 1 of MiroFish satisfies Step 3 of the Research-to-Merge Protocol
(Simulation). Every MERGE decision above the Sovereign-set revenue
threshold now runs through MiroFish before Forge integrates.

## Rollback

`docker compose stop mirofish && docker compose rm -f mirofish`. The
container is sidecar; no upstream services depend on it. Simulation
runs under `context_vault/simulation/` are preserved.

## Out of scope (Stage 2+)

- Agent-Zero-in-the-loop simulation (agents using the actual execution arm)
- Reward Bus feedback to MiroFish scoring weights
- Multi-scenario batch orchestration
- Real-money validation layer (paid A/B)
- Visual asset generation for simulated ads

## Next

Once Stage 1 is live, emit `FORGE_DIRECTIVE_MIROFISH_STAGE2_*.md` per
the remaining growth roadmap.
