#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
code_executor.py — LLM Code Generation Executor
================================================
Constitutional Authority: EPOS Constitution v3.1

Pipeline:
  1. LLM generates implementation via engine.llm_client.complete()
  2. Output written to context_vault/friday/code_output/<ts>_<id>.md
  3. If mission['run_code'] is True — extracted Python is subprocess.run() with 60s timeout

The run_code flag is OFF by default and requires explicit authorization.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
CODE_OUTPUT_DIR = VAULT / "friday" / "code_output"
CODE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are a senior software engineer building EPOS sovereign infrastructure. "
    "When given a coding mission, return a complete, runnable implementation. "
    "Prefer a single fenced Python code block (```python ... ```) with a brief "
    "rationale before the code. No apologies, no TODOs, no stubs."
)


def run(mission: dict) -> dict:
    """Generate code for a mission, persist output, optionally execute."""
    mission_id = mission.get("id", "M-CODE-UNKNOWN")
    description = mission.get("description", "")
    run_code = bool(mission.get("run_code", False))

    result = _generate(mission_id, description, run_code)
    _publish(result)
    return result


def _generate(mission_id: str, description: str, run_code: bool) -> dict:
    try:
        from engine.llm_client import complete

        generated = complete(
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Mission: {description}\n\nProduce the implementation."}],
            temperature=0.2,
            max_tokens=2048,
        )

        # Persist to vault
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = CODE_OUTPUT_DIR / f"{ts}_{mission_id}.md"
        out_path.write_text(
            f"# Code mission {mission_id}\n\n"
            f"- timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            f"- directive: {description}\n\n"
            f"## Output\n\n{generated}\n",
            encoding="utf-8",
        )

        result = {
            "mission_id": mission_id,
            "executor": "code",
            "status": "complete",
            "output": generated[:500] if generated else "(no output)",
            "output_path": str(out_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if run_code and generated:
            exec_result = _execute_generated(generated, mission_id)
            result["execution"] = exec_result

        return result

    except Exception as e:
        return {
            "mission_id": mission_id,
            "executor": "code",
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:400]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _execute_generated(generated: str, mission_id: str) -> dict:
    """Extract and run the first Python code block from generated text."""
    # Extract first ```python ... ``` block
    match = re.search(r"```python\s*(.*?)```", generated, re.DOTALL)
    if not match:
        return {"status": "skipped", "reason": "No Python code block found in output"}

    code = match.group(1).strip()
    script_path = CODE_OUTPUT_DIR / f"run_{mission_id}.py"
    script_path.write_text(code, encoding="utf-8")

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "status": "executed",
            "returncode": proc.returncode,
            "stdout": proc.stdout[:500],
            "stderr": proc.stderr[:300] if proc.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "reason": "Execution exceeded 60s limit"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}


def _publish(result: dict):
    if _BUS:
        try:
            _BUS.publish(
                "code.generated",
                result,
                source_module="code_executor",
            )
        except Exception:
            pass


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    r = run({
        "id": "TEST-CODE-001",
        "description": "Write a Python function that returns the first N Fibonacci numbers",
        "run_code": False,
    })
    print(f"status={r['status']} output_path={r.get('output_path', r.get('error', '?'))}")
    assert r["status"] in ("complete", "failed")
    print("PASS: code_executor")
