# Category 4 — Post-Mortem & Diagnostics (4 templates)

*Use case: something broke, or something that should have worked
didn't, or a decision turned out wrong. You need a clean post-mortem
that won't devolve into blame. These templates enforce discipline.*

---

## Template 4.1 — The Blameless Post-Mortem

### `# DOCUMENT`

This is a post-mortem. It will be read by people who weren't there.
It must be blameless: describe system failures, not person failures.
If a person is named, it's because they were the person who fixed it,
not because they were the person who broke it.

### `# SECTION — What happened (≤150 words)`

Plain English. First: the observable effect. Then: the triggering
change. Then: the time-window. Example: "Between 09:14 and 09:47,
checkouts returned HTTP 500. The trigger was a deploy at 09:13 that
introduced a null-check regression in pricing.py."

### `# SECTION — How we found out`

Specifically: what signal, what timestamp, who saw it first, how long
before they acted. Describe the detection, not the detective.

### `# SECTION — What we did`

Sequential actions with timestamps. Example:
- 09:19 — rollback initiated
- 09:24 — rollback complete
- 09:30 — verified 200s returning
- 09:47 — all-clear

### `# SECTION — Why it happened (systems, not people)`

3–5 bullets. System-level causes. "The null-check was missing because
the unit test mocked a type that couldn't be null in real life." Not
"the author didn't check."

### `# SECTION — What we're changing`

3–5 bullets. Each has an owner and a due date. One per root cause.

### `# TOKEN`

Prefer: passive voice where it removes blame ("the deploy introduced..."),
concrete timestamps, specific module names. Avoid: "X should have," "we
were surprised to find," "lessons learned."

---

## Template 4.2 — The Decision Regret Journal

### `# DOCUMENT`

This is an entry in my decision regret journal. I write one when a
decision turned out wrong. The point is to learn the shape of my own
decision errors, not to beat myself up.

### `# SECTION — Decision (verbatim)`

What I chose. One sentence. Exactly as I stated it to myself at the
time.

### `# SECTION — Why I chose it (verbatim from my past self)`

The reasons my past self would have given. 3–5 bullets.

### `# SECTION — What I know now`

What's true that I didn't know then. 3–5 bullets. Note: this is what's
TRUE NOW. Not "obvious in retrospect." Actually true now.

### `# SECTION — Shape of the error`

One sentence. A classification — e.g., "I over-weighted the most recent
signal." or "I mistook speed for progress."

### `# SECTION — Rule I'm trying`

One sentence. A specific rule I'll try for the next 3 months to avoid
repeating this. Not an aspiration. A rule.

### `# TOKEN`

Prefer: I, chose, wrong, rule. Avoid: "unfortunately," "in hindsight,"
"lesson learned."

---

## Template 4.3 — The Product Pre-Mortem

### `# DOCUMENT`

This is a pre-mortem. I'm writing from 6 months in the future,
assuming the launch failed. I describe what went wrong, from the
future-self perspective, today — before it happens — to surface
blindspots.

### `# SECTION — The failure (one sentence)`

"Six months from launch, this product had X users, Y revenue, Z churn.
It's considered a failure because <specific reason>."

### `# SECTION — What went wrong (5 causes)`

5 bullets. Each is a plausible post-mortem bullet written in the past
tense. "The onboarding was 47 minutes, and 73% of signups abandoned
before finishing."

### `# SECTION — Signals we should have seen (3)`

3 bullets. Things visible RIGHT NOW that could have warned us. Concrete.

### `# SECTION — Mitigations we'll take`

Per signal: one sentence on what we'll change before launch.

### `# TOKEN`

Prefer: past tense (simulating the future), concrete numbers, specific
user behaviors. Avoid: "might have," "could potentially," "in theory."

---

## Template 4.4 — The Reversibility Audit

### `# DOCUMENT`

This is a one-page reversibility audit for a proposed action. I write
it before committing. It tells me whether the action is safe-to-try
or slow-down-first.

### `# SECTION — Action`

One sentence. What I'm considering.

### `# SECTION — Blast radius`

Bullets. Who/what this affects if it goes wrong.

### `# SECTION — Reversibility (1–5 scale)`

- 1 = one command, restores in seconds (e.g. git revert)
- 2 = takes hours to restore, data intact (e.g. redeploy)
- 3 = takes a day, some state lost (e.g. rollback + replay)
- 4 = days to restore, customer-visible degradation
- 5 = irreversible (deletion, published content, sent email)

State the score, state why.

### `# SECTION — Decision gate`

- If 1–2: proceed without confirmation
- If 3: log rationale, proceed
- If 4: get Sovereign ratification
- If 5: Sovereign ratification + explicit rollback plan

### `# TOKEN`

Prefer: specific minutes, specific commands, specific user numbers.
Avoid: "moderate," "significant," "material impact," "potentially."

---

## How to pick the right template

| Situation | Template |
|---|---|
| Something broke; need a post-mortem | 4.1 |
| A past decision turned out wrong | 4.2 |
| Upcoming launch; stress-test in advance | 4.3 |
| Deciding whether to take an action NOW | 4.4 |
