# File: C:\Users\Jamie\workspace\epos_mcp\COMPONENT_INTERACTION_MATRIX.md

# COMPONENT INTERACTION MATRIX
## Comprehensive Dependency and Failure Mapping (Constitutional Document #2)

**Authority:** EPOS Constitution v3.0, Article IV  
**Last Updated:** 2026-01-24  
**Purpose:** Document all component interactions and failure modes

---

## MATRIX LEGEND

Each component documented with:
- **Inputs**: Dependencies, configuration, required services
- **Outputs**: Files, logs, API responses, side effects
- **Ports**: Network resources consumed
- **Failure Modes**: Pre-imagined scenarios with detection methods
- **Observability**: Monitoring endpoints, log locations
- **Recovery**: Rollback and restoration procedures

---

## COMPONENT 1: EPOS Doctor (epos_doctor.py)

### Purpose
Pre-flight validation system that verifies environment compliance before any execution.

### Inputs
| Dependency | Type | Required | Source |
|------------|------|----------|--------|
| Python 3.11.x | Runtime | Yes | System |
| pathlib | Library | Yes | stdlib |
| socket | Library | Yes | stdlib |
| subprocess | Library | Yes | stdlib |
| .env file | Config | Yes | `C:\Users\Jamie\workspace\epos_mcp\.env` |
| EPOS_ROOT | EnvVar | Yes | `.env` |

### Outputs
| Output | Location | Format | Purpose |
|--------|----------|--------|---------|
| Diagnostic report | stdout | Text | Human-readable status |
| Exit code | N/A | 0/1 | Automation success/failure |
| Validation log | `logs/doctor.log` | JSON | Audit trail |

### Ports
None (local validation only)

### Failure Modes

**FM-D1: Python Version Mismatch**
- **Trigger**: `sys.version_info != (3, 11, x)`
- **Impact**: Cannot proceed with execution
- **Detection**: Direct version check in code
- **Recovery**: Install Python 3.11.x
- **Prevention**: Document in onboarding

**FM-D2: Missing .env File**
- **Trigger**: `.env` not found at EPOS root
- **Impact**: Cannot load configuration
- **Detection**: `Path.exists()` check
- **Recovery**: Copy `.env.example` to `.env`, populate values
- **Prevention**: Include `.env.example` in repo

**FM-D3: Ollama Service Down**
- **Trigger**: Connection refused on :11434
- **Impact**: LLM operations unavailable
- **Detection**: Socket connection test
- **Recovery**: `ollama serve &`
- **Prevention**: Service monitoring

**FM-D4: Agent Zero Path Invalid**
- **Trigger**: `AGENT_ZERO_PATH` points to non-existent directory
- **Impact**: Cannot import Agent Zero modules
- **Detection**: Directory existence check
- **Recovery**: Update `.env` with correct path
- **Prevention**: Path validation on config change

### Observability
- **Health Endpoint**: N/A (CLI tool)
- **Logs**: `logs/doctor.log` (JSON format, one entry per run)
- **Metrics**: Exit code, check count, failure reasons

### Recovery
No state to recover (stateless validation)

---

## COMPONENT 2: Governance Gate (governance_gate.py)

### Purpose
Validates all code submissions against constitutional requirements before promotion to `/engine`.

### Inputs
| Dependency | Type | Required | Source |
|------------|------|----------|--------|
| Python 3.11.x | Runtime | Yes | System |
| pathlib | Library | Yes | stdlib |
| json | Library | Yes | stdlib |
| epos_doctor.py | Module | Yes | `/engine` |
| inbox/ directory | Filesystem | Yes | `C:\Users\Jamie\workspace\epos_mcp\inbox` |

### Outputs
| Output | Location | Format | Purpose |
|--------|----------|--------|---------|
| Promoted files | `engine/` | Python/JSON | Production code |
| Rejected files | `rejected/` | Original + receipt | Failed submissions |
| Educational receipts | `rejected/*.receipt.md` | Markdown | Violation explanations |
| Governance log | `logs/governance.log` | JSON | Audit trail |

### Ports
None (file-based operation)

### Failure Modes

**FM-G1: Missing Constitutional Header**
- **Trigger**: File lacks `# File: C:\...` header
- **Impact**: Rejected, cannot determine location
- **Detection**: Regex pattern match
- **Recovery**: Add header, resubmit
- **Prevention**: Template enforcement

**FM-G2: Hard Boundary Violation**
- **Trigger**: Code uses relative paths, silent failures, etc.
- **Impact**: Rejected with specific Article II violation
- **Detection**: AST parsing, pattern matching
- **Recovery**: Fix violation per educational receipt
- **Prevention**: Pre-submit linting

**FM-G3: Missing Failure Mode Analysis**
- **Trigger**: Component lacks pre-mortem documentation
- **Impact**: Rejected, incomplete submission
- **Detection**: Check for `failure_modes` in metadata
- **Recovery**: Document scenarios, resubmit
- **Prevention**: Submission checklist

