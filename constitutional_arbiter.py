#!/usr/bin/env python3
"""
constitutional_arbiter.py — EPOS Constitutional Compliance Checker
===================================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles II, III, IV, XIV
Mission ID: EPOS Core Heal — Module 6 of 9
File Location: C:/Users/Jamie/workspace/epos_mcp/constitutional_arbiter.py

Single responsibility: Audit Python files for constitutional compliance.
Checks path discipline, file headers, version gates, import hygiene,
and governance watermarks. Returns structured verdicts.

Dependencies: path_utils (Module 1), roles (Module 3), epos_intelligence (Module 4)
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

from path_utils import get_epos_root, get_logs_dir
from roles import AgentId
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_event


# ── Violation Codes ──────────────────────────────────────────────

@dataclass
class Violation:
    """A single constitutional violation found during audit."""
    code: str
    title: str
    article: str
    severity: str  # "error", "warning", "info"
    file_path: str
    line: Optional[int] = None
    detail: Optional[str] = None


# Violation definitions
VIOLATION_REGISTRY: Dict[str, Dict[str, str]] = {
    "ERR-PATH-001": {
        "title": "Relative path used instead of absolute",
        "article": "II.1",
        "severity": "error",
    },
    "ERR-PATH-002": {
        "title": "Unix-style path on Windows codebase",
        "article": "II.1",
        "severity": "error",
    },
    "ERR-HEADER-001": {
        "title": "Missing constitutional file header",
        "article": "XIV.2",
        "severity": "warning",
    },
    "ERR-IMPORT-001": {
        "title": "Import-time side effect (function call at module level)",
        "article": "II",
        "severity": "error",
    },
    "ERR-IMPORT-002": {
        "title": "fcntl imported without Windows guard",
        "article": "II",
        "severity": "error",
    },
    "ERR-VERSION-001": {
        "title": "Overly strict version gate (blocks compatible Python)",
        "article": "II.3",
        "severity": "warning",
    },
    "ERR-SHADOW-001": {
        "title": "Built-in name shadowed by class/function definition",
        "article": "II",
        "severity": "warning",
    },
    "ERR-DOCSTRING-001": {
        "title": "Backslash in docstring causes unicode escape error",
        "article": "II",
        "severity": "error",
    },
    "ERR-DUPLICATE-001": {
        "title": "File exists at both root and engine/ (diverged duplicate)",
        "article": "XIV",
        "severity": "warning",
    },
}

# Python builtins that should not be shadowed
PYTHON_BUILTINS = {
    "TimeoutError", "ValueError", "TypeError", "KeyError", "IndexError",
    "RuntimeError", "OSError", "IOError", "FileNotFoundError",
    "ConnectionError", "PermissionError", "StopIteration",
    "list", "dict", "set", "tuple", "str", "int", "float", "bool",
    "type", "object", "print", "input", "open", "range", "map", "filter",
}


# ── Audit Engine ─────────────────────────────────────────────────

def audit_file(filepath: Path) -> Dict[str, Any]:
    """
    Audit a single Python file for constitutional compliance.

    Args:
        filepath: Absolute path to a .py file

    Returns:
        {
            "file": str,
            "status": "compliant" | "violations_found",
            "violations": [Violation as dict],
            "checks_run": int,
            "timestamp": str,
        }
    """
    filepath = Path(filepath).resolve()
    rel_path = str(filepath)
    try:
        rel_path = str(filepath.relative_to(get_epos_root()))
    except ValueError:
        pass

    violations: List[Violation] = []

    if not filepath.exists():
        return {
            "file": rel_path,
            "status": "error",
            "violations": [{"code": "FILE_NOT_FOUND", "detail": str(filepath)}],
            "checks_run": 0,
            "timestamp": datetime.now().isoformat(),
        }

    if filepath.suffix != ".py":
        return {
            "file": rel_path,
            "status": "skipped",
            "violations": [],
            "checks_run": 0,
            "timestamp": datetime.now().isoformat(),
        }

    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return {
            "file": rel_path,
            "status": "error",
            "violations": [{"code": "READ_ERROR", "detail": str(e)}],
            "checks_run": 0,
            "timestamp": datetime.now().isoformat(),
        }

    lines = source.splitlines()
    checks_run = 0

    # CHECK 1: File header / watermark
    checks_run += 1
    _check_header(source, rel_path, violations)

    # CHECK 2: Docstring unicode escape
    checks_run += 1
    _check_docstring_escapes(lines, rel_path, violations)

    # CHECK 3: Import hygiene
    checks_run += 1
    _check_imports(source, lines, rel_path, violations)

    # CHECK 4: Path discipline
    checks_run += 1
    _check_paths(lines, rel_path, violations)

    # CHECK 5: Built-in shadowing
    checks_run += 1
    _check_builtin_shadow(source, rel_path, violations)

    # CHECK 6: Version gates
    checks_run += 1
    _check_version_gates(lines, rel_path, violations)

    result = {
        "file": rel_path,
        "status": "compliant" if not violations else "violations_found",
        "violations": [asdict(v) for v in violations],
        "checks_run": checks_run,
        "timestamp": datetime.now().isoformat(),
    }

    return result


def _check_header(source: str, rel_path: str, violations: List[Violation]):
    """Check for constitutional file header or watermark."""
    first_500 = source[:500].lower()
    has_header = any(marker in first_500 for marker in [
        "file location:", "file:", "constitutional authority:",
        "epos_constitution", "article",
    ])
    if not has_header:
        violations.append(Violation(
            code="ERR-HEADER-001",
            title=VIOLATION_REGISTRY["ERR-HEADER-001"]["title"],
            article="XIV.2",
            severity="warning",
            file_path=rel_path,
            detail="No constitutional header found in first 500 chars",
        ))


def _check_docstring_escapes(lines: List[str], rel_path: str, violations: List[Violation]):
    """Check for backslash sequences in docstrings that cause SyntaxError."""
    in_docstring = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            in_docstring = not in_docstring
        if in_docstring and re.search(r'C:\\U|C:\\u', line):
            violations.append(Violation(
                code="ERR-DOCSTRING-001",
                title=VIOLATION_REGISTRY["ERR-DOCSTRING-001"]["title"],
                article="II",
                severity="error",
                file_path=rel_path,
                line=i,
                detail=f"Backslash in docstring: {line.strip()[:80]}",
            ))


def _check_imports(source: str, lines: List[str], rel_path: str, violations: List[Violation]):
    """Check for import-time side effects and platform-unsafe imports."""
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Import-time execution: EPOSDoctor().run() etc on import line
        if re.match(r'^from\s+\S+\s+import\s+\S+.*;\s*\S+\(\)', stripped):
            violations.append(Violation(
                code="ERR-IMPORT-001",
                title=VIOLATION_REGISTRY["ERR-IMPORT-001"]["title"],
                article="II",
                severity="error",
                file_path=rel_path,
                line=i,
                detail=f"Import-time execution: {stripped[:80]}",
            ))

        # fcntl without guard
        if stripped == "import fcntl":
            violations.append(Violation(
                code="ERR-IMPORT-002",
                title=VIOLATION_REGISTRY["ERR-IMPORT-002"]["title"],
                article="II",
                severity="error",
                file_path=rel_path,
                line=i,
                detail="fcntl is Unix-only; use try/except ImportError guard",
            ))


def _check_paths(lines: List[str], rel_path: str, violations: List[Violation]):
    """Check for hardcoded Unix paths on Windows codebase."""
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        # Detect /mnt/c/ or /home/ paths in string literals
        if re.search(r'''['"]\/mnt\/c\/|['"]\/home\/''', stripped):
            violations.append(Violation(
                code="ERR-PATH-002",
                title=VIOLATION_REGISTRY["ERR-PATH-002"]["title"],
                article="II.1",
                severity="error",
                file_path=rel_path,
                line=i,
                detail=f"Unix path in string: {stripped[:80]}",
            ))


def _check_builtin_shadow(source: str, rel_path: str, violations: List[Violation]):
    """Check if any class or function shadows a Python builtin."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        name = None
        if isinstance(node, ast.ClassDef):
            name = node.name
        elif isinstance(node, ast.FunctionDef):
            name = node.name

        if name and name in PYTHON_BUILTINS:
            violations.append(Violation(
                code="ERR-SHADOW-001",
                title=VIOLATION_REGISTRY["ERR-SHADOW-001"]["title"],
                article="II",
                severity="warning",
                file_path=rel_path,
                line=node.lineno,
                detail=f"'{name}' shadows Python builtin",
            ))


