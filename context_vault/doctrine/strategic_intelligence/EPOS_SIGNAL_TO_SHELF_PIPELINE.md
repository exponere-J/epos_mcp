# EPOS SIGNAL-TO-SHELF PIPELINE — Implementation Plan

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI
**Ratified:** 2026-04-23 by Sovereign
**Triad companion to:** `EPOS_UNIFIED_REGISTRY_DOCTRINE_20260423.md` (strategic overview) + `EPOS_OPERATIONAL_COMPONENTS_EXPLODED.md` (mechanical detail)

---

## Purpose

This document is the **implementation plan** — how to build the
pipeline, in what order, with what dependencies, and when each piece
passes which gate. The strategic overview tells you *why*; the
Operational Components doc tells you *how each piece works internally*;
this doc tells you **how to build them in the right order**.

## Principle — build from the middle outward

The MiroFish Fortification gate is the heart of the pipeline.
Everything upstream (Sensing, Staging, Synthesis) feeds it; everything
downstream (Implantation, Stewardship) consumes its output. Build
MiroFish first, then the nearest dependencies, then the edges.

## Build order (stages × prerequisites)

### Stage A — Fortification Heart

1. **MiroFish local kernel** — already exists at `containers/mirofish/simulator.py` (from BUILD 4).
2. **MiroFish upstream bridge** — port `submit_upstream` in `run_pricing_sim.py` to the Flask-app API on the cloned `external/mirofish/backend/`. (CC-BF-004)
3. **MiroFish 4-Cycle orchestrator** — new file `containers/mirofish/cycles.py` that runs Cycle 1 → Cycle 2 (Dependency-Ledger attack) → Cycle 3 (Bridge-Tool generation) → Cycle 4 (Improvement Flush back to Internal Vault).
4. **Dependency Ledger** — doctrine at `context_vault/doctrine/DEPENDENCY_LEDGER_GT001-GT010.md`; codifies the 10 Hard Truth footguns MiroFish attacks with.

Stage A unblocks the Prover row of the Unified Registry.

### Stage B — Upstream Feed

5. **Signal buffer** (CC-OP-003) — `epos/traffic/signal_buffer.py` with SQLite + nomic-embed dedup + pain-magnitude priority scoring.
6. **FOTW sensors** (matures the 5 stubs from BATCH 5) — wire Discord/LinkedIn/Skool/Newsletter monitors to real session states or API.
7. **Signal registry writer** — attaches to `fotw.signal.captured` event; writes rollup to `context_vault/fotw/signal_registry.json`.
8. **Gap Bridge renderer** — `nodes/bridge/gap_bridge_renderer.py`; re-generates `GAP_BRIDGE_MATRIX.md` from `signal_registry.json` + `organism_state.process_matrix.capability_index` on every signal refresh.
9. **Parts Bin inventory builder** — daily cron; reads `capability_index` + existing products; emits `context_vault/intelligence/PARTS_BIN_INVENTORY.md` listing every component and which product it's currently deployed in.

Stage B unblocks the Listener + Gatekeeper + Synthesizer rows.

### Stage C — Downstream Delivery

10. **Gumroad / Lemon Squeezy client** (CC-OP-001) — `epos/commerce/gumroad_client.py`; v2 API primary + Playwright fallback with `execCommand("insertText")` ProseMirror bypass.
11. **Session keeper** (CC-OP-002) — `epos/commerce/session_keeper.py`; Playwright `storage_state` persistence per platform.
12. **Echolocation agent** (CC-OP-005) — `epos/commerce/echolocation_agent.py`; accessibility-tree scrape at T+24h.
13. **Product catalog writer** — attaches to `product.shelf.implanted` event; writes `context_vault/products/catalog.json` with version + platform + metrics.

Stage C unblocks the Deployer row.

### Stage D — Orchestration

14. **Pipeline orchestrator** (CC-OP-004) — `epos/pipeline/signal_to_shelf.py`; async phase transitions across all 6 phases; the master conductor.
15. **Pipeline Stage Matrix writer** — renders `context_vault/intelligence/PIPELINE_STAGE_MATRIX.md` from orchestrator state; shows how many signals are at each phase.
16. **Sovereign approval gates** — two pause-points in the orchestrator: Pricing Review (after Cycle 1) and Copy Approval (before Implantation). Each emits `sovereign.approval.requested` with payload.

Stage D unblocks autonomous end-to-end runs with two human gates.

### Stage E — Stewardship

17. **Supervisory Monitor integration** — connect existing `epos/ops/supervisory_monitor.py` (BUILD 100) to `product.shelf.implanted` events; each new product acquires a client-like state machine (30-day review, renewal signals, etc.).
18. **Client registry** — `context_vault/ops/client_registry.json` rollup; daily-refreshed from per-client files.

Stage E unblocks the Steward row.

## Backfill directives (CC-BF set)

Seven backfills clear the underlying plumbing. Each is a ~1-3 hour build.

- **CC-BF-001** — Event-bus contract hardening (typed envelopes, versioned topics)
- **CC-BF-002** — Deletion-gate extensions (per-target approval with TTL)
- **CC-BF-003** — Anti-truncation re-check after simulation mutations
- **CC-BF-004** — MiroFish upstream bridge (see Stage A.2)
- **CC-BF-005** — Registry-reconciler for parallel subagent writes
- **CC-BF-006** — Organism-state publisher cron (move from on-demand to scheduled)
- **CC-BF-007** — SCC TAOR real-LLM wiring (LiteLLM @ localhost:4000 → Qwen3-Coder-30B)

## Recommended parallelization

With proper subagent delegation:

- **Track 1 (serial):** Stage A (MiroFish 4-Cycle) → Stage D (Orchestrator) → Stage E (Stewardship wiring)
- **Track 2 (parallel to Track 1):** Stage B (upstream feed)
- **Track 3 (parallel to Track 1):** Stage C (downstream delivery)
- **CC-BF backfills** run in parallel with main tracks where non-conflicting

Estimated agentic time with parallelization: ~24-30 hours. Serial: ~60.

## Verification gates

Each CC-OP build passes:

1. **Doctor** — AST + lint + shebang + watermark
2. **TTLG Post-Completion Diagnostic** — Scout → Thinker → Gate (REGISTER/REVISE/REJECT) → Surgeon → Analyst
3. **Anti-truncation six-field check** on every file
4. **Organism-state registration** with capability_tags + governing_articles + process_role
5. **Integration smoke-test** — the build runs against the prior stage's output

No CC-OP build is "done" until it has a row in `organism_state.json`
with `gate_verdict: REGISTER` and `validator: TTLG live (Doctor)`.

## Immediate next directive

`FORGE_DIRECTIVE_SIGNAL_TO_SHELF_STAGE_A_20260423` — build the
MiroFish 4-Cycle orchestrator + Dependency Ledger + upstream bridge.
Unlocks the Prover gate. Everything downstream depends on this.

---

**See also:**
- `EPOS_UNIFIED_REGISTRY_DOCTRINE_20260423.md` — strategic overview
- `EPOS_OPERATIONAL_COMPONENTS_EXPLODED.md` — mechanical detail
- `missions/FORGE_DIRECTIVE_MIROFISH_STAGE1_20260422.md` — existing Stage-1 directive
- `GAP_BRIDGE_MATRIX.md` — capability × market source
