# File: C:\Users\Jamie\workspace\epos_mcp\EPOS_DOCTOR_UPGRADE_GUIDE.md

# EPOS Doctor v3.1 Upgrade Guide
## What Changed and How to Upgrade

**Created:** 2026-01-25  
**Authority:** EPOS_CONSTITUTION_v3.1.md  
**Purpose:** Document epos_doctor.py changes for v3.1 alignment

---

## EXECUTIVE SUMMARY

`epos_doctor.py` has been upgraded from basic environment validation to **comprehensive constitutional enforcement** with Context Vault validation and flywheel metric tracking.

**Key Changes**:
- ✅ 15 checks (was 10)
- ✅ Context Vault structure validation (NEW)
- ✅ Inline data compliance checking (NEW - Article II Rule 7)
- ✅ Context Handler verification (NEW - Article VII)
- ✅ Flywheel metrics infrastructure (NEW - Strategic)
- ✅ 3-tier exit codes (0=pass, 1=fail, 2=critical)
- ✅ Constitutional document validation (v3.1 required)

---

## WHAT'S NEW IN v3.1

### NEW CHECK 11: Context Vault Structure

**What it validates**:
- `context_vault/` directory exists
- 4 required subdirectories present (mission_data, bi_history, market_sentiment, agent_logs)
- `registry.json` exists and valid
- Registry contains `constitutional_authority` field

**Why it matters**:
- **Flywheel 3 (Data Moat)**: Without vault, can't store large datasets → can't build switching costs
- **Article VII compliance**: Context Vault is constitutional requirement, not optional

**Failure message**:
```
❌ CRITICAL FAIL: Context Vault Structure (Article VII)
   Missing vault subdirectories: mission_data, bi_history
   (Article VII Section 1.2)
```

**Fix**:
```bash
mkdir -p context_vault/{mission_data,bi_history,market_sentiment,agent_logs}

cat > context_vault/registry.json << 'EOF'
{
  "vaults": {},
  "created": "2026-01-25T00:00:00Z",
  "version": "1.0",
  "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
}
EOF
```

---

### NEW CHECK 12: Context Vault Compliance

**What it validates**:
- Scans `engine/` and `inbox/` for `.json` files
- Estimates token count (1 token ≈ 4 characters)
- Flags files >8,192 tokens without `context_vault_path`

**Why it matters**:
- **Article II Rule 7**: "Data >8K tokens MUST use Context Vault"
- **Prevents token overflow**: Catches violations before they hit production
- **Enforces scalability**: Ensures system can handle unlimited data

**Failure message**:
```
❌ FAIL: Context Vault Compliance (Article II Rule 7)
   Inline data violations detected: engine/large_mission.json (12500 tokens)
   (Article II Rule 7)
```

**Fix**:
```bash
# Extract inline data to vault
jq '.market_data' engine/large_mission.json > context_vault/mission_data/market_data.txt

# Update mission to reference vault
jq '.context_vault_path = "context_vault/mission_data/market_data.txt" | del(.market_data)' \
  engine/large_mission.json > temp.json && mv temp.json engine/large_mission.json
```

---

### NEW CHECK 13: Context Handler Available

**What it validates**:
- `context_handler.py` exists in EPOS root
- `ContextVault` class is importable
- RLM symbolic search tools functional

**Why it matters**:
- **Core capability**: Without context_handler, vault is just file storage
- **Article VII Section 2**: ContextVault is required component (C09)
- **Flywheel 3**: Symbolic search enables unlimited context = competitive moat

**Failure message**:
```
❌ FAIL: Context Handler Available (Article VII)
   context_handler.py missing (required for Article VII RLM support)
```

**Fix**:
```bash
# Copy context_handler.py to EPOS root
cp /path/to/downloads/context_handler.py .

# Verify import works
python -c "from context_handler import ContextVault; print('OK')"
```

---

### NEW CHECK 14: Governance Tools Present

**What it validates**:
- `governance_gate.py` exists
- `epos_snapshot.py` exists
- `epos_doctor.py` exists (self-reference)

**Why it matters**:
- **Article III**: Quality gates are constitutional requirement
- **Governance moat**: Without these tools, quality enforcement fails
- **Self-check**: Doctor validates itself is present

**Failure message**:
```
❌ CRITICAL FAIL: Governance Tools Present (Article III)
   Missing governance tools: governance_gate.py
   (Article III enforcement)
```

