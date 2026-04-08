# TTLG Launch Checklist — Pre-Build Verification
<!-- File: C:\Users\Jamie\workspace\epos\TTLG_LAUNCH_CHECKLIST.md -->

**Document authority:** EPOS Constitution v3.1 · TTLG Model & Routing Charter v1.0  
**Steward:** Jamie  
**Purpose:** Single source of truth before the first Claude Code build session opens

---

## How to Use This Checklist

Work through every section in order. Each checkbox must be confirmed — not assumed. "Confirmed" means you ran the command or opened the file, not that you remember it being there.

When every box is checked, the environment is ready. Claude Code may open. The build begins.

If any box cannot be checked, stop. Fix the blocker. Do not open Claude Code until the blocker is resolved. This discipline is the entire point of the pre-mortem framework — the failure is caught before the build starts, not during it.

---

## Section A — Environment & Runtime

### A1. Python Version
- [ ] Run: `python --version`
- [ ] Confirm output reads exactly: `Python 3.11.x` (x = any patch version)
- [ ] If output shows 3.12 or 3.13: install Python 3.11.x and set it on PATH before proceeding

### A2. Shell Environment  
- [ ] Primary shell is Git Bash
- [ ] Run in Git Bash: `echo $EPOS_ROOT`
- [ ] Confirm output is: `C:\Users\Jamie\workspace\epos` (or your actual EPOS root, Windows format)
- [ ] If `EPOS_ROOT` is empty: add `export EPOS_ROOT="C:\Users\Jamie\workspace\epos"` to `~/.bashrc` and restart shell

### A3. Virtual Environment
- [ ] `.venv` exists at `EPOS_ROOT/.venv`
- [ ] Run: `source $EPOS_ROOT/.venv/Scripts/activate` (Git Bash)
- [ ] Confirm prompt changes to show `(.venv)`
- [ ] Run: `pip list | grep fastapi` — confirms venv is active and packages installed

### A4. .env File
- [ ] `.env` exists at `EPOS_ROOT/.env`
- [ ] Open the file and confirm all of the following keys are present and populated (not empty):

| .env Key | Purpose | Confirmed |
|----------|---------|-----------|
| `EPOS_ROOT` | System root path | ☐ |
| `CONTEXT_VAULT_PATH` | Vault directory | ☐ |
| `OPENROUTER_API_KEY` | All TTLG phase agents | ☐ |
| `OPENROUTER_BASE_URL` | OpenRouter endpoint | ☐ |
| `GEMINI_API_KEY` | Friday (Gemini 1.5 Flash) | ☐ |
| `FRIDAY_MODEL` | `gemini-1.5-flash` | ☐ |
| `ANTHROPIC_API_KEY` | Claude Code shell | ☐ |
| `CLAUDE_CODE_MODEL` | `claude-sonnet-4-6` | ☐ |
| `CLAUDE_SURGEON_BACKEND` | `deepseek/deepseek-coder-v2-lite:free` | ☐ |
| `TTLG_SCOUT_A` | `zhipu-ai/glm-4.5-air:free` | ☐ |
| `TTLG_THINKER_A` | `deepseek/deepseek-r1:free` | ☐ |
| `TTLG_SURGEON_A` | `deepseek/deepseek-coder-v2-lite:free` | ☐ |
| `TTLG_ANALYST_A` | `qwen/qwen2.5-coder-7b-instruct:free` | ☐ |
| `TTLG_LEGACY_A` | `deepseek/deepseek-r1:free` | ☐ |
| `TTLG_SCOUT_B` | `zhipu-ai/glm-4.5-air:free` | ☐ |
| `TTLG_THINKER_B` | `deepseek/deepseek-r1:free` | ☐ |
| `TTLG_SURGEON_B` | `zhipu-ai/glm-4.5-air:free` | ☐ |
| `TTLG_ANALYST_B` | `openrouter/free` | ☐ |
| `TTLG_LEGACY_B` | `deepseek/deepseek-r1:free` | ☐ |
| `PRIORITY_MODE` | `accuracy` | ☐ |
| `GOVERNANCE_APPROVAL_MODE` | `ui` or `cli` | ☐ |
| `MAX_API_RETRIES` | `2` | ☐ |
| `API_RETRY_BACKOFF_SECONDS` | `5` | ☐ |
| `FRIDAY_LOG_DECISIONS` | `true` | ☐ |

---

## Section B — Anchor Documents

