# File: /mnt/c/Users/Jamie/workspace/epos_mcp/ttlg_agents.py
# TTLG Agent Team v1.0 — LangGraph Implementation
# Through The Looking Glass: Autonomous Diagnostic & Resolution Pipeline
# Authority: EPOS Constitution v3.1
#
# ARCHITECTURE DECISION: LangGraph over CrewAI
#   TTLG is a stateful, multi-phase pipeline with conditional branching,
#   governance gates, and rollback capability. LangGraph's directed state
#   graph maps 1:1 to TTLG's six phases. CrewAI's role abstraction would
#   obscure the conditional logic we need at every gate.
#
# THE SIX AGENTS (TTLG Phases → LangGraph Nodes):
#
#   1. SCOUT        — Scans the environment. Reads reports. Collects raw state.
#   2. THINKER      — Triages findings. Separates signal from noise.
#   3. GATE         — Constitutional arbiter. GO / PIVOT / KILL verdict.
#   4. SURGEON      — Executes repairs. Calls epos_surgeon + epos_resolver.
#   5. ANALYST      — Validates post-repair state. Runs post-scan.
#   6. AAR          — After Action Report. Writes manifest. Updates memory.
#
# USAGE:
#   python ttlg_agents.py                          # full autonomous run
#   python ttlg_agents.py --dry-run                # plan only, no writes
#   python ttlg_agents.py --phase scout            # run one phase only
#   python ttlg_agents.py --report <file.md>       # use existing report
#   python ttlg_agents.py --resume <session_id>    # resume from checkpoint
#
# REQUIREMENTS:
#   pip install langgraph langchain-anthropic python-dotenv

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import TypedDict, Annotated, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── LangGraph imports ──
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("Missing dependencies. Run:")
    print("  pip install langgraph langchain-anthropic")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

EPOS_ROOT = Path(os.environ.get("EPOS_ROOT", "/mnt/c/Users/Jamie/workspace/epos_mcp"))
WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT", "/mnt/c/Users/Jamie/workspace"))
BACKUP_ROOT = EPOS_ROOT / "ops" / "surgical_backups"
SESSION_LOG_DIR = EPOS_ROOT / "ops" / "ttlg_sessions"

# Constitutional severity thresholds
BLOCK_THRESHOLD = 0        # Any BLOCK → Gate says KILL
CRITICAL_THRESHOLD = 3     # > 3 CRITICAL conflicts → Gate says PIVOT
WARN_THRESHOLD = 10        # > 10 WARNs → Gate says PIVOT

# Terminal colors
C = {
    "reset": "\033[0m", "bold": "\033[1m", "red": "\033[91m",
    "yellow": "\033[93m", "green": "\033[92m", "cyan": "\033[96m",
    "white": "\033[97m", "dim": "\033[2m", "magenta": "\033[95m",
    "blue": "\033[94m",
}

def clr(text, key):
    return f"{C.get(key,'')}{text}{C['reset']}"

def hr(char="═", width=78):
    print(clr(char * width, "dim"))

def phase_header(phase, agent, color="cyan"):
    print()
    hr("─")
    print(clr(f"  [{phase}]  {agent}", color))
    hr("─")

# ─────────────────────────────────────────────────────────────────────────────
# TTLG STATE — the shared memory across all six agents
# Every agent reads from state and writes back to state.
# LangGraph persists this across checkpoints.
# ─────────────────────────────────────────────────────────────────────────────

class TTLGState(TypedDict):
    # Session identity
    session_id: str
    started_at: str
    dry_run: bool
    resume_from: Optional[str]

    # Phase tracking
    current_phase: str
    completed_phases: list[str]

    # Scout outputs
    report_path: Optional[str]
    scan_verdict: str           # PROMOTE / WARN / BLOCK
    raw_issues: dict            # parsed from report

    # Thinker outputs
    triaged_issues: dict        # {real: [...], false_positive: [...]}
    real_issue_count: int
    false_positive_count: int
    critical_count: int
    block_count: int

    # Gate verdict
    gate_verdict: str           # GO / PIVOT / KILL
    gate_rationale: str

    # Surgeon outputs
    repairs_applied: list[dict]
    repairs_failed: list[dict]
    files_patched: int

    # Analyst outputs
    post_scan_verdict: str
    improvement_delta: str      # "BLOCK→WARN", "WARN→PROMOTE", etc.
    remaining_issues: int

    # AAR outputs
    manifest_path: Optional[str]
    session_summary: str

    # Error handling
    errors: list[str]
    abort_reason: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# LLM CLIENT — model-agnostic, swappable per agent
# ─────────────────────────────────────────────────────────────────────────────