**Fix**:
```bash
# Copy missing tools to EPOS root
cp /path/to/downloads/governance_gate.py .
cp /path/to/downloads/epos_snapshot.py .
```

---

### NEW CHECK 15: Flywheel Metrics Tracking

**What it validates**:
- `bi_decision_log.json` exists
- Log contains `decisions` array
- Valid JSON format

**Why it matters**:
- **Flywheel 2 (Revenue)**: Track which features customers use → data-driven upsells
- **Article V**: Evidence-based pivots require BI data
- **Strategic analysis**: Prove institutional memory to acquirers

**Failure message**:
```
⚠️  WARN: Flywheel Metrics Tracking
   BI decision log missing: bi_decision_log.json
   (needed for Flywheel 2 revenue tracking)
```

**Fix**:
```bash
cat > bi_decision_log.json << 'EOF'
{
  "version": "1.0",
  "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article V",
  "decisions": []
}
EOF
```

---

### UPDATED CHECK 10: Constitutional Documents

**What changed**:
- Now requires **6 documents** (was 5)
- New requirement: `EPOS_CONSTITUTION_v3.1.md` (not v3.0)

**Required documents**:
1. `EPOS_CONSTITUTION_v3.1.md` ← NEW version requirement
2. `ENVIRONMENT_SPEC.md`
3. `COMPONENT_INTERACTION_MATRIX.md`
4. `FAILURE_SCENARIOS.md`
5. `PATH_CLARITY_RULES.md`
6. `PRE_FLIGHT_CHECKLIST.md`

**Why it matters**:
- **Constitutional continuity**: v3.1 merges Pre-Mortem + Context governance
- **Single source of truth**: All agents reference same constitutional version

**Failure message**:
```
❌ CRITICAL FAIL: Constitutional Documents (Article I)
   Missing constitutional documents: EPOS_CONSTITUTION_v3.1.md
   (Article I requires 5+1 documents)
```

**Fix**:
```bash
# Download v3.1 constitution
cp /path/to/downloads/EPOS_CONSTITUTION_v3.1.md .
```

---

## EXIT CODE CHANGES

### v3.0 Exit Codes
- `0`: All checks passed
- `1`: Checks failed

### v3.1 Exit Codes (NEW)
- `0`: All checks passed (proceed with execution)
- `1`: Checks failed (fix before proceeding)
- `2`: **Critical constitutional violation** (immediate human intervention required)

**Critical violations trigger exit code 2**:
- Python version wrong (Article II Rule 3)
- EPOS root missing (Article II Rule 1)
- Constitutional documents missing (Article I)
- Required directories missing (Article VII)
- Context Vault structure invalid (Article VII)
- Governance tools missing (Article III)

**Why 3 levels matter**:
- **Exit 0**: Automation proceeds (CI/CD green light)
- **Exit 1**: Automation waits (fix in development)
- **Exit 2**: Human escalation (constitutional crisis, not just bug)

---

## NEW CLI OPTIONS

### `--check-context`

**Purpose**: Validate Context Vault only (fast check)

**Usage**:
```bash
python epos_doctor.py --check-context
```

**Output**:
```
Context Vault Validation:
  Structure: ✅ Context Vault structure valid (4 subdirs + registry)
  Compliance: ✅ No inline data >8K tokens detected
  Handler: ✅ Context Handler functional (ContextVault importable)
```

**When to use**:
- After migrating data to vault
- Before deploying Context Vault-dependent features
- Verifying Article VII compliance

---

### `--cron`

**Purpose**: Daily health check mode (brief output for logs)

**Usage**:
```bash
# Add to cron/scheduled task
0 8 * * * cd /path/to/epos_mcp && python epos_doctor.py --cron >> ops/logs/daily_health.log 2>&1
```

**Output (success)**:
```
(no output if all pass)
```

**Output (failure)**:
```
EPOS Health: DEGRADED (3 failures)
```

**Why it matters**:
- **Continuous monitoring**: Catch drift before it compounds
- **Alerting**: Brief output easy to parse for alerts
- **Audit trail**: Daily snapshots in logs

---

## UPGRADE PROCEDURE

### Step 1: Backup Current Doctor (1 min)

```bash
cd C:\Users\Jamie\workspace\epos_mcp

# Backup old version
cp epos_doctor.py epos_doctor_v3.0_backup.py
```

---

### Step 2: Deploy v3.1 Doctor (1 min)

