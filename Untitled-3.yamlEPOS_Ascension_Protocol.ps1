# File: EPOS_Ascension_Protocol.ps1
# Order: 9th Order Autonomy | Proactive Synthesis
$ErrorActionPreference = "Continue" # Manage warnings through logic, not termination
$EPOS_ROOT = $PSScriptRoot

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "         EPOS 9TH ORDER ASCENSION PROTOCOL             " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. SCORCHED EARTH: PORT & PROCESS PURGE
Write-Host "[!] Phase 1: Scorched Earth (Clearing Debt)..." -ForegroundColor Yellow
8100..8104 | ForEach-Object {
    $proc = Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue
    if ($proc) { 
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "    Purged Zombie on Port $_" -ForegroundColor DarkGray
    }
}

# 2. ATOMIC TRUTH: DYNAMIC YAML GENERATION
Write-Host "[!] Phase 2: Atomic Truth (Synthesizing Manifest)..." -ForegroundColor Yellow
$YAML_TRUTH = @"
services:
  event-bus:
    build: { context: ./containers/event-bus, dockerfile: Dockerfile }
    container_name: epos-event-bus
    ports: ["8100:8100"]
    volumes: ["$($EPOS_ROOT.Replace('\','/'))/logs:/app/logs"]
    networks: [epos-net]
    restart: always

  governance-server:
    build: { context: ./containers/governance-gate, dockerfile: Dockerfile }
    container_name: epos-governance
    ports: ["8101:8101"]
    volumes: ["$($EPOS_ROOT.Replace('\','/'))/logs:/app/logs"]
    depends_on: [event-bus]
    networks: [epos-net]

  learning-server:
    build: { context: ./containers/learning-server, dockerfile: Dockerfile }
    container_name: epos-learning
    ports: ["8102:8102"]
    volumes: ["$($EPOS_ROOT.Replace('\','/'))/logs:/app/logs"]
    depends_on: [event-bus]
    networks: [epos-net]

  context-server:
    build: { context: ./containers/context-server, dockerfile: Dockerfile }
    container_name: epos-context
    ports: ["8103:8103"]
    volumes: ["$($EPOS_ROOT.Replace('\','/'))/logs:/app/logs", "$($EPOS_ROOT.Replace('\','/'))/context_vault:/app/context_vault"]
    depends_on: [event-bus]
    networks: [epos-net]

  immune-sentinel:
    build: { context: ./containers/immune-monitor, dockerfile: Dockerfile }
    container_name: epos-immune-sentinel
    ports: ["8104:8104"]
    volumes: ["$($EPOS_ROOT.Replace('\','/'))/logs:/app/logs"]
    depends_on: [event-bus]
    networks: [epos-net]

networks:
  epos-net:
    driver: bridge
"@
$YAML_TRUTH | Set-Content -Path "$EPOS_ROOT\docker-compose.yml" -Encoding ASCII

# 3. ATOMIC DEPLOYMENT
Write-Host "[!] Phase 3: Building Aligned Nervous System..." -ForegroundColor Yellow
docker-compose down --remove-orphans
docker-compose build --no-cache
docker-compose up -d

# 4. HOMEOTASIS VALIDATION
Write-Host "[!] Phase 4: Verifying 5/5 Heartbeats..." -ForegroundColor Yellow
Start-Sleep -Seconds 25
$success = 0
8100..8104 | ForEach-Object {
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:$_/health" -Method Get -TimeoutSec 2
        Write-Host "    [ONLINE] Port $_" -ForegroundColor Green
        $success++
    } catch {
        Write-Host "    [OFFLINE] Port $_" -ForegroundColor Red
    }
}

Write-Host "=======================================================" -ForegroundColor Cyan
if ($success -eq 5) {
    Write-Host "       MISSION SUCCESS: ASCENSION COMPLETE             " -ForegroundColor Green
} else {
    Write-Host "       WARNING: SYSTEM PARTIAL ($success/5 ONLINE)      " -ForegroundColor Yellow
}
Write-Host "=======================================================" -ForegroundColor Cyan