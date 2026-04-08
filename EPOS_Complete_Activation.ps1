# File: EPOS_Complete_Activation.ps1
# Constitutional Authority: Article II, Rule 1 (Path Absolutism)
$ErrorActionPreference = "Stop"
$EPOS_ROOT = "C:\Users\Jamie\workspace\epos_mcp"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " EPOS COMPLETE ACTIVATION PROTOCOL " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Set-Location $EPOS_ROOT

# STEP 1: REACTIVATE VIRTUAL ENVIRONMENT
Write-Host "[1/4] Reactivating Virtual Environment..." -ForegroundColor Yellow
if (Test-Path ".venv_epos\Scripts\Activate.ps1") {
    & ".venv_epos\Scripts\Activate.ps1"
    Write-Host "      DONE: Virtual environment active." -ForegroundColor Green
}

# STEP 2: SYNCHRONIZE DOCKER CONTEXTS
Write-Host "[2/4] Correcting Docker Build Contexts..." -ForegroundColor Yellow
$dockerComposeFixed = @'
version: '3.8'
networks:
  epos_network:
    driver: bridge
services:
  event-bus:
    build:
      context: ./containers/event-bus
      dockerfile: Dockerfile
    container_name: epos-event-bus
    networks: [epos_network]
    ports: ["8100:8100"]
    volumes: ["./logs:/app/logs"]
    restart: unless-stopped
  governance-server:
    build:
      context: ./containers/governance-server
      dockerfile: Dockerfile
    container_name: epos-governance
    networks: [epos_network]
    ports: ["8101:8101"]
    volumes: ["./logs:/app/logs"]
    depends_on: [event-bus]
    restart: unless-stopped
  learning-server:
    build:
      context: ./containers/learning-server
      dockerfile: Dockerfile
    container_name: epos-learning
    networks: [epos_network]
    ports: ["8102:8102"]
    volumes: ["./logs:/app/logs", "./learning_data:/app/learning_data"]
    depends_on: [event-bus]
    restart: unless-stopped
  context-server:
    build:
      context: ./containers/context-server
      dockerfile: Dockerfile
    container_name: epos-context
    networks: [epos_network]
    ports: ["8103:8103"]
    volumes: ["./logs:/app/logs", "./context_vault:/app/context_vault"]
    depends_on: [event-bus]
    restart: unless-stopped
'@
Set-Content -Path "docker-compose.yml" -Value $dockerComposeFixed -Encoding UTF8
Write-Host "      DONE: docker-compose.yml synchronized." -ForegroundColor Green

# STEP 3: BUILD & DEPLOY
Write-Host "[3/4] Building & Launching Nervous System..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>$null
docker-compose build --no-cache
docker-compose up -d

Write-Host "      Waiting 20s for service heartbeat..." -ForegroundColor Cyan
Start-Sleep -Seconds 20

# STEP 4: HEALTH VALIDATION
Write-Host "[4/4] Running Health Checks..." -ForegroundColor Yellow
$healthChecks = @(
    @{Name="Event Bus"; URL="http://localhost:8100/health"},
    @{Name="Governance"; URL="http://localhost:8101/health"},
    @{Name="Learning"; URL="http://localhost:8102/health"},
    @{Name="Context"; URL="http://localhost:8103/health"}
)
$successCount = 0
foreach ($svc in $healthChecks) {
    try {
        $response = Invoke-WebRequest -Uri $svc.URL -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "      OK: $($svc.Name) is ONLINE" -ForegroundColor Green
            $successCount++
        }
    } catch {
        Write-Host "      FAIL: $($svc.Name) is OFFLINE" -ForegroundColor Red
    }
}

Write-Host "=======================================================" -ForegroundColor Cyan
if ($successCount -eq 4) {
    Write-Host " MISSION SUCCESS: EPOS NERVOUS SYSTEM OPERATIONAL " -ForegroundColor Green
} else {
    Write-Host " WARNING: SYSTEM PARTIAL ($successCount / 4 ONLINE) " -ForegroundColor Yellow
}
Write-Host "=======================================================" -ForegroundColor Cyan