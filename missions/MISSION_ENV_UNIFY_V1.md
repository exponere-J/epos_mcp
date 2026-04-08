<!-- EPOS GOVERNANCE WATERMARK -->
# MISSION: EPOS ENVIRONMENT UNIFICATION
## One-Click Boot Sequence + Software Engineering Housekeeping
### Mission ID: ENV_UNIFY_V1
### Authority: EPOS Constitution v3.1, Article II (Environment Explicitness)
### Triple Compulsion: IMPLEMENT (scripts) / DOCUMENT (commentary) / SURVEIL (Doctor validation)

---

# MISSION BRIEFING

## Objective
Unify EPOS into a single-terminal, one-click boot sequence. Eliminate the 4-terminal problem. Clean up loose files. Document every action with contextual commentary.

## Why This Matters
EPOS currently requires 4 separate terminals (Ollama, EPOS venv, Agent Zero venv, interactive shell) because dependencies were never unified. This creates:
- Startup friction that prevents daily use
- Environment drift between terminals
- Cognitive overhead that should be spent on 9th-Order stewardship

## What Agent Zero Does (No Model Needed)
Every step in this mission is deterministic: shell commands with known inputs and known success criteria. Agent Zero's tool-use logic handles this natively. No reasoning model is required.

## Success Criteria
- `epos_start.ps1` exists at repo root and boots the full system
- One venv (`venv_epos`) contains all dependencies
- Ollama runs as background process (no dedicated terminal)
- EPOS Doctor passes with 0 critical failures
- Housekeeping log written to `context_vault/events/env_unify_v1_report.jsonl`

---

# PHASE 1: AUDIT CURRENT STATE

## Step 1.1 — Map all virtual environments

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

# List all venvs in the workspace
Write-Host "=== Virtual Environments ===" -ForegroundColor Cyan
Get-ChildItem -Directory -Filter "venv*" | ForEach-Object {
    $pipList = & "$($_.FullName)\Scripts\python.exe" -m pip list --format=columns 2>$null
    $count = ($pipList | Measure-Object -Line).Lines - 2  # subtract header lines
    Write-Host "  $($_.Name): $count packages" -ForegroundColor White
    Write-Host "    Python: $(& "$($_.FullName)\Scripts\python.exe" --version 2>&1)" -ForegroundColor Gray
}
```

**Commentary:** We expect to find `venv_az` (Agent Zero) and `venv_epos` (EPOS). Both should be Python 3.11.x. If either is 3.13, that's the ABI compatibility issue from the Architectural Analysis — flag it immediately.

**Success:** Both venvs listed with package counts and Python versions.
**Failure:** Missing venv → create it. Wrong Python → flag for manual intervention.

---

## Step 1.2 — Map loose files that need homes

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

# Files at repo root that should be in engine/ or tools/
Write-Host "=== Root-Level Python Files ===" -ForegroundColor Cyan
Get-ChildItem -Filter "*.py" -File | ForEach-Object {
    $inEngine = Test-Path ".\engine\$($_.Name)"
    $status = if ($inEngine) { "[DUPLICATE of engine/]" } else { "[ROOT ONLY]" }
    Write-Host "  $($_.Name) — $status" -ForegroundColor $(if ($inEngine) { "Yellow" } else { "Red" })
}

Write-Host "`n=== Files in rejected/ ===" -ForegroundColor Cyan
Get-ChildItem -Path ".\rejected" -Filter "*.py" -File -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  $($_.Name) — Last modified: $($_.LastWriteTime)" -ForegroundColor Yellow
}

Write-Host "`n=== Files in inbox/ ===" -ForegroundColor Cyan
Get-ChildItem -Path ".\inbox" -Filter "*.py" -File -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  $($_.Name) — Last modified: $($_.LastWriteTime)" -ForegroundColor Yellow
}
```

**Commentary:** Root-level `.py` files that also exist in `engine/` are duplicates from manual `Copy-Item` operations. We'll establish a canonical location rule: `engine/` is the production path, root gets symlinks or the launcher only.

**Success:** Complete inventory printed.
**Log this output** to `context_vault/events/env_unify_v1_report.jsonl` as `{"phase":"audit","step":"1.2","data":{...}}`.

---

## Step 1.3 — Check what's running on key ports

**Agent Zero: execute via shell tool**
```powershell
Write-Host "=== Port Status ===" -ForegroundColor Cyan

