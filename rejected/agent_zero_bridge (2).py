# File: C:\Users\Jamie\workspace\epos_mcp\engine\agent_zero_bridge.py
# ═══════════════════════════════════════════════════════════════
# EPOS GOVERNANCE WATERMARK
# ───────────────────────────────────────────────────────────────
# Triage ID:      TRG-20260218-BRIDGE-V1
# First Submitted: 2026-02-18T07:00:00Z
# Triage Result:   PROMOTED (attempt 1 of 1)
# Promoted At:     2026-02-18T07:00:00Z
# Destination:     engine/agent_zero_bridge.py
# Constitutional:  Article II, III, VII compliant
# Violations:      None
# Watermark Hash:  PENDING_FIRST_TRIAGE
# ═══════════════════════════════════════════════════════════════

"""
EPOS Agent Zero Bridge v1.0 — Mission Execution Interface

Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles II, III, VII
Component ID: C4 (per Component Interaction Matrix)

Failure Modes (per Matrix):
  FM-B1: Agent Zero Import Failure  → graceful degradation
  FM-B2: Mission Translation Error  → ValueError with fix guidance
  FM-B3: LLM Execution Timeout      → configurable, mission marked failed
  FM-B4: Work Directory Full         → pre-check disk space
"""

import os
import sys
import json
import time
import socket
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
AGENT_ZERO_PATH = Path(os.getenv("AGENT_ZERO_PATH", "C:/Users/Jamie/workspace/agent-zero"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
WORK_DIR = AGENT_ZERO_PATH / "work_dir"
LOG_DIR = EPOS_ROOT / "logs"
MISSION_TIMEOUT = int(os.getenv("EPOS_MISSION_TIMEOUT", "300"))

# ── Logging (Article II Rule 2) ───────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("epos.bridge")
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(LOG_DIR / "agent_zero_bridge.log", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
logger.addHandler(_fh)

# ── Agent Zero Import (FM-B1) ─────────────────────────────────
_az_available = False
_az_import_error: Optional[str] = None

try:
    if AGENT_ZERO_PATH.exists() and (AGENT_ZERO_PATH / "python" / "agent.py").exists():
        az_python = AGENT_ZERO_PATH / "python"
        if str(az_python) not in sys.path:
            sys.path.insert(0, str(az_python))
        from agent import Agent  # type: ignore[import-untyped]
        _az_available = True
        logger.info("Agent Zero loaded from %s", AGENT_ZERO_PATH)
    else:
        _az_import_error = f"Agent Zero not found at {AGENT_ZERO_PATH}"
        logger.warning(_az_import_error)
except ImportError as exc:
    _az_import_error = f"Agent Zero import failed: {exc}"
    logger.warning(_az_import_error)
except Exception as exc:
    _az_import_error = f"Agent Zero init error: {exc}"
    logger.warning(_az_import_error)


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

def health_check() -> Dict[str, Any]:
    """Structured health report. Every claim is backed by evidence."""
    # Ollama
    ollama_ok = False
    try:
        port = int(OLLAMA_HOST.split(":")[-1])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        ollama_ok = s.connect_ex(("127.0.0.1", port)) == 0
        s.close()
    except (ValueError, OSError):
        pass

    # Work dir
    work_ok = False
    free_mb = 0
    try:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        _, _, free = shutil.disk_usage(WORK_DIR)
        free_mb = free // (1024 * 1024)
        work_ok = free_mb > 100
    except OSError:
        pass

    # Logs
    log_ok = False
    try:
        probe = LOG_DIR / ".bridge_probe"
        probe.write_text("ok")
        probe.unlink()
        log_ok = True
    except OSError:
        pass

    overall = _az_available and ollama_ok and work_ok and log_ok

    return {
        "ok": overall,
        "component": "agent_zero_bridge",
        "version": "1.0.0",
        "checks": {
            "agent_zero": {"ok": _az_available, "details": "loaded" if _az_available else _az_import_error},
            "ollama": {"ok": ollama_ok, "host": OLLAMA_HOST},
            "work_directory": {"ok": work_ok, "free_mb": free_mb},
            "logging": {"ok": log_ok},
        },
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# MISSION VALIDATION
# ═══════════════════════════════════════════════════════════════

REQUIRED_FIELDS = ["mission_id", "objective"]


def validate_mission(mission: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate before execution. Returns (ok, message)."""
    if not isinstance(mission, dict):
        return False, "Mission must be a JSON object"
    missing = [f for f in REQUIRED_FIELDS if f not in mission]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    if not mission.get("mission_id"):
        return False, "mission_id must be non-empty"
    if not mission.get("objective"):
        return False, "objective must be non-empty"
    vault = mission.get("context_vault_path")
    if vault:
        vp = Path(vault)
        if not vp.exists():
            return False, f"context_vault_path not found: {vault}"
        if "context_vault" not in str(vp):
            return False, f"context_vault_path must be in context_vault/: {vault}"
    return True, "Mission valid"


# ═══════════════════════════════════════════════════════════════
# MISSION TRANSLATION
# ═══════════════════════════════════════════════════════════════

def _translate(mission: Dict[str, Any]) -> str:
    """Convert structured EPOS mission to Agent Zero prompt."""
    parts = [f"Mission: {mission['objective']}"]
    if mission.get("context"):
        parts.append(f"\nContext: {mission['context']}")
    for label, key in [("Constraints", "constraints"), ("Success Criteria", "success_criteria")]:
        items = mission.get(key, [])
        if items:
            parts.append(f"\n{label}:")
            for item in items:
                parts.append(f"  - {item}")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# MISSION EXECUTION
# ═══════════════════════════════════════════════════════════════

def run_mission(mission: Dict[str, Any]) -> Dict[str, Any]:
    """Primary entry point. Called by Meta Orchestrator.

    Article II Rule 4: 'logged' ≠ 'executed'. Status reflects real outcome.
    """
    t0 = time.time()
    mid = mission.get("mission_id", "unknown")
    logger.info("Mission received: %s", mid)

    # Validate
    ok, msg = validate_mission(mission)
    if not ok:
        logger.error("Validation failed for %s: %s", mid, msg)
        return _result(mid, "failed", t0, error=f"Validation: {msg}")

    # Health gate
    h = health_check()
    if not h["checks"]["agent_zero"]["ok"]:
        logger.warning("AZ unavailable — %s in degraded mode", mid)
        r = _result(mid, "degraded", t0, error="Agent Zero not available. Mission logged, not executed.")
        _persist(mission, r)
        return r
    if not h["checks"]["ollama"]["ok"]:
        logger.warning("Ollama down — %s cannot run LLM tasks", mid)
        r = _result(mid, "degraded", t0, error="Ollama not responding.")
        _persist(mission, r)
        return r

    # Execute
    try:
        prompt = _translate(mission)
        logger.info("Translated %s (%d chars)", mid, len(prompt))

        agent = Agent(  # type: ignore[name-defined]
            agent_id=f"epos-{mid}",
            system_prompt=(
                "You are an EPOS agent executing a mission. "
                "Be precise. Follow constraints. Verify your work."
            ),
        )
        response = agent.run(prompt, timeout=MISSION_TIMEOUT)

        has_output = bool(response and str(response).strip())
        status = "completed" if has_output else "failed"
        r = _result(
            mid, status, t0,
            outputs={"response": str(response), "work_dir": str(WORK_DIR)} if has_output else None,
            error=None if has_output else "Agent Zero returned empty response",
        )
        logger.info("Mission %s %s in %dms", mid, status, r["execution_time_ms"])
        _persist(mission, r)
        return r

    except TimeoutError:
        logger.error("Mission %s timed out after %ds (FM-B3)", mid, MISSION_TIMEOUT)
        r = _result(mid, "failed", t0, error=f"Timeout ({MISSION_TIMEOUT}s)")
        _persist(mission, r)
        return r
    except Exception as exc:
        logger.error("Mission %s exception: %s", mid, exc)
        r = _result(mid, "failed", t0, error=str(exc))
        _persist(mission, r)
        return r


def _result(mid: str, status: str, t0: float, **kw) -> Dict[str, Any]:
    return {
        "status": status,
        "mission_id": mid,
        "execution_time_ms": int((time.time() - t0) * 1000),
        "outputs": kw.get("outputs"),
        "error": kw.get("error"),
    }


def _persist(mission: Dict[str, Any], result: Dict[str, Any]) -> None:
    """Append to mission_history.jsonl for audit trail."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "mission_id": mission.get("mission_id"),
        "objective": str(mission.get("objective", ""))[:200],
        "status": result["status"],
        "execution_time_ms": result["execution_time_ms"],
        "error": result.get("error"),
    }
    try:
        with open(LOG_DIR / "mission_history.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        logger.error("Mission log write failed: %s (Article II Rule 2 violation)", exc)


# ═══════════════════════════════════════════════════════════════
# WORK DIR CLEANUP (FM-B4 prevention)
# ═══════════════════════════════════════════════════════════════

def clean_work_dir(max_age_hours: int = 24) -> Dict[str, int]:
    """Remove files older than max_age_hours from work_dir."""
    if not WORK_DIR.exists():
        return {"removed": 0, "freed_bytes": 0}
    cutoff = time.time() - max_age_hours * 3600
    removed = freed = 0
    for item in WORK_DIR.rglob("*"):
        if item.is_file() and item.stat().st_mtime < cutoff:
            sz = item.stat().st_size
            try:
                item.unlink()
                removed += 1
                freed += sz
            except OSError:
                pass
    logger.info("Work dir cleanup: %d files, %dKB freed", removed, freed // 1024)
    return {"removed": removed, "freed_bytes": freed}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    pa = argparse.ArgumentParser(description="EPOS Agent Zero Bridge v1.0")
    pa.add_argument("--health", action="store_true")
    pa.add_argument("--clean", action="store_true")
    pa.add_argument("--test-mission", action="store_true")
    a = pa.parse_args()

    if a.health:
        print(json.dumps(health_check(), indent=2))
    elif a.clean:
        r = clean_work_dir()
        print(f"Cleaned: {r['removed']} files, {r['freed_bytes'] // 1024}KB freed")
    elif a.test_mission:
        print(json.dumps(run_mission({
            "mission_id": "test-bridge-001",
            "objective": "Verify bridge is functional.",
        }), indent=2))
    else:
        h = health_check()
        print(f"Bridge: {'OPERATIONAL' if h['ok'] else 'DEGRADED'}")
        for n, c in h["checks"].items():
            print(f"  {'PASS' if c['ok'] else 'FAIL'}: {n}")