All of the following `.md` files must exist in `EPOS_ROOT` before Claude Code opens. These are the behavioral constraints that prevent drift and hallucination. Claude Code cannot be anchored to rules that don't exist on disk.

Run: `ls $EPOS_ROOT/*.md` to confirm presence.

| File | Purpose | Confirmed |
|------|---------|-----------|
| `EPOS_CONSTITUTION_v3.1.md` | Core principles, hard boundaries, non-negotiables | ☐ |
| `TTLG_MODEL_ROUTING_CHARTER.md` | Model roles, routing rules, PRIORITY_MODE, amendment process | ☐ |
| `TTLG_SYSTEMS_CYCLE.md` | Cycle A — all 6 phases, inputs/outputs, schemas, halt conditions | ☐ |
| `TTLG_MARKET_CYCLE.md` | Cycle B — all 6 phases, inputs/outputs, schemas, halt conditions | ☐ |
| `FRIDAY_ORCHESTRATION_CHARTER.md` | Friday scope, prohibited actions, decision log format, escalation rules | ☐ |
| `CLAUDE_CODE_CHARTER.md` | Claude Code operational boundaries, gate protocol, error handling rules | ☐ |
| `TTLG_LOGGING_POLICY.md` | What gets logged, where, by whom, in what format | ☐ |
| `PRE_FLIGHT_CHECKLIST.md` | Environment, services, ports validation checklist | ☐ |
| `TTLG_BUILD_COMMANDER_MISSION.html` | What to build — infrastructure layer mission spec | ☐ |

---

## Section C — Model & Routing Sanity

### C1. Model Assignments
- [ ] Open `TTLG_MODEL_ROUTING_CHARTER.md` and confirm the model table matches your `.env` values
- [ ] `TTLG_THINKER_A` and `TTLG_THINKER_B` are both `deepseek/deepseek-r1:free` — confirm these match
- [ ] `TTLG_LEGACY_A` and `TTLG_LEGACY_B` are both `deepseek/deepseek-r1:free` — confirm these match
- [ ] No TTLG model key contains a paid/proprietary model (OpenAI, Claude API direct, etc.)
- [ ] `CLAUDE_SURGEON_BACKEND` is `deepseek/deepseek-coder-v2-lite:free`

### C2. PRIORITY_MODE
- [ ] `PRIORITY_MODE` in `.env` is set to exactly one of: `accuracy`, `speed`, or `cost_zero`
- [ ] If starting fresh: set to `accuracy`

### C3. API Reachability (quick smoke test — no need to run a full query)
- [ ] Run: `curl -s -o /dev/null -w "%{http_code}" https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY"`
- [ ] Confirm HTTP status 200
- [ ] Run: `python -c "import google.generativeai as genai; genai.configure(api_key='$GEMINI_API_KEY'); print('Gemini OK')"`
- [ ] Confirm output: `Gemini OK`

---

## Section D — Vault Structure

### D1. Vault Directories
- [ ] Run: `ls $EPOS_ROOT/vault/`
- [ ] Confirm all four directories exist: `runs/`, `failures/`, `patterns/`, `constitution/`
- [ ] Run: `touch $EPOS_ROOT/vault/write_test.txt && rm $EPOS_ROOT/vault/write_test.txt`
- [ ] Confirm no permission error — vault is writable

### D2. Constitution in Vault
- [ ] `vault/constitution/EPOS_CONSTITUTION_v3.1.md` exists (copied from `EPOS_ROOT`)

---

## Section E — Cycle Definitions

### E1. Cycle A Verified
- [ ] Open `TTLG_SYSTEMS_CYCLE.md`
- [ ] Confirm Phase 1 through Phase 6 are each defined with: inputs, system prompt, output artifact name and path, completion criteria, and halt condition
- [ ] Confirm all six artifact filenames are listed: `Scout_Map.json`, `Heal_List.json`, `Approved_Heal_List.json`, `Proposed_Patches.txt`, `Verification_Report.json`, `AAR.json`

### E2. Cycle B Verified
- [ ] Open `TTLG_MARKET_CYCLE.md`
- [ ] Confirm Phase 1 through Phase 6 are each defined with: inputs, system prompt, output artifact name and path, completion criteria, and halt condition
- [ ] Confirm all six artifact filenames are listed: `Market_Map.json`, `Gap_Opportunity_Map.json`, `Approved_Gap_List.json`, `Solution_Concepts.json`, `Validation_Report.json`, `Productization_Decision.json`

---

## Section F — Friday (Gemini) Oversight

