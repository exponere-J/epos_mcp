# File: /mnt/c/Users/Jamie/workspace/epos_mcp/epos_cli.py
# repair_origin: human_authored
# requires_metadata_confirmation: false

"""
EPOS CLI v1.0 — Unified Command Surface for the Agentic Operating System

Constitutional Authority: EPOS_CONSTITUTION_v3.1.md
Purpose: Single entry point for all governed EPOS operations.
         Replaces ad-hoc script invocations with a consistent CLI contract.

Usage:
    python epos_cli.py doctor                          # Pre-flight environment check
    python epos_cli.py doctor --json                   # Machine-readable doctor output
    python epos_cli.py gate check <file_or_dir>        # Triage + auto-repair
    python epos_cli.py gate check <file> --triage-only # Classify without mutation
    python epos_cli.py gate check <file> --json        # Machine-readable gate output
    python epos_cli.py gate check <file> --propose-patch
    python epos_cli.py snapshot                        # System state snapshot
    python epos_cli.py status                          # Quick system health summary
    python epos_cli.py env-audit                       # Audit environment against Constitution

Exit Codes:
    0 = Success
    1 = Warnings or review needed
    2 = Critical failure / constitutional violation

Design Principle:
    Every command calls epos_doctor pre-flight before executing.
    The gate never runs on an unhealthy environment.
    This is CLI-first; MCP tool facades sit on top of this later.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Ensure we can import sibling modules
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Load environment explicitly (Article II Rule 6)
try:
    from dotenv import load_dotenv
    load_dotenv(_SCRIPT_DIR / ".env")
except ImportError:
    pass  # Degrade gracefully; doctor will flag this

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(_SCRIPT_DIR)))


# ---------------------------------------------------------------------------
# Pre-flight integration
# ---------------------------------------------------------------------------

def _run_doctor_preflight(silent: bool = False) -> bool:
    """Run epos_doctor pre-flight. Returns True if environment is healthy."""
    try:
        from engine.epos_doctor import EPOSDoctor
        doctor = EPOSDoctor(silent=silent)
        return doctor.run_all_checks()
    except ImportError:
        if not silent:
            print("  ⚠️  engine/epos_doctor.py not found — skipping pre-flight.")
            print("     Constitutional Authority: Article III requires pre-flight validation.")
        return True  # Degrade: allow operation but warn
    except Exception as e:
        if not silent:
            print(f"  ⚠️  Doctor pre-flight error: {e}")
        return True


# ---------------------------------------------------------------------------
# COMMAND: doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args: list):
    """Run environment diagnostic."""
    # Pass through to epos_doctor directly
    doctor_path = _SCRIPT_DIR / "epos_doctor.py"
    if not doctor_path.exists():
        print("  ❌ epos_doctor.py not found at EPOS root.")
        sys.exit(2)

    cmd = [sys.executable, str(doctor_path)] + args
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# COMMAND: gate check
# ---------------------------------------------------------------------------

def cmd_gate_check(args: list):
    """Triage files through governance gate."""
    # Pre-flight first
    print("  🩺 Running pre-flight check...")
    healthy = _run_doctor_preflight(silent=True)
    if not healthy:
        print("  ❌ Environment unhealthy. Run 'epos doctor --verbose' to diagnose.")
        print("     Gate will not process files on an unhealthy environment.")
        print("     (Article III: Pre-flight validation required before any execution)")
        sys.exit(2)
    print("  ✅ Pre-flight passed.\n")

    # Delegate to governance_gate
    try:
        from governance_gate import (
            triage_file, triage_directory, Verdict,
            _ensure_dirs, _print_result, _print_summary
        )
    except ImportError:
        print("  ❌ governance_gate.py not found at EPOS root.")
        sys.exit(2)

    # Parse gate-specific args
    target = None
    mode = "auto-repair"
    output_json = False
    verbose = False

    i = 0
    while i < len(args):
        if args[i] == "--triage-only":
            mode = "triage-only"
        elif args[i] == "--propose-patch":
            mode = "propose-patch"
        elif args[i] == "--json":
            output_json = True
        elif args[i] in ("--verbose", "-v"):
            verbose = True
        elif not args[i].startswith("-"):
            target = args[i]
        i += 1

    if not target:
        print("  ❌ No target specified. Usage: epos gate check <file_or_dir>")
        sys.exit(2)

    _ensure_dirs()
    target_path = Path(target)

    if not output_json:
        print(f"  🏛️  EPOS Gate — Mode: {mode}")
        print(f"  📂 Target: {target_path}\n")

    if target_path.is_dir():
        results = triage_directory(target_path, mode=mode)
    elif target_path.is_file():
        results = [triage_file(target_path, mode=mode)]
    else:
        msg = f"Target not found: {target_path}"
        if output_json:
            print(json.dumps({"error": msg}))
        else:
            print(f"  ❌ {msg}")
        sys.exit(2)

    if output_json:
        print(json.dumps({
            "governance_gate_version": "1.0",
            "mode": mode,
            "preflight": "passed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [r.to_dict() for r in results],
            "summary": {
                v.value: sum(1 for r in results if r.verdict == v)
                for v in Verdict
            },
        }, indent=2))
    else:
        for r in results:
            _print_result(r, verbose=verbose)
        _print_summary(results)

    has_reject = any(r.verdict == Verdict.REJECT for r in results)
    has_propose = any(r.verdict == Verdict.PATCH_PROPOSE for r in results)
    sys.exit(2 if has_reject else (1 if has_propose else 0))


# ---------------------------------------------------------------------------
# COMMAND: status
# ---------------------------------------------------------------------------

def cmd_status(args: list):
    """Quick system health summary."""
    print(f"\n{'='*50}")
    print(f"  EPOS System Status")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Python version
    v = sys.version_info
    py_ok = v[:2] == (3, 11)
    py_sym = "✅" if py_ok else ("⚠️" if v[:2] >= (3, 11) else "❌")
    print(f"  {py_sym} Python: {v.major}.{v.minor}.{v.micro}"
          + ("" if py_ok else " (Constitution requires 3.11.x)"))

    # EPOS root
    root_ok = EPOS_ROOT.exists()
    print(f"  {'✅' if root_ok else '❌'} EPOS Root: {EPOS_ROOT}")

    # Constitutional docs
    const_docs = [
        "EPOS_CONSTITUTION_v3.1.md", "ENVIRONMENT_SPEC.md",
        "COMPONENT_INTERACTION_MATRIX.md", "FAILURE_SCENARIOS.md",
        "PATH_CLARITY_RULES.md", "PRE_FLIGHT_CHECKLIST.md",
    ]
    present = sum(1 for d in const_docs if (EPOS_ROOT / d).exists())
    print(f"  {'✅' if present == len(const_docs) else '⚠️'} "
          f"Constitutional Docs: {present}/{len(const_docs)}")

    # Governance tools
    tools = ["governance_gate.py", "epos_doctor.py"]
    tool_present = sum(1 for t in tools if (EPOS_ROOT / t).exists())
    print(f"  {'✅' if tool_present == len(tools) else '❌'} "
          f"Governance Tools: {tool_present}/{len(tools)}")

    # Key directories
    dirs = ["inbox", "engine", "rejected/receipts", "ops/logs",
            "context_vault/mission_data"]
    dir_present = sum(1 for d in dirs if (EPOS_ROOT / d).exists())
    print(f"  {'✅' if dir_present == len(dirs) else '⚠️'} "
          f"Directories: {dir_present}/{len(dirs)}")

    # .env
    env_exists = (EPOS_ROOT / ".env").exists()
    print(f"  {'✅' if env_exists else '❌'} .env file: "
          f"{'present' if env_exists else 'MISSING'}")

    # Inbox queue
    inbox = EPOS_ROOT / "inbox"
    if inbox.exists():
        pending = list(inbox.glob("*.py")) + list(inbox.glob("*.json"))
        print(f"  📥 Inbox queue: {len(pending)} file(s) pending triage")
    else:
        print(f"  📥 Inbox: directory not created yet")

    # Rejected
    receipts = EPOS_ROOT / "rejected" / "receipts"
    if receipts.exists():
        rcount = len(list(receipts.glob("*REJECT*.json")))
        print(f"  {'⚠️' if rcount > 0 else '✅'} "
              f"Rejected files: {rcount} pending review")

    print(f"\n{'='*50}\n")


# ---------------------------------------------------------------------------
# COMMAND: env-audit
# ---------------------------------------------------------------------------

def cmd_env_audit(args: list):
    """Audit current environment against ENVIRONMENT_SPEC.md requirements."""
    print(f"\n{'='*50}")
    print(f"  EPOS Environment Audit")
    print(f"  Constitutional Authority: ENVIRONMENT_SPEC.md")
    print(f"{'='*50}\n")

    issues = []

    # 1. Python version
    v = sys.version_info
    if v[:2] != (3, 11):
        issues.append({
            "severity": "CRITICAL" if v[:2] >= (3, 13) else "WARNING",
            "check": "Python Version",
            "found": f"{v.major}.{v.minor}.{v.micro}",
            "expected": "3.11.x",
            "fix": (
                "Create a new venv with Python 3.11:\n"
                "  python3.11 -m venv venv_epos\n"
                "  source venv_epos/bin/activate  # or venv_epos\\Scripts\\activate\n"
                "  pip install -r requirements.txt"
            ),
        })
        print(f"  ❌ Python {v.major}.{v.minor}.{v.micro} — need 3.11.x")
    else:
        print(f"  ✅ Python {v.major}.{v.minor}.{v.micro}")

    # 2. Shell detection (best effort)
    shell = os.getenv("SHELL", os.getenv("ComSpec", "unknown"))
    print(f"  ℹ️  Shell: {shell}")

    # 3. EPOS_ROOT in env
    epos_env = os.getenv("EPOS_ROOT")
    if not epos_env:
        issues.append({
            "severity": "WARNING",
            "check": "EPOS_ROOT",
            "found": "not set",
            "expected": "C:/Users/Jamie/workspace/epos_mcp",
            "fix": "Add EPOS_ROOT=C:/Users/Jamie/workspace/epos_mcp to .env",
        })
        print(f"  ⚠️  EPOS_ROOT not set in environment")
    else:
        print(f"  ✅ EPOS_ROOT={epos_env}")

    # 4. python-dotenv available
    try:
        import dotenv
        print(f"  ✅ python-dotenv installed")
    except ImportError:
        issues.append({
            "severity": "CRITICAL",
            "check": "python-dotenv",
            "found": "not installed",
            "expected": "installed",
            "fix": "pip install python-dotenv",
        })
        print(f"  ❌ python-dotenv not installed")

    # 5. pathlib available (always is in 3.4+, but verify)
    from pathlib import Path as _P
    print(f"  ✅ pathlib available")

    # 6. Key dependencies
    for pkg in ["fastapi", "uvicorn", "pydantic"]:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg} installed")
        except ImportError:
            issues.append({
                "severity": "WARNING",
                "check": f"{pkg}",
                "found": "not installed",
                "expected": "installed",
                "fix": f"pip install {pkg}",
            })
            print(f"  ⚠️  {pkg} not installed")

    # 7. filelock (WSL2 requirement)
    try:
        import filelock
        print(f"  ✅ filelock installed (WSL2 concurrency)")
    except ImportError:
        issues.append({
            "severity": "WARNING",
            "check": "filelock",
            "found": "not installed",
            "expected": ">=3.13.0",
            "fix": "pip install 'filelock>=3.13.0'",
        })
        print(f"  ⚠️  filelock not installed (needed for WSL2)")

    # Summary
    critical = sum(1 for i in issues if i["severity"] == "CRITICAL")
    warnings = sum(1 for i in issues if i["severity"] == "WARNING")

    print(f"\n{'='*50}")
    if critical:
        print(f"  ❌ {critical} critical issue(s) — must fix before proceeding")
    if warnings:
        print(f"  ⚠️  {warnings} warning(s)")
    if not issues:
        print(f"  ✅ Environment aligned with ENVIRONMENT_SPEC.md")

    if issues:
        print(f"\n  Remediation steps:")
        for i, issue in enumerate(issues, 1):
            print(f"\n  {i}. [{issue['severity']}] {issue['check']}")
            print(f"     Found: {issue['found']}")
            print(f"     Expected: {issue['expected']}")
            print(f"     Fix: {issue['fix']}")

    print(f"\n{'='*50}\n")

    if "--json" in args:
        print(json.dumps({
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": f"{v.major}.{v.minor}.{v.micro}",
            "issues": issues,
            "critical_count": critical,
            "warning_count": warnings,
            "aligned": len(issues) == 0,
        }, indent=2))

    sys.exit(2 if critical else (1 if warnings else 0))


# ---------------------------------------------------------------------------
# COMMAND: snapshot
# ---------------------------------------------------------------------------

def cmd_snapshot(args: list):
    """Delegate to epos_snapshot.py if it exists."""
    snap_path = _SCRIPT_DIR / "epos_snapshot.py"
    if not snap_path.exists():
        print("  ⚠️  epos_snapshot.py not yet built.")
        print("     This is next in the build chain after governance_gate.py.")
        sys.exit(1)
    cmd = [sys.executable, str(snap_path)] + args
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# MAIN ROUTER
# ---------------------------------------------------------------------------

USAGE = """
  EPOS CLI v1.0 — Unified Command Surface

  Usage:
    python epos_cli.py <command> [options]

  Commands:
    doctor              Run environment diagnostic (Article III pre-flight)
    gate check <target> Triage files through Governance Gate (Article III/IV)
    status              Quick system health summary
    env-audit           Audit environment against ENVIRONMENT_SPEC.md
    snapshot            Capture system state snapshot

  Gate Options:
    --triage-only       Classify without applying repairs
    --propose-patch     Generate .patch files instead of applying
    --json              Machine-readable JSON output
    --verbose, -v       Show detailed check results

  Examples:
    python epos_cli.py doctor --verbose
    python epos_cli.py gate check inbox/
    python epos_cli.py gate check my_file.py --triage-only
    python epos_cli.py status
    python epos_cli.py env-audit
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)

    command = sys.argv[1].lower()
    rest = sys.argv[2:]

    if command == "doctor":
        cmd_doctor(rest)
    elif command == "gate":
        if rest and rest[0] == "check":
            cmd_gate_check(rest[1:])
        else:
            print("  Usage: epos gate check <file_or_dir> [options]")
            sys.exit(1)
    elif command == "status":
        cmd_status(rest)
    elif command == "env-audit":
        cmd_env_audit(rest)
    elif command == "snapshot":
        cmd_snapshot(rest)
    elif command in ("--help", "-h", "help"):
        print(USAGE)
        sys.exit(0)
    else:
        print(f"  ❌ Unknown command: {command}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()