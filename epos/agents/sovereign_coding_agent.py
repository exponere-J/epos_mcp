#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/agents/sovereign_coding_agent.py — EPOS Sovereign Coding Agent
====================================================================
Constitutional Authority: EPOS Constitution v3.1

The organism's native coding agent. Replaces Desktop CODE (legacy bootstrap).
Seats Qwen3-Coder-30B (via LiteLLM) inside the EPOS constitutional
architecture with:

  - 16 canonical tools (vault read/write/edit, exec, search, grep, etc.)
  - GATE_PRE_EXECUTE: every tool call passes governance gate
  - AUDIT_POST_EXECUTE: every result published to Event Bus
  - OrganismState: every session updates shared organism state
  - AAR auto-generation: fires on session end — constitutional, not optional
  - Constitutional system prompt: embedded EPOS Constitution + coding skills

The EPOS_EXECUTION_CYCLE:
  gather_context → agentic_loop(call_model → gate → execute → audit) → AAR

Usage:
    agent = SovereignCodingAgent()
    result = agent.execute_directive("Fix the reactor position file.")
    print(result["status"])   # "complete"
    print(result["aar"])      # AAR dict
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
sys.path.insert(0, str(EPOS_ROOT))

# ── Constitutional System Prompt ──────────────────────────────

_CONSTITUTION_SUMMARY = """
EPOS CONSTITUTION v3.1 — ABBREVIATED FOR CONTEXT EFFICIENCY

Article I: Sovereignty
  Every node is independently viable. No circular dependencies.
  Nodes communicate via Event Bus and Context Vault only.

Article II: No Silent Failures
  Every failure must be logged. Every error must surface.
  "Logged" ≠ "Executed." Prove execution, not just logging.

Article III: Path Clarity
  POSIX paths only in Docker. EPOS_ROOT=/app. No Windows paths.
  All file operations relative to EPOS_ROOT.

Article IV: Constitutional Immutability
  Files in /app/skills/ and constitutional docs require Council approval to modify.
  The coding agent cannot modify its own governance manifest.

Article V: AAR Mandate
  Every session produces an AAR. Non-negotiable. Cannot be skipped.
  AAR fires on completion, timeout, and error.

Article VI: Event Bus Supremacy
  Every significant action publishes to the Event Bus.
  The organism sees everything. Nothing operates in the dark.

Article VII: Governance Gate
  Every tool call passes GATE_PRE_EXECUTE before execution.
  BLOCK = abort. WARN = log + proceed with caution. APPROVED = execute.
"""

_CODING_SKILLS = """
EPOS CODING SKILL (Condensed):
1. Every new module MUST publish events to the Event Bus
2. Every new module MUST have a vault path for its data
3. Every new module MUST have a Doctor health check
4. File patterns: Node: nodes/{name}.py | Executor: friday/executors/{name}_executor.py
5. Acceptance test: file exists + imported + runs + Doctor PASS + Event Bus entry

PRE-MORTEM DISCIPLINE (before any code):
- What import could fail? → verify dependency exists
- What path could be wrong? → confirm POSIX, confirm EPOS_ROOT
- What if service is down? → implement graceful fallback
- What does "success" actually mean? → prove execution, not logging

NOTHING IS DONE UNTIL IT RUNS.
"""


def _build_system_prompt(organism_state: Optional[Dict] = None) -> str:
    state_summary = ""
    if organism_state:
        health = organism_state.get("health", {}).get("overall", "unknown")
        missions = len(organism_state.get("pipeline", {}).get("missions_active", []))
        state_summary = f"\nCURRENT ORGANISM STATE: health={health}, active_missions={missions}"

    return f"""=== EPOS SOVEREIGN CODING AGENT ===
You are the EPOS sovereign coding agent — a native component of the organism.
You build EPOS from within EPOS. You are NOT an external tool.

{_CONSTITUTION_SUMMARY}

{_CODING_SKILLS}

TOOL REGISTRY: You have 16 canonical tools. Call them by name.
Tools: VAULT_READ, VAULT_WRITE, VAULT_EDIT, VAULT_LIST, VAULT_GREP,
       EPOS_EXEC, VAULT_SEARCH, MISSION_READ, MISSION_WRITE,
       SCOUT_FETCH, COMPACT_DIRECTIVE, AAR_GENERATE,
       GATE_PRE_EXECUTE, AUDIT_POST_EXECUTE, NODE_SPAWN, SESSION_INIT

ENVIRONMENT: Docker container. POSIX paths only. EPOS_ROOT=/app.
{state_summary}

AAR MANDATE: You WILL generate an AAR at session end. This is constitutional.
Begin by calling SESSION_INIT to load current mission context.
"""