### Observability
- **Health Endpoint**: N/A (batch processor)
- **Logs**: `logs/governance.log` (one entry per file processed)
- **Metrics**: Promotion rate, rejection rate by violation type

### Recovery
```bash
# Restore promoted file from rejected/
cp rejected/bad_file.py inbox/
# Fix issues
# Reprocess
python governance_gate.py
```

---

## COMPONENT 3: Meta Orchestrator (meta_orchestrator.py)

### Purpose
Main API for mission execution, routing requests to Agent Zero bridge.

### Inputs
| Dependency | Type | Required | Source |
|------------|------|----------|--------|
| Python 3.11.x | Runtime | Yes | System |
| FastAPI | Framework | Yes | pip |
| Uvicorn | ASGI Server | Yes | pip |
| pydantic | Validation | Yes | pip |
| epos_doctor.py | Module | Yes | `/engine` |
| agent_zero_bridge.py | Module | Yes | `/engine` |
| .env | Config | Yes | Root |

### Outputs
| Output | Location | Format | Purpose |
|--------|----------|--------|---------|
| API responses | HTTP | JSON | Client communication |
| Mission logs | `logs/missions/*.log` | JSON | Execution records |
| Health status | `/health` endpoint | JSON | Monitoring |

### Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 8001 | HTTP | API server |

### Failure Modes

**FM-O1: Port Already in Use**
- **Trigger**: Another process bound to :8001
- **Impact**: Uvicorn startup fails
- **Detection**: Port binding error
- **Recovery**: Kill existing process or change port
- **Prevention**: Pre-flight port check

**FM-O2: Agent Zero Bridge Unreachable**
- **Trigger**: `agent_zero_bridge.py` import fails
- **Impact**: All missions fail
- **Detection**: ImportError on startup
- **Recovery**: Verify Agent Zero path, reinstall
- **Prevention**: Doctor validation

**FM-O3: Mission Validation Failure**
- **Trigger**: Invalid mission JSON submitted
- **Impact**: 400 Bad Request returned
- **Detection**: Pydantic ValidationError
- **Recovery**: Fix mission JSON per error message
- **Prevention**: Schema documentation

**FM-O4: Ollama Service Interruption**
- **Trigger**: Ollama crashes mid-mission
- **Impact**: Mission hangs or fails
- **Detection**: Timeout on LLM call
- **Recovery**: Restart Ollama, retry mission
- **Prevention**: Service monitoring + auto-restart

### Observability
- **Health Endpoint**: `GET /health`
  - Returns: `{"status": "healthy", "checks": {...}}`
- **Logs**: `logs/orchestrator.log` (all API requests)
- **Metrics**: Request count, error rate, mission success rate

### Recovery
```bash
# Graceful shutdown
curl -X POST http://localhost:8001/shutdown

# Rollback to previous version
git checkout main
python engine/meta_orchestrator.py

# Or restore from backup
cp backups/meta_orchestrator_20260123.py engine/meta_orchestrator.py
```

---

## COMPONENT 4: Agent Zero Bridge (agent_zero_bridge.py)

### Purpose
Interface layer between EPOS and Agent Zero, handling mission translation and execution.

### Inputs
| Dependency | Type | Required | Source |
|------------|------|----------|--------|
| Agent Zero | Library | Yes | `C:\Users\Jamie\workspace\agent-zero` |
| EPOSAgentMission | Schema | Yes | `agent_mission_spec.py` |
| Ollama | Service | Yes | localhost:11434 |
| Work directory | Filesystem | Yes | `C:\Users\Jamie\workspace\agent-zero\work_dir` |

### Outputs
| Output | Location | Format | Purpose |
|--------|----------|--------|---------|
| Mission results | `epos_workspace/outputs/` | JSON + files | Deliverables |
| Execution logs | `logs/agent_zero_bridge.log` | JSON | Debug trail |
| Status updates | Return value | Python dict | API responses |

### Ports
None (library integration)

### Failure Modes

**FM-B1: Agent Zero Import Failure**
- **Trigger**: `AGENT_ZERO_PATH` incorrect or Agent Zero not installed
- **Impact**: Bridge initialization fails
- **Detection**: ImportError on module load
- **Recovery**: Fix path in `.env`, verify Agent Zero setup
- **Prevention**: Doctor validation

**FM-B2: Mission Translation Error**
- **Trigger**: EPOS mission format incompatible with Agent Zero
- **Impact**: Mission rejected by Agent Zero
- **Detection**: Translation function raises ValueError
- **Recovery**: Update mission schema or translation logic
- **Prevention**: Schema versioning

**FM-B3: LLM Execution Timeout**
- **Trigger**: Agent Zero task takes > 5 minutes
- **Impact**: Mission marked as failed
- **Detection**: Timeout exception
- **Recovery**: Increase timeout or simplify mission
- **Prevention**: Task complexity analysis

**FM-B4: Work Directory Full**
- **Trigger**: Disk space exhausted in work_dir/
- **Impact**: Agent Zero cannot write outputs
- **Detection**: OSError on file write
- **Recovery**: Clean old work_dir contents
- **Prevention**: Automated cleanup cron

