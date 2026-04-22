# AAR: Agent Zero Alignment Scan — 2026-03-27

**Mission**: Scan and align agent-zero workspace to unblock EPOS ↔ AZ integration
**Status**: COMPLETE — all integration blocks resolved
**Doctor**: 19 pass / 4 warn / 0 fail (improved from 18/5/0)

---

## 1. FINDINGS

| # | File | Location | Severity | Issue |
|---|------|----------|----------|-------|
| AZ-01 | `config.json` | agent-zero/ | CRITICAL | Extra closing `}` — invalid JSON, breaks all config reads |
| AZ-02 | `epos_config.json` | agent-zero/ | HIGH | WSL path `/c/Users/Jamie/...` — broken on native Windows |
| AZ-03 | `run.py` | agent-zero/ | WARNING | `TimeoutError` class shadows Python builtin |
| AZ-04 | `epos_doctor.py` | epos_mcp/engine/ | CRITICAL | Checks for `python/agent.py` but AZ v0.8+ moved `agent.py` to repo root |
| AZ-05 | `agent_zero_bridge.py` | epos_mcp/engine/ | CRITICAL | Only adds `python/` to sys.path — `from agent import Agent` fails because `agent.py` is at AZ root |

## 2. ROOT CAUSE

Agent Zero restructured between v0.7 and v0.8. The main `agent.py` moved from `python/agent.py` to the repository root. The `python/` directory now only contains helpers, tools, API routes, and extensions. All EPOS integration code (doctor, bridge) still referenced the old location.

## 3. ACTIONS TAKEN

| # | File | Repair |
|---|------|--------|
| 1 | `agent-zero/config.json` | Removed extra `}` on line 8 — now valid JSON |
| 2 | `agent-zero/epos_config.json` | Fixed path `/c/Users/Jamie/...` → `C:/Users/Jamie/...` |
| 3 | `agent-zero/run.py` | Renamed `TimeoutError` → `AgentTimeoutError` (3 occurrences) |
| 4 | `epos_mcp/engine/epos_doctor.py` | Updated AZ check: looks for `agent.py` at repo root first, falls back to `python/agent.py` for legacy compat |
| 5 | `epos_mcp/engine/agent_zero_bridge.py` | Adds both AZ root AND `python/` to sys.path; also imports `AgentContext` alongside `Agent` |

## 4. VERIFICATION

| Check | Result |
|-------|--------|
| `config.json` JSON parse | VALID |
| `epos_config.json` JSON parse | VALID |
| `run.py` py_compile | PASS |
| `node_lifecycle_manager.py` py_compile | PASS |
| `epos_doctor.py` py_compile | PASS |
| `agent_zero_bridge.py` py_compile | PASS |
| **EPOS Doctor** | **Exit 0 — 19 pass, 4 warn, 0 fail** |
| Agent Zero Path check | **PASS** (was WARN) |

## 5. DOCTOR IMPROVEMENT

| Metric | Before | After |
|--------|--------|-------|
| Passed | 18 | **19** |
| Warnings | 5 | **4** |
| Failed | 0 | 0 |

The Agent Zero Path warning is now a PASS. Remaining 4 warnings are pre-existing (file registry, watermarks, duplicates, launcher).

## 6. INTEGRATION ARCHITECTURE (Current State)

```
EPOS CLI / Friday
    │
    ▼
engine/agent_zero_bridge.py    ← imports Agent + AgentContext from AZ root
    │
    ▼
agent-zero/agent.py            ← AgentContext, Agent classes
agent-zero/initialize.py       ← config setup
agent-zero/models.py           ← LLM wiring (litellm)
    │
    ▼
agent-zero/python/             ← helpers, tools, API routes
    ├── helpers/               ← dotenv, logging, history, tokens
    ├── tools/                 ← code_execution, browser, subordinate
    └── api/                   ← REST endpoints for web UI
    │
    ▼
agent-zero/run.py              ← headless CLI runner (EPOS subprocess entry)
```

## 7. REMAINING ITEMS

1. **AZ .env missing**: agent-zero has no `.env` file. LLM keys must be configured before first run. The bridge will degrade gracefully (FM-B1) but AZ won't execute missions without API keys.
2. **AZ dependencies not installed**: `requirements.txt` lists litellm, langchain, sentence-transformers, browser-use, etc. These are heavy (~2GB). Install when ready to test live execution.
3. **`engine/stasis.py` (old)**: Still exists as diverged duplicate. Cleanup deferred to Sprint 2 module pass.
4. **`node_lifecycle_manager.py`**: Lives in agent-zero but header says `epos_mcp` — cosmetic, not functional.

## 8. WHAT THIS UNBLOCKS

- `engine/agent_zero_bridge.py` can now import `Agent` and `AgentContext` from AZ
- EPOS Doctor validates AZ presence correctly
- `run.py` can be invoked as subprocess for headless mission execution
- The bridge → AZ → mission pipeline is structurally connected

**Next**: Install AZ dependencies when ready for live mission test, configure AZ `.env` with LLM keys, then test end-to-end with a simple mission brief.
