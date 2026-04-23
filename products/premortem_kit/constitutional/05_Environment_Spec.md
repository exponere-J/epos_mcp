# File: C:\Users\Jamie\workspace\epos_mcp\ENVIRONMENT_SPEC.md

# ENVIRONMENT SPECIFICATION
## The Environment Canon (Constitutional Document #1)

**Authority:** EPOS Constitution v3.0, Article I  
**Last Updated:** 2026-01-24  
**Purpose:** Single source of truth for all environment assumptions

---

## PRIMARY ENVIRONMENT

### Operating System
- **Platform**: Windows 11
- **Architecture**: x64
- **User**: Jamie
- **Home**: `C:\Users\Jamie`

---

### Shell Environment

**Primary Shell**: Git Bash (MINGW64)
- **Path**: `C:\Program Files\Git\bin\bash.exe`
- **Purpose**: Unix-like commands on Windows
- **Path Translation**: Automatic (`/c/Users` ↔ `C:\Users`)

**Secondary Shell**: PowerShell 7
- **Path**: `C:\Program Files\PowerShell\7\pwsh.exe`
- **Purpose**: Windows-native automation
- **Use Cases**: Docker Desktop, system admin

**Prohibited**: Command Prompt (cmd.exe)
- **Reason**: Inconsistent path handling, limited tooling

---

### Python Environment

**Version**: 3.11.x (specifically 3.11.7 or later)
- **Min Version**: 3.11.0
- **Max Version**: < 3.12.0 (avoid 3.13 due to ABI changes)

**Validation**:
```bash
python --version
# Expected: Python 3.11.7 (or 3.11.8, 3.11.9)
```

**Installation Path**: `C:\Users\Jamie\AppData\Local\Programs\Python\Python311`

**Why 3.11.x?**
- ✅ Stable ABI for native extensions
- ✅ Compatible with Agent Zero dependencies
- ✅ Widely supported by PyPI packages
- ❌ 3.13 breaks many C extensions
- ❌ 3.10 missing some type features

---

### Path Conventions

**In Code (Always)**: Windows-style absolute paths

```python
from pathlib import Path

# CORRECT
EPOS_ROOT = Path("C:/Users/Jamie/workspace/epos_mcp")
AGENT_ZERO_ROOT = Path("C:/Users/Jamie/workspace/agent-zero")

# WRONG - Ambiguous
EPOS_ROOT = Path("~/workspace/epos_mcp")  # Depends on shell
```

**In Documentation**: Windows-style for consistency

**In Shell Scripts**: Let Git Bash handle translation

```bash
# Git Bash automatically translates
cd /c/Users/Jamie/workspace/epos_mcp
# Becomes: C:\Users\Jamie\workspace\epos_mcp
```

---

## DIRECTORY STRUCTURE

### EPOS Root
**Path**: `C:\Users\Jamie\workspace\epos_mcp`

**Structure**:
```
epos_mcp/
├── engine/                 # Promoted, production code
├── inbox/                  # Pending governance review
├── rejected/               # Failed governance checks
├── logs/                   # All operational logs
├── docs/                   # Documentation
├── tests/                  # Validation tests
├── .env                    # Environment variables
├── requirements.txt        # Pinned dependencies
└── epos_doctor.py          # Pre-flight validation
```

---

### Agent Zero Root
**Path**: `C:\Users\Jamie\workspace\agent-zero`

**Structure**:
```
agent-zero/
├── python/                 # Agent Zero core
├── models/                 # LLM configurations
├── work_dir/               # Agent workspace
└── .env                    # Agent Zero config
```

---

### Operational Workspace
**Path**: `C:\Users\Jamie\epos_workspace`

**Purpose**: Runtime execution sandbox for missions

**Structure**:
```
epos_workspace/
├── missions/               # Active mission files
├── outputs/                # Mission results
├── temp/                   # Temporary files
└── backups/                # Rollback snapshots
```

---

## REQUIRED SERVICES

### Ollama (LLM Backend)
- **Port**: 11434
- **URL**: http://localhost:11434
- **Models**: llama3.2:latest (minimum)

**Validation**:
```bash
curl http://localhost:11434/api/tags
# Expected: JSON with available models
```

**Start Command**:
```bash
ollama serve &
```

---

### Docker Desktop
- **Version**: 4.28.0 or later
- **Purpose**: MCP containerization
- **Required**: Yes (for future Docker MCP integration)

**Validation**:
```bash
docker --version
# Expected: Docker version 4.28.0+

docker ps
# Expected: No errors (service running)
```

---

### Git
- **Version**: 2.40.0 or later
- **Purpose**: Version control, Git Bash shell

**Validation**:
```bash
git --version
# Expected: git version 2.40.0+
```

---

## CONFIGURATION MANAGEMENT

### Environment Variables (.env)

**Location**: `C:\Users\Jamie\workspace\epos_mcp\.env`

**Required Variables**:
```bash
# EPOS Paths
EPOS_ROOT=C:/Users/Jamie/workspace/epos_mcp
EPOS_WORKSPACE=C:/Users/Jamie/epos_workspace

# Agent Zero Integration
AGENT_ZERO_PATH=C:/Users/Jamie/workspace/agent-zero
AGENT_ZERO_WORK_DIR=C:/Users/Jamie/workspace/agent-zero/work_dir

# Services
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# API Configuration
EPOS_API_PORT=8001
EPOS_API_HOST=127.0.0.1

# Logging
LOG_LEVEL=INFO
LOG_DIR=C:/Users/Jamie/workspace/epos_mcp/logs
```

**Loading Strategy**:
```python
# MUST be called in all entrypoints
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
```

