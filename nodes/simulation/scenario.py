# EPOS Artifact — MiroFish Stage 1
# Constitutional Authority: Articles V, X, XVI §2
"""
scenario.py — MiroFish Scenario Schema

A Scenario describes a product + market test. The simulator consumes it
and produces a structured report.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Product:
    title: str
    price_usd: float
    copy: str = ""                # or copy_path
    copy_path: str = ""
    audio_overview_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scenario:
    scenario_id: str
    product: Product
    avatars: list[str]                       # avatar IDs from nodes.simulation.avatars
    cycles: int = 60
    agents_per_cycle: int = 1000
    decision_prompt_template: str = (
        "You are evaluating a product for purchase.\n\n"
        "{avatar_block}\n\n"
        "PRODUCT:\n"
        "Title: {product_title}\n"
        "Price: ${price_usd}\n"
        "Copy: {product_copy}\n\n"
        "Respond ONLY in JSON with keys:\n"
        "  buy (bool), price_willingness_usd (number), top_objection (string),\n"
        "  confidence (1-10)\n"
    )
    model_pool: list[str] | None = None       # None ⇒ simulator defaults
    cycle_length_label: str = "month"         # narrative only

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Scenario":
        data = json.loads(text)
        product = Product(**data.pop("product"))
        return cls(product=product, **data)


def example() -> Scenario:
    return Scenario(
        scenario_id="stage1_gumroad_ccp_pack",
        product=Product(
            title="CCP Pack — Stop Sending Flat Prompts",
            price_usd=29.0,
            copy=(
                "A 4-ring methodology guide + prompt library + quick-start. "
                "Stop sending flat prompts. Start engineering context."
            ),
            copy_path="context_vault/doctrine/products/HIDDEN_PRODUCTS_PARTS_BIN_MATRIX.md",
            metadata={"platform": "gumroad", "category": "prompt-engineering"},
        ),
        avatars=[
            "founder_solo", "vp_marketing", "consultant_indie",
            "agency_ops_lead", "growth_hacker",
            "enterprise_innovation", "creator_studio", "small_service_owner",
        ],
        cycles=60,
        agents_per_cycle=1000,
    )


if __name__ == "__main__":
    s = example()
    out = Path("context_vault/simulation/scenarios")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{s.scenario_id}.json").write_text(s.to_json())
    print(f"wrote {out / (s.scenario_id + '.json')}")
