# AAR TEMPLATE — AFTER-ACTION REVIEW
**Learning Capture & Pattern Extraction for Friday's Memory**

**Authority:** EPOS_CONSTITUTION_v3.1.md Article XII (Agent Memory Sovereignty), FRIDAY_LEARNING_FRAMEWORK.md

---

## Preamble

An **After-Action Review** is generated **immediately after a code fix is deployed and tested**. It captures:

1. **What was the problem?** (The brittle point)
2. **How was it fixed?** (The solution)
3. **Did the prediction match reality?** (Validation)
4. **What pattern should Friday remember?** (The learning)
5. **Should this be auto-approved in the future?** (The escalation rule)

This document is read by Friday and ingested into `friday_pattern_library.json`, which grows Friday's ability to **predict and prevent** similar failures.

---

## [A] FIX SUMMARY — What Happened?

### The Brittle Point (The Wound)

```
Description:
[Clear, one-paragraph explanation of the failure that was discovered]

Example:
"Scout failed to write scout_output.json because the parent directory 
context_vault/scans/{scan_id}/ did not exist. The error was silent on 
append mode, only surfaced when Friday tried to read the file."

Discovered By:
[Agent that found it: Claude Code, Friday Health Check, Governance Gate, etc.]

Severity:
[Critical / High / Medium / Low]
- Critical: Breaks the entire loop (Scout fails → FOTW has nothing → Content Lab breaks)
- High: Breaks one phase but others can continue
- Medium: Causes degraded output but doesn't block execution
- Low: Minor efficiency loss or cosmetic issue

Root Cause Category:
[ ] Path/directory issue
[ ] Model routing / environment variable
[ ] Concurrency / file locking
[ ] State synchronization / manifest mismatch
[ ] Schema validation / data format
[ ] Assumption about runtime state
```

### The Healing (The Surgical Intervention)

```
Solution Applied:
[Technical description of what was fixed]

Example:
"Added Path.mkdir(parents=True, exist_ok=True) at Scout startup to ensure 
context_vault/scans/{scan_id}/ exists before any file writes."

Code Change:
[Before and After, or link to commit]

BEFORE:
    with open(f"context_vault/scans/{scan_id}/scout_output.json", "w") as f:
        json.dump(findings, f)

AFTER:
    scan_dir = Path(f"context_vault/scans/{scan_id}")
    scan_dir.mkdir(parents=True, exist_ok=True)
    with open(scan_dir / "scout_output.json", "w") as f:
        json.dump(findings, f)

Files Modified:
- [File paths that were changed]

Constitutional Impact:
✅ Article II (Environment): Still respects POSIX paths
✅ Article VII (Context Vault): Still writes only to deterministic directory
✅ Article XIV (IPP): Mitigates failure scenario "Missing Directory"

Deployment Method:
[How was this deployed? Rolling? Immediate? Staged?]
```

---

## [B] OBSERVED VS. PREDICTED — Validation of Assumptions

### Predicted Outcome (What Claude Code Expected)

```
Hypothesis:
"If we ensure the directory exists at startup, Scout will write scout_output.json 
successfully on all runs."

Confidence Level:
[ ] High (>90%)
[ ] Medium (70-90%)
[ ] Low (<70%)

Reasoning:
"This is a deterministic filesystem operation. Path.mkdir() is idempotent—
calling it on an existing directory succeeds without error. This should 
eliminate the primary failure mode."

Risk Mitigation Planned:
[ ] Retry logic
[ ] Atomic writes with fsync
[ ] Backup file created in alternate location
[X] Validation check: assert scan_dir.exists() after mkdir()
```

### Actual Outcome (What Really Happened)

```
Test Results:
[Description of how this fix was validated]

Example:
"Ran Scout 5 times against EPOS root with targets governance_gate,context_vault. 
All 5 runs produced scout_output.json successfully. FOTW captured ambient context 
without errors. Content Lab synthesized markdown without warnings."

Observations:
[ ] Prediction was correct → no new failure modes emerged
[ ] Prediction was partially correct → new edge case discovered
[ ] Prediction was wrong → failure mode still exists

If Not Exact Match:
"Expected: Directory creation takes <10ms
Actual: First run took 45ms (initial parent dir creation), subsequent runs <5ms
Impact: Negligible for diagnostic cycles, no action needed"

Side Effects:
[Any unintended consequences?]
- [ ] Slowdown in startup time
- [ ] New error messages in logs
- [ ] Dependency on additional libraries
- [ ] Changes to Friday decision-making

VALIDATION: ✅ PASS / ⚠️ PARTIAL / ❌ FAIL
```

---

## [C] PATTERN EXTRACTION — What Should Friday Learn?

### Pattern Name

```
Pattern ID: [e.g., EPOS_PATH_ENSURE_20260311]
Pattern Name: [e.g., "Context Vault Directory Pre-Creation"]
Category: [Initialization / Concurrency / Schema / State Management]

```

### Pattern Description (For Friday's Library)

```
Trigger Condition:
[The exact state/input that causes this pattern to apply]

Example:
"When an agent attempts to write to a subdirectory of context_vault 
that may not have been created in a previous run."

General Form:
"If {condition}, then {action} should be taken to prevent {failure}."

Canonical Solution:
[The general solution, not the specific code]

"Before writing to a file in a nested directory, ensure the parent 
directories exist using atomic mkdir operations with exist_ok=True."

Applicability:
[ ] All agents
[X] Scout and Content Lab (writers)
[ ] FOTW (appenders)
[ ] Friday (state reducer)

Risk of Over-Application:
[Could applying this pattern in the wrong context cause harm?]

"No. mkdir(exist_ok=True) is idempotent. Calling it on every agent 
startup is cheap and safe."

Friday Recommendation:
"This pattern should be included in ALL file-writing startup routines 
across Scout, FOTW, Content Lab, and Friday. It's foundational."
```

