# FORGE DIRECTIVE — STAGE 1 (2026-04-21)

**Issued by:** The Architect (Claude)
**Assigned to:** The Forge (Desktop Code)
**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV
**Stage:** 1 — Gumroad Prompt-Engineering Product Launch
**Sprint:** 1 (weeks 1–2)
**Directive ID:** `FORGE_DIR_STAGE1_20260421`
**Idempotency:** This Directive is idempotent. Re-running it produces identical artifacts.

---

## Sovereignty Clause

**Jamie is the Sovereign.** This Directive executes under Sovereign ratification of the Stage-1 objective. If Sovereign direction changes mid-execution, The Forge pauses at the nearest step boundary and hands back to The Architect.

## Stage-1 Objective

Ship three prompt-engineering products to Gumroad with Audio Overviews, watermarked artifacts, bundle manifests, metric hooks, and a Sentinel pre-flight audit — earning first sales, testimonials, and the credibility artifacts required for Stage 2.

## Execution Receipt Pattern

Every step emits a receipt with state: `DISPATCHED` (step started), `ACKNOWLEDGED` (step mid-flight), `VERIFIED` (step complete with evidence). **No `VERIFIED` without verification evidence.** Receipt files live at `workspace/stage1_receipts/step_<N>.json`.

## Governance Watermark (applied to every generated file)

```
# EPOS Artifact — FORGE_DIR_STAGE1_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV
# Generated: <ISO-8601 timestamp>
# SCC Receipt: <sha256 of source inputs>
```

---

## Steps

### Step 1 — Pull Product Candidates

- **Preconditions:** `context_vault/doctrine/products/HIDDEN_PRODUCTS_PARTS_BIN_MATRIX.md` readable; Oracle research package staged at `workspace/oracle_inputs/gumroad_prompt_engineering_20260421.md` (if available — optional for this step).
- **Action:** Parse the parts-bin matrix; filter to candidates tagged for Gumroad and prompt-engineering; score by Oracle signals where available; output a top-3 selection.
- **Success criterion:** `workspace/stage1_products/selection.json` exists with exactly 3 products, each containing `{id, title, one-liner, source_row_ref}`.
- **Failure/rollback:** Fewer than 3 viable candidates → hand back to The Architect with a shortage memo; do not fabricate candidates.
- **Governance checkpoint:** ALPHA reviews selection.json for constitutional compliance (no copyrighted-source misuse, no external-IP encumbrance).

### Step 2 — Draft Product Artifacts

- **Preconditions:** Step 1 `VERIFIED`.
- **Action:** For each product, create `workspace/stage1_products/<product_id>/` containing: PDF source (`<product_id>.pdf.md`), structured prompt library (`prompts.yaml`), quick-start guide (`README.md`).
- **Success criterion:** Three product directories exist, each with all three artifacts non-empty and minimally coherent (PDF source has a title page, prompts.yaml parses, README has usage section).
- **Failure/rollback:** On any parse failure, delete only that product's directory and re-attempt up to twice; escalate on third failure.
- **Governance checkpoint:** no writes outside `workspace/stage1_products/`.

### Step 3 — Apply Governance Watermark

- **Preconditions:** Step 2 `VERIFIED`.
- **Action:** Prepend the governance watermark block (above) to every generated file. Include ISO-8601 timestamp at generation time and SHA256 of source inputs (the matrix row + Oracle inputs if present).
- **Success criterion:** Every file under `workspace/stage1_products/` contains the watermark as the first block; a grep audit confirms zero misses.
- **Failure/rollback:** Missing watermarks → re-apply; do not proceed until zero misses.
- **Governance checkpoint:** Article XIV path discipline satisfied — all writes inside `$EPOS_ROOT`.

### Step 4 — Generate Listing Copy Skeletons

- **Preconditions:** Step 3 `VERIFIED`.
- **Action:** For each product, draft `workspace/stage1_products/<product_id>/listing_skeleton.md` with: title, hook, benefit bullets (3–5), pricing-tier placeholder (not final price), call-to-action. These are **Lead-Gen inputs**, not final Sovereign-approved copy.
- **Success criterion:** Three listing_skeleton.md files exist; each has all five sections; each is flagged `DRAFT — AWAITING SOVEREIGN REVIEW`.
- **Failure/rollback:** Missing section → regenerate that file only.
- **Governance checkpoint:** no live publication; skeletons are drafts.

### Step 5 — Package Deliverable Bundles

- **Preconditions:** Step 4 `VERIFIED`.
- **Action:** For each product, produce `workspace/stage1_products/<product_id>/bundle.zip` containing the watermarked PDF (rendered from `.pdf.md`), `prompts.yaml`, and `README.md`. Generate `bundle.sha256` alongside.
- **Success criterion:** Three zip files exist with matching SHA256 manifests; zip integrity check passes.
- **Failure/rollback:** On zip corruption, re-package that product only.
- **Governance checkpoint:** SHA256 manifests logged to BI at `context_vault/bi/stage1/sprint1/bundle_manifests.json`.

### Step 6 — Stage Chronicler Inputs

