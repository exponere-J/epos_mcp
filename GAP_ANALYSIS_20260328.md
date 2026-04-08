# EPOS Ecosystem Gap Analysis — 2026-03-28

**Method**: Source code audit across all three repos
**Scope**: friday/, epos_mcp/, agent-zero/
**Baseline**: Sprint 2 complete (9/9), Sprint 3 closed (7/8), Doctor 21/2/0

---

## EXECUTIVE SUMMARY

The foundation is solid — 9 core modules built, doctor at 21 PASS, compliance at 88%, LLM client operational with 3 backends, AZ bridge reports ok=True. But the **integration layer is almost entirely unbuilt**. The individual organs exist. The bridges between them do not.

**Friday is mute.** She has a chat UI but it returns a hardcoded template string — no LLM call. The model router exists but is never wired to the chat input. This is the single biggest gap.

---

## BRIDGES NEEDED — PRIORITY RANKED

### P0 — Blocks All Progress

| # | Bridge | From → To | What Exists | What's Missing |
|---|--------|-----------|-------------|----------------|
| 1 | **Friday LLM Bridge** | app.py chat → model_router → litellm_client | model_router.py has provider configs; litellm_client.py has 3 working backends | app.py never calls model_router. Chat response is a hardcoded string template. Wire: user input → model_router → litellm_client → response displayed |
| 2 | **TTLG Entrypoint Scripts** | friday/scripts/ → TTLG 6-phase cycle | ttlg_agents.py exists in epos_mcp; TTLG charter docs exist | All 4 entrypoint scripts missing: `ttlg_systems_light_scout.sh`, `ttlg_market_light_scout.sh`, `friday_vault_summary.sh`, `friday_check_ttlg_health.sh`. No scripts/ directory in friday/ |
| 3 | **Friday ↔ Agent Zero HTTP Bridge** | bridge_az.py → AZ Flask API | bridge_az.py does filesystem checks; AZ has full Flask API with /message, /poll, /health | No HTTP calls. bridge_az.py only checks if files exist on disk. Cannot dispatch missions or retrieve outcomes |

### P1 — Blocks Sovereign Bridge

| # | Bridge | From → To | What Exists | What's Missing |
|---|--------|-----------|-------------|----------------|
| 4 | **Unified Governance Protocol** | friday/governance.py ↔ epos_mcp/governance_gate.py | Two complete but separate governance systems | No shared protocol, schema, or API. Friday logs receipts one way; EPOS gates files another way. They don't communicate |
| 5 | **Mission Contract Decorator** | agent_orchestrator.py → any execution target | MissionBrief/MissionReceipt dataclasses exist | No `@mission` decorator for wrapping, validating, and proving mission execution. No standard (status, proof) return contract |
| 6 | **Friday .env + Config** | friday/ runtime → API keys | epos_mcp/.env has all keys; friday_cli.py reads from it | friday/app.py has no .env loading. model_router.py can't resolve API keys. No friday/.env or .env.template |
| 7 | **EPOS Runner ↔ Friday UI** | app.py → epos_runner.py :8001 | friday_cli.py chat command posts to /run-task; epos_runner.py has FastAPI app | app.py (Streamlit) never calls the EPOS API. Only friday_cli.py does |
| 8 | **AAR Schema** | TTLG Phase 6 → structured capture | AAR_TEMPLATE.md exists; flywheel_analyst generates reports | No `schemas/aar_v1.json` in friday/. No structured AAR generation pipeline |

### P2 — Blocks Production Readiness

| # | Bridge | What's Missing |
|---|--------|----------------|
| 9 | **Event Bus Cross-Process** | event_bus.py is in-process file-based only. No network transport. Friday can't subscribe to EPOS events in real time |
| 10 | **Dashboard/Chronos/Void Tabs** | Referenced in friday docs but never built. Dashboard is the ops view; Chronos is timeline; Void is idea capture |
| 11 | **Kanban Write Operations** | Kanban tab reads missions but can't create/move/delete. Read-only stub |
| 12 | **Cryptographic Receipt Signing** | Governance receipts are plain JSON. No hash, no tamper detection, no Merkle tree |
| 13 | **Rollback Snapshots Before Mutation** | governance_gate.py declares rollback support; engine/rollback.py exists but isn't wired to the gate |
| 14 | **Hardcoded Paths in friday_cli.py** | Lines 24, 107 have hardcoded Windows paths instead of using paths.py |
| 15 | **Chat History Windowing** | Messages accumulate without bound in session_state. No sliding window |