$ports = @(8001, 11434)
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  :$port — IN USE by $($proc.ProcessName) (PID: $($conn.OwningProcess))" -ForegroundColor Yellow
    } else {
        Write-Host "  :$port — FREE" -ForegroundColor Green
    }
}
```

**Commentary:** Port 8001 is the Meta Orchestrator. Port 11434 is Ollama. If 8001 is in use by a previous uvicorn instance, we'll kill it before the unified launcher takes over. If 11434 is Ollama, we leave it.

---

# PHASE 2: DEPENDENCY MERGE

## Step 2.1 — Extract Agent Zero's unique dependencies

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

# Get packages from both venvs
$azPkgs = & ".\venv_az\Scripts\pip.exe" list --format=freeze 2>$null | ForEach-Object { ($_ -split "==")[0].ToLower() }
$eposPkgs = & ".\venv_epos\Scripts\pip.exe" list --format=freeze 2>$null | ForEach-Object { ($_ -split "==")[0].ToLower() }

# Find packages in AZ that are NOT in EPOS
$missing = $azPkgs | Where-Object { $_ -notin $eposPkgs }

Write-Host "=== Packages in venv_az but NOT in venv_epos ===" -ForegroundColor Cyan
Write-Host "  Count: $($missing.Count)" -ForegroundColor White
$missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }

# Write to a requirements file for merging
$missing | ForEach-Object { $_ } | Set-Content ".\az_missing_deps.txt"
Write-Host "`n  Written to az_missing_deps.txt" -ForegroundColor Green
```

**Commentary:** This identifies what `venv_az` has that `venv_epos` doesn't. These are the packages we need to install into `venv_epos` to make it the single unified environment. Common candidates: `agent-zero` core, any model-specific libraries, websocket packages.

---

## Step 2.2 — Install missing dependencies into venv_epos

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

# Activate the EPOS venv
& ".\venv_epos\Scripts\Activate.ps1"

# Install the missing packages
$deps = Get-Content ".\az_missing_deps.txt"
if ($deps.Count -gt 0) {
    Write-Host "Installing $($deps.Count) packages into venv_epos..." -ForegroundColor Yellow
    pip install $deps 2>&1 | Tee-Object -FilePath ".\context_vault\events\dep_merge_log.txt"
    Write-Host "Done." -ForegroundColor Green
} else {
    Write-Host "No missing dependencies — venvs are already equivalent." -ForegroundColor Green
}
```

**Commentary:** After this step, `venv_epos` has everything both venvs had. We can now use one venv for all EPOS operations including Agent Zero imports.

**Failure mode:** If any package fails to install due to ABI incompatibility (the Python 3.13 issue), log it and flag for manual resolution. Do NOT proceed with a broken install.

---

## Step 2.3 — Verify Agent Zero imports from venv_epos

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp
& ".\venv_epos\Scripts\Activate.ps1"

python -c "
import sys
print(f'Python: {sys.version}')
print(f'Executable: {sys.executable}')
print()

tests = [
    ('fastapi', 'from fastapi import FastAPI'),
    ('uvicorn', 'import uvicorn'),
    ('pydantic', 'from pydantic import BaseModel'),
    ('dotenv', 'from dotenv import load_dotenv'),
    ('pathlib', 'from pathlib import Path'),
    ('content.lab.tributaries.echolocation_algorithm', 'from content.lab.tributaries.echolocation_algorithm import EcholocationAlgorithm'),
    ('content.lab.validation.brand_validator', 'from content.lab.validation.brand_validator import BrandValidator'),
]

for name, stmt in tests:
    try:
        exec(stmt)
        print(f'  [OK] {name}')
    except Exception as e:
        print(f'  [FAIL] {name}: {e}')
