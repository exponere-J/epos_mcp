# EPOS OPERATIONAL COMPONENTS — Exploded View (Mechanical Detail)

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI
**Ratified:** 2026-04-23 by Sovereign
**Triad companion to:** `EPOS_UNIFIED_REGISTRY_DOCTRINE_20260423.md` (strategic overview) + `EPOS_SIGNAL_TO_SHELF_PIPELINE.md` (implementation plan)

---

## Purpose

Strategic overview says *why*. Implementation plan says *in what order*.
This document says **how each piece actually works internally**.

One short section per component. Scannable. Pinned next to the code.

---

## Listener — FOTW Sensors + Firecrawl

**What it does:** Reads the Dream 100 and public communities on a
daily cadence, extracts 5 signal types (pain language, feature
requests, price sensitivity, competitor weaknesses, unmet needs), and
writes them to the signal registry with confidence + frequency scores.

**Inputs:** a Dream 100 config (`context_vault/fotw/dream_100.json`),
Firecrawl API key, platform session states (for Discord/LinkedIn/Skool).

**Outputs:** `context_vault/fotw/signal_registry.json` — append-only,
keyed by `signal_id = sha256(verbatim + source_url)[:16]`.

**Event emissions:**
- `fotw.sensor.pass.complete` (on every full sweep)
- `fotw.signal.captured` (per new signal)
- `fotw.signal.upgraded` (when frequency ≥ 3 within 7 days)

**Failure modes:**
- Firecrawl rate-limited → back-off + log + retry in 60 min
- Session expired → `fotw.session.expired` event for Sovereign re-auth
- Platform UI changed → Sentinel flags; monitor returns empty; no crash

**Current status:** Reddit monitor wired (via Firecrawl arm). Discord/
LinkedIn/Skool/Newsletter are scaffolds returning empty; wiring is a
Stage-B build.

---

## Gatekeeper — SQLite Traffic Buffer

**What it does:** Ingests every FOTW signal (and any other inbound
signal — Oracle research, Sentinel flags), deduplicates via
nomic-embed cosine similarity, assigns a pain-magnitude priority score,
and gates what advances to Synthesis.

**Why a buffer:** the pipeline runs asynchronously. The buffer
decouples sensor cadence from synthesis cadence, and prevents
duplicates from inflating the backlog.

**Dedup algorithm:**
1. New signal arrives with verbatim text
2. Nomic-embed produces a 768-d vector
3. Buffer finds the 5 nearest neighbors in the last 30 days
4. If max cosine similarity > 0.92, merge (increment frequency; keep
   higher-confidence record)
5. Else insert new row

**Priority scoring:**
```
score = (pain_magnitude × 0.4)
      + (frequency × 0.3)
      + (confidence × 0.2)
      + (source_diversity × 0.1)
```
Range 0–10. Scores ≥ 7 trigger immediate Synthesis. Scores 4–6 batch
daily. < 4 quarantined for 7 days.

**Schema (SQLite):**
```sql
CREATE TABLE signals(
  signal_id TEXT PRIMARY KEY,
  verbatim TEXT, source_platform TEXT, source_url TEXT,
  signal_type TEXT, confidence REAL, frequency INTEGER,
  priority_score REAL, created_at TEXT, last_seen_at TEXT,
  embedding BLOB
);
```

**Current status:** not yet built (CC-OP-003).

---

## Synthesizer — Gap Bridge Matrix + CCP

**What it does:** Joins the signal stream (what the market asks for)
with the capability index (what EPOS has) and emits product candidates.

**Join logic:**
1. For each high-priority signal, classify its domain (content /
   voice / pricing / governance / etc.)
2. Query `capability_index[domain]` — get list of components that can
   address the domain
3. Apply CCP 4-ring extraction on the signal's verbatim to identify
   the specific document/section/statement/token the market is asking for
4. Emit product candidate: `{signal_id, parts_bin: [component_ids],
   ccp_rings: {...}, target_avatar: <one>}`

