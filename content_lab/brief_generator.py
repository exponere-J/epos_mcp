#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
brief_generator.py — Avatar-Calibrated Content Brief Generator
====================================================================
Constitutional Authority: EPOS Constitution v3.1 — Content Lab Subsystem

Generates content briefs that carry avatar intelligence directly into
A1 Architect's scripting pipeline. The brief is the instruction set
A1 follows — it includes vocabulary constraints, tone, angle, format,
CTA tokens, and optimization notes from the Echolocation Predictor.

Core operations:
  - generate_brief(spark, avatar, prediction) -> brief dict
  - generate_variants(spark, avatar, prediction) -> 3 Triple-Threat briefs
  - save_brief(brief) -> path
  - health_check()
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from path_utils import get_context_vault

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

VAULT = get_context_vault()
BRIEFS_ROOT = VAULT / "content" / "briefs"
BRIEFS_ROOT.mkdir(parents=True, exist_ok=True)
BRIEFS_LOG = BRIEFS_ROOT / "briefs.jsonl"

# Triple-Threat angle definitions
ANGLES = {
    "challenger": {
        "stance": "Confrontational / myth-busting",
        "opening_strategy": "Name the uncomfortable truth they avoid",
        "proof_style": "Stark comparisons, lost dollars, missed opportunity",
    },
    "architect": {
        "stance": "Framework / systems-thinking",
        "opening_strategy": "Reframe the problem as a system, not an event",
        "proof_style": "Diagrams, processes, before/after architecture",
    },
    "closer": {
        "stance": "Action-oriented / urgency",
        "opening_strategy": "Time-sensitive opportunity cost",
        "proof_style": "Countdown, scarcity, case study with clear CTA",
    },
}


