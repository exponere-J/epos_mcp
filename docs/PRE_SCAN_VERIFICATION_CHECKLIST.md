# PRE-SCAN VERIFICATION CHECKLIST

**Complete validation suite before triggering the first TTLG diagnostic cycle**

---

## CRITICAL: DO NOT SKIP ANY SECTION

This checklist ensures that Friday, Claude Code, and TTLG are properly wired and will execute predictably. Skipping sections will result in failed scans or governance violations.

---

## SECTION 1: ENVIRONMENT HEALTH

### 1.1 Run epos_doctor.py (Manual Verification)

```bash
cd /path/to/epos_mcp
python epos_doctor.py --mode quick
```

**Expected output:**
```
✓ Python 3.11+ detected
✓ All required packages installed
✓ .env file exists and readable
✓ Key directories present
✓ Git repository clean
✓ No untracked critical files
```

**If errors found:**
- [ ] Fix issues before proceeding
- [ ] Re-run epos_doctor.py until all green
- [ ] Document what was fixed
- [ ] Commit changes to git

**Status:** ☐ PASSED

---

### 1.2 Verify Project Structure

```bash
ls -la /path/to/epos_mcp/
```

**Must exist:**
```
✓ .env                                    # Configuration
✓ CLAUDE.md                               # Constitutional charter
✓ CLAUDE_CODE_CHARTER.md                  # Implementation guardrails
✓ FRIDAY_ORCHESTRATION_CHARTER.md         # Decision-making guardrails
✓ FRIDAY_LEARNING_FRAMEWORK.md            # Learning system
✓ AGENTIC_ROLE_MAPPING.md                 # Role definitions
✓ TTLG_SYSTEMS_CYCLE.md                   # Systems diagnostics
✓ TTLG_MARKET_CYCLE.md                    # Market listening
✓ TTLG_MODEL_ROUTING_CHARTER.md           # Model selection rules
✓ TTLG_LOGGING_POLICY.md                  # Audit logging
✓ TTLG_LAUNCH_CHECKLIST.md                # This file's sibling
✓ EPOS_CONSTITUTION_v3.1.md               # Governance rules
✓ NODE_SOVEREIGNTY_CONSTITUTION.md        # Node rules
✓ Coding_Discipline/                      # Development patterns
✓ context_vault/                          # Memory storage
│  ├─ internal_diagnostics/
│  ├─ scans/
│  ├─ patterns/
│  └─ intelligence/
✓ logs/                                   # Audit trail
✓ scripts/                                # Entrypoint scripts
│  ├─ ttlg_systems_light_scout.sh
│  ├─ ttlg_market_light_scout.sh
│  ├─ friday_vault_summary.sh
│  └─ friday_check_ttlg_health.sh
✓ schemas/                                # Data structures
│  └─ aar_v1.json
```

**If missing:**
- [ ] Create missing directories
- [ ] Copy missing charter files
- [ ] Create missing scripts (use templates from ENTRYPOINT_SPECIFICATIONS.md)
- [ ] Verify with `ls -la` again

**Status:** ☐ PASSED

---

## SECTION 2: CONFIGURATION VALIDATION

### 2.1 Verify `.env` API Keys

```bash
source /path/to/epos_mcp/.env
echo "Scout: $SCOUT_PROVIDER - $SCOUT_MODEL"
echo "Thinker: $THINKER_PROVIDER - $THINKER_MODEL"
```

**Must show:**
```
Scout: google - gemini-2.5-flash:free
Thinker: google - gemini-3.1-pro-preview:free
Analyst: google - gemini-2.5-flash:free
```

**If not showing:**
- [ ] Open `.env` and verify SCOUT_PROVIDER, SCOUT_MODEL, etc.
- [ ] Verify OpenRouter API key is set: `echo $OPENROUTER_API_KEY`
- [ ] If API key missing, get it from https://openrouter.ai
- [ ] Update `.env` with correct values

**Status:** ☐ PASSED

---

### 2.2 Test API Connectivity

```bash
# Test OpenRouter connection
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash:free",
    "messages": [{"role": "user", "content": "respond with: OK"}],
    "max_tokens": 10
  }' | jq '.'
```

