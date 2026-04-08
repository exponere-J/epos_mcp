# File: ${EPOS_ROOT}/governance_gate.py
# repair_origin: human_authored
# requires_metadata_confirmation: false

"""
EPOS Governance Gate v1.0 — Constitutional Triage & Safe Repair

Constitutional Authority: EPOS_CONSTITUTION_v3.1.md Articles I, II, III, IV, VII
Purpose: Classify incoming files as PROMOTE / SAFE_REPAIR / PATCH_PROPOSE / REJECT.
         Apply deterministic mechanical repairs. Never fabricate semantic content.

Usage:
    python governance_gate.py <file_or_dir>                   # Triage + auto-repair
    python governance_gate.py <file_or_dir> --triage-only     # Classify without repair
    python governance_gate.py <file_or_dir> --propose-patch   # Generate patch file, don't apply
    python governance_gate.py <file_or_dir> --json            # Machine-readable output
    python governance_gate.py <file_or_dir> --verbose         # Show all check details

Exit Codes:
    0 = All files promoted (compliant or repaired successfully)
    1 = Some files require human review (PATCH_PROPOSE present)
    2 = Constitutional violation detected (REJECT with critical severity)

Safe Repair Lane:
    The gate auto-repairs ONLY mechanical defects where the fix is:
      - Deterministic (one correct answer, defined in constitutional docs)
      - Reversible (rollback snapshot taken before any mutation)
      - Testable (post-repair recheck confirms fix)
      - Non-destructive (never rewrites business logic or invents semantics)

    Repairable violations:
      ERR-HEADER-001  : Missing file header → insert with governance-origin provenance
      ERR-PATH-001    : Unix-style EPOS paths → normalise to Windows canonical
      ERR-CONFIG-001  : Missing load_dotenv() in entrypoint → insert after imports
      ERR-CONTEXT-001 : Inline data > 8K tokens → extract to Context Vault
      ERR-SCHEMA-002  : Missing mission JSON fields → insert placeholders

    Non-repairable violations (REJECT or PATCH_PROPOSE):
      ERR-DESTRUCT-*  : Destructive operations → REJECT, require human approval
      ERR-CONST-001   : Constitutional file modification → REJECT
      ERR-CONTEXT-002 : File is large but no clear extraction target → PATCH_PROPOSE
      ERR-PATH-002    : os.path usage → PATCH_PROPOSE (requires semantic rewrite)
      ERR-SCHEMA-001  : Invalid JSON → REJECT
"""

import sys
import os
import re
import json
import shutil
import hashlib
import argparse
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum


# ---------------------------------------------------------------------------
# Constants — derived from constitutional documents
# ---------------------------------------------------------------------------

_DEFAULT_EPOS_ROOT = str(Path(__file__).resolve().parent)
_DEFAULT_WORKSPACE = str(Path(_DEFAULT_EPOS_ROOT).parent)
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", _DEFAULT_EPOS_ROOT))
AGENT_ZERO_ROOT = Path(os.getenv("AGENT_ZERO_PATH", str(Path(_DEFAULT_WORKSPACE) / "agent-zero")))
FRIDAY_ROOT = Path(os.getenv("FRIDAY_ROOT", str(Path(_DEFAULT_WORKSPACE) / "friday")))

CONTEXT_VAULT = EPOS_ROOT / "context_vault"
INBOX = EPOS_ROOT / "inbox"
ENGINE = EPOS_ROOT / "engine"
REJECTED = EPOS_ROOT / "rejected"
RECEIPTS = REJECTED / "receipts"
ROLLBACKS = EPOS_ROOT / "ops" / "rollbacks"
LOGS = EPOS_ROOT / "ops" / "logs"

# Token proxy: 1 token ~ 4 chars.  8192 tokens ~ 32768 chars.
INLINE_TOKEN_LIMIT = 8192
INLINE_CHAR_LIMIT = INLINE_TOKEN_LIMIT * 4

# Header pattern: # File: <absolute-path>/<file>.py  (accepts / or \ separator)
HEADER_RE = re.compile(r"^#\s*File:\s*[A-Za-z]:[/\\]", re.MULTILINE)

# Entrypoint indicators (files that should call load_dotenv)
ENTRYPOINT_MARKERS = (
    "if __name__",
    "app = FastAPI",
    "app = Starlette",
    "uvicorn.run",
    "def main():",
)

# Destructive patterns → instant REJECT (Article II Rule 5)
DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b"),           "ERR-DESTRUCT-001", "rm -rf detected"),
    (re.compile(r"\bdel\s+/[sS]\b"),        "ERR-DESTRUCT-002", "del /s detected"),
    (re.compile(r"\bshutil\.rmtree\b"),      "ERR-DESTRUCT-003", "shutil.rmtree without safeguard"),
    (re.compile(r"\bformat\s+[A-Z]:"),       "ERR-DESTRUCT-004", "Disk format command detected"),
]

