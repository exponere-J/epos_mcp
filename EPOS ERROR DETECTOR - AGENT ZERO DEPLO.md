# EPOS ERROR DETECTOR - AGENT ZERO DEPLOYMENT (CORRECTED)

## ✅ ALL INCONSISTENCIES FIXED

**Fixed Issues:**
- ✅ Port changed from 8106 to **8115** (no conflicts)
- ✅ All paths use **absolute Windows paths** (C:\Users\Jamie\...)
- ✅ File placement strategy **clearly defined**
- ✅ Dockerfile COPY paths **match actual locations**
- ✅ docker-compose.yml append strategy **explicit**

---

## 📁 ABSOLUTE FILE STRUCTURE

```
C:\Users\Jamie\workspace\epos_mcp\
├── inbox\
│   ├── MISSION-INTEGRATION-LAYER.json     ← PLACE HERE (AZ reads)
│   └── error_detector.py                  ← PLACE HERE (AZ reads)
│
├── error_detector.py                      ← AZ COPIES HERE (root)
│
├── engine\                                ← MUST EXIST (Dockerfile needs this)
│   ├── __init__.py
│   ├── event_bus.py
│   └── enforcement\
│
├── containers\
│   └── error-detector\                    ← AZ CREATES THIS
│       └── Dockerfile                     ← AZ CREATES THIS
│
├── docker-compose.yml                     ← AZ APPENDS SERVICE HERE
│
└── context_vault\
    └── events\
        ├── system_events.jsonl            ← AZ LOGS HERE
        └── mission_completions.jsonl     ← AZ LOGS SUCCESS HERE
```

---

## 🚀 DEPLOYMENT STEPS (AGENT ZERO)

### **Step 1: Download Files**

Download these 2 files from outputs:
1. ✅ `MISSION-INTEGRATION-LAYER.json`
2. ✅ `error_detector_for_az_inbox.py` (rename to `error_detector.py`)

---

### **Step 2: Place Files in Inbox**

```powershell
# In PowerShell

cd C:\Users\Jamie\workspace\epos_mcp

# 1. Create inbox directory (if not exists)
New-Item -ItemType Directory -Path inbox -Force

# 2. Copy mission file to inbox
# Download MISSION-INTEGRATION-LAYER.json from outputs
# Place in: C:\Users\Jamie\workspace\epos_mcp\inbox\MISSION-INTEGRATION-LAYER.json

# 3. Copy error_detector.py to inbox
# Download error_detector_for_az_inbox.py from outputs
# Rename to: error_detector.py
# Place in: C:\Users\Jamie\workspace\epos_mcp\inbox\error_detector.py

# 4. Verify files in place
Write-Host "`nVerifying files in inbox:" -ForegroundColor Yellow
if (Test-Path "inbox\MISSION-INTEGRATION-LAYER.json") { 
    Write-Host "✅ MISSION-INTEGRATION-LAYER.json" -ForegroundColor Green 
} else { 
    Write-Host "❌ MISSING: MISSION-INTEGRATION-LAYER.json" -ForegroundColor Red 
}

if (Test-Path "inbox\error_detector.py") { 
    Write-Host "✅ error_detector.py" -ForegroundColor Green 
} else { 
    Write-Host "❌ MISSING: error_detector.py" -ForegroundColor Red 
}
```

---

### **Step 3: Verify Agent Zero is Running**

```powershell
# Check if Agent Zero container is running
docker ps --filter name=epos-agent-zero

# Should show:
# CONTAINER ID   IMAGE     ...   STATUS        PORTS     NAMES
# abc123def456   epos...   ...   Up 2 hours    8105/tcp  epos-agent-zero

# If NOT running, start it:
docker-compose up -d agent-zero

# Wait 10 seconds for startup
Start-Sleep -Seconds 10

# Check logs
docker logs epos-agent-zero --tail 20
```

---

### **Step 4: Trigger Agent Zero Mission**

```powershell
# Publish mission to Event Bus
$event = @{
    event_type = "inbox.mission_received"
    payload = @{
        mission_id = "INTEGRATION-LAYER-001"
        priority = "CRITICAL"
        agent = "agent-zero"
        file_path = "C:\Users\Jamie\workspace\epos_mcp\inbox\MISSION-INTEGRATION-LAYER.json"
    }
    metadata = @{
        source = "human"
        timestamp = (Get-Date -Format "o")
        trace_id = "MANUAL-TRIGGER-$(Get-Date -Format 'yyyyMMddHHmmss')"
    }
    source_server = "powershell-cli"
} | ConvertTo-Json -Depth 10

# Send to Event Bus
try {
    Invoke-RestMethod `
        -Uri "http://localhost:8100/publish" `
        -Method POST `
        -Body $event `
        -ContentType "application/json"
    
    Write-Host "`n✅ Mission published to Event Bus" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Failed to publish mission" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nIs Event Bus running? Check: docker ps --filter name=epos-event-bus" -ForegroundColor Yellow
}
```

---

### **Step 5: Monitor Agent Zero Execution**

```powershell
# Watch system events in real-time
Write-Host "`nMonitoring Agent Zero execution..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring`n" -ForegroundColor Yellow

Get-Content C:\Users\Jamie\workspace\epos_mcp\context_vault\events\system_events.jsonl -Wait -Tail 20
```

**What you should see:**
```json
{"event_type":"inbox.mission_received","payload":{"mission_id":"INTEGRATION-LAYER-001",...}}
{"event_type":"mission.started","payload":{"mission_id":"INTEGRATION-LAYER-001","agent":"agent-zero",...}}
{"event_type":"task.completed","payload":{"task_id":"T1","phase":"PRE_FLIGHT",...}}
{"event_type":"task.completed","payload":{"task_id":"T2","phase":"GOVERNANCE_VALIDATION",...}}
...
{"event_type":"mission.completed","payload":{"mission_id":"INTEGRATION-LAYER-001","tasks_completed":10,...}}
```

---

### **Step 6: Verify Deployment Success**

```powershell
# 1. Check if error-detector container is running
docker ps --filter name=epos-error-detector