**Validation**:
```bash
# Verify .env is loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('EPOS_ROOT'))"
# Expected: C:/Users/Jamie/workspace/epos_mcp
```

---

## DEPENDENCY MANAGEMENT

### Requirements File
**File**: `requirements.txt`

**Pinning Strategy**: Exact versions (no `>=` or `~=`)

```txt
# Core Framework
fastapi==0.115.5
uvicorn==0.32.1
pydantic==2.10.3

# Environment
python-dotenv==1.0.0

# Utilities
pathlib==1.0.1  # Backport for < 3.4
```

**Why Exact Versions?**
- ✅ Reproducible environments
- ✅ Prevents surprise breakage
- ✅ Clear upgrade decisions

**Installation**:
```bash
pip install -r requirements.txt --no-deps
# --no-deps prevents transitive dependency surprises
```

**Validation**:
```bash
pip check
# Expected: No broken requirements found.
```

---

### Forbidden Dependencies
**Never use**:
- Flask 3.0.3 (doesn't exist for Python 3.11)
- Any package requiring Python 3.13+
- Packages with native code not pre-built for Windows

**Check before adding**:
```bash
# Dry run install
pip install <package> --dry-run
```

---

## NETWORK CONFIGURATION

### Ports
| Service | Port | Purpose |
|---------|------|---------|
| EPOS API | 8001 | Main orchestration API |
| Ollama | 11434 | LLM backend |
| Agent Zero | N/A | Library integration |
| Research Node | 8010 | Future sovereignty node |

**Validation**:
```bash
# Check port availability
netstat -an | grep 8001
# Expected: Empty (port free) or listening (service running)
```

---

### Firewall
- **Ollama**: Allow localhost:11434
- **EPOS API**: Allow localhost:8001
- **External**: No inbound (local-only operation)

---

## VALIDATION COMMANDS

### Full Environment Check
```bash
cd C:\Users\Jamie\workspace\epos_mcp
python epos_doctor.py
```

**Expected Output**:
```
🏥 EPOS ENVIRONMENT DIAGNOSTIC

✅ Python 3.11.7 detected
✅ EPOS root exists: C:\Users\Jamie\workspace\epos_mcp
✅ Agent Zero found: C:\Users\Jamie\workspace\agent-zero
✅ Ollama responding: http://localhost:11434
✅ .env loaded successfully
✅ All dependencies installed
✅ Port 8001 available
✅ Log directory writable

🎉 ENVIRONMENT VALIDATED - Ready for operations
```

---

### Individual Checks

**Python Version**:
```bash
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
# Expected: Python 3.11.7 (or higher 3.11.x)
```

**Path Resolution**:
```bash
python -c "from pathlib import Path; print(Path('C:/Users/Jamie/workspace/epos_mcp').resolve())"
# Expected: C:\Users\Jamie\workspace\epos_mcp
```

**Ollama**:
```bash
curl -s http://localhost:11434/api/tags | python -m json.tool
# Expected: Valid JSON with models list
```

**Dependencies**:
```bash
pip check
# Expected: No broken requirements found.
```

**.env Loading**:
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; assert os.getenv('EPOS_ROOT') == 'C:/Users/Jamie/workspace/epos_mcp', 'EPOS_ROOT not set'"
# Expected: No output (assertion passes)
```

---

## TROUBLESHOOTING

### Common Issues

**Issue**: "Python 3.13 installed"
**Fix**:
```bash
# Uninstall 3.13
py -3.13 -m pip uninstall -y python

# Install 3.11
# Download from python.org/downloads/release/python-3117/
```

---

**Issue**: "EPOS_ROOT not set"
**Fix**:
```bash
# Verify .env exists
ls C:\Users\Jamie\workspace\epos_mcp\.env

# Check contents
cat C:\Users\Jamie\workspace\epos_mcp\.env | grep EPOS_ROOT

# Reload
python -c "from dotenv import load_dotenv; load_dotenv('C:/Users/Jamie/workspace/epos_mcp/.env')"
```

---

**Issue**: "Ollama not responding"
**Fix**:
```bash
# Check service
ollama list

# Restart
ollama serve &

# Verify
curl http://localhost:11434/api/tags
```

---

**Issue**: "Port 8001 already in use"
**Fix**:
```bash
# Find process
netstat -ano | findstr :8001

# Kill process (use PID from above)
taskkill /PID <PID> /F

# Verify
netstat -an | grep 8001
```

---

## UPDATE PROCEDURE

### Changing Environment Spec

**Process**:
1. Propose change via constitutional amendment
2. Update this document
3. Run full validation suite
4. Update `epos_doctor.py` if new checks needed
5. Commit with message: `ENV_SPEC: <change description>`

**Example**:
```bash
git checkout -b env-spec/python-312-upgrade
# Edit ENVIRONMENT_SPEC.md
python epos_doctor.py
git commit -m "ENV_SPEC: Upgrade to Python 3.12 for performance"
```

---

## APPENDIX: Shell Comparison

| Feature | Git Bash | PowerShell | cmd.exe |
|---------|----------|------------|---------|
| Unix commands | ✅ | ❌ | ❌ |
| Path translation | ✅ | ❌ | ❌ |
| Tab completion | ✅ | ✅ | Limited |
| Docker CLI | ⚠️ | ✅ | ✅ |
| Python scripts | ✅ | ✅ | ✅ |
| EPOS primary | ✅ | Secondary | ❌ |

---

**END OF SPECIFICATION**

*Last Validated: 2026-01-24*  
*Next Review: 2026-02-24 (30 days)*