# Constitutional files that agents must never modify autonomously
PROTECTED_FILES = frozenset({
    "EPOS_CONSTITUTION_v3.1.md",
    "EPOS_CONSTITUTION_v3.md",
    "EPOS_CONSTITUTION.md",
    "NODE_SOVEREIGNTY_CONSTITUTION.md",
})

# Mission JSON required fields (Article III)
MISSION_REQUIRED_FIELDS = (
    "mission_id",
    "objective",
    "constraints",
    "success_criteria",
    "failure_modes",
)

# Path patterns
_UNIX_EPOS_PATH = re.compile(r"""['"]/?[Cc]/Users/Jamie/workspace/""")
_OS_PATH_USAGE = re.compile(r"\bos\.path\.(join|abspath|dirname|exists|isfile|isdir)\b")
_LOAD_DOTENV_CALL = re.compile(r"\bload_dotenv\s*\(")
_DOTENV_IMPORT = re.compile(r"from\s+dotenv\s+import\s+load_dotenv")
_LARGE_STRING = re.compile(r'"{3}[\s\S]{2000,}?"{3}|' + r"'{3}[\s\S]{2000,}?'{3}")


# ---------------------------------------------------------------------------
# Enums & Data Structures
# ---------------------------------------------------------------------------

class Verdict(str, Enum):
    PROMOTE = "PROMOTE"
    SAFE_REPAIR = "SAFE_REPAIR"
    PATCH_PROPOSE = "PATCH_PROPOSE"
    REJECT = "REJECT"


class Severity(str, Enum):
    INFO = "info"
    MECHANICAL = "mechanical"    # Deterministic fix exists
    JUDGMENT = "judgment"        # Requires human decision
    CRITICAL = "critical"        # Immediate rejection


@dataclass
class Violation:
    code: str
    article: str
    message: str
    severity: Severity
    repairable: bool
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class RepairAction:
    violation_code: str
    description: str
    before_snippet: str
    after_snippet: str


@dataclass
class TriageResult:
    filepath: str
    verdict: Verdict = Verdict.PROMOTE  # Overwritten by triage logic
    violations: List[Violation] = field(default_factory=list)
    repairs_applied: List[RepairAction] = field(default_factory=list)
    rollback_path: Optional[str] = None
    receipt_path: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["violations"] = [
            {**asdict(v), "severity": v.severity.value} for v in self.violations
        ]
        return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


GATE_JOURNAL_DIR = CONTEXT_VAULT / "governance" / "gate"


def _ensure_dirs():
    for d in (INBOX, ENGINE, REJECTED, RECEIPTS, ROLLBACKS, LOGS, GATE_JOURNAL_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _snapshot(path: Path) -> Path:
    """Rollback snapshot before any mutation.  Returns snapshot path."""
    ROLLBACKS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snap = ROLLBACKS / f"{path.stem}_{ts}{path.suffix}.rollback"
    shutil.copy2(path, snap)
    return snap


def _unified_diff(original: str, modified: str, filename: str) -> str:
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))


def _is_entrypoint(content: str) -> bool:
    return any(m in content for m in ENTRYPOINT_MARKERS)


def _token_estimate(text: str) -> int:
    return len(text) // 4


# ---------------------------------------------------------------------------
# CHECK 1: File Header  (Article III — Governance Gate Triage)
# ---------------------------------------------------------------------------

def check_header(content: str, fp: Path) -> Optional[Violation]:
    if fp.suffix != ".py":
        return None
    if HEADER_RE.search(content[:500]):
        return None
    return Violation(
        code="ERR-HEADER-001",
        article="Article III (Governance Gate Triage)",
        message="Missing mandatory file header with absolute path.",
        severity=Severity.MECHANICAL,
        repairable=True,
        line_number=1,
        suggestion=f"# File: {EPOS_ROOT.as_posix()}/{fp.name}",
    )


def repair_header(content: str, fp: Path) -> Tuple[str, RepairAction]:
    """Insert header with honest governance-origin provenance.
    Never fabricates mission_id or lead_agent metadata."""
    try:
        rel = fp.resolve().relative_to(EPOS_ROOT.resolve())
        canonical = str(EPOS_ROOT / rel).replace("/", "\\")
    except (ValueError, RuntimeError):
        canonical = str(EPOS_ROOT / fp.name).replace("/", "\\")

    block = (
        f"# File: {canonical}\n"
        f"# repair_origin: governance_gate_auto\n"
        f"# requires_metadata_confirmation: true\n"
    )

    lines = content.split("\n", 2)
    if lines and (lines[0].startswith("#!") or lines[0].startswith("# -*-")):
        repaired = lines[0] + "\n" + block + "\n".join(lines[1:])
    else:
        repaired = block + content

    return repaired, RepairAction(
        violation_code="ERR-HEADER-001",
        description="Inserted file header with governance-origin provenance marker.",
        before_snippet=content[:100],
        after_snippet=repaired[:160],
    )