def _check_version_gates(lines: List[str], rel_path: str, violations: List[Violation]):
    """Check for overly strict Python version gates."""
    for i, line in enumerate(lines, 1):
        # Detect sys.version_info[:2] < (3, 11) or == (3, 11)
        if re.search(r'version_info.*==\s*\(3,\s*11\)', line):
            violations.append(Violation(
                code="ERR-VERSION-001",
                title=VIOLATION_REGISTRY["ERR-VERSION-001"]["title"],
                article="II.3",
                severity="warning",
                file_path=rel_path,
                line=i,
                detail="Version gate should use >= not ==",
            ))


# ── Batch Audit ──────────────────────────────────────────────────

def audit_directory(
    directory: Path = None,
    recursive: bool = True,
) -> Dict[str, Any]:
    """
    Audit all Python files in a directory.

    Args:
        directory: Directory to scan (defaults to EPOS_ROOT)
        recursive: Whether to recurse into subdirectories

    Returns:
        {
            "directory": str,
            "total_files": int,
            "compliant": int,
            "violations_found": int,
            "total_violations": int,
            "compliance_score": float,
            "results": [audit_file results],
        }
    """
    if directory is None:
        directory = get_epos_root()
    directory = Path(directory).resolve()

    # Collect files from project directories only (skip venvs and vendor dirs)
    SKIP_PREFIXES = {".", "venv", "node_modules", "dist", "__pycache__",
                     "CLI-Anything", "epos_console.egg-info", "rejected"}

    def _should_skip(name: str) -> bool:
        name_lower = name.lower()
        return (name_lower.startswith(".")
                or "venv" in name_lower
                or name in SKIP_PREFIXES)

    py_files = []
    if recursive:
        # Walk manually to prune skipped dirs early
        import os as _os
        for root_str, dirs, files in _os.walk(str(directory)):
            # Prune dirs in-place so os.walk doesn't descend
            dirs[:] = [d for d in dirs if not _should_skip(d)]
            for fname in sorted(files):
                if fname.endswith(".py"):
                    py_files.append(Path(root_str) / fname)
    else:
        py_files = sorted(directory.glob("*.py"))

    results = []
    compliant = 0
    total_violations = 0

    for f in py_files:
        r = audit_file(f)
        results.append(r)
        if r["status"] == "compliant":
            compliant += 1
        total_violations += len(r.get("violations", []))

    total = len(results)
    score = round(compliant / total * 100, 1) if total > 0 else 100.0

    summary = {
        "directory": str(directory),
        "total_files": total,
        "compliant": compliant,
        "violations_found": total - compliant,
        "total_violations": total_violations,
        "compliance_score": score,
        "timestamp": datetime.now().isoformat(),
    }

    # Log to BI
    record_event({
        "event_type": "governance.audit",
        "agent_id": AgentId.ALPHA.value,
        **{k: v for k, v in summary.items() if k != "timestamp"},
    })

    summary["results"] = results
    return summary