# Should show:
# CONTAINER ID   IMAGE     ...   STATUS        PORTS                    NAMES
# xyz789abc123   epos...   ...   Up 30 seconds 0.0.0.0:8115->8115/tcp   epos-error-detector

# 2. Test health endpoint
Invoke-RestMethod http://localhost:8115/health

# Should return:
# status         : healthy
# service        : error-detector
# port           : 8115
# event_bus      : connected
# timestamp      : 2026-02-08T...

# 3. Test error analysis
$testError = @{
    error = "yaml: line 47: found unexpected end of stream"
    context = "C:\Users\Jamie\workspace\epos_mcp"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8115/analyze `
    -Method POST `
    -Body $testError `
    -ContentType "application/json"

# Should return diagnosis with fix_steps
```

---

## 🔧 AGENT ZERO WORKFLOW (WHAT AZ DOES)

### **Phase 1: Pre-Flight Checks (T1)**
- ✅ Verify Docker running
- ✅ Verify Event Bus operational
- ✅ Verify `engine/` directory exists
- ✅ Check port 8115 available

### **Phase 2: Governance Validation (T2)**
- ✅ Read `inbox/error_detector.py`
- ✅ Validate constitutional header (port 8115, not 8106)
- ✅ Check Event Bus import has fallback
- ✅ Verify all paths use `pathlib.Path`
- ✅ Log validation result

### **Phase 3: File Placement (T3)**
- ✅ Copy `inbox/error_detector.py` → `error_detector.py` (root)
- ✅ Verify file exists and size > 0

### **Phase 4: Dockerfile Creation (T4)**
- ✅ Create directory: `containers/error-detector/`
- ✅ Write Dockerfile with:
  - Base: `python:3.11-slim`
  - Dependencies: `fastapi`, `uvicorn`, `pyyaml`
  - Copy: `engine/` and `error_detector.py`
  - Expose: `8115`
  - Healthcheck: `curl localhost:8115/health`

### **Phase 5: docker-compose Update (T5)**
- ✅ Backup `docker-compose.yml`
- ✅ Insert `error-detector` service after `command-center`
- ✅ Validate YAML: `docker-compose config`
- ✅ Rollback if validation fails

### **Phase 6: Build (T6)**
- ✅ Run: `docker-compose build error-detector`
- ✅ Verify image created
- ✅ Log build output

### **Phase 7: Deploy (T7)**
- ✅ Run: `docker-compose up -d error-detector`
- ✅ Wait 10 seconds
- ✅ Verify container running

### **Phase 8: Health Check (T8)**
- ✅ Curl: `http://localhost:8115/health`
- ✅ Retry 3 times if fails
- ✅ Verify response has `status=healthy`

### **Phase 9: Event Bus Integration (T9)**
- ✅ Search `system_events.jsonl` for `error-detector.online`
- ✅ Verify Event Bus subscription

### **Phase 10: Functional Test (T10)**
- ✅ POST test error to `/analyze`
- ✅ Verify diagnosis returned
- ✅ Log test result

---

## 📊 SUCCESS METRICS

After deployment, you should see:

```powershell
# 1. Container running
docker ps --filter name=epos-error-detector
# ✅ Shows: Up X minutes, 0.0.0.0:8115->8115/tcp

# 2. Health check passing
Invoke-RestMethod http://localhost:8115/health
# ✅ Returns: {"status":"healthy",...}

# 3. Event Bus integration
Get-Content context_vault\events\system_events.jsonl | Select-String "error-detector"
# ✅ Shows: error-detector.online event

# 4. Can analyze errors
# (See Step 6 test above)
# ✅ Returns: Diagnosis with fix_steps
```

---

## ❓ TROUBLESHOOTING

### **Agent Zero doesn't start mission**

```powershell
# Check AZ logs
docker logs epos-agent-zero --tail 50

# Check if mission file is valid JSON
Get-Content inbox\MISSION-INTEGRATION-LAYER.json | ConvertFrom-Json

# Manually trigger AZ bridge
docker exec epos-agent-zero ls /app/inbox
```

### **Build fails**

```powershell
# Check if engine/ directory exists
if (Test-Path "engine\") { 
    Write-Host "✅ engine/ exists" -ForegroundColor Green 
} else { 
    Write-Host "❌ engine/ missing - Dockerfile needs this!" -ForegroundColor Red 
}

# Check if error_detector.py in root
if (Test-Path "error_detector.py") { 
    Write-Host "✅ error_detector.py in root" -ForegroundColor Green 
} else { 
    Write-Host "❌ error_detector.py not in root!" -ForegroundColor Red 
}
```

### **Port conflict**

```powershell
# Check what's using port 8115
netstat -ano | findstr :8115

# Should be EMPTY before deployment
# If not, kill the process or change port in mission file
```

---

## ✅ COMPLETION CRITERIA

Mission is complete when:
- ✅ `epos-error-detector` container running
- ✅ Port 8115 responding to health checks
- ✅ Event Bus shows `error-detector.online` event
- ✅ Can analyze YAML, Docker, and port errors
- ✅ Mission completion event in `mission_completions.jsonl`

---

**All paths are now absolute. All ports corrected. Agent Zero ready to execute.**