# ---------------------------------------------------------------------------
# CHECK 2: Path Discipline  (Article II Rule 1 / PATH_CLARITY_RULES.md)
# ---------------------------------------------------------------------------

def check_paths(content: str, fp: Path) -> List[Violation]:
    if fp.suffix != ".py":
        return []
    violations: List[Violation] = []
    for i, line in enumerate(content.splitlines(), 1):
        if _UNIX_EPOS_PATH.search(line):
            violations.append(Violation(
                code="ERR-PATH-001",
                article="Article II Rule 1 (Path Discipline)",
                message="Unix-style EPOS path. Use Windows canonical or pathlib.",
                severity=Severity.MECHANICAL,
                repairable=True,
                line_number=i,
                suggestion="Use pathlib.Path or EPOS_ROOT / ... instead of hard-coded paths",
            ))
        if _OS_PATH_USAGE.search(line):
            violations.append(Violation(
                code="ERR-PATH-002",
                article="Article II Rule 1 (Path Discipline)",
                message="os.path usage detected. Migrate to pathlib.Path.",
                severity=Severity.JUDGMENT,
                repairable=False,
                line_number=i,
                suggestion="Replace os.path.join(a, b) with Path(a) / b",
            ))
    return violations


def repair_paths(content: str) -> Tuple[str, List[RepairAction]]:
    """Normalise Unix-style EPOS paths to forward-slash Windows canonical."""
    actions: List[RepairAction] = []

    def _fix(m):
        orig = m.group(0)
        quote = orig[0]
        inner = orig[1:].lstrip("/")
        # Ensure drive letter is uppercase with colon: c/Users → C:/Users
        if inner and inner[0].lower() == "c":
            if len(inner) > 1 and inner[1] == "/":
                inner = "C:/" + inner[2:]  # c/Users → C:/Users
            elif len(inner) > 1 and inner[1] == ":":
                inner = "C" + inner[1:]    # c:/Users → C:/Users
            else:
                inner = "C" + inner[1:]
        fixed = quote + inner
        if fixed != orig:
            actions.append(RepairAction(
                violation_code="ERR-PATH-001",
                description="Normalised Unix EPOS path to Windows canonical.",
                before_snippet=orig,
                after_snippet=fixed,
            ))
        return fixed

    repaired = _UNIX_EPOS_PATH.sub(_fix, content)
    return repaired, actions


# ---------------------------------------------------------------------------
# CHECK 3: load_dotenv Presence  (Article II Rule 6)
# ---------------------------------------------------------------------------

def check_dotenv(content: str, fp: Path) -> Optional[Violation]:
    if fp.suffix != ".py":
        return None
    if not _is_entrypoint(content):
        return None
    if _LOAD_DOTENV_CALL.search(content):
        return None
    return Violation(
        code="ERR-CONFIG-001",
        article="Article II Rule 6 (Configuration Explicitness)",
        message="Entrypoint missing explicit load_dotenv() call.",
        severity=Severity.MECHANICAL,
        repairable=True,
        line_number=1,
        suggestion="from dotenv import load_dotenv; load_dotenv(Path(__file__).parent / '.env')",
    )


def repair_dotenv(content: str) -> Tuple[str, RepairAction]:
    """Insert load_dotenv() after the imports block."""
    has_import = bool(_DOTENV_IMPORT.search(content))

    if has_import:
        insertion = "\nload_dotenv(Path(__file__).parent / '.env')\n"
    else:
        insertion = (
            "\nfrom dotenv import load_dotenv\n"
            "from pathlib import Path as _GatePath\n"
            "\n"
            "load_dotenv(_GatePath(__file__).parent / '.env')\n"
        )

    lines = content.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            insert_at = i + 1
        elif s and not s.startswith("#") and insert_at > 0:
            break

    repaired = "".join(lines[:insert_at]) + insertion + "".join(lines[insert_at:])

    return repaired, RepairAction(
        violation_code="ERR-CONFIG-001",
        description="Inserted load_dotenv() call at entrypoint.",
        before_snippet="(no load_dotenv call)",
        after_snippet=insertion.strip()[:120],
    )


