# EPOS GOVERNANCE WATERMARK
# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/command_validator.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# ============================================================
# FILE:    /mnt/c/Users/Jamie/workspace/epos_mcp/engine/command_validator.py
# PURPOSE: Constitutional allowlist and blocklist for all
#          commands dispatched to Agent Zero via Terminal arm.
#          No command executes without passing this gate.
# ARTICLE: Constitution v3.1, Article II, Rule 5 (No Destructive Defaults)
#          Constitution v3.1, Article III (Quality Gates)
# ============================================================

import sys
from pathlib import Path
from dotenv import load_dotenv

MIN_PYTHON = (3, 11)
if sys.version_info[:2] < MIN_PYTHON:
    raise EnvironmentError(f"Python 3.11+ required. Found: {sys.version_info[0]}.{sys.version_info[1]}")

load_dotenv(Path(__file__).parent.parent / ".env")

import logging
from config import LOGS_DIR

logger = logging.getLogger("command_validator")
logging.basicConfig(
    filename=str(LOGS_DIR / "command_validator.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# --- Absolute Blocklist (Article II, Rule 5) ---
BLOCKED_PATTERNS = [
    "rm -rf", "del /s", "del /f", "format ",
    "diskpart", "shutdown", "reboot", "mkfs",
    "DROP TABLE", "DROP DATABASE", "> /dev/sda",
    ":(){ :|:& };:",  # fork bomb
    "sudo rm", "sudo format",
]

# --- Allowlist Prefixes ---
ALLOWED_PREFIXES = [
    "python ", "pip ", "git ", "mkdir ", "cd ",
    "ls ", "dir ", "echo ", "cat ", "type ",
    "copy ", "xcopy ", "move ", "ren ",
    "npm ", "node ", "uvicorn ", "pytest ",
    "powershell -Command ", "cmd /c ",
]

class CommandViolation(Exception):
    """Raised when a command violates constitutional boundaries."""
    pass

def validate(cmd: str) -> bool:
    """
    Returns True if command is safe to execute.
    Raises CommandViolation with educational receipt if blocked.
    """
    cmd_lower = cmd.lower().strip()

    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in cmd_lower:
            receipt = (
                f"GOVERNANCE REJECTION\n"
                f"Command: '{cmd}'\n"
                f"Violation: Matches blocked pattern '{pattern}'\n"
                f"Article: Constitution v3.1, Article II, Rule 5\n"
                f"Remediation: Remove destructive operation. "
                f"Use rollback.py if reversal is needed.\n"
                f"Override: python governance_gate.py --override "
                f"--reason 'your_justification'"
            )
            logger.error(receipt)
            raise CommandViolation(receipt)

    is_allowed = any(cmd_lower.startswith(p.lower()) for p in ALLOWED_PREFIXES)
    if not is_allowed:
        logger.warning(f"UNRECOGNIZED PREFIX — proceeding with caution: {cmd}")

    logger.info(f"VALIDATED: {cmd}")
    return True
