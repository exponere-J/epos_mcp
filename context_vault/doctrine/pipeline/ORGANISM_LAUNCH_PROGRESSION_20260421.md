# ORGANISM LAUNCH PROGRESSION — Stages 0 → 4 (2026-04-21)

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, X
**Strategy Doc:** `../strategic_intelligence/ONE_ORGANISM_TWO_HEARTBEATS_20260421.md`
**Charter:** `../councils/COUNCIL_CHARTER_v1.md`
**Status:** Active — Stage 0 entry

---

## Schema (every block)

Each Stage and Sprint below specifies:

- **Owner archetype** — who drives.
- **Supporting archetypes** — who contributes.
- **Executor agents** — registered `AgentId` values that perform vault-writes / engine touches.
- **Acceptance criteria** — objective, measurable.
- **Rollback trigger** — when to pause or reverse.
- **BI log path** — where the decision and AAR live.

---

## Stage 0 — Council Stand-up (this week)

- **Owner:** The Architect.
- **Supporting:** All six archetypes (ratification only).
- **Executor agents:** `ORCHESTRATOR` (coordination), `ALPHA` (gate).
- **Acceptance:**
  - Each of the six archetype files ratified by its named entity.
  - ALPHA reviews `COUNCIL_CHARTER_v1.md` for constitutional compliance; no unresolved findings.
  - First Council decision (ratification itself) logged to BI with rationale.
- **Rollback trigger:** ALPHA finds a constitutional violation in any archetype file.
- **BI log path:** `context_vault/bi/council/stage0_ratification.json`.

---

## Stage 1 — Gumroad Product Launch (weeks 1–6)

**Platform:** Gumroad (primary), Lemon Squeezy (optional secondary).
**Product class:** prompt-engineering products.

### Sprint 1 — Assemble and List (weeks 1–2)

- **Owner:** The Forge (execution); The Architect (Directive).
- **Supporting:** Oracle (product selection), Chronicler (Audio Overview prep), Steward (metrics hook), Sentinel (pre-flight audit).
- **Executor agents:** `SCC` (artifact generation), `BRIDGE` (mission decomposition), `FRIDAY` (metrics hook), `ALPHA` (gate).
- **Acceptance:**
  - 3 prompt-engineering products live on Gumroad.
  - Each product bundle has: PDF, structured prompt library, quick-start guide, SHA256 manifest.
  - Each product has an Audio Overview staged for Chronicler.
  - Listing copy skeletons approved by Sovereign.
- **Rollback trigger:** Sentinel pre-flight audit flags a critical gap; Forge readiness receipt stuck at `DISPATCHED` past SLA; Oracle signal contradiction on product fit.
- **BI log path:** `context_vault/bi/stage1/sprint1/`.

### Sprint 2 — First Sales & Testimonials (weeks 3–4)

- **Owner:** The Steward (buyer tracking); The Architect (AAR synthesis).
- **Supporting:** Oracle (post-launch signal reads), Chronicler (testimonial audio), Sentinel (conversation-gap audit).
- **Executor agents:** `FRIDAY` (buyer touchpoints), `SCC` (listing iterations).
- **Acceptance:**
  - ≥ 1 paying customer.
  - ≥ 1 published testimonial.
  - Clean AAR — no governance violations, no Status-Lies.