# ---------------------------------------------------------------------------
# CHECK 4: Inline Data Size  (Article VII — Context Governance)
# ---------------------------------------------------------------------------

def check_inline_data(content: str, fp: Path) -> List[Violation]:
    if fp.suffix != ".py":
        return []
    violations: List[Violation] = []

    for m in _LARGE_STRING.finditer(content):
        tok = _token_estimate(m.group())
        if tok > INLINE_TOKEN_LIMIT:
            ln = content[:m.start()].count("\n") + 1
            violations.append(Violation(
                code="ERR-CONTEXT-001",
                article="Article VII (Context Governance)",
                message=f"Inline literal ~{tok} tokens (limit {INLINE_TOKEN_LIMIT}). Use Context Vault.",
                severity=Severity.MECHANICAL,
                repairable=True,
                line_number=ln,
                suggestion="Move to context_vault/mission_data/ and reference via vault path.",
            ))

    total = _token_estimate(content)
    if total > INLINE_TOKEN_LIMIT * 2 and not violations:
        violations.append(Violation(
            code="ERR-CONTEXT-002",
            article="Article VII (Context Governance)",
            message=f"File ~{total} tokens. Review for vault extraction.",
            severity=Severity.JUDGMENT,
            repairable=False,
            suggestion="Consider splitting large data into Context Vault files.",
        ))

    return violations


def repair_inline_data(content: str, fp: Path) -> Tuple[str, List[RepairAction]]:
    """Extract large string literals to Context Vault files."""
    actions: List[RepairAction] = []
    vault_dir = CONTEXT_VAULT / "mission_data"
    vault_dir.mkdir(parents=True, exist_ok=True)
    counter = [0]

    def _extract(m):
        literal = m.group()
        tok = _token_estimate(literal)
        if tok <= INLINE_TOKEN_LIMIT:
            return literal
        counter[0] += 1
        vault_name = f"{fp.stem}_extracted_{counter[0]}.txt"
        vault_path = vault_dir / vault_name
        inner = literal[3:-3]
        vault_path.write_text(inner, encoding="utf-8")
        replacement = (
            f'# AUTO-EXTRACTED by Governance Gate -> context_vault/mission_data/{vault_name}\n'
            f'    _vault_ref_{counter[0]} = "context_vault/mission_data/{vault_name}"'
        )
        actions.append(RepairAction(
            violation_code="ERR-CONTEXT-001",
            description=f"Extracted ~{tok}-token literal to {vault_path}.",
            before_snippet=literal[:60] + "...",
            after_snippet=replacement[:120],
        ))
        return replacement

    repaired = _LARGE_STRING.sub(_extract, content)
    return repaired, actions


# ---------------------------------------------------------------------------
# CHECK 5: Mission JSON Schema  (Article III)
# ---------------------------------------------------------------------------

def check_mission_schema(content: str, fp: Path) -> List[Violation]:
    if fp.suffix != ".json" or "mission" not in fp.stem.lower():
        return []
    violations: List[Violation] = []
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        violations.append(Violation(
            code="ERR-SCHEMA-001",
            article="Article III (Schema Validation)",
            message=f"Invalid JSON: {e}",
            severity=Severity.CRITICAL,
            repairable=False,
        ))
        return violations
    if not isinstance(data, dict):
        return []
    for fname in MISSION_REQUIRED_FIELDS:
        if fname not in data:
            violations.append(Violation(
                code="ERR-SCHEMA-002",
                article="Article III (Schema Validation)",
                message=f"Missing required field: '{fname}'.",
                severity=Severity.MECHANICAL,
                repairable=True,
                suggestion=f"Add '{fname}' field to mission JSON.",
            ))
    return violations


def repair_mission_schema(content: str, fp: Path) -> Tuple[str, List[RepairAction]]:
    """Add missing fields with honest placeholder values — never fabricates semantics."""
    actions: List[RepairAction] = []
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return content, actions
    if not isinstance(data, dict):
        return content, actions

    placeholders = {
        "mission_id": "PLACEHOLDER-REQUIRES-CONFIRMATION",
        "objective": "PLACEHOLDER — define objective before execution",
        "constraints": {
            "repair_origin": "governance_gate_auto",
            "requires_confirmation": True,
            "note": "Define environment, paths, and risk level.",
        },
        "success_criteria": [
            "PLACEHOLDER — define verifiable outcomes before execution"
        ],
        "failure_modes": [{
            "scenario": "PLACEHOLDER — document at least 3 failure scenarios",
            "repair_origin": "governance_gate_auto",
            "requires_confirmation": True,
        }],
    }

    for fname in MISSION_REQUIRED_FIELDS:
        if fname not in data:
            data[fname] = placeholders.get(fname, "PLACEHOLDER")
            actions.append(RepairAction(
                violation_code="ERR-SCHEMA-002",
                description=f"Added placeholder for missing field '{fname}'.",
                before_snippet=f"(field '{fname}' absent)",
                after_snippet=json.dumps({fname: data[fname]})[:120],
            ))

    return json.dumps(data, indent=2) + "\n", actions


