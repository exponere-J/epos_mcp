# ARTICLE XIV: ENFORCEMENT OF IMAGINATIVE PROJECTION

**Constitutional Amendment to EPOS_CONSTITUTION_v3.1.md**

---

## ARTICLE XIV: CODE MUST PROVE INTENT

### Section I: The Principle

> No code submission shall be merged or executed without demonstrating the Imaginative Projection Protocol (IPP). Code without proof of pre-mortem analysis is a governance violation and will be rejected at Phase 3 (Governance Gate).

### Section II: Definition of "Code Proves Intent"

A code submission "proves intent" when it includes:

1. **Alignment Assertion header** (IPP Step 6 documented in file)
   - Mandatory in every function, script, or module
   - Must list all touchpoints (what files does it read/write/call?)
   - Must trace 3+ failure chains (if X breaks, what downstream breaks?)
   - Must verify dependencies (what am I assuming?)
   - Must project failure modes (show 3 disaster scenarios)
   - Must prove constitutional alignment (which Articles are satisfied?)

2. **Explicit failure handling** (no silent failures, ever)
   - Every try-except block has a log statement
   - Every API call has timeout + retry logic
   - Every file write validates permissions before proceeding
   - Every parse operation validates schema before accepting input
   - No function returns "success" without confirming actual execution

3. **Immutable audit trail** (every decision logged)
   - All decisions logged to `logs/ttlg_diagnostics.jsonl`
   - Log entries are appended, never modified
   - Log entry includes: timestamp, phase, actor, decision, status, error (if any)

### Section III: Enforcement Mechanism

**Phase 3 (Governance Gate) Validation:**

When Claude Code submits code for Phase 3 approval:

1. **Check 1: Alignment Assertion Present**
   ```
   IF code header does NOT include "ALIGNMENT ASSERTION (IPP Step 6)"
     THEN: REJECT. Ask Claude Code to add IPP analysis.
   ```

2. **Check 2: All 6 IPP Steps Documented**
   ```
   IF any of the 6 steps is missing or incomplete
     THEN: REJECT. Request complete IPP analysis.
   ```

3. **Check 3: Failure Handling Explicit**
   ```
   IF code contains try-except without log
     OR API call without timeout
     OR file write without permission check
     THEN: REJECT. Request explicit error handling.
   ```

4. **Check 4: Constitutional Alignment Proven**
   ```
   IF code cannot be mapped to at least 3 Articles
     THEN: REJECT. Code may violate governance.
   ```

5. **Check 5: Audit Trail Complete**
   ```
   IF code would execute without logging to JSONL
     THEN: REJECT. Silent operations forbidden.
   ```

**If all 5 checks pass:** Code is approved for Phase 4 (Reconfigure/Implementation).

---

## ARTICLE XIV: ENFORCEMENT OF PARITY

### Section IV: Documentation Without Implementation = Violation

> If a code submission documents a function, diagnostic phase, or process, it MUST include the enforcement code (e.g., script, validation, logging) that actually executes it. Documentation alone is insufficient.

**Examples:**

| Violation | Fix |
|-----------|-----|
| Documented "Phase 1 Scout" but no `ttlg_systems_light_scout.py` | Submit both doc + implementation |
| Documented "error handling" but no try-except in code | Add explicit exception handling |
| Documented "immutable logs" but no JSONL append logic | Implement `validated_write()` function |
| Documented "timeout protection" but no timeout in API call | Add `timeout=60` to all litellm calls |

**Enforcement:** If Phase 3 Governance Gate finds documentation without implementation, the code is rejected and must be resubmitted with both.

---

## ARTICLE XIV: MONO-SOVEREIGNTY (Model Purity)

### Section V: Mandatory Gemini-Only for TTLG Diagnostics

> All TTLG diagnostic phases (Phase 1 Scout, Phase 2 Thinker, Phase 5 Analyst, etc.) must use exclusively Google Gemini models via OpenRouter. Any request to use alternative models (e.g., Claude Sonnet, Mistral, Llama) for internal diagnostics is a violation of this Article and will be rejected.

**Specific Rules:**

1. **Phase 1 Scout:** MUST use `google/gemini-2.5-flash:free`
2. **Phase 2 Thinker:** MUST use `google/gemini-3.1-pro-preview:free`
3. **Phase 5 Analyst:** MUST use `google/gemini-2.5-flash:free`
4. **Nervous System:** MUST use `google/gemma-3-27b-it:free`
5. **Friday Orchestrator:** MUST use Gemini models from `.env`

**Model IDs are non-negotiable.** All must be sourced from `.env` and validated against the list above.

**Why Mono-Sovereignty?**
- Single provider = simpler governance
- Gemini family = consistent behavior across phases
- OpenRouter = unified API endpoint (no proxy needed)
- Prevents vendor switching mid-execution (which breaks Phase 3 reproducibility)

**Enforcement:** If code hardcodes a different model or requests to use Claude for diagnostics, Phase 3 rejects it with: "Mono-Sovereignty violation. TTLG diagnostics must use Google Gemini models only."

---

## ARTICLE XIV: COMPLIANCE AUDIT

### Section VI: Self-Audit Checklist for Claude Code

Before submitting any code, Claude Code must complete this checklist:

