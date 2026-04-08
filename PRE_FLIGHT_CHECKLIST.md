# File: C:\Users\Jamie\workspace\epos_mcp\PRE_FLIGHT_CHECKLIST.md

# PRE-FLIGHT CHECKLIST
## Mandatory Validation Before Execution (Constitutional Document #5)

**Authority:** EPOS Constitution v3.0, Article III  
**Last Updated:** 2026-01-24  
**Purpose:** Prevent failures through systematic validation

---

## WHEN TO USE THIS CHECKLIST

**Run BEFORE:**
- Starting any EPOS service
- Deploying new code to production
- Executing any mission
- Making constitutional amendments
- Integrating new vendors
- Major configuration changes

**Do NOT skip** - this checklist embodies Pre-Mortem Discipline.

---

## PHASE 1: ENVIRONMENT VALIDATION (5 minutes)

### Step 1.1: Python Version Check
```bash
python --version
```

**Expected**: `Python 3.11.7` (or 3.11.8, 3.11.9)  
**If not**: Install Python 3.11.x from python.org  
**Why critical**: Wrong version breaks dependencies

☐ **Python 3.11.x confirmed**

---

### Step 1.2: EPOS Root Verification
```bash
cd C:\Users\Jamie\workspace\epos_mcp
pwd
```

**Expected**: `C:\Users\Jamie\workspace\epos_mcp` (or `/c/Users/Jamie/workspace/epos_mcp` in Git Bash)  
**If not**: Clone repository or fix path  
**Why critical**: All operations assume this root

☐ **EPOS root exists and accessible**

---

### Step 1.3: Agent Zero Path Verification
```bash
ls C:\Users\Jamie\workspace\agent-zero\python\agent.py
```

**Expected**: File exists  
**If not**: Clone Agent Zero or update `.env`  
**Why critical**: Bridge cannot function without Agent Zero

☐ **Agent Zero path valid**

---

### Step 1.4: Directory Structure Check
```bash
ls -la C:\Users\Jamie\workspace\epos_mcp
```

**Expected directories**:
- `engine/` - Production code
- `inbox/` - Pending submissions
- `rejected/` - Failed governance
- `logs/` - All logs
- `docs/` - Documentation

**If missing**: Create directories
```bash
mkdir -p engine inbox rejected logs docs tests
```

☐ **Required directories present**

---

## PHASE 2: CONFIGURATION VALIDATION (3 minutes)

### Step 2.1: .env File Exists
```bash
ls C:\Users\Jamie\workspace\epos_mcp\.env
```

**Expected**: File exists  
**If not**: Copy from `.env.example` and populate  
**Why critical**: All environment variables come from here

☐ **.env file exists**

---

### Step 2.2: .env Syntax Check
```bash
cat .env | grep -v '^#' | grep '='
```

**Expected**: Valid `KEY=VALUE` lines, no syntax errors  
**If not**: Fix malformed lines  
**Common errors**:
- `KEY = VALUE` (spaces around `=`)
- `KEY="VALUE WITH SPACE"` (use `KEY=VALUE\ WITH\ SPACE`)

☐ **.env syntax valid**

---

