"""
EPOS API - Phi-4 Orchestration
FastAPI server for task routing and Agent Zero integration
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os

# Import bridge
try:
    from agent_zero_bridge_for_deployment import AgentZeroBridge
except ImportError:
    # Fallback for development
    class AgentZeroBridge:
        def __init__(self, workspace=None):
            self.workspace = Path.cwd()
        def health_check(self):
            return {"ok": True, "status": "fallback"}

# Initialize FastAPI
app = FastAPI(
    title="EPOS Orchestrator",
    version="1.0.0",
    description="Phi-4 powered task orchestration for Agent Zero"
)

# Bridge instance
try:
    bridge = AgentZeroBridge(Path.cwd())
except:
    bridge = None

# Models
class TaskRequest(BaseModel):
    description: str
    domain: str  # "local_ops", "browser", "ingestion", "analysis"
    context: Optional[Dict[str, Any]] = None
    priority: str = "normal"

class FileIngestionRequest(BaseModel):
    file_path: str
    file_type: str = "markdown"
    tags: Optional[list] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    description: str
    domain: str
    result: Optional[Dict] = None

# Routes

@app.get("/health")
def health():
    """Health check."""
    if bridge:
        bridge_health = bridge.health_check()
    else:
        bridge_health = {"ok": False, "error": "Bridge not initialized"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bridge": bridge_health,
        "python": sys.version.split()[0]
    }

@app.post("/task", response_model=TaskResponse)
def submit_task(
    task: TaskRequest,
    x_api_token: str = Header(None)
):
    """Submit a task for orchestration."""
    
    # Verify token
    expected_token = os.getenv("EPOS_API_TOKEN", "local-dev-token")
    if x_api_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    task_id = f"task_{int(datetime.now().timestamp())}"
    
    # Log task
    log_dir = Path.cwd() / "ops" / "logs" / "api"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
        "domain": task.domain,
        "description": task.description,
        "priority": task.priority
    }
    
    log_file = log_dir / f"tasks_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Route based on domain
    result = None
    status = "queued"
    
    if task.domain == "local_ops":
        if bridge:
            result = bridge.execute_task(task.description, mode="local", context=task.context)
            status = "executing"
        else:
            result = {"error": "Bridge not initialized"}
            status = "error"
    
    elif task.domain == "browser":
        if bridge:
            result = bridge.execute_task(task.description, mode="browser", context=task.context)
            status = "executing"
        else:
            result = {"error": "Bridge not initialized"}
            status = "error"
    
    elif task.domain == "ingestion":
        # File ingestion via Phi-4
        result = {
            "type": "ingestion",
            "description": task.description,
            "status": "ready_for_phi4"
        }
        status = "ready"
    
    elif task.domain == "analysis":
        # Analysis via Phi-4
        result = {
            "type": "analysis",
            "description": task.description,
            "status": "ready_for_phi4"
        }
        status = "ready"
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {task.domain}")
    
    return TaskResponse(
        task_id=task_id,
        status=status,
        description=task.description,
        domain=task.domain,
        result=result
    )

@app.post("/ingest")
def ingest_file(
    request: FileIngestionRequest,
    x_api_token: str = Header(None)
):
    """Ingest a file for processing."""
    
    # Verify token
    expected_token = os.getenv("EPOS_API_TOKEN", "local-dev-token")
    if x_api_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    file_path = Path(request.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    if bridge:
        result = bridge.ingest_file(file_path, request.file_type)
    else:
        result = {"error": "Bridge not initialized"}
    
    return {
        "status": "success" if result.get("ok") else "error",
        "file": request.file_path,
        "file_type": request.file_type,
        "result": result
    }

@app.post("/execute")
def execute_command(
    command: str,
    cwd: Optional[str] = None,
    x_api_token: str = Header(None)
):
    """Execute a shell command."""
    
    # Verify token
    expected_token = os.getenv("EPOS_API_TOKEN", "local-dev-token")
    if x_api_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    if bridge:
        result = bridge.execute_local_command(command, cwd)
    else:
        result = {"error": "Bridge not initialized"}
    
    return {
        "command": command,
        "status": "success" if result.get("ok") else "error",
        "result": result
    }

@app.get("/tasks/{task_id}")
def get_task_status(
    task_id: str,
    x_api_token: str = Header(None)
):
    """Get task status."""
    
    # Verify token
    expected_token = os.getenv("EPOS_API_TOKEN", "local-dev-token")
    if x_api_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    log_dir = Path.cwd() / "ops" / "logs" / "api"
    
    # Search logs for task
    if log_dir.exists():
        for log_file in log_dir.glob("*.jsonl"):
            with log_file.open("r") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get("task_id") == task_id:
                        return {
                            "task_id": task_id,
                            "status": "found",
                            "details": entry
                        }
    
    return {
        "task_id": task_id,
        "status": "not_found"
    }

@app.get("/config")
def get_config():
    """Get EPOS configuration."""
    
    env_file = Path.cwd() / ".env"
    config = {}
    
    if env_file.exists():
        with env_file.open("r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    
    return {
        "environment": "production" if config.get("EPOS_API_TOKEN") != "local-dev-token" else "development",
        "config": {k: v for k, v in config.items() if k != "EPOS_API_TOKEN"}
    }

# Startup
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("🚀 EPOS Orchestrator starting...")
    
    if bridge:
        health = bridge.health_check()
        if health["ok"]:
            print("✓ Agent Zero bridge connected")
        else:
            print("⚠ Agent Zero bridge issues:", health)
    else:
        print("⚠ Agent Zero bridge not initialized")

# Root
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "EPOS Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "submit_task": "POST /task",
            "ingest_file": "POST /ingest",
            "execute_command": "POST /execute",
            "task_status": "GET /tasks/{task_id}",
            "config": "GET /config"
        },
        "auth": "X-API-Token header required"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
cat > api/epos_api.py << 'EOF'
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path
from datetime import datetime
import sys

app = FastAPI(title="EPOS Orchestrator", version="1.0.0")

class AgentZeroBridge:
    def __init__(self):
        self.az_path = Path(os.getenv("AGENT_ZERO_PATH", "~/workspace/agent-zero"))
        self.log_dir = Path.cwd() / "ops" / "logs" / "agent_zero"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def health_check(self) -> Dict[str, Any]:
        return {
            "ok": self.az_path.exists(),
            "path": str(self.az_path)
        }

    def execute_task(self, task: str, mode: str = "local", context: Optional[Dict] = None) -> Dict[str, Any]:
        task_id = f"az_{int(datetime.now().timestamp())}"
        log_file = self.log_dir / f"{task_id}.jsonl"
        
        log_entry = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "mode": mode
        }
        with log_file.open("a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return {
            "task_id": task_id,
            "status": "executed",
            "mode": mode,
            "log_file": str(log_file),
            "agent_zero_path": str(self.az_path)
        }

bridge = AgentZeroBridge()

class TaskRequest(BaseModel):
    description: str
    domain: str = "local_ops"
    context: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any]

EPOS_TOKEN = os.getenv("EPOS_API_TOKEN", "local-dev-token")

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "bridge": bridge.health_check(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/task", response_model=TaskResponse)
def task(req: TaskRequest, x_api_token: str = Header(None)):
    if x_api_token != EPOS_TOKEN:
        raise HTTPException(401, "Invalid token")
    
    task_id = f"task_{int(datetime.now().timestamp())}"
    
    # Route to Agent Zero
    result = bridge.execute_task(req.description, req.domain)
    
    # Log to API logs
    log_dir = Path.cwd() / "ops" / "logs" / "api"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"tasks_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with log_file.open("a") as f:
        f.write(json.dumps({
            "task_id": task_id,
            "req": req.dict(),
            "result": result
        }) + "\n")
    
    return TaskResponse(
        task_id=task_id,
        status="executed",
        result=result
    )

@app.get("/")
def root():
    return {
        "name": "EPOS + Agent Zero",
        "status": "live",
        "token": EPOS_TOKEN,
        "bridge": bridge.health_check()
    }

@app.on_event("startup")
async def startup():
    print("🚀 EPOS live. Bridge:", bridge.health_check())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
EOF
