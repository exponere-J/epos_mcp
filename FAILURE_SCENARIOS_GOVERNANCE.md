# File: C:\Users\Jamie\workspace\epos_mcp\FAILURE_SCENARIOS_GOVERNANCE.md

# FAILURE SCENARIOS: GOVERNANCE GATE SUBSYSTEM
## Pre-Mortem Analysis for Constitutional Enforcement

**Created:** 2026-01-31  
**Constitutional Authority:** EPOS_CONSTITUTION_v3.1.md Article I (Pre-Mortem Mandate)  
**Purpose:** Document all foreseeable failure modes BEFORE implementation  
**Methodology:** Imaginative projection of multi-layered consequences

---

## 🎯 PRE-MORTEM PHILOSOPHY

> "Before we climb Everest, we imagine every way we could fall."

This document embodies **Article I: The Pre-Mortem Mandate:**

1. **Imaginative Projection**: Play out 3-5 failure scenarios mentally
2. **Consequence Mapping**: Document downstream effects of each failure
3. **Alignment Validation**: Verify recovery procedures exist
4. **Recovery Planning**: Define rollback procedures for each failure
5. **Success Criteria**: Know what "working" looks like for each component

**Key Insight from ARCHITECTURAL_ANALYSIS.md:**
> "We were debugging in production instead of designing with foresight."

This document prevents that by designing FOR failure, not FROM failure.

---

## SCENARIO CATEGORY 1: CONSTITUTIONAL DOCUMENT FAILURES

### FS-CONST-001: EPOS_CONSTITUTION_v3.1.md Missing

**Imaginative Projection:**
"What if the constitution file is deleted or moved?"

**Cascade Analysis:**
1. epos_doctor.py check_constitutional_documents() fails
2. epos_doctor.py returns exit code 2 (critical violation)
3. governance_gate.py cannot start (doctor fails pre-flight)
4. All validation halts - no way to know what rules to enforce
5. Agent Zero cannot be seated - no governance framework exists
6. Manual intervention required - system enters STASIS mode

**Downstream Consequences:**
- **Immediate**: No automated validation possible
- **Short-term**: All development halts (no way to approve code)
- **Long-term**: Constitutional drift if recreated from memory vs backup

**Recovery Procedure:**
```bash
# 1. Detect failure
python epos_doctor.py --check-constitution
# Exit code: 2 (critical)

# 2. Enter STASIS mode
python engine/stasis.py --reason "Constitution missing" --severity critical

# 3. Restore from backup
cp ../epos_mcp_backup/EPOS_CONSTITUTION_v3.1.md .

# 4. Validate restoration
python epos_doctor.py --check-constitution
# Exit code: 0 (success)

# 5. Resume operations
python engine/stasis.py --resume --verified-by Jamie
```

**Prevention Design:**
- [ ] Daily backup of constitutional documents to external drive
- [ ] Git version control with remote backup
- [ ] epos_doctor.py validates presence before ANY operation
- [ ] Read-only permissions on constitutional files (prevent accidental deletion)

**Success Criteria:**
- Constitution file exists at C:\Users\Jamie\workspace\epos_mcp\EPOS_CONSTITUTION_v3.1.md
- First line contains "# EPOS CONSTITUTION v3.1"
- File is readable and parsable as Markdown
- epos_doctor.py constitutional checks pass

---

### FS-CONST-002: Version Mismatch (Code references v3.0, file is v3.1)

**Imaginative Projection:**
"What if updated constitution but forgot to update code references?"

**Cascade Analysis:**
1. governance_gate.py imports old violation codes from memory
2. Validation logic enforces v3.0 rules, ignores v3.1 rules
3. Context Vault violations not detected (Article VII is new in v3.1)
4. Files with inline data > 8K tokens get promoted
5. Token overflow occurs in production
6. Agent Zero consumes entire context window with single mission
7. Execution failures with cryptic "context too long" errors

**Downstream Consequences:**
- **Immediate**: Incorrect validation (false negatives)
- **Short-term**: Non-compliant code enters production
- **Long-term**: Constitutional drift, governance erosion

