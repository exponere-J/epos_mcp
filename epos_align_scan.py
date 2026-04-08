# # File: C:\Users\Jamie\workspace\epos_mcp\epos_align_scan.py
# EPOS Alignment Scanner v1.0
# Pre-Mortem Imaginative Projection Engine
# Authority: EPOS Constitution v3.1, Article I (Pre-Mortem Mandate)
#
# PURPOSE:
#   Point this at any component, module, file, or directory.
#   It performs full pre-mortem imaginative projection BEFORE code runs:
#     - Extracts all imports, paths, env vars, function calls
#     - Cross-references them against the live environment and other components
#     - Projects failure scenarios (happy path + 5 failure modes)
#     - Outputs an alignment report with PROMOTE / WARN / BLOCK verdicts
#
# USAGE:
#   python epos_align_scan.py <target>              # scan one file or dir
#   python epos_align_scan.py <target> --deep       # follow imports recursively
#   python epos_align_scan.py <target> --compare <other_target>  # cross-compare two components
#   python epos_align_scan.py <target> --report     # save report to file
#   python epos_align_scan.py . --deep              # scan entire codebase
#
# OUTPUT:
#   Terminal: color-coded alignment report
#   File (--report): epos_align_report_<timestamp>.md

import sys
import os
import ast
import re
import json
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

EPOS_ROOT_CANDIDATES = [
    Path("C:/Users/Jamie/workspace/epos_mcp"),
    Path("/mnt/c/Users/Jamie/workspace/epos_mcp"),
    Path.cwd(),
]

REQUIRED_ENV_VARS = ["EPOS_ROOT", "AGENT_ZERO_PATH", "WORKSPACE_ROOT"]

CONSTITUTIONAL_PATTERNS = {
    "no_silent_failure": {
        "pattern": r"except\s*:",
        "verdict": "WARN",
        "message": "Bare except clause — silent failure risk. Catch specific exceptions.",
    },
    "shell_in_python": {
        "pattern": r"^\s*(cat|ls|rm|cp|mv|mkdir|echo|grep)\s",
        "verdict": "BLOCK",
        "message": "Shell command found in Python file. Use subprocess or pathlib instead.",
    },
    "path_mixing": {
        "pattern": r'["\']C:\\\\.*?["\']',
        "verdict": "WARN",
        "message": "Windows-style hardcoded path. Use Path() and EPOS_ROOT env var.",
    },
    "missing_header": {
        "pattern": r"^# File:",
        "verdict": "WARN",
        "message": "Missing constitutional file header. Add: # File: <absolute_path>",
    },
    "logged_not_executed": {
        "pattern": r'(log|print|logger)\s*\(.*?(success|executed|completed|done).*?\)',
        "verdict": "WARN",
        "message": "Status logged but actual execution not verified. Separate logging from proof of execution.",
    },
    "dotenv_not_loaded": {
        "pattern": r"os\.environ\.get|os\.getenv",
        "verdict": "INFO",
        "message": "Env var access detected. Confirm load_dotenv() is called at entrypoint.",
    },
    "tilde_path": {
        "pattern": r'["\']~/.*?["\']',
        "verdict": "WARN",
        "message": "Tilde path used. Resolve with Path.home() for cross-shell compatibility.",
    },
    "subprocess_no_check": {
        "pattern": r"subprocess\.(run|call|Popen)\b(?!.*check=True)",
        "verdict": "WARN",
        "message": "subprocess call without check=True. Silent failure if command fails.",
    },
}

