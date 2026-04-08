# EPOS GOVERNANCE WATERMARK
# Constitutional Authority: EPOS Constitution v3.1, Article XIV
# Governed: True
"""
engine.enforcement.governance_gate — Re-export for sovereignty certification.

The canonical implementation lives at the EPOS root (governance_gate.py).
This module makes it importable as engine.enforcement.governance_gate.
"""

import sys
from pathlib import Path

# Add EPOS root to path so we can import the canonical module
_epos_root = Path(__file__).resolve().parent.parent.parent
if str(_epos_root) not in sys.path:
    sys.path.insert(0, str(_epos_root))

# Re-export everything from the canonical module
from governance_gate import (  # noqa: E402, F401
    GovernanceGate,
    gate_check,
    gate_check_batch,
    Verdict,
    Severity,
    Violation,
    RepairAction,
    TriageResult,
)
