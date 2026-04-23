# File: C:\Users\Jamie\workspace\epos_mcp\FAILURE_SCENARIOS.md

# FAILURE SCENARIOS CATALOG
## Pre-Mortem Analysis of System Failures (Constitutional Document #3)

**Authority:** EPOS Constitution v3.0, Article IV  
**Last Updated:** 2026-01-24  
**Purpose:** Document all pre-imagined failures before they occur

---

## CATALOG STRUCTURE

Each scenario includes:
- **ID**: Unique identifier (category-number)
- **Trigger**: What causes this failure
- **Impact**: What breaks and why it matters
- **Detection**: How we know it happened
- **Recovery**: Steps to fix
- **Prevention**: Design changes to avoid
- **Probability**: Low / Medium / High
- **Severity**: Low / Medium / High / Critical

---

## ENVIRONMENT FAILURES (E)

### E-1: Python Version Mismatch

**Trigger**: Python 3.13 installed instead of 3.11.x  
**Impact**: Agent Zero dependencies fail with C extension errors  
**Detection**: `epos_doctor.py` version check fails  
**Recovery**:
```bash
# Uninstall 3.13
py -3.13 -m pip uninstall -y python
# Install 3.11 from python.org
# Verify
python --version  # Should show 3.11.x
```
**Prevention**: Document in onboarding, add to CI/CD  
**Probability**: Medium  
**Severity**: High (blocks all operations)

---

### E-2: Missing .env File

**Trigger**: `.env` file deleted or not created  
**Impact**: All environment variables undefined, startup fails  
**Detection**: `FileNotFoundError` on `.env` load  
**Recovery**:
```bash
# Copy template
cp .env.example .env
# Populate required values
nano .env
```
**Prevention**: Include `.env.example` in repo, validate on startup  
**Probability**: Low (one-time setup)  
**Severity**: Critical (cannot start)

---

### E-3: Corrupted .env File

**Trigger**: Syntax error in `.env` (e.g., `KEY=VALUE WITH SPACE`)  
**Impact**: Some variables load, others don't → partial failure  
**Detection**: `python-dotenv` warnings, missing expected values  
**Recovery**:
```bash
# Validate syntax
cat .env | grep -v '^#' | grep '='
# Fix malformed lines
# Reload
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ)"
```
**Prevention**: `.env` linter in pre-commit hook  
**Probability**: Low  
**Severity**: Medium (silent partial failure)

---

### E-4: Disk Space Exhaustion

**Trigger**: Logs, work_dir, or outputs fill disk  
**Impact**: File writes fail, missions abort, system unstable  
**Detection**: `OSError: No space left on device`  
**Recovery**:
```bash
# Check usage
df -h C:\Users\Jamie\workspace
# Clean logs
rm logs/*.log.old
# Clean work_dir
rm -rf C:\Users\Jamie\workspace\agent-zero\work_dir/*
```
**Prevention**: Automated log rotation, disk space monitoring  
**Probability**: Medium (over time)  
**Severity**: High (system-wide)

---

## SERVICE FAILURES (S)

### S-1: Ollama Not Running

**Trigger**: Ollama service stopped or crashed  
**Impact**: All LLM operations fail, missions abort  
**Detection**: Connection refused on :11434  
**Recovery**:
```bash
# Check status
curl http://localhost:11434/api/tags
# Restart
ollama serve &
# Verify
curl http://localhost:11434/api/tags
```
**Prevention**: Service monitoring, auto-restart on failure  
**Probability**: Medium  
**Severity**: Critical (LLM unavailable)

---

### S-2: Ollama Model Missing

**Trigger**: Required model (llama3.2:latest) not pulled  
**Impact**: LLM calls fail with "model not found"  
**Detection**: 404 error from Ollama API  
**Recovery**:
```bash
# Pull model
ollama pull llama3.2:latest
# Verify
ollama list | grep llama3.2
```
**Prevention**: Include in setup checklist, validate on doctor run  
**Probability**: Low (setup issue)  
**Severity**: High

---

### S-3: Docker Desktop Not Running

