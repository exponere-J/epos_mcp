# EPOS Artifact — MiroFish (Simulator) Stage 1
# Constitutional Authority: Articles V, X, XVI §2
"""
nodes.simulation — MiroFish Simulation Engine (client-side)

Host-side Python interface to the MiroFish Docker sidecar. Council members
submit Scenario objects; the sidecar runs the swarm; results come back as
structured reports.
"""
from .avatars import AVATARS, Avatar
from .scenario import Scenario, Product
from .mirofish_client import MiroFishClient, submit, health

__all__ = [
    "AVATARS", "Avatar",
    "Scenario", "Product",
    "MiroFishClient", "submit", "health",
]