# ---------------------------------------------------------------------------
# CHECK 6: Destructive / Constitutional Violations  (Article II Rule 5)
# ---------------------------------------------------------------------------

def check_destructive(content: str, fp: Path) -> List[Violation]:
    violations: List[Violation] = []

    if fp.name in PROTECTED_FILES:
        violations.append(Violation(
            code="ERR-CONST-001",
            article="Article VI (Autonomous Evolution Safeguards)",
            message="Constitutional file modification requires human approval.",
            severity=Severity.CRITICAL,
            repairable=False,
        ))

    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        # Skip comments, string-only lines, and regex/pattern definitions
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("'", '"', "r'", 'r"', "b'", 'b"')):
            continue
        # Skip lines that are inside tuple/list/dict literals defining patterns
        if "re.compile" in line or "ERR-DESTRUCT" in line:
            continue

        for pattern, code, desc in DESTRUCTIVE_PATTERNS:
            if pattern.search(line):
                violations.append(Violation(
                    code=code,
                    article="Article II Rule 5 (No Destructive Defaults)",
                    message=desc,
                    severity=Severity.CRITICAL,
                    repairable=False,
                    line_number=i,
                    suggestion="Remove destructive command or add backup + confirmation.",
                ))

    return violations


# ---------------------------------------------------------------------------
# TRIAGE ENGINE — the core decision loop
# ---------------------------------------------------------------------------

def triage_file(filepath: Path, mode: str = "auto-repair") -> TriageResult:
    """
    Run all checks on a single file.  Return TriageResult.

    Modes:
        "triage-only"    — classify only, never mutate
        "auto-repair"    — apply safe mechanical repairs (snapshot first)
        "propose-patch"  — write .patch file, don't apply
    """
    result = TriageResult(filepath=str(filepath))

    # --- Can we read the file? ---
    if not filepath.exists():
        result.verdict = Verdict.REJECT
        result.violations.append(Violation(
            code="ERR-IO-001", article="Article II Rule 2",
            message=f"File not found: {filepath}",
            severity=Severity.CRITICAL, repairable=False,
        ))
        return result

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        result.verdict = Verdict.REJECT
        result.violations.append(Violation(
            code="ERR-IO-002", article="Article II Rule 2",
            message=f"Cannot read file: {e}",
            severity=Severity.CRITICAL, repairable=False,
        ))
        return result

    original_content = content

    # --- CHECK 6 first: destructive / constitutional → instant REJECT ---
    destructs = check_destructive(content, filepath)
    result.violations.extend(destructs)
    if any(v.severity == Severity.CRITICAL for v in destructs):
        result.verdict = Verdict.REJECT
        _write_receipt(result)
        return result

    # --- Remaining checks ---
    header_v = check_header(content, filepath)
    if header_v:
        result.violations.append(header_v)

    path_vs = check_paths(content, filepath)
    result.violations.extend(path_vs)

    dotenv_v = check_dotenv(content, filepath)
    if dotenv_v:
        result.violations.append(dotenv_v)

    inline_vs = check_inline_data(content, filepath)
    result.violations.extend(inline_vs)

    schema_vs = check_mission_schema(content, filepath)
    result.violations.extend(schema_vs)

    # --- No violations? Promote immediately ---
    if not result.violations:
        result.verdict = Verdict.PROMOTE
        return result

    # --- Classify ---
    has_critical = any(v.severity == Severity.CRITICAL for v in result.violations)
    has_judgment = any(v.severity == Severity.JUDGMENT for v in result.violations)
    has_mechanical = any(v.severity == Severity.MECHANICAL for v in result.violations)

    if has_critical:
        result.verdict = Verdict.REJECT
        _write_receipt(result)
        return result

    if not has_mechanical:
        # Only judgment-level violations remain
        result.verdict = Verdict.PATCH_PROPOSE
        _write_receipt(result)
        return result

    # --- Mechanical violations present — attempt repair ---
    if mode == "triage-only":
        result.verdict = Verdict.SAFE_REPAIR
        _write_receipt(result)
        return result

    # Snapshot before any mutation
    rollback_path = _snapshot(filepath)
    result.rollback_path = str(rollback_path)

    # Apply repairs in deterministic order
    if header_v:
        content, action = repair_header(content, filepath)
        result.repairs_applied.append(action)

    mech_paths = [v for v in path_vs if v.code == "ERR-PATH-001"]
    if mech_paths:
        content, acts = repair_paths(content)
        result.repairs_applied.extend(acts)

    if dotenv_v:
        content, action = repair_dotenv(content)
        result.repairs_applied.append(action)

    mech_inline = [v for v in inline_vs if v.code == "ERR-CONTEXT-001"]
    if mech_inline:
        content, acts = repair_inline_data(content, filepath)
        result.repairs_applied.extend(acts)

    mech_schema = [v for v in schema_vs if v.repairable]
    if mech_schema:
        content, acts = repair_mission_schema(content, filepath)
        result.repairs_applied.extend(acts)

    # --- Write result ---
    if content != original_content:
        if mode == "propose-patch":
            patch = _unified_diff(original_content, content, filepath.name)
            patch_path = filepath.with_suffix(filepath.suffix + ".gate.patch")
            patch_path.write_text(patch, encoding="utf-8")
            result.verdict = Verdict.SAFE_REPAIR
        else:
            filepath.write_text(content, encoding="utf-8")

            # VERIFY write (Article II Rule 2: never lie about success)
            verify = filepath.read_text(encoding="utf-8")
            if verify != content:
                shutil.copy2(rollback_path, filepath)
                result.verdict = Verdict.REJECT
                result.violations.append(Violation(
                    code="ERR-IO-003", article="Article II Rule 2",
                    message="Repair write verification failed. Rolled back.",
                    severity=Severity.CRITICAL, repairable=False,
                ))
                _write_receipt(result)
                return result

            # Post-repair recheck
            remaining = _recheck(content, filepath)
            unresolved = [v for v in remaining if v.severity in (Severity.CRITICAL, Severity.JUDGMENT)]
            if unresolved:
                result.verdict = Verdict.PATCH_PROPOSE
                result.violations.extend(unresolved)
            else:
                result.verdict = Verdict.PROMOTE
    else:
        result.verdict = Verdict.PATCH_PROPOSE if has_judgment else Verdict.PROMOTE

    _write_receipt(result)
    return result