def get_llm(model: str = "claude-sonnet-4-6", temperature: float = 0.0):
    """
    Returns a LangChain-compatible LLM client.
    Uses Claude Sonnet by default — swap to any model without code changes.
    temperature=0.0 for deterministic governance decisions.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set in .env. "
            "Add it to proceed with LLM-assisted phases."
        )
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 1: SCOUT
# Role: Scan the environment. Collect raw state. Generate or load report.
# Constitutional alignment: Article I Pre-Mortem Mandate
# ─────────────────────────────────────────────────────────────────────────────

def agent_scout(state: TTLGState) -> TTLGState:
    phase_header("PHASE 1", "SCOUT — Environment Scan", "cyan")

    session_id = state["session_id"]
    dry_run = state["dry_run"]

    # ── Check if report already provided ──
    if state.get("report_path") and Path(state["report_path"]).exists():
        print(clr(f"  Using existing report: {state['report_path']}", "dim"))
        report_path = state["report_path"]
    else:
        # ── Run epos_doctor first ──
        print(clr("  Running epos_doctor.py preflight...", "dim"))
        doctor_result = _run_tool("python epos_doctor.py", cwd=EPOS_ROOT)
        if doctor_result["returncode"] != 0:
            print(clr("  ⚠ Doctor found issues — proceeding to scan anyway", "yellow"))

        # ── Run alignment scan ──
        print(clr("  Running epos_align_scan.py...", "dim"))
        scan_result = _run_tool(
            "python epos_align_scan.py . --deep --report",
            cwd=EPOS_ROOT
        )

        # ── Find the report ──
        reports = sorted(EPOS_ROOT.glob("epos_align_report_*.md"), reverse=True)
        if not reports:
            state["errors"].append("Scout: No alignment report generated")
            state["abort_reason"] = "No report produced by epos_align_scan.py"
            state["current_phase"] = "ABORT"
            return state

        report_path = str(reports[0])
        print(clr(f"  Report: {Path(report_path).name}", "green"))

    # ── Parse verdict from report ──
    verdict = "UNKNOWN"
    real_issues = {
        "missing_deps": [],
        "port_collisions": [],
        "env_missing": [],
        "path_mixing": False,
        "dotenv_missing": False,
        "python_version_wrong": False,
    }

    try:
        report_text = Path(report_path).read_text(encoding="utf-8", errors="replace")

        # Extract verdict
        if "**Final Verdict: BLOCK**" in report_text or "VERDICT: BLOCK" in report_text:
            verdict = "BLOCK"
        elif "**Final Verdict: WARN**" in report_text or "VERDICT: WARN" in report_text:
            verdict = "WARN"
        elif "**Final Verdict: PROMOTE**" in report_text or "VERDICT: PROMOTE" in report_text:
            verdict = "PROMOTE"

        # Quick parse for issue counts
        real_issues["missing_deps"] = _extract_missing_deps(report_text)
        real_issues["port_collisions"] = _extract_port_collisions(report_text)
        real_issues["env_missing"] = []
        if "AGENT_ZERO_PATH: MISSING" in report_text:
            real_issues["env_missing"].append("AGENT_ZERO_PATH")
        if "WORKSPACE_ROOT: MISSING" in report_text:
            real_issues["env_missing"].append("WORKSPACE_ROOT")
        real_issues["python_version_wrong"] = "✗" in report_text and "3.11" in report_text
        real_issues["dotenv_missing"] = "DOTENV_NOT_LOADED" in report_text
        real_issues["path_mixing"] = "PATH_STYLE_MIXING" in report_text

        print(clr(f"  Scan verdict : {verdict}", "red" if verdict == "BLOCK" else "yellow" if verdict == "WARN" else "green"))
        print(clr(f"  Dep flags    : {len(real_issues['missing_deps'])}", "white"))
        print(clr(f"  Env missing  : {real_issues['env_missing']}", "white"))

    except Exception as e:
        state["errors"].append(f"Scout parse error: {e}")

    state["report_path"] = report_path
    state["scan_verdict"] = verdict
    state["raw_issues"] = real_issues
    state["current_phase"] = "SCOUT"
    state["completed_phases"] = state.get("completed_phases", []) + ["SCOUT"]

    print(clr("  ✓ Scout complete", "green"))
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 2: THINKER
# Role: Triage. Separate signal from noise. Classify every issue.
# Constitutional alignment: TTLG Phase 2 — Market/Technical analysis
# ─────────────────────────────────────────────────────────────────────────────

def agent_thinker(state: TTLGState) -> TTLGState:
    phase_header("PHASE 2", "THINKER — Triage & Classification", "magenta")

    raw = state["raw_issues"]

    # ── Known vendored packages — never pip install these ──
    VENDORED = {
        "CodeHelpers", "ModuleCodes", "ExpressionBases", "FunctionNodes",
        "ChildrenHavingMixins", "PythonAPICodes", "ErrorCodes",
        "ExpressionBasesGenerated", "NodeMakingHelpers", "AttributeNodesGenerated",
        "AttributeLookupNodes", "StatementBasesGenerated", "ExpressionShapeMixins",
        "_winxptheme", "win32api", "win32com", "win32con", "win32gui",
        "session", "cli", "utils",
    }

    # ── EPOS internal modules (need to exist on disk, not pip install) ──
    INTERNAL = {
        "constitutional_arbiter", "flywheel_analyst", "context_librarian",
        "agent_zero_bridge", "agent_orchestrator", "stasis", "path_utils",
        "roles", "epos_intelligence", "cascades", "tributaries", "validation",
    }

    # ── Real installable packages ──
    REAL_PACKAGES = {
        "fastapi", "uvicorn", "websockets", "python-dotenv",
        "duckduckgo_search", "langchain_openai", "browser_use",
        "pydantic", "httpx", "requests", "anthropic", "openai",
        "litellm", "langchain", "langgraph", "langchain-anthropic",
    }

    real_issues = []
    false_positives = []
    critical_count = 0
    block_count = 0

    # ── Classify dependencies ──
    for dep in raw.get("missing_deps", []):
        pkg = dep.get("pkg", "")
        files = dep.get("files", [])
        epos_files = [f for f in files if _is_epos_owned(f)]

        if pkg in VENDORED or not epos_files:
            false_positives.append({
                "type": "VENDORED_INTERNAL",
                "pkg": pkg,
                "reason": "Nuitka/Win32/stdlib internal — not pip-installable"
            })
        elif pkg in INTERNAL:
            exists = (EPOS_ROOT / f"{pkg}.py").exists()
            real_issues.append({
                "type": "INTERNAL_MODULE_MISSING" if not exists else "IMPORT_PATH_ERROR",
                "severity": "CRITICAL" if not exists else "HIGH",
                "pkg": pkg,
                "action": f"CREATE {pkg}.py or fix import path",
                "files": epos_files[:3],
            })
            if not exists:
                critical_count += 1
        elif pkg in REAL_PACKAGES or _looks_real(pkg):
            real_issues.append({
                "type": "MISSING_PACKAGE",
                "severity": "CRITICAL",
                "pkg": pkg,
                "action": f"pip install {pkg}",
                "files": epos_files[:3],
            })
            critical_count += 1
        else:
            # Unknown — flag for review
            real_issues.append({
                "type": "UNKNOWN_DEPENDENCY",
                "severity": "WARN",
                "pkg": pkg,
                "action": "Review: may be internal module or vendored package",
                "files": epos_files[:3],
            })

    # ── Env var issues (always real) ──
    for var in raw.get("env_missing", []):
        real_issues.append({
            "type": "ENV_VAR_MISSING",
            "severity": "CRITICAL",
            "var": var,
            "action": f"Add {var} to .env",
        })
        critical_count += 1

    # ── Python version (always real, cannot auto-fix) ──
    if raw.get("python_version_wrong"):
        real_issues.append({
            "type": "PYTHON_VERSION",
            "severity": "CRITICAL",
            "action": "pyenv install 3.11.9 && pyenv local 3.11.9",
            "note": "Cannot auto-fix — requires manual intervention",
        })
        block_count += 1  # This is a genuine BLOCK

    # ── Dotenv missing ──
    if raw.get("dotenv_missing"):
        real_issues.append({
            "type": "DOTENV_NOT_LOADED",
            "severity": "HIGH",
            "action": "epos_surgeon.py auto-inject load_dotenv()",
        })

    # ── Path mixing ──
    if raw.get("path_mixing"):
        real_issues.append({
            "type": "PATH_MIXING",
            "severity": "HIGH",
            "action": "epos_surgeon.py flags for human review",
        })

    triaged = {
        "real": real_issues,
        "false_positive": false_positives,
        "auto_fixable": [i for i in real_issues if i.get("type") in (
            "MISSING_PACKAGE", "ENV_VAR_MISSING", "DOTENV_NOT_LOADED"
        )],
        "needs_human": [i for i in real_issues if i.get("type") in (
            "PYTHON_VERSION", "INTERNAL_MODULE_MISSING", "PATH_MIXING", "UNKNOWN_DEPENDENCY"
        )],
    }

    print(clr(f"  Real issues       : {len(real_issues)}", "white"))
    print(clr(f"  Auto-fixable      : {len(triaged['auto_fixable'])}", "green"))
    print(clr(f"  Need human review : {len(triaged['needs_human'])}", "yellow"))
    print(clr(f"  False positives   : {len(false_positives)}", "dim"))
    print(clr(f"  Critical count    : {critical_count}", "red"))
    print(clr(f"  Block count       : {block_count}", "red"))

    state["triaged_issues"] = triaged
    state["real_issue_count"] = len(real_issues)
    state["false_positive_count"] = len(false_positives)
    state["critical_count"] = critical_count
    state["block_count"] = block_count
    state["current_phase"] = "THINKER"
    state["completed_phases"] = state.get("completed_phases", []) + ["THINKER"]

    print(clr("  ✓ Thinker complete", "green"))
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 3: GATE
# Role: Constitutional arbiter. Render GO / PIVOT / KILL verdict.
# This is the immune system. It cannot be bypassed.
# Constitutional alignment: EPOS Constitution v3.1 Governance Gate
# ─────────────────────────────────────────────────────────────────────────────

def agent_gate(state: TTLGState) -> TTLGState:
    phase_header("PHASE 3", "GOVERNANCE GATE — Constitutional Verdict", "yellow")

    block_count = state["block_count"]
    critical_count = state["critical_count"]
    auto_fixable = len(state["triaged_issues"].get("auto_fixable", []))
    needs_human = len(state["triaged_issues"].get("needs_human", []))
    scan_verdict = state["scan_verdict"]

    # ── Constitutional verdict logic ──
    # KILL: Python version wrong — nothing can run until fixed
    if block_count > 0:
        verdict = "KILL"
        rationale = (
            f"KILL: {block_count} BLOCK-level issue(s) detected. "
            f"Python version mismatch prevents any execution. "
            f"Manual intervention required before pipeline can proceed."
        )

    # GO: All issues are auto-fixable, nothing needs human
    elif critical_count == 0 and needs_human == 0:
        verdict = "GO"
        rationale = (
            f"GO: {auto_fixable} auto-fixable issues detected. "
            f"No manual intervention required. Surgeon cleared to proceed."
        )

    # PIVOT: Mix of auto-fixable and human-review items
    elif auto_fixable > 0 and needs_human > 0:
        verdict = "PIVOT"
        rationale = (
            f"PIVOT: {auto_fixable} auto-fixable + {needs_human} manual items. "
            f"Surgeon will apply auto-fixes. Human review required for remaining {needs_human} items."
        )

    # PIVOT: Only human-review items, nothing auto-fixable
    elif auto_fixable == 0 and needs_human > 0:
        verdict = "PIVOT"
        rationale = (
            f"PIVOT: {needs_human} items require human review. "
            f"No auto-fixes available. Generating human-readable action list."
        )

    # GO: Clean state
    else:
        verdict = "GO"
        rationale = "GO: No real issues detected after triage. System is constitutionally aligned."

    print(clr(f"  Gate verdict : {verdict}", "green" if verdict == "GO" else "red" if verdict == "KILL" else "yellow"))
    print(clr(f"  Rationale    : {rationale}", "white"))

    state["gate_verdict"] = verdict
    state["gate_rationale"] = rationale
    state["current_phase"] = "GATE"
    state["completed_phases"] = state.get("completed_phases", []) + ["GATE"]

    print(clr("  ✓ Gate complete", "green"))
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 4: SURGEON
# Role: Execute repairs. Auto-fix everything clearable. Flag the rest.
# Constitutional alignment: EPOS Constitution v3.1 Article I Pre-Mortem
# ─────────────────────────────────────────────────────────────────────────────

def agent_surgeon(state: TTLGState) -> TTLGState:
    phase_header("PHASE 4", "SURGEON — Surgical Repair", "green")

    dry_run = state["dry_run"]
    gate_verdict = state["gate_verdict"]
    triaged = state["triaged_issues"]
    auto_fixable = triaged.get("auto_fixable", [])

    repairs_applied = []
    repairs_failed = []
    files_patched = 0

    if gate_verdict == "KILL":
        print(clr("  ⛔ Gate verdict is KILL — Surgeon standing down.", "red"))
        print(clr("  Manual actions required:", "yellow"))
        for issue in triaged.get("needs_human", []):
            print(clr(f"    • [{issue['severity']}] {issue.get('action', issue.get('type'))}", "yellow"))
        state["repairs_applied"] = []
        state["repairs_failed"] = []
        state["files_patched"] = 0
        state["current_phase"] = "SURGEON"
        state["completed_phases"] = state.get("completed_phases", []) + ["SURGEON"]
        return state

    # ── REPAIR 1: Install missing packages ──
    pkg_issues = [i for i in auto_fixable if i["type"] == "MISSING_PACKAGE"]
    if pkg_issues:
        pkgs = list({i["pkg"] for i in pkg_issues})
        print(clr(f"  Installing {len(pkgs)} package(s)...", "dim"))
        for pkg in pkgs:
            if dry_run:
                print(clr(f"  [DRY-RUN] pip install {pkg}", "yellow"))
                repairs_applied.append({"type": "pip_install", "pkg": pkg, "status": "dry_run"})
                continue

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True, text=True, cwd=str(EPOS_ROOT)
            )
            if result.returncode == 0:
                print(clr(f"  ✓ Installed: {pkg}", "green"))
                repairs_applied.append({"type": "pip_install", "pkg": pkg, "status": "success"})
            else:
                print(clr(f"  ✗ Failed: {pkg} — {result.stderr[:100]}", "red"))
                repairs_failed.append({"type": "pip_install", "pkg": pkg, "error": result.stderr[:200]})

    # ── REPAIR 2: Fix .env missing vars ──
    env_issues = [i for i in auto_fixable if i["type"] == "ENV_VAR_MISSING"]
    if env_issues:
        env_file = EPOS_ROOT / ".env"
        env_content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""

        ENV_VALUES = {
            "AGENT_ZERO_PATH": "/mnt/c/Users/Jamie/workspace/agent-zero",
            "WORKSPACE_ROOT":  "/mnt/c/Users/Jamie/workspace",
        }

        for issue in env_issues:
            var = issue["var"]
            if var in env_content:
                print(clr(f"  ⚠ {var} already in .env — skipping", "dim"))
                continue
            val = ENV_VALUES.get(var, f"# SET {var} VALUE HERE")
            line = f"{var}={val}\n"
            if dry_run:
                print(clr(f"  [DRY-RUN] Would add to .env: {line.strip()}", "yellow"))
                repairs_applied.append({"type": "env_fix", "var": var, "status": "dry_run"})
            else:
                env_content += line
                env_file.write_text(env_content, encoding="utf-8")
                print(clr(f"  ✓ Added to .env: {line.strip()}", "green"))
                repairs_applied.append({"type": "env_fix", "var": var, "status": "success"})

    # ── REPAIR 3: Dotenv injection via epos_surgeon ──
    dotenv_issues = [i for i in auto_fixable if i["type"] == "DOTENV_NOT_LOADED"]
    if dotenv_issues:
        surgeon = EPOS_ROOT / "epos_surgeon.py"
        if surgeon.exists():
            cmd = [sys.executable, str(surgeon), ".", "--deep"]
            if dry_run:
                cmd.append("--dry-run")
            print(clr("  Running epos_surgeon for dotenv injection...", "dim"))
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(EPOS_ROOT))
            if result.returncode in (0, 1):
                # Count patched files from output
                patched = result.stdout.count("✓ PATCH") + result.stdout.count("✓ INSERT")
                files_patched += patched
                print(clr(f"  ✓ Surgeon complete — {patched} patch(es) applied", "green"))
                repairs_applied.append({"type": "dotenv_inject", "files_patched": patched, "status": "success" if not dry_run else "dry_run"})
            else:
                print(clr(f"  ✗ Surgeon failed: exit {result.returncode}", "red"))
                repairs_failed.append({"type": "dotenv_inject", "error": f"exit {result.returncode}"})
        else:
            print(clr("  ⚠ epos_surgeon.py not found — dotenv injection skipped", "yellow"))
            repairs_failed.append({"type": "dotenv_inject", "error": "epos_surgeon.py not found"})

    # ── FLAG items needing human review ──
    needs_human = triaged.get("needs_human", [])
    if needs_human:
        print()
        print(clr(f"  ⚑ {len(needs_human)} item(s) require human action:", "yellow"))
        for item in needs_human:
            print(clr(f"    [{item['severity']}] {item.get('type', '')}", "yellow"))
            print(clr(f"           Action: {item.get('action', 'See manifest')}", "cyan"))

    state["repairs_applied"] = repairs_applied
    state["repairs_failed"] = repairs_failed
    state["files_patched"] = files_patched
    state["current_phase"] = "SURGEON"
    state["completed_phases"] = state.get("completed_phases", []) + ["SURGEON"]

    print()
    print(clr(f"  Repairs applied : {len(repairs_applied)}", "green"))
    print(clr(f"  Repairs failed  : {len(repairs_failed)}", "red" if repairs_failed else "dim"))
    print(clr("  ✓ Surgeon complete", "green"))
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 5: ANALYST
# Role: Validate post-repair state. Re-scan. Measure delta.
# Constitutional alignment: TTLG Phase 5 — Verification
# ─────────────────────────────────────────────────────────────────────────────

def agent_analyst(state: TTLGState) -> TTLGState:
    phase_header("PHASE 5", "ANALYST — Post-Repair Validation", "blue")

    dry_run = state["dry_run"]
    gate_verdict = state["gate_verdict"]
    original_verdict = state["scan_verdict"]

    if dry_run:
        print(clr("  [DRY-RUN] Skipping post-scan in dry-run mode", "yellow"))
        state["post_scan_verdict"] = "DRY_RUN"
        state["improvement_delta"] = f"{original_verdict}→DRY_RUN"
        state["remaining_issues"] = state["real_issue_count"]
        state["current_phase"] = "ANALYST"
        state["completed_phases"] = state.get("completed_phases", []) + ["ANALYST"]
        return state

    if gate_verdict == "KILL":
        print(clr("  Skipping post-scan — KILL verdict requires manual intervention first", "yellow"))
        state["post_scan_verdict"] = "SKIP"
        state["improvement_delta"] = f"{original_verdict}→BLOCKED_BY_KILL"
        state["remaining_issues"] = state["real_issue_count"]
        state["current_phase"] = "ANALYST"
        state["completed_phases"] = state.get("completed_phases", []) + ["ANALYST"]
        return state

    # ── Run post-repair scan ──
    print(clr("  Running post-repair alignment scan...", "dim"))
    result = _run_tool("python epos_align_scan.py . --deep --report", cwd=EPOS_ROOT)

    # ── Find the new report ──
    reports = sorted(EPOS_ROOT.glob("epos_align_report_*.md"), reverse=True)
    post_verdict = "UNKNOWN"
    remaining = 0

    if reports:
        post_report = reports[0]
        report_text = post_report.read_text(encoding="utf-8", errors="replace")

        if "BLOCK" in report_text.split("Final Verdict:")[-1]:
            post_verdict = "BLOCK"
        elif "WARN" in report_text.split("Final Verdict:")[-1]:
            post_verdict = "WARN"
        elif "PROMOTE" in report_text.split("Final Verdict:")[-1]:
            post_verdict = "PROMOTE"

        # Count remaining real issues (rough count from CRITICAL flags)
        remaining = report_text.count("### MISSING_DEPENDENCY [CRITICAL]")
        remaining += report_text.count("### PORT_COLLISION [HIGH]")

    delta = f"{original_verdict}→{post_verdict}"
    improvement = {
        "BLOCK→PROMOTE": "FULL RESOLUTION",
        "BLOCK→WARN":    "PARTIAL RESOLUTION",
        "BLOCK→BLOCK":   "NO CHANGE",
        "WARN→PROMOTE":  "FULL RESOLUTION",
        "WARN→WARN":     "PARTIAL/NO CHANGE",
    }.get(delta, delta)

    verdict_color = "green" if "PROMOTE" in post_verdict else "yellow" if "WARN" in post_verdict else "red"
    print(clr(f"  Pre-repair  : {original_verdict}", "white"))
    print(clr(f"  Post-repair : {post_verdict}", verdict_color))
    print(clr(f"  Delta       : {improvement}", "cyan"))
    print(clr(f"  Remaining   : ~{remaining} issue flags", "white"))

    state["post_scan_verdict"] = post_verdict
    state["improvement_delta"] = delta
    state["remaining_issues"] = remaining
    state["current_phase"] = "ANALYST"
    state["completed_phases"] = state.get("completed_phases", []) + ["ANALYST"]

    print(clr("  ✓ Analyst complete", "green"))
    return state


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 6: AAR (After Action Report)
# Role: Write manifest. Log session. Seed next TTLG cycle.
# Constitutional alignment: EPOS Constitution v3.1 Audit Trail
# ─────────────────────────────────────────────────────────────────────────────

def agent_aar(state: TTLGState) -> TTLGState:
    phase_header("PHASE 6", "AAR — After Action Report", "white")

    session_id = state["session_id"]
    SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)

    # ── Build manifest ──
    manifest = {
        "session_id": session_id,
        "started_at": state["started_at"],
        "completed_at": datetime.now().isoformat(),
        "dry_run": state["dry_run"],
        "phases_completed": state.get("completed_phases", []),

        "scout": {
            "report_path": state.get("report_path"),
            "scan_verdict": state.get("scan_verdict"),
        },
        "thinker": {
            "real_issues": state.get("real_issue_count", 0),
            "false_positives": state.get("false_positive_count", 0),
            "critical": state.get("critical_count", 0),
            "blocks": state.get("block_count", 0),
        },
        "gate": {
            "verdict": state.get("gate_verdict"),
            "rationale": state.get("gate_rationale"),
        },
        "surgeon": {
            "repairs_applied": len(state.get("repairs_applied", [])),
            "repairs_failed": len(state.get("repairs_failed", [])),
            "files_patched": state.get("files_patched", 0),
            "repair_log": state.get("repairs_applied", []),
        },
        "analyst": {
            "post_verdict": state.get("post_scan_verdict"),
            "delta": state.get("improvement_delta"),
            "remaining_issues": state.get("remaining_issues", 0),
        },
        "errors": state.get("errors", []),
        "abort_reason": state.get("abort_reason"),
    }

    # ── Session summary ──
    repairs = len(state.get("repairs_applied", []))
    delta = state.get("improvement_delta", "UNKNOWN")
    gate = state.get("gate_verdict", "UNKNOWN")
    remaining = state.get("remaining_issues", 0)
    needs_human = len(state.get("triaged_issues", {}).get("needs_human", []))

    summary_lines = [
        f"TTLG Session {session_id}",
        f"Gate verdict      : {gate}",
        f"Repairs applied   : {repairs}",
        f"Alignment delta   : {delta}",
        f"Remaining issues  : {remaining}",
        f"Human review items: {needs_human}",
    ]
    if needs_human > 0:
        summary_lines.append("")
        summary_lines.append("ITEMS REQUIRING HUMAN ACTION:")
        for item in state.get("triaged_issues", {}).get("needs_human", []):
            summary_lines.append(f"  [{item.get('severity')}] {item.get('action', item.get('type'))}")

    summary = "\n".join(summary_lines)

    # ── Write files ──
    manifest_path = SESSION_LOG_DIR / f"ttlg_manifest_{session_id}.json"
    summary_path  = EPOS_ROOT / f"TTLG_SESSION_{session_id}.md"

    if not state["dry_run"]:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        summary_path.write_text(
            f"# TTLG Session Report\n\n```\n{summary}\n```\n",
            encoding="utf-8"
        )
        print(clr(f"  ✓ Manifest  : {manifest_path}", "green"))
        print(clr(f"  ✓ Summary   : {summary_path}", "green"))
    else:
        print(clr("  [DRY-RUN] Manifest would be written to ops/ttlg_sessions/", "yellow"))

    # ── Print terminal summary ──
    print()
    hr("─")
    for line in summary_lines:
        color = "red" if "KILL" in line else "yellow" if "PIVOT" in line or "WARN" in line else "green" if "GO" in line or "PROMOTE" in line else "white"
        print(clr(f"  {line}", color))
    hr("─")

    state["manifest_path"] = str(manifest_path)
    state["session_summary"] = summary
    state["current_phase"] = "AAR"
    state["completed_phases"] = state.get("completed_phases", []) + ["AAR"]

    print(clr("  ✓ AAR complete", "green"))
    return state


# ─────────────────────────────────────────────────────────────────────────────
# CONDITIONAL ROUTING — LangGraph edge logic
# ─────────────────────────────────────────────────────────────────────────────

def route_after_gate(state: TTLGState) -> str:
    """
    After Gate renders verdict:
    GO / PIVOT → proceed to Surgeon
    KILL → skip to AAR (manual action required)
    ABORT → END
    """
    if state.get("abort_reason"):
        return "aar"
    verdict = state.get("gate_verdict", "KILL")
    if verdict in ("GO", "PIVOT"):
        return "surgeon"
    return "aar"  # KILL → skip surgeon, write report immediately


def route_after_scout(state: TTLGState) -> str:
    """If scout produced no report, abort."""
    if state.get("abort_reason"):
        return "aar"
    return "thinker"


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH ASSEMBLY — wire the six agents into a LangGraph state machine
# ─────────────────────────────────────────────────────────────────────────────

def build_ttlg_graph():
    """
    Assemble the TTLG LangGraph.
    
    Flow:
      scout → thinker → gate → [surgeon | aar] → analyst → aar → END
    
    Conditional edges:
      gate → surgeon  (GO / PIVOT verdict)
      gate → aar      (KILL verdict — skip surgery)
      scout → aar     (abort if no report)
    """
    graph = StateGraph(TTLGState)

    # Register nodes
    graph.add_node("scout",   agent_scout)
    graph.add_node("thinker", agent_thinker)
    graph.add_node("gate",    agent_gate)
    graph.add_node("surgeon", agent_surgeon)
    graph.add_node("analyst", agent_analyst)
    graph.add_node("aar",     agent_aar)

    # Entry point
    graph.set_entry_point("scout")

    # Edges
    graph.add_conditional_edges("scout", route_after_scout, {
        "thinker": "thinker",
        "aar": "aar",
    })
    graph.add_edge("thinker", "gate")
    graph.add_conditional_edges("gate", route_after_gate, {
        "surgeon": "surgeon",
        "aar": "aar",
    })
    graph.add_edge("surgeon", "analyst")
    graph.add_edge("analyst", "aar")
    graph.add_edge("aar", END)

    # Memory checkpointer — enables --resume
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _run_tool(cmd: str, cwd: Path) -> dict:
    """Run a shell command, return result dict."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, cwd=str(cwd)
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


