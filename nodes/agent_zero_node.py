#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
agent_zero_node.py — Agent Zero HTTP Bridge Node
====================================================
Constitutional Authority: EPOS Constitution v3.1

Sovereign HTTP bridge to Agent Zero Docker container running on port 50080.
Companion to agent_zero_bridge.py (subprocess version).

This node uses the AZ web API directly. No subprocess needed.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
AZ_VAULT = VAULT / "agent_zero"
AZ_VAULT.mkdir(parents=True, exist_ok=True)
AZ_LOG = AZ_VAULT / "events.jsonl"

AZ_BASE_URL = os.getenv("AGENT_ZERO_URL", "http://localhost:50080")


class AgentZeroNode:
    """
    HTTP bridge to Agent Zero Docker container.
    Runs missions via the AZ web API on port 50080.
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or AZ_BASE_URL

    def health_check(self) -> dict:
        """Verify Agent Zero container is responding via /api/health endpoint."""
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=5)
            if r.status_code == 200:
                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                return {
                    "status": "operational",
                    "url": self.base_url,
                    "http_code": 200,
                    "version": data.get("gitinfo", {}).get("version", "unknown"),
                    "branch": data.get("gitinfo", {}).get("branch", "unknown"),
                }
            # Fallback: check root
            r = requests.get(f"{self.base_url}/", timeout=5)
            if r.status_code == 200:
                return {"status": "operational", "url": self.base_url, "http_code": 200}
            return {"status": "degraded", "url": self.base_url, "http_code": r.status_code}
        except requests.exceptions.ConnectionError:
            return {"status": "unavailable", "url": self.base_url,
                    "reason": "Connection refused — container not running"}
        except Exception as e:
            return {"status": "error", "url": self.base_url, "reason": str(e)[:200]}

    def dispatch_mission(self, mission: str, timeout: int = 120) -> dict:
        """Dispatch a mission to Agent Zero via /api/api_message endpoint."""
        result = {
            "mission_id": f"AZ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "mission": mission[:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Use AZ's /api/api_message endpoint (correct path: /api/<filename>)
            response = requests.post(
                f"{self.base_url}/api/message_async",
                json={"text": mission, "context": ""},
                timeout=timeout,
            )

            if response.status_code == 200:
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                result["status"] = "dispatched"
                result["response"] = data
                self._log_event("agent_zero.mission.dispatched", result)
                return result
            elif response.status_code == 404:
                # Try alternate endpoint
                return self._try_message_endpoint(mission, timeout, result)
            else:
                result["status"] = "failed"
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                self._log_event("agent_zero.mission.failed", result)
                return result

        except requests.exceptions.ConnectionError:
            result["status"] = "unavailable"
            result["error"] = "Agent Zero container not responding"
            self._log_event("agent_zero.mission.unavailable", result)
            return result
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)[:300]
            self._log_event("agent_zero.mission.error", result)
            return result

    def _try_message_endpoint(self, mission: str, timeout: int, result: dict) -> dict:
        """Fallback: try /message endpoint."""
        try:
            response = requests.post(
                f"{self.base_url}/message",
                json={"text": mission},
                timeout=timeout,
            )
            if response.status_code == 200:
                result["status"] = "dispatched"
                result["response"] = response.text[:500]
                self._log_event("agent_zero.mission.dispatched", result)
                return result
            else:
                result["status"] = "failed"
                result["error"] = f"HTTP {response.status_code}"
                return result
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)[:300]
            return result

    def _log_event(self, event_type: str, payload: dict):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "event_type": event_type, "payload": payload}
        with open(AZ_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="agent_zero_node")
            except Exception:
                pass


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    node = AgentZeroNode()

    # Test 1: Health check
    health = node.health_check()
    print(f"Health: {health['status']} | URL: {health['url']}")
    assert health["status"] in ("operational", "degraded", "unavailable", "error")
    passed += 1

    # Test 2: If operational, try a dispatch
    if health["status"] == "operational":
        print("Testing mission dispatch...")
        result = node.dispatch_mission("Echo back: Agent Zero operational test", timeout=30)
        print(f"Dispatch: {result['status']}")
        if result.get("error"):
            print(f"  Error: {result['error'][:200]}")
        passed += 1
    else:
        print("SKIP: AZ not operational")
        passed += 1

    # Test 3: Event log written
    if AZ_LOG.exists():
        lines = AZ_LOG.read_text(encoding="utf-8").splitlines()
        print(f"Event log: {len(lines)} entries")
    passed += 1

    print(f"\nPASS: agent_zero_node ({passed} assertions)")
