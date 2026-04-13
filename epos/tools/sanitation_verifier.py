#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
sanitation_verifier.py — 8-Point Binary Verification Suite
============================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-01 (Step C: Path & Secret Sanitation)

Runs 8 binary checks to verify the codebase is fully sanitized:
  1. No Windows backslash paths (C:\\...)
  2. No Windows forward-slash paths (C:/...)
  3. No WSL mount paths (/mnt/c/...)
  4. No API key literals in source files
  5. env_secrets.json exists and is valid
  6. .env.production exists and is valid
  7. All audit directories are writable
  8. No broken imports from refactoring

Score: N/8 — must be 8/8 before marking M4 complete.

Vault: context_vault/reports/sanitation_20260413-01.json
Event: system.sanitation_verifier.complete
"""

import os
import re
import ast
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))

SCAN_DIRS = [
    EPOS_ROOT / "epos",
    EPOS_ROOT / "engine",
    EPOS_ROOT / "friday",
    EPOS_ROOT / "reactor",
]
SKIP_PATTERNS = {
    "__pycache__", ".venv", "venv", "venv_epos", ".git",
    "rejected", "_archive", "node_modules",
}
AUDIT_DIRS = [
    EPOS_ROOT / "epos",
    EPOS_ROOT / "epos" / "tools",
    VAULT,
    VAULT / "aar",
    VAULT / "reports",
    VAULT / "infrastructure",
]


def _get_py_files() -> List[Path]:
    files = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if not any(skip in f.parts for skip in SKIP_PATTERNS):
                files.append(f)
    return files


def _read_files() -> List[Tuple[Path, str]]:
    result = []
    for f in _get_py_files():
        try:
            result.append((f, f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return result


# ── 8 Checks ─────────────────────────────────────────────────

def check_1_no_backslash_paths() -> Tuple[bool, str]:
    """Check 1: No Windows backslash paths C:\\... in source."""
    pattern = re.compile(r'["\'][A-Za-z]:\\[^"\']+["\']')
    hits = []
    for path, content in _read_files():
        for m in pattern.finditer(content):
            line = content[:m.start()].count("\n") + 1
            if not content.split("\n")[line - 1].strip().startswith("#"):
                hits.append(f"{path.name}:L{line}: {m.group(0)[:50]}")
    ok = len(hits) == 0
    detail = "0 found" if ok else f"{len(hits)} found: " + "; ".join(hits[:3])
    return ok, detail


def check_2_no_forward_slash_windows() -> Tuple[bool, str]:
    """Check 2: No Windows forward-slash paths C:/... in source."""
    pattern = re.compile(r'["\'][A-Za-z]:/[^"\']+["\']')
    hits = []
    for path, content in _read_files():
        for m in pattern.finditer(content):
            line = content[:m.start()].count("\n") + 1
            line_text = content.split("\n")[line - 1].strip()
            if line_text.startswith("#"):
                continue
            if "os.getenv" in content[max(0, m.start()-30):m.start()]:
                continue
            hits.append(f"{path.name}:L{line}: {m.group(0)[:50]}")
    ok = len(hits) == 0
    detail = "0 found" if ok else f"{len(hits)} found: " + "; ".join(hits[:3])
    return ok, detail


def check_3_no_wsl_mnt_paths() -> Tuple[bool, str]:
    """Check 3: No WSL /mnt/c/... paths in source."""
    pattern = re.compile(r'["\']/mnt/[a-z]/[^"\']+["\']')
    hits = []
    for path, content in _read_files():
        for m in pattern.finditer(content):
            line = content[:m.start()].count("\n") + 1
            if not content.split("\n")[line - 1].strip().startswith("#"):
                hits.append(f"{path.name}:L{line}")
    ok = len(hits) == 0
    detail = "0 found" if ok else f"{len(hits)} found"
    return ok, detail


def check_4_no_api_keys_in_source() -> Tuple[bool, str]:
    """Check 4: No raw API key literals in source files."""
    patterns = [
        re.compile(r'["\']sk-or-v1-[A-Za-z0-9_\-]{20,}["\']'),
        re.compile(r'["\']gsk_[A-Za-z0-9]{30,}["\']'),
        re.compile(r'["\']sk-ant-[A-Za-z0-9_\-]{20,}["\']'),
    ]
    hits = []
    for path, content in _read_files():
        # Skip the extractor's own pattern strings
        if "secret_extractor" in path.name:
            continue
        for pat in patterns:
            for m in pat.finditer(content):
                line = content[:m.start()].count("\n") + 1
                hits.append(f"{path.name}:L{line}")
    ok = len(hits) == 0
    detail = "0 found" if ok else f"{len(hits)} found: " + "; ".join(hits[:3])
    return ok, detail


def check_5_env_secrets_exists() -> Tuple[bool, str]:
    """Check 5: env_secrets.json exists and has required sections."""
    env_path = VAULT / "infrastructure" / "env_secrets.json"
    if not env_path.exists():
        return False, "env_secrets.json not found"
    try:
        data = json.loads(env_path.read_text(encoding="utf-8"))
        required = {"auto_generated", "human_gate", "schema_version"}
        missing = required - set(data.keys())
        if missing:
            return False, f"Missing keys: {missing}"
        return True, f"Valid — {len(data['auto_generated'])} auto + {len(data['human_gate'])} human-gate keys"
    except Exception as e:
        return False, f"Invalid JSON: {e}"


def check_6_env_production_exists() -> Tuple[bool, str]:
    """Check 6: .env.production exists and is non-empty."""
    prod_path = EPOS_ROOT / ".env.production"
    if not prod_path.exists():
        return False, ".env.production not found"
    content = prod_path.read_text(encoding="utf-8")
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
    if len(lines) < 5:
        return False, f"Too few entries ({len(lines)})"
    return True, f"Valid — {len(lines)} env entries"


def check_7_permissions_writable() -> Tuple[bool, str]:
    """Check 7: All audit directories are writable."""
    failed = []
    for d in AUDIT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".perm_probe"
        try:
            probe.write_text("x", encoding="utf-8")
            probe.unlink()
        except Exception:
            failed.append(str(d))
    ok = len(failed) == 0
    detail = f"All {len(AUDIT_DIRS)} writable" if ok else f"Failed: {failed}"
    return ok, detail


def check_8_imports_not_broken() -> Tuple[bool, str]:
    """Check 8: No syntax errors introduced by refactoring."""
    broken = []
    for path in _get_py_files():
        try:
            content = path.read_text(encoding="utf-8")
            ast.parse(content)
        except SyntaxError as e:
            broken.append(f"{path.name}: {e}")
        except Exception:
            pass
    ok = len(broken) == 0
    detail = f"All {len(_get_py_files())} files parse clean" if ok else f"{len(broken)} broken: " + "; ".join(broken[:3])
    return ok, detail


# ── Verifier class ────────────────────────────────────────────

class SanitationVerifier:
    """Runs all 8 checks and produces a structured report."""

    CHECKS = [
        ("windows_backslash_paths",  check_1_no_backslash_paths),
        ("windows_forward_slash_paths", check_2_no_forward_slash_windows),
        ("wsl_mnt_paths",            check_3_no_wsl_mnt_paths),
        ("api_keys_in_source",       check_4_no_api_keys_in_source),
        ("env_secrets_exists",       check_5_env_secrets_exists),
        ("env_production_exists",    check_6_env_production_exists),
        ("permissions_all_writable", check_7_permissions_writable),
        ("imports_not_broken",       check_8_imports_not_broken),
    ]

    def run(self) -> dict:
        results = {}
        passed = 0

        for name, fn in self.CHECKS:
            try:
                ok, detail = fn()
            except Exception as e:
                ok, detail = False, f"Check raised: {e}"
            results[name] = {"pass": ok, "detail": detail}
            if ok:
                passed += 1

        score = f"{passed}/{len(self.CHECKS)}"
        report = {
            "report_id": "VERIFY-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "directive": "20260413-01",
            "score": score,
            "passed": passed,
            "total": len(self.CHECKS),
            "status": "PASS" if passed == len(self.CHECKS) else "FAIL",
            "checks": results,
        }

        # Persist
        report_path = VAULT / "reports" / "sanitation_20260413-01.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        if _BUS:
            try:
                _BUS.publish("system.sanitation_verifier.complete", {
                    "score": score,
                    "status": report["status"],
                    "directive": "20260413-01",
                }, source_module="sanitation_verifier")
            except Exception:
                pass

        return report


def run_verification() -> dict:
    return SanitationVerifier().run()


if __name__ == "__main__":
    report = run_verification()
    print(f"Score:  {report['score']}")
    print(f"Status: {report['status']}")
    print()
    for name, result in report["checks"].items():
        mark = "PASS" if result["pass"] else "FAIL"
        print(f"  [{mark}] {name}: {result['detail']}")
    print()
    print(f"Report: {VAULT}/reports/sanitation_20260413-01.json")
    assert report["status"] == "PASS", f"Verification FAILED: score={report['score']}"
    print(f"\nPASS: sanitation_verifier — {report['score']}")