def _extract_missing_deps(report_text: str) -> list[dict]:
    import re
    deps = []
    pattern = re.compile(
        r"### MISSING_DEPENDENCY \[CRITICAL\]\n\*\*Detail:\*\* Package '([^']+)' not installed but required by: (.+?)(?=\n\n|\Z)",
        re.DOTALL
    )
    for m in pattern.finditer(report_text):
        deps.append({
            "pkg": m.group(1).strip(),
            "files": [f.strip() for f in m.group(2).strip().split(",")][:10]
        })
    return deps


def _extract_port_collisions(report_text: str) -> list[dict]:
    import re
    collisions = []
    pattern = re.compile(
        r"### PORT_COLLISION \[HIGH\]\n\*\*Detail:\*\* Port (\d+) referenced in multiple components: (.+?)(?=\n\n|\Z)",
        re.DOTALL
    )
    for m in pattern.finditer(report_text):
        collisions.append({
            "port": int(m.group(1)),
            "files": [f.strip() for f in m.group(2).strip().split(",")][:10]
        })
    return collisions


def _is_epos_owned(filename: str) -> bool:
    import re
    filename = filename.strip()
    if re.search(r'(Codes|Nodes|Mixins|Bases|Helpers|Generated)\.py$', filename):
        return False
    if filename.startswith(("win32", "Win32", "test_")):
        return False
    EPOS_PATTERNS = [
        "governance", "epos", "orchestrator", "az_dispatch", "bridge",
        "constitutional", "flywheel", "context_", "stasis", "path_utils",
        "command_center", "phi3", "phi4", "llm_client", "jarvis",
        "workflow_demo", "setup_agents", "autonomy", "audio_input",
        "brand_validator", "echolocation", "immediate_execute",
    ]
    name_lower = filename.lower()
    return any(p in name_lower for p in EPOS_PATTERNS)