class ContentBriefGenerator:
    """Generates avatar-calibrated content briefs for A1 Architect."""

    def __init__(self, briefs_root: Optional[Path] = None):
        self.briefs_root = Path(briefs_root) if briefs_root else BRIEFS_ROOT
        self.briefs_root.mkdir(parents=True, exist_ok=True)

    def generate_brief(self, spark: dict, avatar: dict,
                       prediction: Optional[dict] = None,
                       angle: str = "architect") -> dict:
        """Generate a single avatar-calibrated brief."""
        brief_id = f"BRIEF-{uuid.uuid4().hex[:10]}"
        topic = spark.get("topic", spark.get("title", "untitled"))
        avatar_id = avatar.get("avatar_id", "unknown")

        comm = avatar.get("communication_preferences", {}) or {}
        demo = avatar.get("demographics", {}) or {}
        price = avatar.get("price_tolerance", {}) or {}
        channels = avatar.get("channels", {}) or {}
        conv = avatar.get("conversion_path", {}) or {}

        # Preferred format — first of communication_preferences.format list
        formats = comm.get("format", []) or ["linkedin_post"]
        preferred_format = formats[0] if isinstance(formats, list) else str(formats)

        # Vocabulary — include signal_keywords + comm vocabulary, exclude exclusion_keywords
        vocab_include = list(avatar.get("signal_keywords", []))[:10]
        vocab_exclude = list(avatar.get("exclusion_keywords", []))[:10]
        if comm.get("vocabulary"):
            vocab_include.extend([w.strip() for w in comm["vocabulary"].split(",")[:6]])

        # Hook — craft from top pain point + angle
        pains = avatar.get("pain_points", [])
        top_pain = max(pains, key=lambda p: p.get("severity", 0))["pain"] if pains else topic
        hook = self._craft_hook(top_pain, topic, angle, avatar)

        # Structure
        structure = self._craft_structure(topic, avatar, angle, conv)

        # Constraints
        constraints = self._craft_constraints(comm, avatar)

        # CTA token
        date_str = datetime.now(timezone.utc).strftime("%Y-%m")
        topic_slug = "-".join(topic.upper().split()[:3])[:40]
        cta_token = f"ECHO-{date_str}-{avatar_id.upper()}-{topic_slug}"

        predicted_score = (prediction or {}).get("predicted_score", 65)
        optimizations = (prediction or {}).get("optimization_suggestions", [])

        brief = {
            "brief_id": brief_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "topic": topic,
            "target_avatar": avatar_id,
            "avatar_display_name": avatar.get("display_name"),
            "angle": angle,
            "angle_stance": ANGLES.get(angle, {}).get("stance"),
            "format": preferred_format,
            "tone": comm.get("tone", "professional, clear, direct"),
            "vocabulary_include": vocab_include,
            "vocabulary_exclude": vocab_exclude,
            "hook": hook,
            "structure": structure,
            "cta_token": cta_token,
            "constraints": constraints,
            "predicted_resonance": predicted_score,
            "optimization_notes": optimizations,
            "primary_channels": channels.get("primary", []),
            "proof_type": comm.get("proof_type", ""),
            "price_tolerance": price,
            "prediction_id": (prediction or {}).get("prediction_id"),
            "spark_ref": spark.get("spark_id") or spark.get("path"),
        }

        self.save_brief(brief)

        if _BUS:
            try:
                _BUS.publish("content.brief.generated", {
                    "brief_id": brief_id,
                    "target_avatar": avatar_id,
                    "angle": angle,
                    "predicted_resonance": predicted_score,
                }, source_module="brief_generator")
            except Exception:
                pass

        return brief

    def generate_variants(self, spark: dict, avatar: dict,
                          prediction: Optional[dict] = None) -> list[dict]:
        """Generate 3 Triple-Threat briefs (challenger, architect, closer)."""
        variants = []
        for angle in ("challenger", "architect", "closer"):
            variants.append(self.generate_brief(spark, avatar, prediction, angle=angle))
        return variants

    # ── Internals ─────────────────────────────────────────────────

    def _craft_hook(self, top_pain: str, topic: str, angle: str, avatar: dict) -> str:
        proof_type = (avatar.get("communication_preferences", {}) or {}).get("proof_type", "")
        price_floor = (avatar.get("price_tolerance", {}) or {}).get("monthly_floor", 0)

        if angle == "challenger":
            if "dollar" in proof_type.lower() or price_floor:
                return f"You're losing money every week because of this: {top_pain.lower()}."
            return f"Most operators don't realize: {top_pain.lower()} is costing them more than they think."
        elif angle == "architect":
            return f"There's a system-level fix for this: {top_pain.lower()}. Here's the architecture."
        elif angle == "closer":
            return f"If you don't fix {top_pain.lower()} this month, next quarter is already compromised."
        return f"About {topic}: {top_pain}"

    def _craft_structure(self, topic: str, avatar: dict, angle: str, conv: dict) -> dict:
        proof_type = (avatar.get("communication_preferences", {}) or {}).get("proof_type", "")
        return {
            "opening": f"Acknowledge the specific reality this avatar lives in — use their vocabulary, not yours.",
            "value": f"Name the cost of {topic} in terms this avatar tracks (time, money, or reputation).",
            "evidence": f"Show proof in the format they trust: {proof_type or 'quantified outcome'}.",
            "system": f"Present the fix as a repeatable system, not a one-off tactic.",
            "cta": conv.get("interest", "Offer the diagnostic as the next step."),
            "signoff": "1% daily. 37x annually.",
        }

    def _craft_constraints(self, comm: dict, avatar: dict) -> dict:
        length_pref = (comm.get("length") or "").lower()
        if "short" in length_pref or "60" in length_pref:
            max_words = 200
        elif "medium" in length_pref:
            max_words = 500
        elif "long" in length_pref:
            max_words = 1200
        else:
            max_words = 400

        proof_type = (comm.get("proof_type") or "").lower()
        return {
            "max_words": max_words,
            "must_include_dollar_amount": "dollar" in proof_type or "number" in proof_type,
            "must_include_comparison": "before" in proof_type or "after" in proof_type,
            "must_include_screenshot": "screenshot" in proof_type,
            "must_include_case_study": "case stud" in proof_type,
            "preferred_send_time": self._guess_send_time(avatar),
        }

    def _guess_send_time(self, avatar: dict) -> str:
        aid = avatar.get("avatar_id", "")
        if "local" in aid:
            return "05:00-07:00 local"
        if "agency" in aid or "fractional" in aid or "boutique" in aid or "consultant" in aid:
            return "07:00-09:00 local"
        if "creative" in aid or "solo_operator" in aid:
            return "evenings + weekends"
        if "technical" in aid:
            return "late morning or late evening"
        return "09:00 local"

    def save_brief(self, brief: dict) -> Path:
        path = self.briefs_root / f"{brief['brief_id']}.json"
        path.write_text(json.dumps(brief, indent=2), encoding="utf-8")
        with open(BRIEFS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "brief_id": brief["brief_id"],
                "avatar": brief["target_avatar"],
                "angle": brief["angle"],
                "predicted_resonance": brief.get("predicted_resonance"),
            }) + "\n")
        return path

    def health_check(self) -> dict:
        try:
            count = len(list(self.briefs_root.glob("BRIEF-*.json")))
            return {
                "node": "brief_generator",
                "status": "operational",
                "briefs_generated": count,
                "briefs_root": str(self.briefs_root),
            }
        except Exception as e:
            return {"node": "brief_generator", "status": "error", "error": str(e)[:200]}


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    from nodes.avatar_registry import AvatarRegistry
    from content_lab.echolocation_predictor import EcholocationPredictor

    passed = 0
    gen = ContentBriefGenerator()
    reg = AvatarRegistry()
    pred = EcholocationPredictor()

    # Test 1: Generate a brief for local_champion
    avatar = reg.get_avatar("local_champion")
    assert avatar is not None
    spark = {"spark_id": "SPARK-TEST-001", "topic": "lead follow-up automation for service businesses"}
    prediction = pred.predict_resonance(
        topic=spark["topic"], avatar_id="local_champion",
        format="email", angle="challenger"
    )
    brief = gen.generate_brief(spark, avatar, prediction, angle="challenger")
    assert brief["brief_id"].startswith("BRIEF-")
    assert brief["target_avatar"] == "local_champion"
    assert brief["angle"] == "challenger"
    assert brief["hook"]
    assert brief["cta_token"].startswith("ECHO-")
    assert brief["vocabulary_exclude"], "Expected exclusion vocabulary"
    print(f"Brief: {brief['brief_id']}")
    print(f"  Hook: {brief['hook']}")
    print(f"  CTA token: {brief['cta_token']}")
    print(f"  Vocab exclude: {brief['vocabulary_exclude'][:4]}")
    print(f"  Max words: {brief['constraints']['max_words']}")
    passed += 1

    # Test 2: Variants (Triple-Threat)
    variants = gen.generate_variants(spark, avatar, prediction)
    assert len(variants) == 3
    angles = {v["angle"] for v in variants}
    assert angles == {"challenger", "architect", "closer"}
    print(f"Variants: {[v['angle'] for v in variants]}")
    passed += 1

    # Test 3: Different avatar — agency_builder
    agency = reg.get_avatar("agency_builder")
    brief2 = gen.generate_brief(
        {"spark_id": "SPARK-TEST-002", "topic": "agency margin recovery playbook"},
        agency,
        None,
        angle="architect"
    )
    assert brief2["target_avatar"] == "agency_builder"
    assert brief2["constraints"]["max_words"] >= 500
    print(f"Agency brief max words: {brief2['constraints']['max_words']}")
    passed += 1

    # Test 4: Brief is persisted
    saved = list(gen.briefs_root.glob(f"{brief['brief_id']}.json"))
    assert saved
    passed += 1

    # Test 5: Health
    h = gen.health_check()
    assert h["status"] == "operational"
    assert h["briefs_generated"] >= 4
    print(f"Health: {h['status']} briefs={h['briefs_generated']}")
    passed += 1

    print(f"\nPASS: brief_generator ({passed} assertions)")
