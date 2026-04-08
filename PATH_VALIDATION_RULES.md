# PATH VALIDATION RULES

**File:** C:\Users\Jamie\workspace\epos_mcp\PATH_VALIDATION_RULES.md

**Authority:** Jamie Lawson, EPOS Steward  
**Effective:** 2026-02-28  
**Classification:** BINDING GOVERNANCE REQUIREMENT

---

## MISSION

Path mixing (C:\ vs /c/ vs ~/ vs relative paths) has been the **primary source of silent failures** in EPOS development.

This document establishes **single source of truth** for all path references in code, documentation, and configuration.

---

## THE INVARIANT: WINDOWS ABSOLUTE PATHS EVERYWHERE

Every file in EPOS must include its **complete Windows absolute path** in the header comment.

### Format (All file types)

**Python:**
```python
"""
File: C:\Users\Jamie\workspace\epos_mcp\path\to\file.py
"""
```

**Bash:**
```bash
#!/bin/bash
# File: C:\Users\Jamie\workspace\epos_mcp\path\to\file.sh
```

**Markdown:**
```markdown
# File: C:\Users\Jamie\workspace\epos_mcp\path\to\file.md
```

**JSON:**
```json
{
  "_file_path": "C:\\Users\\Jamie\\workspace\\epos_mcp\\path\\to\\file.json"
}
```

### Why This Matters

| Failure Mode | Root Cause | Mitigation |
|--------------|-----------|------------|
| Path mixing in logs | Code assumes /mnt/c/ but system uses C:\ | Every file declares its canonical path |
| Silent import failures | Module imported from wrong location | Path declared at module level |
| Relative path ambiguity | Same filename in multiple directories | Absolute path eliminates ambiguity |
| Cross-platform confusion | Script works in WSL but fails in native Windows | Path is explicit, verifiable |

---

## CANONICALIZATION RULES

### Root Directory
```
Canonical: C:\Users\Jamie\workspace\epos_mcp
Aliases (forbidden):
  ❌ /mnt/c/Users/Jamie/workspace/epos_mcp (WSL path)
  ❌ ~/workspace/epos_mcp (home alias)
  ❌ ./epos_mcp (relative)
  ❌ $EPOS_ROOT (environment variable, ambiguous)
```

### Subdirectories (Standard Structure)

```
C:\Users\Jamie\workspace\epos_mcp\
├── tools\                          # Utility modules
│   ├── litellm_client.py           # LiteLLM wrapper (Path: C:\Users\Jamie\workspace\epos_mcp\tools\litellm_client.py)
│   ├── governance_gate_audit.py    # Phase 3 validator (Path: C:\Users\Jamie\workspace\epos_mcp\tools\governance_gate_audit.py)
│   └── ...
├── api\                            # TTLG entrypoint modules
│   ├── ttlg_systems_light_scout.py (Path: C:\Users\Jamie\workspace\epos_mcp\api\ttlg_systems_light_scout.py)
│   ├── ttlg_market_light_scout.py  (Path: C:\Users\Jamie\workspace\epos_mcp\api\ttlg_market_light_scout.py)
│   ├── friday_vault_summary.py     (Path: C:\Users\Jamie\workspace\epos_mcp\api\friday_vault_summary.py)
│   └── friday_check_ttlg_health.py (Path: C:\Users\Jamie\workspace\epos_mcp\api\friday_check_ttlg_health.py)
├── scripts\                        # CLI wrappers
│   ├── ttlg_systems_light_scout.sh (Path: C:\Users\Jamie\workspace\epos_mcp\scripts\ttlg_systems_light_scout.sh)
│   ├── ttlg_market_light_scout.sh  (Path: C:\Users\Jamie\workspace\epos_mcp\scripts\ttlg_market_light_scout.sh)
│   ├── friday_vault_summary.sh     (Path: C:\Users\Jamie\workspace\epos_mcp\scripts\friday_vault_summary.sh)
│   └── friday_check_ttlg_health.sh (Path: C:\Users\Jamie\workspace\epos_mcp\scripts\friday_check_ttlg_health.sh)
├── context_vault\                  # Runtime artifact storage
│   ├── scans\                      # Phase 1 Scout output
│   ├── market_scans\               # Market intelligence output
│   ├── patterns\                   # Learned patterns
│   └── intelligence\               # External intelligence
├── logs\                           # Immutable audit trails
│   ├── ttlg_diagnostics.jsonl      # TTLG lifecycle log
│   └── governance_gate_audit.jsonl # Phase 3 decisions
├── .env                            # Configuration (Path: C:\Users\Jamie\workspace\epos_mcp\.env)
├── CLAUDE.md                       # TTLG charter (Path: C:\Users\Jamie\workspace\epos_mcp\CLAUDE.md)
├── IMAGINATIVE_PROJECTION_PROTOCOL.md (Path: C:\Users\Jamie\workspace\epos_mcp\IMAGINATIVE_PROJECTION_PROTOCOL.md)
└── ... (all other files with complete paths in headers)
```

---

## CODE RULES: HOW TO USE PATHS

### Python (pathlib.Path - Mandatory)

