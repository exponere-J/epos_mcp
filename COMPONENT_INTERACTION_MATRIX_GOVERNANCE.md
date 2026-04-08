# File: C:\Users\Jamie\workspace\epos_mcp\COMPONENT_INTERACTION_MATRIX_GOVERNANCE.md

# COMPONENT INTERACTION MATRIX
## Governance Gate Subsystem Specification

**Created:** 2026-01-31  
**Constitutional Authority:** EPOS_CONSTITUTION_v3.1.md Article I  
**Scope:** Governance Gate and related validation components  
**Purpose:** Define dependencies, data flows, and failure modes for governance subsystem

---

## OVERVIEW: The Governance Triangle

```
                    EPOS_CONSTITUTION_v3.1.md
                            (THE LAW)
                                 |
                                 |
                     +-----------+-----------+
                     |                       |
            epos_doctor.py              governance_gate.py
         (HEALTH VALIDATOR)              (CODE ARBITER)
                     |                       |
                     |                       |
                     +----------+------------+
                                |
                          EPOS CODEBASE
                       (FILES TO VALIDATE)
```

**Core Principle:**  
The Constitution is law, epos_doctor validates the environment, governance_gate validates the code, and all three must align for the system to be trustworthy.

---

## COMPONENT 1: EPOS_CONSTITUTION_v3.1.md

### What It Is
The supreme governing document defining all rules, boundaries, and requirements for EPOS operations.

### Inputs
- Constitutional amendments (human-approved only)
- Version history from prior constitutions

### Outputs
- Article specifications (Article I through XI)
- Rule definitions (Article II: 7 Hard Boundaries)
- Violation code specifications (cross-referenced with VIOLATION_CODES.json)

### Dependencies
- **None** (Constitution is foundational)

### Dependents
- epos_doctor.py (enforces Article III)
- governance_gate.py (enforces Article II)
- All EPOS components (must comply with all Articles)

### Failure Modes

| Failure | Symptom | Impact | Recovery |
|---------|---------|--------|----------|
| **Constitution Missing** | File not found at EPOS_ROOT | All governance fails, no validation possible | Immediate STASIS, restore from backup |
| **Version Mismatch** | Code references v3.0, file is v3.1 | Enforcement diverges from specification | Update all references to v3.1 |
| **Internal Contradictions** | Article II contradicts Article VII | Impossible to comply with both rules | Human constitutional review required |
| **Incomplete Article** | Article VII missing Section 4 | Enforcement gaps, undefined behavior | Amendment to complete article |

### Data Format
```yaml
Format: Markdown
Size: ~30KB (866 lines)
Encoding: UTF-8
Location: C:\Users\Jamie\workspace\epos_mcp\EPOS_CONSTITUTION_v3.1.md
```

### Validation Tests
- [ ] File exists at expected path
- [ ] First line contains "# EPOS CONSTITUTION v3.1"
- [ ] All 11 Articles present (I through XI)
- [ ] Article II contains 7 rules
- [ ] Article VII contains Context Vault specification
- [ ] Version number in header matches filename

---

## COMPONENT 2: epos_doctor.py

### What It Is
Comprehensive environment and dependency validator that runs before any EPOS execution.

### Inputs
- EPOS_ROOT environment variable or default path
- AGENT_ZERO_PATH environment variable
- System environment (Python version, Ollama service, ports)
- Constitutional documents (to validate their presence)

### Outputs
- Exit code 0: All checks pass, proceed with execution
- Exit code 1: Non-critical failures detected, fix recommended
- Exit code 2: Critical constitutional violation, immediate intervention required
- JSON report (with --json flag)
- Console output with ✅/❌/⚠️ indicators

### Dependencies
- Python 3.11+ (self-validates)
- pathlib (stdlib)
- socket (stdlib)
- subprocess (stdlib)
- python-dotenv (optional, graceful degradation if missing)
- EPOS_CONSTITUTION_v3.1.md (validates presence)
- VIOLATION_CODES.json (if present, validates structure)

### Dependents
- governance_gate.py (should call doctor before validation)
- All entrypoint scripts (Article III requirement)
- CI/CD pipelines (automated validation)

### Failure Modes

| Failure | Symptom | Impact | Recovery |
|---------|---------|--------|----------|
| **Python Version Wrong** | sys.version_info < (3, 11) | Exit code 2, immediate termination | Install Python 3.11+ |
| **EPOS_ROOT Missing** | Directory doesn't exist | Exit code 2, cannot proceed | Create directory or fix path |
| **Agent Zero Not Found** | AGENT_ZERO_PATH invalid | Exit code 1, Agent Zero functions fail | Install Agent Zero or fix path |
| **Ollama Not Running** | Port 11434 not responding | Exit code 1, AI functions unavailable | Start Ollama service |
| **Log Dir Not Writable** | Permission denied on ops/logs | Exit code 2, audit trail impossible | Fix permissions or create directory |
| **Constitutional Docs Missing** | Required .md files absent | Exit code 2, governance impossible | Restore constitutional documents |
| **Context Vault Missing** | context_vault/ doesn't exist | Exit code 1, large data handling fails | Create context vault structure |