- **Rollback trigger:** Zero sales by end of week 4 with no Oracle-validated market-signal contradiction (redirect, don't pivot).
- **BI log path:** `context_vault/bi/stage1/sprint2/`.

### Sprint 3 — Iterate & Expand (weeks 5–6)

- **Owner:** The Oracle (iteration signal); The Architect (Directive v2).
- **Supporting:** Forge (listing updates, second-platform push), Chronicler (new-platform Overviews), Steward (metrics delta).
- **Executor agents:** `SCC`, `FRIDAY`, `ALPHA`.
- **Acceptance:**
  - ≥ 5 cumulative sales across both platforms.
  - Review-velocity threshold met (Stage-2-entry rubric).
  - Second platform (Lemon Squeezy) live with ≥ 1 listing.
- **Exit criterion to Stage 2:** Oracle Stage-2-entry rubric passes — credibility artifacts sufficient for service-marketplace listing.
- **Rollback trigger:** Review velocity below threshold; Oracle rubric fails.
- **BI log path:** `context_vault/bi/stage1/sprint3/`.

---

## Stage 2 — Service Marketplace Launch (milestone level)

**Platforms:** Fiverr, Upwork, and other service marketplaces.
**Architecture:** `SERVICE_MARKETPLACE_ARCHITECTURE.md` nodes 8130–8139.

### Milestones

- **M2.1 — Node 8130–8132 activation:** ingest/qualify/match surfaces live.
- **M2.2 — First service listing:** one offering live on Fiverr or Upwork.
- **M2.3 — First signed engagement:** one paid service contract.
- **M2.4 — CSR/marketing/sales profiler training:** Steward owns training data ingestion from Stage-1 and Stage-2 buyer conversations.
- **M2.5 — Node 8133–8139 full activation:** delivery coordinator, fulfillment, and closeout nodes.

- **Owner:** The Steward (operations); The Architect (Directive cadence).
- **Supporting:** Forge (node hardening), Oracle (category mapping), Chronicler (profiler training content), Sentinel (gap audit per milestone).
- **Executor agents:** `FRIDAY`, `SCC`, `BRIDGE`, `ALPHA`.
- **Exit criterion to Stage 3:** service-delivery repeatability (≥ 3 repeat motions without Directive revision) + Echoes-readiness rubric from `../../attachments/ECHOES_LAUNCH_WORKSPACE_AAR_20260328.md`.
- **BI log path:** `context_vault/bi/stage2/`.

---

## Stage 3 — Echoes Launch (milestone level)

**Source:** `../../attachments/ECHOES_LAUNCH_WORKSPACE_AAR_20260328.md` gap registry.

### Milestones

- **M3.1 — Gap closure:** every AAR-identified gap has a closed Directive.
- **M3.2 — Trust/notoriety leverage:** Stage 1–2 testimonials incorporated into Echoes positioning.
- **M3.3 — Flywheel ignition:** first self-reinforcing loop running.
- **M3.4 — Metrics stabilization:** flywheel KPIs stable across two weekly cycles.

- **Owner:** The Architect (vision); The Forge (execution).
- **Supporting:** All archetypes per active milestone.
- **Executor agents:** full registry.
- **Exit criterion to Stage 4:** Echoes flywheel metrics stabilized; Sovereign ratifies advance.
- **BI log path:** `context_vault/bi/stage3/`.

---

## Stage 4 — EPOS Launch (milestone level)

**Positioning:** `EPOS_MARKET_POSITIONING_20260404.md`.

### Milestones

- **M4.1 — Productize SCC:** enterprise-consumable packaging.
- **M4.2 — Governance hardening:** gate integrity at enterprise-buyer scrutiny level.
- **M4.3 — Enterprise demo motion:** repeatable demo → pilot → contract flow.
- **M4.4 — First enterprise contract.**

- **Owner:** The Architect (Sovereign-aligned); The Oracle (enterprise-buyer motion).
- **Supporting:** Forge, Chronicler, Steward, Sentinel per milestone.
- **Executor agents:** full registry.
- **Exit criterion:** Sovereign decision — no further stage; EPOS runs as the organism.
- **BI log path:** `context_vault/bi/stage4/`.

---

## Heartbeat Cross-References

At every stage, the Build heartbeat consumes Marketplace evidence (per `../councils/OPERATING_PROTOCOL_v1.md §II`):

- Stage 1 conversations → Stage 2 profiler training data.
- Stage 2 engagements → Stage 3 Echoes gap-closure priorities.
- Stage 3 flywheel signals → Stage 4 enterprise-positioning refinement.

No stage runs its Build work against hypothetical data. Evidence first; improvement second.

---

**See also:**
- `../strategic_intelligence/ONE_ORGANISM_TWO_HEARTBEATS_20260421.md`
- `../councils/COUNCIL_CHARTER_v1.md`
- `../councils/OPERATING_PROTOCOL_v1.md`
- `/home/user/epos_mcp/missions/FORGE_DIRECTIVE_STAGE1_20260421.md`
- `/home/user/epos_mcp/SERVICE_MARKETPLACE_ARCHITECTURE.md`
- `/home/user/epos_mcp/context_vault/attachments/ECHOES_LAUNCH_WORKSPACE_AAR_20260328.md`
- `/home/user/epos_mcp/context_vault/doctrine/strategic_intelligence/EPOS_MARKET_POSITIONING_20260404.md`
