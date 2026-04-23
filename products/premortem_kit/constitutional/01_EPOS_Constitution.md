# File: C:\Users\Jamie\workspace\epos_mcp\EPOS_CONSTITUTION_v3.1.md

# EPOS CONSTITUTION v3.1
## The Law Governing Agentic Operating System Sovereignty
### Unified Framework: Pre-Mortem Discipline + Context Governance

**Ratified:** 2026-01-25  
**Authority:** EXPONERE Founder Jamie  
**Supersedes:** EPOS_CONSTITUTION_v3.0 (Everest), EPOS_CONSTITUTION_v3.0 (Context)  
**Purpose:** Unified governance preventing architectural drift AND enabling unlimited context scaling

---

## PREAMBLE: THE EVEREST PRINCIPLE

*"We are climbing Everest, laying the governance that will keep our agentic OS on the road as we climb."*

This Constitution exists because **architectural misalignment is more dangerous than bugs**. Bugs crash systems; misalignment causes systemic drift, silent failures, and compound workarounds.

EPOS operates under **Pre-Mortem Discipline**: we imagine failure before building, weigh multi-layered consequences before executing, and validate alignment before deployment.

**Dual Mandate:**
1. **Prevent drift** through constitutional enforcement (Pre-Mortem Framework)
2. **Enable scale** through context orchestration (RLM Integration)

**Core Philosophy:**
- Design foresight > Reactive debugging
- Constitutional frameworks > Ad-hoc solutions
- Imaginative projection > Trial-and-error iteration
- Operational sovereignty > Vendor dependency
- Symbolic context > Token limitations

---

## Article I: Foundational Principles

### The Pre-Mortem Mandate

**Before ANY code is written, component is added, or architecture is changed:**

1. **Imaginative Projection**: Play out 3-5 failure scenarios mentally
2. **Consequence Mapping**: Document downstream effects of each decision
3. **Alignment Validation**: Verify compatibility with existing components
4. **Recovery Planning**: Define rollback procedures
5. **Success Criteria**: Establish verifiable outcomes

**Violation of this mandate results in immediate rejection by Governance Gate.**

---

### The Five Constitutional Documents

All EPOS operations require these documents at root:

1. **`ENVIRONMENT_SPEC.md`**: Environment canon (shells, Python, paths, services)
2. **`COMPONENT_INTERACTION_MATRIX.md`**: Component dependencies, inputs, outputs, failure modes
3. **`FAILURE_SCENARIOS.md`**: Pre-imagined failures with recovery procedures
4. **`PATH_CLARITY_RULES.md`**: Single source of truth for path handling
5. **`PRE_FLIGHT_CHECKLIST.md`**: Step-by-step validation protocol

**These documents are LAW. Code is ENFORCEMENT.**

---

### The Sovereignty Covenant

EPOS maintains complete operational control through:

- **Data Sovereignty**: All operational data on local disk, no cloud dependencies
- **Vendor Replaceability**: External services must be swappable without core functionality loss
- **Rollback Capability**: All operations must be reversible
- **Integration Boundaries**: Clear contracts defining what external agents can/cannot do
- **Constitutional Supremacy**: No code overrides constitutional requirements
- **Context Sovereignty**: Local context storage, symbolic access, no vendor lock-in

---

## Article II: Hard Boundaries (Non-Negotiable)

### Rule 1: Path Absolutism
**Every file path MUST use Windows-style absolute paths in code.**

```python
# CORRECT
from pathlib import Path
EPOS_ROOT = Path("C:/Users/Jamie/workspace/epos_mcp")
mission_file = EPOS_ROOT / "engine" / "missions" / "mission_001.json"

# WRONG - Ambiguous
mission_file = "missions/mission_001.json"  # Relative to what?
```

