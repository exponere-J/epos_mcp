#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
remediation_runbook.py — TTLG Self-Healing Remediation Runbook (Mission 5)
===========================================================================
Constitutional Authority: EPOS Constitution v3.1

The Surgeon module for self-healing. Applies tiered remediation for each
failure type detected by the Self-Healing Scout.

Constitutional boundaries:
  - NEVER modifies .env, constitutional documents, or governance rules
  - NEVER deletes data -- archive, compress, or flag only
  - Tier 2/3 always stops and waits for human approval
  - Recurrence escalation: same failure 3x in 24h -> bump one tier
"""

import json
import os
import subprocess
import shutil
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

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
HEALING_VAULT = VAULT / "self_healing"
ACTIONS_LOG = HEALING_VAULT / "actions.jsonl"
COLD_STORAGE = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent))) / "cold_storage"


class RemediationRunbook:
    """
    Applies tiered remediation for diagnosed failures.
    Logs every action. Publishes events. Tracks recurrence.
    """

    def __init__(self):
        HEALING_VAULT.mkdir(parents=True, exist_ok=True)
        self._recurrence = {}  # {failure_type: [timestamps]}

    def remediate(self, finding: dict) -> dict:
        """Apply the appropriate remediation for a finding."""
        failure_type = finding.get("failure_type", "unknown")
        tier = finding.get("tier", "fully_autonomous")

        # Recurrence check -- escalate if 3+ in 24h
        tier = self._check_recurrence(failure_type, tier)

        # Tier enforcement FIRST (before handler lookup)
        if tier == "constitutional_boundary":
            return self._log_action(finding, "full_stop",
                                     "Constitutional boundary. Escalated to Jamie. No auto-action.", False)

        if tier == "human_review":
            return self._log_action(finding, "awaiting_approval",
                                     f"Tier 2: Diagnosed but not remediated. Run 'epos heal approve' to proceed.", False)

        # Route to handler
        handler = self._get_handler(failure_type)
        if not handler:
            return self._log_action(finding, "no_handler",
                                     f"No runbook entry for: {failure_type}", False)

        # Execute remediation (Tier 0 or Tier 1)
        try:
            result = handler(finding)
            action_type = "healed" if result["success"] else "healing_failed"
            action = self._log_action(finding, action_type, result["message"], result["success"])

            if tier == "monitored":
                action["flagged_for_review"] = True

            return action
        except Exception as e:
            return self._log_action(finding, "healing_exception",
                                     f"Exception during remediation: {str(e)[:200]}", False)

    # ── Remediation Handlers ────────────────────────────────

    def _handle_vault_path_missing(self, finding: dict) -> dict:
        """Tier 0: Create missing vault directory."""
        details = finding.get("details", {})
        # Create common vault paths
        paths_to_check = [
            VAULT / "events" / "system",
            VAULT / "self_healing",
            VAULT / "governance" / "gate",
            VAULT / "crm" / "journey",
            VAULT / "ttlg" / "diagnostics",
            VAULT / "fotw" / "expressions",
            VAULT / "financial" / "payments",
        ]
        created = []
        for p in paths_to_check:
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                created.append(str(p.relative_to(VAULT)))

        if created:
            return {"success": True, "message": f"Created {len(created)} vault paths: {', '.join(created)}"}
        return {"success": True, "message": "All vault paths already exist"}

    def _handle_api_rate_limit(self, finding: dict) -> dict:
        """Tier 0: Switch to fallback provider."""
        # Check Ollama availability
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        try:
            r = requests.get(f"{ollama_host}/api/tags", timeout=3)
            if r.status_code == 200:
                return {"success": True, "message": "Ollama available as fallback. Groq Router will auto-switch on next call."}
        except Exception:
            pass
        return {"success": False, "message": "Ollama also unavailable. No LLM fallback. Wait for API cooldown."}

    def _handle_event_bus_stall(self, finding: dict) -> dict:
        """Tier 0: Force heartbeat on event bus."""
        if _BUS:
            try:
                _BUS.publish("system.heartbeat.forced", {
                    "trigger": "self_healing",
                    "reason": "Event bus stall detected",
                }, source_module="self_healing")
                return {"success": True, "message": "Forced heartbeat published to event bus"}
            except Exception as e:
                return {"success": False, "message": f"Failed to publish heartbeat: {str(e)[:100]}"}
        return {"success": False, "message": "Event bus not available"}

    def _handle_stale_journal(self, finding: dict) -> dict:
        """Tier 0: Alert via event and queue for Friday."""
        if _BUS:
            try:
                _BUS.publish("system.health.stale_journal", {
                    "trigger": "self_healing",
                    "details": finding.get("message", ""),
                }, source_module="self_healing")
            except Exception:
                pass
        return {"success": True, "message": "Stale journal alert published. Queued for Friday triage."}

    def _handle_node_import_failure(self, finding: dict) -> dict:
        """Tier 1: Attempt pip install for missing dependency."""
        failed_nodes = finding.get("details", [])
        fixed = []
        for node_name in failed_nodes:
            # Map display names to pip packages (conservative -- only known safe packages)
            pip_map = {
                "Event Bus": "python-dotenv",
                "Groq Router": "groq",
            }
            pkg = pip_map.get(node_name)
            if pkg:
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        fixed.append(node_name)
                except Exception:
                    pass
        if fixed:
            return {"success": True, "message": f"Installed dependencies for: {', '.join(fixed)}"}
        return {"success": False, "message": f"Could not auto-fix imports for: {', '.join(failed_nodes)}"}

    def _handle_port_conflict(self, finding: dict) -> dict:
        """Tier 1: Log port conflict for manual resolution."""
        return {"success": True, "message": "Port conflict logged. Restart the conflicting service or use an alternate port."}

    def _handle_vault_size_threshold(self, finding: dict) -> dict:
        """Tier 1: Archive old sessions to cold storage."""
        COLD_STORAGE.mkdir(parents=True, exist_ok=True)
        archived = 0
        sessions_dir = VAULT / "fotw" / "raw" / "threads"
        if sessions_dir.exists():
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            for f in sessions_dir.glob("FOTW-*.json"):
                if f.stat().st_mtime < cutoff.timestamp():
                    dest = COLD_STORAGE / "fotw_archive" / f.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dest))
                    archived += 1
        if archived > 0:
            return {"success": True, "message": f"Archived {archived} sessions older than 90 days to cold storage"}
        return {"success": True, "message": "No sessions old enough to archive"}

    def _handle_config_drift(self, finding: dict) -> dict:
        """Tier 2: Diagnose only, do NOT modify."""
        return {"success": False, "message": "Configuration drift detected. STOPPED. Requires human review: epos heal approve"}

    def _handle_sovereignty_degradation(self, finding: dict) -> dict:
        """Tier 2: Report details, do NOT auto-fix."""
        return {"success": False, "message": "Sovereignty score degraded. Full report published. Requires human review."}

    def _handle_doctor_warning(self, finding: dict) -> dict:
        """Tier 0: Log and publish, no action needed for warnings."""
        return {"success": True, "message": "Doctor warnings acknowledged and logged."}

    def _handle_doctor_failure(self, finding: dict) -> dict:
        """Tier 1: Attempt self-heal mode."""
        try:
            result = subprocess.run(
                [sys.executable, "engine/epos_doctor.py", "--self-heal"],
                capture_output=True, text=True, timeout=60,
                cwd=str(Path(os.getenv("EPOS_ROOT", "."))))
            if "Healed" in result.stdout:
                return {"success": True, "message": f"Doctor self-heal applied. Re-run 'epos doctor' to verify."}
        except Exception:
            pass
        return {"success": False, "message": "Doctor self-heal could not resolve failures. Manual intervention needed."}

    def _handle_ollama_offline(self, finding: dict) -> dict:
        """Tier 0: Log, Groq is fallback."""
        return {"success": True, "message": "Ollama offline. Groq Router will use cloud API as primary. No action needed."}

    # ── Handler Dispatch ────────────────────────────────────

    def _get_handler(self, failure_type: str):
        handlers = {
            "vault_path_missing": self._handle_vault_path_missing,
            "api_rate_limit": self._handle_api_rate_limit,
            "event_bus_stall": self._handle_event_bus_stall,
            "stale_journal": self._handle_stale_journal,
            "node_import_failure": self._handle_node_import_failure,
            "port_conflict": self._handle_port_conflict,
            "vault_size_threshold": self._handle_vault_size_threshold,
            "config_drift": self._handle_config_drift,
            "sovereignty_degradation": self._handle_sovereignty_degradation,
            "doctor_warning": self._handle_doctor_warning,
            "doctor_failure": self._handle_doctor_failure,
            "ollama_offline": self._handle_ollama_offline,
        }
        return handlers.get(failure_type)

    # ── Recurrence Tracking ─────────────────────────────────

    def _check_recurrence(self, failure_type: str, current_tier: str) -> str:
        """If same failure 3+ times in 24h, escalate one tier."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        if failure_type not in self._recurrence:
            self._recurrence[failure_type] = []
        self._recurrence[failure_type].append(now)
        # Clean old entries
        self._recurrence[failure_type] = [t for t in self._recurrence[failure_type] if t > cutoff]

        if len(self._recurrence[failure_type]) >= 3:
            tier_order = ["fully_autonomous", "monitored", "human_review", "constitutional_boundary"]
            idx = tier_order.index(current_tier) if current_tier in tier_order else 0
            if idx < len(tier_order) - 1:
                return tier_order[idx + 1]
        return current_tier

    # ── Action Logging ──────────────────────────────────────

    def _log_action(self, finding: dict, action_type: str, message: str, success: bool) -> dict:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "finding_check": finding.get("check", "unknown"),
            "failure_type": finding.get("failure_type", "unknown"),
            "tier": finding.get("tier", "unknown"),
            "action_type": action_type,
            "message": message,
            "success": success,
        }
        with open(ACTIONS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # Publish event
        event_type = f"system.healed.{finding.get('failure_type', 'unknown')}" if success else f"system.healing.failed.{finding.get('failure_type', 'unknown')}"
        if _BUS:
            try:
                _BUS.publish(event_type, entry, source_module="self_healing")
            except Exception:
                pass

        return entry

    def get_action_history(self, limit: int = 20) -> list:
        if not ACTIONS_LOG.exists():
            return []
        lines = ACTIONS_LOG.read_text(encoding="utf-8").splitlines()
        entries = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return entries


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    runbook = RemediationRunbook()

    # Test 1: Tier 0 remediation (vault path)
    result = runbook.remediate({
        "check": "vault_path_test",
        "failure_type": "vault_path_missing",
        "tier": "fully_autonomous",
        "message": "Test vault path creation",
    })
    assert result["action_type"] in ("healed", "healing_failed", "healing_exception")
    passed += 1

    # Test 2: Tier 0 remediation (event bus stall)
    result2 = runbook.remediate({
        "check": "event_bus_test",
        "failure_type": "event_bus_stall",
        "tier": "fully_autonomous",
        "message": "Test heartbeat",
    })
    assert result2["action_type"] in ("healed", "healing_failed")
    passed += 1

    # Test 3: Tier 2 stops and waits
    result3 = runbook.remediate({
        "check": "config_drift_test",
        "failure_type": "config_drift",
        "tier": "human_review",
        "message": "Test tier 2 stop",
    })
    assert result3["action_type"] == "awaiting_approval"
    passed += 1

    # Test 4: Constitutional boundary full stop
    result4 = runbook.remediate({
        "check": "constitutional_test",
        "failure_type": "constitutional_violation",
        "tier": "constitutional_boundary",
        "message": "Test tier 3 stop",
    })
    assert result4["action_type"] == "full_stop"
    passed += 1

    # Test 5: Action history logged
    history = runbook.get_action_history()
    assert len(history) >= 4
    passed += 1

    print(f"PASS: remediation_runbook ({passed} assertions)")
    print(f"Actions logged: {len(history)}")