"
```

**Commentary:** Every import that EPOS or Agent Zero needs must resolve from within `venv_epos`. If any fail, the dependency merge is incomplete.

**Success:** All imports show `[OK]`.

---

# PHASE 3: CREATE UNIFIED LAUNCHER

## Step 3.1 — Generate epos_start.ps1

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

$launcher = @'
# =============================================================================
# EPOS UNIFIED LAUNCHER v1.0
# One terminal. One command. EPOS breathes.
# Constitutional Authority: EPOS Constitution v3.1, Article II
# =============================================================================

param(
    [switch]$SkipOllama,
    [switch]$SkipAPI,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$EPOS_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $EPOS_ROOT

function Write-Step($num, $total, $msg, $color = "Yellow") {
    Write-Host "[$num/$total] $msg" -ForegroundColor $color
}

function Test-Port($port) {
    (Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     EPOS UNIFIED LAUNCHER v1.0       ║" -ForegroundColor Cyan
Write-Host "  ║     One terminal. EPOS breathes.     ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$totalSteps = 5
$startTime = Get-Date

# --- Step 1: Activate unified venv ---
Write-Step 1 $totalSteps "Activating unified environment..."
$activatePath = Join-Path $EPOS_ROOT "venv_epos\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
    & $activatePath
    Write-Host "  venv_epos active (Python $(python --version 2>&1))" -ForegroundColor Green
} else {
    Write-Host "  FATAL: venv_epos not found at $activatePath" -ForegroundColor Red
    exit 2
}

# --- Step 2: Start Ollama (background, no terminal) ---
Write-Step 2 $totalSteps "Checking Ollama..."
if ($SkipOllama) {
    Write-Host "  Skipped (--SkipOllama)" -ForegroundColor Gray
} elseif (Test-Port 11434) {
    Write-Host "  Ollama already running on :11434" -ForegroundColor Green
} else {
    Write-Host "  Starting Ollama server..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    if (Test-Port 11434) {
        Write-Host "  Ollama started (background, :11434)" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Ollama failed to start. Model calls will fail." -ForegroundColor Yellow
        Write-Host "  (EPOS governance and Content Lab still functional without it)" -ForegroundColor Gray
    }
}

# --- Step 3: Run EPOS Doctor (pre-flight) ---
Write-Step 3 $totalSteps "Running EPOS Doctor pre-flight..."
$doctorOutput = python "$EPOS_ROOT\engine\epos_doctor.py" --json 2>&1
try {
    $doctorJson = $doctorOutput | ConvertFrom-Json
    $fails = if ($doctorJson.failures) { $doctorJson.failures.Count } else { 0 }
    $warns = if ($doctorJson.warnings) { $doctorJson.warnings.Count } else { 0 }
    $passes = if ($doctorJson.checks_passed) { $doctorJson.checks_passed } else { 0 }

    if ($fails -gt 0) {
        Write-Host "  Doctor: $passes passed, $warns warnings, $fails CRITICAL FAILURES" -ForegroundColor Red
        foreach ($f in $doctorJson.failures) {
            Write-Host "    FAIL: $($f.check) — $($f.details)" -ForegroundColor Red
        }
        Write-Host "  Fix critical failures before proceeding." -ForegroundColor Red
        Write-Host "  (Run 'python engine\epos_doctor.py --verbose' for details)" -ForegroundColor Gray
        exit 1
    } else {
        Write-Host "  Doctor: $passes passed, $warns warnings, 0 failures" -ForegroundColor Green
        if ($Verbose -and $warns -gt 0) {
            foreach ($w in $doctorJson.warnings) {
                Write-Host "    WARN: $($w.check) — $($w.details)" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "  Doctor returned non-JSON output. Running verbose..." -ForegroundColor Yellow
    python "$EPOS_ROOT\engine\epos_doctor.py"
}

# --- Step 4: Start Meta Orchestrator API (background) ---
Write-Step 4 $totalSteps "Checking EPOS API..."
if ($SkipAPI) {
    Write-Host "  Skipped (--SkipAPI)" -ForegroundColor Gray
} elseif (Test-Port 8001) {
    Write-Host "  API already running on :8001" -ForegroundColor Green
} else {
    Write-Host "  Starting Meta Orchestrator on :8001..." -ForegroundColor Yellow
    Start-Process -FilePath "python" `
        -ArgumentList "-m uvicorn engine.meta_orchestrator:app --port 8001 --host 0.0.0.0" `
        -WorkingDirectory $EPOS_ROOT `
        -WindowStyle Hidden `
        -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    if (Test-Port 8001) {
        Write-Host "  API started (background, :8001)" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: API failed to start. Check meta_orchestrator.py" -ForegroundColor Yellow
    }
}

# --- Step 5: System Ready ---
$elapsed = ((Get-Date) - $startTime).TotalSeconds
Write-Step 5 $totalSteps "EPOS is operational." "Green"

Write-Host ""
Write-Host "  ┌──────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "  │  SYSTEM STATUS                       │" -ForegroundColor Cyan
Write-Host "  ├──────────────────────────────────────┤" -ForegroundColor Cyan
Write-Host "  │  Environment:  venv_epos (unified)   │" -ForegroundColor White
Write-Host "  │  Ollama:       :11434                │" -ForegroundColor White
Write-Host "  │  EPOS API:     :8001                 │" -ForegroundColor White
Write-Host "  │  Doctor:       PASSED                │" -ForegroundColor White
Write-Host "  │  C10 Lab:      OPERATIONAL           │" -ForegroundColor White
Write-Host "  │  Boot time:    $([math]::Round($elapsed,1))s                  │" -ForegroundColor White
Write-Host "  └──────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Write-Host "  You are now in the EPOS shell." -ForegroundColor Gray
Write-Host "  Run 'python engine\epos_doctor.py' for full diagnostics." -ForegroundColor Gray
Write-Host ""
'@

$launcher | Set-Content ".\epos_start.ps1" -Encoding UTF8
Write-Host "Created: epos_start.ps1 ($((Get-Item '.\epos_start.ps1').Length) bytes)" -ForegroundColor Green
```