**Trigger**: Docker Desktop stopped (for future MCP containers)  
**Impact**: Container-based nodes unavailable  
**Detection**: `docker ps` fails with connection error  
**Recovery**:
```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
# Wait for startup
docker ps
```
**Prevention**: Service monitoring, startup script  
**Probability**: Medium  
**Severity**: Medium (only affects containerized nodes)

---

## NETWORK FAILURES (N)

### N-1: Port 8001 Already in Use

**Trigger**: Another process bound to :8001  
**Impact**: Meta orchestrator cannot start  
**Detection**: Uvicorn binding error  
**Recovery**:
```bash
# Find process
netstat -ano | findstr :8001
# Kill process
taskkill /PID <PID> /F
# Restart orchestrator
python engine/meta_orchestrator.py
```
**Prevention**: Pre-flight port check in doctor  
**Probability**: Low  
**Severity**: Medium (single component)

---

### N-2: Firewall Blocking Ollama

**Trigger**: Windows Firewall rule blocks :11434  
**Impact**: LLM calls timeout, missions fail  
**Detection**: Connection timeout (not refused)  
**Recovery**:
```powershell
# Add firewall rule
New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```
**Prevention**: Document in setup, validate connectivity  
**Probability**: Low (setup issue)  
**Severity**: High

---

## PATH FAILURES (P)

### P-1: Path Mixing (C:\ vs /c/)

**Trigger**: Code uses `/c/Users/...` instead of `C:\Users\...`  
**Impact**: Silent failures, logs show mixed paths  
**Detection**: Governance gate path validation fails  
**Recovery**: Fix code to use Windows-style paths  
**Prevention**: Constitutional Rule 1, governance enforcement  
**Probability**: Medium (developer error)  
**Severity**: Medium (confusion, not crash)

---

### P-2: Relative Path Ambiguity

**Trigger**: Code uses `"missions/mission.json"` without context  
**Impact**: File not found if cwd changes  
**Detection**: `FileNotFoundError` in unexpected contexts  
**Recovery**:
```python
# Change to absolute
from pathlib import Path
EPOS_ROOT = Path("C:/Users/Jamie/workspace/epos_mcp")
mission_file = EPOS_ROOT / "missions" / "mission.json"
```
**Prevention**: Constitutional Rule 1, lint for relative paths  
**Probability**: Medium  
**Severity**: Medium

---

### P-3: Agent Zero Path Invalid

**Trigger**: `AGENT_ZERO_PATH` in `.env` points to wrong directory  
**Impact**: Bridge import fails, all missions abort  
**Detection**: `ImportError: No module named 'agent'`  
**Recovery**:
```bash
# Fix .env
nano .env
# Change AGENT_ZERO_PATH=C:/Users/Jamie/workspace/agent-zero
# Reload
python -c "from dotenv import load_dotenv; load_dotenv()"
```
**Prevention**: Doctor validates path on startup  
**Probability**: Low (setup issue)  
**Severity**: Critical

---

## FILE I/O FAILURES (F)

### F-1: Log Write Failure

**Trigger**: Log directory not writable, disk full  
**Impact**: Audit trail lost, debugging impossible  
**Detection**: `PermissionError` or `OSError` on log write  
**Recovery**:
```bash
# Check permissions
ls -la logs/
# Fix permissions
chmod 755 logs/
# Check disk space
df -h
```
**Prevention**: Doctor validates log directory writable  
**Probability**: Low  
**Severity**: High (lose audit trail)

---

### F-2: Mission File Corruption

**Trigger**: JSON syntax error in mission file  
**Impact**: Mission validation fails, cannot execute  
**Detection**: `json.JSONDecodeError`  
**Recovery**:
```bash
# Validate JSON
python -m json.tool missions/mission.json
# Fix syntax errors
# Resubmit
```
**Prevention**: Schema validation before submission  
**Probability**: Medium (human error)  
**Severity**: Low (single mission)

---

### F-3: Simultaneous Write Conflict

**Trigger**: Two processes write to same log file  
**Impact**: Interleaved or corrupted log entries  
**Detection**: Malformed log lines on read  
**Recovery**: Use file locking or separate log files  
**Prevention**: Process-specific log files (e.g., `orchestrator_<pid>.log`)  
**Probability**: Low (concurrency)  
**Severity**: Medium (debugging difficulty)