def audit_engine() -> Dict[str, Any]:
    """Audit the engine/ directory specifically."""
    return audit_directory(get_epos_root() / "engine")


# ── Report Writer ────────────────────────────────────────────────

def write_audit_report(summary: Dict[str, Any], output_path: Path = None) -> Path:
    """Write audit results to a JSON report file."""
    if output_path is None:
        logs = get_logs_dir() / "arbiter"
        logs.mkdir(parents=True, exist_ok=True)
        output_path = logs / f"audit_{datetime.now():%Y%m%d_%H%M%S}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="EPOS Constitutional Arbiter v2.0")
    parser.add_argument("path", nargs="?", help="File or directory to audit (default: EPOS_ROOT)")
    parser.add_argument("--engine", action="store_true", help="Audit engine/ only")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--report", action="store_true", help="Save report to logs")
    args = parser.parse_args()

    if args.engine:
        result = audit_engine()
    elif args.path:
        target = Path(args.path).resolve()
        if target.is_file():
            result = audit_file(target)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                status_icon = "PASS" if result["status"] == "compliant" else "FAIL"
                print(f"  [{status_icon}] {result['file']} ({result['checks_run']} checks)")
                for v in result.get("violations", []):
                    print(f"    {v['code']}: {v['title']}")
                    if v.get("line"):
                        print(f"      Line {v['line']}: {v.get('detail', '')}")
            sys.exit(0)
        else:
            result = audit_directory(target)
    else:
        result = audit_directory()

    if args.json:
        # Don't include individual results in JSON dump (too large)
        out = {k: v for k, v in result.items() if k != "results"}
        print(json.dumps(out, indent=2))
    else:
        print(f"\nEPOS Constitutional Audit")
        print("=" * 50)
        print(f"  Directory: {result['directory']}")
        print(f"  Files scanned: {result['total_files']}")
        print(f"  Compliant: {result['compliant']}")
        print(f"  With violations: {result['violations_found']}")
        print(f"  Total violations: {result['total_violations']}")
        print(f"  Compliance score: {result['compliance_score']}%")

        # Show top violations
        if result["total_violations"] > 0:
            print(f"\n  Top violations:")
            from collections import Counter
            codes = Counter()
            for r in result.get("results", []):
                for v in r.get("violations", []):
                    codes[v["code"]] += 1
            for code, count in codes.most_common(10):
                title = VIOLATION_REGISTRY.get(code, {}).get("title", code)
                print(f"    {code}: {title} ({count}x)")

    if args.report:
        report_path = write_audit_report(result)
        print(f"\n  Report saved: {report_path}")

    # Self-test assertion
    if not args.path and not args.engine:
        assert result["total_files"] > 0, "No files scanned"
        print(f"\n  Self-test: PASS ({result['total_files']} files audited)")
