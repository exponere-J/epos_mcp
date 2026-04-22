# TTLG RESUBMISSION LOOP v1

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §1
**Charter:** `COUNCIL_CHARTER_v1.md`
**Ratified:** 2026-04-22 by Sovereign
**Status:** Active

---

## Purpose

Define the elegant cycle by which a component that fails TTLG validation
becomes a registered, market-validated capability without human orchestration.

**Hard rule:** no component reaches the Process Registry except through this
loop. No market claim is made about a component not in the Registry.

## The Loop (one revolution)

```
┌──────────────┐
│  1. SUBMIT   │  new or revised module appears under epos/, nodes/, or friday/
└──────┬───────┘
       ▼
┌──────────────┐
│  2. SCOUT    │  What does this do? Inputs/outputs/deps/failure modes.
└──────┬───────┘
       ▼
┌──────────────┐
│  3. THINKER  │  How does it interact? Capabilities? Overlap? Risk?
└──────┬───────┘
       ▼
┌──────────────┐
│  4. GATE     │  REGISTER | REVISE | REJECT | LEGACY_AUDIT
└──┬────┬───┬──┘
   │    │   │
   │    │   └─→ REJECT  → AAR; quarantine; loop ends for this component
   │    │
   │    └─→ REVISE    →  5a. Architect emits FORGE_DIRECTIVE_TTLG_REMEDIATION_<component>
   │                      5b. Forge executes remediation
   │                      5c. Ingestion-runner detects the revised file
   │                      5d. RESUBMIT — component re-enters at Step 2
   │
   └─→ REGISTER or LEGACY_AUDIT → 6. SURGEON writes registry entry
                                    7. ANALYST logs spec ↔ actual delta
                                    8. Reward Bus scores at T+24h, T+48h, T+90d
```

Every transition is an event on the bus:
- `ttlg.submitted` (1 → 2)
- `ttlg.scouted` (2 → 3)
- `ttlg.thought` (3 → 4)
- `ttlg.gate.<verdict>` (4 → 5/6)
- `ttlg.remediation.directive_emitted` (5a)
- `ttlg.remediation.forge_complete` (5b)
- `ttlg.resubmitted` (5d → 2)
- `ttlg.registered` (6)
- `ttlg.analyzed` (7)
- `ttlg.rewarded` (8)

## Elegance clauses

### E1. Verdict-driven routing
Each Gate verdict has exactly one downstream handler. No branching human
judgment inside the loop. Sovereign-override is available at Step 5a
(approve/decline the proposed remediation) and nowhere else.

### E2. Idempotent resubmission
A module that re-enters the loop at Step 2 is diffed against its prior
Scout result. If the diff is empty, the loop short-circuits to the prior
verdict — no re-work. If the diff is non-empty, full re-validation runs.

### E3. Non-blocking legacy
LEGACY_AUDIT entries are registered with metadata only and do NOT block
downstream consumers. They enter a lower-priority queue for deep live-TTLG
verification. When deep TTLG runs, the LEGACY_AUDIT entry is upgraded to
REGISTER or downgraded to REVISE/REJECT — in place, with a version bump.

### E4. Reward Bus integration
Every REGISTER produces a training pair for QLoRA at the 90-day mark:
`(component, actual_performance, predicted_performance, delta)`.
REVISE → REGISTER transitions are especially high-signal training pairs
because they capture what "good enough" looks like in practice.

### E5. Sovereign override trapdoor
Sovereign may invoke `ttlg.override` at any step with a rationale.
The override is logged, the component takes the overridden verdict, and
the override event feeds the Reward Bus just like any other decision.

## Remediation Directive Template

When Gate returns REVISE, Architect emits a Directive at
`missions/FORGE_DIRECTIVE_TTLG_REMEDIATION_<component>_<yyyymmdd>.md` with
this structure:

```markdown
# FORGE DIRECTIVE — TTLG REMEDIATION: <component>

**Source verdict:** REVISE (see <registry entry version>)
**Gate reason:** <TTLG verdict reason verbatim>
**Component:** <module path>
**Spec-delta required:**
  1. <specific change 1>
  2. <specific change 2>
  ...
**Verification (Forge must pass):**
  - <criterion 1>
  - <criterion 2>
**On success:** component re-enters loop at Step 2 automatically.
**On failure:** escalate to Sovereign with blocker memo.
```

## Wiring (three artifacts, ordered)

1. **Doctrine** — this file. Ratified. Governs the cycle.
2. **Forge Directive** — `FORGE_DIRECTIVE_TTLG_RESUBMISSION_WIRING_<yyyymmdd>.md`
   — builds the event handlers for each transition, extends
   `friday/executors/ttlg_executor.py` with a `post_completion` mode,
   adds `ttlg.request` → `ttlg_executor.run` routing.
3. **Ingestion-runner wiring** — extends the Bridge ingestion-runner
   (proposed in the prior turn) so new files pulled from GitHub
   auto-submit to Step 1 of this loop.

All three reference each other. When all three are live, the loop closes.

## Constitutional compliance

- **Article V** — all routing respects the `AgentId` registry. Scout/Thinker/
  Analyst ops execute via `AgentId.TTLG` (and `AgentId.OMEGA` for pattern
  extraction). Gate may invoke `AgentId.ALPHA` for constitutional-breach
  REJECT decisions.
- **Article X** — every verdict + transition is logged to the BI surface
  with rationale. No unlogged decisions.
- **Article XVI §1** — "the roster IS the truth" — the Process Registry
  reflects only what has passed this loop.

## Amendment

This doctrine is amended only by Sovereign decision, logged to the BI
surface with rationale. Version increments on amendment (`v1` → `v2`).

---

**See also:**
- `COUNCIL_CHARTER_v1.md`
- `OPERATING_PROTOCOL_v1.md` (the four canonical flows)
- `../../state/organism_state.json` — the Process Registry this loop feeds
- `../../aar/TTLG_POST_COMPLETION_20260422_AAR.md` — the first pass that
  produced the initial Registry population