### Expected Impact for Future Runs

```
Incidents This Pattern Would Prevent:
1. Scout failures due to missing scan directory
2. FOTW failures due to missing agent_logs directory
3. Content Lab failures due to missing mission_data directory

Estimated Frequency of Prevention:
[Based on observed failure rate]

"This was the 3rd time in 12 runs that the directory-missing issue 
surfaced. Applying this pattern prevents 25% of current Scout failures."

Auto-Approval Criteria (For Friday):
"If a new Scout variant is submitted, and it includes Path.mkdir(parents=True, exist_ok=True)
at startup, Friday can auto-approve this pattern without escalation."
```

---

## [D] PATTERN LIBRARY ENTRY

**This is the JSON entry that Friday will ingest into `friday_pattern_library.json`:**

```json
{
  "pattern_id": "EPOS_PATH_ENSURE_20260311",
  "pattern_name": "Context Vault Directory Pre-Creation",
  "category": "initialization",
  "created_date": "2026-03-11",
  "source_aar": "scout_directory_fix_AAR.md",
  "trigger": {
    "agent": "Scout",
    "condition": "Write to subdirectory of context_vault",
    "symptom": "FileNotFoundError when parent directory missing"
  },
  "solution": {
    "description": "Ensure parent directories exist before writing",
    "code_pattern": "Path(dir).mkdir(parents=True, exist_ok=True)",
    "applies_to": ["Scout", "FOTW", "ContentLab"],
    "risk_level": "none"
  },
  "validation": {
    "test_runs": 5,
    "success_rate": 1.0,
    "incidents_prevented": 3,
    "frequency_in_baseline": "25%"
  },
  "friday_rule": {
    "auto_approve_if": "Code includes Path.mkdir(parents=True, exist_ok=True) before file writes",
    "escalate_if": "Directory creation fails or is missing at startup",
    "confidence": 0.95
  },
  "articles_enforced": ["II", "VII", "XIV"],
  "next_review": "2026-04-11"
}
```

---

## [E] ESCALATION DECISION — Auto-Approve or Manual Review?

### Friday's Decision Criteria

```
Question 1: Is this pattern foundational (applies to many agents)?
Answer: [Yes / No]
→ If Yes: Approve for auto-inclusion in all similar code submissions

Question 2: Does applying this pattern create new failure modes?
Answer: [No new modes identified]
→ If No: Approve for auto-approval

Question 3: Is the fix reversible if it causes unexpected issues?
Answer: [Yes, mkdir is idempotent and safe]
→ If Yes: Approve for fast-track deployment

ESCALATION DECISION: ✅ AUTO-APPROVE
Confidence Level: 95%

This pattern will be added to Friday's memory at priority=HIGH.
Future submissions matching this pattern will be fast-tracked.
```

### Manual Review Triggers

```
Escalate to Claude Code if:
[ ] Pattern applies to <20% of agents (too specific)
[X] Pattern solves a common failure (frequent enough to automate)
[ ] Pattern requires new library dependency
[ ] Pattern introduces new Article XIV considerations

In This Case:
✅ APPROVED FOR AUTO-APPROVAL
No manual review needed unless applied in a novel context.
```

---

## [F] TIMELINE & METADATA

```
Date Fix Identified: 2026-03-11 14:32:00Z
Date Fix Deployed: 2026-03-11 15:10:00Z
Date AAR Completed: 2026-03-11 16:00:00Z

Submitting Agent: Claude Code
Submitting Agent Model: claude-sonnet-4-6
Reviewed By: Friday (Friday Vault Summary Agent)
Approved By: governance_gate_audit.py

Scan ID Associated: scan_20260311_083000
Trace ID: trace-abc123def456

IPP Reference: context_vault/pending_ipp/scan_20260311_083000_IPP.md
Commit Hash (if applicable): [git commit hash]

Friday Ingest Status:
[ ] Pending
[X] Ingested into friday_pattern_library.json
[ ] Added to friday_learning_framework.json
[ ] Training signal recorded
```

---

## [G] NEXT ACTIONS FOR FRIDAY

```
Action 1: Update Pattern Library
→ Add pattern_id: EPOS_PATH_ENSURE_20260311 to friday_pattern_library.json
→ Set auto_approve_if rule for future Scout variants

Action 2: Log Learning
→ Append to friday_learning_framework.json: 
   "Learned: Directory pre-creation prevents 25% of Scout failures"

Action 3: Propagate Pattern
→ Flag all existing Scout, FOTW, ContentLab submissions to check if they 
  include Path.mkdir() at startup
→ Recommend retrofit if missing

Action 4: Set Review Timer
→ Schedule next review of this pattern on 2026-04-11
→ Check if actual prevention rate matches predicted 25%

Action 5: Confidence Update
→ Increase Friday's confidence in path-handling patterns from 0.80 → 0.95
```

---

## References

- **IPP_TEMPLATE.md** — Pre-mortem discipline that led to this fix
- **FRIDAY_LEARNING_FRAMEWORK.md** — How Friday ingests and uses pattern libraries
- **EPOS_CONSTITUTION_v3.1.md** — Article XII (Agent Memory Sovereignty)
- **friday_pattern_library.json** — Live database of learned patterns

---

**Last Updated:** 2026-03-11
**Constitutional Authority:** Article XII, EPOS Constitution v3.1
**Next Phase:** SQUAD_COMMUNICATION_PROTOCOL.md (How agents communicate discoveries to Friday)
