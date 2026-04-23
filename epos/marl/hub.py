#!/usr/bin/env python3
# EPOS Artifact — BUILD 104 (MARL Neural Hub)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
hub.py — Centralized Multi-Agent Reinforcement Learning Hub

A lightweight central state store for MARL-style coordination across
EPOS agents. Not a neural trainer itself (that's the QLoRA runner).
This is the coordination substrate: agents submit observations and
action-outcomes; the hub stores them keyed by (agent_id, state_hash,
action, outcome) so policy-learning can happen downstream.

Keyed on:
  - agent_id       (who observed)
  - state_hash     (hash of the observation space)
  - action         (what was chosen)
  - outcome_signal (positive | neutral | negative; from Reward Bus)

Outputs a simple policy artifact: for a given agent + state_hash, what
action has the best recent outcome? That's what downstream agents
consult when they have to act but haven't been trained specifically.

Lives as an append-only JSONL + periodic rollup. No external deps.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
OBS_LOG = Path(os.getenv("EPOS_MARL_OBSERVATIONS",
                          str(REPO / "context_vault" / "marl" / "observations.jsonl")))
POLICY = Path(os.getenv("EPOS_MARL_POLICY",
                         str(REPO / "context_vault" / "marl" / "policy.json")))
OBS_LOG.parent.mkdir(parents=True, exist_ok=True)


def _hash_state(state: Any) -> str:
    return hashlib.sha256(
        json.dumps(state, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


class MARLHub:
    def submit(self, agent_id: str, state: Any, action: str,
                outcome_signal: str, reward_value: float = 0.0,
                metadata: dict[str, Any] | None = None) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "state_hash": _hash_state(state),
            "state_preview": str(state)[:200],
            "action": action,
            "outcome_signal": outcome_signal,
            "reward_value": float(reward_value),
            "metadata": metadata or {},
        }
        with OBS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry["state_hash"]

    def rebuild_policy(self) -> dict[str, Any]:
        """Aggregate observations into a best-action-per-state policy.
        Uses mean reward per (agent, state_hash, action)."""
        agg: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
            lambda: {"count": 0.0, "reward_sum": 0.0}
        )
        if not OBS_LOG.exists():
            POLICY.write_text(json.dumps({}) + "\n")
            return {}
        for line in OBS_LOG.read_text().splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            key = (e["agent_id"], e["state_hash"], e["action"])
            agg[key]["count"] += 1
            agg[key]["reward_sum"] += float(e.get("reward_value", 0))

        # Pick best action per (agent, state_hash)
        best: dict[str, dict[str, Any]] = {}
        for (agent, sh, action), stats in agg.items():
            mean = stats["reward_sum"] / max(stats["count"], 1)
            k = f"{agent}:{sh}"
            if k not in best or mean > best[k]["mean_reward"]:
                best[k] = {
                    "agent_id": agent, "state_hash": sh,
                    "recommended_action": action,
                    "mean_reward": round(mean, 4),
                    "n_observations": int(stats["count"]),
                }
        POLICY.write_text(json.dumps(best, indent=2) + "\n")
        return best

    def query(self, agent_id: str, state: Any) -> dict[str, Any] | None:
        if not POLICY.exists():
            return None
        policy = json.loads(POLICY.read_text())
        sh = _hash_state(state)
        return policy.get(f"{agent_id}:{sh}")


def submit_observation(agent_id: str, state: Any, action: str,
                        outcome_signal: str, reward_value: float = 0.0,
                        metadata: dict | None = None) -> str:
    return MARLHub().submit(agent_id, state, action, outcome_signal,
                              reward_value, metadata)


def get_policy(agent_id: str, state: Any) -> dict | None:
    return MARLHub().query(agent_id, state)


if __name__ == "__main__":
    hub = MARLHub()
    hub.submit("test_agent", {"situation": "test"}, "do_X", "positive", 1.0)
    hub.submit("test_agent", {"situation": "test"}, "do_Y", "negative", -0.5)
    policy = hub.rebuild_policy()
    print(json.dumps(policy, indent=2))
    q = hub.query("test_agent", {"situation": "test"})
    print(f"Recommended action: {q}")
