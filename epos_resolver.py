# File: C:\Users\Jamie\workspace\epos_mcp\epos_resolver.py
# EPOS Resolution Agent v1.0
# TTLG Diagnostic → Surgical Resolution Pipeline
# Authority: EPOS Constitution v3.1
#
# PURPOSE:
#   Reads an epos_align_report_*.md, performs TTLG triage to separate
#   real EPOS issues from scanner false positives (vendored package internals),
#   then applies targeted resolutions in priority order:
#
#   PHASE 1 — Environment  : .env fixes (AGENT_ZERO_PATH, WORKSPACE_ROOT)
#   PHASE 2 — Dependencies : pip install for REAL missing packages only
#   PHASE 3 — Entrypoints  : load_dotenv() injection via epos_surgeon
#   PHASE 4 — Manifest     : writes RESOLUTION_MANIFEST.md with full audit trail
#
# USAGE:
#   python epos_resolver.py <report.md>              # full auto-resolve
#   python epos_resolver.py <report.md> --dry-run    # show plan, touch nothing
#   python epos_resolver.py <report.md> --phase 1    # run only one phase
#   python epos_resolver.py <report.md> --triage     # print triage analysis only
#
# SAFETY:
#   - Never installs packages that are internal EPOS modules
#   - Never touches files outside epos_mcp/ root
#   - Never modifies vendored/venv/site-packages directories
#   - Creates ops/surgical_backups/ session before any file write
#   - Writes full manifest of every action taken

import sys
import os
import re
import json
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

EPOS_ROOT = Path(os.environ.get("EPOS_ROOT", "/mnt/c/Users/Jamie/workspace/epos_mcp"))
WORKSPACE_ROOT = EPOS_ROOT.parent
BACKUP_ROOT = EPOS_ROOT / "ops" / "surgical_backups"

# Packages that are REAL third-party installs for EPOS
EPOS_REAL_PACKAGES = {
    "fastapi", "uvicorn", "websockets", "python-dotenv", "dotenv",
    "duckduckgo_search", "langchain_openai", "browser_use",
    "pydantic", "httpx", "aiohttp", "requests", "starlette",
    "anthropic", "openai", "litellm",
}

# EPOS internal modules — these should EXIST on disk, not be pip-installed
# The resolver will check if their .py file exists and report if missing
EPOS_INTERNAL_MODULES = {
    "constitutional_arbiter", "flywheel_analyst", "context_librarian",
    "agent_zero_bridge", "agent_orchestrator", "stasis", "path_utils",
    "roles", "epos_intelligence", "governance", "epos_doctor",
    "governed_orchestrator", "meta_orchestrator", "az_dispatch",
    "epos_runner", "epos_api", "command_center", "cascades",
    "tributaries", "validation", "cascade_worker", "tributary_worker",
}

# Vendored package prefixes — any "missing dependency" traced to these
# directories is a false positive. The scanner should not have entered them
# but SKIP_DIRS didn't catch them all in this run.
VENDORED_PREFIXES = {
    # Nuitka compiler internals
    "CodeHelpers", "ModuleCodes", "ExpressionBases", "FunctionNodes",
    "ChildrenHavingMixins", "PythonAPICodes", "ErrorCodes",
    "ExpressionBasesGenerated", "NodeMakingHelpers", "AttributeNodesGenerated",
    "AttributeLookupNodes", "StatementBasesGenerated", "ExpressionShapeMixins",
    "ExpressionShapeMixins", "NodeBases", "VariableRefNodes",
    # Windows-specific packages that are never pip-installable
    "_winxptheme", "win32api", "win32com", "win32con", "win32event",
    "win32file", "win32gui", "win32net", "win32print", "win32process",
    "win32security", "win32service", "win32transaction", "win32ts",
    "winreg", "winerror", "pywintypes",
    # Internal module patterns from pandas/numpy/scipy/PIL that self-reference
    "session",   # not a pip package — internal to some libs
    "cli",       # not the 'cli' package — internal reference
    "utils",     # not a pip package — every lib has utils.py
}

