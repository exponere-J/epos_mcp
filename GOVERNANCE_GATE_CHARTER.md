# GOVERNANCE GATE CHARTER
**Constitutional Hard-Stop Rules for Code Submission**

**Authority:** EPOS_CONSTITUTION_v3.1.md Article XIV (IPP Enforcement), Article III (Governance Gate)

---

## Preamble

The **Governance Gate** is the mechanical enforcer that prevents code from executing if it violates the EPOS Constitution. It is **not a suggestion, preference, or review suggestion**—it is a hard-stop that blocks deployment.

This document formalizes the **exact criteria** that cause the gate to **REJECT** a submission and require rework.

The gate operates in two modes:

1. **Automatic (governance_gate_audit.py)** — Machine-readable validation
2. **Manual (Friday/Claude Code)** — Constitutional interpretation for edge cases

---

## PART 1: AUTOMATIC HARD-STOPS

These criteria are checked by `tools/governance_gate_audit.py`. **Presence of any violation = automatic rejection.**

### Hard-Stop 1: Missing IPP Header

**Violation:** Code file does not start with the required Alignment Assertion docstring.

```
TRIGGER:
  File is submitted for deployment to api/, scripts/, tools/, or friday_orchestrator/

CHECK:
  Does the file start with:
  r"""
  File: C:\Users\Jamie\workspace\epos_mcp\[ABSOLUTE_PATH]
  
  ALIGNMENT ASSERTION (IPP Step 6):
  ==================================
  STEP 1 - TOUCHPOINTS: [filled]
  STEP 2 - FAILURE CHAINS: [filled]
  STEP 3 - DEPENDENCIES: [filled]
  STEP 4 - FAILURE SCENARIOS: [filled with 3+ scenarios]
  STEP 5 - CONSTITUTIONAL: Article II ✅, Article III ✅, ...
  STEP 6 - PROOF: [filled with 5+ explicit behaviors]
  
  Authority: Article XIV (ARTICLE_XIV_ENFORCEMENT.md)
  Submission Date: [YYYY-MM-DD]
  Submitting Agent: [Agent Name]
  Governance Gate Status: PENDING → APPROVED
  """?

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_MISSING_IPP_HEADER: File lacks required Alignment Assertion docstring.
   Submit IPP_TEMPLATE.md section [6/6] at top of file.
   Authority: Article XIV, Section VI.2"

EXIT CODE: 1 (Failure)
```

### Hard-Stop 2: Hardcoded Model Literals (Non-Gemini or Non-Aliased)

**Violation:** Code contains strings like `"google/gemini-1.5-flash"`, `"openai/gpt-4"`, or any direct model name instead of env-driven aliases.

```
TRIGGER:
  File is submitted to api/, tools/, or friday_orchestrator/

CHECK:
  Regex search for patterns:
  - "google/gemini.*" (anywhere in code)
  - "openai/.*"
  - "anthropic/.*"
  - "deepseek.*"
  - Any other model ID literals in string form

  CORRECT pattern:
  - model_alias = os.getenv("TTLG_SCOUT_MODEL_ALIAS")
  - model_id = tools.litellm_client.resolve_alias(model_alias)
  - response = tools.litellm_client.run_model(model_id, prompt)

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_HARDCODED_MODEL: Found hardcoded model literal at line [N].
   All models must route through tools/litellm_client.py with env aliases.
   Replace with: os.getenv('MODEL_ALIAS_NAME')
   Authority: Article III, Section IV (Mono-Sovereign Gemini Policy)"

EXIT CODE: 1 (Failure)
```

### Hard-Stop 3: Direct os.system() or Shell Injection

**Violation:** Code uses `os.system()`, `subprocess.call()`, or raw shell commands instead of approved wrappers.

```
TRIGGER:
  File contains system calls to shell commands

CHECK:
  Search for patterns:
  - os.system(
  - subprocess.call(
  - subprocess.Popen(... shell=True ...)
  - Any f-string or format string passed to shell execution

  ALLOWED patterns:
  - subprocess.run(..., capture_output=True, text=True) with explicit args list
  - tools.epos_tools.safe_execute() (if wrapper exists)
  - bash scripts in scripts/ with shellcheck validation

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_UNSAFE_SHELL_EXECUTION: Code uses os.system() at line [N].
   Use subprocess.run() with explicit argument lists instead.
   Never pass user input or environment variables directly to shell.
   Authority: Article II, Section III (Environment Safety)"

EXIT CODE: 1 (Failure)
```

