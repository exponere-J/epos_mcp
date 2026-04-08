# File: EPOS_Ascension_Protocol.ps1
# Order: 9th Order Autonomy | Total Manifestation
$ErrorActionPreference = "Continue" 
$EPOS_ROOT = $PSScriptRoot

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "         EPOS 9TH ORDER ASCENSION PROTOCOL             " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. SCORCHED EARTH
Write-Host "[!] Phase 1: Scorched Earth (Clearing Debt)..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>$null
8100..8104 | ForEach-Object {
    $proc = Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue
    if ($proc) { 
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# 2. ORGANIC SYNTHESIS (Manifesting Files)
Write-Host "[!] Phase 2: Organic Synthesis (Manifesting Files)..." -ForegroundColor Yellow

$Map = @{
    "event-bus"        = "event-bus-server.py"
    "governance-gate"  = "governance-gate-server.py"
    "learning-server"  = "learning-server.py"
    "context-server"   = "context-server.py"
    "immune-monitor"   = "immune_monitor.py"
}

$Reqs = "fastapi==0.104.1`nuvicorn[standard]==0.24.0`nwebsockets==12.0`npydantic==2.5.0`npython-dotenv==1.0.0`nhttpx==0.25.2"

foreach ($s in $Map.Keys) {
    $dir = "$EPOS_ROOT\containers\$s"
    if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    
    # Manifest requirements.txt
    $Reqs | Set-Content -Path "$dir\requirements.txt" -Encoding ASCII
    
    # Manifest server.py (Copying from root to container folder)
    $sourceFile = "$EPOS_ROOT\$($Map[$s])"
    if (Test-Path $sourceFile) {
        Copy-Item -Path $sourceFile -Destination "$dir\server.py" -Force
        Write-Host "    Synthesized $s/server.py" -ForegroundColor Green
    } else {
        # Fallback: Create a placeholder if the source is missing to prevent build crash
        "print('Service $s starting...')`nfrom fastapi import FastAPI`napp=FastAPI()`n@app.get('/health')`nasync def h(): return {'status':'ok'}" | Set-Content -Path "$dir\server.py" -Encoding ASCII
        Write-Host "    Warning: Source $sourceFile missing. Using placeholder for $s" -ForegroundColor Yellow
    }

    # Manifest Dockerfile
    $port = switch($s) { "event-bus"{8100} "governance-gate"{8101} "learning-server"{8102} "context-server"{8103} "immune-monitor"{8104} }
    $dockerfile = "FROM python:3.11-slim`nWORKDIR /app`nRUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*`nCOPY requirements.txt .`nRUN pip install --no-cache-dir -r requirements.txt`nCOPY server.py .`nEXPOSE $port`nCMD [`"python`", `"server.py`"]"
    $dockerfile | Set-Content -Path "$dir\Dockerfile" -Encoding ASCII
}

# 3. DYNAMIC YAML GENERATION
$YAML_TRUTH = @"
services:
  event-bus:
    build: { context: ./containers/event-bus }
    container_name: epos-event-bus
    ports: ["8100:8100"]
    networks: [epos-net]
  governance-gate:
    build: { context: ./containers/governance-gate }
    container_name: epos-governance
    ports: ["8101:8101"]
    depends_on: [event-bus]
    networks: [epos-net]
  learning-server:
    build: { context: ./containers/learning-server }
    container_name: epos-learning
    ports: ["8102:8102"]
    depends_on: [event-bus]
    networks: [epos-net]
  context-server:
    build: { context: ./containers/context-server }
    container_name: epos-context
    ports: ["8103:8103"]
    depends_on: [event-bus]
    networks: [epos-net]
  immune-monitor:
    build: { context: ./containers/immune-monitor }
    container_name: epos-immune-sentinel
    ports: ["8104:8104"]
    depends_on: [event-bus]
    networks: [epos-net]
networks:
  epos-net:
    driver: bridge
"@
$YAML_TRUTH | Set-Content -Path "$EPOS_ROOT\docker-compose.yml" -Encoding ASCII

# 4. ATOMIC DEPLOYMENT
Write-Host "[!] Phase 3: Building Aligned Nervous System..." -ForegroundColor Yellow
docker-compose build
docker-compose up -d

# 5. HOMEOTASIS VALIDATION
Write-Host "[!] Phase 4: Verifying 5/5 Heartbeats..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
$success = 0
8100..8104 | ForEach-Object {
    try {
        $check = Invoke-WebRequest -Uri "http://localhost:$_/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($check.StatusCode -eq 200) {
            Write-Host "    [ONLINE] Port $_" -ForegroundColor Green
            $success++
        }
    } catch {
        Write-Host "    [OFFLINE] Port $_" -ForegroundColor Red
    }
}

Write-Host "=======================================================" -ForegroundColor Cyan
if ($success -eq 5) { Write-Host "       MISSION SUCCESS: ASCENSION COMPLETE" -ForegroundColor Green }
else { Write-Host "       WARNING: SYSTEM PARTIAL ($success/5 ONLINE)" -ForegroundColor Yellow }
Write-Host "=======================================================`n" -ForegroundColor Cyan