### Step 2.3: Required Environment Variables
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('EPOS_ROOT:', os.getenv('EPOS_ROOT')); print('AGENT_ZERO_PATH:', os.getenv('AGENT_ZERO_PATH'))"
```

**Expected**:
```
EPOS_ROOT: C:/Users/Jamie/workspace/epos_mcp
AGENT_ZERO_PATH: C:/Users/Jamie/workspace/agent-zero
```

**If not**: Add missing variables to `.env`

**Required variables**:
- `EPOS_ROOT`
- `EPOS_WORKSPACE`
- `AGENT_ZERO_PATH`
- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `LOG_LEVEL`

☐ **All required environment variables set**

---

## PHASE 3: DEPENDENCY VALIDATION (5 minutes)

### Step 3.1: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected**: All packages installed successfully  
**If errors**: Check Python version, resolve conflicts  
**Common issues**:
- Flask 3.0.3 (doesn't exist) → Use 3.0.0
- C extension build failures → Install Visual C++ Build Tools

☐ **All dependencies installed**

---

### Step 3.2: Dependency Health Check
```bash
pip check
```

**Expected**: `No broken requirements found.`  
**If errors**: Fix dependency conflicts  
**Why critical**: Broken dependencies cause runtime failures

☐ **Dependency integrity validated**

---

### Step 3.3: Import Critical Modules
```bash
python -c "from pathlib import Path; from dotenv import load_dotenv; import fastapi; import uvicorn; import pydantic; print('Imports successful')"
```

**Expected**: `Imports successful`  
**If errors**: Reinstall failing package  
**Why critical**: Verifies packages are usable

☐ **Critical imports validated**

---

## PHASE 4: SERVICE VALIDATION (5 minutes)

### Step 4.1: Ollama Service Check
```bash
curl http://localhost:11434/api/tags
```

**Expected**: JSON response with models list  
**If not**: Start Ollama
```bash
ollama serve &
```

**Why critical**: LLM backend required for missions

☐ **Ollama service running**

---

### Step 4.2: Ollama Model Check
```bash
ollama list | grep llama3.2
```

**Expected**: `llama3.2:latest` (or configured model)  
**If not**: Pull model
```bash
ollama pull llama3.2:latest
```

☐ **Required LLM model available**

---

### Step 4.3: Docker Desktop Check (Optional)
```bash
docker ps
```

**Expected**: No errors (service running)  
**If errors**: Start Docker Desktop  
**Why critical**: Future MCP containers require Docker

☐ **Docker Desktop running (if needed)**

---

## PHASE 5: NETWORK VALIDATION (3 minutes)

### Step 5.1: Port Availability - 8001 (EPOS API)
```bash
netstat -an | grep 8001
```

**Expected**: Empty (port free) OR listening (service already running)  
**If occupied by wrong process**: Kill process
```bash
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

☐ **Port 8001 available**

---

### Step 5.2: Port Availability - 11434 (Ollama)
```bash
netstat -an | grep 11434
```

**Expected**: Listening (Ollama running)  
**If empty**: Ollama not running (see Step 4.1)

☐ **Port 11434 listening**

---

## PHASE 6: FILE SYSTEM VALIDATION (3 minutes)

### Step 6.1: Log Directory Writable
```bash
touch logs/test.log
rm logs/test.log
```

**Expected**: No errors  
**If errors**: Fix permissions
```bash
chmod 755 logs/
```

☐ **Log directory writable**

---

### Step 6.2: Workspace Directory Writable
```bash
touch C:\Users\Jamie\epos_workspace\test.txt
rm C:\Users\Jamie\epos_workspace\test.txt
```

**Expected**: No errors  
**If directory missing**: Create it
```bash
mkdir -p C:\Users\Jamie\epos_workspace
```

☐ **Workspace directory writable**

---

### Step 6.3: Disk Space Check
```bash
df -h C:\Users\Jamie\workspace
```

**Expected**: At least 5GB free  
**If low**: Clean old logs, work_dir  
**Why critical**: Out of space causes silent failures

☐ **Adequate disk space (5GB+)**

---

## PHASE 7: CONSTITUTIONAL VALIDATION (5 minutes)

### Step 7.1: Constitutional Documents Present
```bash
ls C:\Users\Jamie\workspace\epos_mcp\ENVIRONMENT_SPEC.md
ls C:\Users\Jamie\workspace\epos_mcp\COMPONENT_INTERACTION_MATRIX.md
ls C:\Users\Jamie\workspace\epos_mcp\FAILURE_SCENARIOS.md
ls C:\Users\Jamie\workspace\epos_mcp\PATH_CLARITY_RULES.md
ls C:\Users\Jamie\workspace\epos_mcp\PRE_FLIGHT_CHECKLIST.md
```

**Expected**: All files exist  
**If not**: Create missing documents  
**Why critical**: These are constitutional law

☐ **All 5 constitutional documents present**

---

### Step 7.2: Governance Gate Functional
```bash
python governance_gate.py --test
```

**Expected**: Test mode passes  
**If errors**: Fix governance_gate.py  
**Why critical**: All code must pass through gate

☐ **Governance gate functional**

---

## PHASE 8: AUTOMATED VALIDATION (2 minutes)

### Step 8.1: Run EPOS Doctor
```bash
python epos_doctor.py
```

**Expected**: All checks pass, exit code 0  
**If errors**: Address specific failures  
**Why critical**: Comprehensive automated validation

☐ **epos_doctor.py passes (exit code 0)**

---

## PHASE 9: COMPONENT-SPECIFIC CHECKS

### For Meta Orchestrator Deployment

**Additional checks**:
```bash
# Test FastAPI import
python -c "from engine.meta_orchestrator import app; print('Orchestrator importable')"

# Test health endpoint (if already running)
curl http://localhost:8001/health

# Verify governance integration
grep "epos_doctor" engine/meta_orchestrator.py
```

