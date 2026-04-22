#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §3
"""
computer_use_arm.py — ComputerUse Arm (headless + headed)
==========================================================
OS/desktop-level execution via Anthropic's computer-use tool loop
(screenshot → action → screenshot). Reaches anything a human at the
machine can reach: desktop apps, file manager, terminals, cross-app
flows the browser can't touch.

Capabilities:
    - read        (screenshots, file reads, app inspection)
    - write       (type, click, drag, drop, file save)
    - shell       (controlled bash via the shell tool)
    - delete      (only through deletion_gate.enforce)

Modes:
    - headless: runs inside Xvfb :99 (virtual display). Useful for
                scheduled/background desktop tasks that still need a
                real GUI (Obsidian, Notion app, VS Code).
    - headed:   runs on the real user display. Required when the
                Sovereign needs to observe, when MFA/CAPTCHA is likely,
                or when visual verification is explicit.

Deletion: every `str_replace`, `create` (overwrite), file `rm`, or
row-level delete in a DB tool MUST pass `deletion_gate.enforce`
before the tool call executes. Blanket approval is discouraged.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .deletion_gate import enforce as enforce_deletion

_LOG_DIR = Path(os.getenv("EPOS_ARM_LOG_DIR", "context_vault/execution_arm"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "computer_use.jsonl"

_MODEL_DEFAULT = os.getenv("COMPUTER_USE_MODEL", "claude-opus-4-7")
_MAX_TOKENS_DEFAULT = int(os.getenv("COMPUTER_USE_MAX_TOKENS", "4096"))


@dataclass
class ArmResult:
    success: bool
    arm: str = "computer_use"
    mode: str = "headless"
    task: str = ""
    output: str = ""
    error: str = ""
    turns: int = 0
    started_at: str = ""
    finished_at: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "arm": self.arm,
            "mode": self.mode,
            "task": self.task,
            "output": self.output,
            "error": self.error,
            "turns": self.turns,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "extras": self.extras,
        }


class ComputerUseArm:
    """Sovereign OS/desktop execution arm — both modes behind one interface."""

    def __init__(self) -> None:
        self._anthropic_available = False
        self._reason = ""
        try:
            import anthropic  # noqa: F401
            self._anthropic_available = True
        except ImportError as e:
            self._reason = f"anthropic SDK not installed: {e}"

        self._xvfb_proc: subprocess.Popen | None = None
        self._xvfb_display: str | None = None

    def health(self) -> dict[str, Any]:
        if not self._anthropic_available:
            return {"status": "unavailable", "reason": self._reason}

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        display = os.getenv("DISPLAY", "")
        xvfb = shutil.which("Xvfb")
        xdotool = shutil.which("xdotool")
        scrot = shutil.which("scrot") or shutil.which("gnome-screenshot") or shutil.which("import")
        return {
            "status": "operational" if api_key else "degraded",
            "reason": "" if api_key else "ANTHROPIC_API_KEY not set",
            "modes": ["headless", "headed"],
            "display": display or "unset",
            "xvfb": bool(xvfb),
            "xdotool": bool(xdotool),
            "screenshot_tool": bool(scrot),
            "model": _MODEL_DEFAULT,
            "log": str(_LOG_FILE),
        }

    async def run(
        self,
        task: str,
        mode: str = "headless",
        max_turns: int = 12,
        context: dict[str, Any] | None = None,
    ) -> ArmResult:
        started = datetime.now(timezone.utc).isoformat()
        ctx = dict(context or {})
        ctx.setdefault("arm", "computer_use")

        if not self._anthropic_available:
            return self._fail(task, mode, started, self._reason)

        if not os.getenv("ANTHROPIC_API_KEY"):
            return self._fail(task, mode, started, "ANTHROPIC_API_KEY not set")

        if mode not in ("headless", "headed"):
            return self._fail(task, mode, started, f"invalid mode {mode!r}")

        effective_mode = mode
        setup_warning = ""
        if mode == "headless":
            ok, reason = self._ensure_virtual_display()
            if not ok:
                return self._fail(task, mode, started, f"headless setup failed: {reason}")
        elif mode == "headed":
            if not os.getenv("DISPLAY"):
                if shutil.which("Xvfb"):
                    ok, reason = self._ensure_virtual_display()
                    if ok:
                        effective_mode = "headless"
                        setup_warning = "no real display; fell back to Xvfb-headless"
                    else:
                        return self._fail(task, mode, started, reason)
                else:
                    return self._fail(task, mode, started, "no DISPLAY and no Xvfb")

        try:
            result = await asyncio.to_thread(
                self._run_tool_loop,
                task,
                effective_mode,
                max_turns,
                ctx,
            )
            if setup_warning:
                result.extras["mode_warning"] = setup_warning
            self._log(result)
            return result
        except Exception as e:  # noqa: BLE001
            r = self._fail(task, effective_mode, started, f"{type(e).__name__}: {e}")
            self._log(r)
            return r

    def run_sync(
        self,
        task: str,
        mode: str = "headless",
        max_turns: int = 12,
        context: dict[str, Any] | None = None,
    ) -> ArmResult:
        return asyncio.run(self.run(task, mode, max_turns, context))

    # ── Internals ─────────────────────────────────────────────

    def _run_tool_loop(
        self,
        task: str,
        mode: str,
        max_turns: int,
        ctx: dict[str, Any],
    ) -> ArmResult:
        import anthropic
        started = datetime.now(timezone.utc).isoformat()

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        messages = [{"role": "user", "content": task}]
        tools = [
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": int(os.getenv("COMPUTER_USE_WIDTH", "1280")),
                "display_height_px": int(os.getenv("COMPUTER_USE_HEIGHT", "800")),
            },
            {"type": "bash_20250124", "name": "bash"},
            {"type": "text_editor_20250124", "name": "str_replace_editor"},
        ]

        final_text = ""
        turns = 0
        while turns < max_turns:
            turns += 1
            resp = client.messages.create(
                model=_MODEL_DEFAULT,
                max_tokens=_MAX_TOKENS_DEFAULT,
                messages=messages,
                tools=tools,
                betas=["computer-use-2025-01-24"],
            )

            # Collect assistant content
            assistant_blocks = []
            tool_uses = []
            for block in resp.content:
                assistant_blocks.append(block)
                if block.type == "tool_use":
                    tool_uses.append(block)
                elif block.type == "text":
                    final_text += block.text

            messages.append({"role": "assistant", "content": assistant_blocks})

            if resp.stop_reason == "end_turn" or not tool_uses:
                return ArmResult(
                    success=True,
                    arm="computer_use",
                    mode=mode,
                    task=task,
                    output=final_text.strip()[:1500],
                    turns=turns,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    extras={"mission_id": ctx.get("mission_id", "")},
                )

            tool_results = []
            for tu in tool_uses:
                try:
                    out = self._dispatch_tool(tu, ctx)
                except PermissionError as pe:
                    out = {"type": "tool_result", "tool_use_id": tu.id,
                           "content": f"BLOCKED: {pe}", "is_error": True}
                except Exception as e:  # noqa: BLE001
                    out = {"type": "tool_result", "tool_use_id": tu.id,
                           "content": f"ERROR: {e}", "is_error": True}
                tool_results.append(out)
            messages.append({"role": "user", "content": tool_results})

        return ArmResult(
            success=False,
            arm="computer_use",
            mode=mode,
            task=task,
            error=f"hit max_turns ({max_turns})",
            turns=turns,
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            extras={"mission_id": ctx.get("mission_id", "")},
        )

    def _dispatch_tool(self, tool_use, ctx: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a single tool_use block. Enforces deletion gate."""
        name = tool_use.name
        inp = tool_use.input or {}

        if name == "bash":
            cmd = inp.get("command", "")
            if _looks_destructive(cmd):
                enforce_deletion(target=f"bash:{cmd[:120]}", context=ctx)
            return self._exec_bash(tool_use.id, cmd)

        if name == "str_replace_editor":
            cmd = inp.get("command", "")
            path = inp.get("path", "")
            if cmd in {"create", "str_replace", "insert"} and path:
                # These can overwrite — treat as deletion of prior state
                enforce_deletion(target=f"edit:{path}:{cmd}", context=ctx)
            return self._exec_editor(tool_use.id, inp)

        if name == "computer":
            return self._exec_computer(tool_use.id, inp)

        return {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": f"unknown tool: {name}",
            "is_error": True,
        }

    def _exec_bash(self, tool_use_id: str, cmd: str) -> dict[str, Any]:
        if not cmd:
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": ""}
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60,
            )
            out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
            return {"type": "tool_result", "tool_use_id": tool_use_id,
                    "content": out[:4000], "is_error": r.returncode != 0}
        except Exception as e:  # noqa: BLE001
            return {"type": "tool_result", "tool_use_id": tool_use_id,
                    "content": f"bash error: {e}", "is_error": True}

    def _exec_editor(self, tool_use_id: str, inp: dict) -> dict[str, Any]:
        cmd = inp.get("command", "")
        path = inp.get("path", "")
        try:
            p = Path(path)
            if cmd == "view":
                data = p.read_text(encoding="utf-8", errors="replace")
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": data[:4000]}
            if cmd == "create":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(inp.get("file_text", ""), encoding="utf-8")
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"created {path}"}
            if cmd == "str_replace":
                old = inp.get("old_str", "")
                new = inp.get("new_str", "")
                body = p.read_text(encoding="utf-8")
                if old not in body:
                    return {"type": "tool_result", "tool_use_id": tool_use_id,
                            "content": "old_str not found", "is_error": True}
                p.write_text(body.replace(old, new, 1), encoding="utf-8")
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"replaced in {path}"}
            if cmd == "insert":
                line = int(inp.get("insert_line", 0))
                text = inp.get("new_str", "") or inp.get("text", "")
                lines = p.read_text(encoding="utf-8").splitlines()
                lines.insert(max(0, min(line, len(lines))), text)
                p.write_text("\n".join(lines), encoding="utf-8")
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"inserted into {path}"}
        except Exception as e:  # noqa: BLE001
            return {"type": "tool_result", "tool_use_id": tool_use_id,
                    "content": f"editor error: {e}", "is_error": True}
        return {"type": "tool_result", "tool_use_id": tool_use_id,
                "content": f"unknown editor command: {cmd}", "is_error": True}

    def _exec_computer(self, tool_use_id: str, inp: dict) -> dict[str, Any]:
        """Screenshot / mouse / keyboard via xdotool + screenshot tool."""
        action = inp.get("action", "")
        try:
            if action == "screenshot":
                img = self._screenshot()
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": [{
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png",
                                   "data": img},
                    }],
                }
            if action in ("left_click", "double_click", "right_click", "middle_click"):
                coord = inp.get("coordinate", [0, 0])
                btn = {"left_click": "1", "middle_click": "2",
                       "right_click": "3", "double_click": "1"}[action]
                repeat = "2" if action == "double_click" else "1"
                subprocess.run(["xdotool", "mousemove", str(coord[0]), str(coord[1])], check=False)
                subprocess.run(["xdotool", "click", "--repeat", repeat, btn], check=False)
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"{action} at {coord}"}
            if action == "mouse_move":
                coord = inp.get("coordinate", [0, 0])
                subprocess.run(["xdotool", "mousemove", str(coord[0]), str(coord[1])], check=False)
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"moved to {coord}"}
            if action == "type":
                text = inp.get("text", "")
                subprocess.run(["xdotool", "type", "--delay", "12", text], check=False)
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"typed {len(text)} chars"}
            if action == "key":
                key = inp.get("text", "")
                subprocess.run(["xdotool", "key", key], check=False)
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"pressed {key}"}
            if action in ("left_click_drag", "scroll"):
                # Simplified: treat drag/scroll as a best-effort key/mouse combo.
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": f"{action} not fully implemented — use key/type fallback"}
            if action == "cursor_position":
                r = subprocess.run(["xdotool", "getmouselocation"],
                                   capture_output=True, text=True)
                return {"type": "tool_result", "tool_use_id": tool_use_id,
                        "content": r.stdout.strip()}
        except Exception as e:  # noqa: BLE001
            return {"type": "tool_result", "tool_use_id": tool_use_id,
                    "content": f"computer error: {e}", "is_error": True}
        return {"type": "tool_result", "tool_use_id": tool_use_id,
                "content": f"unknown action: {action}", "is_error": True}

    def _screenshot(self) -> str:
        tool = (shutil.which("scrot") or shutil.which("import")
                or shutil.which("gnome-screenshot"))
        if not tool:
            raise RuntimeError("no screenshot tool (install scrot, imagemagick, or gnome-screenshot)")
        out = Path("/tmp/epos_cu_shot.png")
        if tool.endswith("scrot"):
            subprocess.run([tool, "-o", str(out)], check=True)
        elif tool.endswith("import"):
            subprocess.run([tool, "-window", "root", str(out)], check=True)
        else:  # gnome-screenshot
            subprocess.run([tool, "-f", str(out)], check=True)
        return base64.b64encode(out.read_bytes()).decode("ascii")

    def _ensure_virtual_display(self) -> tuple[bool, str]:
        if os.getenv("DISPLAY"):
            return True, "real display"
        if not shutil.which("Xvfb"):
            return False, "Xvfb not on PATH"
        disp = os.getenv("EPOS_XVFB_DISPLAY", ":99")
        if self._xvfb_proc and self._xvfb_proc.poll() is None:
            os.environ["DISPLAY"] = disp
            return True, "Xvfb already running"
        try:
            self._xvfb_proc = subprocess.Popen(
                ["Xvfb", disp, "-screen", "0", "1280x800x24", "-ac"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(0.5)
            os.environ["DISPLAY"] = disp
            self._xvfb_display = disp
            return True, f"Xvfb {disp} started"
        except Exception as e:  # noqa: BLE001
            return False, f"Xvfb start failed: {e}"

    def _fail(self, task: str, mode: str, started: str, error: str) -> ArmResult:
        return ArmResult(
            success=False, arm="computer_use", mode=mode, task=task,
            error=error, started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )

    def _log(self, result: ArmResult) -> None:
        try:
            with _LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result.to_dict()) + "\n")
        except Exception:
            pass