**Expected response:**
```json
{
  "choices": [
    {"message": {"content": "OK"}}
  ]
}
```

**If error:**
- [ ] Verify API key is correct (no typos, no expiration)
- [ ] Verify network connectivity (`ping openrouter.ai`)
- [ ] Check OpenRouter account status (quotas, rate limits)
- [ ] Try again; if still fails, contact OpenRouter support

**Status:** ☐ PASSED

---

### 2.3 Verify Charter File Integrity

```bash
# Check all charter files are readable and valid
for file in CLAUDE.md CLAUDE_CODE_CHARTER.md FRIDAY_ORCHESTRATION_CHARTER.md \
            FRIDAY_LEARNING_FRAMEWORK.md TTLG_SYSTEMS_CYCLE.md TTLG_MARKET_CYCLE.md; do
  if [ ! -f "$file" ]; then
    echo "MISSING: $file"
  else
    echo "✓ $file"
  fi
done
```

**Expected:**
```
✓ CLAUDE.md
✓ CLAUDE_CODE_CHARTER.md
✓ FRIDAY_ORCHESTRATION_CHARTER.md
... (all present)
```

**If missing:**
- [ ] Copy missing files from `/mnt/user-data/outputs/`
- [ ] Verify all are readable: `head -5 <file>`

**Status:** ☐ PASSED

---

## SECTION 3: GOVERNANCE SETUP

### 3.1 Verify Audit Logging Infrastructure

```bash
# Ensure logs directory exists and is writable
mkdir -p logs
touch logs/test_write.txt && rm logs/test_write.txt
echo "✓ Logs directory writable"

# Check for existing TTLG logs
ls logs/ttlg_diagnostics.jsonl 2>/dev/null || echo "(First run, new log will be created)"
```

**Expected:**
```
✓ Logs directory writable
(First run, new log will be created)
```

**If error:**
- [ ] Fix directory permissions: `chmod 755 logs/`
- [ ] Verify you have write access to logs/

**Status:** ☐ PASSED

---

### 3.2 Verify Context Vault Structure

```bash
# Ensure context vault directories exist
mkdir -p context_vault/internal_diagnostics/aars
mkdir -p context_vault/scans
mkdir -p context_vault/patterns
mkdir -p context_vault/intelligence/market

# Verify structure
find context_vault -type d | sort
```

**Expected:**
```
context_vault
context_vault/internal_diagnostics
context_vault/internal_diagnostics/aars
context_vault/scans
context_vault/patterns
context_vault/intelligence
context_vault/intelligence/market
```

**If not present:**
- [ ] Create directories: commands shown above
- [ ] Verify with `ls -la context_vault/`

**Status:** ☐ PASSED

---

### 3.3 Verify AAR Schema

```bash
# Check that AAR schema is valid JSON
python -m json.tool schemas/aar_v1.json > /dev/null && echo "✓ AAR schema valid"
```

**Expected:**
```
✓ AAR schema valid
```

**If error:**
- [ ] Check schema file syntax: `cat schemas/aar_v1.json | python -m json.tool`
- [ ] Fix JSON errors (missing commas, quotes, etc.)
- [ ] Re-validate

**Status:** ☐ PASSED

---

## SECTION 4: ENTRYPOINT READINESS

### 4.1 Verify Entrypoint Scripts Exist

```bash
# Check all 4 required scripts
for script in ttlg_systems_light_scout \
              ttlg_market_light_scout \
              friday_vault_summary \
              friday_check_ttlg_health; do
  if [ -f "scripts/${script}.sh" ]; then
    echo "✓ $script"
  else
    echo "MISSING: $script"
  fi
done
```

**Expected:**
```
✓ ttlg_systems_light_scout
✓ ttlg_market_light_scout
✓ friday_vault_summary
✓ friday_check_ttlg_health
```

**If missing:**
- [ ] Create scripts from ENTRYPOINT_SPECIFICATIONS.md templates
- [ ] Use provided bash script templates
- [ ] Make executable: `chmod +x scripts/*.sh`

**Status:** ☐ PASSED

---

### 4.2 Verify Entrypoint Scripts Are Executable

```bash
# Check execute permissions
ls -la scripts/*.sh
```

