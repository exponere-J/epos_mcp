# OPERATING_PROTOCOL_v1

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, X; Charter `COUNCIL_CHARTER_v1.md`
**Ratified:** 2026-04-21
**Status:** Active

---

## Preamble

**Jamie is the Sovereign.** This protocol describes how the six named archetypes of the EPOS Sovereign Council coordinate across the two heartbeats of the organism — Marketplace (primary) and Build (support posture).

The four flows below are **canonical**. They are reproduced verbatim from the Sovereign's specification and are not to be paraphrased, reordered, or truncated. Commentary belongs around the blocks, never inside them.

---

## I. Canonical Flows (verbatim)

```
MARKETPLACE LAUNCH (Primary Track):
  Oracle researches → Architect plans → Forge builds →
  Chronicler synthesizes → Steward delivers → Sentinel audits

BUILD TRACK (Support Posture):
  Sentinel identifies gaps → Architect writes directives →
  Forge executes → Oracle validates → Chronicler documents →
  Steward monitors

DECISION PROTOCOL:
  Jamie states intent → Architect structures the options →
  Oracle provides market evidence → Sentinel flags blind spots →
  Jamie decides → Forge executes → Steward tracks →
  Chronicler records for training

CONFLICT RESOLUTION:
  When council members disagree (Oracle says "market wants X"
  but Sentinel says "we're not ready for X"):
  → Architect presents both positions with evidence
  → Jamie makes the sovereign decision
  → Decision logged to PM surface with rationale
  → Reward Bus scores the outcome 90 days later
```

---

## II. Heartbeat Synchronization

The Marketplace and Build flows are not parallel-independent tracks. They are **one organism with two heartbeats** — the marketplace generates revenue, evidence, and training data; the build consumes that data to improve the organism.

### Marketplace → Build (evidence flow)

- Signed deals, reviews, buyer conversations arrive via Steward BI hooks.
- Chronicler synthesizes patterns into source satellites.
- Sentinel audits synthesized patterns for gaps the flywheel missed.
- Architect packages gaps into Build-track Directives.
- Forge executes improvements to the organism.

### Build → Marketplace (engine flow)

- New nodes, refactored agents, hardened gates arrive via Forge completion receipts.
- Steward updates client-facing surfaces.
- Oracle re-validates positioning against the improved capability.
- Chronicler re-synthesizes marketing surface.
- Architect adjusts the active-stage Directive to exploit the upgrade.

Neither flow is "done" — they loop. A stage advances only when the Sovereign ratifies the advance.

---

## III. Reward Bus Hook (scoring at 90 days)

Every Sovereign decision logged under the Conflict Resolution block is scored 90 days after ratification. The score is written to:

`context_vault/bi/reward_bus/<decision_id>.json`

Score inputs: actual vs. predicted outcome, financial delta, organism-health delta, Sentinel post-hoc flag count. The Reward Bus output feeds Training/BizEd rubrics via The Steward.

---

## IV. Escalation Lattice

Each flow pauses and routes to the Sovereign under these conditions (per `COUNCIL_CHARTER_v1.md §V`):

| Flow | Pause Condition | Route |
|---|---|---|
| Marketplace Launch | Sentinel audits flag a live risk | → Sovereign via Architect |
| Marketplace Launch | Oracle detects market-signal contradiction mid-execution | → Sovereign via Architect |
| Build Track | ALPHA veto on a proposed Directive | → Sovereign via Architect |
| Build Track | Forge readiness receipt marks a step `DISPATCHED` but not `VERIFIED` past SLA | → Sovereign via Steward |
| Decision Protocol | Any step ambiguous in Sovereign intent | → Sovereign via Architect (restated options) |
| Conflict Resolution | Split persists after one re-deliberation cycle | → Sovereign (unlatched decision) |

Routes are always through a registered agent (Architect, Steward) per Charter §VIII and Article VII.

---

## V. Cadence Overlay

- **Daily (05:30 / 22:00):** Steward briefings.
- **Weekly:** full Council sync; Sentinel audit summary; Oracle signal digest.
- **Per-stage gate:** Council sign-off; Reward Bus check-in for decisions at the 90-day mark.
- **On-event:** Conflict Resolution triggers immediately when split is detected; Decision Protocol triggers on Sovereign intent expression.

---

## VI. Non-Negotiable Principles

1. **Sovereignty** — no flow executes against a logged Sovereign decision.
2. **Heartbeat unity** — no archetype runs a private side-track.
3. **Citation discipline** — every claim traces to a source; every decision traces to rationale.
4. **Offline sovereignty** — Sentinel data stays on Jamie's machine.
5. **Execution honesty** — `DISPATCHED / ACKNOWLEDGED / VERIFIED` receipts reflect actual state.

---

**See also:**
- `COUNCIL_CHARTER_v1.md` (governance)
- `ARCHITECT_ARCHETYPE.md`, `ORACLE_ARCHETYPE.md`, `SENTINEL_ARCHETYPE.md`, `FORGE_ARCHETYPE.md`, `CHRONICLER_ARCHETYPE.md`, `STEWARD_ARCHETYPE.md`
- `../strategic_intelligence/ONE_ORGANISM_TWO_HEARTBEATS_20260421.md` (vision)
- `../pipeline/ORGANISM_LAUNCH_PROGRESSION_20260421.md` (execution plan)