**Recovery Procedure:**
```bash
# 1. Detect mismatch
grep -r "EPOS_CONSTITUTION_v3.0" *.py
# Shows files still referencing old version

# 2. Update all references
find . -name "*.py" -exec sed -i 's/v3.0/v3.1/g' {} +

# 3. Validate alignment
python governance_gate.py --dry-run --verbose
# Check that v3.1 rules (ERR-CONTEXT-001) are enforced

# 4. Re-run compliance audit
python governance_gate.py --full-audit > audit_post_fix.json
```

**Prevention Design:**
- [ ] Constitutional version check in epos_doctor.py
- [ ] All code files reference constitution via variable, not hardcoded string
- [ ] CI/CD pipeline fails if version mismatch detected
- [ ] Constitutional amendments trigger automated code updates

```python
# GOOD PATTERN:
from pathlib import Path
CONSTITUTION_PATH = Path(__file__).parent / "EPOS_CONSTITUTION_v3.1.md"
CONSTITUTION_VERSION = "3.1.0"

def validate_constitution():
    with open(CONSTITUTION_PATH) as f:
        first_line = f.readline()
        if CONSTITUTION_VERSION not in first_line:
            raise EnvironmentError(f"Constitution version mismatch")
```

**Success Criteria:**
- All .py files reference current constitution version
- epos_doctor.py validates version alignment
- No hardcoded v3.0 references remain in codebase

---

## SCENARIO CATEGORY 2: ENVIRONMENT VALIDATION FAILURES

### FS-ENV-001: Python Version Drift (User upgrades to 3.13)

**Imaginative Projection:**
"What if user upgrades Python and libraries break?"

**Cascade Analysis:**
1. User installs Python 3.13 for another project
2. PATH now points to Python 3.13 instead of 3.11
3. Some dependencies (e.g., Flask) have incompatible ABIs
4. `pip install -r requirements.txt` fails with cryptic errors
5. epos_doctor.py detects Python 3.13 (version check passes ≥3.11)
6. But import failures occur at runtime
7. governance_gate.py crashes on import of broken dependency

**Downstream Consequences:**
- **Immediate**: governance_gate.py cannot start
- **Short-term**: All validation halts
- **Long-term**: Frustration, manual environment debugging

**Recovery Procedure:**
```bash
# 1. Detect Python version
python --version
# Python 3.13.0

# 2. Check for library compatibility
pip check
# Shows incompatible packages

# 3. Downgrade Python or use virtual environment
pyenv install 3.11.9
pyenv local 3.11.9

# 4. Reinstall dependencies
pip install -r requirements.txt

# 5. Validate environment
python epos_doctor.py
# Exit code: 0
```

**Prevention Design:**
- [ ] Virtual environment REQUIRED (not optional)
- [ ] epos_doctor.py checks exact Python version (3.11.x, not just ≥3.11)
- [ ] requirements.txt pins EXACT versions (Flask==3.0.0, not Flask>=3.0)
- [ ] Pre-flight fails with specific guidance if version wrong

```python
# GOOD PATTERN:
REQUIRED_PYTHON_EXACT = (3, 11)
ALLOWED_PYTHON_MINOR = range(0, 20)  # 3.11.0 through 3.11.19

if sys.version_info[:2] != REQUIRED_PYTHON_EXACT:
    print(f"❌ Python {REQUIRED_PYTHON_EXACT[0]}.{REQUIRED_PYTHON_EXACT[1]}.x required")
    print(f"   Current: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    sys.exit(2)
```

**Success Criteria:**
- Python version is 3.11.x (not 3.12 or 3.13)
- All dependencies install without errors
- epos_doctor.py passes all checks

---

### FS-ENV-002: Ollama Service Down

**Imaginative Projection:**
"What if Ollama crashes or user forgets to start it?"

**Cascade Analysis:**
1. User reboots machine, Ollama doesn't auto-start
2. governance_gate.py starts, passes epos_doctor.py checks
3. Agent Zero mission submitted
4. Agent Zero tries to call Ollama on localhost:11434
5. Connection refused error
6. Agent Zero reports "mission failed" but doesn't explain why
7. User spends 30 minutes debugging, eventually realizes Ollama not running