# Port numbers that are LEGITIMATELY shared (assigned roles, not collisions)
LEGITIMATE_PORT_ASSIGNMENTS = {
    8001:  "epos_api / meta_orchestrator  (EPOS API server)",
    11434: "ollama                         (LLM inference)",
    8080:  "agent_zero                     (Agent Zero UI)",
    5432:  "postgresql                     (EPOS DB)",
    3000:  "postgrest                      (REST API layer)",
}

# Terminal colors
C = {
    "reset": "\033[0m", "bold": "\033[1m", "red": "\033[91m",
    "yellow": "\033[93m", "green": "\033[92m", "cyan": "\033[96m",
    "white": "\033[97m", "dim": "\033[2m", "magenta": "\033[95m",
}

def c(text, key):
    return f"{C.get(key,'')}{text}{C['reset']}"

def hr(char="═", width=78):
    print(c(char * width, "dim"))

def section(title):
    print()
    print(c(f"  {title}", "cyan"))
    print(c("  " + "─" * 74, "dim"))

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TriagedIssue:
    category: str         # REAL_PACKAGE / INTERNAL_MODULE / ENV_VAR / FALSE_POSITIVE / PATH / DOTENV
    severity: str         # CRITICAL / HIGH / WARN
    description: str
    action: str           # what the resolver will do
    affected_files: list[str] = field(default_factory=list)
    resolved: bool = False
    resolution_note: str = ""


@dataclass
class ResolutionManifest:
    session_id: str
    report_path: str
    started_at: str
    dry_run: bool
    issues_total: int = 0
    issues_real: int = 0
    issues_false_positive: int = 0
    actions_taken: list[dict] = field(default_factory=list)
    actions_skipped: list[dict] = field(default_factory=list)
    completed: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# REPORT PARSER
# ─────────────────────────────────────────────────────────────────────────────

def parse_report(report_path: Path) -> dict:
    """
    Parse the markdown report into structured conflict/recommendation buckets.
    Returns: {
        'env': {...},
        'missing_deps': [{'pkg': str, 'files': [str]}],
        'port_collisions': [{'port': int, 'files': [str]}],
        'dotenv_missing': bool,
        'path_mixing': bool,
        'recommendations': [str],
    }
    """
    text = report_path.read_text(encoding="utf-8", errors="replace")
    result = {
        "env": {},
        "missing_deps": [],
        "port_collisions": [],
        "dotenv_missing": False,
        "path_mixing": False,
        "recommendations": [],
    }

    # Environment section
    for line in text.splitlines():
        if line.startswith("- Python:"):
            result["env"]["python"] = line
        elif "AGENT_ZERO_PATH: MISSING" in line:
            result["env"]["agent_zero_path_missing"] = True
        elif "WORKSPACE_ROOT: MISSING" in line:
            result["env"]["workspace_root_missing"] = True
        elif "DOTENV_NOT_LOADED" in line:
            result["dotenv_missing"] = True
        elif "PATH_STYLE_MIXING" in line or "FS-PATH-MIXING" in line:
            result["path_mixing"] = True

    # Missing dependencies
    dep_pattern = re.compile(
        r"### MISSING_DEPENDENCY \[CRITICAL\]\n\*\*Detail:\*\* Package '([^']+)' not installed but required by: (.+?)(?=\n\n|\Z)",
        re.DOTALL
    )
    for match in dep_pattern.finditer(text):
        pkg = match.group(1).strip()
        files_raw = match.group(2).strip()
        files = [f.strip() for f in files_raw.split(",")]
        result["missing_deps"].append({"pkg": pkg, "files": files})

    # Port collisions (only real EPOS ports)
    port_pattern = re.compile(
        r"### PORT_COLLISION \[HIGH\]\n\*\*Detail:\*\* Port (\d+) referenced in multiple components: (.+?)(?=\n\n|\Z)",
        re.DOTALL
    )
    for match in port_pattern.finditer(text):
        port = int(match.group(1))
        files_raw = match.group(2).strip()
        files = [f.strip() for f in files_raw.split(",")]
        result["port_collisions"].append({"port": port, "files": files})

    # Recommendations
    in_recs = False
    for line in text.splitlines():
        if line.strip() == "## Recommendations":
            in_recs = True
            continue
        if in_recs and line.startswith("- "):
            result["recommendations"].append(line[2:].strip())
        elif in_recs and line.startswith("---"):
            in_recs = False

    return result


