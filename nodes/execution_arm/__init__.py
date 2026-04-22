# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
nodes.execution_arm — EPOS Execution Arm (four variants)

The four agents:
    browser_use.headless     browser_use.headed
    computer_use.headless    computer_use.headed

Universal entrypoint:
    from nodes.execution_arm import execute, execute_async, health

Governance:
    Deletion only with Sovereign approval. Every attempt logged.
    Callable by any component via Python call, event bus, or REST.
"""

from .browser_use_arm import BrowserUseArm
from .callable import execute, execute_async, health, install_event_bus_handler
from .computer_use_arm import ComputerUseArm
from .deletion_gate import DeletionRefused, GuardResult, enforce, guard
from .mode_selector import Selection, select

__all__ = [
    "execute",
    "execute_async",
    "health",
    "install_event_bus_handler",
    "select",
    "Selection",
    "guard",
    "enforce",
    "GuardResult",
    "DeletionRefused",
    "BrowserUseArm",
    "ComputerUseArm",
]
