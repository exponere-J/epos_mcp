# EPOS Unified Launcher — epos_start.ps1
# Constitutional Authority: EPOS Constitution v3.1
# Run: .\epos_start.ps1

Set-Location "C:\Users\Jamie\workspace\epos_mcp"

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  EPOS Stack Launcher" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan

# 1. Start Docker DB stack
Write-Host "`n[1/4] Starting database stack..." -ForegroundColor Yellow
docker start epos_db epos_api epos_ui epos_swagger 2>$null
Start-Sleep 2

# 2. Check DB health
$dbHealth = docker inspect epos_db --format '{{.State.Health.Status}}' 2>$null
if ($dbHealth -eq "healthy") {
    Write-Host "  Database: HEALTHY" -ForegroundColor Green
} else {
    Write-Host "  Database: $dbHealth (waiting...)" -ForegroundColor Yellow
    Start-Sleep 5
}

# 3. Start EPOS API
Write-Host "`n[2/4] Starting EPOS API on :8001..." -ForegroundColor Yellow
$apiJob = Start-Process -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "epos_runner:app", "--host", "127.0.0.1", "--port", "8001" `
    -WorkingDirectory "C:\Users\Jamie\workspace\epos_mcp" `
    -PassThru -WindowStyle Minimized
Write-Host "  EPOS API: PID $($apiJob.Id)" -ForegroundColor Green

# 4. Run Doctor
Write-Host "`n[3/4] Running EPOS Doctor..." -ForegroundColor Yellow
& .venv\Scripts\python.exe engine\epos_doctor.py

# 5. Show dashboard
Write-Host "`n[4/4] Project Dashboard:" -ForegroundColor Yellow
& .venv\Scripts\python.exe life_os_cli.py projects

Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  EPOS is operational." -ForegroundColor Green
Write-Host "  API:  http://localhost:8001" -ForegroundColor White
Write-Host "  DB:   http://localhost:8080 (Adminer)" -ForegroundColor White
Write-Host "  Docs: http://localhost:8081 (Swagger)" -ForegroundColor White
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
