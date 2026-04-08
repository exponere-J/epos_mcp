from __future__ import annotations

from pathlib import Path

DEFAULT_LAYERS = [
    "brand/prompt_layers/00_manifesto.md",
    "brand/prompt_layers/01_constitution.md",
    "brand/prompt_layers/02_icp.md",
    "brand/prompt_layers/03_brand_voice.md",
    "brand/prompt_layers/04_doctrine_engineering.md",
]

def load_prompt_layers(paths: list[str] | None = None) -> str:
    paths = paths or DEFAULT_LAYERS
    parts: list[str] = []
    for p in paths:
        text = Path(p).read_text(encoding="utf-8")
        parts.append(f"\n---\n# LAYER: {p}\n{text}\n")
    return "\n".join(parts).strip()