- [ ] Open `FRIDAY_ORCHESTRATION_CHARTER.md`
- [ ] Confirm Friday's system prompt template is present in Section 7
- [ ] Confirm `FridayDecision` JSON schema is defined
- [ ] Confirm the escalation rules table is populated with all 7 conditions
- [ ] Confirm `.env` contains: `FRIDAY_LOG_DECISIONS=true`, `FRIDAY_TEMPERATURE=0.1`, `FRIDAY_SCHEDULE_UTC`

---

## Section G — Claude Code Operational Boundaries

- [ ] Open `CLAUDE_CODE_CHARTER.md`
- [ ] Confirm "First Action — Every Session" section specifies `python epos_doctor.py` as first command
- [ ] Confirm `ModelRouter` class definition is present or linked
- [ ] Confirm build verification report schema is defined
- [ ] Confirm all six constitutional violation types are listed with required responses

---

## Section H — epos_doctor.py

### H1. Script Exists and Runs
- [ ] `epos_doctor.py` exists at `EPOS_ROOT/epos_doctor.py`
- [ ] Run: `python epos_doctor.py`
- [ ] Confirm exit code 0 and "all checks passed" output

### H2. Doctor Checks Confirmed
The doctor script must check all of the following. Open `epos_doctor.py` and verify each check is implemented:

| Check | Implemented in doctor | Confirmed |
|-------|----------------------|-----------|
| Python version is 3.11.x | ☐ | ☐ |
| `EPOS_ROOT` env var set and directory exists | ☐ | ☐ |
| `.env` file exists and is parseable | ☐ | ☐ |
| `OPENROUTER_API_KEY` present | ☐ | ☐ |
| `GEMINI_API_KEY` present | ☐ | ☐ |
| `ANTHROPIC_API_KEY` present | ☐ | ☐ |
| All `TTLG_*` model keys present | ☐ | ☐ |
| `PRIORITY_MODE` is valid value | ☐ | ☐ |
| `vault/` directory writable | ☐ | ☐ |
| No hardcoded paths in `.py` files (grep) | ☐ | ☐ |
| All anchor `.md` files present in `EPOS_ROOT` | ☐ | ☐ |

### H3. Integration Smoke Test
- [ ] Run a simulated `code_audit` trigger through the Auto-Router
- [ ] Confirm `RouteDecision.json` appears in `vault/runs/{run_id}/`
- [ ] Confirm `BUILD_VERIFICATION_REPORT_{mission_id}.json` exists in `vault/` with `build_status: "COMPLETE"` after infrastructure build completes

---

## Section I — Logging & Drift Protection

- [ ] Open `TTLG_LOGGING_POLICY.md`
- [ ] Confirm Logger module implementation or specification is present
- [ ] Confirm `FailureArtifact` schema is defined
- [ ] Confirm log retention policy (permanent, never delete) is stated
- [ ] Run any phase test and confirm `run.log` appears in `vault/runs/{run_id}/` with at least one JSON-lines entry

---

## Section J — Pre-Launch Sign-Off

All sections A through I must be checked before this section is reached.

- [ ] Every checkbox in Sections A–I is confirmed
- [ ] `python epos_doctor.py` exits 0 in a fresh terminal session (not just in an active venv)
- [ ] Jamie has reviewed and accepts this checklist as complete

**Sign-off:**

```
Launch authorized: _____________________________ Date: ________________
                   Jamie (Human Steward)
```

---

## What Happens After This Checklist Is Complete

1. Open Claude Code with `EPOS_ROOT` as the workspace
2. Add to Claude Code's project context:
   - `TTLG_BUILD_COMMANDER_MISSION.html`
   - `TTLG_MODEL_ROUTING_CHARTER.md`
   - `CLAUDE_CODE_CHARTER.md`
3. Claude Code reads the mission brief
4. Claude Code runs `python epos_doctor.py` as its first action
5. Infrastructure build proceeds from Step 1 to Step 10 with gate checks
6. `BUILD_VERIFICATION_REPORT_{mission_id}.json` is produced with `build_status: "COMPLETE"`
7. Archive this checklist and this conversation to project knowledge
8. Track A and Track B mission briefs are the next build sessions

---

## If You Come Back to This After a Break

Before resuming any build session — even one hour later — re-run:

```bash
python epos_doctor.py
```

And re-confirm Section A (Python version, EPOS_ROOT, .env). Environments drift. The doctor catches drift. The checklist is your reminder that the doctor runs first, always.

---

*Last updated: 2026-03-01 · Authority: TTLG Model & Routing Charter v1.0*