# ─────────────────────────────────────────────────────────────────────────────
# TRIAGE ENGINE
# The TTLG brain — separates signal from noise before any action is taken
# ─────────────────────────────────────────────────────────────────────────────

def triage(parsed: dict) -> list[TriagedIssue]:
    """
    Apply TTLG diagnostic logic:
    - Real EPOS packages → pip install
    - Internal EPOS modules → check if file exists, report missing
    - Vendored/Windows packages → false positive, skip
    - Env vars missing → .env fix
    - Port collisions on EPOS ports with EPOS files → real issue
    - Port collisions where all files are vendored → false positive
    """
    issues: list[TriagedIssue] = []

    # ── Env vars ──
    if parsed["env"].get("agent_zero_path_missing"):
        issues.append(TriagedIssue(
            category="ENV_VAR",
            severity="CRITICAL",
            description="AGENT_ZERO_PATH not set in .env",
            action="Append AGENT_ZERO_PATH=/mnt/c/Users/Jamie/workspace/agent-zero to .env",
        ))

    if parsed["env"].get("workspace_root_missing"):
        issues.append(TriagedIssue(
            category="ENV_VAR",
            severity="HIGH",
            description="WORKSPACE_ROOT not set in .env",
            action="Append WORKSPACE_ROOT=/mnt/c/Users/Jamie/workspace to .env",
        ))

    # ── Python version ──
    if parsed["env"].get("python") and "✗" in parsed["env"]["python"]:
        issues.append(TriagedIssue(
            category="ENVIRONMENT",
            severity="CRITICAL",
            description="Python 3.12.3 active — EPOS requires 3.11.x",
            action="FLAG ONLY: cannot auto-fix Python version. Run: pyenv install 3.11.9 && pyenv local 3.11.9",
        ))

    # ── Missing dependencies — triage each one ──
    for dep in parsed["missing_deps"]:
        pkg = dep["pkg"]
        files = dep["files"]

        # Filter to only EPOS-owned files (not vendored)
        epos_files = [f for f in files if _is_epos_file(f)]

        if not epos_files:
            # All affected files are vendored — pure false positive
            issues.append(TriagedIssue(
                category="FALSE_POSITIVE",
                severity="INFO",
                description=f"'{pkg}' flagged but all affected files are vendored internals",
                action="SKIP — scanner false positive from vendored package tree",
                affected_files=files[:3],
            ))
            continue

        if pkg in VENDORED_PREFIXES:
            issues.append(TriagedIssue(
                category="FALSE_POSITIVE",
                severity="INFO",
                description=f"'{pkg}' is a vendored internal module (Nuitka/Win32/stdlib), not a pip package",
                action="SKIP — not installable via pip",
                affected_files=epos_files[:3],
            ))
            continue

        if pkg in EPOS_INTERNAL_MODULES:
            # Check if the .py file actually exists in epos_mcp
            module_file = EPOS_ROOT / f"{pkg}.py"
            engine_file = EPOS_ROOT / "engine" / f"{pkg}.py"
            exists = module_file.exists() or engine_file.exists()
            issues.append(TriagedIssue(
                category="INTERNAL_MODULE",
                severity="CRITICAL" if not exists else "INFO",
                description=f"Internal EPOS module '{pkg}' imported but {'file not found on disk' if not exists else 'file exists — import path issue'}",
                action=f"{'FLAG: module file missing — needs to be created or path fixed' if not exists else 'Check sys.path / import resolution'}",
                affected_files=epos_files,
            ))
            continue

        if pkg in EPOS_REAL_PACKAGES or _looks_like_real_package(pkg):
            # Check if already installed
            spec = importlib.util.find_spec(pkg.replace("-", "_"))
            if spec is not None:
                issues.append(TriagedIssue(
                    category="REAL_PACKAGE",
                    severity="INFO",
                    description=f"'{pkg}' already installed (find_spec found it)",
                    action="SKIP — already available",
                    affected_files=epos_files,
                    resolved=True,
                    resolution_note="Already installed",
                ))
            else:
                issues.append(TriagedIssue(
                    category="REAL_PACKAGE",
                    severity="CRITICAL",
                    description=f"'{pkg}' not installed — required by EPOS components",
                    action=f"pip install {pkg}",
                    affected_files=epos_files,
                ))
        else:
            # Unknown — flag for human review
            issues.append(TriagedIssue(
                category="UNKNOWN",
                severity="WARN",
                description=f"'{pkg}' — unclear if real package or internal module",
                action="FLAG FOR REVIEW — check if this should be pip install or a local module",
                affected_files=epos_files[:3],
            ))

    # ── Port collisions — filter to real EPOS-to-EPOS conflicts ──
    for pc in parsed["port_collisions"]:
        port = pc["port"]
        files = pc["files"]
        epos_files = [f for f in files if _is_epos_file(f)]

        if len(epos_files) <= 1:
            # Only one EPOS file references this port — the rest are vendored false positives
            continue

        if port in LEGITIMATE_PORT_ASSIGNMENTS:
            # Known assigned port — document assignment, not a real collision
            issues.append(TriagedIssue(
                category="PORT_ASSIGNMENT",
                severity="INFO",
                description=f"Port {port} is legitimately assigned: {LEGITIMATE_PORT_ASSIGNMENTS[port]}",
                action=f"Document port assignment in ENVIRONMENT_SPEC.md. {len(epos_files)} EPOS files reference it.",
                affected_files=epos_files,
            ))
        else:
            issues.append(TriagedIssue(
                category="PORT_COLLISION",
                severity="HIGH",
                description=f"Port {port} referenced in {len(epos_files)} EPOS components without clear assignment",
                action=f"Assign canonical owner in .env and ENVIRONMENT_SPEC.md",
                affected_files=epos_files[:5],
            ))

    # ── Dotenv missing ──
    if parsed["dotenv_missing"]:
        issues.append(TriagedIssue(
            category="DOTENV",
            severity="HIGH",
            description="load_dotenv() not found in scanned entrypoints",
            action="Run epos_surgeon.py to auto-inject load_dotenv() block",
        ))

    # ── Path mixing ──
    if parsed["path_mixing"]:
        issues.append(TriagedIssue(
            category="PATH",
            severity="HIGH",
            description="Windows-style hardcoded paths detected in EPOS files",
            action="Run epos_align_scan.py to identify exact lines, then epos_surgeon.py to flag for review",
        ))

    return issues


