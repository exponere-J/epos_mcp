# EPOS GOVERNANCE WATERMARK
# Constitutional Authority: EPOS Constitution v3.1, Article XIV
# Governed: True
"""
engine.governance_gate — Re-export for sovereignty certification.

The canonical implementation lives at the EPOS root (governance_gate.py).
This module makes it importable as engine.governance_gate.
"""

import sys
from pathlib import Path

_epos_root = Path(__file__).resolve().parent.parent
if str(_epos_root) not in sys.path:
    sys.path.insert(0, str(_epos_root))

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