```
ARTICLE XIV COMPLIANCE CHECKLIST
=================================

Code Proves Intent:
☐ Alignment Assertion header present
☐ IPP Step 1 (Touchpoints) documented
☐ IPP Step 2 (Failure chains) documented with 3+ scenarios
☐ IPP Step 3 (Dependencies) verified
☐ IPP Step 4 (Failure modes) projected
☐ IPP Step 5 (Constitutional alignment) mapped to ≥3 Articles
☐ IPP Step 6 (Proof) demonstrated

Explicit Failure Handling:
☐ No silent failures (all paths logged)
☐ All try-except blocks have log statements
☐ All API calls have timeout + retry
☐ All file writes validated before proceeding
☐ All JSON/schema parsing validated before accepting
☐ All errors exit with non-zero code

Immutable Audit Trail:
☐ Every decision logged to logs/ttlg_diagnostics.jsonl
☐ Log entries append-only (never modified)
☐ Log format: {"phase": X, "stage": Y, "status": Z, ...}

Documentation = Implementation:
☐ If function documented, it is implemented
☐ If phase documented, it has execution code
☐ If error handling documented, it is in try-except
☐ If logging promised, it is in the code

Mono-Sovereignty (Models):
☐ No hardcoded model IDs
☐ All models read from .env
☐ All models are Google Gemini (not Claude/Mistral/Llama)
☐ Model IDs match TTLG_*_MODEL_* convention

RESULT: All ☐ checked = Ready for Phase 3. Any unchecked = Incomplete.
```

---

## ARTICLE XIV: AMENDMENT HISTORY

| Date | Version | Change | Authority |
|------|---------|--------|-----------|
| 2026-02-28 | 1.0 | Initial ratification | Jamie Lawson |
| — | — | — | — |

---

## ARTICLE XIV: AUTHORITY & RATIFICATION

**Ratified by:** Jamie Lawson, EPOS Steward  
**Effective date:** 2026-02-28  
**Scope:** All code submissions to EPOS via Claude Code  
**Override authority:** Jamie Lawson only (with explicit written exception)  
**Review cycle:** Quarterly (or when governance violations occur)

---

## HOW THIS WORKS IN PRACTICE

### Example: Claude Code submits Phase 1 Scout implementation

```python
"""
ALIGNMENT ASSERTION (IPP Step 6):
==================================

STEP 1 - TOUCHPOINTS:
- Read: .env (TTLG_SCOUT_MODEL_SYSTEMS, OPENROUTER_API_KEY)
- Read: CLAUDE.md (Scout role definition)
- Call: tools.litellm_client.run_model()
- Write: context_vault/scans/{scan_id}/scout_output.json
- Write: logs/ttlg_diagnostics.jsonl

STEP 2 - FAILURE CHAINS:
- API timeout → logs error → exits 1 → Phase 2 sees missing scan
- Disk full → logs error → exits 1 → Phase 2 waits for retry
- Malformed JSON → validated + rejected → logs schema error → exits 1

STEP 3 - DEPENDENCIES:
- .env readable: checked with try-except
- OPENROUTER_API_KEY set: checked before API call
- context_vault/ writable: checked with test write
- Gemini reachable: timeout + retry on timeout

STEP 4 - FAILURE SCENARIOS:
- Timeout: API doesn't respond in 60s → logs timeout → user retries
- Disk full: Write fails → logs error → user frees space → retries
- Network error: Response corrupted → schema validation catches → logs corruption

STEP 5 - CONSTITUTIONAL:
- Article II (No silent failures): ✅ All errors logged
- Article III (Sovereignty): ✅ Uses local context_vault
- Article V (Transparency): ✅ Every decision in audit trail
- Article VII (Gated autonomy): ✅ Respects Phase 3 gate
- Article XIV (Code proves intent): ✅ This header proves it

STEP 6 - PROOF:
This function:
✅ Reads all config before execution (fail if missing)
✅ Validates schema before accepting model response
✅ Logs all outcomes to immutable JSONL
✅ Handles all 3+ failure modes explicitly
✅ Returns structured JSON with status field
✅ Never silently succeeds or fails
"""

def ttlg_systems_light_scout(targets: str, scan_id: str, intensity: str, timeout_minutes: int):
    # Implementation here (with all Article XIV checks built in)
    pass
```

**Phase 3 Governance Gate Review:**

```
Checklist:
✅ Alignment Assertion present
✅ All 6 IPP Steps documented
✅ Failure handling explicit (3+ scenarios)
✅ Constitutional alignment proven (5 Articles)
✅ Audit trail enabled (JSONL logging)
✅ Mono-sovereignty enforced (Gemini models only)

DECISION: APPROVED. Proceed to Phase 4 (Claude Code execution).
```

---

## NEXT STEPS

1. **Jamie ratifies Article XIV** (this document)
2. **Claude Code reads this document** (before submitting code)
3. **Claude Code includes Alignment Assertion** in all submissions
4. **Phase 3 Governance Gate validates** using the checklist
5. **Only approved code** proceeds to Phase 4

---

**Status:** 🟢 ARTICLE XIV READY FOR RATIFICATION

This is the mechanism that prevents rework by forcing imaginative projection *before* code is written, not after it fails.