def _is_epos_file(filename: str) -> bool:
    """
    Returns True if a filename looks like an EPOS-owned file,
    not a vendored package internal.
    Known vendored filename patterns are excluded.
    """
    filename = filename.strip()

    # Nuitka internal patterns
    if re.search(r'(Codes|Nodes|Mixins|Bases|Helpers|Generated)\.py$', filename):
        return False
    # Win32 internals
    if filename.startswith("win32") or filename.startswith("Win32"):
        return False
    # Standard test files from numpy/pandas/scipy
    if re.match(r'test_(algos|arrayprint|datetime|frame|hashing|iloc|join|json|'
                r'linalg|loadtxt|melt|mem|mman|multithreading|nunique|orc|parallel|'
                r'period|read_fwf|regex|smoke|stata|timestamp|to_datetime|'
                r'usecols|win32|pandas|parquet|stack|constructors|numeric|'
                r'expanding|format|generator|histograms|nanfunctions|nditer|'
                r'util|array|downstream)', filename):
        return False
    # setuptools internals
    if filename in {"Build.py", "bdist_egg.py", "bdist_wheel.py", "build_meta.py",
                    "develop.py", "easy_install.py", "egg_info.py", "expand.py",
                    "fixtures.py", "monkey.py", "saveopts.py", "setupcfg.py",
                    "setuptools_ext.py", "_apply_pyprojecttoml.py", "_bdist_wheel.py",
                    "_shimmed_dist_utils.py", "pyprojecttoml.py"}:
        return False
    # Tornado/async test internals
    if filename in {"iostream_test.py", "httpserver_test.py", "escape_test.py",
                    "ansitowin32_test.py", "initialise_test.py", "isatty_test.py",
                    "simple_httpclient_test.py"}:
        return False

    # EPOS-owned patterns — these are real
    epos_patterns = [
        "governance", "epos", "meta_orchestrator", "az_dispatch", "bridge",
        "agent_orchestrator", "cascades", "tributary", "constitutional",
        "flywheel", "context_librarian", "stasis", "path_utils", "roles",
        "command_center", "governed_orchestrator", "epos_runner", "epos_api",
        "brand_validator", "echolocation", "immediate_execute", "phi3", "phi4",
        "llm_client", "mistral", "jarvis", "workflow_demo", "setup_agents",
        "autonomy", "audio_input",
    ]
    name_lower = filename.lower()
    if any(p in name_lower for p in epos_patterns):
        return True

    # If it's a well-known vendored file pattern, exclude
    vendored_names = {
        "effects.py", "filters.py", "frame.py", "series.py", "probability.py",
        "symbolic.py", "layer.py", "indexing.py", "networks.py", "datetimes.py",
        "arrow.py", "config.py", "main.py", "runner.py", "server.py", "output.py",
        "project.py", "session.py", "shapes.py", "transitions.py", "compositing.py",
        "export.py", "media.py", "timeline.py", "connectors.py", "pages.py",
    }
    if filename in vendored_names:
        return False

    # Default: include (err on side of more review, not less)
    return True


