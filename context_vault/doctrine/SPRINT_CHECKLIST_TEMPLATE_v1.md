# EPOS Sprint Checklist Template v1.0
## Constitutional Authority: EPOS Constitution v3.1
## Ratified: 2026-03-30

**Doctrine**: The checklist generates the AAR as a byproduct of disciplined execution. Not AAR plus checklist — checklist that produces AAR.

---

## A. BEFORE CODE (Gate — nothing executes until all checked)

### Environment Verification
- [ ] Working directory confirmed: `pwd` matches expected path
- [ ] Python version verified: `python --version` → 3.11.x
- [ ] Venv active: `which python` shows `.venv/` path
- [ ] .env loaded: all required keys present (list them)
- [ ] Docker containers running: `docker ps` shows expected services
- [ ] Ports verified: no conflicts on required ports
- [ ] Shell context confirmed: WSL / PowerShell / Git Bash (specify which)

### File Touch Declaration
- [ ] Every file this session will create or modify is listed below:
  ```
  CREATE: <path>
  MODIFY: <path>
  DELETE: <path>
  ```
- [ ] For each MODIFY file: read it first, confirm current state
- [ ] For each dependency: verify import chain resolves

### Pre-Mortem (3 minimum)
- [ ] Failure mode 1: _____________ Prevention: _____________
- [ ] Failure mode 2: _____________ Prevention: _____________
- [ ] Failure mode 3: _____________ Prevention: _____________

### Success Criteria (defined before work begins)
- [ ] Criterion 1: _____________
- [ ] Criterion 2: _____________
- [ ] Criterion 3: _____________

---

## B. DURING BUILD (One task at a time)

### Task Log (fill as you go — this becomes the AAR)

| # | Task | File(s) | Command Run | Expected | Actual | Status |
|---|------|---------|-------------|----------|--------|--------|
| 1 | | | | | | |
| 2 | | | | | | |

### Decision Ledger (every deviation from plan gets an entry)

| Decision | Rationale | Consequence | Reversal Cost |
|----------|-----------|-------------|---------------|
| | | | |

### Verification Receipts

| Module | Command | Expected | Actual | PASS/FAIL |
|--------|---------|----------|--------|-----------|
| | `py_compile` | exit 0 | | |
| | self-test | PASS | | |
| | doctor | 0 fail | | |

---

## C. SESSION CLOSE

### Touched Assets Register
```
Files created:    N
Files modified:   N
Files deleted:    N
DB changes:       N tables / N rows
Vault assets:     N new entries
Events published: N
```

### Architectural Decisions Summary
| Decision | Why | What it prevents | What it enables |
|----------|-----|-----------------|-----------------|
| | | | |

### Remaining Risks
| Risk | Trigger | Mitigation | Owner |
|------|---------|------------|-------|
| | | | |

### Next Session Starting Conditions
```
Doctor state:     ___ PASS / ___ WARN / ___ FAIL
Event bus:        ___ events
Key dependencies: ___
First action:     ___
```

### AAR Summary (5 sections — all required)
1. **What changed**: (list components that moved)
2. **Why this way**: (tie to prior failure or constitutional principle)
3. **Failure modes anticipated**: (from pre-mortem above)
4. **New capabilities**: (what the organism can now do)
5. **Success criteria met**: (check against Section A criteria)

---

## Usage

Copy this template at session start. Fill Section A completely before writing any code. Fill Section B as you work. Fill Section C before closing the session. The completed checklist IS the AAR.