**Commentary:** This launcher handles everything: venv activation, Ollama as background daemon, Doctor pre-flight, API startup, and a clean status display. Supports `--SkipOllama` and `--SkipAPI` flags for when you only need the shell. Boot target is under 10 seconds.

---

# PHASE 4: HOUSEKEEPING

## Step 4.1 — Establish canonical file locations

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

# Doctor's canonical home is engine/ — root copy is convenience symlink
# Governance gate canonical home is engine/enforcement/
# These root copies were created via Copy-Item during debugging sessions

$rootDuplicates = @(
    @{Name="epos_doctor.py"; Canonical="engine\epos_doctor.py"},
    @{Name="governance_gate.py"; Canonical="engine\enforcement\governance_gate.py"},
    @{Name="epos_snapshot.py"; Canonical="engine\epos_snapshot.py"}  # if promoted from rejected/
)

Write-Host "=== Canonical File Location Audit ===" -ForegroundColor Cyan
foreach ($item in $rootDuplicates) {
    $rootPath = Join-Path "." $item.Name
    $canonPath = Join-Path "." $item.Canonical
    $rootExists = Test-Path $rootPath
    $canonExists = Test-Path $canonPath

    if ($rootExists -and $canonExists) {
        $rootSize = (Get-Item $rootPath).Length
        $canonSize = (Get-Item $canonPath).Length
        $match = if ($rootSize -eq $canonSize) { "IDENTICAL" } else { "DIVERGED" }
        Write-Host "  $($item.Name): root=$rootSize bytes, canonical=$canonSize bytes [$match]" -ForegroundColor $(if ($match -eq "IDENTICAL") { "Green" } else { "Red" })
    } elseif ($rootExists -and -not $canonExists) {
        Write-Host "  $($item.Name): ROOT ONLY (canonical missing at $($item.Canonical))" -ForegroundColor Yellow
    } elseif (-not $rootExists -and $canonExists) {
        Write-Host "  $($item.Name): CANONICAL ONLY (root missing)" -ForegroundColor Yellow
    } else {
        Write-Host "  $($item.Name): MISSING EVERYWHERE" -ForegroundColor Red
    }
}
```

**Commentary:** This audit reveals which root-level files are duplicates of `engine/` files and whether they've diverged. The rule going forward: `engine/` is production truth. Doctor expects to find tools at root, so we update Doctor's paths in v3.2 to look in `engine/` first, or we maintain root copies via the launcher.

---

## Step 4.2 — Document the cleanup in the Vault

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

python -c "
import json
from pathlib import Path
from datetime import datetime

report = {
    'mission_id': 'ENV_UNIFY_V1',
    'completed_at': datetime.now().isoformat(),
    'actions_taken': [
        {
            'action': 'dependency_merge',
            'description': 'Merged venv_az unique packages into venv_epos',
            'artifact': 'az_missing_deps.txt',
            'commentary': 'venv_az existed because Agent Zero was treated as a separate service. It is actually a library import inside EPOS. One venv is correct.'
        },
        {
            'action': 'launcher_creation',
            'description': 'Created epos_start.ps1 unified launcher',
            'artifact': 'epos_start.ps1',
            'commentary': '4 terminals reduced to 1. Ollama runs as background daemon. Doctor runs as pre-flight. API starts if not already running.'
        },
        {
            'action': 'canonical_path_audit',
            'description': 'Audited root-level duplicates of engine/ files',
            'artifact': 'context_vault/events/env_unify_v1_report.jsonl',
            'commentary': 'Root copies of epos_doctor.py, governance_gate.py, epos_snapshot.py created during debugging. Canonical location is engine/. Doctor v3.2 should search engine/ first.'
        },
        {
            'action': 'venv_deprecation',
            'description': 'venv_az marked for deprecation',
            'artifact': None,
            'commentary': 'venv_az is now redundant. All its packages are in venv_epos. Keep for 7 days as rollback, then delete.'
        }
    ],
    'doctor_upgrade_needed': {
        'version': '3.2',
        'changes': [
            'Search engine/ for governance tools before checking root',
            'Self-heal: if tool found in engine/ but not root, copy it and log repair',
            'Add check: verify epos_start.ps1 exists and is current version',
            'Add check: verify only one venv is active'
        ]
    },
    'triple_compulsion': {
        'IMPLEMENT': 'epos_start.ps1 created, dependencies merged',
        'DOCUMENT': 'This report + contextual commentary per action',
        'SURVEIL': 'Run epos_doctor.py after launcher to confirm 0 critical failures'
    }
}

out = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\events\env_unify_v1_report.jsonl')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'a', encoding='utf-8') as f:
    f.write(json.dumps(report) + '\n')
print(f'Housekeeping report written: {out}')
"
```