_DESTRUCTIVE_RX = None


def _looks_destructive(cmd: str) -> bool:
    """Rough heuristic: does a bash command look like it deletes things?"""
    import re
    global _DESTRUCTIVE_RX
    if _DESTRUCTIVE_RX is None:
        _DESTRUCTIVE_RX = re.compile(
            r"(?:^|\s|;|&&|\|)"
            r"(rm\s+-[rRf]|rm\s+-[^ ]*f|rmdir|shred|unlink|truncate\s+-s\s*0|"
            r">\s*\S+|dd\s+.*of=|mkfs|fdisk|parted|wipefs|"
            r"git\s+clean\s+-[fdx]|git\s+reset\s+--hard|"
            r"DROP\s+TABLE|DELETE\s+FROM|TRUNCATE\s+TABLE|"
            r"docker\s+(rm|rmi|volume\s+rm|system\s+prune)|"
            r"aws\s+s3\s+rm|rclone\s+delete)",
            re.IGNORECASE,
        )
    return bool(_DESTRUCTIVE_RX.search(cmd))


if __name__ == "__main__":
    arm = ComputerUseArm()
    h = arm.health()
    print(f"health: {h['status']}")
    if h["status"] != "operational":
        print(f"  reason: {h.get('reason', '')}")

    assert _looks_destructive("rm -rf /tmp/foo")
    assert _looks_destructive("DROP TABLE users;")
    assert not _looks_destructive("ls -la /tmp")
    print("PASS: computer_use_arm (structural)")
