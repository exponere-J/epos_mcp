#!/usr/bin/env python3
# EPOS Artifact — SCC Persona Loader
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
SCC persona loader.

Each persona lives as a .md file in this directory and is loaded by name
(e.g. load_persona("architect") → returns the text of architect.md).

A persona represents a stable operating mode — system-prompt text, output
schema, refusal conditions. SCC consumes the text as a prefix to its
system prompt when entering the named mode.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Persona:
    name: str
    path: Path
    text: str
    sha256_16: str


def list_personas() -> list[str]:
    return sorted(p.stem for p in _HERE.glob("*.md"))


def load_persona(name: str) -> Persona:
    path = _HERE / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"persona '{name}' not found at {path}")
    text = path.read_text(encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return Persona(name=name, path=path, text=text, sha256_16=sha)


if __name__ == "__main__":
    for name in list_personas():
        p = load_persona(name)
        print(f"{name:<20}  sha={p.sha256_16}  {len(p.text)} chars")