**Downstream Consequences:**
- **Immediate**: Agent Zero missions fail silently
- **Short-term**: Wasted debugging time
- **Long-term**: User loses trust in system reliability

**Recovery Procedure:**
```bash
# 1. Detect Ollama failure
python epos_doctor.py --verbose
# ❌ FAIL: Ollama service not responding on :11434

# 2. Start Ollama
ollama serve &

# 3. Verify connectivity
curl http://localhost:11434/api/tags
# Should return JSON

# 4. Re-run validation
python epos_doctor.py
# Exit code: 0
```

**Prevention Design:**
- [ ] epos_doctor.py ALWAYS checks Ollama before allowing execution
- [ ] Clear error message: "Start Ollama: `ollama serve`"
- [ ] Optionally: Auto-start Ollama if detected but not running
- [ ] Health check every 60 seconds in continuous mode

```python
# GOOD PATTERN:
def check_ollama(self) -> Tuple[bool, str]:
    try:
        sock = socket.socket()
        sock.settimeout(2)
        sock.connect(('localhost', 11434))
        sock.close()
        return True, "Ollama service running on :11434"
    except (ConnectionRefusedError, TimeoutError):
        return False, "Ollama not running. Start with: ollama serve"
```

**Success Criteria:**
- Ollama responds to health check on port 11434
- epos_doctor.py detects service and reports status
- Agent Zero missions can connect to Ollama

---

## SCENARIO CATEGORY 3: GOVERNANCE GATE VALIDATION FAILURES

### FS-GATE-001: False Positive (Compliant Code Rejected)

**Imaginative Projection:**
"What if governance_gate.py rejects perfectly good code?"

**Cascade Analysis:**
1. Developer writes compliant module with header, absolute paths, pre-flight
2. governance_gate.py has overly strict regex for ERR-PATH-001
3. Code uses `Path("C:/Users/Jamie/...")` which is CORRECT
4. But regex expects `Path("C:\\Users\\...")`  (backslashes)
5. False positive: ERR-PATH-001 detected
6. File rejected, educational receipt generated
7. Developer confused: "But this IS an absolute path!"
8. Developer files complaint, loses trust in governance

**Downstream Consequences:**
- **Immediate**: Developer blocked from progressing
- **Short-term**: Manual override required, governance bypassed
- **Long-term**: Governance gate seen as obstacle, not helper

**Recovery Procedure:**
```bash
# 1. Developer reviews rejection receipt
cat rejected/receipts/my_module_2026-01-31_143022.md
# Shows ERR-PATH-001: Path("C:/Users/...") detected

# 2. Developer confirms code IS compliant
# Manually reads EPOS_CONSTITUTION_v3.1.md Article II Rule 1

# 3. Developer uses override
python governance_gate.py --override --file my_module.py --reason "False positive on ERR-PATH-001"

# 4. File promoted manually
mv inbox/my_module.py engine/my_module.py

# 5. Developer files bug report
# governance_gate.py regex needs to accept forward slashes
```

**Prevention Design:**
- [ ] Test suite with known-good files (should all pass)
- [ ] Regex patterns tested against constitutional examples
- [ ] Human review of first 10 rejections to calibrate
- [ ] --override flag requires human justification (logged)

```python
# BAD REGEX (too strict):
PATH_PATTERN = r'Path\("C:\\\\Users\\\\Jamie'

# GOOD REGEX (accepts both):
PATH_PATTERN = r'Path\(["\']C:[/\\]Users[/\\]Jamie'
```

**Success Criteria:**
- False positive rate <5%
- All constitutional examples pass validation
- Override mechanism works and logs justification

---

### FS-GATE-002: False Negative (Violating Code Promoted)

**Imaginative Projection:**
"What if governance_gate.py misses a real violation?"

**Cascade Analysis:**
1. Developer writes code with relative path: `config = "../../config.json"`
2. governance_gate.py regex for ERR-PATH-001 doesn't catch this pattern
3. File promoted to engine/
4. Code runs on developer machine (current directory is EPOS_ROOT)
5. Code fails in production (current directory is different)
6. Silent failure: config file not found, no error raised
7. Agent Zero uses default config instead of production config
8. Wrong behavior ensues, no idea why