**Two outputs:**
- Gap Bridge Matrix row update (for the Sovereign's read)
- Product candidate JSON at `context_vault/intelligence/candidates/<id>.json`

**Parts Bin query:**
```python
def parts_for(domain, ring):
    components = capability_index.get(domain, [])
    return [c for c in components
            if c.version.major >= 1
            and c.amendment_compliance == "COMPLIANT"
            and ring in c.ccp_applicable_rings]
```

**Current status:** Gap Bridge Matrix exists (D-0001). Parts Bin
Inventory doesn't exist as a separate matrix yet — Stage-B build.

---

## Prover — MiroFish Simulation Engine (4-Cycle)

**What it does:** Pushes every product candidate through four cycles
before allowing it to reach Implantation.

**Cycle 1 — Narrative Validation:**
- 100 virtual buyers, 5 personas × 20 each
- Each buyer receives the listing copy + the product's CCP rings
- Buyer emits an "emotional resonance" score (1–10) based on whether
  the copy matches the pain-language signal that spawned the candidate
- Aggregate score < 7 → REVISE (Content Lab rewrite)

**Cycle 2 — Environmental Diagnostics:**
- Dependency Ledger (`GT-001` through `GT-010`) enumerates the 10
  Hard Truth footguns: path mixing, Docker down, missing env vars, etc.
- For each GT, MiroFish simulates a buyer encountering it during setup
- Products without recovery paths fail → REVISE (generate Bridge Tool)

**Cycle 3 — Prescription:**
- For every GT that failed in Cycle 2, Claude Code (via SCC TAOR)
  generates a Bridge Tool: an auto-installer, setup script, or FAQ
  entry
- Tools are added to the product bundle AND flushed back to the
  internal vault as hardening

**Cycle 4 — Improvement Flush:**
- Cycle 3's Bridge Tools become new components in the Parts Bin
- Tagged `origin=marketplace_feedback`
- Next Synthesis pass can reuse them in future products
- This is the **flywheel** — the marketplace teaches the internal system

**Outputs:**
- `context_vault/simulation/run_registry.json` — one row per run with
  cycle scores + bridge-tool paths + verdict
- `sovereign.approval.requested` event with payload (Pricing Review gate)

**Pass criterion:** all 4 cycles complete + Cycle 1 score ≥ 7 +
Cycle 2 failure count ≤ 1 (or all Cycle 2 failures have Cycle 3 bridges).

**Current status:** Stage-1 kernel exists. 4-Cycle orchestrator +
Dependency Ledger are Stage-A builds.

---

## Deployer — Playwright / Gumroad API

**What it does:** Lists the product on Gumroad (and Lemon Squeezy, and
Etsy for digital-physical hybrid products), uploads assets, sets price,
publishes.

**Primary path — API:**
- Gumroad v2 API: POST `/products` with title, price, description, files
- Lemon Squeezy API: similar shape
- Etsy requires OAuth 1.0a + a live listing fee

**Fallback path — Playwright:**
- When API is missing a feature (Gumroad's rich-text description uses
  ProseMirror, which the API can't accept cleanly)
- BrowserUse arm with `browser_use.headed` for observability + the
  `execCommand("insertText")` shim to bypass ProseMirror pasting
  restrictions
- Session state: stored via Session Keeper (CC-OP-002)

**Gate:** Copy Approval (Sovereign reviews the listing text once before
publish; subsequent identical-structure listings use the approved
template).

**Outputs:**
- `product.shelf.implanted` event
- `context_vault/products/catalog.json` row

**Current status:** LinkedIn Publisher (different but similar pattern)
exists. Gumroad + Lemon Squeezy clients are Stage-C builds (CC-OP-001).

---

## Steward — Supervisory Monitor + 31-Touchpoint Journey

**What it does:** Treats every buyer of a product as a client with a
state machine that advances through the 31 touchpoints of the Consumer
Journey Map. Detects stalls, at-risk patterns, and advocacy openings.

**State machine per client:**
- LEAD → DISCOVERY → PROPOSAL → ACTIVE → RETAINED (or LAPSED / CHURNED)
- Per-archetype SLA (LuLu archetype has 2× the default SLA; growth-hacker archetype has 0.5×)
- Days in stage > SLA → `client.stage.stalled` event

**Touchpoint layers (13 per touchpoint):**
identity, intent, data capture, classification, scoring, routing,
delivery, feedback, learning, steward signal, measurement, continuity,
reactivation.

**Health scoring (0-100, composite):**
```
score = 0.40 × recency
      + 0.25 × stage_velocity
      + 0.20 × engagement
      + 0.15 × sentiment
```
Score < 40 + 7d decline > 15 → `client.health.at_risk`.

**Outputs:**
- Per-client state files: `context_vault/clients/<id>.json`
- Health history: `context_vault/clients/<id>_health.jsonl`
- Rollup registry: `context_vault/ops/client_registry.json`

**Current status:** Supervisory Monitor + Client Health Scoring +
Talking Point Cards + Friday Client Briefing all exist (BUILDs
100–103). The rollup `client_registry.json` writer is a small add-on.

---

## Cross-cutting — Reward Bus

Every component emits outcomes to the Reward Bus. The bus is the
organism's nervous system for learning.

**Signal types (27 total):**
- product.conversion.delta (T+24h vs T+48h)
- client.stage.advanced
- fotw.signal.acted_upon
- bridge_tool.reused (from Cycle 4 flush → future product)
- … (full list at `context_vault/rewards/signal_types.json`)

**At T+90d, Reward Bus scores the outcome for every decision made
during that window. Scores flow into QLoRA training targets.**

---

## Cross-cutting — Governance Gates

Three gates apply per artifact:

1. **Anti-truncation** — six-field integrity check (`TTLG_ANTI_TRUNCATION_CONTRACT_v1.md`)
2. **Deletion gate** — no destructive action without Sovereign approval
3. **Article XIV path discipline** — WSL-canonical paths only

Any gate fail → component doesn't register. REVISE directive emitted
automatically.

---

## Component-by-component status (current registry)

| Component | Role | Status | Registry entry |
|---|---|---|---|
| FOTW sensors | Listener | Partial — Reddit done, others stubbed | E-0153, E-0154, sensor scaffolds registered |
| SQLite buffer | Gatekeeper | Not built | — |
| Gap Bridge Matrix | Synthesizer | Done | D-0001 |
| Parts Bin Inventory | Synthesizer | Not built | — |
| MiroFish Stage-1 | Prover | Done | E-0187 |
| MiroFish 4-Cycle | Prover | Not built | — |
| Gumroad client | Deployer | Not built | — |
| Session Keeper | Deployer | Not built | — |
| Echolocation agent | Deployer | Not built | — |
| Supervisory Monitor | Steward | Done | E-0222+ |
| Client Health Scoring | Steward | Done | — |
| Friday Client Briefing | Steward | Done | — |
| Signal Registry | cross | Not built | — |
| Pipeline Stage Matrix | cross | Not built | — |
| Product Catalog | cross | Not built | — |
| Client Registry rollup | cross | Not built | — |

**Immediate Forge Directive queue:** CC-OP-001 → CC-OP-005, plus
Stage-A MiroFish 4-Cycle, plus the 6 registry/matrix writers.

---

**See also:**
- `EPOS_UNIFIED_REGISTRY_DOCTRINE_20260423.md` — strategic overview
- `EPOS_SIGNAL_TO_SHELF_PIPELINE.md` — implementation plan
- `GAP_BRIDGE_MATRIX.md`
- `COUNCIL_CHARTER_v1.md`
