#!/usr/bin/env python3
# EPOS Artifact — BUILD 90 (SCC TAOR Loop)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, XIV
"""
scc_taor.py — Think-Act-Observe-Repeat runtime for the Sovereign Coding Component

Transforms SCC from one-shot → stateful iterative loop. Each turn:
  - THINK: LLM produces a reasoning step + optional tool_use
  - ACT:   tool executes (ripgrep | tree | read_file | write_file | run_test)
  - OBSERVE: tool output goes back to the model
  - REPEAT: until model emits end_turn OR max_turns reached

Tools:
  - rg(pattern, path):   ripgrep search
  - tree(path, depth):   directory listing
  - read(path):          file contents
  - write(path, content): write with deletion_gate check
  - run_test(cmd):       execute test command, capture output
  - architect_directive(text): emit a Directive (architect-mode only)

Persona switch: SCC can run in "forge" (code) or "architect" (directives).
Persona file: nodes/scc/personas/<persona>.md hot-swapped via Bridge
persona_reloader on every invocation.

This is the critical EPAS Mission 1 foundation. Every subsequent build
that relies on SCC depends on this loop being stateful.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
LOG_DIR = Path(os.getenv("SCC_LOG_DIR", str(REPO / "context_vault" / "scc" / "sessions")))
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TAORTurn:
    turn: int
    role: str            # "assistant" | "tool_result"
    think: str = ""
    action: str = ""      # tool name used
    tool_args: dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    error: str = ""


@dataclass
class TAORSession:
    session_id: str
    mission: str
    persona: str
    started_at: str
    turns: list[TAORTurn] = field(default_factory=list)
    final_output: str = ""
    status: str = "running"   # running | complete | blocked | failed


# ── Tool implementations ─────────────────────────────────────────

def tool_rg(pattern: str, path: str = ".") -> str:
    """ripgrep wrapper — returns up to 200 matching lines."""
    try:
        r = subprocess.run(
            ["rg", "--max-count", "50", pattern, path],
            capture_output=True, text=True, timeout=30,
        )
        return r.stdout[:8000] or "(no matches)"
    except FileNotFoundError:
        # Fallback to grep
        try:
            r = subprocess.run(
                ["grep", "-rn", pattern, path],
                capture_output=True, text=True, timeout=30,
            )
            return r.stdout[:8000] or "(no matches)"
        except Exception as e:
            return f"tool_error: {type(e).__name__}: {e}"
    except Exception as e:
        return f"tool_error: {type(e).__name__}: {e}"


def tool_tree(path: str = ".", depth: int = 2) -> str:
    """Directory listing."""
    try:
        r = subprocess.run(
            ["find", path, "-maxdepth", str(depth), "-not", "-path", "*/.git/*",
             "-not", "-path", "*/__pycache__/*", "-not", "-path", "*/venv*"],
            capture_output=True, text=True, timeout=15,
        )
        return r.stdout[:4000]
    except Exception as e:
        return f"tool_error: {type(e).__name__}: {e}"


def tool_read(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"(missing: {path})"
        text = p.read_text(encoding="utf-8", errors="replace")
        # Cap at 8K chars — if bigger, show head+tail
        if len(text) > 8000:
            return text[:4000] + f"\n\n[... {len(text) - 8000} chars elided ...]\n\n" + text[-4000:]
        return text
    except Exception as e:
        return f"tool_error: {type(e).__name__}: {e}"


def tool_write(path: str, content: str, context: dict | None = None) -> str:
    """Writes via deletion_gate enforcement — overwrites require approval."""
    p = Path(path)
    if p.exists():
        try:
            from nodes.execution_arm.deletion_gate import enforce as enforce_del
            enforce_del(target=f"write-over:{path}", context=context or {})
        except Exception as e:
            return f"deletion_gate_refused: {e}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"tool_error: {type(e).__name__}: {e}"


def tool_run_test(cmd: str) -> str:
    try:
        r = subprocess.run(
            shlex.split(cmd), capture_output=True, text=True, timeout=120,
        )
        return (
            f"returncode={r.returncode}\n"
            f"--- stdout ---\n{r.stdout[:2000]}\n"
            f"--- stderr ---\n{r.stderr[:2000]}"
        )
    except Exception as e:
        return f"tool_error: {type(e).__name__}: {e}"


def tool_architect_directive(text: str, out_path: str = "") -> str:
    """Architect-mode only — emit a Forge Directive markdown."""
    if not out_path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        out_path = str(REPO / "missions" / f"FORGE_DIRECTIVE_SCC_ARCHITECT_{ts}.md")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(text, encoding="utf-8")
    return f"directive written to {out_path}"


TOOLS: dict[str, Callable] = {
    "rg": tool_rg,
    "tree": tool_tree,
    "read": tool_read,
    "write": tool_write,
    "run_test": tool_run_test,
    "architect_directive": tool_architect_directive,
}


# ── Session runner ────────────────────────────────────────────

def load_persona(name: str) -> str:
    try:
        from nodes.scc.personas import load_persona as _load
        return _load(name).text
    except Exception:
        return f"(persona '{name}' not loadable; default forge-mode active)"


def run_session(mission: str, persona: str = "forge",
                max_turns: int = 12) -> TAORSession:
    """Stub loop — in production this calls LiteLLM/Qwen3-Coder. Here we
    demonstrate the deterministic scaffold; real LLM wiring lives in a
    separate Directive (requires LiteLLM at $LITELLM_BASE_URL).
    """
    session_id = datetime.now(timezone.utc).strftime("scc_%Y%m%d_%H%M%S")
    persona_text = load_persona(persona)
    session = TAORSession(
        session_id=session_id,
        mission=mission,
        persona=persona,
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    # Deterministic scaffold: proves the loop shape. Real model calls
    # plug into `_turn()` below. For now: one tree() call, one rg() call,
    # then end_turn. Swap out `_turn()` with a LiteLLM wrapper to go live.
    for turn_idx in range(1, max_turns + 1):
        turn = _turn(turn_idx, session, persona_text)
        session.turns.append(turn)
        if turn.action == "end_turn":
            session.status = "complete"
            session.final_output = turn.think
            break
        if turn.error:
            session.status = "failed"
            break
    else:
        session.status = "blocked"
        session.final_output = f"max_turns ({max_turns}) reached without end_turn"

    _persist(session)
    return session


def _turn(turn_idx: int, session: TAORSession, persona_text: str) -> TAORTurn:
    """Placeholder for the model call. Real impl routes to LiteLLM / Qwen3-Coder."""
    if turn_idx == 1:
        result = tool_tree(str(REPO), depth=2)
        return TAORTurn(turn=turn_idx, role="tool_result",
                        think="Exploring repo layout",
                        action="tree", tool_args={"path": str(REPO), "depth": 2},
                        observation=result[:500])
    if turn_idx == 2:
        result = tool_rg(session.mission.split()[0] if session.mission else "TODO", str(REPO))
        return TAORTurn(turn=turn_idx, role="tool_result",
                        think=f"Searching for '{session.mission.split()[0] if session.mission else 'TODO'}'",
                        action="rg", tool_args={"pattern": session.mission.split()[0] if session.mission else "TODO"},
                        observation=result[:500])
    return TAORTurn(turn=turn_idx, role="assistant",
                    think="Scaffold complete — real LLM call goes here.",
                    action="end_turn")


def _persist(session: TAORSession) -> None:
    data = {
        "session_id": session.session_id,
        "mission": session.mission,
        "persona": session.persona,
        "started_at": session.started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "status": session.status,
        "final_output": session.final_output,
        "turns": [
            {"turn": t.turn, "role": t.role, "think": t.think,
             "action": t.action, "tool_args": t.tool_args,
             "observation": t.observation[:500], "error": t.error}
            for t in session.turns
        ],
    }
    (LOG_DIR / f"{session.session_id}.json").write_text(
        json.dumps(data, indent=2) + "\n"
    )


if __name__ == "__main__":
    import sys
    mission = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Explore the repo structure"
    s = run_session(mission)
    print(f"Session {s.session_id}: {s.status} ({len(s.turns)} turns)")
    print(f"Log: {LOG_DIR / (s.session_id + '.json')}")