def _looks_real(pkg: str) -> bool:
    if pkg[0].isupper() and "-" not in pkg and "_" not in pkg:
        return False
    if pkg.startswith("_"):
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="TTLG Agent Team — LangGraph Autonomous Diagnostic Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phases: Scout → Thinker → Gate → Surgeon → Analyst → AAR

Examples:
  python ttlg_agents.py                          # full run
  python ttlg_agents.py --dry-run                # plan only
  python ttlg_agents.py --report epos_align_report_20260322.md
  python ttlg_agents.py --phase scout            # single phase
        """
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", metavar="FILE", help="Use existing report (skip scan)")
    parser.add_argument("--phase", choices=["scout","thinker","gate","surgeon","analyst","aar"])
    parser.add_argument("--resume", metavar="SESSION_ID", help="Resume from checkpoint")
    args = parser.parse_args()

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initial state
    initial_state: TTLGState = {
        "session_id": session_id,
        "started_at": datetime.now().isoformat(),
        "dry_run": args.dry_run,
        "resume_from": args.resume,
        "current_phase": "INIT",
        "completed_phases": [],
        "report_path": args.report,
        "scan_verdict": "UNKNOWN",
        "raw_issues": {},
        "triaged_issues": {},
        "real_issue_count": 0,
        "false_positive_count": 0,
        "critical_count": 0,
        "block_count": 0,
        "gate_verdict": "UNKNOWN",
        "gate_rationale": "",
        "repairs_applied": [],
        "repairs_failed": [],
        "files_patched": 0,
        "post_scan_verdict": "UNKNOWN",
        "improvement_delta": "",
        "remaining_issues": 0,
        "manifest_path": None,
        "session_summary": "",
        "errors": [],
        "abort_reason": None,
    }

    # Build graph
    app = build_ttlg_graph()
    config = {"configurable": {"thread_id": session_id}}

    # Header
    hr("═")
    print(clr("  TTLG AGENT TEAM  —  LangGraph Autonomous Pipeline", "bold"))
    print(clr(f"  Session : {session_id}", "dim"))
    print(clr(f"  Mode    : {'DRY-RUN' if args.dry_run else 'LIVE'}", "yellow" if args.dry_run else "green"))
    print(clr(f"  Phases  : Scout → Thinker → Gate → Surgeon → Analyst → AAR", "white"))
    hr("═")

    # Run
    final_state = app.invoke(initial_state, config=config)

    # Final verdict
    print()
    hr("═")
    gate = final_state.get("gate_verdict", "UNKNOWN")
    delta = final_state.get("improvement_delta", "UNKNOWN")
    color = "green" if gate == "GO" else "red" if gate == "KILL" else "yellow"
    print(clr(f"  TTLG COMPLETE  |  Gate: {gate}  |  Delta: {delta}", color))
    hr("═")

    # Exit code for automation
    exit_codes = {"GO": 0, "PIVOT": 1, "KILL": 2, "UNKNOWN": 3}
    sys.exit(exit_codes.get(gate, 3))


if __name__ == "__main__":
    main()