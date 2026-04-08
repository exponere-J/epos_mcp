# EPOS INFRASTRUCTURE DIAGNOSTIC SCRIPT
# PowerShell 7.5.4 Native - Windows 11
# Purpose: Assess current state and identify what needs rebuild

# Color output for readability
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

Clear-Host
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "EPOS INFRASTRUCTURE DIAGNOSTIC REPORT" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ==============================================================================
# SECTION 1: DIRECTORY STRUCTURE
# ==============================================================================

Write-Host "SECTION 1: DIRECTORY STRUCTURE" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

$EPOS_ROOT = "C:\Users\Jamie\workspace\epos_mcp"
$RequiredDirs = @(
    "engine",
    "inbox",
    "rejected",
    "mcp/servers/filehub",
    "mcp/servers/logger",
    "ops/logs",
    "docs"
)

foreach ($dir in $RequiredDirs) {
    $fullPath = Join-Path $EPOS_ROOT $dir
    if (Test-Path $fullPath -PathType Container) {
        Write-Success "Directory exists: $dir"
    } else {
        Write-Error "Directory MISSING: $dir"
    }
}

Write-Host ""

# ==============================================================================
# SECTION 2: REQUIRED FILES
# ==============================================================================

Write-Host "SECTION 2: REQUIRED FILES" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

$RequiredFiles = @(
    ".env",
    "requirements.txt",
    "docker-compose.yml",
    "Dockerfile",
    "epos_doctor.py",
    "mcp/servers/filehub/package.json",
    "mcp/servers/logger/package.json"
)

foreach ($file in $RequiredFiles) {
    $fullPath = Join-Path $EPOS_ROOT $file
    if (Test-Path $fullPath -PathType Leaf) {
        $size = (Get-Item $fullPath).Length
        Write-Success "File exists: $file ($size bytes)"
    } else {
        Write-Error "File MISSING: $file"
    }
}

Write-Host ""

# ==============================================================================
# SECTION 3: PYTHON ENVIRONMENT
# ==============================================================================

Write-Host "SECTION 3: PYTHON ENVIRONMENT" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "3\.11") {
        Write-Success "Python 3.11.x installed: $pythonVersion"
    } else {
        Write-Warning "Python version mismatch: $pythonVersion (expected 3.11.x)"
    }
} catch {
    Write-Error "Python NOT FOUND in PATH"
}

# Check venv
$venvPath = Join-Path $EPOS_ROOT "venv"
if (Test-Path $venvPath) {
    Write-Success "Virtual environment exists: venv/"
    $venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Success "venv activation script found"
    } else {
        Write-Error "venv activation script NOT FOUND"
    }
} else {
    Write-Warning "Virtual environment DOES NOT EXIST (will need to create)"
}

# Check pip packages
Write-Info "Checking pip packages (this requires venv activation)..."
try {
    # Try to list packages
    $packages = pip list 2>&1
    if ($packages -match "fastapi") {
        Write-Success "fastapi package installed"
    } else {
        Write-Warning "fastapi package NOT FOUND (requirements not installed)"
    }
    
    if ($packages -match "uvicorn") {
        Write-Success "uvicorn package installed"
    }
    
    if ($packages -match "anthropic") {
        Write-Success "anthropic package installed"
    }
} catch {
    Write-Warning "Could not check pip packages (might need to activate venv first)"
}

Write-Host ""

# ==============================================================================
# SECTION 4: ENVIRONMENT VARIABLES
# ==============================================================================

Write-Host "SECTION 4: ENVIRONMENT VARIABLES (.env)" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

$envFile = Join-Path $EPOS_ROOT ".env"
if (Test-Path $envFile) {
    Write-Success ".env file exists"
    
    # Parse .env file
    $envVars = @{}
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2]
            $envVars[$key] = $value
        }
    }
    
    # Check critical variables
    $criticalVars = @("EPOS_ROOT", "ANTHROPIC_API_KEY", "LOG_DIR", "OLLAMA_HOST")
    foreach ($var in $criticalVars) {
        if ($envVars.ContainsKey($var)) {
            $val = $envVars[$var]
            if ($var -eq "ANTHROPIC_API_KEY") {
                # Mask the key
                $masked = $val.Substring(0, 10) + "..." + $val.Substring($val.Length - 5)
                Write-Success "Environment variable set: $var = $masked"
            } else {
                Write-Success "Environment variable set: $var = $val"
            }
        } else {
            Write-Error "Environment variable MISSING: $var"
        }
    }
} else {
    Write-Error ".env file NOT FOUND"
}

Write-Host ""

# ==============================================================================
# SECTION 5: DOCKER STATUS
# ==============================================================================

Write-Host "SECTION 5: DOCKER & CONTAINERS" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

try {
    $dockerVersion = docker --version 2>&1
    Write-Success "Docker installed: $dockerVersion"
    
    # Check if Docker daemon is running
    $dockerPs = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker daemon is running"
        
        # List containers
        $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}"
        if ($containers) {
            Write-Info "Containers found:"
            $containers -split "`n" | ForEach-Object {
                if ($_ -match "epos-core|ollama") {
                    if ($_ -match "Up") {
                        Write-Success "  $_ (RUNNING)"
                    } else {
                        Write-Warning "  $_ (STOPPED)"
                    }
                }
            }
        } else {
            Write-Warning "No containers found (need to build docker-compose setup)"
        }
    } else {
        Write-Error "Docker daemon is NOT RUNNING"
        Write-Info "Start Docker Desktop and try again"
    }
} catch {
    Write-Error "Docker NOT FOUND in PATH"
}