**Expected:**
```
-rwxr-xr-x ... ttlg_systems_light_scout.sh
-rwxr-xr-x ... ttlg_market_light_scout.sh
-rwxr-xr-x ... friday_vault_summary.sh
-rwxr-xr-x ... friday_check_ttlg_health.sh
```

**If not executable:**
- [ ] Make executable: `chmod +x scripts/*.sh`
- [ ] Verify: `ls -la scripts/*.sh`

**Status:** ☐ PASSED

---

### 4.3 Test Entrypoint Signatures

```bash
# Dry-run each script to check syntax
bash -n scripts/ttlg_systems_light_scout.sh && echo "✓ Syntax OK"
bash -n scripts/ttlg_market_light_scout.sh && echo "✓ Syntax OK"
bash -n scripts/friday_vault_summary.sh && echo "✓ Syntax OK"
bash -n scripts/friday_check_ttlg_health.sh && echo "✓ Syntax OK"
```

**Expected:**
```
✓ Syntax OK
✓ Syntax OK
✓ Syntax OK
✓ Syntax OK
```

**If errors:**
- [ ] Check script syntax: `bash -n scripts/<script>.sh`
- [ ] Fix any bash syntax errors
- [ ] Re-test

**Status:** ☐ PASSED

---

## SECTION 5: CLAUDE CODE INTEGRATION

### 5.1 Verify Claude Code Has Project Root Set

**In Claude Code terminal:**
```bash
pwd
# Should output: /path/to/epos_mcp
```

**If not:**
- [ ] Close Claude Code
- [ ] Open Claude Code with Friday root as project: `claude epos_mcp/`
- [ ] Verify pwd shows correct path

**Status:** ☐ PASSED

---

### 5.2 Verify Claude Code Can Read Charters

**In Claude Code:**
```bash
head -5 CLAUDE.md
head -5 CLAUDE_CODE_CHARTER.md
head -5 FRIDAY_ORCHESTRATION_CHARTER.md
```

**Expected:**
```
# CLAUDE.md: TTLG Diagnostic Identity & Charter
...
# CLAUDE CODE CHARTER
...
# FRIDAY ORCHESTRATION CHARTER
...
```

**If missing or unreadable:**
- [ ] Verify files exist: `ls *.md`
- [ ] Verify permissions: `cat CLAUDE.md | head -5`
- [ ] Copy files from `/mnt/user-data/outputs/` if needed

**Status:** ☐ PASSED

---

### 5.3 Verify Claude Code Can Execute Scripts

**In Claude Code:**
```bash
bash scripts/ttlg_systems_light_scout.sh --help 2>/dev/null || echo "Script runs"
```

**Expected:**
```
Script runs
```

**If error:**
- [ ] Check script is executable: `ls -la scripts/ttlg_systems_light_scout.sh`
- [ ] Make executable if needed: `chmod +x scripts/*.sh`

**Status:** ☐ PASSED

---

## SECTION 6: GOVERNANCE VERIFICATION

### 6.1 Verify EPOS Constitution Is Current

```bash
grep "EPOS_CONSTITUTION_v3.1" EPOS_CONSTITUTION_v3.1.md | head -1
```

**Expected:**
```
# EPOS CONSTITUTION v3.1
```

**If not found:**
- [ ] Verify constitution file exists
- [ ] Check version is 3.1 or later

**Status:** ☐ PASSED

---

### 6.2 Verify Governance Gate Logic

```bash
# Check that GOVERNANCE_GATE_APPROVAL_REQUIRED is set
grep "GOVERNANCE_GATE_APPROVAL_REQUIRED" .env
```

**Expected:**
```
GOVERNANCE_GATE_APPROVAL_REQUIRED="true"
```

**If not:**
- [ ] Update `.env` to include this line
- [ ] Set to "true" (no phase 4 without approval)

**Status:** ☐ PASSED

---

### 6.3 Verify Audit Trail Is Immutable

```bash
# Check AUDIT_LOG_IMMUTABLE is set
grep "AUDIT_LOG_IMMUTABLE" .env
```

**Expected:**
```
AUDIT_LOG_IMMUTABLE="true"
```

