#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
scc.py — Sovereign Coding Component (SCC)
==========================================
Constitutional Authority: EPOS Constitution v3.1

The EPOS-native coding agent. Replaces Desktop CODE.
Routes to Qwen3-Coder-30B via LiteLLM proxy.
Publishes every action to the Event Bus.
Generates AARs constitutionally — not by request.
"""

import os
import re
import sys
import json
import ast
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ── Lazy EPOS imports — boot even if dependencies absent ─────

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from epos.state.universal_state_graph import OrganismState
    _STATE = OrganismState()
except Exception:
    _STATE = None

try:
    from governance_gate import GovernanceGate
    _GATE = GovernanceGate()
except Exception:
    _GATE = None

from path_utils import get_context_vault

VAULT_ROOT = get_context_vault()
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL",
                              os.getenv("LITELLM_URL", "http://litellm:4000")).rstrip("/")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-epos-local-proxy")

# Immutable paths the SCC must never overwrite without council approval
_IMMUTABLE = {"skills/", "EPOS_CONSTITUTION", ".env", "docker-compose.yml"}

_LOCK = threading.Lock()


# ═══════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════

class ToolRegistry:
    """16 canonical EPOS tools. Every call gate-checked + event-published."""

    def __init__(self, session_log: list, publish_fn):
        self._log = session_log
        self._publish = publish_fn
        self._tools = {
            "VAULT_READ":         self._vault_read,
            "VAULT_WRITE":        self._vault_write,
            "VAULT_EDIT":         self._vault_edit,
            "VAULT_LIST":         self._vault_list,
            "VAULT_GREP":         self._vault_grep,
            "EPOS_EXEC":          self._epos_exec,
            "VAULT_SEARCH":       self._vault_search,
            "MISSION_READ":       self._mission_read,
            "MISSION_WRITE":      self._mission_write,
            "SCOUT_FETCH":        self._scout_fetch,
            "COMPACT_DIRECTIVE":  self._compact_directive,
            "AAR_GENERATE":       self._aar_generate,
            "GATE_PRE_EXECUTE":   self._gate_pre_execute,
            "AUDIT_POST_EXECUTE": self._audit_post_execute,
            "NODE_SPAWN":         self._node_spawn,
            "SESSION_INIT":       self._session_init,
        }

    def __len__(self):
        return len(self._tools)

    def __contains__(self, name):
        return name in self._tools

    def call(self, tool_name: str, args: Any) -> dict:
        """Gate → execute → audit. Returns result dict."""
        # Governance gate
        gate = self._gate_pre_execute({"tool_name": tool_name, "args": str(args)[:200]})
        if gate.get("verdict") == "BLOCK":
            self._publish("scc.tool.blocked", {"tool": tool_name, "reason": gate.get("reason")})
            return {"status": "blocked", "reason": gate.get("reason")}

        # Execute
        fn = self._tools.get(tool_name)
        if not fn:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}
        try:
            if isinstance(args, dict):
                result = fn(**args)
            elif isinstance(args, str):
                result = fn(args)
            else:
                result = fn(args)
        except Exception as e:
            result = {"status": "error", "error": str(e)}

        # Audit
        self._audit_post_execute({"tool": tool_name, "status": result.get("status", "unknown")})
        self._log.append({"tool": tool_name, "result": str(result)[:300]})
        return result

    # ── Vault operations ─────────────────────────────────────

    def _vault_read(self, path: str) -> dict:
        resolved = self._resolve(path)
        if not resolved.exists():
            return {"status": "error", "error": f"Not found: {path}"}
        try:
            content = resolved.read_text(encoding="utf-8")
            return {"status": "ok", "content": content, "path": str(resolved)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _vault_write(self, path: str, content: str) -> dict:
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        try:
            tmp = resolved.with_suffix(".tmp")
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(resolved)
            self._publish("vault.file.written", {"path": str(resolved), "bytes": len(content)})
            return {"status": "ok", "written": str(resolved), "bytes": len(content)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _vault_edit(self, path: str, old_string: str, new_string: str) -> dict:
        resolved = self._resolve(path)
        if not resolved.exists():
            return {"status": "error", "error": f"Not found: {path}"}
        try:
            text = resolved.read_text(encoding="utf-8")
            if old_string not in text:
                return {"status": "error", "error": "old_string not found in file"}
            new_text = text.replace(old_string, new_string, 1)
            tmp = resolved.with_suffix(".tmp")
            tmp.write_text(new_text, encoding="utf-8")
            tmp.replace(resolved)
            self._publish("vault.file.edited", {"path": str(resolved)})
            return {"status": "ok", "path": str(resolved)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _vault_list(self, path: str) -> dict:
        resolved = self._resolve(path)
        if not resolved.exists():
            return {"status": "error", "error": f"Path not found: {path}"}
        try:
            items = [
                {"name": p.name, "type": "dir" if p.is_dir() else "file",
                 "size": p.stat().st_size if p.is_file() else 0}
                for p in sorted(resolved.iterdir())
            ]
            return {"status": "ok", "path": str(resolved), "items": items}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _vault_grep(self, pattern: str, path: str = None) -> dict:
        search_path = self._resolve(path) if path else EPOS_ROOT
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", "--include=*.md",
                 "--include=*.json", pattern, str(search_path)],
                capture_output=True, text=True, timeout=15,
            )
            matches = [l for l in result.stdout.split("\n") if l.strip()]
            return {"status": "ok", "matches": matches, "count": len(matches)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _vault_search(self, query: str) -> dict:
        try:
            result = subprocess.run(
                ["grep", "-rn", "-i", query, str(VAULT_ROOT)],
                capture_output=True, text=True, timeout=15,
            )
            matches = [l for l in result.stdout.split("\n") if l.strip()][:20]
            return {"status": "ok", "matches": matches, "count": len(matches), "query": query}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── Execution ────────────────────────────────────────────

    def _epos_exec(self, command: str) -> dict:
        blocked_patterns = ["rm -rf /", "drop table", "mkfs", "> /dev/sd"]
        for p in blocked_patterns:
            if p in command.lower():
                return {"status": "blocked", "reason": f"Destructive command blocked: {p}"}
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=60, cwd=str(EPOS_ROOT),
            )
            return {
                "status": "ok", "stdout": result.stdout[:3000],
                "stderr": result.stderr[:1000], "returncode": result.returncode,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": f"Command exceeded 60s: {command[:100]}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── Mission ops ──────────────────────────────────────────

    def _mission_read(self, mission_id: str) -> dict:
        pm_path = VAULT_ROOT / "pm" / "pm_surface.jsonl"
        if not pm_path.exists():
            return {"status": "ok", "missions": [], "note": "pm_surface.jsonl not found"}
        try:
            missions = []
            for line in pm_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    m = json.loads(line)
                    if mission_id in str(m):
                        missions.append(m)
            return {"status": "ok", "missions": missions}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _mission_write(self, mission_id: str, content: str, status: str = "in_progress") -> dict:
        pm_path = VAULT_ROOT / "pm" / "pm_surface.jsonl"
        pm_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "mission_id": mission_id, "content": content,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with _LOCK:
            with open(pm_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        self._publish("scc.mission.updated", {"mission_id": mission_id, "status": status})
        return {"status": "ok", "mission_id": mission_id}

    # ── Network ──────────────────────────────────────────────

    def _scout_fetch(self, url: str) -> dict:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "EPOS-SCC/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read(32768).decode("utf-8", errors="replace")
            return {"status": "ok", "url": url, "content": body, "bytes": len(body)}
        except Exception as e:
            return {"status": "error", "url": url, "error": str(e)}

    # ── Session / governance tools ───────────────────────────

    def _compact_directive(self, directive: str, context: str = "") -> dict:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        compact_path = VAULT_ROOT / "sessions" / f"compact_{ts}.json"
        compact_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"directive": directive, "context": context, "saved_at": ts}
        compact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"status": "ok", "saved": str(compact_path)}

    def _aar_generate(self, session_id: str, directive: str, result: dict) -> dict:
        aar = {
            "session_id": session_id,
            "directive": directive,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "missions_completed": result.get("missions_completed", []),
            "what_went_well": result.get("what_went_well", []),
            "what_went_wrong": result.get("what_went_wrong", []),
            "what_was_learned": result.get("what_was_learned", []),
            "state_delta": result.get("state_delta", {}),
            "files_created": [e["tool"] for e in self._log if "WRITE" in e.get("tool", "")],
            "files_modified": [e["tool"] for e in self._log if "EDIT" in e.get("tool", "")],
            "events_published": len([e for e in self._log if e]),
            "doctor_result": "not_run",
        }
        aar_dir = VAULT_ROOT / "aar"
        aar_dir.mkdir(parents=True, exist_ok=True)
        aar_path = aar_dir / f"aar_{session_id}.json"
        aar_path.write_text(json.dumps(aar, indent=2), encoding="utf-8")
        self._publish("scc.aar.generated", {"session_id": session_id, "path": str(aar_path)})
        return {"status": "ok", "aar_path": str(aar_path), "aar": aar}

    def _gate_pre_execute(self, params: dict = None, **kwargs) -> dict:
        if params is None:
            params = kwargs
        tool_name = params.get("tool_name", "")
        args_str = str(params.get("args", ""))
        # Block immutable paths
        for immutable in _IMMUTABLE:
            if immutable in args_str:
                return {"verdict": "BLOCK", "reason": f"Immutable path: {immutable}"}
        # Block Windows-style paths
        if re.search(r"[A-Z]:\\", args_str):
            return {"verdict": "BLOCK", "reason": "Windows path rejected — POSIX only"}
        return {"verdict": "APPROVED", "reason": "All checks passed"}

    def _audit_post_execute(self, params: dict = None, **kwargs) -> dict:
        if params is None:
            params = kwargs
        self._publish("scc.tool.executed", params)
        return {"status": "logged"}

    def _node_spawn(self, node_name: str, directive: str = "") -> dict:
        self._publish("scc.node.spawn_requested", {"node": node_name, "directive": directive[:200]})
        return {"status": "queued", "node": node_name}

    def _session_init(self, session_id: str = None) -> dict:
        sid = session_id or datetime.now(timezone.utc).strftime("SCC-%Y%m%dT%H%M%SZ")
        self._publish("scc.session.initialized", {"session_id": sid})
        return {"status": "ok", "session_id": sid}

    # ── Helpers ──────────────────────────────────────────────

    def _resolve(self, path: str) -> Path:
        """Resolve a path relative to EPOS_ROOT if not absolute."""
        p = Path(path)
        if p.is_absolute():
            return p
        return EPOS_ROOT / path


# ═══════════════════════════════════════════════════════════════
# GOVERNANCE MANIFEST
# ═══════════════════════════════════════════════════════════════

class GovernanceManifest:
    """Loads constitutional parameters from vault or uses safe defaults."""

    def __init__(self, constitution_version: str, immutable_paths: list,
                 allowed_events: list, governance_tier: str):
        self.constitution_version = constitution_version
        self.immutable_paths = immutable_paths
        self.allowed_events = allowed_events
        self.governance_tier = governance_tier

    @classmethod
    def load(cls, epos_root: Path = EPOS_ROOT) -> "GovernanceManifest":
        manifest_path = epos_root / "context_vault" / "governance" / "governance_manifest.json"
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                return cls(**data)
            except Exception:
                pass
        return cls(
            constitution_version="v3.1",
            immutable_paths=list(_IMMUTABLE),
            allowed_events=["scc.*", "vault.*", "system.*"],
            governance_tier="T1",
        )

    def to_dict(self) -> dict:
        return {
            "constitution_version": self.constitution_version,
            "immutable_paths": self.immutable_paths,
            "allowed_events": self.allowed_events,
            "governance_tier": self.governance_tier,
        }


# ═══════════════════════════════════════════════════════════════
# SOVEREIGN CODING COMPONENT
# ═══════════════════════════════════════════════════════════════

class SovereignCodingComponent:
    """EPOS-native coding agent. Replaces Desktop CODE.

    Governed by the EPOS Constitution v3.1.
    Publishes every action to the Event Bus.
    Generates AARs constitutionally — not by request.
    Routes through LiteLLM to Qwen3-Coder-30B.
    """

    MODEL = "qwen3-coder-30b"

    def __init__(self):
        self.session_log: List[dict] = []
        self.governance = GovernanceManifest.load()
        self.tools = ToolRegistry(self.session_log, self._publish)

    def execute_directive(self, directive: str, timeout: int = 600) -> dict:
        """The agentic loop: gather context → take action → verify."""
        session_id = datetime.now(timezone.utc).strftime("SCC-%Y%m%dT%H%M%SZ")
        self._publish("scc.session.start", {
            "session_id": session_id,
            "directive": directive[:200],
        })

        if _STATE:
            try:
                _STATE.update("sovereignty.last_scc_session", session_id)
            except Exception:
                pass

        result = self._agentic_loop(directive, session_id, max_iterations=50)
        self._close_session(session_id, directive, result)
        return result

    def health_check(self) -> dict:
        return {
            "status": "operational",
            "model": self.MODEL,
            "tools": len(self.tools),
            "governance": self.governance is not None,
            "event_bus": _BUS is not None,
            "state_graph": _STATE is not None,
            "litellm": LITELLM_BASE_URL,
        }

    # ── Agentic loop ─────────────────────────────────────────

    def _agentic_loop(self, directive: str, session_id: str,
                      max_iterations: int = 50) -> dict:
        """LLM-driven tool execution loop."""
        system_prompt = self._build_system_prompt()
        messages = [{"role": "user", "content": directive}]
        iterations = 0
        final_response = ""

        while iterations < max_iterations:
            iterations += 1
            try:
                response = self._call_model(system_prompt, messages, timeout=120)
            except Exception as e:
                final_response = f"Model call failed: {e}"
                break

            final_response = response
            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                # No tools requested — model is done
                break

            # Execute each tool call
            tool_results = []
            for tc in tool_calls:
                tool_name = tc["name"]
                args = tc["args"]
                result = self.tools.call(tool_name, args)
                tool_results.append({
                    "tool": tool_name,
                    "result": result,
                })

            # Feed results back to model
            results_text = "\n".join(
                f"[{tr['tool']}] → {json.dumps(tr['result'])[:500]}"
                for tr in tool_results
            )
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user",
                             "content": f"Tool results:\n{results_text}\n\nContinue."})

        return {
            "status": "complete",
            "session_id": session_id,
            "iterations": iterations,
            "response": final_response,
            "tools_used": len(self.session_log),
        }

    def _call_model(self, system: str, messages: list, timeout: int = 120) -> str:
        """Call Qwen3-Coder via LiteLLM proxy."""
        import requests as _req
        resp = _req.post(
            f"{LITELLM_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LITELLM_MASTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.MODEL,
                "messages": [{"role": "system", "content": system}] + messages,
                "max_tokens": 4096,
                "temperature": 0.2,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _extract_tool_calls(self, response: str) -> List[dict]:
        """
        Parse tool calls from model response.

        Expected format:
            TOOL:TOOL_NAME:argument
            TOOL:VAULT_WRITE:/path/to/file|||file content here
            TOOL:EPOS_EXEC:python -c "print('hello')"
        """
        tool_calls = []
        for line in response.split("\n"):
            line = line.strip()
            if not line.startswith("TOOL:"):
                continue
            parts = line[5:].split(":", 1)
            if len(parts) < 2:
                continue
            tool_name = parts[0].strip()
            raw_args = parts[1].strip()

            if tool_name not in self.tools:
                continue

            # Parse args based on tool
            if tool_name == "VAULT_WRITE" and "|||" in raw_args:
                path, content = raw_args.split("|||", 1)
                args = {"path": path.strip(), "content": content}
            elif tool_name == "VAULT_EDIT" and "|||" in raw_args:
                parts3 = raw_args.split("|||")
                if len(parts3) >= 3:
                    args = {"path": parts3[0].strip(),
                            "old_string": parts3[1], "new_string": parts3[2]}
                else:
                    continue
            elif tool_name in ("VAULT_READ", "VAULT_LIST", "EPOS_EXEC",
                               "VAULT_GREP", "VAULT_SEARCH", "SCOUT_FETCH"):
                args = raw_args
            elif tool_name == "GATE_PRE_EXECUTE":
                args = {"tool_name": raw_args}
            elif tool_name == "AAR_GENERATE":
                args = {"session_id": raw_args, "directive": "", "result": {}}
            else:
                args = raw_args

            tool_calls.append({"name": tool_name, "args": args})

        return tool_calls

    def _build_system_prompt(self) -> str:
        """Build constitutional system prompt with skills context."""
        parts = [
            "You are the EPOS Sovereign Coding Component (SCC).",
            "You are governed by the EPOS Constitution v3.1.",
            f"Constitution version: {self.governance.constitution_version}",
            "You publish every action to the Event Bus.",
            "You generate an AAR at the end of every session.",
            "You use POSIX paths only. EPOS_ROOT=/app.",
            "You never modify constitutional files without council approval.",
            "",
            "AVAILABLE TOOLS (call by emitting TOOL:TOOL_NAME:args on its own line):",
        ]
        for name in self.tools._tools:
            parts.append(f"  TOOL:{name}:<args>")

        parts += [
            "",
            "TOOL ARGUMENT FORMATS:",
            "  TOOL:VAULT_READ:/app/path/to/file.py",
            "  TOOL:VAULT_WRITE:/app/path/file.py|||file content here",
            "  TOOL:VAULT_EDIT:/app/path/file.py|||old text|||new text",
            "  TOOL:VAULT_LIST:/app/context_vault/sessions",
            "  TOOL:VAULT_GREP:pattern_to_search",
            "  TOOL:EPOS_EXEC:python -c \"print('hello')\"",
            "  TOOL:AAR_GENERATE:session_id_here",
            "",
            "When you are done with all actions, respond with your final summary.",
            "Do NOT use TOOL: lines in your final summary.",
        ]

        # Load skills context
        skills_dir = EPOS_ROOT / "skills"
        if skills_dir.exists():
            for sf in sorted(skills_dir.glob("*.md"))[:3]:
                try:
                    content = sf.read_text(encoding="utf-8")[:800]
                    parts.append(f"\n--- Skill: {sf.name} ---\n{content}")
                except Exception:
                    pass

        return "\n".join(parts)

    # ── Session close ────────────────────────────────────────

    def _close_session(self, session_id: str, directive: str, result: dict):
        """Constitutional: AAR always fires on session end."""
        aar_result = self.tools._aar_generate(session_id, directive, result)
        result["aar"] = aar_result.get("aar")
        result["aar_path"] = aar_result.get("aar_path")

        self._publish("scc.session.complete", {
            "session_id": session_id,
            "iterations": result.get("iterations", 0),
            "status": result.get("status"),
            "aar_path": result.get("aar_path"),
        })

        if _STATE:
            try:
                _STATE.increment("sovereignty.scc_sessions_total")
            except Exception:
                pass

    # ── Event Bus ────────────────────────────────────────────

    def _publish(self, event_type: str, payload: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="scc")
            except Exception:
                pass


# ── Module-level convenience ─────────────────────────────────

def get_scc() -> SovereignCodingComponent:
    """Get a ready-to-use SCC instance."""
    return SovereignCodingComponent()


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    scc = SovereignCodingComponent()

    print(f"Tools: {len(scc.tools)}")
    assert len(scc.tools) == 16, f"Expected 16 tools, got {len(scc.tools)}"

    print(f"Model: {scc.MODEL}")
    assert scc.MODEL == "qwen3-coder-30b"

    print(f"Governance: {scc.governance.constitution_version}")
    assert scc.governance is not None

    # Test health check
    health = scc.health_check()
    print(f"Health: {health['status']}")
    assert health["status"] == "operational"

    # Test tool execution
    r = scc.tools.call("VAULT_WRITE", {
        "path": "context_vault/sessions/scc_self_test.txt",
        "content": "SCC self-test passed"
    })
    assert r["status"] == "ok", f"VAULT_WRITE failed: {r}"
    print(f"VAULT_WRITE: {r['status']}")

    r2 = scc.tools.call("VAULT_READ", {"path": "context_vault/sessions/scc_self_test.txt"})
    assert r2["content"] == "SCC self-test passed"
    print(f"VAULT_READ: {r2['content']}")

    # Test governance gate
    g = scc.tools.call("GATE_PRE_EXECUTE", {"tool_name": "VAULT_READ", "args": "test.txt"})
    assert g.get("verdict") == "APPROVED"
    print(f"GATE_PRE_EXECUTE: {g['verdict']}")

    print("\nPASS: SovereignCodingComponent — all checks passed")
