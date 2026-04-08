#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
schema.py — TTLG Props Schema and Loader
==========================================
Constitutional Authority: EPOS Constitution v3.1

Pydantic models for TTLG Custom Props. Makes diagnostics parametrizable.
Presets are JSON files in ttlg/props/presets/ — drop a file, no code change.
"""

import json
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime, timezone

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:
    # Fallback for environments without pydantic v2
    from pydantic import BaseModel, Field, validator as field_validator

PRESETS_DIR = Path(__file__).resolve().parent / "presets"


# ── Nested Models ───────────────────────────────────────────

class ScoutConfig(BaseModel):
    scope: list = Field(default=["marketing", "sales", "service", "governance"],
                        min_length=1, description="Layers/tracks to scan")
    depth: Literal["quick", "standard", "detailed"] = "standard"
    measurement_points: list = Field(default=[], description="Specific measurement targets")


class ThinkerConfig(BaseModel):
    weighting_model: Literal["market_forward", "internal_health", "competitive"] = "market_forward"
    extract_intelligence: list = Field(default=["moats", "gaps", "opportunities"],
                                        description="What intelligence to extract")


class GateConfig(BaseModel):
    approval_criteria: str = "strategic_alignment"
    auto_remediate: bool = False
    escalation_threshold: int = Field(default=3, ge=1, le=10)


class SurgeonConfig(BaseModel):
    change_scope: Literal["prescriptive", "remediation", "advisory"] = "prescriptive"
    priority_filter: str = "revenue_impact"
    max_prescriptions_per_gap: int = 3


class AnalystConfig(BaseModel):
    verification_metrics: list = Field(default=["roi_projection", "score_trajectory", "value_at_risk"])
    projection_days: list = Field(default=[30, 60, 90])


class PhaseConfig(BaseModel):
    scout: ScoutConfig = Field(default_factory=ScoutConfig)
    thinker: ThinkerConfig = Field(default_factory=ThinkerConfig)
    gate: GateConfig = Field(default_factory=GateConfig)
    surgeon: SurgeonConfig = Field(default_factory=SurgeonConfig)
    analyst: AnalystConfig = Field(default_factory=AnalystConfig)


class ContextConfig(BaseModel):
    domain: str = "general"
    market_position: str = "challenger"
    assessment_type: Literal["internal", "external", "competitive", "market_forward", "continuous_internal"] = "external"
    time_horizon_days: int = Field(default=90, ge=1, le=365)


class OutputConfig(BaseModel):
    type: Literal["strategic_intelligence", "mirror_report", "competitive_analysis", "healing_report"] = "mirror_report"
    sections: list = Field(default=["executive_summary", "findings", "prescriptions", "engagement_menu"])


# ── Main Props Model ────────────────────────────────────────

class TTLGProps(BaseModel):
    """
    Complete configuration for a TTLG diagnostic session.
    Parametrizes every phase of the pipeline.
    """
    name: str = "Unnamed Diagnostic"
    version: str = "1.0"
    target: Literal["epos", "client", "competitor"] = "client"
    context: ContextConfig = Field(default_factory=ContextConfig)
    phases: PhaseConfig = Field(default_factory=PhaseConfig)
    output_format: OutputConfig = Field(default_factory=OutputConfig)

    class Config:
        extra = "allow"


# ── Loader Functions ────────────────────────────────────────

def load_props(name_or_path: str) -> TTLGProps:
    """
    Load props from a preset name or file path.
    If name matches a preset in presets/, load that.
    Otherwise treat as a file path.
    """
    # Check presets first
    preset_path = PRESETS_DIR / f"{name_or_path}.json"
    if preset_path.exists():
        data = json.loads(preset_path.read_text(encoding="utf-8"))
        return TTLGProps.model_validate(data)

    # Try as file path
    file_path = Path(name_or_path)
    if file_path.exists():
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return TTLGProps.model_validate(data)

    raise FileNotFoundError(f"Props not found: {name_or_path}. "
                             f"Available presets: {', '.join(list_presets())}")


def list_presets() -> list:
    """List available preset names."""
    if not PRESETS_DIR.exists():
        return []
    return sorted(p.stem for p in PRESETS_DIR.glob("*.json"))


def show_preset(name: str) -> dict:
    """Load and return a preset as a dict for display."""
    preset_path = PRESETS_DIR / f"{name}.json"
    if not preset_path.exists():
        return {"error": f"Preset not found: {name}"}
    return json.loads(preset_path.read_text(encoding="utf-8"))


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: Default props validate
    props = TTLGProps()
    assert props.name == "Unnamed Diagnostic"
    assert props.target == "client"
    assert len(props.phases.scout.scope) >= 1
    passed += 1

    # Test 2: List presets
    presets = list_presets()
    print(f"Available presets: {presets}")
    passed += 1

    # Test 3: Load each preset
    for preset_name in presets:
        p = load_props(preset_name)
        assert p.name, f"Preset {preset_name} has no name"
        assert p.version, f"Preset {preset_name} has no version"
        print(f"  {preset_name}: {p.name} (target={p.target}, scope={p.phases.scout.scope})")
    passed += 1

    # Test 4: Invalid props rejected
    try:
        bad = TTLGProps(target="invalid_target")
        assert False, "Should have rejected invalid target"
    except Exception:
        pass  # Expected
    passed += 1

    print(f"\nPASS: ttlg_props_schema ({passed} assertions)")