**If not:**
- [ ] Update `.env` to include this line
- [ ] Set to "true"

**Status:** ☐ PASSED

---

## SECTION 7: LEARNING FRAMEWORK READINESS

### 7.1 Verify Learning Framework Document

```bash
grep "FRIDAY_LEARNING_FRAMEWORK" FRIDAY_LEARNING_FRAMEWORK.md | head -1
```

**Expected:**
```
# FRIDAY LEARNING FRAMEWORK
```

**If not found:**
- [ ] Verify file exists: `ls FRIDAY_LEARNING_FRAMEWORK.md`
- [ ] Check content is present: `wc -l FRIDAY_LEARNING_FRAMEWORK.md`

**Status:** ☐ PASSED

---

### 7.2 Verify Decision Journal Path

```bash
# Check directory for decision journal
ls context_vault/internal_diagnostics/aars/
# Should be empty (first run)
```

**Expected:**
```
(empty directory)
```

**Status:** ☐ PASSED

---

## SECTION 8: FINAL SAFETY CHECKS

### 8.1 Verify Git Status (Clean Baseline)

```bash
git status
```

**Expected:**
```
On branch main
nothing to commit, working tree clean
```

**If not clean:**
- [ ] Commit all changes: `git add -A && git commit -m "Pre-TTLG setup"`
- [ ] Verify clean: `git status`

**Status:** ☐ PASSED

---

### 8.2 Verify Database/Storage Backup (If Applicable)

```bash
# If you have important data in context_vault, back it up
tar -czf context_vault_backup_$(date +%Y%m%d).tar.gz context_vault/
```

**Expected:**
```
(backup file created)
```

**Status:** ☐ PASSED

---

### 8.3 Verify Network Connectivity

```bash
# Test internet connectivity
curl -I https://openrouter.ai/
# Should return 200 or 301
```

**Expected:**
```
HTTP/1.1 200 OK
```

**If fails:**
- [ ] Check internet connectivity
- [ ] Check firewall/proxy settings
- [ ] Verify API endpoint is correct

**Status:** ☐ PASSED

---

### 8.4 Review Logging Policy

```bash
grep "TTLG_LOGGING_POLICY" TTLG_LOGGING_POLICY.md | head -1
```

**Expected:**
```
# TTLG LOGGING POLICY
```

**If missing:**
- [ ] Copy from `/mnt/user-data/outputs/TTLG_LOGGING_POLICY.md`

**Status:** ☐ PASSED

---

## FINAL APPROVAL

### Jamie's Sign-Off (Required)

Before proceeding to the first scan, Jamie must verify and sign off:

- [ ] **All sections passed** (8 sections × all items ✓)
- [ ] **Environment healthy** (epos_doctor.py passed)
- [ ] **Charters understood** (CLAUDE.md, FRIDAY_ORCHESTRATION_CHARTER.md read)
- [ ] **API keys configured** (OpenRouter key present)
- [ ] **Governance rules enforced** (approval gate required, audit immutable)
- [ ] **Learning framework ready** (Friday_LEARNING_FRAMEWORK.md in place)
- [ ] **Entrypoint specs understood** (ENTRYPOINT_SPECIFICATIONS.md reviewed)

**Jamie's approval:**
- [ ] All checks passed
- [ ] Ready to trigger Phase 1 Scout
- [ ] Approval timestamp: ________________
- [ ] Jamie signature: _______________________

---

## NEXT STEP: TRIGGER PHASE 1

Once all sections pass and Jamie approves:

```bash
# Run initial health check
bash scripts/friday_check_ttlg_health.sh

# If healthy, trigger Phase 1 Scout
bash scripts/ttlg_systems_light_scout.sh \
  --targets "governance_gate,context_vault" \
  --scan-id "scan_$(date +%Y%m%d_%H%M%S)" \
  --intensity "light" \
  --timeout-minutes 60 \
  --output-path "./context_vault/scans/scan_initial/scout_output.json"
```

**Monitor output:**
```bash
tail -f logs/ttlg_diagnostics.jsonl
```

---

**CHECKLIST COMPLETE**  
**Status:** 🟢 Ready for Phase 1  
**Next:** Run health check, then trigger Scout

