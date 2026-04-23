# REMEDIATION LESSON: ERR-PATH-001
## Path Format Constitutional Requirement

**Lesson ID**: PATH-LESSON-001  
**Difficulty Level**: STANDARD  
**Constitutional Authority**: PATH_CLARITY_RULES.md Article I, Section 1.1  
**Estimated Completion Time**: 30 minutes  
**Success Criteria**: Pass all 3 exercises with 100% accuracy

---

## 🚨 What You Did Wrong

### Your Actual Submission:
```python
# Line 42 in your file:
path = '/c/Users/Jamie/workspace'  # ❌ POSIX absolute path

# Line 58 in your file:
config_path = '~/workspace/config.json'  # ❌ Tilde expansion

# Line 73 in your file:
data_dir = '../data/files'  # ❌ Relative path
```

### The Violation:
You used **non-canonical path formats** that violate EPOS Constitution v3.1's path clarity requirements.

---

## 📜 The Constitutional Rule

**PATH_CLARITY_RULES.md Article I, Section 1.1** states:

> "ALL paths in the EPOS ecosystem SHALL use Windows absolute format."

**Canonical Form**:
```
C:\Users\Jamie\workspace\epos_mcp\engine\governance_gate.py
```

**Forbidden Forms**:
- `/c/Users/Jamie/...` ← POSIX absolute (FORBIDDEN)
- `~/workspace/...` ← Tilde expansion (FORBIDDEN)
- `../engine/file.py` ← Relative parent (FORBIDDEN)
- `./current/file.py` ← Relative current (FORBIDDEN)

---

## 💡 Why This Matters

### The Real-World Impact:

1. **Context Dependency**
   - Your code works in Git Bash
   - **FAILS** in PowerShell
   - **FAILS** in VS Code integrated terminal
   - **FAILS** when Docker mounts volumes

2. **Silent Failures**
   ```python
   # This might work:
   with open('/c/Users/Jamie/file.txt', 'r') as f:
       data = f.read()
   
   # This might fail silently (wrong context):
   # FileNotFoundError: [Errno 2] No such file or directory
   ```

3. **Audit Trail Corruption**
   ```
   # Mixed formats in logs make debugging impossible:
   [2026-02-03] Processed: /c/Users/Jamie/data.txt
   [2026-02-03] Saved to: C:\Users\Jamie\output.txt
   [2026-02-03] Failed: ~/workspace/temp.json
   
   # Which paths are the same file? Impossible to tell.
   ```

4. **Cross-Platform Disasters**
   - Windows paths work everywhere (forward slashes accepted)
   - POSIX paths **only** work in Unix-like shells
   - EPOS operates in **mixed environment**

---

## ✅ The Correct Implementation

### Method 1: Dynamic Path Construction (RECOMMENDED)
```python
from pathlib import Path

# Construct from current file location
script_location = Path(__file__)
project_root = script_location.parent.parent
config_path = project_root / "config" / "settings.json"

# Verify before use
if not config_path.exists():
    raise FileNotFoundError(f"Config missing: {config_path}")

# Open safely
with open(config_path, 'r') as f:
    config = json.load(f)
```

**Why this is best**:
- ✅ Works in ANY terminal
- ✅ Works when file is moved
- ✅ Automatically handles separators
- ✅ Built-in existence checking

### Method 2: Explicit Absolute Paths
```python
from pathlib import Path

# Explicit Windows absolute path
workspace = Path("C:/Users/Jamie/workspace/epos_mcp")
engine_dir = workspace / "engine"
gate_file = engine_dir / "governance_gate.py"

# Note: Forward slashes (/) work on Windows
# pathlib.Path handles conversion automatically
```

**When to use this**:
- Configuration files with known locations
- Root-level directory references
- Constants that never change

### Method 3: Environment Variable + Validation
```python
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    raise FileNotFoundError(f".env missing: {env_path}")

load_dotenv(env_path)

# Get path from environment
agent_path = os.getenv("AGENT_ZERO_PATH")
if not agent_path:
    raise ValueError("AGENT_ZERO_PATH not set in environment")

# Convert to Path object and verify
agent_path = Path(agent_path)
if not agent_path.exists():
    raise FileNotFoundError(f"Agent Zero not found: {agent_path}")
```

**When to use this**:
- Paths that vary per deployment
- User-specific configurations
- External tool locations

---

## 🎓 Practice Exercises

### Exercise 1: Path Conversion (PATH-EX-001)

**Task**: Convert these POSIX/relative paths to Windows absolute format using `pathlib.Path`.