```bash
# Download from outputs
cp /path/to/downloads/epos_doctor_v3.1.py epos_doctor.py

# Verify version
head -5 epos_doctor.py | grep "v3.1"
# Should see: EPOS Doctor v3.1
```

---

### Step 3: Create Missing Infrastructure (5 min)

```bash
# Create Context Vault structure (if missing)
mkdir -p context_vault/{mission_data,bi_history,market_sentiment,agent_logs}

# Create registry
cat > context_vault/registry.json << 'EOF'
{
  "vaults": {},
  "created": "2026-01-25T00:00:00Z",
  "version": "1.0",
  "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
}
EOF

# Create BI log (if missing)
cat > bi_decision_log.json << 'EOF'
{
  "version": "1.0",
  "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article V",
  "decisions": []
}
EOF

# Ensure governance tools present
# (download if missing: governance_gate.py, epos_snapshot.py)
```

---

### Step 4: Run First v3.1 Validation (2 min)

```bash
# Run full validation
python epos_doctor.py --verbose

# Expected output:
# 🏥 EPOS ENVIRONMENT DIAGNOSTIC v3.1
# Constitutional Authority: EPOS_CONSTITUTION_v3.1.md
# ...
# ✅ Passed: 15
# ⚠️  Warnings: 0
# ❌ Failed: 0
# 🎉 ENVIRONMENT VALIDATED - Ready for operations
```

---

### Step 5: Fix Any Failures (variable)

**Common failures on first run**:

**Failure: Context Vault Structure**
```bash
mkdir -p context_vault/{mission_data,bi_history,market_sentiment,agent_logs}
cat > context_vault/registry.json << 'EOF'
{
  "vaults": {},
  "created": "2026-01-25T00:00:00Z",
  "version": "1.0",
  "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
}
EOF
```

**Failure: Context Vault Compliance**
```bash
# Find violating files
python epos_doctor.py --check-context

# For each violation, extract to vault
# Example:
jq '.large_data' engine/mission.json > context_vault/mission_data/data.txt
jq '.context_vault_path = "context_vault/mission_data/data.txt" | del(.large_data)' \
  engine/mission.json > temp.json && mv temp.json engine/mission.json
```

**Failure: Missing v3.1 Constitution**
```bash
cp /path/to/downloads/EPOS_CONSTITUTION_v3.1.md .
```

---

### Step 6: Verify Upgrade Success (1 min)

```bash
# Run validation with JSON output
python epos_doctor.py --json | jq

# Check compliance rate
python epos_doctor.py --json | jq '.compliance_rate'
# Target: 1.0 (100%)

# Check constitutional version
python epos_doctor.py --json | jq '.constitutional_version'
# Expected: "v3.1"
```

---

## MIGRATION CHECKLIST

Use this to track upgrade progress:

- [ ] **Backup**: Old epos_doctor.py saved as `epos_doctor_v3.0_backup.py`
- [ ] **Deploy**: v3.1 doctor copied to `epos_doctor.py`
- [ ] **Context Vault**: 4 subdirectories created
- [ ] **Registry**: `context_vault/registry.json` created with constitutional authority
- [ ] **BI Log**: `bi_decision_log.json` created
- [ ] **Constitution**: `EPOS_CONSTITUTION_v3.1.md` present
- [ ] **Governance Tools**: `governance_gate.py` and `epos_snapshot.py` present
- [ ] **Context Handler**: `context_handler.py` present and importable
- [ ] **First Run**: `python epos_doctor.py` returns exit code 0
- [ ] **Compliance**: No inline data >8K tokens detected
- [ ] **Cron Setup**: Daily health check configured (optional)

---

## INTEGRATION WITH GOVERNANCE GATE

**Important**: `governance_gate.py` should call `epos_doctor.py` before processing files.

**Update governance_gate.py** (if needed):

```python
# File: C:\Users\Jamie\workspace\epos_mcp\governance_gate.py

from epos_doctor import EPOSDoctor

def main():
    # Pre-flight check before governance processing
    doctor = EPOSDoctor(silent=True)
    if not doctor.run_all_checks():
        print("❌ Pre-flight checks failed. Fix environment before running gate.")
        print("Run: python epos_doctor.py --verbose")
        sys.exit(1)
    
    # Continue with governance triage...
```

---

## INTEGRATION WITH META-ORCHESTRATOR

**Update meta_orchestrator.py** (if needed):