### Data Format
```python
# Input: Command line flags
--verbose: Detailed output
--json: Machine-readable output
--check-constitution: Only validate constitutional docs
--check-context: Only validate Context Vault
--cron: Silent mode for automated runs

# Output: JSON structure
{
  "timestamp": "ISO8601",
  "exit_code": 0|1|2,
  "checks_passed": 10,
  "checks_failed": 0,
  "checks_warned": 0,
  "failures": [],
  "warnings": [],
  "environment": {...}
}
```

### Integration Points
```python
# How governance_gate.py should call doctor:
if __name__ == "__main__":
    from epos_doctor import EPOSDoctor
    
    doctor = EPOSDoctor(verbose=False)
    passed = doctor.run_all_checks()
    
    if not passed:
        print("❌ Environment validation failed")
        sys.exit(1)
    
    # Proceed with governance gate logic...
```

### Validation Tests
- [ ] Detects Python < 3.11 and exits with code 2
- [ ] Validates EPOS_ROOT exists
- [ ] Checks all 6 constitutional documents present
- [ ] Verifies context_vault/ directory structure
- [ ] Tests Ollama connectivity on port 11434
- [ ] Confirms log directories writable
- [ ] JSON output is valid and complete

---

## COMPONENT 3: governance_gate.py

### What It Is
The automated code validator that enforces EPOS_CONSTITUTION_v3.1.md Article II rules through pattern matching and structural analysis.

### Inputs
- Files in inbox/ directory (pending validation)
- VIOLATION_CODES.json (violation specifications)
- EPOS_CONSTITUTION_v3.1.md (constitutional authority)
- Command line flags (--dry-run, --verbose, --auto-fix, --check-context)

### Outputs
- **Promoted Files:** Moved to engine/ if compliant
- **Rejected Files:** Moved to rejected/ if non-compliant
- **Educational Receipts:** Written to rejected/receipts/ with fix guidance
- **Compliance Report:** JSON summary of validation results
- **Console Output:** Detailed validation logs
- **Exit Code:** 0 if successful, 1 if errors

### Dependencies
- epos_doctor.py (should run first for environment validation)
- VIOLATION_CODES.json (violation pattern specifications)
- EPOS_CONSTITUTION_v3.1.md (rule definitions)
- pathlib (stdlib)
- re (stdlib for regex pattern matching)
- json (stdlib for config loading)

### Dependents
- Sprint execution workflow (Phase 1.5)
- CI/CD integration (automated validation)
- Human developers (manual submission to inbox/)
- Agent Zero (future: autonomous code submission)

### Failure Modes

| Failure | Symptom | Impact | Recovery |
|---------|---------|--------|----------|
| **VIOLATION_CODES.json Missing** | FileNotFoundError | Cannot validate files | Restore VIOLATION_CODES.json |
| **inbox/ Directory Missing** | DirectoryNotFoundError | No files to validate | Create inbox/ directory |
| **Regex Compile Error** | re.error exception | Specific validation fails | Fix regex in VIOLATION_CODES.json |
| **False Positive** | Compliant file rejected | Blocks valid code | Adjust detection pattern, --override |
| **False Negative** | Violating file promoted | Constitutional drift | Strengthen validation patterns |
| **Receipt Write Failure** | Permission denied | No audit trail for rejection | Fix permissions on rejected/receipts/ |
| **Context Vault File Missing** | Ref'd file doesn't exist | ERR-CONTEXT-002 violation | Create file or fix reference |
| **Token Count Overflow** | Data > 8K tokens inline | ERR-CONTEXT-001 violation | Move to context vault |

### Data Flow

```
INPUT: inbox/my_module.py
   |
   v
[Read file content]
   |
   v
[Check ERR-HEADER-001: File header present?]
   |
   +--NO--> [Generate receipt] --> rejected/receipts/my_module_2026-01-31_143022.md
   |
   +--YES--> [Check ERR-PATH-001: Absolute paths used?]
             |
             +--NO--> [Generate receipt] --> rejected/
             |
             +--YES--> [Check ERR-CONTEXT-001: Data < 8K tokens?]
                       |
                       +--NO--> [Generate receipt] --> rejected/
                       |
                       +--YES--> [ALL CHECKS PASS]
                                  |
                                  v
                              [Promote to engine/]
                                  |
                                  v
                              OUTPUT: engine/my_module.py
```

