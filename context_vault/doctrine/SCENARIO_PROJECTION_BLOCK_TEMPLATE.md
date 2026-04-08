# SCENARIO PROJECTION BLOCK — MANDATORY DIRECTIVE ATTACHMENT
## Constitutional Authority: EPOS Constitution v3.1, Pre-Mortem Mandate
## Ratified: 2026-04-01

---

## PURPOSE

Every directive handed from planning context to execution context (Desktop Claude Code, Agent Zero, or any future agent) MUST include this block. The planning intelligence performs the pre-mortem; the execution agent verifies before writing the first line.

The gap this closes: the IPP happens in the planning thread but evaporates at the boundary between planning and execution. This block is the bridge.

---

## TEMPLATE

```
=== SCENARIO PROJECTION BLOCK ===
Directive: [One-line description]
Target Files: [List of files that will be created or modified]

ENVIRONMENT GRID:
  Python:     3.11.x (C:\Users\Jamie\AppData\Local\Programs\Python\Python311\python.exe)
  OS:         Windows 11
  DB:         PostgreSQL 17 via Docker (epos_db container, accessed via docker exec)
  API Keys:   GROQ_API_KEY in .env (Groq router for LLM calls)
  Framework:  Reflex (Command Center), LangGraph (state machines)
  Event Bus:  JSONL file at context_vault/events/system/events.jsonl
  Vault:      context_vault/ (JSONL journals, JSON artifacts)
  No Git:     Standing order — no git add, commit, push, or PR operations

SCENARIO PROJECTIONS:

  Scenario 1: [Failure mode]
    Trigger: [What causes it]
    Expected Behavior: [What should happen]
    Verification: [How to confirm before writing code]

  Scenario 2: [Failure mode]
    Trigger: [What causes it]
    Expected Behavior: [What should happen]
    Verification: [How to confirm before writing code]

  Scenario 3: [Failure mode]
    Trigger: [What causes it]
    Expected Behavior: [What should happen]
    Verification: [How to confirm before writing code]

PRE-FLIGHT CHECKS (agent must verify before first line of code):
  [ ] Target files exist and are readable
  [ ] Required imports are available in current Python
  [ ] .env is loaded and required keys are present
  [ ] Docker container epos_db is running (if DB needed)
  [ ] No fcntl or Unix-only imports on Windows
  [ ] No f-string backslash paths (use forward slashes)
  [ ] Self-test passes after changes

STOP CONDITION:
  If any pre-flight check fails or any scenario cannot be verified,
  STOP and report. Do not write speculative code.

=== END SCENARIO PROJECTION BLOCK ===
```

---

## KNOWN FAILURE CATEGORIES (from Architectural Analysis)

These are the six categories that have caused real failures in the EPOS codebase. Every directive should check whether its changes touch any of these:

1. **Path Mixing** — Windows backslash vs forward slash. `C:\Users` parsed as Unicode escape in f-strings.
2. **File I/O Silent Failures** — Writing to a path that doesn't exist doesn't always throw. JSONL append to missing parent dir.
3. **Module Import Assumptions** — Importing `fcntl` (Unix-only). Importing at module level causes crash at import time.
4. **Shell Syntax in Python** — Docker exec commands with pipes, quotes. Subprocess needs list args, not string.
5. **Status Lies** — "Logged" confused with "executed." Event published but handler never ran.
6. **.env Not Auto-Loading** — dotenv must be explicitly loaded before any os.getenv call.

---

## ENFORCEMENT

- Planning agent includes this block in every directive
- Execution agent verifies pre-flight before writing
- If execution agent cannot verify a scenario, it stops and asks
- AAR documents which scenarios were hit and how they were resolved
- Doctor checks for presence of SPB in active directives (future)

---

*The IPP happens once. The SPB travels forever.*