### Hard-Stop 4: Unauthorized Context Vault Modifications

**Violation:** Code writes or deletes files outside of approved subdirectories in context_vault/.

```
TRIGGER:
  File attempts file I/O operations on context_vault/ paths

CHECK:
  Approved write paths:
  ✅ context_vault/scans/{scan_id}/ (Scout owns)
  ✅ context_vault/agent_logs/fotw_captures/{scan_id}/ (FOTW owns)
  ✅ context_vault/mission_data/ (Content Lab owns)
  ✅ context_vault/events/ (append-only with filelock)
  ✅ context_vault/pending_ipp/ (pending submissions)
  ✅ context_vault/aar/ (after-action reviews)

  Forbidden operations:
  ❌ Delete any file in context_vault/
  ❌ Modify existing scan_state.json (only Friday writes)
  ❌ Write outside deterministic scan_id paths
  ❌ Access context_vault/secrets/ (no direct access)

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_UNAUTHORIZED_VAULT_WRITE: Code attempts write to context_vault/[PATH].
   Only these agents can write:
     - Scout: context_vault/scans/{scan_id}/
     - FOTW: context_vault/agent_logs/fotw_captures/{scan_id}/
     - ContentLab: context_vault/mission_data/
     - Friday: context_vault/scans/{scan_id}/scan_state.json (only)
   Authority: Article VII, Section II (Context Vault Governance)"

EXIT CODE: 1 (Failure)
```

### Hard-Stop 5: Path Clarity Violation