### Validation Tests
- [ ] Detects missing file headers (ERR-HEADER-001)
- [ ] Detects relative paths (ERR-PATH-001)
- [ ] Detects inline data > 8K tokens (ERR-CONTEXT-001)
- [ ] Detects missing vault files (ERR-CONTEXT-002)
- [ ] Detects missing pre-flight checks (ERR-ENTRYPOINT-001)
- [ ] Generates educational receipts for rejections
- [ ] Produces valid compliance_report.json
- [ ] --dry-run doesn't move any files
- [ ] --auto-fix adds headers correctly

---

## COMPONENT 4: VIOLATION_CODES.json

### What It Is
Structured registry of all constitutional violation codes with detection patterns, examples, and remediation guidance.

### Inputs
- Constitutional amendment process (when new rules added)
- Field experience (when new violation patterns discovered)

### Outputs
- Violation code definitions (ERR-HEADER-001 through ERR-DESTRUCTIVE-002)
- Detection patterns (regex, methods)
- Example violations and fixes
- Severity classifications
- Auto-fix specifications

### Dependencies
- **None** (Configuration file)

### Dependents
- governance_gate.py (reads violations for validation)
- Educational receipt generator (formats violation explanations)
- Compliance reporting (categorizes violations)

### Failure Modes

| Failure | Symptom | Impact | Recovery |
|---------|---------|--------|----------|
| **File Missing** | FileNotFoundError | governance_gate.py cannot validate | Restore from backup or regenerate |
| **Invalid JSON** | json.JSONDecodeError | governance_gate.py crashes on load | Fix JSON syntax |
| **Invalid Regex** | re.error when compiling pattern | Specific validation disabled | Fix regex syntax in pattern |
| **Missing Violation Code** | KeyError when looking up violation | Error in receipt generation | Add missing violation definition |

### Data Format
```json
{
  "violations": {
    "ERR-HEADER-001": {
      "code": "ERR-HEADER-001",
      "category": "HEADER",
      "severity": "critical",
      "constitutional_reference": "Article II Rule 1",
      "detection_pattern": "regex_pattern",
      "example_violation": "string",
      "example_fix": "string",
      "remediation": "string",
      "auto_fixable": true|false
    }
  }
}
```

### Validation Tests
- [ ] File is valid JSON
- [ ] All violation codes follow ERR-CATEGORY-NNN format
- [ ] All regex patterns compile without errors
- [ ] All constitutional references are valid
- [ ] All severity levels are valid (critical|high|medium|low)

---

## COMPONENT 5: context_vault/

### What It Is
Directory structure for storing large datasets (>8K tokens) that are referenced symbolically rather than loaded inline.

### Inputs
- Large mission data (mission_data/)
- Business intelligence history (bi_history/)
- Market sentiment aggregations (market_sentiment/)
- Agent execution logs (agent_logs/)

### Outputs
- Symbolic references (file paths, not content)
- Regex search results (context_handler.py)
- Registry metadata (context_vault/registry.json)

### Dependencies
- File system (directories and files)
- context_handler.py (symbolic search tool)

### Dependents
- governance_gate.py (validates vault references)
- Mission execution (loads data symbolically)
- Context-aware agents (query vault without full load)

### Failure Modes

| Failure | Symptom | Impact | Recovery |
|---------|---------|--------|----------|
| **Directory Missing** | DirectoryNotFoundError | Cannot store large data | Create context_vault/ structure |
| **File Too Large (>100MB)** | Performance degradation | Slow symbolic search | Split file or compress |
| **Invalid Registry** | JSON parse error | Cannot track vault contents | Regenerate registry.json |
| **Ref'd File Missing** | FileNotFoundError on query | Mission fails | Create file or update reference |

### Data Format
```
context_vault/
  ├── mission_data/         # Mission-specific datasets
  ├── bi_history/           # Business intelligence logs
  ├── market_sentiment/     # Aggregated feedback
  ├── agent_logs/           # Execution logs
  └── registry.json         # Vault file metadata
```

### Validation Tests
- [ ] All subdirectories exist
- [ ] registry.json is valid JSON
- [ ] No files exceed 100MB (warning threshold)
- [ ] All files referenced in code exist in vault

---

## INTERACTION SEQUENCES

### Sequence 1: File Submission to Governance Gate