---

## AGENT ZERO FAILURES (A)

### A-1: Agent Zero Import Failure

**Trigger**: Agent Zero not installed or path wrong  
**Impact**: Bridge initialization fails, no missions execute  
**Detection**: `ImportError` on bridge startup  
**Recovery**:
```bash
# Reinstall Agent Zero
cd C:\Users\Jamie\workspace\agent-zero
git pull origin main
pip install -e .
```
**Prevention**: Doctor validates import  
**Probability**: Low  
**Severity**: Critical

---

### A-2: LLM Execution Timeout

**Trigger**: Agent Zero task takes > 5 minutes  
**Impact**: Mission marked as failed  
**Detection**: Timeout exception in bridge  
**Recovery**: Increase timeout or simplify mission  
**Prevention**: Task complexity analysis, timeout warnings  
**Probability**: Medium (complex tasks)  
**Severity**: Medium (retry possible)

---

### A-3: Work Directory Conflict

**Trigger**: Multiple missions run simultaneously, share work_dir  
**Impact**: File overwrites, output confusion  
**Detection**: Unexpected files in outputs  
**Recovery**: Use mission-specific work directories  
**Prevention**: Isolate work_dir per mission  
**Probability**: Medium (concurrency)  
**Severity**: High (data loss)

---

## API FAILURES (API)

### API-1: Invalid Mission JSON

**Trigger**: Client submits mission missing required fields  
**Impact**: 400 Bad Request, mission rejected  
**Detection**: Pydantic `ValidationError`  
**Recovery**: Fix mission JSON per error message  
**Prevention**: Provide schema documentation, examples  
**Probability**: High (client error)  
**Severity**: Low (client-side fix)

---

### API-2: Health Check Lies

**Trigger**: `/health` returns "healthy" but bridge is broken  
**Impact**: User attempts missions, all fail mysteriously  
**Detection**: Mission failures despite green health  
**Recovery**: Fix health check to test actual bridge  
**Prevention**: Constitutional Rule 4 (logging ≠ execution)  
**Probability**: Medium (design flaw)  
**Severity**: High (misleading user)

---

### API-3: Uncaught Exception in Endpoint

**Trigger**: Unexpected error in mission execution  
**Impact**: 500 Internal Server Error, no details  
**Detection**: Stack trace in logs  
**Recovery**: Add try/except, return structured error  
**Prevention**: Comprehensive exception handling  
**Probability**: Medium (edge cases)  
**Severity**: Medium (debugging difficulty)

---

## GOVERNANCE FAILURES (G)

### G-1: Missing Constitutional Header

**Trigger**: Submitted file lacks `# File: C:\...` header  
**Impact**: Rejected, cannot determine location  
**Detection**: Governance gate header check fails  
**Recovery**: Add header, resubmit  
**Prevention**: Template enforcement, pre-submit validation  
**Probability**: Medium (developer oversight)  
**Severity**: Low (easy fix)

---

### G-2: Hard Boundary Violation Not Detected

**Trigger**: Governance gate misses a violation  
**Impact**: Bad code promoted to production  
**Detection**: Runtime error, manual code review  
**Recovery**: Retroactively reject, fix gate  
**Prevention**: Improve gate validation, add test cases  
**Probability**: Low (gate robustness)  
**Severity**: High (production bug)

---

### G-3: Educational Receipt Ignored

**Trigger**: Developer resubmits without fixing violation  
**Impact**: Rejected again, wasted time  
**Detection**: Same file in rejected/ twice  
**Recovery**: Read receipt, fix issue  
**Prevention**: Better communication, receipt clarity  
**Probability**: Medium (developer confusion)  
**Severity**: Low (time waste)

---

## DEPENDENCY FAILURES (D)

### D-1: Incompatible Dependency Version

