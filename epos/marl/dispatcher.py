#!/usr/bin/env python3
# EPOS Artifact — BUILD 105 (Agentic Dispatcher)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
dispatcher.py — Route tasks to the right agent/arm based on MARL policy

Given a task spec (verb, target, context), the dispatcher:
  1. Classifies the task into an action space
  2. Queries the MARL Hub for the best-known action for similar states
  3. Routes through the execution arm's mode_selector for final choice
  4. Logs the dispatch + outcome back to MARL for training

Acts as the organism's "choose your own adventure" layer:
  - New task → guess from policy (explore vs exploit)
  - Known task with known state → execute best action
  - Known task but novel state → fall back to mode_selector defaults
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
DISPATCH_LOG = Path(os.getenv("EPOS_DISPATCH_LOG",
                                str(REPO / "context_vault" / "bi" / "dispatcher.jsonl")))
DISPATCH_LOG.parent.mkdir(parents=True, exist_ok=True)

EXPLORATION_EPSILON = float(os.getenv("EPOS_DISPATCH_EPSILON", "0.10"))


@dataclass
class DispatchResult:
    task: str
    chosen_agent: str
    chosen_action: str
    policy_source: str   # "marl" | "mode_selector" | "explore"
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgenticDispatcher:
    def dispatch(self, task: str, context: dict[str, Any] | None = None) -> DispatchResult:
        ctx = context or {}
        state_key = {
            "task_type": self._classify(task),
            "has_url": bool(self._extract_url(task)),
            "needs_write": any(k in task.lower() for k in ("write", "create", "update", "post")),
            "needs_delete": any(k in task.lower() for k in ("delete", "remove", "drop")),
        }

        # Explore-exploit
        if random.random() < EXPLORATION_EPSILON:
            return self._explore(task, state_key)

        # Consult MARL policy
        try:
            from epos.marl.hub import get_policy
            policy = get_policy("dispatcher", state_key)
        except Exception:
            policy = None

        if policy and policy.get("mean_reward", 0) > 0.1:
            return DispatchResult(
                task=task, chosen_agent=policy["recommended_action"].split(".")[0],
                chosen_action=policy["recommended_action"],
                policy_source="marl",
                confidence=min(0.95, 0.5 + policy["mean_reward"]),
            )

        # Fall back to the execution arm's mode_selector
        try:
            from nodes.execution_arm.mode_selector import select
            sel = select(task=task, context=ctx)
            result = DispatchResult(
                task=task, chosen_agent=sel.arm,
                chosen_action=sel.variant,
                policy_source="mode_selector",
                confidence=sel.confidence,
            )
        except Exception as e:
            result = DispatchResult(
                task=task, chosen_agent="human",
                chosen_action="escalate",
                policy_source="mode_selector_failed",
                confidence=0.0,
            )
        self._log(result, state_key)
        return result

    def _classify(self, task: str) -> str:
        t = task.lower()
        if any(k in t for k in ("scrape", "fetch", "read site", "url")):
            return "web_read"
        if any(k in t for k in ("click", "type", "fill", "submit", "post to")):
            return "web_write"
        if any(k in t for k in ("screenshot", "desktop", "file manager", "open app")):
            return "os_action"
        if any(k in t for k in ("summarize", "extract", "analyze")):
            return "reason"
        if any(k in t for k in ("build", "create file", "write code")):
            return "code"
        return "unknown"

    def _extract_url(self, task: str) -> str | None:
        import re
        m = re.search(r"https?://[^\s]+", task)
        return m.group(0) if m else None

    def _explore(self, task: str, state: dict) -> DispatchResult:
        options = ["browser_use.headless", "browser_use.headed",
                   "computer_use.headless", "computer_use.headed"]
        choice = random.choice(options)
        result = DispatchResult(
            task=task, chosen_agent=choice.split(".")[0],
            chosen_action=choice, policy_source="explore",
            confidence=0.30,
        )
        self._log(result, state)
        return result

    def _log(self, result: DispatchResult, state: dict) -> None:
        rec = {"state": state, **result.__dict__}
        with DISPATCH_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")


def dispatch(task: str, context: dict | None = None) -> dict[str, Any]:
    r = AgenticDispatcher().dispatch(task, context)
    return r.__dict__


if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Scrape top Gumroad products"
    print(json.dumps(dispatch(task), indent=2, default=str))
