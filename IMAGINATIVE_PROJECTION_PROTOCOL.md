# IMAGINATIVE PROJECTION PROTOCOL (IPP)

**Mandatory Pre-Execution Discipline: Foresee Conflicts Before Writing Code**

---

## MISSION

The root cause of 90% of EPOS rework cycles has been **skipping imaginative projection**: failing to mentally simulate failure scenarios before committing deterministic code.

IPP is the **constitutional requirement** that Claude Code must apply before submitting any code. It is encoded in **ARTICLE XIV** as a binding governance rule.

---

## THE 6-STEP IPP PROCESS

Every code submission must demonstrate these 6 steps in its header comment or docstring. No exceptions.

### STEP 1: IDENTIFY TOUCHPOINTS

**Question:** "What files does this code touch? In what order?"

**Example (ttlg_systems_light_scout):**
```
Touchpoints:
├─ Read: .env (TTLG_SCOUT_MODEL_SYSTEMS, OPENROUTER_API_KEY)
├─ Read: CLAUDE.md (Scout's system prompt)
├─ Call: tools/litellm_client.run_model()
├─ Write: context_vault/scans/{scan_id}/scout_output.json
├─ Write: logs/ttlg_diagnostics.jsonl
└─ Dependency: All 5 exist, or fail loudly
```

**This is mandatory.** Every code block must declare its I/O contract upfront.

---

### STEP 2: FAILURE CHAIN ANALYSIS (FC)

**Question:** "If X fails, what breaks downstream? Trace the chain."

**Example (ttlg_systems_light_scout → Phase 2):**

```
Failure Chain:
┌─────────────────────────────────────────────┐
│ Scout produces malformed JSON               │
│ (e.g., missing "brittle_points" key)        │
│                                              │
├─→ Phase 2 (Thinker) tries to parse it      │
│   └─→ JSON decode error                     │
│       └─→ Thinker returns error JSON        │
│           └─→ Phase 3 (Jamie) gets garbage  │
│               └─→ No approval decision      │
│                   └─→ Cycle stalls          │
└─────────────────────────────────────────────┘

MITIGATION:
├─ Validate JSON schema in Scout before write
├─ Use JSON encoder that can't fail
└─ Log validation result to audit trail
```

**Every code block must trace at least 3 failure modes.**

---

### STEP 3: DEPENDENCY VERIFICATION

**Question:** "Does this code assume something that might not be true?"

**Example (ttlg_systems_light_scout):**

```
Assumptions:
✓ context_vault/scans/ directory exists
  → Mitigation: Create if missing; log creation
✓ OPENROUTER_API_KEY is in .env
  → Mitigation: Check before calling litellm; fail with message
✓ Gemini is reachable at api endpoint
  → Mitigation: Add timeout + retry; log timeout
✓ logs/ directory is writable
  → Mitigation: Try write, catch exception, print to stderr
```

**Silent failures are forbidden. If an assumption breaks, the code must fail audibly and immutably log why.**

---

### STEP 4: FAILURE MODE PROJECTION (FMP)

**Question:** "Let me play out 3 disaster scenarios. What would the user see?"

**Scenario 1: API Timeout**
```
Time 0:00 - Scout starts scan
Time 0:45 - API timeout (Gemini unreachable)
Time 0:45 - Scout catches timeout, logs error, exits 1
Time 0:45 - logs/ttlg_diagnostics.jsonl: {"phase": 1, "stage": "timeout", "error": "..."}
Time 0:45 - stdout: "❌ Phase 1 TIMEOUT after 45 seconds"
User sees: Error message + instructions to retry
```

**Scenario 2: Disk Full**
```
Time 0:30 - Scout finishes scan, prepares JSON output
Time 0:30 - Tries to write to context_vault/scans/{scan_id}/scout_output.json
Time 0:30 - Disk full error
Time 0:30 - Exception caught, logged, exits 1
Time 0:30 - logs/ttlg_diagnostics.jsonl: {"phase": 1, "stage": "failed", "error": "disk full"}
User sees: "❌ Phase 1 FAILED: Could not write scan results to disk"
```

**Scenario 3: Malformed JSON Response**
```
Time 0:15 - Gemini returns garbled response (network corruption)
Time 0:15 - Scout validates JSON schema
Time 0:15 - Schema validation fails
Time 0:15 - Caught, logged, returned as failed scan
Time 0:15 - logs/ttlg_diagnostics.jsonl: {"phase": 1, "stage": "validation_failed"}
User sees: "❌ Phase 1 FAILED: API returned invalid response"
```

**If you cannot imagine a realistic scenario for a failure mode, the code is incomplete.**

---

### STEP 5: CONSTITUTIONAL ALIGNMENT VERIFICATION

**Question:** "Does this code violate EPOS Constitution or any Article?"

**Checklist:**