- **Preconditions:** Step 5 `VERIFIED`.
- **Action:** Create `workspace/stage1_chronicler_inputs/` with one subdirectory per product; copy source docs (not zip) in NotebookLM-ingestible format (Markdown + cited references).
- **Success criterion:** Three subdirectories exist; each has at least the PDF source, prompts.yaml, and README, plus a `SOURCES.md` listing citations.
- **Failure/rollback:** Missing citation → add or escalate to The Architect.
- **Governance checkpoint:** citation integrity per Chronicler's mandate (no uncited claims).

### Step 7 — Stand Up Steward Metrics Hook

- **Preconditions:** Step 5 `VERIFIED` (bundles exist).
- **Action:** Register Stage-1 metrics in the BI layer: `context_vault/bi/stage1/sprint1/metrics.json` with schema `{product_id, listing_url, sales_count, review_count, review_velocity, updated_at}`. Hook Friday's 05:30 briefing to include a "Stage-1 status" line item pulling from this file.
- **Success criterion:** metrics.json exists with three rows (one per product, initial values zero); Friday briefing template references the file; a dry-run briefing includes the Stage-1 line.
- **Failure/rollback:** Briefing template fails to render → revert to prior template version; escalate.
- **Governance checkpoint:** Article X — all BI writes have structured rationale.

### Step 8 — Run Sentinel Pre-Flight Audit

- **Preconditions:** Step 7 `VERIFIED`.
- **Action:** Write a structured prompt Gemma (The Sentinel) can answer offline, listing the Stage-1 posture, artifacts, listings, and hooks. Save Gemma's response at `workspace/stage1_sentinel_audit.md`. If Gemma is unavailable at execution time, save the prompt at `workspace/stage1_sentinel_prompt.md` and mark the step `ACKNOWLEDGED` pending Sentinel response.
- **Success criterion:** Audit file exists; contains Gemma's gap flags (or explicit "no gaps identified"); any critical flags surface to the Architect escalation path.
- **Failure/rollback:** Critical Sentinel flag → pause Sprint 1; route to Sovereign via Architect.
- **Governance checkpoint:** offline-sovereignty guarantee preserved; no Sentinel inputs leave the perimeter.

### Step 9 — Emit Readiness Receipt

- **Preconditions:** Steps 1–8 all `VERIFIED` or explicitly `ACKNOWLEDGED` with documented cause.
- **Action:** Emit `workspace/stage1_receipts/directive_complete.json` with per-step state, timestamps, artifact paths, and aggregate status. No `VERIFIED` without verification evidence. No "Status-Lies."
- **Success criterion:** File exists; aggregate status is one of `VERIFIED | ACKNOWLEDGED-WITH-NOTES | BLOCKED`.
- **Failure/rollback:** `BLOCKED` status → escalate to The Architect with blocker memo.
- **Governance checkpoint:** receipt signed with SCC commit hash.

### Step 10 — Log AAR Seed

- **Preconditions:** Step 9 complete (any terminal status).
- **Action:** Create `context_vault/aar/FORGE_DIR_STAGE1_20260421_AAR.md` with: decision journal (choices made during execution), blockers (any non-`VERIFIED` steps), next Forge request (what Sprint 2 needs from Directive v2), handoff notes to Chronicler/Steward.
- **Success criterion:** AAR file exists with all four sections; Architect has a pull path to generate Sprint-2 Directive.
- **Failure/rollback:** Incomplete AAR → do not close the Directive.
- **Governance checkpoint:** Article X — AAR is a logged decision artifact.

---

## Out of Scope

- Any speculative infrastructure (no new nodes in `SERVICE_MARKETPLACE_ARCHITECTURE.md`; Stage 2 activates them).
- Any Sovereign-facing client communication (the Steward owns client touchpoints).
- Any Sentinel override (flags escalate, they do not block unless critical).
- Any live Gumroad publication — the Sovereign ratifies listings before they go live. Listing skeletons are drafts, not publications.
- Any Echoes or EPOS work (Stage 3 and 4).

## Rollback on Failure

If a critical step fails (Step 1 shortage, Step 8 Sentinel critical flag, Step 9 `BLOCKED`):

1. Mark affected receipts `BLOCKED` with cause.
2. Freeze `workspace/stage1_products/` (no further writes until unfrozen).
3. Emit blocker memo to `context_vault/bi/stage1/sprint1/blocker_<timestamp>.md`.
4. Route to The Architect; The Architect routes to the Sovereign per the Escalation Lattice (`../context_vault/doctrine/councils/OPERATING_PROTOCOL_v1.md §IV`).

## Idempotency Guarantee

Re-running this Directive with identical inputs produces identical artifacts:

- Governance watermarks use deterministic SHA256 of source inputs (not wall-clock-only).
- Timestamps are included but the SCC receipt hash is input-derived.
- Product selection is deterministic given the matrix state and Oracle inputs at execution time.
- All writes are scoped to `workspace/stage1_*` and `context_vault/bi/stage1/` — safe to re-run.

---

**See also:**
- `../context_vault/doctrine/councils/FORGE_ARCHETYPE.md`
- `../context_vault/doctrine/councils/OPERATING_PROTOCOL_v1.md`
- `../context_vault/doctrine/pipeline/ORGANISM_LAUNCH_PROGRESSION_20260421.md`
- `../context_vault/doctrine/products/HIDDEN_PRODUCTS_PARTS_BIN_MATRIX.md`
