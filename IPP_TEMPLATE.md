# IPP SUBMISSION TEMPLATE
**Imaginative Projection Protocol (IPP) — Article XIV Enforcement**

**Authority:** EPOS_CONSTITUTION_v3.1.md Article XIV, ARTICLE_XIV_ENFORCEMENT.md Section VI

---

## Preamble

This template is **mandatory for all code submissions** before they reach the Governance Gate. Failure to complete all 6 steps results in automatic rejection by `governance_gate_audit.py`.

The 6-step IPP discipline forces **pre-mortem reasoning** — the human equivalent of "playing out the scenario before executing it."

---

## [1/6] TOUCHPOINTS — What Files & Systems Are Affected?

**Purpose:** Map the immediate blast radius of this change.

```
Files Modified:
- [Path relative to EPOS_ROOT]
- [e.g., api/ttlg_systems_light_scout.py]

Files Read (No Modification):
- [e.g., .env, tools/litellm_client.py]

Directories Created/Changed:
- [e.g., context_vault/scans/{scan_id}/]

External Services Called:
- [e.g., OpenRouter Gemini API, LiteLLM proxy]

Configuration Dependencies:
- [e.g., TTLG_SCOUT_MODEL_ALIAS from .env]
```

---

## [2/6] FAILURE CHAINS — What Breaks If This Fails?

**Purpose:** Trace cascading failures down 3+ levels.

```
Primary Failure:
[What is the most likely failure mode? e.g., "Scout fails to parse market data"]

Level 1 Cascade:
[What downstream system depends on this output?]
- FOTW cannot capture ambient context → friday_vault_summary.py gets stale data

Level 2 Cascade:
[What depends on Level 1?]
- Content Lab node has incomplete input → markdown synthesis fails

Level 3 Cascade:
[What depends on Level 2?]
- Friday loop is "degraded" instead of "healthy" → user doesn't trust the diagnosis
```

---

## [3/6] ASSUMPTIONS — What Must Be True for This to Work?

**Purpose:** State the environmental preconditions explicitly.

```
Runtime Assumptions:
- Python version >= 3.11 (required by pathlib.Path features)
- filelock library installed (for JSONL concurrency safety)
- .env file has OPENROUTER_API_KEY set

Architectural Assumptions:
- context_vault/scans/{scan_id}/ directory exists (created by Scout startup)
- Friday is the sole writer to scan_state.json (single-writer enforcement)
- All model IDs are routed through litellm_client.py (mono-sovereign rule)

State Assumptions:
- At script startup, no other agent is reading context_vault/events/system_events.jsonl
- Previous scan (if any) has completed and closed its state file
```

---

## [4/6] DISASTER SCENARIOS — 3+ Failure Cases & Mitigations

**Purpose:** Rehearse failure before it happens. For each scenario, state:
- **Trigger:** The exact condition that causes failure
- **Symptom:** How failure manifests (log output, error, silent failure)
- **Mitigation:** What code prevents or catches this

### Scenario A: Missing Context Vault Directory

**Trigger:** `context_vault/scans/{scan_id}/` does not exist at runtime.

**Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: 'context_vault/scans/scan_20260311.../scout_output.json'`

**Mitigation:**
```python
# In every entrypoint startup:
scan_dir = Path(f"context_vault/scans/{scan_id}")
scan_dir.mkdir(parents=True, exist_ok=True)  # ← Safe creation
assert scan_dir.exists(), f"Context vault creation failed for {scan_id}"
```

### Scenario B: FOTW Appends While Scout Is Reading System Events

**Trigger:** Concurrent write to `context_vault/events/system_events.jsonl` without filelock.

**Symptom:** Corrupted JSONL line (partial JSON that fails `json.loads()`), silent data loss, or duplicate events.

**Mitigation:**
```python
from filelock import FileLock

def append_event(log_path: str, event: dict) -> None:
    lock = FileLock(f"{log_path}.lock")
    with lock:  # ← Blocks until lock acquired
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
```

### Scenario C: Model Alias Not Defined in .env

**Trigger:** `os.getenv("TTLG_SCOUT_MODEL_ALIAS")` returns `None`, then `litellm_client.py` receives `model=None`.

**Symptom:** `ValueError: Model name cannot be None` at runtime, or silent fallback to wrong model (if no validation).

**Mitigation:**
```python
# In litellm_client.py startup:
scout_alias = os.getenv("TTLG_SCOUT_MODEL_ALIAS")
assert scout_alias is not None, "TTLG_SCOUT_MODEL_ALIAS not set in .env"
model_id = ALIAS_MAP.get(scout_alias)
assert model_id is not None, f"Alias '{scout_alias}' not found in ALIAS_MAP"
```

---

## [5/6] CONSTITUTIONAL ALIGNMENT — Which Articles Does This Obey?

**Purpose:** Prove this change is governance-compliant, not just technically sound.

```
✅ Article II (Environment & Infrastructure):
  - Uses only POSIX path operations (pathlib.Path)
  - Does not assume specific filesystem layout outside EPOS_ROOT
  - Declares all environment dependencies in .env schema

✅ Article III (Governance Gate):
  - Does not import any non-Gemini models
  - Uses tools.litellm_client.run_model() (not direct litellm calls)
  - Produces immutable audit logs in append-only JSONL

✅ Article VII (Context Vault Compliance):
  - Writes only to deterministic paths: context_vault/scans/{scan_id}/...
  - Never deletes or modifies existing scan_state.json files directly
  - Appends to system_events.jsonl with filelock protection

