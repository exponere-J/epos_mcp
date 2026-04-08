#!/usr/bin/env python3
"""
EPOS Error Detector Service
Constitutional Authority: Article VI (Autonomous Evolution), Article VII (Context Governance)
Port: 8115 (Media Production Pipeline)
Mission: INTEGRATION-LAYER-001
File Location: C:/Users/Jamie/workspace/epos_mcp/error_detector.py
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
import logging

# Add engine to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from event_bus import get_event_bus
    bus = get_event_bus()
    BUS_AVAILABLE = True
except ImportError:
    print("[WARNING] Event Bus not available - running in standalone mode")
    bus = None
    BUS_AVAILABLE = False

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [ErrorDetector] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(
    title="EPOS Error Detector",
    version="3.1.0",
    description="Autonomous error detection and remediation"
)

# ============================================
# MODELS
# ============================================
class ErrorAnalysisRequest(BaseModel):
    error: str
    context: str  # Working directory path

class DiagnosisResponse(BaseModel):
    id: str
    error_type: str
    root_cause: str
    fix_steps: List[str]
    fix_available: bool
    diff: str = ""

class FixRequest(BaseModel):
    diagnosis_id: str

# ============================================
# ERROR PATTERNS
# ============================================
ERROR_PATTERNS = {
    "yaml_parse": {
        "pattern": r"yaml: line (\d+): found unexpected end",
        "handler": "handle_yaml_truncation"
    },
    "yaml_syntax": {
        "pattern": r"yaml: line (\d+): (.+)",
        "handler": "handle_yaml_syntax"
    },
    "docker_build": {
        "pattern": r"ERROR: Service '(.+)' failed to build",
        "handler": "handle_docker_build_error"
    },
    "port_conflict": {
        "pattern": r"bind: address already in use",
        "handler": "handle_port_conflict"
    },
    "python_import": {
        "pattern": r"ModuleNotFoundError: No module named '(.+)'",
        "handler": "handle_import_error"
    },
    "docker_not_running": {
        "pattern": r"Cannot connect to the Docker daemon",
        "handler": "handle_docker_not_running"
    }
}

# ============================================
# ERROR DETECTION
# ============================================
def detect_error_type(error_text: str) -> Tuple[str, Tuple, Optional[str]]:
    """Detect error type from text."""
    for error_type, config in ERROR_PATTERNS.items():
        match = re.search(config["pattern"], error_text, re.IGNORECASE)
        if match:
            return error_type, match.groups(), config["handler"]
    return "unknown", (), None

# ============================================
# ERROR HANDLERS
# ============================================
def handle_yaml_truncation(error: str, context: str) -> DiagnosisResponse:
    """Handle YAML truncation errors."""
    match = re.search(r"line (\d+)", error)
    line_num = int(match.group(1)) if match else 0
    
    compose_file = Path(context) / "docker-compose.yml"
    
    if compose_file.exists():
        with open(compose_file) as f:
            content = f.read()
            lines = content.split("\n")
        
        # Detect what's missing
        if line_num < len(lines):
            last_line = lines[line_num - 1]
        else:
            last_line = lines[-1] if lines else ""
        
        diagnosis = DiagnosisResponse(
            id=f"DIAG-YAML-TRUNC-{line_num}",
            error_type="YAML Truncation",
            root_cause=f"docker-compose.yml ends unexpectedly at line {line_num}",
            fix_steps=[
                f"File appears incomplete after line {line_num}",
                "Last line: " + last_line.strip(),
                "Download docker-compose-FIXED.yml from outputs",
                "Replace current docker-compose.yml"
            ],
            fix_available=True,
            diff=f"Issue at line {line_num}: {last_line}"
        )
        
        if bus:
            bus.publish(
                event_type="diagnostic.analysis_complete",
                payload={
                    "diagnosis_id": diagnosis.id,
                    "error_type": diagnosis.error_type,
                    "fix_available": True,
                    "line_number": line_num
                },
                source_server="error-detector"
            )
        
        return diagnosis
    
    return DiagnosisResponse(
        id="DIAG-YAML-NOTFOUND",
        error_type="YAML File Not Found",
        root_cause="Unable to locate docker-compose.yml",
        fix_steps=[
            f"Expected path: {compose_file}",
            "Verify you're in the EPOS root directory",
            f"Run: cd {os.getenv('EPOS_ROOT', str(Path(__file__).resolve().parent))}"
        ],
        fix_available=False
    )

def handle_yaml_syntax(error: str, context: str) -> DiagnosisResponse:
    """Handle generic YAML syntax errors."""
    match = re.search(r"line (\d+): (.+)", error)
    line_num = int(match.group(1)) if match else 0
    error_msg = match.group(2) if match and len(match.groups()) > 1 else "syntax error"
    
    return DiagnosisResponse(
        id=f"DIAG-YAML-SYNTAX-{line_num}",
        error_type="YAML Syntax Error",
        root_cause=f"Line {line_num}: {error_msg}",
        fix_steps=[
            "Check indentation (use spaces, not tabs)",
            "Verify all colons have space after them",
            "Check for unmatched quotes or brackets"
        ],
        fix_available=False
    )

def handle_docker_build_error(error: str, context: str) -> DiagnosisResponse:
    """Handle Docker build failures."""
    match = re.search(r"Service '(.+)' failed to build", error)
    service_name = match.group(1) if match else "unknown"
    
    dockerfile_path = Path(context) / f"containers/{service_name}/Dockerfile"
    
    diagnosis = DiagnosisResponse(
        id=f"DIAG-DOCKER-{service_name}",
        error_type="Docker Build Error",
        root_cause=f"Service '{service_name}' failed to build",
        fix_steps=[
            f"Check Dockerfile: {dockerfile_path}",
            "Verify all COPY/ADD paths exist",
            "Check base image availability",
            "Review build logs for specific error"
        ],
        fix_available=False
    )
    
    if bus:
        bus.publish(
            event_type="diagnostic.analysis_complete",
            payload={
                "diagnosis_id": diagnosis.id,
                "error_type": diagnosis.error_type,
                "service_name": service_name
            },
            source_server="error-detector"
        )
    
    return diagnosis

def handle_port_conflict(error: str, context: str) -> DiagnosisResponse:
    """Handle port binding conflicts."""
    # Try to extract port number
    port_match = re.search(r":(\d+)", error)
    port = port_match.group(1) if port_match else "unknown"
    
    diagnosis = DiagnosisResponse(
        id=f"DIAG-PORT-{port}",
        error_type="Port Conflict",
        root_cause=f"Port {port} is already in use",
        fix_steps=[
            f"Find process using port: netstat -ano | findstr :{port}",
            "Kill conflicting process or change EPOS port",
            "Check if another EPOS instance is running"
        ],
        fix_available=False
    )
    
    if bus:
        bus.publish(
            event_type="diagnostic.analysis_complete",
            payload={
                "diagnosis_id": diagnosis.id,
                "error_type": diagnosis.error_type,
                "port": port
            },
            source_server="error-detector"
        )
    
    return diagnosis

def handle_import_error(error: str, context: str) -> DiagnosisResponse:
    """Handle Python import errors."""
    match = re.search(r"No module named '(.+)'", error)
    module_name = match.group(1) if match else "unknown"
    
    return DiagnosisResponse(
        id=f"DIAG-IMPORT-{module_name}",
        error_type="Module Import Error",
        root_cause=f"Missing Python module: {module_name}",
        fix_steps=[
            f"Install module: pip install {module_name}",
            "Or add to requirements.txt",
            "Check if module is in correct directory"
        ],
        fix_available=False
    )

def handle_docker_not_running(error: str, context: str) -> DiagnosisResponse:
    """Handle Docker daemon not running."""
    return DiagnosisResponse(
        id="DIAG-DOCKER-DAEMON",
        error_type="Docker Not Running",
        root_cause="Docker daemon is not running",
        fix_steps=[
            "Start Docker Desktop",
            "Wait for Docker to fully start",
            "Verify: docker ps"
        ],
        fix_available=False
    )

# ============================================
# API ENDPOINTS
# ============================================
@app.post("/analyze", response_model=DiagnosisResponse)
async def analyze_error(request: ErrorAnalysisRequest) -> DiagnosisResponse:
    """
    Analyze error and provide diagnosis.
    
    Example:
    POST /analyze
    {
        "error": "yaml: line 47: found unexpected end of stream",
        "context": "${EPOS_ROOT}"
    }
    """
    logger.info(f"Analyzing error: {request.error[:100]}...")
    
    error_type, groups, handler_name = detect_error_type(request.error)
    
    if handler_name:
        handler = globals()[handler_name]
        diagnosis = handler(request.error, request.context)
        
        logger.info(f"Diagnosis: {diagnosis.id} - {diagnosis.error_type}")
        return diagnosis
    
    logger.warning("Unknown error type")
    return DiagnosisResponse(
        id="DIAG-UNKNOWN",
        error_type="Unknown Error",
        root_cause="Unable to automatically diagnose",
        fix_steps=[
            "Review full error message",
            "Check EPOS logs in context_vault/",
            "Manual investigation required"
        ],
        fix_available=False
    )

@app.post("/apply-fix")
async def apply_fix(request: FixRequest):
    """Apply automated fix (if available)."""
    # TODO: Implement auto-fix logic
    return {
        "success": False,
        "message": "Auto-fix not yet implemented for this error type"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "error-detector",
        "port": 8115,
        "event_bus": "connected" if BUS_AVAILABLE else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/patterns")
async def list_patterns():
    """List all supported error patterns."""
    return {
        "patterns": list(ERROR_PATTERNS.keys()),
        "count": len(ERROR_PATTERNS)
    }

# ============================================
# STARTUP
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 50)
    logger.info("EPOS ERROR DETECTOR SERVICE")
    logger.info("=" * 50)
    logger.info("Port: 8115")
    logger.info("Event Bus: " + ("Connected" if BUS_AVAILABLE else "Standalone"))
    logger.info("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8115,
        log_level="info"
    )
