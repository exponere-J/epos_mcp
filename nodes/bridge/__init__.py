"""
nodes.bridge — The Sandbox ↔ WSL Bridge Runtime

Ratified under the Bridge Protocol (2026-04-22).
Sandbox-sovereign Architect pushes artifacts to the scoped GitHub remote;
WSL-local Agent Zero pulls them and routes each new file to its correct
organism component via the ingestion runner.
"""
from .ingestion_runner import IngestionRunner, run_once
from .persona_reloader import reload_architect_persona
from .directive_queue import queue_directive

__all__ = [
    "IngestionRunner",
    "run_once",
    "reload_architect_persona",
    "queue_directive",
]