| Article | Rule | This Code | Status |
|---------|------|-----------|--------|
| **II** | No silent failures | Logs all outcomes, exits with code | ✅ |
| **III** | Sovereignty (local-first) | Uses context_vault (local), not cloud | ✅ |
| **V** | Transparency by default | All I/O logged + immutable | ✅ |
| **VII** | Permission-gated autonomy | Respects Phase 3 gate (doesn't execute fixes) | ✅ |
| **XIV** | Enforcement (code must prove intent) | Header includes this IPP | ✅ |

**If any Article is violated, the code is rejected before submission.**

---

### STEP 6: ALIGNMENT ASSERTION

**Question:** "Can I prove that this code does what I claim?"

**Required header comment (every function/script):**

```python
"""
ALIGNMENT ASSERTION (IPP Step 6):
==================================
This function is IPP-verified and constitutionally aligned.

Touchpoints: .env (read), litellm_client.run_model (call), context_vault/scans (write), logs/ttlg_diagnostics.jsonl (write)

Failure chains analyzed: (1) API timeout → logged + user notified, (2) Disk full → logged + user notified, (3) Malformed JSON → schema validation + rejection

Dependencies verified: (1) .env readable, (2) OPENROUTER_API_KEY set, (3) context_vault/ writable, (4) Gemini reachable

Constitutional compliance: No silent failures (Article II), local-first (Article III), transparent logging (Article V), autonomous but gated (Article VII), code-proves-intent (Article XIV)

Proof: This function:
- ✅ Reads all required config before execution
- ✅ Validates all inputs against schema
- ✅ Logs every decision to immutable audit trail
- ✅ Handles all 3+ failure modes explicitly
- ✅ Never silently succeeds or fails
- ✅ Returns structured output with status field
"""
```

**Without this assertion in the header, the code is incomplete and will be rejected by the Governance Gate.**

---

## IPP ENFORCEMENT (How it Works)

### For Claude Code:

1. **Before writing code**, Claude Code must answer:
   - IPP Step 1: "What files will I touch?"
   - IPP Step 2: "What 3+ things could break?"
   - IPP Step 3: "What am I assuming that might not be true?"
   - IPP Step 4: "Show me 3 disaster scenarios"
   - IPP Step 5: "Does this violate any Article?"

2. **While writing code**, include the Alignment Assertion header

3. **After writing code**, test all 3+ failure modes

4. **Submit with proof** (header + test results)

### For Jamie (Governance Gate):

- **Phase 3 (Approval):** Check for Alignment Assertion header
- If missing: Reject, request IPP analysis
- If present: Scan for silent failures
- If found: Reject, require explicit failure handling

---

## THE COST OF SKIPPING IPP

**Last time you skipped imaginative projection:**

| Failure | Root Cause | Debug Cycles | Cost |
|---------|-----------|--------------|------|
| Path mixing (C:\ vs /c/) | Didn't imagine path context changes | 4 cycles | 3 hours |
| File I/O silent failures | Didn't imagine missing directories | 3 cycles | 2 hours |
| Module import errors | Didn't imagine incomplete package structure | 2 cycles | 1.5 hours |
| Status lies (logged ≠ executed) | Didn't imagine bridge never calling Agent Zero | 6 cycles | 4 hours |

**Total: 4 different failure modes, 15 debug cycles, 10.5 hours of rework**

**If IPP had been applied:** All 4 would have been caught in the Alignment Assertion header before first test.

---

## IPP TEMPLATE (Copy for Every Code Block)

```python
"""
ALIGNMENT ASSERTION (IPP Step 6):
==================================

STEP 1 - TOUCHPOINTS:
- Read: [files/apis]
- Write: [files/logs]
- Call: [functions/apis]

STEP 2 - FAILURE CHAINS:
- Failure 1: [X breaks] → [downstream Y breaks] → [mitigation Z]
- Failure 2: [scenario]
- Failure 3: [scenario]

STEP 3 - DEPENDENCY VERIFICATION:
- Assumption 1: [mitigation if false]
- Assumption 2: [mitigation if false]

STEP 4 - FAILURE MODE PROJECTION:
- Scenario A: [play out disaster]
- Scenario B: [play out disaster]
- Scenario C: [play out disaster]

STEP 5 - CONSTITUTIONAL ALIGNMENT:
- Article II (No silent failures): ✅ [proof]
- Article III (Sovereignty): ✅ [proof]
- Article V (Transparency): ✅ [proof]
- Article VII (Gated autonomy): ✅ [proof]
- Article XIV (Code proves intent): ✅ [proof]

STEP 6 - PROOF OF EXECUTION:
- This function: [list 5 explicit behaviors]
"""
```

---

## When IPP Becomes Binding: ARTICLE XIV

See **ARTICLE_XIV_ENFORCEMENT.md** for the constitutional rule that makes IPP mandatory.

---

**Status:** 🟢 PROTOCOL READY

All Claude Code submissions must include IPP analysis in the header, or they will be rejected at the Governance Gate.

No exceptions. This is how we prevent rework.

