from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from engine.llm_client import call_llm
from engine.prompt_loader import load_prompt_layers
from engine.structured_output import parse_or_repair_json
from engine.contracts.validator import validate_contract

@dataclass
class DuetModels:
    cadence: str
    metaphor: str
    critic: str

def _load_models_from_env() -> DuetModels:
    return DuetModels(
        cadence=os.getenv("CADENCE_MODEL", "phi3:mini"),
        metaphor=os.getenv("METAPHOR_MODEL", "phi4"),
        critic=os.getenv("CRITIC_MODEL", "mistral:instruct"),
    )

import os

CADENCE_SYSTEM = """You are EPOS.Cadence (Intent + Constraints).
Your job:
- compress the task into a precise intent
- identify risks
- enforce EPOS Constitution constraints
Return ONLY JSON with keys:
{
  "intent": {"category":"...", "summary":"...", "confidence":0.0-1.0},
  "constraints": ["..."],
  "edge_cases": ["..."],
  "acceptance": ["..."]
}
"""

METAPHOR_SYSTEM = """You are EPOS.Metaphor (Architecture + Implementation).
Your job:
- invent a working solution
- produce a Build Contract that can be executed deterministically
HARD RULES:
- Output ONLY valid JSON matching the EPOS Build Contract schema.
- Prefer additive changes (new files, patches) over overwrites.
- No destructive commands.
"""

CRITIC_SYSTEM = """You are EPOS.Critic (Adversarial QA).
Your job:
- attempt to break the proposed contract
- find missing imports, wrong paths, schema mismatches, OS issues, unsafe commands
Return ONLY JSON:
{
  "issues": [{"severity":"low|med|high","problem":"...","fix":"..."}],
  "verdict": "pass|fail"
}
"""

def duet_build_contract(*, task: str, cwd: str, os_hint: str = "gitbash", extra_context: str = "") -> Dict[str, Any]:
    layers = load_prompt_layers()

    cadence_user = f"""CWD: {cwd}
OS_HINT: {os_hint}

TASK:
{task}

EXTRA_CONTEXT:
{extra_context}
"""
    cadence_raw = call_llm(os.getenv("CADENCE_MODEL","phi3:mini"), layers + "\n\n" + CADENCE_SYSTEM, cadence_user, temperature=0.2)
    cadence = parse_or_repair_json(model=os.getenv("CADENCE_MODEL","phi3:mini"), system_prompt=layers + "\n\n" + CADENCE_SYSTEM, raw_text=cadence_raw)

    metaphor_user = f"""CWD: {cwd}
OS_HINT: {os_hint}
INTENT_JSON:
{json.dumps(cadence, indent=2)}

TASK:
{task}

EXTRA_CONTEXT:
{extra_context}

Now output a Build Contract JSON ONLY, matching schema exactly.
"""
    metaphor_raw = call_llm(os.getenv("METAPHOR_MODEL","phi4"), layers + "\n\n" + METAPHOR_SYSTEM, metaphor_user, temperature=0.2)
    contract = parse_or_repair_json(model=os.getenv("METAPHOR_MODEL","phi4"), system_prompt=layers + "\n\n" + METAPHOR_SYSTEM, raw_text=metaphor_raw)

    # Ensure metadata fields exist even if model forgets
    contract.setdefault("metadata", {})
    contract["metadata"].setdefault("cwd", cwd)
    contract["metadata"].setdefault("os_hint", os_hint)
    contract["metadata"].setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
    contract["metadata"].setdefault("models", {
        "cadence": os.getenv("CADENCE_MODEL","phi3:mini"),
        "metaphor": os.getenv("METAPHOR_MODEL","phi4"),
        "critic": os.getenv("CRITIC_MODEL","mistral:instruct"),
    })

    # Validate schema
    validate_contract(contract)

    # Critic pass (optional but recommended)
    critic_user = f"""Review this Build Contract JSON for breakage and risks.
Return ONLY the critic JSON schema.

CONTRACT:
{json.dumps(contract, indent=2)}
"""
    critic_raw = call_llm(os.getenv("CRITIC_MODEL","mistral:instruct"), layers + "\n\n" + CRITIC_SYSTEM, critic_user, temperature=0.0)
    critic = parse_or_repair_json(model=os.getenv("CRITIC_MODEL","mistral:instruct"), system_prompt=layers + "\n\n" + CRITIC_SYSTEM, raw_text=critic_raw)

    contract["_critic"] = critic
    contract["_cadence"] = cadence
    return contract

def save_run(contract: Dict[str, Any], out_dir: str = "out/duet_runs") -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = Path(out_dir) / f"duet_contract_{ts}.json"
    p.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return p
