# epos.ps1 - EPOS Shell Wrapper
# Constitutional Authority: Article VI (Autonomous Evolution)
# Purpose: Intercept commands, capture errors, route to constellation

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$CommandArgs
)

$EPOS_ROOT = "C:\Users\Jamie\workspace\epos_mcp"
$EVENT_BUS_URL = "http://localhost:8100"
$DIAGNOSTIC_URL = "http://localhost:8104"

function Publish-EPOSEvent {
    param($EventType, $Payload)
    
    $event = @{
        event_type = $EventType
        payload = $Payload
        metadata = @{
            source = "epos-shell"
            timestamp = (Get-Date).ToString("o")
            user = $env:USERNAME
        }
    } | ConvertTo-Json -Depth 10
    
    try {
        Invoke-RestMethod -Uri "$EVENT_BUS_URL/publish" -Method POST -Body $event -ContentType "application/json" -ErrorAction SilentlyContinue
    } catch {
        Write-Host "[EPOS Shell] Event Bus unreachable - running offline" -ForegroundColor Yellow
    }
}

function Invoke-EPOSDiagnostic {
    param($ErrorOutput)
    
    try {
        $result = Invoke-RestMethod -Uri "$DIAGNOSTIC_URL/analyze-error" -Method POST -Body (@{
            error = $ErrorOutput
            context = (Get-Location).Path
        } | ConvertTo-Json) -ContentType "application/json"
        
        return $result
    } catch {
        return $null
    }
}

function Show-EPOSRemediation {
    param($Diagnosis)
    
    Write-Host "`n┌─────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "│  EPOS AUTO-FIX AVAILABLE                    │" -ForegroundColor Cyan
    Write-Host "├─────────────────────────────────────────────┤" -ForegroundColor Cyan
    Write-Host "│  Error: $($Diagnosis.error_type.PadRight(36))│" -ForegroundColor Yellow
    Write-Host "│  Cause: $($Diagnosis.root_cause.PadRight(36))│" -ForegroundColor White
    Write-Host "│                                             │"
    Write-Host "│  Suggested Fix:                             │" -ForegroundColor Green
    foreach ($step in $Diagnosis.fix_steps) {
        Write-Host "│  - $($step.PadRight(42))│" -ForegroundColor White
    }
    Write-Host "│                                             │"
    Write-Host "└─────────────────────────────────────────────┘" -ForegroundColor Cyan
    
    $response = Read-Host "`n[Apply Fix] [Show Diff] [Ignore] (A/D/I)"
    
    return $response.ToUpper()
}

# ===== MAIN EXECUTION =====

$command = $CommandArgs -join " "

Write-Host "[EPOS] Executing: $command" -ForegroundColor Cyan

# Publish command execution event
Publish-EPOSEvent "shell.command_started" @{
    command = $command
    working_dir = (Get-Location).Path
}

# Execute command and capture output
$output = ""
$errorOutput = ""

try {
    # Execute command
    $result = Invoke-Expression $command 2>&1
    
    # Separate stdout and stderr
    $output = $result | Where-Object { $_ -is [string] } | Out-String
    $errorOutput = $result | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | Out-String
    
    # Display output
    Write-Output $result
    
    # Check for errors
    if ($LASTEXITCODE -ne 0 -or $errorOutput) {
        Write-Host "`n[EPOS] Error detected" -ForegroundColor Red
        
        # Publish error event
        Publish-EPOSEvent "shell.error_detected" @{
            command = $command
            exit_code = $LASTEXITCODE
            error = $errorOutput
            output = $output
        }
        
        # Request diagnostic
        Write-Host "[EPOS Diagnostic Server] Analyzing error..." -ForegroundColor Yellow
        $diagnosis = Invoke-EPOSDiagnostic $errorOutput
        
        if ($diagnosis -and $diagnosis.fix_available) {
            Write-Host "[EPOS] ✅ Remediation available" -ForegroundColor Green
            
            $choice = Show-EPOSRemediation $diagnosis
            
            switch ($choice) {
                "A" {
                    Write-Host "`n[EPOS] Applying fix..." -ForegroundColor Green
                    
                    # Apply fix via Diagnostic Server
                    $fixResult = Invoke-RestMethod -Uri "$DIAGNOSTIC_URL/apply-fix" -Method POST -Body (@{
                        diagnosis_id = $diagnosis.id
                    } | ConvertTo-Json) -ContentType "application/json"
                    
                    if ($fixResult.success) {
                        Write-Host "[EPOS] ✅ Fix applied successfully" -ForegroundColor Green
                        Write-Host "[EPOS] Re-running command..." -ForegroundColor Cyan
                        
                        # Re-run command
                        & epos $CommandArgs
                    } else {
                        Write-Host "[EPOS] ❌ Fix failed: $($fixResult.error)" -ForegroundColor Red
                    }
                }
                "D" {
                    Write-Host "`n[EPOS] Showing diff..." -ForegroundColor Cyan
                    Write-Host $diagnosis.diff -ForegroundColor White
                }
                "I" {
                    Write-Host "[EPOS] Ignored" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "[EPOS] No automatic fix available" -ForegroundColor Yellow
            Write-Host "[EPOS] Logging error to Context Vault for learning..." -ForegroundColor Cyan
        }
    } else {
        Write-Host "`n[EPOS] ✅ Command completed successfully" -ForegroundColor Green
        
        # Publish success event
        Publish-EPOSEvent "shell.command_completed" @{
            command = $command
            exit_code = 0
        }
    }
    
} catch {
    Write-Host "`n[EPOS] Fatal error: $_" -ForegroundColor Red
    
    Publish-EPOSEvent "shell.fatal_error" @{
        command = $command
        error = $_.Exception.Message
    }
}