**Downstream Consequences:**
- **Immediate**: No impact (code appears to work)
- **Short-term**: Production failures in different environment
- **Long-term**: Constitutional drift, governance erosion

**Recovery Procedure:**
```bash
# 1. Production failure detected
# Error: FileNotFoundError: ../../config.json

# 2. Code review identifies relative path
grep -n "\.\./\.\./config.json" engine/*.py
# Shows file and line number

# 3. Fix violation
# Replace with: Path("C:/Users/Jamie/workspace/epos_mcp/config.json")

# 4. Update governance_gate.py regex
# Add pattern to catch "../" relative paths

# 5. Re-run validation on ALL engine/ files
python governance_gate.py --audit-engine

# 6. Move non-compliant files back to inbox for re-validation
```

**Prevention Design:**
- [ ] Comprehensive regex test suite (all known violation patterns)
- [ ] Periodic re-audit of engine/ files (weekly)
- [ ] Production environment different from dev (catches path issues early)
- [ ] Continuous improvement: Add new patterns when false negatives discovered

```python
# IMPROVED REGEX (catches more patterns):
RELATIVE_PATH_PATTERNS = [
    r'["\']\.\./',           # ../ pattern
    r'["\']\./',             # ./ pattern
    r'["\'][^C:/].*\.json',  # any relative file reference
]
```

**Success Criteria:**
- False negative rate = 0% for critical violations
- Periodic audits catch any missed violations
- Governance patterns updated when new violations discovered

---

### FS-GATE-003: VIOLATION_CODES.json Corrupted

**Imaginative Projection:**
"What if VIOLATION_CODES.json becomes invalid JSON?"

**Cascade Analysis:**
1. Developer manually edits VIOLATION_CODES.json
2. Forgets trailing comma in JSON object
3. File becomes syntactically invalid
4. governance_gate.py tries to load file
5. `json.JSONDecodeError: Expecting ',' delimiter: line 42 column 5`
6. governance_gate.py crashes with stack trace
7. No validation possible until fixed

**Downstream Consequences:**
- **Immediate**: governance_gate.py cannot start
- **Short-term**: All validation halts
- **Long-term**: Developer frustration with brittle system

**Recovery Procedure:**
```bash
# 1. Detect JSON error
python governance_gate.py
# JSONDecodeError: Expecting ',' delimiter: line 42 column 5

# 2. Validate JSON syntax
python -m json.tool VIOLATION_CODES.json
# Shows syntax error location

# 3. Fix syntax error
# Edit file, add missing comma

# 4. Re-validate
python -m json.tool VIOLATION_CODES.json > /dev/null
# Exit code 0: valid JSON

# 5. Retry governance gate
python governance_gate.py --dry-run
# Should work now
```

**Prevention Design:**
- [ ] JSON schema validation before loading
- [ ] Automated syntax check in epos_doctor.py
- [ ] Version control (git) for easy rollback
- [ ] Automated tests that load VIOLATION_CODES.json

```python
# GOOD PATTERN:
def load_violation_codes():
    try:
        with open("VIOLATION_CODES.json") as f:
            codes = json.load(f)
        
        # Validate schema
        required_keys = ["violations", "severity_levels"]
        for key in required_keys:
            if key not in codes:
                raise ValueError(f"Missing required key: {key}")
        
        return codes
    
    except json.JSONDecodeError as e:
        print(f"❌ VIOLATION_CODES.json syntax error: {e}")
        print(f"   Validate with: python -m json.tool VIOLATION_CODES.json")
        sys.exit(2)
```

**Success Criteria:**
- VIOLATION_CODES.json is valid JSON
- Schema validation passes
- governance_gate.py loads file without errors

---

## SCENARIO CATEGORY 4: CONTEXT VAULT FAILURES

### FS-VAULT-001: Referenced File Missing

**Imaginative Projection:**
"What if mission references context vault file that doesn't exist?"