def _recheck(content: str, fp: Path) -> List[Violation]:
    """Lightweight post-repair recheck — no recursion."""
    vs: List[Violation] = []
    v = check_header(content, fp)
    if v:
        vs.append(v)
    vs.extend(check_paths(content, fp))
    v = check_dotenv(content, fp)
    if v:
        vs.append(v)
    vs.extend(check_inline_data(content, fp))
    vs.extend(check_mission_schema(content, fp))
    vs.extend(check_destructive(content, fp))
    return vs


# ---------------------------------------------------------------------------
# RECEIPT SYSTEM — educational + repair receipts
# ---------------------------------------------------------------------------

def _write_receipt(result: TriageResult):
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = Path(result.filepath).stem
    name = f"{stem}_{ts}_{result.verdict.value}.json"
    path = RECEIPTS / name

    data = {
        "governance_gate_version": "1.0",
        "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md",
        "timestamp": result.timestamp,
        "file": result.filepath,
        "verdict": result.verdict.value,
        "violations": [
            {
                "code": v.code,
                "article": v.article,
                "message": v.message,
                "severity": v.severity.value,
                "repairable": v.repairable,
                "line_number": v.line_number,
                "suggestion": v.suggestion,
            }
            for v in result.violations
        ],
        "repairs_applied": [
            {
                "violation_code": r.violation_code,
                "description": r.description,
                "before": r.before_snippet,
                "after": r.after_snippet,
            }
            for r in result.repairs_applied
        ],
        "rollback_path": result.rollback_path,
    }

    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result.receipt_path = str(path)
    except Exception:
        pass  # Receipt failure is non-fatal


# ---------------------------------------------------------------------------
# BATCH PROCESSING
# ---------------------------------------------------------------------------

def triage_directory(dirpath: Path, mode: str = "auto-repair") -> List[TriageResult]:
    results: List[TriageResult] = []
    for fp in sorted(dirpath.rglob("*")):
        if fp.suffix not in (".py", ".json"):
            continue
        if not fp.is_file():
            continue
        if ".rollback" in fp.name:
            continue
        try:
            if fp.is_relative_to(ROLLBACKS) or fp.is_relative_to(RECEIPTS):
                continue
        except (ValueError, TypeError):
            pass
        results.append(triage_file(fp, mode=mode))
    return results


# ---------------------------------------------------------------------------
# CLI OUTPUT
# ---------------------------------------------------------------------------

_SYMBOLS = {
    Verdict.PROMOTE:       "✅",
    Verdict.SAFE_REPAIR:   "🔧",
    Verdict.PATCH_PROPOSE: "📋",
    Verdict.REJECT:        "❌",
}


