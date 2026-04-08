from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from epos_hq.core.receipts import utc_now


POLICY_PATH = Path("epos_hq/contracts/self_ops/self_ops_policy.json")
RECEIPTS_DIR = Path("epos_hq/data/receipts")
STATE_DIR = Path("epos_hq/data/self_ops")
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Issue:
    kind: str
    message: str
    details: Dict[str, Any]


class SelfOps:
    """
    EPOS Self-Ops:
    - Observes receipts/logs
    - Detects repeated failures
    - Produces a repair plan (JSON)
    - (Optional) dispatches repair tasks via your existing task entrypoint
    """

    def __init__(self):
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        if not POLICY_PATH.exists():
            return {"self_ops": {}}
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def scan_receipts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        if not RECEIPTS_DIR.exists():
            return []
        cutoff = time.time() - (minutes * 60)
        out = []
        for f in RECEIPTS_DIR.rglob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    continue
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

    def detect_issues(self, receipts: List[Dict[str, Any]]) -> List[Issue]:
        # Detect repeated failures by (intent + task_type + error.type)
        failures = [r for r in receipts if r.get("status") == "FAILED"]
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for r in failures:
            err = (r.get("error") or {}).get("type", "UnknownError")
            key = f"{r.get('intent','unknown')}::{r.get('task_type','unknown')}::{err}"
            buckets.setdefault(key, []).append(r)

        issues = []
        for key, items in buckets.items():
            if len(items) >= int(self.policy.get("self_ops", {}).get("escalation", {}).get("max_same_error_repeat", 2)):
                issues.append(Issue(
                    kind="repeated_failure",
                    message=f"Repeated failure detected: {key}",
                    details={"count": len(items), "sample": items[0]}
                ))
        return issues

    def build_repair_plan(self, issues: List[Issue]) -> Dict[str, Any]:
        plan_id = f"repair_{uuid.uuid4().hex[:10]}"
        now = utc_now()

        # Default: no direct action; propose steps.
        steps = [{
            "step_id": "note_1",
            "type": "note",
            "payload": {
                "timestamp": now,
                "issues": [i.__dict__ for i in issues],
                "instruction": "Generate a targeted repair plan per issue type (dependency/config/router/worker)."
            }
        }]

        plan = {
            "plan_id": plan_id,
            "summary": f"Self-Ops detected {len(issues)} issue(s). Proposed repair workflow queued.",
            "risk": "low",
            "needs_approval": True,  # start conservative
            "steps": steps,
            "expected_receipts": []
        }

        return plan

    def save_plan(self, plan: Dict[str, Any]) -> Path:
        out = STATE_DIR / f"{plan['plan_id']}.json"
        out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        return out


def run_once(minutes: int = 60) -> str:
    so = SelfOps()
    receipts = so.scan_receipts(minutes=minutes)
    issues = so.detect_issues(receipts)
    plan = so.build_repair_plan(issues)
    path = so.save_plan(plan)
    return str(path)

import httpx

SIDECAR_URL = "http://localhost:8010"

def dispatch_plan(plan_path: str, auto_execute: bool = False) -> None:
    """
    Dispatches a repair plan into EPOS via /mcp/submit_task.
    Respects policy: auto_execute only allowed for low-risk plans.
    """
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))

    if plan.get("needs_approval", True) and not auto_execute:
        print("[SELF_OPS] Plan requires approval. Not dispatching.")
        return

    for step in plan.get("steps", []):
        if step["type"] == "note":
            continue

        task = {
            "run_id": plan["plan_id"],
            "type": f"self_ops.{step['type']}",
            "required_capability": "self_ops",
            "intent": "self_repair",
            "role": "self_ops",
            "inputs": step["payload"]
        }

        print(f"[SELF_OPS] Dispatching step {step['step_id']}")

        httpx.post(
            f"{SIDECAR_URL}/mcp/submit_task",
            json=task,
            timeout=30
        )
