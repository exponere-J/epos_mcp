#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
permission_audit.py — Pre-Flight Write-Access Verification
===========================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-01 (Step C: Path & Secret Sanitation)

Verifies write-access to every directory the SCC and Desktop CODE
need to touch before any file modification is attempted.
Article XIV: Pre-Mortem Mandate — audit before act.

Vault: context_vault/reports/
Event: system.permission_audit.complete
"""

import os
import sys
import json
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
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))

# All directories that sanitation directives write to
AUDIT_TARGETS = [
    EPOS_ROOT / "epos",
    EPOS_ROOT / "epos" / "tools",
    EPOS_ROOT / "epos" / "agents",
    EPOS_ROOT / "epos" / "state",
    EPOS_ROOT / "epos" / "models",
    EPOS_ROOT / "epos" / "pm",
    EPOS_ROOT / "engine",
    EPOS_ROOT / "friday",
    EPOS_ROOT / "friday" / "executors",
    EPOS_ROOT / "friday" / "skills",
    EPOS_ROOT / "reactor",
    VAULT,
    VAULT / "aar",
    VAULT / "reports",
    VAULT / "infrastructure",
    VAULT / "sessions",
]


class PermissionAudit:
    """Pre-flight write-access verification for EPOS tools directories."""

    def run(self) -> dict:
        """
        Audit all AUDIT_TARGETS for write access.
        Creates missing directories.
        Returns structured report.
        """
        results = []
        writable = 0
        failed = []

        for target in AUDIT_TARGETS:
            # Create if missing
            try:
                target.mkdir(parents=True, exist_ok=True)
                created = True
            except Exception as e:
                results.append({
                    "path": str(target),
                    "exists": target.exists(),
                    "writable": False,
                    "error": f"mkdir failed: {e}",
                })
                failed.append(str(target))
                continue

            # Test write access with a probe file
            probe = target / ".write_probe"
            try:
                probe.write_text("probe", encoding="utf-8")
                probe.unlink()
                results.append({
                    "path": str(target),
                    "exists": True,
                    "writable": True,
                    "error": None,
                })
                writable += 1
            except Exception as e:
                results.append({
                    "path": str(target),
                    "exists": target.exists(),
                    "writable": False,
                    "error": str(e),
                })
                failed.append(str(target))

        status = "PASS" if not failed else "FAIL"
        report = {
            "audit_id": "PERM-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "directories_checked": len(AUDIT_TARGETS),
            "directories_writable": writable,
            "directories_failed": len(failed),
            "failed_paths": failed,
            "results": results,
        }

        # Persist report
        report_path = VAULT / "reports" / "permission_audit.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Publish event
        if _BUS:
            try:
                _BUS.publish("system.permission_audit.complete", {
                    "status": status,
                    "checked": len(AUDIT_TARGETS),
                    "writable": writable,
                    "failed": len(failed),
                }, source_module="permission_audit")
            except Exception:
                pass

        return report

    def health_check(self) -> dict:
        report = self.run()
        return {
            "status": "operational" if report["status"] == "PASS" else "degraded",
            "directories_writable": report["directories_writable"],
            "directories_checked": report["directories_checked"],
        }


def run_audit() -> dict:
    """Module-level entry point."""
    return PermissionAudit().run()


if __name__ == "__main__":
    report = run_audit()
    print(f"Status:      {report['status']}")
    print(f"Checked:     {report['directories_checked']}")
    print(f"Writable:    {report['directories_writable']}")
    print(f"Failed:      {report['directories_failed']}")
    if report["failed_paths"]:
        print("FAILED PATHS:")
        for p in report["failed_paths"]:
            print(f"  ! {p}")
    else:
        print("All directories writable — pre-flight PASS")
    assert report["status"] == "PASS", f"Permission audit FAILED: {report['failed_paths']}"
    print(f"\nPASS: permission_audit — {report['directories_writable']}/{report['directories_checked']} writable")
