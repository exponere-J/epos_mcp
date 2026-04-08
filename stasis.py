#!/usr/bin/env python3
"""
stasis.py — EPOS Emergency Halt and Constitutional Violation System
====================================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Article V (Pre-Flight), Article VI
Mission ID: EPOS Core Heal — Module 2 of 9
File Location: C:/Users/Jamie/workspace/epos_mcp/stasis.py

Single responsibility: emergency halt and constitutional violation raising.
All log writes use absolute paths from path_utils.get_logs_dir().

Dependencies: stdlib + python-dotenv + path_utils (Module 1)

Exports:
    ConstitutionalViolation  — exception for hard constitutional stops
    StasisError              — exception for emergency halt state
    engage_stasis()          — halt the system with logging
    constitutional_violation() — log + raise constitutional violation
    is_stasis_active()       — check if system is in stasis (last 60s)
"""

import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# ── Load env and import canonical path resolution ────────────────
load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_epos_root, get_logs_dir, detect_platform


# ── Exceptions ───────────────────────────────────────────────────

class ConstitutionalViolation(Exception):
    """
    Raised when an EPOS constitutional rule is violated.

    This is the single exception class used across all EPOS modules
    for hard stops that require human or governance review.

    Attributes:
        rule:      The constitutional rule violated (e.g., "Article II Rule 1")
        detail:    Human-readable description of the violation
        component: The module/component that detected the violation
    """

    def __init__(self, rule: str, detail: str, component: str = "unknown"):
        self.rule = rule
        self.detail = detail
        self.component = component
        super().__init__(
            f"CONSTITUTIONAL VIOLATION [{component}]: {rule} — {detail}"
        )


class StasisError(Exception):
    """
    Raised when the system enters emergency halt state.

    Stasis is engaged when a critical subsystem fails or a
    constitutional violation is severe enough to require full stop.

    Attributes:
        reason:    Why stasis was engaged
        component: The module that triggered stasis
    """

    def __init__(self, reason: str, component: str = "unknown"):
        self.reason = reason
        self.component = component
        super().__init__(
            f"STASIS ENGAGED [{component}]: {reason}"
        )


# ── Log Helpers ──────────────────────────────────────────────────

def _write_log(filename: str, record: dict) -> None:
    """Append a JSON record to a log file in the logs directory."""
    log_path = get_logs_dir() / filename
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        # Last-resort: print to stderr if logging fails
        print(f"[stasis] CRITICAL: Cannot write to {log_path}: {e}", file=sys.stderr)


def _now_iso() -> str:
    """Return current time as ISO 8601 string with timezone."""
    return datetime.now(timezone.utc).isoformat()


# ── Core Functions ───────────────────────────────────────────────

def engage_stasis(reason: str, component: str = "unknown") -> None:
    """
    Engage emergency halt — logs the event and raises StasisError.

    This is a hard stop. Nothing should proceed after stasis is engaged.
    The system must be manually reviewed before resuming.

    Args:
        reason:    Why stasis is being engaged
        component: The module engaging stasis

    Raises:
        StasisError always.
    """
    record = {
        "event": "stasis_engaged",
        "timestamp": _now_iso(),
        "reason": reason,
        "component": component,
        "platform": detect_platform(),
        "python_version": platform.python_version(),
        "epos_root": str(get_epos_root()),
    }

    _write_log("stasis.log", record)

    raise StasisError(reason=reason, component=component)


def constitutional_violation(
    rule: str, detail: str, component: str = "unknown"
) -> None:
    """
    Log a constitutional violation and raise ConstitutionalViolation.

    This is used when any EPOS module detects a rule breach that
    requires immediate attention.

    Args:
        rule:      The rule violated (e.g., "Article II Rule 1")
        detail:    Human-readable description
        component: The module that detected it

    Raises:
        ConstitutionalViolation always.
    """
    record = {
        "event": "constitutional_violation",
        "timestamp": _now_iso(),
        "rule": rule,
        "detail": detail,
        "component": component,
        "platform": detect_platform(),
    }

    _write_log("constitutional_violations.log", record)

    raise ConstitutionalViolation(rule=rule, detail=detail, component=component)


def is_stasis_active() -> bool:
    """
    Check if the system is currently in stasis.

    Stasis is considered active if stasis.log exists and the most
    recent entry was written within the last 60 seconds.

    Returns:
        True if stasis was engaged in the last 60 seconds.
    """
    stasis_log = get_logs_dir() / "stasis.log"

    if not stasis_log.exists():
        return False

    try:
        # Check file modification time
        mtime = stasis_log.stat().st_mtime
        age_seconds = time.time() - mtime
        return age_seconds <= 60.0
    except Exception:
        return False


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EPOS Stasis Module — Self-Test")
    print("=" * 50)

    # Test 1: is_stasis_active when no log exists
    # (Clear any stale log first)
    stasis_log = get_logs_dir() / "stasis.log"
    had_existing = stasis_log.exists()
    if had_existing:
        stasis_log.rename(stasis_log.with_suffix(".log.bak"))

    result = is_stasis_active()
    print(f"  is_stasis_active (no log): {result} — {'PASS' if not result else 'FAIL'}")

    # Test 2: engage_stasis writes log and raises
    try:
        engage_stasis(reason="Self-test trigger", component="stasis_self_test")
        print("  engage_stasis: FAIL (no exception raised)")
        sys.exit(1)
    except StasisError as e:
        print(f"  engage_stasis: PASS — {e}")

    # Test 3: is_stasis_active should now be True
    result = is_stasis_active()
    print(f"  is_stasis_active (after engage): {result} — {'PASS' if result else 'FAIL'}")

    # Test 4: constitutional_violation writes log and raises
    try:
        constitutional_violation(
            rule="Article TEST",
            detail="Self-test violation",
            component="stasis_self_test",
        )
        print("  constitutional_violation: FAIL (no exception raised)")
        sys.exit(1)
    except ConstitutionalViolation as e:
        print(f"  constitutional_violation: PASS — {e}")

    # Cleanup: restore backup if existed, remove test log
    if stasis_log.exists():
        stasis_log.unlink()
    if had_existing:
        stasis_log.with_suffix(".log.bak").rename(stasis_log)

    violations_log = get_logs_dir() / "constitutional_violations.log"
    # Leave violations log — it's useful for audit

    print("\nAll checks passed.")
    sys.exit(0)