def _print_result(r: TriageResult, verbose: bool = False):
    sym = _SYMBOLS[r.verdict]
    name = Path(r.filepath).name
    print(f"  {sym} {r.verdict.value:14s}  {name}")

    if verbose or r.verdict in (Verdict.REJECT, Verdict.PATCH_PROPOSE):
        for v in r.violations:
            print(f"       [{v.severity.value.upper():10s}] {v.code}: {v.message}")
            if v.suggestion:
                print(f"              Fix: {v.suggestion}")

    if r.repairs_applied and verbose:
        print(f"       Repairs: {len(r.repairs_applied)}")
        for a in r.repairs_applied:
            print(f"         - {a.violation_code}: {a.description}")

    if r.rollback_path and verbose:
        print(f"       Rollback: {r.rollback_path}")


def _print_summary(results: List[TriageResult]):
    counts = {v: 0 for v in Verdict}
    for r in results:
        counts[r.verdict] += 1

    total = sum(counts.values())
    compliance = (counts[Verdict.PROMOTE] / total * 100) if total else 0

    print(f"\n{'='*60}")
    print(f"  GOVERNANCE GATE — TRIAGE SUMMARY")
    print(f"{'='*60}")
    print(f"  ✅ Promoted:       {counts[Verdict.PROMOTE]}")
    print(f"  🔧 Safe-repaired:  {counts[Verdict.SAFE_REPAIR]}")
    print(f"  📋 Patch-proposed: {counts[Verdict.PATCH_PROPOSE]}")
    print(f"  ❌ Rejected:       {counts[Verdict.REJECT]}")
    print(f"{'='*60}")
    print(f"  Compliance: {compliance:.0f}%  ({total} files)")

    if counts[Verdict.REJECT]:
        print(f"\n  ⚠️  {counts[Verdict.REJECT]} file(s) REJECTED — human review required.")
    if counts[Verdict.PATCH_PROPOSE]:
        print(f"  📋 {counts[Verdict.PATCH_PROPOSE]} file(s) need patch review.")
    print()


# ---------------------------------------------------------------------------
# PUBLIC API — for programmatic use by CLI wrappers and agents
# ---------------------------------------------------------------------------

def _publish_gate_event(event_type: str, payload: dict):
    """Publish to EPOS event bus (optional — degrades gracefully)."""
    try:
        from epos_event_bus import EPOSEventBus
        EPOSEventBus().publish(event_type, payload, source_module="governance_gate")
    except Exception:
        pass  # Sovereign — works without bus