**CORRECT:**
```python
from pathlib import Path

# Use absolute path resolution from Windows root
root = Path("C:\\Users\\Jamie\\workspace\\epos_mcp")
logs_dir = root / "logs"
audit_file = logs_dir / "ttlg_diagnostics.jsonl"

# Or use os.getcwd() + join for relative paths (with validation)
import os
cwd = Path(os.getcwd())
if "epos_mcp" not in str(cwd):
    raise ValueError(f"Must run from EPOS root. Current: {cwd}")
```

**INCORRECT:**
```python
# ❌ String paths (ambiguous across platforms)
logs_dir = "logs/ttlg_diagnostics.jsonl"

# ❌ Relative paths without validation
audit_file = "../logs/ttlg_diagnostics.jsonl"

# ❌ ~ home alias (different per user)
config_file = "~/workspace/epos_mcp/.env"

# ❌ /mnt/c/ WSL paths (breaks in native Windows)
absolute_path = "/mnt/c/Users/Jamie/workspace/epos_mcp/logs"
```

### Bash (Use $EPOS_ROOT with validation)

**CORRECT:**
```bash
#!/bin/bash
# File: C:\Users\Jamie\workspace\epos_mcp\scripts\example.sh

EPOS_ROOT="C:\Users\Jamie\workspace\epos_mcp"
if [ ! -d "$EPOS_ROOT" ]; then
    echo "❌ EPOS_ROOT not found: $EPOS_ROOT"
    exit 1
fi

LOGS_DIR="$EPOS_ROOT\logs"
python3 "$EPOS_ROOT\tools\example.py"
```

**INCORRECT:**
```bash
# ❌ Relative paths
LOGS_DIR="logs"

# ❌ WSL-style paths in native scripts
EPOS_ROOT="/mnt/c/Users/Jamie/workspace/epos_mcp"

# ❌ ~ home alias
CONFIG_FILE="~/.env"
```

### Environment Variables (Never Ambiguous)

**Set in .env (canonical path):**
```
EPOS_ROOT=C:\Users\Jamie\workspace\epos_mcp
EPOS_LOGS=$EPOS_ROOT\logs
EPOS_VAULT=$EPOS_ROOT\context_vault
```

**Use in code:**
```python
import os
from pathlib import Path

epos_root = Path(os.getenv("EPOS_ROOT", "C:\\Users\\Jamie\\workspace\\epos_mcp"))
logs_dir = epos_root / "logs"
```

---

## FILE HEADER TEMPLATE

Every file must include this header (adapted for file type):

### Python
```python
#!/usr/bin/env python3
"""
File: C:\Users\Jamie\workspace\epos_mcp\path\to\file.py

[2-3 line description]

ALIGNMENT ASSERTION (IPP Step 6):
==================================
[Full IPP Steps 1-6]
"""
```

### Bash
```bash
#!/bin/bash
# File: C:\Users\Jamie\workspace\epos_mcp\path\to\file.sh
# 
# [2-3 line description]
# 
# GOVERNANCE: [Brief governance note]
# AUTHORITY: [Which article/rule authorizes this]
```

### Markdown
```markdown
# [Title]

**File:** C:\Users\Jamie\workspace\epos_mcp\path\to\file.md

**Authority:** [Article/Charter]  
**Effective:** [Date]  
**Status:** [🟢 Active / 🟡 Draft / 🔴 Deprecated]
```

---

## VALIDATION: GOVERNANCE GATE CHECK

The **governance_gate_audit.py** script automatically checks:

✅ Every Python file has "File: C:\Users\Jamie\..." header  
✅ Every .sh script has "# File: C:\Users\Jamie\..." header  
✅ Every path in code uses pathlib.Path (not string concatenation)  
✅ No /mnt/c/ paths in production code  
✅ No ~ home aliases in code  
✅ No relative paths without explicit validation  

**If check fails:** Code is REJECTED at Phase 3.

---

## EMERGENCY PATH RECOVERY

If code references ambiguous paths:

1. **Identify all path references** in the file
   ```bash
   grep -E '(\./, /mnt/c/, ~/)' file.py
   ```

2. **Convert to absolute Windows paths**
   ```python
   # Before
   open("logs/audit.jsonl")
   
   # After
   from pathlib import Path
   epos_root = Path("C:\\Users\\Jamie\\workspace\\epos_mcp")
   open(epos_root / "logs" / "audit.jsonl")
   ```

3. **Update file header** with canonical path

4. **Resubmit** for Phase 3 validation

---

## AUTHORITY & ENFORCEMENT

**Authority:** ARTICLE XIV, Section V (Path Clarity Enforcement)  
**Enforcer:** governance_gate_audit.py (automatic, non-negotiable)  
**Violation:** Automatic code rejection at Phase 3  
**No exceptions:** This rule applies to 100% of production code

---

## FINAL PRINCIPLE

**Single Source of Truth (Path Clarity):**

> Every file's location is unambiguous and verifiable. Code can assume a canonical path structure without guessing or fallback logic. Paths are explicit, testable, and documented.

This eliminates the path-mixing failures that cost Jamie 10+ hours of debugging last time.

---

**Status:** 🟢 **BINDING ENFORCEMENT ACTIVE**

All EPOS files must follow these rules or be rejected at Phase 3 Governance Gate.