**Given these paths**:
1. `/c/Users/Jamie/workspace/epos_mcp/inbox`
2. `~/workspace/epos_mcp/governance`
3. `../engine/governance_gate.py` (assume you're in `/workspace/epos_mcp/tools/`)
4. `./data/files` (assume you're in `/workspace/epos_mcp/`)
5. `/mnt/c/Users/Jamie/workspace/agent-zero`

**Your answers** (write in a file called `path_ex_001_answers.txt`):
```
1. C:/Users/Jamie/workspace/epos_mcp/inbox
2. [YOUR ANSWER]
3. [YOUR ANSWER]
4. [YOUR ANSWER]
5. [YOUR ANSWER]
```

**Validation**:
```bash
python governance/enforcement/exercise_validator.py PATH-EX-001 path_ex_001_answers.txt
```

**Expected output**: `✅ PASS: Found 5 valid Windows absolute paths`

---

### Exercise 2: Code Violation Identification (PATH-EX-002)

**Task**: Identify ALL path violations in this code sample.

```python
import os
import json

def load_config():
    # Load configuration from relative path
    config_path = '../config/settings.json'
    
    with open(config_path) as f:
        return json.load(f)

def process_data():
    # Get data directory from home
    data_dir = '~/workspace/data'
    
    # Process all files
    for file in os.listdir(data_dir):
        filepath = f"{data_dir}/{file}"
        process_file(filepath)

def save_output(data):
    # Save to POSIX absolute path
    output_path = '/c/Users/Jamie/output.json'
    
    with open(output_path, 'w') as f:
        json.dump(data, f)
```

**Your answers** (create `path_ex_002_answers.md`):
```markdown
## Violations Found:

1. Line __: Violation type __
   - Current: `[code snippet]`
   - Correct: `[corrected code]`

2. Line __: [continue for all violations]
```

**Hint**: There are 5 violations in this code.

---

### Exercise 3: Write Correct Path Code (PATH-EX-003)

**Task**: Write Python code that performs these operations using ONLY Windows absolute paths and `pathlib.Path`:

1. Construct path to `governance/registry/VIOLATION_CODES.json` from project root
2. Verify the file exists before opening
3. Load the JSON content
4. Handle the case where file doesn't exist with a clear error message

**Your code** (save as `path_ex_003_solution.py`):
```python
from pathlib import Path
import json

# Your code here
```

**Validation**:
```bash
python path_ex_003_solution.py
```

**Expected behavior**:
- If file exists: Prints violation codes
- If file missing: Raises clear error with absolute path shown

---

## 🔍 Self-Validation Checklist

Before submitting your exercises, verify:

- [ ] All paths use Windows absolute format (`C:/Users/...`)
- [ ] All paths constructed with `pathlib.Path`
- [ ] All file operations include `.exists()` check
- [ ] No string concatenation for path building
- [ ] No POSIX paths (`/c/`, `/mnt/c/`)
- [ ] No tilde expansion (`~/`)
- [ ] No relative paths (`../`, `./`)

---

## 📝 Next Steps

### After Completing Exercises:

1. **Validate your work**:
   ```bash
   python governance/enforcement/exercise_validator.py PATH-EX-001 path_ex_001_answers.txt
   python governance/enforcement/exercise_validator.py PATH-EX-002 path_ex_002_answers.md
   python path_ex_003_solution.py
   ```

2. **Submit to remediation inbox**:
   ```bash
   mkdir -p inbox/remediation/agent_zero/
   cp path_ex_*.* inbox/remediation/agent_zero/
   ```

3. **Request validation**:
   ```bash
   python governance_gate.py --validate-remediation agent_zero PATH-LESSON-001
   ```

4. **Upon passing**: Retry your original mission (VAULT-INIT-001) with corrected code

---

## 🎯 Success Criteria

You have successfully completed this lesson when:

✅ All 3 exercises pass validation  
✅ You can explain why path mixing causes failures  
✅ You can identify path violations in unfamiliar code  
✅ You can write path-compliant code from scratch  

**Estimated mastery time**: 1-2 mission cycles after lesson completion

---

## 📚 Additional Resources

### Reference Documents:
- `PATH_CLARITY_RULES.md` - Complete path specification
- `ARCHITECTURAL_ANALYSIS.md` - AP-001 (Path Mixing anti-pattern)
- Python `pathlib` docs - https://docs.python.org/3/library/pathlib.html

### Common Questions:

**Q: Why not just use `os.path.join()`?**  
A: `os.path` is legacy and platform-specific. `pathlib.Path` is modern, cross-platform, and has better error handling.

**Q: Do I need to use backslashes `\` in Windows paths?**  
A: No! `pathlib.Path` accepts forward slashes `/` on Windows and converts automatically.

**Q: What if my path is from user input?**  
A: Always validate and convert: `user_path = Path(user_input); if not user_path.exists(): raise ValueError(...)`

---

## ⚠️ Consequences of Repeated Failure

- **First failure**: This lesson (STANDARD difficulty)
- **Second failure**: COMPREHENSIVE lesson (10 exercises + essay)
- **Third failure**: Peer review required
- **Fifth failure**: Constitutional Arbiter manual review

**Avoid escalation**: Take time to internalize these principles now.

---

**Lesson Version**: 1.0.0  
**Last Updated**: 2026-02-03  
**Maintenance**: Reward Bus auto-updates based on effectiveness metrics

---

**END OF REMEDIATION LESSON**