# Known EPOS component ports
KNOWN_PORTS = {
    "epos_api": 8001,
    "ollama": 11434,
    "agent_zero": 8080,
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ComponentProfile:
    """Pre-mortem profile extracted from a single file."""
    path: Path
    imports: list[str] = field(default_factory=list)
    stdlib_imports: list[str] = field(default_factory=list)
    third_party_imports: list[str] = field(default_factory=list)
    internal_imports: list[str] = field(default_factory=list)
    env_vars_accessed: list[str] = field(default_factory=list)
    hardcoded_paths: list[str] = field(default_factory=list)
    function_defs: list[str] = field(default_factory=list)
    class_defs: list[str] = field(default_factory=list)
    ports_referenced: list[int] = field(default_factory=list)
    constitutional_violations: list[dict] = field(default_factory=list)
    missing_packages: list[str] = field(default_factory=list)
    parse_error: Optional[str] = None


@dataclass
class AlignmentReport:
    """Final output of the imaginative projection pass."""
    target: str
    generated_at: str
    overall_verdict: str  # PROMOTE / WARN / BLOCK
    profiles: list[ComponentProfile] = field(default_factory=list)
    cross_component_conflicts: list[dict] = field(default_factory=list)
    failure_scenarios: list[dict] = field(default_factory=list)
    environment_check: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# STDLIB REFERENCE (abbreviated — covers 95% of common imports)
# ─────────────────────────────────────────────────────────────────────────────

STDLIB_MODULES = {
    "os", "sys", "re", "json", "ast", "io", "math", "time", "datetime",
    "pathlib", "shutil", "subprocess", "socket", "threading", "multiprocessing",
    "logging", "unittest", "typing", "dataclasses", "collections", "itertools",
    "functools", "contextlib", "abc", "copy", "enum", "hashlib", "hmac",
    "base64", "uuid", "random", "string", "struct", "traceback", "warnings",
    "weakref", "gc", "inspect", "importlib", "pkgutil", "platform", "signal",
    "tempfile", "glob", "fnmatch", "stat", "errno", "http", "urllib",
    "email", "html", "xml", "csv", "configparser", "argparse", "textwrap",
    "pprint", "decimal", "fractions", "statistics", "pickle", "shelve",
    "sqlite3", "zipfile", "tarfile", "gzip", "bz2", "lzma",
}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def classify_import(module_name: str) -> str:
    root = module_name.split(".")[0]
    if root in STDLIB_MODULES:
        return "stdlib"
    # Heuristic: if it looks like an internal EPOS module
    if root in {"epos", "governance", "engine", "agents", "context", "brand", "content"}:
        return "internal"
    return "third_party"


def extract_env_vars(source: str) -> list[str]:
    """Pull all os.environ.get / os.getenv / .env references."""
    found = []
    patterns = [
        r'os\.environ\.get\(["\'](\w+)["\']',
        r'os\.getenv\(["\'](\w+)["\']',
        r'os\.environ\[["\'](\w+)["\']\]',
        r'getenv\(["\'](\w+)["\']',
    ]
    for p in patterns:
        found.extend(re.findall(p, source))
    return list(set(found))


def extract_hardcoded_paths(source: str) -> list[str]:
    """Find hardcoded path strings."""
    found = []
    patterns = [
        r'["\']([C-Z]:\\\\[^"\']+)["\']',          # Windows backslash
        r'["\']([C-Z]:/[^"\']+)["\']',               # Windows forward slash
        r'["\'](/c/[^"\']+)["\']',                   # Git Bash style
        r'["\'](~/[^"\']+)["\']',                    # Tilde paths
        r'["\'](/mnt/[^"\']+)["\']',                 # WSL mount paths
    ]
    for p in patterns:
        found.extend(re.findall(p, source))
    return list(set(found))


def extract_ports(source: str) -> list[int]:
    """Find port numbers referenced in source."""
    ports = []
    for match in re.finditer(r'\b(8001|8080|8000|11434|5432|6379|3000|5000)\b', source):
        ports.append(int(match.group(1)))
    return list(set(ports))


def check_constitutional_patterns(source: str, filepath: Path) -> list[dict]:
    """Run all constitutional pattern checks against source lines."""
    violations = []
    lines = source.splitlines()

    # Header check (whole file)
    if not source.strip().startswith("# File:"):
        violations.append({
            "rule": "missing_header",
            "verdict": "WARN",
            "line": 1,
            "message": CONSTITUTIONAL_PATTERNS["missing_header"]["message"],
        })

    for i, line in enumerate(lines, start=1):
        for rule_name, rule in CONSTITUTIONAL_PATTERNS.items():
            if rule_name == "missing_header":
                continue
            if re.search(rule["pattern"], line):
                violations.append({
                    "rule": rule_name,
                    "verdict": rule["verdict"],
                    "line": i,
                    "snippet": line.strip()[:80],
                    "message": rule["message"],
                })

    return violations


def profile_file(filepath: Path) -> ComponentProfile:
    """Full pre-mortem profile of a single Python file."""
    profile = ComponentProfile(path=filepath)

    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        profile.parse_error = f"Read error: {e}"
        return profile

    # AST parse for imports, functions, classes
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        profile.imports.append(module)
                        classification = classify_import(module)
                        if classification == "stdlib":
                            profile.stdlib_imports.append(module)
                        elif classification == "internal":
                            profile.internal_imports.append(module)
                        else:
                            profile.third_party_imports.append(module)
                else:
                    module = node.module or ""
                    profile.imports.append(module)
                    classification = classify_import(module)
                    if classification == "stdlib":
                        profile.stdlib_imports.append(module)
                    elif classification == "internal":
                        profile.internal_imports.append(module)
                    else:
                        profile.third_party_imports.append(module)

            elif isinstance(node, ast.FunctionDef):
                profile.function_defs.append(node.name)

            elif isinstance(node, ast.ClassDef):
                profile.class_defs.append(node.name)

    except SyntaxError as e:
        profile.parse_error = f"SyntaxError at line {e.lineno}: {e.msg}"

    # Regex-based extractions (work even with syntax errors)
    profile.env_vars_accessed = extract_env_vars(source)
    profile.hardcoded_paths = extract_hardcoded_paths(source)
    profile.ports_referenced = extract_ports(source)
    profile.constitutional_violations = check_constitutional_patterns(source, filepath)

    # Check if third-party packages are installed — use find_spec, NOT __import__.
    # __import__ executes module-level code (file handlers, network calls, etc.)
    # which causes crashes on misconfigured modules. find_spec only checks existence.
    import importlib.util
    for pkg in set(profile.third_party_imports):
        root_pkg = pkg.split(".")[0]
        if root_pkg and root_pkg not in STDLIB_MODULES:
            try:
                spec = importlib.util.find_spec(root_pkg)
                if spec is None:
                    profile.missing_packages.append(root_pkg)
            except (ModuleNotFoundError, ValueError):
                profile.missing_packages.append(root_pkg)

    return profile


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-COMPONENT CONFLICT DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_cross_conflicts(profiles: list[ComponentProfile]) -> list[dict]:
    """
    The imaginative projection step:
    Simulate how components interact and where they will collide.
    """
    conflicts = []

    # Port collision check
    port_owners: dict[int, list[str]] = {}
    for p in profiles:
        for port in p.ports_referenced:
            port_owners.setdefault(port, []).append(str(p.path.name))
    for port, owners in port_owners.items():
        if len(owners) > 1:
            conflicts.append({
                "type": "PORT_COLLISION",
                "severity": "HIGH",
                "detail": f"Port {port} referenced in multiple components: {', '.join(owners)}",
                "scenario": f"If both components start simultaneously, port {port} binding will fail for the second starter.",
                "fix": "Assign unique ports per component in ENVIRONMENT_SPEC.md and .env",
            })

    # Missing package that another component depends on
    all_missing = {}
    for p in profiles:
        for pkg in p.missing_packages:
            all_missing.setdefault(pkg, []).append(str(p.path.name))
    for pkg, users in all_missing.items():
        conflicts.append({
            "type": "MISSING_DEPENDENCY",
            "severity": "CRITICAL",
            "detail": f"Package '{pkg}' not installed but required by: {', '.join(users)}",
            "scenario": f"At runtime, any component importing '{pkg}' will crash with ImportError before execution begins.",
            "fix": f"Run: pip install {pkg}  (then pin to requirements.txt)",
        })

    # Env var referenced but likely not loaded
    dotenv_loaded = False
    for p in profiles:
        source_text = ""
        try:
            source_text = p.path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
        if "load_dotenv" in source_text:
            dotenv_loaded = True
            break

    if not dotenv_loaded:
        all_env_vars = set()
        for p in profiles:
            all_env_vars.update(p.env_vars_accessed)
        if all_env_vars:
            conflicts.append({
                "type": "DOTENV_NOT_LOADED",
                "severity": "HIGH",
                "detail": f"Env vars accessed ({', '.join(sorted(all_env_vars))}) but load_dotenv() not found in any scanned file.",
                "scenario": "All os.environ.get() calls return None. Config silently uses defaults or crashes on None access.",
                "fix": "Add from dotenv import load_dotenv; load_dotenv() at the top of every entrypoint.",
            })

    # Internal import that doesn't exist on disk
    all_internal = {}
    for p in profiles:
        for mod in p.internal_imports:
            all_internal.setdefault(mod, []).append(str(p.path.name))

    # Hardcoded path references across multiple files (potential inconsistency)
    all_paths: dict[str, list[str]] = {}
    for p in profiles:
        for hp in p.hardcoded_paths:
            all_paths.setdefault(hp, []).append(str(p.path.name))

    path_roots = {}
    for hp in all_paths:
        # Normalize to root style
        normalized = hp.replace("\\", "/").lower()
        if normalized.startswith("c:/"):
            path_roots.setdefault("windows_c_slash", []).append(hp)
        elif normalized.startswith("/c/"):
            path_roots.setdefault("gitbash_c_slash", []).append(hp)
        elif normalized.startswith("/mnt/c"):
            path_roots.setdefault("wsl_mnt", []).append(hp)

    if len(path_roots) > 1:
        conflicts.append({
            "type": "PATH_STYLE_MIXING",
            "severity": "HIGH",
            "detail": f"Multiple path styles detected across components: {list(path_roots.keys())}",
            "scenario": "Paths that work in Git Bash will fail in PowerShell and vice versa. Silent failures when file open/write uses wrong style.",
            "fix": "Adopt one canonical style. Recommendation: use Path() objects everywhere, resolve at runtime from EPOS_ROOT env var.",
        })

    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# IMAGINATIVE FAILURE SCENARIO GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_failure_scenarios(profiles: list[ComponentProfile], conflicts: list[dict]) -> list[dict]:
    """
    For each BLOCK or CRITICAL conflict, project a 3-act failure movie:
    1. What the user expects
    2. What actually happens
    3. How it surfaces (or doesn't)
    """
    scenarios = []

    # Scenario: missing dependency
    for c in conflicts:
        if c["type"] == "MISSING_DEPENDENCY":
            pkg = c["detail"].split("'")[1]
            scenarios.append({
                "id": f"FS-IMPORT-{pkg.upper()}",
                "trigger": f"Component starts that imports '{pkg}'",
                "user_expectation": "Component initializes normally",
                "what_actually_happens": f"ImportError: No module named '{pkg}' raised immediately",
                "how_it_surfaces": "Traceback in terminal. If wrapped in try/except pass, silent death with no logging.",
                "downstream_effect": "All dependent operations skipped or silently fail. Audit trail may show 'started' but never 'completed'.",
                "prevention": c["fix"],
                "severity": "CRITICAL",
            })

        elif c["type"] == "PATH_STYLE_MIXING":
            scenarios.append({
                "id": "FS-PATH-MIXING",
                "trigger": "Component opened from PowerShell instead of Git Bash (or vice versa)",
                "user_expectation": "File reads/writes succeed normally",
                "what_actually_happens": "Path resolution fails silently. File not found errors or writes to wrong location.",
                "how_it_surfaces": "No error unless explicit path validation exists. Logs may write to unexpected directories.",
                "downstream_effect": "Audit trail disappears. Config changes don't persist. Doctor pre-flight may pass but runtime fails.",
                "prevention": c["fix"],
                "severity": "HIGH",
            })

        elif c["type"] == "DOTENV_NOT_LOADED":
            scenarios.append({
                "id": "FS-DOTENV-SILENT",
                "trigger": ".env updated with new EPOS_ROOT or AGENT_ZERO_PATH value",
                "user_expectation": "Component picks up new config on next run",
                "what_actually_happens": "os.environ.get() returns None or stale system env value",
                "how_it_surfaces": "Component silently uses wrong path or None. No error unless None is dereferenced.",
                "downstream_effect": "Config changes appear to work (no crash) but have zero effect. Debugging takes 30+ min.",
                "prevention": "Add load_dotenv() as first call in every entrypoint. Never assume env vars are loaded.",
                "severity": "HIGH",
            })

        elif c["type"] == "PORT_COLLISION":
            scenarios.append({
                "id": f"FS-PORT-{c['detail'].split('Port ')[1].split(' ')[0]}",
                "trigger": "Two components started in sequence (e.g., startup script or orchestrator)",
                "user_expectation": "Both services start and respond on their ports",
                "what_actually_happens": "Second service fails with 'Address already in use'",
                "how_it_surfaces": "OSError in terminal. If caught generically, service silently doesn't start.",
                "downstream_effect": "Orchestrator thinks both services are up. Health checks may lie if they don't test the port.",
                "prevention": c["fix"],
                "severity": "HIGH",
            })

    # Universal scenarios (always generated)
    scenarios.append({
        "id": "FS-HAPPY-PATH",
        "trigger": "Normal execution from correct shell, all deps installed, .env loaded",
        "user_expectation": "All components initialize, health checks pass, operations execute",
        "what_actually_happens": "Same as expectation — this is the golden path",
        "how_it_surfaces": "Green output from epos_doctor.py, /health returns ok=true",
        "downstream_effect": "Operations execute, audit trail written, Context Vault updated",
        "prevention": "N/A — this is the target state",
        "severity": "NONE",
    })

    scenarios.append({
        "id": "FS-LOGGED-NOT-EXECUTED",
        "trigger": "Operation logged as 'success' but actual execution step (file write, API call, subprocess) fails",
        "user_expectation": "Task marked complete in audit trail",
        "what_actually_happens": "Log says success. Actual artifact (file, response) does not exist.",
        "how_it_surfaces": "Only discovered when downstream component tries to consume the artifact.",
        "downstream_effect": "Cascading silent failures. 3+ operations may report success with nothing actually done.",
        "prevention": "ALWAYS verify the artifact exists after the operation. Log only after proof. Never log then act.",
        "severity": "CRITICAL",
    })

    return scenarios


# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT CHECK
# ─────────────────────────────────────────────────────────────────────────────

def run_environment_check() -> dict:
    """Live environment validation — mirrors epos_doctor logic."""
    results = {}

    # Python version
    ver = sys.version_info
    results["python"] = {
        "actual": f"{ver.major}.{ver.minor}.{ver.micro}",
        "required": "3.11+",
        "aligned": ver.major == 3 and ver.minor >= 11,
    }

    # EPOS root
    epos_root = os.environ.get("EPOS_ROOT", "")
    if not epos_root:
        for candidate in EPOS_ROOT_CANDIDATES:
            if candidate.exists():
                epos_root = str(candidate)
                break
    results["epos_root"] = {
        "actual": epos_root,
        "exists": Path(epos_root).exists() if epos_root else False,
        "source": "EPOS_ROOT env var" if os.environ.get("EPOS_ROOT") else "auto-detected",
    }

    # Key env vars
    env_check = {}
    for var in REQUIRED_ENV_VARS:
        val = os.environ.get(var, "")
        env_check[var] = {"set": bool(val), "value_preview": val[:30] + "..." if len(val) > 30 else val}
    results["env_vars"] = env_check

    # Port availability
    port_status = {}
    for name, port in KNOWN_PORTS.items():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", port))
                port_status[name] = {"port": port, "in_use": result == 0}
        except Exception:
            port_status[name] = {"port": port, "in_use": False, "error": True}
    results["ports"] = port_status

    # Shell detection
    shell = os.environ.get("SHELL", os.environ.get("ComSpec", "unknown"))
    results["shell"] = shell

    return results


# ─────────────────────────────────────────────────────────────────────────────
# VERDICT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_overall_verdict(profiles: list[ComponentProfile], conflicts: list[dict]) -> str:
    """PROMOTE / WARN / BLOCK based on severity of findings."""
    has_block = any(
        v["verdict"] == "BLOCK"
        for p in profiles
        for v in p.constitutional_violations
    )
    has_critical_conflict = any(c["severity"] == "CRITICAL" for c in conflicts)
    has_parse_error = any(p.parse_error for p in profiles)

    if has_block or has_critical_conflict or has_parse_error:
        return "BLOCK"

    has_warn = any(
        v["verdict"] == "WARN"
        for p in profiles
        for v in p.constitutional_violations
    )
    has_high_conflict = any(c["severity"] == "HIGH" for c in conflicts)

    if has_warn or has_high_conflict:
        return "WARN"

    return "PROMOTE"


# ─────────────────────────────────────────────────────────────────────────────
# REPORT RENDERER
# ─────────────────────────────────────────────────────────────────────────────

DARK_COLORS = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "red":     "\033[91m",
    "yellow":  "\033[93m",
    "green":   "\033[92m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "dim":     "\033[2m",
    "magenta": "\033[95m",
}

def c(text: str, color: str) -> str:
    return f"{DARK_COLORS.get(color, '')}{text}{DARK_COLORS['reset']}"


def verdict_color(v: str) -> str:
    if v == "BLOCK" or v == "CRITICAL":
        return "red"
    if v == "WARN" or v == "HIGH":
        return "yellow"
    if v == "PROMOTE" or v == "NONE":
        return "green"
    return "white"


def render_report(report: AlignmentReport, to_file: bool = False) -> str:
    lines = []
    W = 78

    def hr(char="═"):
        lines.append(c(char * W, "dim"))

    def section(title: str):
        lines.append("")
        lines.append(c(f"  {title}", "cyan"))
        lines.append(c("  " + "─" * (W - 4), "dim"))

    hr("═")
    lines.append(c(f"  EPOS ALIGNMENT SCAN — PRE-MORTEM PROJECTION REPORT", "bold"))
    lines.append(c(f"  Target  : {report.target}", "white"))
    lines.append(c(f"  Generated: {report.generated_at}", "dim"))
    verdict_str = f"  ▶ OVERALL VERDICT: {report.overall_verdict}"
    lines.append(c(verdict_str, verdict_color(report.overall_verdict)))
    hr("═")

    # ── Environment ──
    section("ENVIRONMENT ALIGNMENT")
    env = report.environment_check
    py = env.get("python", {})
    py_ok = py.get("aligned", False)
    lines.append(f"  Python   : {c(py.get('actual','?'), 'green' if py_ok else 'red')}  (required: 3.11+)")
    lines.append(f"  Shell    : {env.get('shell','?')}")

    root = env.get("epos_root", {})
    root_ok = root.get("exists", False)
    lines.append(f"  EPOS_ROOT: {c(root.get('actual', 'NOT SET'), 'green' if root_ok else 'red')}  [{root.get('source','')}]")

    lines.append("")
    lines.append(c("  Env Vars:", "white"))
    for var, info in env.get("env_vars", {}).items():
        status = c("✓ SET", "green") if info["set"] else c("✗ MISSING", "red")
        lines.append(f"    {var:25s} {status}")

    lines.append("")
    lines.append(c("  Ports:", "white"))
    for svc, info in env.get("ports", {}).items():
        state = c("● RUNNING", "green") if info.get("in_use") else c("○ not running", "dim")
        lines.append(f"    {svc:20s} :{info['port']}  {state}")

    # ── Component Profiles ──
    section(f"COMPONENT PROFILES  ({len(report.profiles)} file(s))")
    for p in report.profiles:
        rel = p.path.name
        lines.append("")
        lines.append(c(f"  ┌─ {rel}", "white"))

        if p.parse_error:
            lines.append(c(f"  │  ✗ PARSE ERROR: {p.parse_error}", "red"))
        else:
            lines.append(f"  │  Functions  : {', '.join(p.function_defs[:6]) or 'none'}")
            lines.append(f"  │  Classes    : {', '.join(p.class_defs[:4]) or 'none'}")
            if p.third_party_imports:
                lines.append(f"  │  3rd-party  : {', '.join(sorted(set(p.third_party_imports))[:8])}")
            if p.internal_imports:
                lines.append(f"  │  Internal   : {', '.join(sorted(set(p.internal_imports))[:6])}")
            if p.missing_packages:
                lines.append(c(f"  │  ✗ MISSING  : {', '.join(p.missing_packages)}", "red"))
            if p.env_vars_accessed:
                lines.append(f"  │  Env vars   : {', '.join(p.env_vars_accessed)}")
            if p.hardcoded_paths:
                lines.append(c(f"  │  ⚠ Hard paths: {len(p.hardcoded_paths)} found", "yellow"))
            if p.ports_referenced:
                lines.append(f"  │  Ports      : {p.ports_referenced}")

        if p.constitutional_violations:
            lines.append(c(f"  │  Constitutional violations: {len(p.constitutional_violations)}", "yellow"))
            for v in p.constitutional_violations[:5]:
                icon = c("✗", "red") if v["verdict"] == "BLOCK" else c("⚠", "yellow")
                line_ref = f"L{v.get('line','?')}"
                lines.append(c(f"  │    {icon} [{line_ref}] {v['rule']}: {v['message'][:60]}", "yellow"))
        else:
            lines.append(c("  │  ✓ No constitutional violations", "green"))

        lines.append(c("  └" + "─" * 60, "dim"))

    # ── Cross-Component Conflicts ──
    section(f"CROSS-COMPONENT CONFLICT ANALYSIS  ({len(report.cross_component_conflicts)} conflict(s))")
    if not report.cross_component_conflicts:
        lines.append(c("  ✓ No cross-component conflicts detected", "green"))
    else:
        for i, conflict in enumerate(report.cross_component_conflicts, 1):
            sev_color = verdict_color(conflict["severity"])
            lines.append("")
            lines.append(c(f"  [{i}] {conflict['type']}  [{conflict['severity']}]", sev_color))
            lines.append(f"      Detail   : {conflict['detail']}")
            lines.append(c(f"      Scenario : {conflict['scenario']}", "dim"))
            lines.append(c(f"      Fix      : {conflict['fix']}", "cyan"))

    # ── Failure Scenarios ──
    section(f"IMAGINATIVE PROJECTION — FAILURE SCENARIOS  ({len(report.failure_scenarios)} scenario(s))")
    for s in report.failure_scenarios:
        sev_color = verdict_color(s["severity"])
        lines.append("")
        lines.append(c(f"  [{s['id']}]  severity: {s['severity']}", sev_color))
        lines.append(f"    Trigger      : {s['trigger']}")
        lines.append(f"    Expected     : {s['user_expectation']}")
        if s["severity"] != "NONE":
            lines.append(c(f"    Reality      : {s['what_actually_happens']}", "red" if s["severity"] == "CRITICAL" else "yellow"))
            lines.append(c(f"    Surface      : {s['how_it_surfaces']}", "dim"))
            lines.append(c(f"    Downstream   : {s['downstream_effect']}", "magenta"))
            lines.append(c(f"    Prevention   : {s['prevention']}", "cyan"))
        else:
            lines.append(c(f"    ✓ Happy path — target state", "green"))

    # ── Recommendations ──
    section("RECOMMENDATIONS")
    if report.recommendations:
        for r in report.recommendations:
            lines.append(f"  • {r}")
    else:
        lines.append(c("  ✓ No additional recommendations", "green"))

    # ── Final Verdict ──
    lines.append("")
    hr("═")
    v = report.overall_verdict
    verdict_icon = {"PROMOTE": "✓", "WARN": "⚠", "BLOCK": "✗"}.get(v, "?")
    lines.append(c(f"  {verdict_icon}  VERDICT: {v}", verdict_color(v)))

    if v == "BLOCK":
        lines.append(c("  Component(s) must NOT be deployed. Resolve all BLOCK/CRITICAL items first.", "red"))
    elif v == "WARN":
        lines.append(c("  Component(s) may proceed with caution. Resolve WARN items before production.", "yellow"))
    else:
        lines.append(c("  Component(s) are constitutionally aligned. Safe to deploy.", "green"))

    hr("═")

    output = "\n".join(lines)
    return output


def render_markdown_report(report: AlignmentReport) -> str:
    """Plain markdown version for file output (no ANSI)."""
    lines = []
    lines.append(f"# EPOS Alignment Scan Report")
    lines.append(f"**Target:** {report.target}  ")
    lines.append(f"**Generated:** {report.generated_at}  ")
    lines.append(f"**Verdict:** {report.overall_verdict}\n")

    lines.append("## Environment")
    env = report.environment_check
    py = env.get("python", {})
    lines.append(f"- Python: {py.get('actual','?')} (required: 3.11+) — {'✓' if py.get('aligned') else '✗'}")
    lines.append(f"- EPOS_ROOT: {env.get('epos_root',{}).get('actual','NOT SET')}")
    for var, info in env.get("env_vars", {}).items():
        lines.append(f"- {var}: {'SET' if info['set'] else 'MISSING'}")

    lines.append("\n## Cross-Component Conflicts")
    if not report.cross_component_conflicts:
        lines.append("No conflicts detected.")
    for c_item in report.cross_component_conflicts:
        lines.append(f"\n### {c_item['type']} [{c_item['severity']}]")
        lines.append(f"**Detail:** {c_item['detail']}  ")
        lines.append(f"**Scenario:** {c_item['scenario']}  ")
        lines.append(f"**Fix:** {c_item['fix']}")

    lines.append("\n## Failure Scenarios")
    for s in report.failure_scenarios:
        lines.append(f"\n### {s['id']} [{s['severity']}]")
        lines.append(f"- **Trigger:** {s['trigger']}")
        lines.append(f"- **Expected:** {s['user_expectation']}")
        if s["severity"] != "NONE":
            lines.append(f"- **Reality:** {s['what_actually_happens']}")
            lines.append(f"- **Downstream:** {s['downstream_effect']}")
            lines.append(f"- **Prevention:** {s['prevention']}")

    lines.append("\n## Recommendations")
    for r in report.recommendations:
        lines.append(f"- {r}")

    lines.append(f"\n---\n**Final Verdict: {report.overall_verdict}**")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

# Directories to never recurse into during deep scan.
# Prevents 18K-file explosions from vendored deps and sibling workspaces.
SKIP_DIRS = {
    # Python packaging / virtualenv
    ".venv", "venv", "venv_epos", "venv_epos_311", "venv_az", "env", "site-packages", "__pycache__",
    "dist", "build", ".eggs", ".tox", ".mypy_cache",
    ".pytest_cache", "htmlcov",
    # Node / JS
    "node_modules", ".next", ".nuxt",
    # Version control / OS
    ".git", ".svn", ".hg",
    # Sibling workspaces — never scan these during epos_mcp deep scan
    "agent-zero", "friday", "echoes", "epos_db", "friday_backups",
    "_archive_openclaw_20260225",
    # Large vendored sub-trees
    "lib", "libs", "vendor", "third_party",
}


def collect_python_files(target: Path, deep: bool = False, skip_dirs: set | None = None) -> list[Path]:
    """Collect .py files from target (file or directory).

    deep=True recurses subdirectories but always prunes SKIP_DIRS so we
    never accidentally scan 18 000 vendored files.
    """
    if skip_dirs is None:
        skip_dirs = SKIP_DIRS

    if target.is_file():
        return [target] if target.suffix == ".py" else []

    if not target.is_dir():
        return []

    if not deep:
        return sorted(target.glob("*.py"))

    # Deep scan with directory pruning
    collected: list[Path] = []

    def _walk(directory: Path):
        try:
            entries = sorted(directory.iterdir())
        except (PermissionError, OSError):
            return
        for entry in entries:
            try:
                if entry.is_dir():
                    if entry.name in skip_dirs or entry.name.startswith("."):
                        continue
                    _walk(entry)
                elif entry.is_file() and entry.suffix == ".py":
                    collected.append(entry)
            except OSError:
                continue  # skip broken symlinks

    _walk(target)
    return collected


def build_recommendations(profiles, conflicts, env_check) -> list[str]:
    recs = []

    if not env_check.get("python", {}).get("aligned"):
        recs.append("WARNING: Python 3.11+ required. Run: python --version to verify.")

    if not env_check.get("epos_root", {}).get("exists"):
        recs.append("Set EPOS_ROOT in your .env file pointing to the epos_mcp workspace root.")

    for var, info in env_check.get("env_vars", {}).items():
        if not info["set"]:
            recs.append(f"Add {var} to your .env file.")

    dotenv_found = any(
        "load_dotenv" in (p.path.read_text(errors="replace") if not p.parse_error else "")
        for p in profiles
    )
    if not dotenv_found and any(p.env_vars_accessed for p in profiles):
        recs.append("Add 'from dotenv import load_dotenv; load_dotenv()' to every entrypoint.")

    if any(p.missing_packages for p in profiles):
        all_missing = set(pkg for p in profiles for pkg in p.missing_packages)
        recs.append(f"Install missing packages: pip install {' '.join(all_missing)}")

    path_mixing = any(c["type"] == "PATH_STYLE_MIXING" for c in conflicts)
    if path_mixing:
        recs.append("Standardize all paths to use Path() objects resolved from EPOS_ROOT. Remove hardcoded strings.")

    logged_not_exec = any(
        v["rule"] == "logged_not_executed"
        for p in profiles
        for v in p.constitutional_violations
    )
    if logged_not_exec:
        recs.append("Separate logging from execution. Only log 'success' AFTER verifying the artifact exists on disk.")

    return recs


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="EPOS Alignment Scanner — Pre-Mortem Imaginative Projection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python epos_align_scan.py governance_gate.py
  python epos_align_scan.py engine/ --deep
  python epos_align_scan.py . --deep --report
  python epos_align_scan.py epos_doctor.py --compare governance_gate.py
        """
    )
    parser.add_argument("target", help="File or directory to scan")
    parser.add_argument("--deep", action="store_true", help="Recursively scan subdirectories")
    parser.add_argument("--compare", metavar="OTHER", help="Cross-compare with a second target")
    parser.add_argument("--report", action="store_true", help="Save markdown report to file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON (machine-readable)")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(c(f"ERROR: Target does not exist: {target_path}", "red"))
        sys.exit(1)

    # Collect files
    files = collect_python_files(target_path, deep=args.deep)
    if args.compare:
        compare_path = Path(args.compare).resolve()
        files += collect_python_files(compare_path, deep=args.deep)

    if not files:
        print(c(f"No Python files found at: {target_path}", "yellow"))
        sys.exit(0)

    print(c(f"\n  Scanning {len(files)} file(s)...", "dim"))

    # Profile all files
    profiles = [profile_file(f) for f in files]

    # Cross-component analysis
    conflicts = detect_cross_conflicts(profiles)

    # Failure scenario generation
    scenarios = generate_failure_scenarios(profiles, conflicts)

    # Environment check
    env = run_environment_check()

    # Verdict
    verdict = compute_overall_verdict(profiles, conflicts)

    # Recommendations
    recs = build_recommendations(profiles, conflicts, env)

    # Build report
    report = AlignmentReport(
        target=str(target_path),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        overall_verdict=verdict,
        profiles=profiles,
        cross_component_conflicts=conflicts,
        failure_scenarios=scenarios,
        environment_check=env,
        recommendations=recs,
    )

    # Render
    if args.json:
        # Simplified JSON output
        output = {
            "target": report.target,
            "generated_at": report.generated_at,
            "verdict": report.overall_verdict,
            "conflicts": conflicts,
            "scenarios": scenarios,
            "recommendations": recs,
        }
        print(json.dumps(output, indent=2))
    else:
        print(render_report(report))

    if args.report:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"epos_align_report_{ts}.md")
        report_path.write_text(render_markdown_report(report), encoding="utf-8")
        print(c(f"\n  Report saved: {report_path.absolute()}", "cyan"))

    # Exit code for CI/automation
    exit_codes = {"PROMOTE": 0, "WARN": 1, "BLOCK": 2}
    sys.exit(exit_codes.get(verdict, 1))


if __name__ == "__main__":
    main()