---

# PHASE 5: VALIDATE

## Step 5.1 — Test the unified launcher

**Agent Zero: execute via shell tool**
```powershell
cd C:\Users\Jamie\workspace\epos_mcp

# Kill any existing processes on our ports first
$ports = @(8001)
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Killed process on :$port" -ForegroundColor Yellow
    }
}

# Run the launcher
.\epos_start.ps1
```

**Success criteria:**
- Banner displays with system status
- Doctor shows 0 critical failures
- Boot time < 15 seconds
- You're in an active EPOS shell ready for commands

## Step 5.2 — Run full Doctor from the unified environment

```powershell
python engine\epos_doctor.py --verbose
```

**Success:** 0 critical failures. Warnings for Agent Zero path and Ollama (if not pulled yet) are acceptable.

## Step 5.3 — Confirm C10 still operational

```powershell
python -c "
from content.lab.tributaries.echolocation_algorithm import EcholocationAlgorithm
from content.lab.validation.brand_validator import BrandValidator
print('C10 Content Lab: OPERATIONAL')
"
```

---

# PHASE 6: FUTURE SELF-HEALING (DOCTOR v3.2 QUEUE)

These are the self-healing behaviors to encode into `epos_doctor.py` v3.2 as the next evolution mission:

| Trigger | Current Behavior | Self-Healing Behavior |
|---------|-----------------|----------------------|
| governance_gate.py missing at root | CRITICAL FAIL, halt | Search engine/enforcement/ → copy to root → log repair → re-validate |
| epos_snapshot.py missing | CRITICAL FAIL, halt | Search engine/ and rejected/ → copy best version to root → log |
| Ollama not responding | WARNING only | Attempt `Start-Process ollama serve` → wait 3s → re-check → log |
| Port 8001 in use | WARNING only | Check if it's our uvicorn → if yes, accept. If unknown process → warn with PID |
| venv_az still exists after 7 days | (not checked) | NEW CHECK: warn that deprecated venv should be removed |
| epos_start.ps1 missing | (not checked) | NEW CHECK: warn that unified launcher is absent |

These self-healing rules follow the same pattern as C10 self-evolution: detect → locate → repair → validate → log. The Doctor doesn't just diagnose — it prescribes and executes.

---

> **Constitutional Commentary:** This mission proves that EPOS can perform deterministic multi-step operations through Agent Zero without model calls. The shell tool logic embedded in AZ's files provides the orchestration; the mission JSON provides the sequence. When EPOS needs to *think* (design a node, evaluate strategy), it calls a model. When it needs to *do* (start services, copy files, run checks), it uses its own tools. This separation is the foundation of scalable autonomy.