**Cascade Analysis:**
1. Developer creates mission_spec.json
2. Sets `"context_vault_path": "context_vault/mission_data/dataset.txt"`
3. Forgets to actually create dataset.txt
4. governance_gate.py validates mission_spec.json
5. Checks for ERR-CONTEXT-002: vault file referenced but missing
6. File rejected with educational receipt
7. Developer realizes mistake, creates dataset.txt
8. Re-submits mission_spec.json

**Downstream Consequences:**
- **Immediate**: Mission rejected (good - prevents runtime failure)
- **Short-term**: Developer creates missing file
- **Long-term**: System remains robust (no runtime surprises)

**Recovery Procedure:**
```bash
# 1. Rejection receipt shows ERR-CONTEXT-002
cat rejected/receipts/mission_spec_2026-01-31_143022.md
# Context vault file referenced but missing: context_vault/mission_data/dataset.txt

# 2. Create missing file
touch context_vault/mission_data/dataset.txt
# Or populate with actual data

# 3. Re-submit mission
cp rejected/mission_spec.json inbox/mission_spec.json

# 4. Re-run validation
python governance_gate.py
# ✅ PROMOTED: mission_spec.json
```

**Prevention Design:**
- [ ] governance_gate.py checks vault file existence
- [ ] Clear error message with exact file path
- [ ] Optional: --auto-create-vault-files flag to create empty placeholders
- [ ] Documentation: Always create vault file BEFORE referencing it

**Success Criteria:**
- Referenced vault file exists at specified path
- governance_gate.py detects missing files
- Clear remediation guidance provided

---

### FS-VAULT-002: File Size Exceeds 100MB

**Imaginative Projection:**
"What if vault file grows too large for efficient search?"

**Cascade Analysis:**
1. Developer stores 150MB CSV in context_vault/
2. Mission uses symbolic search on this file
3. Regex search loads file into memory for pattern matching
4. Search takes 30+ seconds
5. User waits, thinks system froze
6. Multiple concurrent missions cause memory exhaustion
7. System becomes unresponsive

**Downstream Consequences:**
- **Immediate**: Poor performance
- **Short-term**: User experience degrades
- **Long-term**: System perceived as slow/broken

**Recovery Procedure:**
```bash
# 1. Detect large files
find context_vault/ -type f -size +100M
# Shows: context_vault/mission_data/huge_dataset.csv (150MB)

# 2. Split file into chunks
split -l 100000 huge_dataset.csv chunk_
# Creates: chunk_aa, chunk_ab, chunk_ac, ...

# 3. Move chunks to vault
mv chunk_* context_vault/mission_data/

# 4. Update mission to query multiple chunks
# Or compress file: gzip huge_dataset.csv

# 5. Re-validate
python governance_gate.py --check-context
# ⚠️ WARNING: No files exceed 100MB
```

**Prevention Design:**
- [ ] governance_gate.py warns on files >100MB
- [ ] epos_doctor.py includes context vault size check
- [ ] Automated chunking tool for large datasets
- [ ] Documentation: Best practices for large data handling

**Success Criteria:**
- No vault files exceed 100MB (warning threshold)
- Symbolic search completes in <5 seconds
- System remains responsive under load

---

## SCENARIO CATEGORY 5: INTEGRATION FAILURES

### FS-INTEG-001: governance_gate.py Doesn't Call epos_doctor.py

**Imaginative Projection:**
"What if developer forgets to run epos_doctor.py before validation?"

**Cascade Analysis:**
1. Developer runs governance_gate.py directly
2. Skips epos_doctor.py pre-flight checks
3. Python version is wrong (3.13 instead of 3.11)
4. Ollama service not running
5. governance_gate.py starts anyway
6. Validation logic works
7. But Agent Zero missions will fail later
8. Constitutional requirement (Article III) violated

**Downstream Consequences:**
- **Immediate**: No impact on governance_gate.py itself
- **Short-term**: Environment issues not detected
- **Long-term**: Runtime failures, constitutional drift