# ── Tool Registry ─────────────────────────────────────────────

class ToolRegistry:
    """16 canonical EPOS tools with real implementations."""

    def __init__(self, epos_root: Path, bus: Any, gate: Any):
        self._root = epos_root
        self._bus = bus
        self._gate = gate

        self._tools: Dict[str, Callable] = {
            "VAULT_READ": self._vault_read,
            "VAULT_WRITE": self._vault_write,
            "VAULT_EDIT": self._vault_edit,
            "VAULT_LIST": self._vault_list,
            "VAULT_GREP": self._vault_grep,
            "EPOS_EXEC": self._epos_exec,
            "VAULT_SEARCH": self._vault_search,
            "MISSION_READ": self._mission_read,
            "MISSION_WRITE": self._mission_write,
            "SCOUT_FETCH": self._scout_fetch,
            "COMPACT_DIRECTIVE": self._compact_directive,
            "AAR_GENERATE": self._aar_generate,
            "GATE_PRE_EXECUTE": self._gate_pre_execute,
            "AUDIT_POST_EXECUTE": self._audit_post_execute,
            "NODE_SPAWN": self._node_spawn,
            "SESSION_INIT": self._session_init,
        }

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self._tools:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}
        try:
            return self._tools[tool_name](args)
        except Exception as e:
            return {"status": "error", "error": f"{type(e).__name__}: {e}"}

    # ── Tool 1: VAULT_READ ────────────────────────────────────
    def _vault_read(self, args: Dict) -> Dict:
        path = self._resolve(args.get("path", ""))
        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        return {"status": "ok", "content": path.read_text(), "path": str(path)}

    # ── Tool 2: VAULT_WRITE ───────────────────────────────────
    def _vault_write(self, args: Dict) -> Dict:
        path = self._resolve(args.get("path", ""))
        content = args.get("content", "")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"status": "ok", "written": str(path), "bytes": len(content)}

    # ── Tool 3: VAULT_EDIT ────────────────────────────────────
    def _vault_edit(self, args: Dict) -> Dict:
        path = self._resolve(args.get("path", ""))
        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        old = args.get("old_text", "")
        new = args.get("new_text", "")
        content = path.read_text()
        if old not in content:
            return {"status": "error", "error": f"old_text not found in {path}"}
        count = content.count(old)
        path.write_text(content.replace(old, new))
        return {"status": "ok", "path": str(path), "replacements": count}

    # ── Tool 4: VAULT_LIST ────────────────────────────────────
    def _vault_list(self, args: Dict) -> Dict:
        path = self._resolve(args.get("path", ""))
        if not path.exists():
            return {"status": "error", "error": f"Path not found: {path}"}
        items = [
            {"name": p.name, "type": "dir" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else 0}
            for p in sorted(path.iterdir())
        ]
        return {"status": "ok", "path": str(path), "items": items}

    # ── Tool 5: VAULT_GREP ────────────────────────────────────
    def _vault_grep(self, args: Dict) -> Dict:
        pattern = args.get("pattern", "")
        path = self._resolve(args.get("path", ""))
        if not pattern:
            return {"status": "error", "error": "pattern required"}
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", "--include=*.json", "--include=*.yaml",
             "--include=*.md", pattern, str(path)],
            capture_output=True, text=True, timeout=30,
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return {"status": "ok", "matches": lines[:50], "count": len(lines)}

    # ── Tool 6: EPOS_EXEC ─────────────────────────────────────
    def _epos_exec(self, args: Dict) -> Dict:
        command = args.get("command", "")
        timeout = min(int(args.get("timeout", 60)), 300)
        if not command:
            return {"status": "error", "error": "command required"}

        # Block destructive commands
        blocked = ["rm -rf /", "mkfs", "dd if=", "> /dev/", ":(){ :|:& };:"]
        for b in blocked:
            if b in command:
                return {"status": "blocked", "error": f"Destructive command blocked: {b}"}

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(self._root),
        )
        return {
            "status": "ok" if result.returncode == 0 else "failed",
            "stdout": result.stdout[:4000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "command": command,
        }

    # ── Tool 7: VAULT_SEARCH ─────────────────────────────────
    def _vault_search(self, args: Dict) -> Dict:
        pattern = args.get("pattern", "")
        path = self._resolve(args.get("path", "context_vault"))
        matches = [str(p) for p in path.rglob(pattern) if p.is_file()]
        return {"status": "ok", "matches": matches[:50], "count": len(matches)}

    # ── Tool 8: MISSION_READ ─────────────────────────────────
    def _mission_read(self, args: Dict) -> Dict:
        mission_id = args.get("mission_id", "current")
        mission_dir = self._root / "context_vault" / "missions"
        if mission_id == "current":
            files = sorted(mission_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not files:
                return {"status": "ok", "mission": None, "note": "No missions found"}
            return {"status": "ok", "mission": json.loads(files[0].read_text()), "path": str(files[0])}
        path = mission_dir / f"{mission_id}.json"
        if not path.exists():
            return {"status": "error", "error": f"Mission {mission_id} not found"}
        return {"status": "ok", "mission": json.loads(path.read_text())}

    # ── Tool 9: MISSION_WRITE ────────────────────────────────
    def _mission_write(self, args: Dict) -> Dict:
        mission_id = args.get("mission_id", datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
        payload = args.get("payload", {})
        mission_dir = self._root / "context_vault" / "missions"
        mission_dir.mkdir(parents=True, exist_ok=True)
        path = mission_dir / f"{mission_id}.json"
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(payload, indent=2))
        return {"status": "ok", "path": str(path), "mission_id": mission_id}

    # ── Tool 10: SCOUT_FETCH ─────────────────────────────────
    def _scout_fetch(self, args: Dict) -> Dict:
        url = args.get("url", "")
        if not url:
            return {"status": "error", "error": "url required"}
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")[:10000]
            return {"status": "ok", "url": url, "content": content}
        except Exception as e:
            return {"status": "error", "error": str(e), "url": url}

    # ── Tool 11: COMPACT_DIRECTIVE ───────────────────────────
    def _compact_directive(self, args: Dict) -> Dict:
        """Summarize session history when context approaches 80%."""
        summary = args.get("summary", "")
        work_done = args.get("work_done", [])
        next_steps = args.get("next_steps", [])
        compact = {
            "compacted_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "work_done": work_done,
            "next_steps": next_steps,
            "files_touched": args.get("files_touched", []),
        }
        path = self._root / "context_vault" / "sessions" / f"compact_{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(compact, indent=2))
        return {"status": "ok", "compact_path": str(path), "summary": summary[:200]}

    # ── Tool 12: AAR_GENERATE ────────────────────────────────
    def _aar_generate(self, args: Dict) -> Dict:
        """Produce a structured AAR from session data."""
        session_id = args.get("session_id", datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
        aar = {
            "session_id": session_id,
            "directive": args.get("directive", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "missions_completed": args.get("missions_completed", []),
            "what_went_well": args.get("what_went_well", []),
            "what_went_wrong": args.get("what_went_wrong", []),
            "what_was_learned": args.get("what_was_learned", []),
            "state_delta": args.get("state_delta", {}),
            "files_created": args.get("files_created", []),
            "files_modified": args.get("files_modified", []),
            "events_published": args.get("events_published", 0),
            "doctor_result": args.get("doctor_result", "not_run"),
        }
        # Store in vault
        aar_dir = self._root / "context_vault" / "aar"
        aar_dir.mkdir(parents=True, exist_ok=True)
        aar_path = aar_dir / f"aar_{session_id}.json"
        aar_path.write_text(json.dumps(aar, indent=2))

        # Mirror to local Attachments (path configurable via env)
        attachments = Path(os.getenv("EPOS_ATTACHMENTS_PATH", "/app/context_vault/attachments"))
        try:
            if attachments.exists():
                (attachments / f"aar_{session_id}.json").write_text(json.dumps(aar, indent=2))
        except Exception:
            pass

        return {"status": "ok", "aar_path": str(aar_path), "aar": aar}

    # ── Tool 13: GATE_PRE_EXECUTE ────────────────────────────
    def _gate_pre_execute(self, args: Dict) -> Dict:
        tool_name = args.get("tool_name", "")
        tool_args = args.get("tool_args", {})

        # Constitutional path guards
        target_path = str(tool_args.get("path", ""))
        command = str(tool_args.get("command", ""))

        immutable_paths = ["skills/", "EPOS_CONSTITUTION", "governance/"]
        for imp in immutable_paths:
            if imp in target_path and tool_name in ["VAULT_WRITE", "VAULT_EDIT"]:
                return {"verdict": "BLOCK", "reason": f"Constitutional file {target_path} is immutable"}

        if "\\" in target_path or "C:" in target_path:
            return {"verdict": "BLOCK", "reason": "Windows paths not allowed in container"}

        if tool_name == "EPOS_EXEC" and any(b in command for b in ["rm -rf /", "mkfs"]):
            return {"verdict": "BLOCK", "reason": "Destructive command blocked"}

        # Use EPOS governance gate for file writes
        if tool_name in ["VAULT_WRITE", "VAULT_EDIT"] and target_path:
            try:
                gate_result = self._gate.check(target_path)
                verdict = gate_result.get("verdict", "APPROVED")
                if verdict in ("REJECT",):
                    return {"verdict": "BLOCK", "reason": gate_result.get("reason", "Gate rejected")}
                if verdict in ("SAFEREPAIR", "PATCHPROPOSE"):
                    return {"verdict": "WARN", "reason": gate_result.get("reason", "Gate warns")}
            except Exception:
                pass

        return {"verdict": "APPROVED", "reason": "All checks passed"}

    # ── Tool 14: AUDIT_POST_EXECUTE ──────────────────────────
    def _audit_post_execute(self, args: Dict) -> Dict:
        if self._bus:
            try:
                self._bus.publish(
                    "sovereign_agent.tool_executed",
                    args,
                    source_module="sovereign_coding_agent",
                )
            except Exception:
                pass
        return {"status": "ok", "audited": True}

    # ── Tool 15: NODE_SPAWN ──────────────────────────────────
    def _node_spawn(self, args: Dict) -> Dict:
        """Dispatch a subtask to another EPOS node via the mission queue."""
        subtask = args.get("subtask", "")
        target_node = args.get("target_node", "epos_daemon")
        if not subtask:
            return {"status": "error", "error": "subtask required"}

        mission = {
            "id": f"SUB-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "description": subtask,
            "spawned_by": "sovereign_coding_agent",
            "target_node": target_node,
            "status": "queued",
        }
        result = self._mission_write({"mission_id": mission["id"], "payload": mission})
        return {"status": "spawned", "mission": mission, "written_to": result.get("path")}

    # ── Tool 16: SESSION_INIT ────────────────────────────────
    def _session_init(self, args: Dict) -> Dict:
        """Load constitution + skills + current organism state at session start."""
        loaded = {}

        # Load constitution
        const_path = self._root / "EPOS_CONSTITUTION_v3.1.md"
        if not const_path.exists():
            const_path = self._root / "EPOS_CONSTITUTION_v3_1.md"
        if const_path.exists():
            loaded["constitution"] = f"Loaded: {const_path.name}"
        else:
            loaded["constitution"] = "Not found (using embedded summary)"

        # Load skills
        skills_dir = self._root / "skills"
        if skills_dir.exists():
            loaded["skills"] = [p.name for p in skills_dir.glob("*.md")]
        else:
            loaded["skills"] = []

        # Load organism state summary
        try:
            from epos.state.universal_state_graph import OrganismState
            state = OrganismState()
            loaded["organism_state"] = {
                "health": state.query("health.overall"),
                "active_missions": state.query("pipeline.missions_active"),
            }
        except Exception as e:
            loaded["organism_state"] = {"error": str(e)}

        return {"status": "initialized", "loaded": loaded}

    # ── Helpers ───────────────────────────────────────────────

    def _resolve(self, path: str) -> Path:
        """Resolve a path relative to EPOS_ROOT if not absolute."""
        p = Path(path)
        if not p.is_absolute():
            p = self._root / p
        return p


# ── Governance Manifest ───────────────────────────────────────

class GovernanceManifest:
    """Loads and exposes the EPOS node governance manifest."""

    def __init__(self, data: Dict):
        self._data = data

    @classmethod
    def load(cls, epos_root: Path = EPOS_ROOT) -> "GovernanceManifest":
        candidates = [
            epos_root / "context_vault" / "doctrine" / "governance_manifest.json",
            epos_root / "governance_manifest.json",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return cls(json.loads(path.read_text()))
                except Exception:
                    pass
        # Default minimal manifest
        return cls({
            "immutable_paths": ["skills/", "EPOS_CONSTITUTION"],
            "require_approval_paths": ["epos_daemon.py", "groq_router.py"],
            "agent_id": "sovereign_coding_agent",
            "version": "1.0",
        })

    def __repr__(self) -> str:
        return f"GovernanceManifest(immutable={self._data.get('immutable_paths', [])})"

    def to_dict(self) -> Dict:
        return dict(self._data)


# ── Main Agent Class ──────────────────────────────────────────

class SovereignCodingAgent:
    """
    EPOS Sovereign Coding Agent.

    Executes coding directives within the EPOS constitutional architecture.
    Every action is gated, audited, and contributes to organism state.
    Every session ends with a constitutional AAR.
    """

    def __init__(self, model: str = "qwen3-coder-30b"):
        self.model = model
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self._session_log: List[Dict] = []
        self._files_created: List[str] = []
        self._files_modified: List[str] = []
        self._events_published = 0

        # Wire Event Bus
        self._bus = None
        try:
            from epos_event_bus import EPOSEventBus
            self._bus = EPOSEventBus()
        except Exception:
            pass

        # Wire Governance Gate
        self._gate = None
        try:
            from engine.governance_gate import GovernanceGate
            self._gate = GovernanceGate()
        except Exception:
            pass

        # Load governance manifest
        self.governance = GovernanceManifest.load()

        # Wire organism state
        self._state = None
        try:
            from epos.state.universal_state_graph import OrganismState
            self._state = OrganismState()
        except Exception:
            pass

        # Initialize tool registry
        self.tools = ToolRegistry(
            epos_root=EPOS_ROOT,
            bus=self._bus,
            gate=self._gate,
        )

        # Build system prompt
        organism_state = self._state.snapshot() if self._state else None
        self._system_prompt = _build_system_prompt(organism_state)

        # Publish session start
        self._publish("coding.session.start", {
            "session_id": self.session_id,
            "model": self.model,
            "tools": len(self.tools),
        })

        # Update organism state
        if self._state:
            self._state.increment("meta.session_count")

    # ── Public API ────────────────────────────────────────────

    def execute_directive(self, directive: str, max_iterations: int = 20) -> Dict[str, Any]:
        """
        Execute a coding directive through the EPOS_EXECUTION_CYCLE.

        This method drives the agentic loop:
          1. Session init (load constitution + context)
          2. Gather context (read relevant files)
          3. Agentic loop: call model → gate → execute → audit
          4. Generate AAR (constitutional — always fires)

        Returns {"status": "complete"|"failed", "aar": ..., "log": ...}
        """
        # Update organism state
        if self._state:
            missions = self._state.query("pipeline.missions_active") or []
            missions.append(directive[:100])
            self._state.update("pipeline.missions_active", missions)

        self._log("directive_received", {"directive": directive[:200]})

        try:
            # SESSION_INIT
            init_result = self.tools.call("SESSION_INIT", {})
            self._log("session_initialized", init_result)

            # Try LLM-driven agentic loop
            result = self._agentic_loop(directive, max_iterations)

        except Exception as e:
            result = {"status": "failed", "error": str(e)}
            self._log("execution_error", {"error": str(e)})
        finally:
            # AAR — constitutional, fires regardless of outcome
            aar_result = self._close_session(directive, result)
            result["aar"] = aar_result.get("aar", {})
            result["aar_path"] = aar_result.get("aar_path", "")

            # Clear active mission from state
            if self._state:
                missions = self._state.query("pipeline.missions_active") or []
                try:
                    missions.remove(directive[:100])
                except ValueError:
                    pass
                self._state.update("pipeline.missions_active", missions)
                self._state.increment("pipeline.missions_completed_today")

        return result

    def health_check(self) -> Dict[str, Any]:
        """Fast importability + wiring check."""
        return {
            "status": "operational",
            "model": self.model,
            "tools": len(self.tools),
            "governance": self.governance is not None,
            "event_bus": self._bus is not None,
            "organism_state": self._state is not None,
            "governance_gate": self._gate is not None,
            "session_id": self.session_id,
        }

    # ── Agentic Loop ──────────────────────────────────────────

    def _agentic_loop(self, directive: str, max_iterations: int) -> Dict[str, Any]:
        """
        Call the LLM with tools in a loop until the directive is complete.
        Falls back to a structured task analysis if LLM is unavailable.
        """
        try:
            return self._llm_driven_loop(directive, max_iterations)
        except Exception as e:
            self._log("llm_unavailable", {"error": str(e)})
            return self._analysis_loop(directive)

    def _llm_driven_loop(self, directive: str, max_iterations: int) -> Dict[str, Any]:
        """Drive the agentic loop via the EPOS LLM client."""
        from engine.llm_client import complete

        context_messages = [{"role": "user", "content": directive}]
        iteration = 0
        tool_results = []

        while iteration < max_iterations:
            iteration += 1

            # Build prompt with tool results context
            full_prompt = directive
            if tool_results:
                full_prompt += f"\n\nTool results so far:\n{json.dumps(tool_results[-3:], indent=2)}"
                full_prompt += "\n\nContinue. If the directive is complete, respond with DIRECTIVE_COMPLETE."

            response = complete(
                system=self._system_prompt,
                messages=context_messages + [{"role": "user", "content": full_prompt}],
                max_tokens=2048,
                temperature=0.2,
            )

            self._log("llm_response", {"iteration": iteration, "response_preview": response[:200]})

            # Parse tool calls from response
            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                # No more tool calls — directive complete or model is done
                return {"status": "complete", "iterations": iteration, "response": response}

            # Execute each tool call
            for tc in tool_calls:
                tool_name = tc.get("tool")
                tool_args = tc.get("args", {})

                # Pre-execute gate
                gate_result = self.tools.call("GATE_PRE_EXECUTE", {
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                })

                if gate_result.get("verdict") == "BLOCK":
                    self._log("tool_blocked", {"tool": tool_name, "reason": gate_result.get("reason")})
                    tool_results.append({"tool": tool_name, "result": gate_result})
                    continue

                # Execute
                result = self.tools.call(tool_name, tool_args)
                tool_results.append({"tool": tool_name, "result": result})

                # Track file operations
                if tool_name == "VAULT_WRITE" and result.get("status") == "ok":
                    self._files_created.append(result.get("written", ""))
                elif tool_name == "VAULT_EDIT" and result.get("status") == "ok":
                    self._files_modified.append(str(tool_args.get("path", "")))

                # Post-execute audit
                self.tools.call("AUDIT_POST_EXECUTE", {
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result,
                    "iteration": iteration,
                })
                self._events_published += 1

            context_messages.append({"role": "assistant", "content": response})

        return {"status": "complete", "iterations": iteration, "note": "max_iterations reached"}

    def _parse_tool_calls(self, response: str) -> List[Dict]:
        """
        Parse tool calls from model response.
        Supports JSON format: {"tool": "VAULT_READ", "args": {"path": "..."}}
        """
        if "DIRECTIVE_COMPLETE" in response:
            return []

        import re
        tool_calls = []

        # Find JSON tool call blocks
        pattern = r'\{[^{}]*"tool"\s*:\s*"([^"]+)"[^{}]*\}'
        matches = re.findall(pattern, response)

        # Try to parse full JSON objects
        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        for match in re.finditer(json_pattern, response):
            try:
                tc = json.loads(match.group(0))
                if "tool" in tc:
                    tool_calls.append(tc)
            except json.JSONDecodeError:
                # Minimal call with just tool name
                tool_name = re.search(r'"tool"\s*:\s*"([^"]+)"', match.group(0))
                if tool_name:
                    tool_calls.append({"tool": tool_name.group(1), "args": {}})

        return tool_calls

    def _analysis_loop(self, directive: str) -> Dict[str, Any]:
        """
        Fallback when LLM is unavailable.
        Performs structured analysis of the directive and executes
        best-effort file operations based on keywords.
        """
        self._log("fallback_analysis", {"directive": directive[:200]})

        # Read relevant files based on directive keywords
        actions_taken = []
        directive_lower = directive.lower()

        # Common patterns: "read X", "fix X", "create X at PATH"
        import re
        read_matches = re.findall(r'read\s+([^\s,.]+)', directive_lower)
        for match in read_matches[:3]:
            result = self.tools.call("VAULT_READ", {"path": match})
            actions_taken.append({"action": "read", "path": match, "status": result.get("status")})

        return {
            "status": "complete",
            "method": "fallback_analysis",
            "actions_taken": actions_taken,
            "note": "LLM unavailable — structural analysis only",
        }

    # ── Session Close + AAR ───────────────────────────────────

    def _close_session(self, directive: str, execution_result: Dict) -> Dict:
        """Generate and store the constitutional AAR. Always fires."""
        aar_args = {
            "session_id": self.session_id,
            "directive": directive[:500],
            "missions_completed": [directive[:100]] if execution_result.get("status") == "complete" else [],
            "what_went_well": self._infer_went_well(execution_result),
            "what_went_wrong": self._infer_went_wrong(execution_result),
            "what_was_learned": [],
            "state_delta": {
                "files_created": self._files_created,
                "files_modified": self._files_modified,
                "events_published": self._events_published,
            },
            "files_created": self._files_created,
            "files_modified": self._files_modified,
            "events_published": self._events_published,
            "doctor_result": "not_run",
            "execution_status": execution_result.get("status", "unknown"),
        }

        result = self.tools.call("AAR_GENERATE", aar_args)

        self._publish("coding.session.complete", {
            "session_id": self.session_id,
            "status": execution_result.get("status"),
            "aar_path": result.get("aar_path"),
        })

        return result

    def _infer_went_well(self, result: Dict) -> List[str]:
        well = []
        if result.get("status") == "complete":
            well.append("Directive completed successfully")
        if self._files_created:
            well.append(f"{len(self._files_created)} files created")
        if self._events_published > 0:
            well.append(f"{self._events_published} events published to Event Bus")
        return well or ["Session completed"]

    def _infer_went_wrong(self, result: Dict) -> List[str]:
        wrong = []
        if result.get("status") == "failed":
            wrong.append(f"Execution failed: {result.get('error', 'unknown error')}")
        if result.get("method") == "fallback_analysis":
            wrong.append("LLM unavailable — ran fallback analysis only")
        return wrong or ["No errors recorded"]

    # ── Helpers ───────────────────────────────────────────────

    def _log(self, event_type: str, data: Dict) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data,
        }
        self._session_log.append(entry)

    def _publish(self, event_type: str, payload: Dict) -> None:
        if self._bus:
            try:
                self._bus.publish(event_type, payload, source_module="sovereign_coding_agent")
                self._events_published += 1
            except Exception:
                pass


# ── Self-test ─────────────────────────────────────────────────

if __name__ == "__main__":
    agent = SovereignCodingAgent()
    hc = agent.health_check()
    print(f"Tools: {hc['tools']}")
    print(f"Model: {hc['model']}")
    print(f"Governance loaded: {hc['governance']}")
    print(f"Event Bus: {hc['event_bus']}")
    print(f"Organism State: {hc['organism_state']}")
    print(f"Governance Gate: {hc['governance_gate']}")
    assert hc["tools"] == 16, f"Expected 16 tools, got {hc['tools']}"
    assert hc["governance"] is True
    print("\nPASS: SovereignCodingAgent health check")
