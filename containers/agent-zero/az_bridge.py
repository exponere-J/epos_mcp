#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XIV, XVI
"""
Agent Zero Bridge — EPOS Governed Executor (with execution-arm routing)

Surfaces:
  - HTTP  :8105 /api/health           — status of bridge + arms
           /api/execute          POST — universal arm call
           /api/message_async    POST — back-compat executor endpoint
  - Event bus  mission.assigned       — legacy mission flow
               execution.arm.request  — universal arm call over bus
  - Inbox      /app/inbox/*.json      — file-drop mission flow

Every tool-bearing mission routes through nodes.execution_arm.execute,
which selects headless/headed and BrowserUse/ComputerUse, applies the
deletion gate, and logs the outcome.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# /app is the WORKDIR set in the AZ Dockerfile; engine/ and nodes/ are copied there.
sys.path.insert(0, "/app")

try:
    from event_bus import get_event_bus
except Exception:  # pragma: no cover - bus optional in minimal test contexts
    def get_event_bus():  # type: ignore[misc]
        return _StubBus()


try:
    from nodes.execution_arm import execute as arm_execute, health as arm_health  # type: ignore
    _ARM_AVAILABLE = True
    _ARM_IMPORT_ERROR = ""
except Exception as e:  # noqa: BLE001
    _ARM_AVAILABLE = False
    _ARM_IMPORT_ERROR = f"{type(e).__name__}: {e}"

    def arm_execute(task: str, mode_hint: str | None = "auto",
                    max_steps: int = 8, context: dict | None = None) -> dict:
        return {
            "success": False,
            "error": f"execution_arm not importable: {_ARM_IMPORT_ERROR}",
        }

    def arm_health() -> dict:
        return {"status": "unavailable", "reason": _ARM_IMPORT_ERROR}


AZ_HTTP_PORT = int(os.getenv("AZ_HTTP_PORT", "8105"))


class _StubBus:
    def publish(self, *a, **kw): pass
    def subscribe(self, *a, **kw): pass
    def start_polling(self, *a, **kw): pass


# ── HTTP surface ───────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    server_version = "EPOS-AZ/1.0"

    def _send(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return {"_raw": raw}

    def log_message(self, fmt, *args):  # silence default access log
        return

    def do_GET(self):  # noqa: N802
        if self.path == "/api/health":
            return self._send(200, {
                "bridge": "operational",
                "arm_available": _ARM_AVAILABLE,
                "arm_health": arm_health(),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
        return self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        body = self._read_json()

        if self.path == "/api/execute":
            task = body.get("task", "")
            if not task:
                return self._send(400, {"error": "task required"})
            result = arm_execute(
                task=task,
                mode_hint=body.get("mode_hint", "auto"),
                max_steps=int(body.get("max_steps", 8)),
                context=body.get("context") or {},
            )
            return self._send(200, result)

        if self.path == "/api/message_async":
            # Back-compat with friday/executors/*_executor.py
            task = body.get("text", "") or body.get("description", "")
            tools = body.get("tools") or []
            ctx = body.get("context") or {}
            mission_id = ctx.get("mission_id", f"M_{int(time.time())}")

            if not task:
                return self._send(400, {"error": "text or description required"})

            # Route to arm if the caller asked for a tool, else acknowledge.
            if any(t in ("computer_use", "browser_use", "execution_arm") for t in tools):
                hint = (
                    "computer_use" if "computer_use" in tools
                    else "browser_use" if "browser_use" in tools
                    else "auto"
                )
                result = arm_execute(
                    task=task, mode_hint=hint,
                    max_steps=int(body.get("max_steps", 8)),
                    context={**ctx, "mission_id": mission_id},
                )
                return self._send(202, {
                    "mission_id": mission_id,
                    "message": "arm dispatched",
                    "response": result,
                })

            return self._send(202, {
                "mission_id": mission_id,
                "message": f"Mission acknowledged (no tools): {task[:200]}",
            })

        return self._send(404, {"error": "not found"})


def _start_http() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", AZ_HTTP_PORT), _Handler)
    print(f"[AZ-Bridge] HTTP on 0.0.0.0:{AZ_HTTP_PORT} (arm_available={_ARM_AVAILABLE})")
    server.serve_forever()


# ── Governed bridge (existing behavior preserved) ───────────────────

class AgentZeroBridge:
    def __init__(self) -> None:
        self.agent_id = os.getenv("AGENT_ID", "agent-zero")
        self.role = os.getenv("ROLE", "software_development")
        self.inbox = Path("/app/inbox")
        self.outbox = Path("/app/outbox")
        self.bus = get_event_bus()
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)
        print(f"[AZ-Bridge] Agent ID: {self.agent_id}")
        print(f"[AZ-Bridge] Role: {self.role}")

    def start(self) -> None:
        print("[AZ-Bridge] Starting governed execution loop...")
        # Start HTTP in a daemon thread
        threading.Thread(target=_start_http, daemon=True).start()

        self.bus.publish(
            event_type="agent.online",
            payload={"agent_id": self.agent_id, "role": self.role,
                     "status": "ready", "arm_available": _ARM_AVAILABLE},
            source_server=self.agent_id,
        )
        self.bus.subscribe("mission.assigned", self._handle_mission)
        self.bus.subscribe("execution.arm.request", self._handle_arm_request)
        self.bus.subscribe("governance.correction", self._handle_correction)
        self.bus.subscribe("learning.lesson", self._handle_lesson)
        try:
            self.bus.start_polling(interval=2.0)
        except Exception:
            pass

        print("[AZ-Bridge] READY — Awaiting missions")
        while True:
            self._check_inbox()
            time.sleep(5)

    def _check_inbox(self) -> None:
        for mission_file in self.inbox.glob("*.json"):
            try:
                with open(mission_file, "r", encoding="utf-8") as f:
                    mission = json.load(f)
                self._process_mission(mission)
                processed = self.inbox / "processed"
                processed.mkdir(exist_ok=True)
                mission_file.rename(processed / mission_file.name)
            except Exception as e:
                print(f"[AZ-Bridge] Error processing {mission_file}: {e}")

    def _handle_mission(self, event):
        self._process_mission((event or {}).get("payload", {}))

    def _handle_arm_request(self, event):
        payload = (event or {}).get("payload", {}) or {}
        result = arm_execute(
            task=payload.get("task", ""),
            mode_hint=payload.get("mode_hint", "auto"),
            max_steps=int(payload.get("max_steps", 8)),
            context=payload.get("context") or {},
        )
        self.bus.publish(
            event_type="execution.arm.response",
            payload=result,
            metadata={"trace_id": payload.get("mission_id", "")},
            source_server=self.agent_id,
        )

    def _process_mission(self, mission: dict) -> None:
        mission_id = mission.get("mission_id") or mission.get("id") \
            or f"M_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[AZ-Bridge] Processing mission: {mission_id}")

        self.bus.publish(
            event_type="agent.mission_started",
            payload={"agent_id": self.agent_id, "mission_id": mission_id,
                     "mission_type": mission.get("type", "unknown"),
                     "description": mission.get("description", "")},
            metadata={"trace_id": mission_id},
            source_server=self.agent_id,
        )

        self.bus.publish(
            event_type="governance.validation_request",
            payload={"mission_id": mission_id, "mission_content": mission,
                     "requesting_agent": self.agent_id},
            metadata={"trace_id": mission_id},
            source_server=self.agent_id,
        )

        # Route to execution arm when tools are requested
        tools = mission.get("tools") or []
        if tools and _ARM_AVAILABLE:
            hint = (
                "computer_use" if "computer_use" in tools
                else "browser_use" if "browser_use" in tools
                else "auto"
            )
            result = arm_execute(
                task=mission.get("description", "") or mission.get("task", ""),
                mode_hint=hint,
                max_steps=int(mission.get("max_steps", 8)),
                context={**(mission.get("context") or {}), "mission_id": mission_id},
            )
        else:
            result = {
                "status": "executed",
                "message": f"Mission acknowledged: {mission.get('description', '?')[:200]}",
                "executed_at": datetime.now().isoformat(),
            }

        self.bus.publish(
            event_type="governance.output_review",
            payload={"mission_id": mission_id, "agent_id": self.agent_id, "output": result},
            metadata={"trace_id": mission_id},
            source_server=self.agent_id,
        )

        self.bus.publish(
            event_type="agent.mission_completed",
            payload={"agent_id": self.agent_id, "mission_id": mission_id,
                     "status": "completed",
                     "result_location": str(self.outbox / f"{mission_id}_result.json")},
            metadata={"trace_id": mission_id},
            source_server=self.agent_id,
        )

        result_file = self.outbox / f"{mission_id}_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({"mission_id": mission_id, "status": "completed",
                       "result": result, "completed_at": datetime.now().isoformat()},
                      f, indent=2)
        print(f"[AZ-Bridge] Mission {mission_id} completed")

    def _handle_correction(self, event):
        correction = (event or {}).get("payload", {})
        print(f"[AZ-Bridge] Correction: {correction.get('violation_type')}")
        self.bus.publish(
            event_type="agent.correction_received",
            payload={"agent_id": self.agent_id, "correction": correction},
            source_server=self.agent_id,
        )

    def _handle_lesson(self, event):
        lesson = (event or {}).get("payload", {})
        print(f"[AZ-Bridge] Lesson: {lesson.get('lesson_id')}")
        lessons_dir = Path("/app/context_vault/learning/agent_lessons")
        lessons_dir.mkdir(parents=True, exist_ok=True)
        lesson_file = lessons_dir / f"{lesson.get('lesson_id', 'unknown')}.json"
        with open(lesson_file, "w", encoding="utf-8") as f:
            json.dump(lesson, f, indent=2)


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT ZERO BRIDGE — GOVERNED EXECUTOR + EXECUTION ARM")
    print("Constitutional Authority: Articles V, X, XIV, XVI")
    print(f"Execution Arm available: {_ARM_AVAILABLE}")
    if not _ARM_AVAILABLE:
        print(f"  reason: {_ARM_IMPORT_ERROR}")
    print("=" * 60)
    try:
        AgentZeroBridge().start()
    except KeyboardInterrupt:
        print("\n[AZ-Bridge] Shutdown requested — Goodbye")