**Reason**: Prevents path mixing (`C:\` vs `/c/`), shell confusion, silent failures.

---

### Rule 2: No Silent Failures
**All file I/O operations MUST log and validate.**

```python
# CORRECT
log_path = EPOS_ROOT / "logs" / "mission_001.log"
try:
    log_path.write_text(log_data)
    logger.info(f"Log written: {log_path}")
    assert log_path.exists(), "Log file not created"
except Exception as e:
    logger.error(f"Log write failed: {e}")
    raise

# WRONG
log_path.write_text(log_data)  # Silent failure if disk full
```

**Reason**: Prevents "logged vs executed" confusion, ensures audit trail.

---

### Rule 3: Environment Explicitness
**Python version and environment MUST be validated before execution.**

```python
# CORRECT - In all entrypoints
import sys
from dotenv import load_dotenv

REQUIRED_PYTHON = (3, 11)
if sys.version_info[:2] < REQUIRED_PYTHON:
    raise EnvironmentError(f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required")

load_dotenv(Path(__file__).parent / ".env")
```

**Violations**:
- ❌ Assuming Python version
- ❌ Not calling `load_dotenv()`
- ❌ Using `shell=True` without path validation

---

### Rule 4: Separation of Concerns
**Logging ≠ Execution. Status reports MUST reflect actual work done.**

```python
# CORRECT
def execute_mission(mission_id):
    logger.info(f"Starting mission {mission_id}")
    
    result = agent_zero.run(mission_id)
    
    if result.success:
        logger.info(f"Mission {mission_id} COMPLETED")
        return {"status": "executed", "proof": result.output_path}
    else:
        logger.error(f"Mission {mission_id} FAILED: {result.error}")
        return {"status": "failed", "error": result.error}

# WRONG
def execute_mission(mission_id):
    logger.info(f"Executing mission {mission_id}")
    return {"status": "executed"}  # LIE - nothing happened
```

---

### Rule 5: No Destructive Defaults
**Destructive operations require explicit confirmation.**

**Blocked without confirmation**:
- File deletion (`rm -rf`, `del /s`)
- Disk operations (`format`, `diskpart`)
- System commands (`shutdown`, `reboot`)
- Overwriting files without backup

**Implementation**: Command allowlist in `engine/command_validator.py`

---

### Rule 6: Configuration Explicitness
**All configuration MUST be loaded explicitly via `python-dotenv`.**

```python
# CORRECT - At entrypoint
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# WRONG - Assumes auto-loading
import os
agent_path = os.getenv("AGENT_ZERO_PATH")  # May be None
```

**Violation symptom**: "It worked yesterday" (environment drift)

---

### Rule 7: Context Vault Mandate (NEW)
**Data exceeding 8,192 tokens MUST use Context Vault, not inline.**

```python
# CORRECT - Large data in vault
mission = {
    "mission_id": "analysis-001",
    "objective": "Analyze Q1-Q4 2025 market data",
    "context_vault_path": "context_vault/market_data/2025_full.txt",
    "success_criteria": ["Insights extracted via symbolic search"]
}

# WRONG - Inline data > 8K tokens
mission = {
    "mission_id": "analysis-001",
    "data": "[... 50,000 tokens of data ...]"  # VIOLATION
}
```

**Reason**: Prevents token overflow, enables RLM scaling, maintains governance.

---

## Article III: Quality Gates

### Pre-Flight Validation
**Before ANY execution, `epos_doctor.py` MUST pass:**

```bash
python epos_doctor.py
# Exit code 0: Proceed
# Exit code 1: Fix issues, re-validate
```

**10 Critical Checks:**
1. ✅ Python 3.11.x confirmed
2. ✅ EPOS root exists and accessible
3. ✅ Agent Zero path valid
4. ✅ Required directories present (engine/, logs/, inbox/, context_vault/)
5. ✅ Ollama service running on :11434
6. ✅ `.env` loaded successfully
7. ✅ All dependencies installed (`pip check`)
8. ✅ Port 8001 available
9. ✅ Log directories writable
10. ✅ Constitutional documents present

---

### Schema Validation
**All mission JSONs MUST validate against `EPOSAgentMission` schema.**

```python
from agent_mission_spec import EPOSAgentMission

mission = EPOSAgentMission(**json_data)
mission.validate()  # Raises ValidationError if invalid
```

**Required fields**:
- `mission_id` (UUID)
- `objective` (clear statement)
- `constraints` (environment, paths, risk level)
- `success_criteria` (verifiable outcomes)
- `failure_modes` (pre-imagined scenarios)
- `context_vault_path` (optional, required if data > 8K tokens)

---

### Governance Gate Triage
**All code enters via `/inbox`, triaged by `governance_gate.py`:**

**Promoted to `/engine`** if:
- ✅ Passes constitutional checks (no violations of Article II)
- ✅ Includes absolute path header
- ✅ Has pre-mortem analysis (if component)
- ✅ Validates against schema (if mission)
- ✅ Includes recovery procedures
- ✅ Context vault usage correct (if > 8K tokens)

**Rejected to `/rejected`** if:
- ❌ Violates hard boundaries
- ❌ Missing required documentation
- ❌ No failure mode analysis
- ❌ Ambiguous success criteria
- ❌ Inline data > 8K tokens without vault

**Educational Receipt** includes:
- Specific violation code
- Constitutional article reference
- Exact fix required
- Example of correct implementation

---

## Article IV: Architectural Discipline

### Component Interaction Matrix

**Every component MUST document in `COMPONENT_INTERACTION_MATRIX.md`:**

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Component identifier | EPOS API |
| **Inputs** | Dependencies, config | Python 3.11, FastAPI, `.env` |
| **Outputs** | Files, logs, responses | JSON responses, `logs/*.log` |
| **Ports** | Network resources | 8001 (HTTP) |
| **Failure Modes** | Pre-imagined failures | Agent Zero unreachable → 503 |
| **Observability** | Monitoring points | `/health`, `logs/api.log` |
| **Recovery** | Rollback procedure | Stop service, restore backup |
| **Context Usage** | Vault integration | Uses `context_vault/mission_data/` |

---

### Failure Scenario Catalog

**Before implementing ANY feature, document in `FAILURE_SCENARIOS.md`:**

**Template:**
```markdown
## Scenario: [Name]

**Trigger**: [What causes this failure]
**Impact**: [What breaks]
**Detection**: [How we know it happened]
**Recovery**: [Steps to fix]
**Prevention**: [Design changes to avoid]

**Example:**
## Scenario: Context Vault File Missing

**Trigger**: Mission references non-existent vault file
**Impact**: Symbolic search fails, mission aborts
**Detection**: `FileNotFoundError` in context_handler.py
**Recovery**: Create vault file or update mission spec
**Prevention**: Pre-flight validation checks vault path exists
```

**Minimum scenarios per component**: 3-5

---

### Pre-Mortem Discipline

**The Core Practice**: Before writing code, answer these questions:

1. **"What if dependency X is missing?"**
   - Example: Agent Zero not installed
   - Response: Health check returns `ok: false`, mission returns 503

2. **"What if file Y is corrupted?"**
   - Example: `.env` has syntax error
   - Response: Startup fails with explicit error, not silent skip

3. **"What if service Z is down?"**
   - Example: Ollama not running
   - Response: Health check detects, mission doesn't attempt execution

4. **"What if context is too large?"**
   - Example: Mission has 100K tokens of data
   - Response: Use Context Vault, symbolic search, no token overflow

5. **"What if we need to rollback?"**
   - Example: New version breaks missions
   - Response: Git tag + restore script in recovery docs

**These questions MUST be answered in design docs before implementation.**

---

## Article V: Business Intelligence Integration

### Decision Logging

**Every architectural decision logged to `bi_decision_log.json`:**

```json
{
  "timestamp": "2026-01-25T12:00:00Z",
  "decision": "Merge Context Vault into main constitution",
  "reason": "Unify governance, prevent token overflow, enable RLM scaling",
  "impact": "Single source of truth, scalable missions, no vendor lock-in",
  "category": "constitutional_amendment",
  "constitutional_article": "Article VII (Context Governance)"
}
```

**Categories**: dependency_management, path_strategy, failure_prevention, vendor_integration, context_scaling

---

### Pivot Cooldown

**System MAY NOT suggest architectural pivots unless:**

1. **72 hour data collection minimum**
2. **150+ data points collected**
3. **Clear failure pattern identified**
4. **Alternative solution validated**

**Purpose**: Prevents reactive thrashing, forces evidence-based decisions.

**Exception**: Critical security vulnerability (immediate action required)

---

### Market Sentiment Bridge

**External feedback ingested via `/market` directory:**

- `*.csv`: Survey results, user feedback
- `*.json`: Analytics data, error logs
- `*.txt`: Email transcripts, support tickets

**Processing**: BI engine analyzes, recommends features, logs to `INTERNAL_FEEDBACK.json`

**Context Vault Integration**: Large feedback datasets (>8K tokens) stored in `context_vault/market_sentiment/`, queried symbolically for pattern detection.

---

## Article VI: Autonomous Evolution Safeguards

### Feature Proposer Constraints

**Autonomous feature suggestions MUST:**

1. Pass through Governance Gate like human code
2. Include complete pre-mortem analysis
3. Reference specific BI data supporting need
4. Provide rollback procedure
5. Estimate resource cost (compute, storage, dev time)
6. Use Context Vault for large data analysis (not inline)

**Example: Agent proposes new API endpoint**

Required documentation:
- Pre-mortem: 5 failure scenarios
- BI justification: "73% of users requested this" (from context vault analysis)
- Resource estimate: "2 hours dev, 10MB storage"
- Rollback: "Remove endpoint, restore previous API spec"
- Context usage: "Analyzed 6 months user feedback via vault symbolic search"

---

### Safety Covenant

**EPOS MUST NOT (without explicit human approval):**

1. Execute code from untrusted sources
2. Modify constitutional files
3. Make destructive changes without backup
4. Suggest pivots during cooldown period
5. Deploy to production without green pre-flight
6. Share operational data externally
7. Modify vendor integration boundaries
8. Inline large data instead of using Context Vault

**Violation**: Immediate shutdown, human intervention required

---

## Article VII: Context Governance (RLM Integration)

### Section 1: Context Limits & Vault Requirements

**7.1 Token Inline Limit**
- No mission specification may inline more than **8,192 tokens** of data
- Data exceeding this limit MUST be stored in `/context_vault` directory
- Violations: `ERR-CONTEXT-001: Inline data exceeds token limit`

**7.2 Vault Directory Structure**
```
C:\Users\Jamie\workspace\epos_mcp\context_vault\
├── mission_data\          # Mission-specific large datasets
├── bi_history\            # Business intelligence logs
├── market_sentiment\      # Aggregated user feedback
├── agent_logs\            # Long-running agent execution logs
└── registry.json          # Vault file registry
```

**7.3 Mandatory Vault Usage**
When data > 8,192 tokens, missions MUST:
1. Store data in `/context_vault/[category]/[name].txt`
2. Reference vault in mission spec via `context_vault_path` field
3. Use ContextVault symbolic search (not full load)

---

### Section 2: Component C09 - Context Orchestrator

**7.4 Purpose**
- Store ultra-long mission/BI/state data
- Expose symbolic search tools to Agent Zero and Execution Bridge
- Enable million+ token working context
- Prevent "context rot" in long-running analysis

**7.5 Constitutional Compliance**
- Uses `pathlib.Path` for all operations (Article II, Rule 1)
- Validates all paths are in `/context_vault/` directory
- Logs all search operations (Article II, Rule 2)
- Pre-imagined failure modes documented (Article IV)

**7.6 Search Methods** (RLM "Symbolic Queries")
- `regex_search()`: Pattern-based retrieval
- `window_search()`: Context window extraction
- `chunk_search()`: Chunked location-aware search
- `extract_json_objects()`: Structured data extraction

---

### Section 3: Agent Zero Integration

**7.7 Tool Exposure**
Agent Zero receives ContextVault as **tools**, not inline context:
```python
tools = {
    "search_context": vault.regex_search,
    "get_context_window": vault.window_search,
    "get_metadata": vault.get_metadata
}
```

**7.8 Execution Pattern**
1. Agent Zero receives mission with `context_vault_path`
2. Execution Bridge instantiates ContextVault
3. Agent Zero uses search tools to query vault
4. Agent Zero receives ONLY relevant snippets (not full file)
5. Agent Zero can recursively refine queries ("multi-hop")

**7.9 Prohibition**
- Agent Zero MUST NOT load full vault into prompt
- Execution Bridge MUST NOT inline vault content
- Mission specs MUST NOT contain > 8K tokens of data

---

### Section 4: Governance Gate Enforcement

**7.10 Pre-Flight Checks**
Governance Gate validates:
1. Files > 50KB do NOT inline data (use vault)
2. Missions referencing vaults include valid `context_vault_path`
3. Vault files exist and are in `/context_vault/` directory
4. Vault files do not exceed 100MB size limit

**7.11 Rejection Codes**
- `ERR-CONTEXT-001`: Inline long literal; must use ContextVault
- `ERR-CONTEXT-002`: Invalid vault path (not in context_vault/)
- `ERR-CONTEXT-003`: Vault file not found
- `ERR-CONTEXT-004`: Vault file exceeds size limit (100MB)

**7.12 Snapshot Detection**
`epos_snapshot.py` flags:
- Hard-coded strings > 2000 characters
- Ad-hoc file reads outside context_vault
- Mission specs > 8K tokens without vault reference

---

### Section 5: Business Intelligence Context Integration

**7.13 BI Logging**
BI engine tracks:
- Which vault files used in each mission
- Depth of recursive searches (RLM "trajectory length")
- Context query costs (proxy for token usage)
- Vault file sizes over time

**7.14 Optimization Triggers**
Missions that trigger deep recursive searches (>10 iterations) get flagged for optimization.

**7.15 Historical Analysis**
BI engine can query vault history without token limits:
```python
vault = ContextVault(Path("context_vault/bi_history/decisions_2026.jsonl"))
pivots = vault.extract_json_objects()  # No context window limit
```

---

## Article VIII: Amendment Process

### Constitutional Changes

**Amendments require:**

1. **Justification**: Clear problem statement
2. **Impact Analysis**: Downstream consequences documented
3. **Validation**: 3+ test scenarios pass
4. **Approval**: Explicit commit to main branch
5. **Communication**: Updated in all dependent systems
6. **Version Increment**: Major (breaking), Minor (additive), Patch (clarification)

**Process**:
```bash
# 1. Propose amendment
git checkout -b constitution/amendment-name

# 2. Update EPOS_CONSTITUTION_v3.1.md
# 3. Run validation
python epos_doctor.py --check-constitution

# 4. Submit for review
git commit -m "CONSTITUTION: Amendment XYZ - Reason"
git push origin constitution/amendment-name

# 5. Merge after approval
```

---

### Version Control

**Constitution versions:**
- **Major (vX.0.0)**: Core principle changes (e.g., v2.0 → v3.0)
- **Minor (v3.X.0)**: New articles or rules (e.g., v3.0 → v3.1)
- **Patch (v3.1.X)**: Clarifications, examples (e.g., v3.1.0 → v3.1.1)

**Current**: v3.1.0 (Unified Pre-Mortem + Context Governance)

**History**:
- v2.0: Basic governance rules
- v3.0 (Everest): Pre-mortem discipline framework
- v3.0 (Context): RLM context vault integration
- v3.1: Merged unified framework (this document)

---

## Article IX: Enforcement

### Immediate Rejection

**Violations of Article II (Hard Boundaries) result in:**

1. Immediate execution halt
2. Governance Gate rejection
3. Educational receipt generated
4. No execution until fixed

**Non-negotiable violations:**
- Path ambiguity
- Silent failures
- Missing environment validation
- Status lies (logged ≠ executed)
- Destructive operations without confirmation
- Configuration assumptions
- Inline data > 8K tokens

---

### Monitoring & Alerts

**Continuous validation via:**

1. **Health Checks**: `/health` endpoint every 60s
2. **Log Analysis**: Daily scan for constitutional violations
3. **Metric Tracking**: Compliance rate, rejection rate, pivot frequency, context vault usage
4. **Alert Thresholds**:
   - Compliance < 95% → Warning
   - Compliance < 85% → System review required
   - 3+ violations in 24h → Architecture audit
   - Context vault file > 100MB → Optimization review

---

### Compliance Metrics

**Tracked in `compliance_report.json`:**

```json
{
  "date": "2026-01-25",
  "total_submissions": 47,
  "promoted": 42,
  "rejected": 5,
  "compliance_rate": 0.89,
  "top_violations": [
    {"rule": "Article II, Rule 1", "count": 3},
    {"rule": "Article VII, Rule 7", "count": 2}
  ],
  "context_vault_usage": {
    "missions_using_vault": 12,
    "avg_vault_size_mb": 1.2,
    "total_symbolic_queries": 157
  }
}
```

**Target**: 95%+ compliance rate

---

## Article X: Vendor Integration Framework

### External Agent Contracts

**All external agents (Agent Zero, Claude Code, Abacus) MUST:**

1. Operate within defined sandboxes
2. Report status explicitly (no silent failures)
3. Provide rollback mechanisms
4. Respect data sovereignty (local-only)
5. Accept governance boundaries
6. Use Context Vault for large data (no inline)

**Example: Agent Zero Contract**

```yaml
vendor: Agent Zero
version: 1.0
sandbox: C:\Users\Jamie\workspace\agent-zero
permissions:
  - read: C:\Users\Jamie\epos_workspace
  - write: C:\Users\Jamie\epos_workspace\outputs
  - execute: python, git, npm
data_flow: local_only
reporting: structured_json
rollback: git_reset
context_access: vault_symbolic_only  # NEW
```

---

### Integration Boundaries

**What external agents CAN do:**
- Execute tasks within sandbox
- Read/write to designated workspace
- Report structured results
- Query Context Vault symbolically

**What external agents CANNOT do:**
- Modify EPOS core (`/engine`)
- Change constitutional files
- Access other vendor sandboxes
- Make irreversible changes
- Execute without governance approval
- Load full vault files into context (symbolic only)

---

## Article XI: Emergency Procedures

### Stasis Mode

**Trigger stasis if:**
- Compliance rate < 75%
- Critical constitutional violation detected
- Vendor agent goes rogue
- Data sovereignty breach
- Context vault corruption detected

**Stasis protocol:**
1. Halt all autonomous operations
2. Snapshot current state
3. Generate diagnostic report
4. Human intervention required
5. Root cause analysis before resuming

**File**: `engine/stasis.py`

---

### Rollback Authority

**Any operation can be rolled back within 24 hours:**

```bash
# Rollback mission
python engine/rollback.py --mission mission_001

# Rollback component
python engine/rollback.py --component research_node

# Full system rollback
python engine/rollback.py --snapshot snapshot_20260125

# Rollback context vault file
python engine/rollback.py --vault context_vault/mission_data/corrupted.txt
```

**Retention**: 30 days of rollback snapshots

---

### Constitutional Override

**Emergency override (human-only):**

```bash
# Bypass governance gate (requires justification)
python governance_gate.py --override --reason "critical_bug_fix"

# Skip pre-flight (requires approval)
python meta_orchestrator.py --skip-doctor --approved-by Jamie

# Emergency context vault bypass (temporary)
python execution_bridge.py --allow-inline-context --emergency --approved-by Jamie
```

**Logging**: All overrides logged to `override_log.json` with justification

---

## APPENDIX A: Glossary

- **Pre-Mortem**: Imagining failure before building
- **Constitutional Document**: One of the 5 foundational governance files
- **Governance Gate**: Validation system for code/mission submissions
- **Educational Receipt**: Rejection notice with specific fix guidance
- **Pivot Cooldown**: 72-hour period before architectural changes allowed
- **Data Sovereignty**: All operational data on local disk
- **Vendor Replaceability**: Ability to swap external services without loss
- **Stasis Mode**: Emergency halt of autonomous operations
- **Context Vault**: Local storage for large datasets (>8K tokens)
- **Symbolic Search**: RLM pattern-based context retrieval without full load
- **RLM**: Recursive Language Model (context scaling technique)

---

## APPENDIX B: Quick Reference

**Before writing code:**
1. Read relevant constitutional articles
2. Document 3-5 failure scenarios
3. Update Component Interaction Matrix
4. Run `python epos_doctor.py`
5. Determine if Context Vault needed (data > 8K tokens)

**Before deploying:**
1. Submit to Governance Gate
2. Pass pre-flight checks
3. Verify constitutional compliance
4. Create rollback snapshot
5. Validate context vault paths (if used)

**When things break:**
1. Check `logs/*.log`
2. Run `python epos_doctor.py`
3. Consult `FAILURE_SCENARIOS.md`
4. Execute recovery procedure
5. Check context vault integrity (if used)

---

## APPENDIX C: Failure Mode Cross-Reference

### Pre-Mortem Framework Failures (FS-PM)
- **FS-PM01**: Path mixing (Article II, Rule 1)
- **FS-PM02**: Silent file I/O (Article II, Rule 2)
- **FS-PM03**: Environment drift (Article II, Rule 3)
- **FS-PM04**: Status lies (Article II, Rule 4)
- **FS-PM05**: Destructive defaults (Article II, Rule 5)
- **FS-PM06**: Config assumptions (Article II, Rule 6)

### Context Vault Failures (FS-CV)
- **FS-CV01**: Vault file missing (Article VII, Section 4)
- **FS-CV02**: Invalid vault path (Article VII, Section 4)
- **FS-CV03**: Vault size exceeded (Article VII, Section 4)
- **FS-CV04**: Invalid regex pattern (Article VII, Section 2)
- **FS-CV05**: Inline data > 8K tokens (Article II, Rule 7)

---

**END OF CONSTITUTION**

*Ratified 2026-01-25 by EXPONERE Founder Jamie*  
*Next Review: 2026-02-25 (30 days)*  
*Version: 3.1.0 (Unified Framework)*