def _journal_decision(filepath: str, verdict: str, violations: int, repairs: int):
    """Write decision to governance gate JSONL journal."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filepath": str(filepath),
        "verdict": verdict,
        "violations_count": violations,
        "repairs_count": repairs,
    }
    journal_path = GATE_JOURNAL_DIR / "decisions.jsonl"
    GATE_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(journal_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def gate_check(filepath: str, mode: str = "auto-repair") -> dict:
    """
    Public API: triage a single file programmatically.

    Args:
        filepath: Path to file to check.
        mode: "triage-only" | "auto-repair" | "propose-patch"

    Returns:
        dict with keys: verdict, violations, repairs_applied, rollback_path
    """
    _ensure_dirs()
    result = triage_file(Path(filepath), mode=mode)
    result_dict = result.to_dict()

    # Journal every decision
    _journal_decision(filepath, result.verdict.value,
                      len(result.violations), len(result.repairs_applied))

    # Publish event to bus
    event_type = {
        Verdict.PROMOTE: "governance.gate.triage",
        Verdict.SAFE_REPAIR: "governance.gate.repair",
        Verdict.PATCH_PROPOSE: "governance.gate.triage",
        Verdict.REJECT: "governance.gate.reject",
    }.get(result.verdict, "governance.gate.triage")

    _publish_gate_event(event_type, {
        "filepath": str(filepath),
        "verdict": result.verdict.value,
        "violations": len(result.violations),
        "repairs": len(result.repairs_applied),
        "mode": mode,
    })

    return result_dict


def gate_check_batch(dirpath: str, mode: str = "auto-repair") -> dict:
    """
    Public API: triage a directory programmatically.

    Returns:
        dict with keys: results (list), summary (counts)
    """
    _ensure_dirs()
    results = triage_directory(Path(dirpath), mode=mode)
    return {
        "results": [r.to_dict() for r in results],
        "summary": {
            v.value: sum(1 for r in results if r.verdict == v)
            for v in Verdict
        },
    }


# ---------------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EPOS Governance Gate v1.0 — Constitutional Triage & Safe Repair",
        epilog="Authority: EPOS_CONSTITUTION_v3.1.md | Exit: 0=pass, 1=review, 2=reject",
    )
    parser.add_argument("target", help="File or directory to triage.")
    parser.add_argument("--triage-only", action="store_true",
                        help="Classify without applying repairs.")
    parser.add_argument("--propose-patch", action="store_true",
                        help="Generate .patch files instead of applying.")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable JSON output.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed check results.")

    args = parser.parse_args()

    mode = "triage-only" if args.triage_only else (
        "propose-patch" if args.propose_patch else "auto-repair"
    )

    _ensure_dirs()
    target = Path(args.target)

    if not args.json:
        print(f"\n{'='*60}")
        print(f"  EPOS GOVERNANCE GATE v1.0")
        print(f"  Authority: EPOS_CONSTITUTION_v3.1.md")
        print(f"  Mode: {mode}")
        print(f"{'='*60}\n")

    if target.is_dir():
        results = triage_directory(target, mode=mode)
    elif target.is_file():
        results = [triage_file(target, mode=mode)]
    else:
        if args.json:
            print(json.dumps({"error": f"Target not found: {target}"}))
        else:
            print(f"  ❌ Target not found: {target}")
        sys.exit(2)

    if args.json:
        print(json.dumps({
            "governance_gate_version": "1.0",
            "mode": mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [r.to_dict() for r in results],
            "summary": {
                v.value: sum(1 for r in results if r.verdict == v)
                for v in Verdict
            },
        }, indent=2))
    else:
        for r in results:
            _print_result(r, verbose=args.verbose)
        _print_summary(results)

    has_reject = any(r.verdict == Verdict.REJECT for r in results)
    has_propose = any(r.verdict == Verdict.PATCH_PROPOSE for r in results)
    sys.exit(2 if has_reject else (1 if has_propose else 0))


class GovernanceGate:
    """
    Configurable wrapper for governance gate operations.
    Allows custom vault paths, token limits, and modes.
    """

    def __init__(self, vault_path: Optional[Path] = None,
                 token_limit: int = 8192, mode: str = "auto-repair"):
        global GATE_JOURNAL_DIR, INLINE_TOKEN_LIMIT, INLINE_CHAR_LIMIT
        self.mode = mode
        if vault_path:
            GATE_JOURNAL_DIR = Path(vault_path)
        INLINE_TOKEN_LIMIT = token_limit
        INLINE_CHAR_LIMIT = token_limit * 4
        _ensure_dirs()

    def check(self, filepath: str) -> dict:
        return gate_check(filepath, mode=self.mode)

    def check_batch(self, dirpath: str) -> dict:
        return gate_check_batch(dirpath, mode=self.mode)

    def get_journal(self, limit: int = 50) -> list:
        journal_path = GATE_JOURNAL_DIR / "decisions.jsonl"
        if not journal_path.exists():
            return []
        lines = journal_path.read_text(encoding="utf-8").splitlines()
        entries = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return entries


if __name__ == "__main__":
    # Self-test when run directly without CLI args
    if len(sys.argv) < 2:
        import tempfile
        _ensure_dirs()
        passed = 0

        # Test 1: file with missing header should get SAFE_REPAIR
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                          dir=str(EPOS_ROOT)) as f:
            f.write("# no governance header\nprint('hello')\n")
            test_file = f.name
        try:
            result = gate_check(test_file, mode="auto-repair")
            assert result["verdict"] in ("SAFE_REPAIR", "PROMOTE"), \
                f"Expected repair/promote, got {result['verdict']}"
            passed += 1
        finally:
            Path(test_file).unlink(missing_ok=True)

        # Test 2: compliant file should PROMOTE
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                          dir=str(EPOS_ROOT)) as f:
            f.write(f"# File: {f.name}\n# repair_origin: human_authored\n"
                    f"# requires_metadata_confirmation: false\n\nprint('ok')\n")
            test_file2 = f.name
        try:
            result2 = gate_check(test_file2, mode="triage-only")
            assert result2["verdict"] == "PROMOTE", \
                f"Expected PROMOTE, got {result2['verdict']}"
            passed += 1
        finally:
            Path(test_file2).unlink(missing_ok=True)

        # Test 3: GovernanceGate class instantiates
        gate = GovernanceGate()
        assert hasattr(gate, "check"), "Missing check method"
        assert hasattr(gate, "check_batch"), "Missing check_batch method"
        assert hasattr(gate, "get_journal"), "Missing get_journal method"
        passed += 1

        # Test 4: Journal was written
        journal = gate.get_journal(limit=5)
        assert len(journal) > 0, "Journal should have entries from tests above"
        passed += 1

        print(f"PASS: governance_gate ({passed} assertions)")
    else:
        main()