```python
# File: C:\Users\Jamie\workspace\epos_mcp\engine\meta_orchestrator.py

from epos_doctor import EPOSDoctor

# CONSTITUTIONAL REQUIREMENT: Pre-flight (Article III)
doctor = EPOSDoctor()
if not doctor.validate():
    raise EnvironmentError(
        "Pre-flight checks failed - see epos_doctor output\n"
        "Run: python epos_doctor.py --verbose"
    )
```

---

## TROUBLESHOOTING

### Issue: "EPOS_CONSTITUTION_v3.1.md not found"

**Cause**: Still have v3.0 constitution

**Fix**:
```bash
# Download v3.1
cp /path/to/downloads/EPOS_CONSTITUTION_v3.1.md .

# Verify
ls EPOS_CONSTITUTION_v3.1.md
```

---

### Issue: "Context Vault registry missing"

**Cause**: Missing `context_vault/registry.json`

**Fix**:
```bash
cat > context_vault/registry.json << 'EOF'
{
  "vaults": {},
  "created": "2026-01-25T00:00:00Z",
  "version": "1.0",
  "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
}
EOF
```

---

### Issue: "Inline data violations detected"

**Cause**: Files in `engine/` or `inbox/` have >8K tokens inline

**Fix**:
```bash
# Find violating file
python epos_doctor.py --check-context

# Extract data to vault
jq '.data_field' path/to/file.json > context_vault/mission_data/extracted.txt

# Update file to reference vault
jq '.context_vault_path = "context_vault/mission_data/extracted.txt" | del(.data_field)' \
  path/to/file.json > temp.json && mv temp.json path/to/file.json

# Re-run check
python epos_doctor.py --check-context
```

---

### Issue: "Context Handler import failed"

**Cause**: `context_handler.py` missing or broken

**Fix**:
```bash
# Download context_handler.py
cp /path/to/downloads/context_handler.py .

# Test import
python -c "from context_handler import ContextVault; print('OK')"

# If still fails, check for dependency issues
pip install --upgrade pathlib
```

---

## COMPARISON TABLE

| Feature | v3.0 | v3.1 |
|---------|------|------|
| Total checks | 10 | 15 |
| Context Vault validation | ❌ No | ✅ Yes |
| Inline data compliance | ❌ No | ✅ Yes |
| Constitutional version | Any v3 | v3.1 only |
| Exit codes | 2 (0/1) | 3 (0/1/2) |
| Flywheel metrics | ❌ No | ✅ Yes |
| `--check-context` option | ❌ No | ✅ Yes |
| `--cron` mode | ❌ No | ✅ Yes |
| Strategic alignment | Basic | Complete |

---

## EXPECTED OUTCOMES AFTER UPGRADE

### Immediate (Day 1)
- ✅ 15 checks validated (was 10)
- ✅ Context Vault compliance enforced
- ✅ Constitutional v3.1 alignment verified
- ✅ 3-tier exit codes operational

### Week 1
- ✅ No inline data violations (all migrated to vault)
- ✅ Daily health checks running via cron
- ✅ Governance gate integrates v3.1 doctor
- ✅ Meta-orchestrator pre-flight checks operational

### Month 1
- ✅ Context Vault contains mission data (Flywheel 3 starting)
- ✅ BI decision log tracking improvements (Flywheel 2 data)
- ✅ Zero constitutional violations (95%+ compliance)
- ✅ Developer onboarding faster (doctor teaches constitutional law)

---

## SUPPORT

**Documentation**:
- `EPOS_CONSTITUTION_v3.1.md` - The unified law
- `SPRINT_EXECUTION_GUIDE_v3.md` - Implementation steps
- `EPOS_STRATEGIC_ANALYSIS.md` - Why these changes matter

**Commands**:
```bash
python epos_doctor.py                    # Full validation
python epos_doctor.py --verbose          # Detailed output
python epos_doctor.py --check-context    # Context Vault only
python epos_doctor.py --json             # Machine-readable output
python epos_doctor.py --cron             # Daily health check
```

**Status Check**:
```bash
# Quick validation
python epos_doctor.py --json | jq '{version: .constitutional_version, passed: .passed, failed: .failed, compliance: .compliance_rate}'
```

---

**END OF UPGRADE GUIDE**

*Created: 2026-01-25*  
*Constitutional Authority: EPOS_CONSTITUTION_v3.1.md*  
*Version: epos_doctor.py v3.1*