### Observability
- **Health Check**: `health_check()` function
  - Returns: `{"ok": bool, "agent_zero_path": str}`
- **Logs**: `logs/agent_zero_bridge.log`
- **Metrics**: Mission count, success rate, avg execution time

### Recovery
```bash
# Clean Agent Zero work directory
rm -rf C:\Users\Jamie\workspace\agent-zero\work_dir/*

# Reinstall Agent Zero (if corrupted)
cd C:\Users\Jamie\workspace\agent-zero
git pull origin main
pip install -e .
```

---

## COMPONENT 5: Research Node (Future)

### Purpose
Sovereign node for market research and content intelligence.

### Inputs
| Dependency | Type | Required | Source |
|------------|------|----------|--------|
| Python 3.11.x | Runtime | Yes | System |
| node_manifest.json | Config | Yes | `nodes/research/` |
| EPOSDoctor | Module | Yes | `/engine` |

### Outputs
| Output | Location | Format | Purpose |
|--------|----------|--------|---------|
| Research reports | `nodes/research/outputs/` | JSON + MD | Deliverables |
| Node logs | `nodes/research/logs/` | JSON | Audit trail |

### Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 8010 | HTTP | Node API |

### Failure Modes

**FM-R1: Manifest Missing**
- **Trigger**: `node_manifest.json` not found
- **Impact**: Node identity unverifiable
- **Detection**: File existence check
- **Recovery**: Generate manifest from template
- **Prevention**: Sovereignty installation checklist

**FM-R2: Engine Connectivity Lost**
- **Trigger**: `EPOSDoctor` import fails
- **Impact**: Cannot validate against core
- **Detection**: ImportError
- **Recovery**: Fix sys.path, verify engine/ exists
- **Prevention**: Path validation

### Observability
- **Health Endpoint**: `GET /nodes/research/health`
- **Logs**: `nodes/research/logs/node.log`
- **Metrics**: Sovereignty score (0-100)

### Recovery
```bash
# Restart node
python nodes/research/research_doctor.py

# Rebuild manifest
python nodes/research/generate_manifest.py
```

---

## INTERACTION FLOWS

### Flow 1: Mission Execution
```
User → Meta Orchestrator (:8001)
  ↓
Orchestrator → epos_doctor.py (pre-flight)
  ↓
Orchestrator → governance_gate.py (validate mission)
  ↓
Orchestrator → agent_zero_bridge.py
  ↓
Bridge → Agent Zero (library)
  ↓
Agent Zero → Ollama (:11434)
  ↓
Agent Zero → Work Directory (outputs)
  ↓
Bridge → Orchestrator (results)
  ↓
Orchestrator → User (JSON response)
```

**Failure Points**:
- Doctor validation fails → 503 Service Unavailable
- Governance rejects → 400 Bad Request
- Bridge fails → 500 Internal Server Error
- Ollama down → 503 Service Unavailable

---

### Flow 2: Code Submission
```
Developer → inbox/ (new file)
  ↓
governance_gate.py → Constitutional checks
  ↓
  ├─ PASS → engine/ (promotion)
  └─ FAIL → rejected/ + receipt
```

**Failure Points**:
- Hard boundary violation → Educational receipt
- Missing pre-mortem → Rejection
- Invalid syntax → Lint failure

---

## DEPENDENCY GRAPH

```
epos_doctor.py (root validator)
  │
  ├─ meta_orchestrator.py
  │   ├─ agent_zero_bridge.py
  │   │   └─ Agent Zero (external)
  │   │       └─ Ollama (external)
  │   └─ governance_gate.py
  │
  └─ research_node/
      └─ research_doctor.py
```

**Critical Path**: epos_doctor.py → All components depend on it

---

## CHANGE IMPACT ANALYSIS

### Example: Changing Python Version 3.11 → 3.12

**Impacted Components**:
1. epos_doctor.py - Version check logic
2. ENVIRONMENT_SPEC.md - Canonical version
3. governance_gate.py - Validation rules
4. agent_zero_bridge.py - Dependency compatibility
5. All `/engine` Python files - Testing required

**Process**:
1. Update ENVIRONMENT_SPEC.md
2. Update epos_doctor.py version check
3. Test all components with 3.12
4. Update requirements.txt for 3.12-compatible versions
5. Constitutional amendment approval
6. Commit with full impact analysis

---

## APPENDIX: Quick Lookup

**Find component by port**:
- :8001 → meta_orchestrator.py
- :8010 → research_node
- :11434 → Ollama (external)

**Find component by log**:
- logs/doctor.log → epos_doctor.py
- logs/governance.log → governance_gate.py
- logs/orchestrator.log → meta_orchestrator.py
- logs/agent_zero_bridge.log → agent_zero_bridge.py

**Find component by path**:
- /engine → Promoted, production
- /inbox → Pending governance
- /rejected → Failed validation
- /nodes → Sovereignty nodes

---

**END OF MATRIX**

*Last Updated: 2026-01-24*  
*Components Documented: 5*  
*Total Failure Modes: 14*