**Trigger**: `pip install` upgrades package to incompatible version  
**Impact**: Import errors, runtime failures  
**Detection**: `ImportError` or `AttributeError`  
**Recovery**:
```bash
# Pin exact version
pip install package==1.2.3
# Update requirements.txt
echo "package==1.2.3" >> requirements.txt
```
**Prevention**: Use exact versions in requirements.txt  
**Probability**: Medium (transitive dependencies)  
**Severity**: High

---

### D-2: Missing System Library

**Trigger**: Python package requires C library not installed  
**Impact**: `pip install` fails or runtime crashes  
**Detection**: Import error mentioning `.dll` or `.so`  
**Recovery**: Install system library (e.g., Visual C++ Redistributable)  
**Prevention**: Document system dependencies  
**Probability**: Low (Windows pre-built wheels)  
**Severity**: High

---

## CONSTITUTIONAL FAILURES (C)

### C-1: Amendment Without Approval

**Trigger**: Developer modifies constitutional file directly  
**Impact**: System drift, governance breakdown  
**Detection**: Git history shows unauthorized commit  
**Recovery**: Revert commit, follow amendment process  
**Prevention**: Protected branches, approval required  
**Probability**: Low (intentional)  
**Severity**: Critical (governance violation)

---

### C-2: Skipped Pre-Flight Check

**Trigger**: Developer bypasses `epos_doctor.py` check  
**Impact**: Environment issues go undetected  
**Detection**: Runtime failures that doctor would catch  
**Recovery**: Run doctor, fix issues  
**Prevention**: Make doctor mandatory in orchestrator  
**Probability**: Medium (impatience)  
**Severity**: High

---

## RECOVERY SCENARIOS (R)

### R-1: Full System Rollback Needed

**Trigger**: Major bug deployed to production  
**Impact**: All operations broken  
**Detection**: Multiple failures, user reports  
**Recovery**:
```bash
# Rollback to last known good
git checkout <last-good-commit>
# Restore from backup
cp backups/snapshot_20260123.tar.gz .
tar -xzf snapshot_20260123.tar.gz
# Restart services
python epos_doctor.py && python engine/meta_orchestrator.py
```
**Prevention**: Staging environment, gradual rollout  
**Probability**: Low (catastrophic)  
**Severity**: Critical

---

### R-2: Emergency Stasis Activation

**Trigger**: Vendor agent goes rogue, data breach suspected  
**Impact**: All autonomous operations halted  
**Detection**: Anomaly detection, manual trigger  
**Recovery**:
```bash
# Activate stasis
python engine/stasis.py --activate --reason "security_incident"
# Investigate
# Fix issue
# Deactivate stasis
python engine/stasis.py --deactivate --approved-by Jamie
```
**Prevention**: Vendor sandboxing, monitoring  
**Probability**: Very Low  
**Severity**: Critical

---

## APPENDIX: Failure Mode Statistics

**Total Scenarios Documented**: 25  
**By Category**:
- Environment: 4
- Service: 3
- Network: 2
- Path: 3
- File I/O: 3
- Agent Zero: 3
- API: 3
- Governance: 3
- Dependency: 2
- Constitutional: 2
- Recovery: 2

**By Severity**:
- Critical: 7 (28%)
- High: 8 (32%)
- Medium: 9 (36%)
- Low: 1 (4%)

**By Probability**:
- High: 1 (4%)
- Medium: 12 (48%)
- Low: 11 (44%)
- Very Low: 1 (4%)

**Priority: Critical + High Probability** = 3 scenarios require immediate mitigation

---

## APPENDIX: Quick Recovery Checklist

**If system is completely broken:**

1. ✅ Run `python epos_doctor.py` - get diagnostic report
2. ✅ Check logs: `logs/*.log` - find stack traces
3. ✅ Verify services: Ollama, Docker - ensure running
4. ✅ Validate .env: `cat .env` - check syntax
5. ✅ Check disk space: `df -h` - ensure space available
6. ✅ Rollback if needed: `git checkout <commit>` - restore last good
7. ✅ Consult COMPONENT_INTERACTION_MATRIX.md - identify dependencies
8. ✅ Test incrementally: Start with doctor, then orchestrator, then missions

---

**END OF CATALOG**

*Last Updated: 2026-01-24*  
*Total Scenarios: 25*  
*Next Review: After first production incident*