### P3 — Blocks Scale/Cloud

| # | Bridge | What's Missing |
|---|--------|----------------|
| 16 | **TTLG Automated Schedule** | Daily cycle (06:00/14:00/20:00) has no cron or scheduler integration |
| 17 | **AZ EPOS Agent Profile** | Agent Zero has no EPOS-specific tools, receipt generation, or governance awareness |
| 18 | **Learning Loop Implementation** | FRIDAY_LEARNING_FRAMEWORK.md is document only. No decision journal, no pattern detection from past sessions |
| 19 | **Content Lab Pipeline** | content/lab/ has module stubs (cascade, tributary, echolocation) but no end-to-end execution |
| 20 | **PostgREST ↔ EPOS Wiring** | PostgREST runs at :3000 serving epos schema. epos_db.py CLI uses it. But no EPOS module queries it directly — all use docker exec psql |

---

## COMPONENT STATUS MATRIX

| Component | Status | Notes |
|-----------|--------|-------|
| **EPOS Core (9 modules)** | ✅ WORKING | All import clean, doctor validated |
| **LLM Client** | ✅ WORKING | 3 backends live (Ollama, Groq fast, Groq reasoning) |
| **AZ Bridge** | ✅ WORKING | ok=True, health check passes |
| **Life OS CLI** | ✅ WORKING | projects, project, gate, update, log commands |
| **Friday CLI** | ✅ WORKING | status, mission, chat commands |
| **Docker Stack** | ✅ WORKING | epos_db, epos_api, epos_ui, epos_swagger all healthy |
| **Niche Intelligence** | ✅ WORKING | Schema, scanner, pack, 20 briefs created |
| **epos_runner.py** | ⚠️ PARTIAL | FastAPI app exists but not verified serving |
| **Friday app.py** | ⚠️ PARTIAL | UI renders but chat is mute (no LLM call) |
| **model_router.py** | ⚠️ PARTIAL | Provider configs exist but never called |
| **bridge_az.py** | ⚠️ PARTIAL | Filesystem checks only, no HTTP |
| **governance.py** | ⚠️ PARTIAL | Logs after the fact, not a blocking gate |
| **Kanban tab** | ⚠️ STUB | Read-only display |
| **TTLG Pipeline** | ❌ MISSING | Zero of 6 phases implemented |
| **Sovereign Bridge** | ❌ MISSING | Integration protocol not built |
| **Friday .env** | ❌ MISSING | No environment config for Friday |
| **Content Lab execution** | ❌ MISSING | Stubs only |

---

## RECOMMENDED BUILD ORDER

**Phase 1 — Make Friday Talk (1 session)**
1. Create friday/.env loading from epos_mcp/.env
2. Wire app.py chat → model_router → litellm_client
3. Friday can think and respond via Ollama/Groq

**Phase 2 — Connect the Pipes (2-3 sessions)**
4. Wire app.py to call epos_runner.py /run-task endpoint
5. Build HTTP bridge in bridge_az.py (dispatch + outcome retrieval)
6. Unify governance protocol (shared receipt schema)
7. Build @mission decorator for contract enforcement

**Phase 3 — TTLG Cycle (2 sessions)**
8. Create friday/scripts/ with 4 entrypoint scripts
9. Create schemas/aar_v1.json
10. Wire TTLG phases 1-6 using existing modules as backends

**Phase 4 — Production Polish (2-3 sessions)**
11. Dashboard tab (ops view from life_os_cli data)
12. Kanban write operations
13. Event bus cross-process (WebSocket or SSE)
14. Chat history windowing
15. Content Lab pipeline execution

---

## THE ONE-LINE SUMMARY

**The organs are built. The nervous system works. The bridges between them do not exist yet. Build Phase 1 first — making Friday talk — and the rest cascades from there.**