**Recovery Procedure:**
```bash
# 1. Detect missing pre-flight
# (User realizes Agent Zero missions failing)

# 2. Run epos_doctor.py manually
python epos_doctor.py
# ❌ FAIL: Python version wrong, Ollama not running

# 3. Fix environment issues
pyenv local 3.11.9
ollama serve &

# 4. Re-validate environment
python epos_doctor.py
# ✅ PASS: All checks passed
```

**Prevention Design:**
- [ ] governance_gate.py MUST call epos_doctor.py at startup
- [ ] No --skip-doctor flag (or requires explicit override with justification)
- [ ] Constitutional enforcement: Pre-flight is NON-NEGOTIABLE

```python
# GOOD PATTERN (in governance_gate.py):
if __name__ == "__main__":
    from epos_doctor import EPOSDoctor
    
    # ALWAYS run pre-flight checks
    doctor = EPOSDoctor(verbose=args.verbose)
    if not doctor.run_all_checks():
        print("❌ Pre-flight checks failed. Fix environment before validation.")
        sys.exit(1)
    
    # Only proceed if environment is healthy
    gate = GovernanceGate()
    gate.run()
```

**Success Criteria:**
- governance_gate.py automatically calls epos_doctor.py
- Pre-flight failures prevent validation
- Constitutional requirement enforced

---

## SCENARIO CATEGORY 6: HUMAN ERROR FAILURES

### FS-HUMAN-001: Developer Bypasses Governance Gate

**Imaginative Projection:**
"What if developer manually copies files to engine/ to skip validation?"

**Cascade Analysis:**
1. Developer frustrated with governance rejections
2. Manually copies broken_module.py to engine/broken_module.py
3. Skips governance_gate.py entirely
4. broken_module.py has relative paths and no header
5. Code appears to work on developer machine
6. Agent Zero mission uses broken_module.py
7. Silent failures in production (wrong config loaded)
8. No audit trail (no rejection receipt, no log)

**Downstream Consequences:**
- **Immediate**: Constitutional drift begins
- **Short-term**: Non-compliant code in production
- **Long-term**: Governance becomes meaningless

**Recovery Procedure:**
```bash
# 1. Periodic audit of engine/ directory
python governance_gate.py --audit-engine

# 2. Non-compliant files detected
# ❌ engine/broken_module.py: ERR-HEADER-001, ERR-PATH-001

# 3. Move back to inbox for re-validation
mv engine/broken_module.py inbox/broken_module.py

# 4. Re-run governance gate
python governance_gate.py
# ❌ REJECTED: broken_module.py (2 violations)

# 5. Developer fixes violations or explains override
```

**Prevention Design:**
- [ ] Periodic audits of engine/ directory (weekly)
- [ ] Git pre-commit hooks block direct writes to engine/
- [ ] CI/CD pipeline rejects non-validated files
- [ ] Constitutional education: Explain WHY governance matters

**Success Criteria:**
- All files in engine/ pass governance validation
- Periodic audits catch any bypass attempts
- Developer understands value of governance

---

## CONCLUSION: PRE-MORTEM SUCCESS

### What We've Accomplished

By documenting these 13 failure scenarios BEFORE implementation, we have:

1. **Prevented Silent Failures**
   - Every scenario has explicit detection and recovery
   - No "it worked yesterday" mysteries

2. **Designed Resilient Systems**
   - Multiple layers of validation (doctor → gate → audit)
   - Graceful degradation where possible

3. **Created Learning Documentation**
   - Educational receipts guide developers to fixes
   - Failure scenarios become reference material

4. **Embedded Constitutional Discipline**
   - Pre-mortem analysis is now THE WAY WE WORK
   - Failures are expected and planned for

### Next Steps

1. **Implementation**: Build governance_gate.py with these scenarios in mind
2. **Testing**: Write test cases for each failure scenario
3. **Validation**: Trigger each failure mode and verify recovery
4. **Documentation**: Keep this document updated as new scenarios discovered

---

**END OF FAILURE SCENARIOS**

*This document is a living artifact - update whenever new failure patterns emerge.*  
*Version: 1.0.0*  
*Created: 2026-01-31*  
*Next Review: After each production failure (to add new scenarios)*