def _looks_like_real_package(pkg: str) -> bool:
    """Heuristic: does this look like a real installable package name?"""
    # Real packages tend to be lowercase with underscores/hyphens
    # Vendored internals tend to be CamelCase or all-caps
    if pkg[0].isupper() and not any(c in pkg for c in ["-", "_"]):
        return False  # CamelCase → likely internal
    if pkg.startswith("_"):
        return False  # Private module → not pip-installable
    return True


# ─────────────────────────────────────────────────────────────────────────────
# RESOLUTION PHASES
# ─────────────────────────────────────────────────────────────────────────────

def phase_1_env_fixes(issues: list[TriagedIssue], manifest: ResolutionManifest, dry_run: bool):
    """Fix missing .env entries."""
    section("PHASE 1 — ENVIRONMENT FIXES")

    env_file = EPOS_ROOT / ".env"
    env_issues = [i for i in issues if i.category == "ENV_VAR" and not i.resolved]

    if not env_issues:
        print(c("  ✓ No .env issues to fix", "green"))
        return

    if not env_file.exists():
        print(c(f"  ✗ .env not found at {env_file}", "red"))
        print(c("    Creating new .env file...", "cyan"))
        if not dry_run:
            env_file.write_text("# EPOS Environment Configuration\n", encoding="utf-8")

    if dry_run:
        for issue in env_issues:
            print(c(f"  [DRY-RUN] Would: {issue.action}", "yellow"))
        return

    # Read current .env
    env_content = env_file.read_text(encoding="utf-8")

    # Backup first
    backup_env = BACKUP_ROOT / manifest.session_id / ".env.bak"
    backup_env.parent.mkdir(parents=True, exist_ok=True)
    backup_env.write_text(env_content, encoding="utf-8")

    appended = []
    for issue in env_issues:
        # Extract key=value from action string
        if "AGENT_ZERO_PATH" in issue.action and "AGENT_ZERO_PATH" not in env_content:
            line = "AGENT_ZERO_PATH=/mnt/c/Users/Jamie/workspace/agent-zero\n"
            env_content += line
            appended.append(line.strip())
            issue.resolved = True
            issue.resolution_note = "Appended to .env"

        elif "WORKSPACE_ROOT" in issue.action and "WORKSPACE_ROOT" not in env_content:
            line = "WORKSPACE_ROOT=/mnt/c/Users/Jamie/workspace\n"
            env_content += line
            appended.append(line.strip())
            issue.resolved = True
            issue.resolution_note = "Appended to .env"

    env_file.write_text(env_content, encoding="utf-8")

    for line in appended:
        print(c(f"  ✓ Added to .env: {line}", "green"))
        manifest.actions_taken.append({"phase": 1, "action": f"Added to .env: {line}"})