☐ **Orchestrator-specific checks passed**

---

### For Agent Zero Bridge Deployment

**Additional checks**:
```bash
# Test Agent Zero import
python -c "import sys; sys.path.append('C:/Users/Jamie/workspace/agent-zero'); from python.agent import Agent; print('Agent Zero importable')"

# Test bridge health
python -c "from engine.agent_zero_bridge import health_check; print(health_check())"
```

☐ **Bridge-specific checks passed**

---

### For Sovereignty Node Deployment

**Additional checks**:
```bash
# Verify manifest
cat nodes/research/node_manifest.json | python -m json.tool

# Test node doctor
python nodes/research/research_doctor.py

# Check port availability
netstat -an | grep 8010
```

☐ **Node-specific checks passed**

---

## PHASE 10: FINAL GO/NO-GO (1 minute)

### Review Checklist
**Count checkmarks above. Must be 100% before proceeding.**

**Total Required**: 20+ checkmarks (varies by deployment type)  
**Achieved**: _____ / _____

**If < 100%**: STOP. Address failures. Re-run checklist.  
**If 100%**: Proceed with deployment.

☐ **All phases completed successfully**

---

## POST-FLIGHT VALIDATION (After Deployment)

### Immediate Post-Deployment (5 minutes)

**Step 1: Service Health**
```bash
curl http://localhost:8001/health
```
**Expected**: `{"status": "healthy", "checks": {...}}`

**Step 2: Log Verification**
```bash
tail -f logs/orchestrator.log
```
**Expected**: Startup messages, no errors

**Step 3: Test Mission (if applicable)**
```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"mission_json": "{\"mission_id\": \"test-001\", \"objective\": \"Health check\", \"constraints\": {}, \"success_criteria\": [\"Responds\"], \"failure_modes\": []}"}'
```
**Expected**: 200 OK, mission executes

☐ **Post-deployment validation completed**

---

## TROUBLESHOOTING COMMON FAILURES

### Pre-Flight Fails: Python Version
**Issue**: Python 3.13 detected  
**Fix**: Uninstall 3.13, install 3.11.x  
**Prevention**: Lock Python version in documentation

---

### Pre-Flight Fails: .env Missing
**Issue**: `.env` file not found  
**Fix**: `cp .env.example .env`, populate values  
**Prevention**: Include .env.example in repo

---

### Pre-Flight Fails: Ollama Not Running
**Issue**: Connection refused on :11434  
**Fix**: `ollama serve &`  
**Prevention**: Add Ollama to startup services

---

### Pre-Flight Fails: Port Occupied
**Issue**: Port 8001 already in use  
**Fix**: Kill process or change port  
**Prevention**: Pre-flight port check

---

### Pre-Flight Fails: Permission Denied
**Issue**: Cannot write to logs/  
**Fix**: `chmod 755 logs/`  
**Prevention**: Set permissions in setup

---

## APPENDIX: Quick Checklist Summary

**30-Second Version** (for experienced operators):

1. ✅ Python 3.11.x
2. ✅ EPOS root exists
3. ✅ Agent Zero path valid
4. ✅ .env loaded
5. ✅ Dependencies installed
6. ✅ Ollama running
7. ✅ Port 8001 free
8. ✅ Logs writable
9. ✅ Constitutional docs present
10. ✅ `python epos_doctor.py` passes

**If all 10 pass → GO**  
**If any fail → NO-GO, fix first**

---

## APPENDIX: Checklist Automation

**Future Enhancement**: Automate this checklist in `epos_doctor.py`

```python
# Proposal: epos_doctor.py --checklist
# Runs all pre-flight checks, reports pass/fail for each
# Exit code 0 = all pass, exit code 1 = failures detected
# Outputs: JSON report of all checks
```

**Currently**: Manual execution required

---

## CONSTITUTIONAL COMPLIANCE

**This checklist is MANDATORY per Article III.**

**Violations**:
- Skipping checklist → Governance rejection
- Proceeding despite failures → Stasis trigger
- False reporting → Constitutional audit

**Enforcement**: All entrypoints call `epos_doctor.py` before execution

---

**END OF CHECKLIST**

*Last Updated: 2026-01-24*  
*Phases: 10*  
*Total Checks: 20+*  
*Estimated Time: 30 minutes (first run), 10 minutes (subsequent)*
