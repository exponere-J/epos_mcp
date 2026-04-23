# The Pre-Mortem Framework

## Five documents that prevent the failures you'd otherwise post-mortem.

---

## Why pre-mortems beat post-mortems

A post-mortem is the autopsy. It tells you what killed the patient
AFTER the funeral. A pre-mortem is the stress test. It imagines the
patient's failure in advance so you can bolt on the guard-rails before
the operation starts.

Pre-mortems are cheap. Post-mortems are expensive.

The Pre-Mortem Framework is five constitutional documents and one
enforcement script, arranged so that together they prevent ~80% of the
failures that would otherwise require post-mortems.

## How the five documents fit together

```
                  ┌─────────────────────────┐
                  │ 01. EPOS Constitution   │  ← the ROOT
                  │   Hard boundaries,       │    governing everything
                  │   quality gates,         │    below
                  │   amendment process      │
                  └───────────┬─────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
 ┌───────────────┐  ┌───────────────────┐  ┌───────────────────┐
 │ 02. Failure   │  │ 03. Path Clarity  │  │ 05. Environment   │
 │  Scenarios    │  │   Rules           │  │   Spec            │
 │ (the catalog  │  │ (the single most  │  │ (the contract     │
 │  of what      │  │  common class of  │  │  between code     │
 │  fails)       │  │  failure)         │  │  and runtime)     │
 └───────┬───────┘  └─────────┬─────────┘  └─────────┬─────────┘
         │                    │                      │
         └────────────────────┼──────────────────────┘
                              ▼
                  ┌─────────────────────────┐
                  │ 04. Pre-Flight          │
                  │   Checklist              │  ← the OPERATIONAL
                  │   (go/no-go before       │    enforcement point
                  │   any deploy or          │
                  │   significant op)        │
                  └───────────┬─────────────┘
                              │
                              ▼
                  ┌─────────────────────────┐
                  │   epos_doctor.py         │  ← the AUTOMATIC
                  │   (runs the checklist,   │    guard-rail
                  │   refuses to proceed if  │
                  │   violations exist)      │
                  └─────────────────────────┘
```

## How to read them in order

### 1. Start with `01_EPOS_Constitution.md` (15 min)

This is the root. It defines:
- **Foundational principles** — what the system optimizes for
- **Hard boundaries** — what will never be crossed, regardless of
  convenience
- **Quality gates** — what must pass before code merges or deploys
- **Architectural discipline** — the invariants
- **Amendment process** — how the rules themselves change

You won't remember all of it. You'll return.

### 2. Then `03_Path_Clarity_Rules.md` (10 min)

We put this second because **path mixing is the #1 cause of
"it-works-on-my-machine" deployment failures.** The document gives you
the specific rules that eliminate it. Read this before you touch any
code.

### 3. Then `05_Environment_Spec.md` (10 min)

This describes the environments your code runs in (dev, staging,
production) and what contract each of them enforces. If your code
makes an assumption about the environment, that assumption should be
in this doc. If it's not, your code has an uncaptured dependency.

### 4. Then `02_Failure_Scenarios.md` (reference, 20 min skim)

This is the encyclopedia of failure patterns. Skim it once. Come back
when something breaks — you'll often find the exact pattern documented
with a recovery procedure.

### 5. Then `04_Pre_Flight_Checklist.md` (10 min)

This is the operational document — the actual list you run before
every deploy or significant operation. It references the other four
documents.

### 6. Finally, `EPOS_DOCTOR_REFERENCE.md` (5 min)

The Doctor automates the checklist. This reference explains what it
runs, how to invoke it, and how to add your own checks.

Total first-read time: ~75 minutes.

## What to do after you've read them

1. **Adopt the Path Clarity Rules immediately.** They're the cheapest
   win — a 10-minute discipline change that prevents a class of
   deploy failures permanently.

2. **Run the Pre-Flight Checklist on your next deploy.** You'll feel
   what the framework does.

3. **Catalog your own failures.** The Failure Scenarios document is
   a reference for EPOS-style failures. Your organization has its own.
   Add them in the same format. Over time this becomes your
   institutional memory.

4. **Extend the Doctor.** Each custom check you add is one less
   failure you can make twice.

## What this kit does NOT give you

- A post-mortem template. (Use `CCP Pack templates/04_diagnostics.md`
  for that — or any standard incident-review template.)
- A fix for organizational problems. If your team doesn't use
  checklists, adding a constitution won't help. Culture first.
- A substitute for judgment. The framework constrains decisions; it
  doesn't make them.

## The compound effect

Every failure you prevent with this framework is one you don't have
to explain in a post-mortem. Over a year, that's dozens of hours of
meetings, thousands of dollars of engineer time, and (most
importantly) the trust that comes from shipping reliably.

One percent better every day. Thirty-seven times better in a year.

---

*Produced by EPOS. 1% daily. 37x annually.*