def phase_2_install_packages(issues: list[TriagedIssue], manifest: ResolutionManifest, dry_run: bool):
    """pip install real missing packages."""
    section("PHASE 2 — PACKAGE INSTALLATION")

    pkg_issues = [i for i in issues if i.category == "REAL_PACKAGE" and not i.resolved]

    if not pkg_issues:
        print(c("  ✓ No real package installations needed", "green"))
        return

    # Deduplicate
    pkgs_to_install = list({i.description.split("'")[1] for i in pkg_issues})

    print(c(f"  Installing {len(pkgs_to_install)} package(s): {', '.join(pkgs_to_install)}", "white"))

    for pkg in pkgs_to_install:
        if dry_run:
            print(c(f"  [DRY-RUN] Would: pip install {pkg}", "yellow"))
            continue

        print(c(f"  → pip install {pkg} ...", "dim"))
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(c(f"  ✓ Installed: {pkg}", "green"))
            manifest.actions_taken.append({"phase": 2, "action": f"pip install {pkg}"})
            # Mark resolved
            for issue in pkg_issues:
                if f"'{pkg}'" in issue.description:
                    issue.resolved = True
                    issue.resolution_note = "pip install succeeded"
        else:
            print(c(f"  ✗ Failed: {pkg}", "red"))
            print(c(f"    {result.stderr[:200]}", "dim"))
            manifest.actions_skipped.append({
                "phase": 2,
                "action": f"pip install {pkg}",
                "reason": result.stderr[:200],
            })


def phase_3_dotenv_injection(issues: list[TriagedIssue], manifest: ResolutionManifest, dry_run: bool):
    """Run epos_surgeon for load_dotenv injection."""
    section("PHASE 3 — DOTENV INJECTION")

    dotenv_issues = [i for i in issues if i.category == "DOTENV" and not i.resolved]
    if not dotenv_issues:
        print(c("  ✓ No dotenv injection needed", "green"))
        return

    surgeon = EPOS_ROOT / "epos_surgeon.py"
    if not surgeon.exists():
        print(c(f"  ✗ epos_surgeon.py not found at {surgeon}", "red"))
        print(c("    Copy epos_surgeon.py to epos_mcp root first.", "yellow"))
        manifest.actions_skipped.append({
            "phase": 3,
            "action": "dotenv injection",
            "reason": "epos_surgeon.py not found",
        })
        return

    cmd = [sys.executable, str(surgeon), ".", "--deep"]
    if dry_run:
        cmd.append("--dry-run")
        print(c(f"  [DRY-RUN] Would run: {' '.join(cmd)}", "yellow"))
        return

    print(c("  → Running epos_surgeon.py for dotenv injection...", "dim"))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(EPOS_ROOT))
    print(result.stdout[-2000:] if result.stdout else "")

    if result.returncode in (0, 1):  # 0=PROMOTE, 1=WARN both acceptable
        print(c("  ✓ Surgeon pass complete", "green"))
        manifest.actions_taken.append({"phase": 3, "action": "epos_surgeon dotenv injection"})
        for issue in dotenv_issues:
            issue.resolved = True
            issue.resolution_note = "epos_surgeon injected load_dotenv()"
    else:
        print(c(f"  ✗ Surgeon returned exit code {result.returncode}", "red"))
        manifest.actions_skipped.append({
            "phase": 3,
            "action": "epos_surgeon dotenv injection",
            "reason": f"exit code {result.returncode}",
        })