```
1. Developer writes new_module.py
2. Developer copies to inbox/new_module.py
3. Developer runs: python governance_gate.py --verbose
4. governance_gate.py calls epos_doctor.py for environment check
5. epos_doctor.py validates Python version, paths, constitutional docs
6. epos_doctor.py returns exit code 0 (all pass)
7. governance_gate.py loads VIOLATION_CODES.json
8. governance_gate.py reads inbox/new_module.py
9. governance_gate.py runs validation checks:
   - ERR-HEADER-001: Header present? YES
   - ERR-PATH-001: Absolute paths used? YES
   - ERR-CONTEXT-001: Data < 8K tokens? YES
   - ERR-ENTRYPOINT-001: Doctor check present? YES
10. governance_gate.py promotes file to engine/new_module.py
11. governance_gate.py updates compliance_report.json
12. governance_gate.py prints ✅ PROMOTED: new_module.py
```

### Sequence 2: File Rejection with Educational Receipt

```
1. Developer writes broken_module.py (no header, relative paths)
2. Developer copies to inbox/broken_module.py
3. Developer runs: python governance_gate.py
4. governance_gate.py validates environment (epos_doctor.py)
5. governance_gate.py reads inbox/broken_module.py
6. governance_gate.py detects violations:
   - ERR-HEADER-001: Missing header
   - ERR-PATH-001: Relative path detected
7. governance_gate.py generates receipt:
   - Header: "Constitutional Violation Receipt"
   - Lists violations with examples and fixes
   - Provides step-by-step remediation
8. governance_gate.py writes rejected/receipts/broken_module_2026-01-31_143022.md
9. governance_gate.py moves inbox/broken_module.py to rejected/broken_module.py
10. governance_gate.py updates compliance_report.json
11. governance_gate.py prints ❌ REJECTED: broken_module.py (2 violations)
```

### Sequence 3: Context Vault Integration

```
1. Developer writes analysis_mission.json with large dataset inline
2. governance_gate.py detects ERR-CONTEXT-001 (data > 8K tokens)
3. Developer moves data to context_vault/mission_data/dataset.txt
4. Developer updates mission: "context_vault_path": "context_vault/mission_data/dataset.txt"
5. governance_gate.py validates:
   - Data inline? NO
   - Vault path present? YES
   - Vault file exists? YES
   - File size < 100MB? YES
6. governance_gate.py promotes analysis_mission.json to engine/
```

---

## DEPENDENCY GRAPH

```
EPOS_CONSTITUTION_v3.1.md (no dependencies)
      ↓
      ├──→ epos_doctor.py (reads constitution)
      │         ↓
      │         └──→ governance_gate.py (calls doctor, reads constitution)
      │                   ↓
      │                   ├──→ VIOLATION_CODES.json (loaded by gate)
      │                   └──→ context_vault/ (validated by gate)
      │
      └──→ All EPOS Components (must comply)
```

**Critical Path:**  
Constitution → Doctor → Gate → Codebase

**Failure Propagation:**  
If Constitution missing → Doctor fails → Gate cannot run → No validation possible

---

## PERFORMANCE SPECIFICATIONS

| Component | Target Performance | Measured By | Acceptable Range |
|-----------|-------------------|-------------|------------------|
| epos_doctor.py | <5 seconds for full check | Time from start to exit | 0-10 seconds |
| governance_gate.py | <5 seconds per file | Time per validation | 0-10 seconds |
| VIOLATION_CODES.json | Instant load | JSON parse time | <100ms |
| context_vault/ query | <1 second per search | Regex search time | 0-5 seconds |

---

## TESTING STRATEGY

### Unit Tests
- [ ] epos_doctor.py: Each check function individually
- [ ] governance_gate.py: Each violation detection separately
- [ ] VIOLATION_CODES.json: Schema validation
- [ ] context_vault/: File operations and registry

### Integration Tests
- [ ] Full governance flow: inbox → gate → engine
- [ ] Rejection flow: inbox → gate → rejected with receipt
- [ ] Doctor → Gate integration
- [ ] Context vault reference validation

### End-to-End Tests
- [ ] Submit 10 files, verify promotion/rejection rates
- [ ] Measure compliance rate calculation accuracy
- [ ] Validate educational receipt completeness
- [ ] Test auto-fix capabilities

---

## CONCLUSION

This Component Interaction Matrix defines the governance subsystem's architecture, dependencies, and failure modes. Every component has:

1. **Clear Inputs/Outputs** - No ambiguity in data flow
2. **Explicit Dependencies** - Know what breaks if X fails
3. **Documented Failure Modes** - Pre-mortem discipline applied
4. **Validation Tests** - How we verify it works
5. **Integration Points** - How components communicate

**Next Steps:**
1. Implement governance_gate.py per this specification
2. Write test suite covering all failure modes
3. Validate against Sprint Execution Guide v3 requirements
4. Execute Phase 1-6 per GOVERNANCE_GATE_ALIGNMENT_PLAN.md

---

**END OF COMPONENT INTERACTION MATRIX**

*Version: 1.0.0*  
*Created: 2026-01-31*  
*Next Review: After governance_gate.py implementation*
