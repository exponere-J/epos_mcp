# EPOS Evolution Index
## The Organism's Institutional Memory

**Generated:** 2026-04-13
**Directive:** 20260413-04
**Source:** `context_vault/state/evolution_archive.json`

---

### How to Use This File

| Question | How to Find the Answer |
|----------|----------------------|
| When was a capability built? | Search the Phase/Event column below |
| Why was an architectural decision made? | See `evolution_archive.json → architectural_decisions_ledger` |
| Which directive built a component? | Find the event, note the Directive column |
| What does the AAR say about it? | Open the AAR file in `context_vault/aar/` |
| What should be built next? | See Successor Directives in the latest AAR |
| Is a component regression new or old? | Find the directive that built it, check its AAR for known issues |

**Full catalog of all AARs:** `context_vault/aar/AAR_CATALOG.json`
**Machine-readable archive:** `context_vault/state/evolution_archive.json`

---

### Quick Reference — Phase Timeline

| Phase | Date | Key Event | Directive | AAR |
|-------|------|-----------|-----------|-----|
| Genesis | 2026-03-27 | Agent roles + intelligence layer + constitutional scaffold | RETRO-20260327-GENESIS-SPRINT | AAR_MODULE3-8_20260327 |
| Foundation | 2026-04-04 | CCP sovereignty 105/105 + Custom Props Framework | RETRO-20260404-01 | — |
| Foundation | 2026-04-06 | TTLG 4-node rewrite, 12 nodes sovereign, Doctor live | RETRO-20260406-01 | EPOS_AAR_20260406 |
| Execution Layer | 2026-04-07 | BrowserUse + Daemon + Reactor + Agent Zero + 42 handlers | RETRO-20260407-01 | EPOS_AAR_20260407_GAP_CLOSURE |
| Execution Layer | 2026-04-07 | LLM path wiring — LiteLLM proxy routing established | RETRO-20260407-02 | AAR_CC_WIRE_LLM_PATH_20260407 |
| Containerization | 2026-04-08 | 14-service Docker compose, 4 running, vault 577 files | EPOS_DOCKERIZATION_DIRECTIVE | AAR_DOCKERIZATION_20260408 |
| Intelligence | 2026-04-08 | Friday Chief of Staff, 18/18 arms, nightly upskill | FRIDAY_CHIEF_OF_STAFF | AAR_CC_DEPLOY_UPSKILL_20260408 |
| Intelligence | 2026-04-10 | Groq 12k TPM limit confirmed → SCC sprint triggered | RETRO-20260410-01 | AAR_INTELLIGENCE_LAYER_PROXY |
| Self-Building | 2026-04-11 | SCC seated, Desktop CODE retired, Qwen3-Coder live | SCC_SEATING_DIRECTIVE | AAR-20260411-FINAL-RETIREMENT |
| Sanitation | 2026-04-13 | 8/8 verification, 7 Windows paths fixed, SCC shadow 1.0 | 20260413-01 | AAR_20260413-01 |
| Institutional Memory | 2026-04-13 | This file + evolution_archive.json + state redundancy | 20260413-04 | AAR_20260413-04 |

---

### Capability Growth Chart

| Metric | Apr 6 | Apr 7 | Apr 8 | Apr 11 | Apr 13 | Current |
|--------|-------|-------|-------|--------|--------|---------|
| Nodes sovereign | 12 | 22 | 22 | 22 | 22 | 22 |
| Event handlers | — | 42 | 42 | 42 | 42 | 42 |
| Docker services (running) | — | — | 4 | 4 | 4 | 4 |
| Models seated | 2 | 2 | 2 | 3 | 3 | 3 |
| Model slots selected | — | — | — | 22 | 22 | 22 |
| Execution arms | — | — | 18 | 18 | 18 | 18 |
| Doctor checks passing | 31 | — | 38 | 38 | 38 | 38 |
| Event bus total events | 10 | 42 | 994 | — | — | 1,050+ |
| AARs cataloged | — | — | — | — | 24 | 24 |
| SCC shadow match rate | — | — | — | — | 1.0 | 1.0 |
| Verification score | — | — | — | — | 8/8 | 8/8 |

---

### Key Architectural Decisions

| ID | Date | Decision | Why |
|----|------|----------|-----|
| AD-001 | 2026-03-27 | LangGraph as canonical state machine | Composable, observable, conditional routing |
| AD-002 | 2026-03-27 | File-based JSONL event bus | No ports, survives restarts, human-readable |
| AD-003 | 2026-04-07 | Nothing done until it runs | Prevent incomplete work from entering organism |
| AD-004 | 2026-04-07 | AAR is constitutional mandate | Institutional memory + QLoRA training data |
| AD-005 | 2026-04-08 | Context vault as single source of truth | All agents read/write same vault |
| AD-006 | 2026-04-08 | LiteLLM as unified routing proxy | Model-agnostic, swap providers without code changes |
| AD-007 | 2026-04-11 | SCC replaces Desktop CODE | Self-sufficiency + constitutional governance + cost |
| AD-008 | 2026-04-11 | Lazy imports for all EPOS nodes | Boot even if dependencies absent |
| AD-009 | 2026-04-13 | Internal secrets auto-generated, external human-gated | EPOS can rotate its own; cannot invent external keys |
| AD-010 | 2026-04-13 | Directive ID in every file header | Trace any file to the session that created it |

---

### Market Evaluation Triggers

These events should prompt an archive update and may trigger a new directive:

- **Echolocation shift >10%** on a topic → update content_lab capabilities
- **FOTW recurring objection** → evaluate new node for next directive
- **Competitor overlap** → evaluate defensive positioning
- **Model benchmark exceeded** → queue model swap in registry
- **Constitutional friction** → submit amendment via governance gate
- **Client capability gap** → log in pm_surface.jsonl as dependency
- **SCC match rate <0.9** → pause retirement, investigate divergence
- **Event bus >10k events** → evaluate rotation/archival policy

---

### Successor Directives (as of 2026-04-13)

| ID | Title | Depends On | Status |
|----|-------|-----------|--------|
| 20260413-02 | Step A: Repository Sovereignty | 20260413-01 (clean codebase) | QUEUED |
| 20260413-03A | Voice System Initialization | — | IN PROGRESS |
| 20260413-03 | Step B: Infrastructure Adapter | 20260413-02 | QUEUED |
| 20260414-01 | Cloud Migration Execution | 20260413-03 | QUEUED |
| 20260414-02 | Voice Vertical Initialization | 20260414-01 | QUEUED |

---

*Raw capture first. Parse second. Route situationally.*
*1% daily. 37x annually.*