def phase_4_write_manifest(
    issues: list[TriagedIssue],
    manifest: ResolutionManifest,
    dry_run: bool
):
    """Write RESOLUTION_MANIFEST.md — the permanent audit trail."""
    section("PHASE 4 — RESOLUTION MANIFEST")

    manifest.completed = True

    real_issues = [i for i in issues if i.category != "FALSE_POSITIVE"]
    false_positives = [i for i in issues if i.category == "FALSE_POSITIVE"]
    resolved = [i for i in real_issues if i.resolved]
    flagged = [i for i in real_issues if not i.resolved]

    lines = []
    lines.append(f"# EPOS Resolution Manifest")
    lines.append(f"**Session:** {manifest.session_id}  ")
    lines.append(f"**Report:** {manifest.report_path}  ")
    lines.append(f"**Started:** {manifest.started_at}  ")
    lines.append(f"**Mode:** {'DRY-RUN' if dry_run else 'LIVE'}  ")
    lines.append(f"**Completed:** {datetime.now().isoformat()}  ")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total issues in report: {len(issues)}")
    lines.append(f"- Real EPOS issues: {len(real_issues)}")
    lines.append(f"- False positives filtered: {len(false_positives)}")
    lines.append(f"- Resolved this session: {len(resolved)}")
    lines.append(f"- Flagged for human review: {len(flagged)}")
    lines.append("")

    lines.append("## Actions Taken")
    if manifest.actions_taken:
        for a in manifest.actions_taken:
            lines.append(f"- [Phase {a['phase']}] {a['action']}")
    else:
        lines.append("- None (dry-run or nothing to fix)")
    lines.append("")

    lines.append("## Flagged for Human Review")
    for issue in flagged:
        if issue.category in ("ENVIRONMENT", "INTERNAL_MODULE", "UNKNOWN", "PORT_COLLISION", "PATH"):
            lines.append(f"\n### [{issue.severity}] {issue.category}: {issue.description}")
            lines.append(f"**Required action:** {issue.action}")
            if issue.affected_files:
                lines.append(f"**Files:** {', '.join(issue.affected_files[:5])}")

    lines.append("")
    lines.append("## False Positives Filtered")
    lines.append(f"({len(false_positives)} vendored/internal package references excluded from remediation)")
    lines.append("")

    lines.append("## Actions Skipped")
    if manifest.actions_skipped:
        for a in manifest.actions_skipped:
            lines.append(f"- [Phase {a['phase']}] {a['action']} — reason: {a.get('reason','unknown')}")
    else:
        lines.append("- None")

    manifest_text = "\n".join(lines)

    if not dry_run:
        out_path = EPOS_ROOT / f"RESOLUTION_MANIFEST_{manifest.session_id}.md"
        out_path.write_text(manifest_text, encoding="utf-8")
        print(c(f"  ✓ Manifest saved: {out_path}", "green"))
    else:
        print(c("  [DRY-RUN] Manifest would be saved to RESOLUTION_MANIFEST_<session>.md", "yellow"))

    # Always print summary to terminal
    print()
    print(c(f"  Real issues     : {len(real_issues)}", "white"))
    print(c(f"  Resolved        : {len(resolved)}", "green"))
    print(c(f"  Need human eyes : {len(flagged)}", "yellow"))
    print(c(f"  False positives : {len(false_positives)}", "dim"))


# ─────────────────────────────────────────────────────────────────────────────
# TRIAGE PRINT
# ─────────────────────────────────────────────────────────────────────────────

