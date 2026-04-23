#!/usr/bin/env python3
# EPOS Artifact — BUILD 91 (Training Data Collection Pipeline)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
data_collection_pipeline.py — AAR → QLoRA training-pair extraction

Scans context_vault/aar/ for AAR documents, extracts:
  - Decisions made + rationale
  - Failures + fixes
  - Pattern names + examples

Emits training pairs in JSONL format:
    {instruction, input, output, metadata}

Per Reward Bus integration: every pair includes the reward signal
(positive / negative / neutral) inferred from the AAR's "Key Learning"
field and from Reward Bus scoring at T+24h/48h/90d where available.

Output: context_vault/training/pairs/<yyyymmdd>_<kind>.jsonl

This feeds the QLoRA training runner (BUILD 92, deferred — needs GPU).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
AAR_DIR = Path(os.getenv("EPOS_AAR_DIR", str(REPO / "context_vault" / "aar")))
OUT_DIR = Path(os.getenv("EPOS_TRAINING_PAIRS", str(REPO / "context_vault" / "training" / "pairs")))
REWARD_DIR = Path(os.getenv("EPOS_REWARDS_DIR", str(REPO / "context_vault" / "rewards")))


@dataclass
class TrainingPair:
    instruction: str
    input: str
    output: str
    metadata: dict[str, Any]


def extract_sections(text: str) -> dict[str, str]:
    """Split markdown into sections by H2 headings."""
    sections: dict[str, str] = {}
    current = "preamble"
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^#{1,2}\s+(.+)$", line)
        if m:
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()
    return sections


def extract_decisions(sections: dict[str, str]) -> list[dict]:
    """Pull decision-journal entries out of AAR sections."""
    decisions = []
    for key, body in sections.items():
        if "decision" in key:
            for line in body.splitlines():
                line = line.strip().lstrip("-* ")
                if not line:
                    continue
                decisions.append({"text": line, "section": key})
    return decisions


def extract_failures(sections: dict[str, str]) -> list[dict]:
    """Pull failure→fix pairs."""
    failures = []
    for key, body in sections.items():
        if any(k in key for k in ("failure", "blocker", "broken", "issue", "regression")):
            for line in body.splitlines():
                line = line.strip().lstrip("-* ")
                if not line:
                    continue
                failures.append({"text": line, "section": key})
    return failures


def reward_for(aar_path: Path) -> str:
    """Lookup Reward Bus signal for this AAR, if present."""
    aar_id = aar_path.stem
    reward_file = REWARD_DIR / f"{aar_id}.json"
    if reward_file.exists():
        try:
            data = json.loads(reward_file.read_text())
            return str(data.get("signal", "neutral"))
        except Exception:
            pass
    return "neutral"


def pairs_from_aar(path: Path) -> list[TrainingPair]:
    """Generate training pairs from a single AAR."""
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = extract_sections(text)
    pairs: list[TrainingPair] = []
    reward = reward_for(path)

    # Decision pairs: "given situation, explain the decision made"
    for d in extract_decisions(sections):
        pairs.append(TrainingPair(
            instruction="Given this situation, what decision did the Architect make and why?",
            input=sections.get("preamble", "")[:800] or "(no preamble)",
            output=d["text"][:800],
            metadata={"kind": "decision", "aar": path.name, "reward": reward,
                      "section": d["section"]},
        ))

    # Failure → fix pairs
    for f in extract_failures(sections):
        fix_text = sections.get("what we're changing", "") or sections.get("fix", "") \
                   or sections.get("remediation", "")
        if not fix_text.strip():
            continue
        pairs.append(TrainingPair(
            instruction="This failure occurred. What should be done to prevent it?",
            input=f["text"][:800],
            output=fix_text[:800],
            metadata={"kind": "failure_fix", "aar": path.name, "reward": reward,
                      "section": f["section"]},
        ))

    # Pattern naming pair
    key_learning = sections.get("key learning", "") or sections.get("lesson", "")
    if key_learning:
        summary = (sections.get("summary", "") or sections.get("what happened", "")
                   or sections.get("preamble", ""))[:800]
        pairs.append(TrainingPair(
            instruction="Name the pattern in this situation in one phrase.",
            input=summary,
            output=key_learning[:400],
            metadata={"kind": "pattern_name", "aar": path.name, "reward": reward},
        ))

    return pairs


def run() -> dict[str, Any]:
    """Scan all AARs, extract pairs, write per-kind JSONL bundles."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_pairs: list[TrainingPair] = []
    aar_count = 0
    for p in sorted(AAR_DIR.glob("*.md")):
        aar_count += 1
        try:
            all_pairs.extend(pairs_from_aar(p))
        except Exception as e:
            print(f"warn: {p.name}: {type(e).__name__}: {e}")

    by_kind: dict[str, list[dict]] = {}
    for pair in all_pairs:
        by_kind.setdefault(pair.metadata["kind"], []).append(asdict(pair))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_files = []
    for kind, items in by_kind.items():
        out = OUT_DIR / f"{stamp}_{kind}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item) + "\n")
        out_files.append({"kind": kind, "count": len(items), "path": str(out)})

    return {
        "aar_scanned": aar_count,
        "total_pairs": len(all_pairs),
        "by_kind": {k: len(v) for k, v in by_kind.items()},
        "output_files": out_files,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
