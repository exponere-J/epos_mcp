import asyncio
import httpx
import time
import uuid
from pathlib import Path

from epos_hq.core.receipts import Receipt, write_receipt, payload_hash, build_error, utc_now

SIDECAR_URL = "http://localhost:8010"
_RECEIPT_BASE = Path("epos_hq/data")

def _ensure_task_identity(task: dict) -> dict:
    if not isinstance(task, dict):
        return {"id": str(uuid.uuid4()), "run_id": "default", "type": "unknown", "intent": "unknown", "role": "unknown"}

    task.setdefault("id", str(uuid.uuid4()))
    task.setdefault("run_id", task.get("mission_id") or "default")
    task.setdefault("intent", task.get("intent") or "unknown")
    task.setdefault("role", task.get("role") or "unknown")
    task.setdefault("type", task.get("type") or "unknown")
    task.setdefault("retry_count", int(task.get("retry_count", 0) or 0))
    return task

def _write_task_receipt(*, task: dict, status: str, agent: str, started_at: str, outputs: dict | None = None, error: Exception | None = None):
    rec = Receipt(
        run_id=str(task.get("run_id", "default")),
        task_id=str(task.get("id", "unknown")),
        task_type=str(task.get("type", "unknown")),
        intent=str(task.get("intent", "unknown")),
        agent=str(agent),
        status=status,
        started_at=started_at,
        finished_at=utc_now(),
        retry_count=int(task.get("retry_count", 0) or 0),
        payload_hash=payload_hash(task),
        outputs=outputs or None,
        error=build_error(error) if error else None,
    )
    write_receipt(_RECEIPT_BASE, rec)

class MCPWorker:
    def __init__(self, agent_id, role, capabilities):
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities

    async def connect(self):
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{SIDECAR_URL}/mcp/register_worker", json={
                    "worker_id": self.agent_id,
                    "model": "local",
                    "capabilities": self.capabilities
                })
                print(f"✅ {self.agent_id} connected to Sidecar.")
            except Exception as e:
                print(f"❌ Connection failed: {e}")

    async def run_loop(self, execute_fn):
        print(f"🚀 {self.agent_id} loop started.")
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.post(f"{SIDECAR_URL}/mcp/request_task", params={"worker_id": self.agent_id})
                    data = res.json()

                    task = data.get("task")
                    if task:
                        task = _ensure_task_identity(task)
                        started_at = utc_now()

                        print(f"🔨 {self.agent_id} working on {task['type']}...")

                        try:
                            output = await execute_fn(task)

                            _write_task_receipt(
                                task=task,
                                status="COMPLETED",
                                agent=self.agent_id,
                                started_at=started_at,
                                outputs={"output": output},
                            )

                            event = {
                                "topic": "task.completed",
                                "payload": {
                                    "task_id": task["id"],
                                    "run_id": task.get("run_id", "default"),
                                    "type": task.get("type"),
                                    "intent": task.get("intent"),
                                    "role": task.get("role"),
                                    "output": output
                                },
                                "source": self.agent_id
                            }
                            await client.post(f"{SIDECAR_URL}/mcp/publish_event", json=event)

                        except Exception as e:
                            _write_task_receipt(
                                task=task,
                                status="FAILED",
                                agent=self.agent_id,
                                started_at=started_at,
                                error=e,
                            )

                            event = {
                                "topic": "task.failed",
                                "payload": {
                                    "task_id": task["id"],
                                    "run_id": task.get("run_id", "default"),
                                    "type": task.get("type"),
                                    "intent": task.get("intent"),
                                    "role": task.get("role"),
                                    "error": str(e)
                                },
                                "source": self.agent_id
                            }
                            await client.post(f"{SIDECAR_URL}/mcp/publish_event", json=event)

                    else:
                        await asyncio.sleep(2)

            except Exception as e:
                print(f"⚠️ Worker Error: {e}")
                await asyncio.sleep(5)