Write-Host ""

# ==============================================================================
# SECTION 6: MCP SERVERS
# ==============================================================================

Write-Host "SECTION 6: MCP SERVERS (Node.js)" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

try {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js installed: $nodeVersion"
} catch {
    Write-Error "Node.js NOT FOUND in PATH"
}

try {
    $npmVersion = npm --version 2>&1
    Write-Success "npm installed: $npmVersion"
} catch {
    Write-Error "npm NOT FOUND in PATH"
}

# Check if MCP servers are compiled
$filehubDist = Join-Path $EPOS_ROOT "mcp\servers\filehub\dist\index.js"
if (Test-Path $filehubDist) {
    Write-Success "Filehub MCP server compiled (dist/index.js exists)"
} else {
    Write-Warning "Filehub MCP server NOT COMPILED (need to: npm run build)"
}

$loggerDist = Join-Path $EPOS_ROOT "mcp\servers\logger\dist\index.js"
if (Test-Path $loggerDist) {
    Write-Success "Logger MCP server compiled (dist/index.js exists)"
} else {
    Write-Warning "Logger MCP server NOT COMPILED (need to: npm run build)"
}

Write-Host ""

# ==============================================================================
# SECTION 7: NETWORK & PORTS
# ==============================================================================

Write-Host "SECTION 7: NETWORK & PORTS" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

# Check if critical ports are available/listening
$ports = @(8001, 11434, 5678)
foreach ($port in $ports) {
    try {
        # Try to connect to localhost:port
        $connection = Test-NetConnection -ComputerName "127.0.0.1" -Port $port -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Success "Port $port is LISTENING (service running)"
        } else {
            Write-Warning "Port $port is NOT listening (service may not be running)"
        }
    } catch {
        Write-Warning "Could not test port $port"
    }
}

Write-Host ""

# ==============================================================================
# SECTION 8: OLLAMA SERVICE
# ==============================================================================

Write-Host "SECTION 8: OLLAMA SERVICE" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

try {
    $ollamaResponse = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    if ($ollamaResponse.StatusCode -eq 200) {
        Write-Success "Ollama is RESPONDING on port 11434"
        
        # Parse response to check for models
        $content = $ollamaResponse.Content | ConvertFrom-Json
        if ($content.models) {
            Write-Success "Ollama models found: $($content.models.Count) model(s)"
            $content.models | ForEach-Object {
                Write-Info "  - $($_.name)"
            }
        } else {
            Write-Warning "No models installed in Ollama (need to: ollama pull llama3.2:latest)"
        }
    }
} catch {
    Write-Warning "Ollama is NOT RESPONDING on port 11434 (service may not be running)"
}

Write-Host ""

# ==============================================================================
# SECTION 9: EPOS API HEALTH
# ==============================================================================

Write-Host "SECTION 9: EPOS API HEALTH" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Yellow

try {
    $healthResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -TimeoutSec 5 -ErrorAction Stop
    if ($healthResponse.StatusCode -eq 200) {
        Write-Success "EPOS API is RESPONDING on port 8001"
        $content = $healthResponse.Content | ConvertFrom-Json
        Write-Info "  Status: $($content.status)"
        Write-Info "  Timestamp: $($content.timestamp)"
    }
} catch {
    Write-Warning "EPOS API is NOT RESPONDING on port 8001 (service may not be running)"
}

Write-Host ""

# ==============================================================================
# SUMMARY & RECOMMENDATIONS
# ==============================================================================

Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SUMMARY & NEXT STEPS" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Info "Based on the diagnostic results above, here's what to do next:"
Write-Host ""

# Provide intelligent recommendations
$issues = @()

if (-not (Test-Path $venvPath)) {
    $issues += "1. CREATE PYTHON VENV: `python -m venv venv`"
}

if (-not (Test-Path $filehubDist)) {
    $issues += "2. BUILD FILEHUB: `cd mcp\servers\filehub && npm install && npm run build && cd ..\..\..`"
}

if (-not (Test-Path $loggerDist)) {
    $issues += "3. BUILD LOGGER: `cd mcp\servers\logger && npm install && npm run build && cd ..\..\..`"
}

try {
    $dockerPs = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        $issues += "4. START DOCKER DESKTOP: Open Docker Desktop from Start Menu, wait for it to start"
    }
} catch {
    $issues += "4. INSTALL DOCKER: Download Docker Desktop from docker.com and install"
}

if ($issues.Count -gt 0) {
    Write-Warning "Action items found:"
    $issues | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
} else {
    Write-Success "No critical issues found! Your infrastructure appears operational."
}

Write-Host ""
Write-Info "After addressing any action items above, run the full Docker Compose:"
Write-Host "  docker-compose up -d" -ForegroundColor Cyan
Write-Host ""

# Save report to file
$reportPath = Join-Path $EPOS_ROOT "diagnostic_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
Write-Host ""
Write-Info "Diagnostic report: $reportPath"

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "END OF DIAGNOSTIC REPORT" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