**Violation:** Code mixes Windows paths (`C:\`), Unix paths (`/c/`), or relative paths without a canonical rule.

```
TRIGGER:
  File contains path construction or file I/O operations

CHECK:
  Every path operation must follow ONE of these patterns:

  PATTERN A (Recommended): pathlib.Path + relative to EPOS_ROOT
    epos_root = Path(os.getenv("EPOS_ROOT", "."))
    scan_dir = epos_root / "context_vault" / "scans" / scan_id
    ✅ APPROVED

  PATTERN B: Absolute path with explicit env var
    abs_path = Path(os.getenv("AGENT_ZERO_PATH")) / "config.json"
    ✅ APPROVED (if .env declares absolute path)

  PATTERN C: Never use these
    ❌ os.path.join("C:\\Users", "Jamie", ...)
    ❌ f"/c/Users/Jamie/workspace/{file}"
    ❌ hardcoded "/home/claude/..." paths

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_PATH_CLARITY_VIOLATION: Code uses mixed path formats at line [N].
   Choose ONE canonical path strategy:
     - pathlib.Path + EPOS_ROOT env var (recommended)
     - Absolute paths via env vars only
   Never mix Windows/Unix paths or use hardcoded paths.
   Authority: Article II, Section II (Path Validation Rules)"

EXIT CODE: 1 (Failure)
```

### Hard-Stop 6: No File Locking on Shared JSONL

**Violation:** Code appends to a shared JSONL file (multi-writer) without `filelock`.

```
TRIGGER:
  File writes to these paths in append mode:
  - context_vault/events/system_events.jsonl
  - logs/ttlg_diagnostics.jsonl
  - friday_orchestrator/logs/friday_decisions.jsonl
  - Any other JSONL file that multiple agents write to

CHECK:
  Does the code use filelock?

  CORRECT pattern:
    from filelock import FileLock
    lock = FileLock(f"{log_path}.lock")
    with lock:
        with open(log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

  INCORRECT patterns:
    ❌ No lock at all
    ❌ fcntl.flock() on WSL2
    ❌ threading.Lock() (process-level, not inter-process)

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_CONCURRENCY_UNSAFE: Code appends to [FILE] without filelock.
   Install filelock and use:
     lock = FileLock('{log_path}.lock')
     with lock: [write operation]
   Authority: Article VII, Section III (Serialized State Reduction)"

EXIT CODE: 1 (Failure)
```

### Hard-Stop 7: Missing Trace ID / Scan ID

**Violation:** Code that writes to system_events.jsonl does not include trace_id and scan_id in every event.

```
TRIGGER:
  File calls append_event() or writes to system_events.jsonl

CHECK:
  Does every event have these fields?
  - trace_id (UUID, same across entire diagnostic cycle)
  - scan_id (deterministic: scan_YYYYMMDD_HHMMSS)

ACTION IF VIOLATED:
  ❌ REJECT with error:
  "ERR_MISSING_TRACE_CORRELATION: Event lacks trace_id or scan_id at line [N].
   Every event must include:
     {
       'trace_id': 'trace-abc123...',
       'scan_id': 'scan_20260311_083000',
       'timestamp': '2026-03-11T08:30:00Z',
       ...
     }
   Authority: Article VIII, Section II (Unified Nervous System)"

EXIT CODE: 1 (Failure)
```

---

## PART 2: MANUAL HARD-STOPS

These are checked by **Friday or Claude Code** when machine rules are ambiguous. Violation = rejection + human escalation.

### Manual Hard-Stop 1: Undocumented Failure Mode

**Violation:** Code handles an error case but doesn't log it to audit trail.

```
TRIGGER:
  Code contains try/except block

CHECK:
  Is there a corresponding audit log entry?

  CORRECT pattern:
    try:
        result = risky_operation()
    except SpecificError as e:
        event = {
            "trace_id": trace_id,
            "scan_id": scan_id,
            "event_type": "error.operation_failed",
            "severity": "warning",
            "error": str(e)
        }
        append_event(event)
        raise

  INCORRECT pattern:
    try:
        result = risky_operation()
    except:
        pass  # ❌ Silent failure

ACTION IF VIOLATED:
  ❌ REJECT with comment:
  "Silent error handling detected. All exceptions must be logged to
   system_events.jsonl before being handled or re-raised.
   Authority: Article II, Section IV (No Silent Failures)"

ESCALATION: Requires Friday or Claude Code review
```

### Manual Hard-Stop 2: Incomplete IPP Disaster Scenarios

**Violation:** IPP Step 4 lists fewer than 3 disaster scenarios or scenarios lack explicit mitigations.

```
TRIGGER:
  IPP_TEMPLATE.md Section [4/6] is incomplete

CHECK:
  Are there 3+ scenarios?
  Does each scenario have:
  - Trigger (the exact condition)
  - Symptom (how failure manifests)
  - Mitigation (code that prevents it)

ACTION IF VIOLATED:
  ❌ REJECT with comment:
  "IPP disaster scenarios incomplete. Article XIV requires imagination
   about 3+ failure modes and explicit mitigations BEFORE code submission.
   
   Missing scenarios or mitigations in:
   [scenario list]
   
   Resubmit with complete disaster planning."

ESCALATION: Claude Code must revise IPP before code is accepted
```

### Manual Hard-Stop 3: Constitutional Articles Not Demonstrated

**Violation:** IPP Step 5 lists articles as "compliant" but code doesn't actually prove compliance.

```
TRIGGER:
  IPP_TEMPLATE.md Section [5/6] claims Article X compliance

CHECK:
  Is there actual code evidence?

  EXAMPLE (Good):
  "✅ Article III (Governance Gate):
     - Does not import any non-Gemini models ✓
     - Uses tools.litellm_client.run_model() ✓ (see line 42)
     - Produces immutable audit logs in append-only JSONL ✓ (see line 88)"

  EXAMPLE (Bad):
  "✅ Article III (Governance Gate):
     - Governance compliant" (no evidence)

ACTION IF VIOLATED:
  ❌ REJECT with comment:
  "Constitutional alignment claims lack evidence. Article XIV requires
   explicit demonstration (with line numbers) that code obeys Articles II-VII.
   
   Generic claims like 'compliant' are insufficient.
   
   Resubmit IPP Step 5 with specific code citations."

ESCALATION: Claude Code must add evidence before resubmission
```

### Manual Hard-Stop 4: Agent Authority Violation

**Violation:** Code attempts to write to a file that another agent owns.

```
TRIGGER:
  Code writes to context_vault/ or context_vault/scans/

CHECK:
  Is this agent authorized to write to this path?

  Ownership Map:
  - Scout: context_vault/scans/{scan_id}/scout_output.json
  - FOTW: context_vault/agent_logs/fotw_captures/{scan_id}/ambient_log.jsonl
  - Content Lab: context_vault/mission_data/content_lab_output_{scan_id}*.md
  - Friday: context_vault/scans/{scan_id}/scan_state.json (sole writer)
  - All: context_vault/events/system_events.jsonl (append-only)

ACTION IF VIOLATED:
  ❌ REJECT with comment:
  "Agent authority violation. [Agent] is not authorized to write to
   [Path]. Only [Authorized Agent] can write to this location.
   
   Redesign code to use event-based coordination instead of direct writes.
   Authority: Article VIII (Unified Nervous System) — Single Writer Rule"

ESCALATION: Requires architectural redesign + new IPP
```

---

## PART 3: GOVERNANCE GATE AUDIT SCRIPT

The automatic enforcement is implemented in `tools/governance_gate_audit.py`. Here's the validation checklist it runs:

```python
def validate_submission(file_path: str) -> tuple[bool, str]:
    """
    Returns: (is_approved: bool, reason: str)
    Approved = True, Rejected = False
    """
    
    checks = [
        ("IPP Header Present", check_ipp_header),
        ("No Hardcoded Models", check_model_routing),
        ("No Direct Shell Execution", check_shell_safety),
        ("Context Vault Paths Authorized", check_vault_permissions),
        ("Path Clarity Rules", check_path_consistency),
        ("File Locking on Shared JSONL", check_file_locking),
        ("Trace ID / Scan ID Present", check_correlation_ids),
    ]
    
    results = []
    for check_name, check_func in checks:
        passed, reason = check_func(file_path)
        results.append((check_name, passed, reason))
        if not passed:
            return False, f"{check_name}: {reason}"
    
    return True, "All governance checks passed"
```

**Invocation:**
```bash
python3 tools/governance_gate_audit.py api/ttlg_systems_light_scout.py

# Output (if passing):
✅ Governance Gate APPROVED
File: api/ttlg_systems_light_scout.py
Checks: 7/7 passed
Reason: All governance checks passed

# Output (if failing):
❌ Governance Gate REJECTED
File: api/ttlg_systems_light_scout.py
Failing Check: No Hardcoded Models
Reason: Found hardcoded model at line 42: "google/gemini-1.5-flash"
        Replace with env alias via tools.litellm_client.run_model()
Authority: Article III, Section IV

Exit Code: 1
```

---

## PART 4: ESCALATION PATHS

### If Automatic Validation Fails

1. **Report** to Friday's inbox:
   ```json
   {
     "message_type": "ESCALATION",
     "subject": "Governance Gate Rejection: [File]",
     "failing_check": "[Check Name]",
     "reason": "[Machine-readable error]",
     "required_action": "Claude Code must revise and resubmit"
   }
   ```

2. **Claude Code** receives the rejection and must revise the code or IPP

3. **Resubmit** after fixes are applied

4. **Friday logs** the revision in `friday_decisions.jsonl`:
   ```json
   {
     "action": "governance_gate_rejection",
     "file": "api/...",
     "reason": "ERR_HARDCODED_MODEL",
     "timestamp": "2026-03-11T10:30:00Z"
   }
   ```

### If Manual Validation Flags Ambiguity

1. **Friday or Claude Code** writes a detailed comment to the IPP

2. **Author** has 24 hours to respond with evidence or redesign

3. **Final decision** by Friday Orchestrator:
   - Approve (confidence > 0.95)
   - Reject (confidence < 0.70)
   - Request redesign (needs architectural change)

---

## PART 5: CONSTITUTIONAL BINDING

**This charter is binding because:**

1. **Article III** (Governance Gate) mandates hard-stops on security/integrity violations
2. **Article XIV** (IPP Enforcement) requires documented failure analysis before submission
3. **Article VII** (Context Vault Governance) defines authority boundaries
4. **Article II** (Environment & Infrastructure) requires path clarity and failure logging

**Violation of this charter = Violation of the EPOS Constitution.**

---

## PART 6: OVERRIDE RULES

Only **one person can override** the Governance Gate: **Jamie (Founder)**.

**Override Procedure:**
1. Jamie explicitly signs off in the IPP with: `[FOUNDER_OVERRIDE: reason]`
2. The override reason must be **documented** in the submission
3. A compensating control must be added (new test, monitoring, etc.)
4. Friday logs the override with full audit trail

**Example:**
```markdown
## [FOUNDER_OVERRIDE]

Reason: This is a temporary patch for a critical production incident.
Compensating Control: Will be replaced with compliant implementation by [DATE]
Approval: Jamie Signature + Timestamp
```

Override frequency is monitored by Friday. If overrides exceed 2 per month, Friday escalates to strategic review.

---

## References

- **ARTICLE_XIV_ENFORCEMENT.md** — The constitutional mandate for this charter
- **EPOS_CONSTITUTION_v3.1.md** — Articles II, III, VII, VIII, XIV
- **governance_gate_audit.py** — The mechanical enforcer
- **IPP_TEMPLATE.md** — The submission discipline that this gate validates

---

**Last Updated:** 2026-03-11
**Constitutional Authority:** Article III, XIV, EPOS Constitution v3.1
**Next Evolution:** SCALING_PROTOCOL.md (How to request new resources when governance is proven)