✅ Article XIV (IPP Enforcement):
  - This IPP submission itself is the proof of Article XIV compliance
  - Code cannot be submitted without this form
```

---

## [6/6] ALIGNMENT ASSERTION — The Required Header

**Purpose:** Every code file must start with this exact header (using raw string to avoid Unicode escape errors).

This is the **literal text** that must appear at the top of every Python file generated:

```python
#!/usr/bin/env python3
r"""
File: C:\Users\Jamie\workspace\epos_mcp\[PATH_TO_FILE]

ALIGNMENT ASSERTION (IPP Step 6):
==================================
STEP 1 - TOUCHPOINTS: [List files affected]
STEP 2 - FAILURE CHAINS: [Describe cascades]
STEP 3 - DEPENDENCIES: [State assumptions]
STEP 4 - FAILURE SCENARIOS: [3+ scenarios with mitigations]
STEP 5 - CONSTITUTIONAL: Article II ✅, Article III ✅, Article VII ✅, Article XIV ✅
STEP 6 - PROOF: [5 explicit behaviors that demonstrate compliance]

Authority: Article XIV (ARTICLE_XIV_ENFORCEMENT.md)
Submission Date: [YYYY-MM-DD]
Submitting Agent: [Claude Code / Friday / Architect / etc.]
Governance Gate Status: PENDING → APPROVED (by governance_gate_audit.py)
"""

# [Rest of code follows below]
```

**Critical Rules:**
1. Must use `r"""..."""` (raw string) to avoid Python Unicode escape errors
2. The file path must be **Windows absolute path** (not WSL path)
3. All 6 steps must be completed and visible
4. Governance Gate audit checks for this header; its absence = auto-rejection

---

## Submission Workflow

### For Claude Code (The Submitter):

1. **Before writing any code,** complete this IPP template
2. **Save the completed IPP** to `context_vault/pending_ipp/{scan_id}_IPP.md`
3. **Write the code** with the Alignment Assertion header at the top
4. **Run the Governance Gate audit:**
   ```bash
   python3 tools/governance_gate_audit.py api/your_new_file.py
   ```
5. **Only if approved**, commit to the Friday decision log:
   ```json
   {"action": "code_submitted_approved", "file": "api/your_new_file.py", "scan_id": "..."}
   ```

### For Friday (The Orchestrator):

1. **Monitor** `context_vault/pending_ipp/` for new IPP submissions
2. **Validate** each IPP for completeness (all 6 sections)
3. **Trigger** the Governance Gate audit
4. **Log the decision** (approved/rejected) with timestamp
5. **If rejected,** escalate to Claude Code with specific Article XIV violations cited

### For the Governance Gate Audit (`governance_gate_audit.py`):

1. **Check for IPP header** in docstring (required)
2. **Verify all 6 steps** are documented in header
3. **Confirm Windows path** in File: declaration
4. **Verify model routing** (only litellm_client calls, no hardcoded models)
5. **Confirm Constitutional articles** (Articles II, III, VII, XIV)
6. **Log result** to `logs/governance_gate_audit.jsonl`
7. **Exit with code 0** (approved) or **1** (rejected)

---

## Examples

### Example 1: Scout Entrypoint Submission

```markdown
# IPP SUBMISSION: ttlg_systems_light_scout.py

## [1/6] TOUCHPOINTS
Files Modified:
- api/ttlg_systems_light_scout.py (new)
- .env (reads TTLG_SCOUT_MODEL_ALIAS)

Files Read:
- tools/litellm_client.py
- docs/governance/ (all governance files)

Directories Created:
- context_vault/scans/{scan_id}/

## [2/6] FAILURE CHAINS
Primary: Scout cannot parse target list → empty findings

Level 1: FOTW has nothing to capture → ambient_log is sparse

Level 2: Content Lab has incomplete input → markdown synthesis weak

Level 3: Friday marks loop as "degraded" → user doesn't trust diagnosis

## [3/6] ASSUMPTIONS
- Target list format is deterministic (comma-separated or JSON array)
- Gemini 1.5-flash can parse governance violations consistently
- Files in context_vault/ can be read without lock (read-only for Scout)

## [4/6] DISASTER SCENARIOS

### Scenario A: Empty Target List
Mitigation: Assert len(targets) > 0 before Scout execution

### Scenario B: Gemini Rate Limit
Mitigation: Retry with exponential backoff (max 3 retries)

### Scenario C: scout_output.json Incomplete
Mitigation: Write atomic JSON with version counter, validate schema before FOTW reads

## [5/6] CONSTITUTIONAL ALIGNMENT
✅ Article II (Environment): Uses .env for model alias, POSIX paths
✅ Article III (Governance): Only Gemini via litellm_client
✅ Article VII (Context Vault): Writes to context_vault/scans/{scan_id}/scout_output.json
✅ Article XIV (IPP): This IPP proves compliance

## [6/6] ALIGNMENT ASSERTION
[Header code pasted above]
```

---

## References

- **ARTICLE_XIV_ENFORCEMENT.md** — Section VI (Governance Gate Hard Stops)
- **IMAGINATIVE_PROJECTION_PROTOCOL.md** — Full discipline specification
- **EPOS_CONSTITUTION_v3.1.md** — Constitutional articles II, III, VII, XIV
- **governance_gate_audit.py** — The enforcement mechanism that validates this template

---

**Last Updated:** 2026-03-11
**Constitutional Authority:** Article XIV, EPOS Constitution v3.1
**Next Evolution:** AAR_TEMPLATE.md (After-Action Review) — Captures learnings from execution