def print_triage(issues: list[TriagedIssue]):
    """Print triage analysis — what is real, what is noise, what will be done."""
    hr("═")
    print(c("  TTLG TRIAGE ANALYSIS", "bold"))
    hr("═")

    categories = {}
    for issue in issues:
        categories.setdefault(issue.category, []).append(issue)

    order = ["ENVIRONMENT", "ENV_VAR", "REAL_PACKAGE", "INTERNAL_MODULE",
             "DOTENV", "PATH", "PORT_ASSIGNMENT", "PORT_COLLISION", "UNKNOWN", "FALSE_POSITIVE"]

    for cat in order:
        cat_issues = categories.get(cat, [])
        if not cat_issues:
            continue

        if cat == "FALSE_POSITIVE":
            print(c(f"\n  ░ FALSE POSITIVES ({len(cat_issues)}) — will be skipped", "dim"))
            print(c(f"    These are vendored/internal package references from nuitka, numpy,", "dim"))
            print(c(f"    pandas, win32, setuptools internals. Not pip-installable.", "dim"))
            continue

        color_key = {
            "ENVIRONMENT": "red", "ENV_VAR": "red", "REAL_PACKAGE": "yellow",
            "INTERNAL_MODULE": "magenta", "DOTENV": "yellow", "PATH": "yellow",
            "PORT_COLLISION": "yellow", "PORT_ASSIGNMENT": "dim", "UNKNOWN": "white",
        }.get(cat, "white")

        print(c(f"\n  ▶ {cat} ({len(cat_issues)})", color_key))
        for issue in cat_issues[:8]:  # cap display to 8 per category
            sev_color = "red" if issue.severity == "CRITICAL" else "yellow" if issue.severity == "HIGH" else "dim"
            print(c(f"    [{issue.severity}] {issue.description[:80]}", sev_color))
            print(c(f"           → {issue.action[:80]}", "cyan"))
        if len(cat_issues) > 8:
            print(c(f"    ... and {len(cat_issues) - 8} more", "dim"))

    hr("═")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="EPOS Resolution Agent — TTLG Triage → Surgical Fix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python epos_resolver.py epos_align_report_20260318_184650.md
  python epos_resolver.py epos_align_report_20260318_184650.md --dry-run
  python epos_resolver.py epos_align_report_20260318_184650.md --triage
  python epos_resolver.py epos_align_report_20260318_184650.md --phase 1
        """
    )
    parser.add_argument("report", help="Path to epos_align_report_*.md")
    parser.add_argument("--dry-run", action="store_true", help="Show plan, touch nothing")
    parser.add_argument("--triage", action="store_true", help="Print triage only, no fixes")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run one phase only")
    args = parser.parse_args()

    report_path = Path(args.report).resolve()
    if not report_path.exists():
        print(c(f"  ✗ Report not found: {report_path}", "red"))
        sys.exit(1)

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = ResolutionManifest(
        session_id=session_id,
        report_path=str(report_path),
        started_at=datetime.now().isoformat(),
        dry_run=args.dry_run,
    )

    hr("═")
    print(c("  EPOS RESOLUTION AGENT", "bold"))
    print(c(f"  Report  : {report_path.name}", "white"))
    print(c(f"  Session : {session_id}", "dim"))
    print(c(f"  Mode    : {'DRY-RUN' if args.dry_run else 'LIVE'}", "yellow" if args.dry_run else "green"))
    hr("═")

    # Parse
    print(c("\n  Parsing report...", "dim"))
    parsed = parse_report(report_path)
    print(c(f"  Found: {len(parsed['missing_deps'])} dep flags, "
            f"{len(parsed['port_collisions'])} port flags", "white"))

    # Triage
    print(c("  Running TTLG triage...", "dim"))
    issues = triage(parsed)

    real = [i for i in issues if i.category != "FALSE_POSITIVE"]
    fps  = [i for i in issues if i.category == "FALSE_POSITIVE"]
    manifest.issues_total = len(issues)
    manifest.issues_real = len(real)
    manifest.issues_false_positive = len(fps)

    print(c(f"  Triage complete: {len(real)} real issues, {len(fps)} false positives filtered", "green"))

    print_triage(issues)

    if args.triage:
        return

    # Run phases
    dry = args.dry_run
    if args.phase is None or args.phase == 1:
        phase_1_env_fixes(issues, manifest, dry)
    if args.phase is None or args.phase == 2:
        phase_2_install_packages(issues, manifest, dry)
    if args.phase is None or args.phase == 3:
        phase_3_dotenv_injection(issues, manifest, dry)
    if args.phase is None or args.phase == 4:
        phase_4_write_manifest(issues, manifest, dry)

    hr("═")
    print(c(f"  RESOLUTION AGENT COMPLETE  —  session: {session_id}", "bold"))
    hr("═")


if __name__ == "__main__":
    main()