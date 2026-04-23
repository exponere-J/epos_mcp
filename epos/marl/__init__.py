# EPOS Artifact — Multi-Agent RL (MARL)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""epos.marl — centralized MARL hub + agentic dispatcher."""
from .hub import MARLHub, submit_observation, get_policy
from .dispatcher import AgenticDispatcher, dispatch

__all__ = ["MARLHub", "submit_observation", "get_policy",
           "AgenticDispatcher", "dispatch"]
