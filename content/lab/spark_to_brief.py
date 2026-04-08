#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
spark_to_brief.py — Spark-to-Creative-Brief Converter
======================================================
Constitutional Authority: EPOS Constitution v3.1

Converts captured sparks (R1 Radar output) into Creative Briefs
that the A1 Architect can consume for script generation.

Uses GroqRouter for intelligent brief construction from raw spark content.
Falls back to template-based generation when LLM is unavailable.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

try:
    from groq_router import GroqRouter
except ImportError:
    GroqRouter = None

try:
    from epos_event_bus import EPOSEventBus
except ImportError:
    EPOSEventBus = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

from path_utils import get_context_vault


# ── Angle & Hook Libraries ─────────────────────────────────

ANGLE_TYPES = ["challenger", "architect", "steward", "educator", "storyteller"]
HOOK_TYPES = ["controversy", "question", "list", "statistic", "story", "how_to"]
VISUAL_MASKS = ["founder_glow", "schematic", "glitch", "clean_professional", "cinematic"]


class SparkToBriefConverter:
    """
    Converts raw sparks into structured Creative Briefs.

    Uses LLM to extract angle, hook type, premise, and CTA from spark content.
    Falls back to template-based generation when LLM unavailable.
    """

    BRIEF_SYSTEM_PROMPT = """You are a content strategist for Echoes Marketing.
Given a raw content spark (idea fragment), produce a structured Creative Brief.

Rules:
- angle_type: one of [challenger, architect, steward, educator, storyteller]
- hook_type: one of [controversy, question, list, statistic, story, how_to]
- visual_mask: one of [founder_glow, schematic, glitch, clean_professional, cinematic]
- script_premise: 1 sentence capturing the core insight
- hook_line: The exact opening line (must grab attention in 3 seconds)
- cta: The specific call to action

Return ONLY valid JSON with these keys:
{
  "angle_type": "...",
  "hook_type": "...",
  "visual_mask": "...",
  "script_premise": "...",
  "hook_line": "...",
  "cta": "..."
}"""

    def __init__(self, niche_id: str = "lego_affiliate", target_platform: str = "youtube_shorts"):
        self.niche_id = niche_id
        self.target_platform = target_platform
        self.vault = get_context_vault()
        self.sparks_dir = self.vault / "sparks"
        self.missions_dir = self.vault / "missions" / niche_id
        self.missions_dir.mkdir(parents=True, exist_ok=True)

    def convert_spark(self, spark_path: Path) -> dict:
        """Convert a single spark file into a Creative Brief."""
        spark = json.loads(spark_path.read_text(encoding="utf-8"))
        raw_content = spark.get("raw_content", "")
        tags = spark.get("tags", [])

        # Try LLM-based conversion
        brief_data = self._llm_convert(raw_content, tags)
        if not brief_data:
            brief_data = self._template_convert(raw_content, tags)

        # Build full brief
        brief_id = f"CB-{self.niche_id.upper().replace('_', '')[:6]}-{uuid.uuid4().hex[:4].upper()}"
        brief = {
            "brief_id": brief_id,
            "niche_id": self.niche_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_spark_id": spark.get("spark_id", "unknown"),
            "angle_type": brief_data.get("angle_type", "challenger"),
            "hook_type": brief_data.get("hook_type", "question"),
            "visual_mask": brief_data.get("visual_mask", "clean_professional"),
            "target_platform": self.target_platform,
            "script_premise": brief_data.get("script_premise", raw_content[:150]),
            "hook_line": brief_data.get("hook_line", raw_content[:80]),
            "cta": brief_data.get("cta", "Link in description."),
            "predicted_eri_score": 0,  # AN1 will predict this
            "affiliate_products": [],
            "status": "draft",
        }

        # Save brief
        brief_path = self.missions_dir / f"{brief_id}.json"
        brief_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")

        # Update spark status
        spark["status"] = "converted"
        spark["converted_to"] = brief_id
        spark_path.write_text(json.dumps(spark, indent=2), encoding="utf-8")

        # Publish event
        try:
            if EPOSEventBus:
                EPOSEventBus().publish("content.spark.converted",
                    {"spark_id": spark["spark_id"], "brief_id": brief_id},
                    source_module="spark_to_brief")
        except Exception:
            pass

        record_decision(
            decision_type="content.spark_converted",
            description=f"Spark {spark['spark_id']} -> Brief {brief_id}",
            agent_id="spark_to_brief",
            outcome="success",
            context={"spark_id": spark["spark_id"], "brief_id": brief_id,
                     "angle": brief["angle_type"], "hook": brief["hook_type"]},
        )

        return brief

    def _llm_convert(self, content: str, tags: list) -> Optional[dict]:
        """Use GroqRouter to intelligently construct a brief."""
        if not GroqRouter:
            return None
        try:
            router = GroqRouter()
            tag_str = ", ".join(tags) if tags else "general"
            prompt = (
                f"Raw spark content: \"{content}\"\n"
                f"Tags: {tag_str}\n"
                f"Niche: {self.niche_id}\n"
                f"Platform: {self.target_platform}\n\n"
                f"Generate a Creative Brief from this spark."
            )
            result = router.route("scripting", prompt,
                                   system_prompt=self.BRIEF_SYSTEM_PROMPT,
                                   max_tokens=300, temperature=0.6)
            # Parse JSON from response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass
        return None

    def _template_convert(self, content: str, tags: list) -> dict:
        """Fallback: template-based brief construction."""
        # Detect angle from content
        content_lower = content.lower()
        if any(w in content_lower for w in ["stop", "don't", "wrong", "most people"]):
            angle = "challenger"
        elif any(w in content_lower for w in ["build", "create", "system", "framework"]):
            angle = "architect"
        elif any(w in content_lower for w in ["protect", "care", "serve", "help"]):
            angle = "steward"
        else:
            angle = "educator"

        # Detect hook type
        if "?" in content:
            hook = "question"
        elif any(w in content_lower for w in ["top", "best", "worst", "5 ", "3 ", "10 "]):
            hook = "list"
        elif any(w in content_lower for w in ["how to", "how do", "step"]):
            hook = "how_to"
        else:
            hook = "controversy"

        return {
            "angle_type": angle,
            "hook_type": hook,
            "visual_mask": "glitch" if angle == "challenger" else "schematic",
            "script_premise": content[:150],
            "hook_line": content[:80],
            "cta": "Link in description.",
        }

    def convert_all_new(self, limit: int = 10) -> list:
        """Convert all sparks with status='new' into briefs."""
        converted = []
        for spark_path in sorted(self.sparks_dir.glob("SPARK-*.json")):
            if len(converted) >= limit:
                break
            spark = json.loads(spark_path.read_text(encoding="utf-8"))
            if spark.get("status") == "new":
                brief = self.convert_spark(spark_path)
                converted.append(brief)
                print(f"  {spark['spark_id']} -> {brief['brief_id']} [{brief['angle_type']}/{brief['hook_type']}]")
        return converted

    def get_unconverted_count(self) -> int:
        """Count sparks that haven't been converted yet."""
        count = 0
        for spark_path in self.sparks_dir.glob("SPARK-*.json"):
            spark = json.loads(spark_path.read_text(encoding="utf-8"))
            if spark.get("status") == "new":
                count += 1
        return count


if __name__ == "__main__":
    converter = SparkToBriefConverter()
    passed = 0

    # Test 1: Instantiation
    assert hasattr(converter, "convert_spark"), "Missing convert_spark"
    assert hasattr(converter, "convert_all_new"), "Missing convert_all_new"
    passed += 1

    # Test 2: Template fallback
    result = converter._template_convert(
        "Stop renting attention. Build your own audience.", ["sovereignty"])
    assert result["angle_type"] == "challenger", f"Expected challenger, got {result['angle_type']}"
    assert result["hook_type"] in HOOK_TYPES, f"Invalid hook type: {result['hook_type']}"
    passed += 1

    # Test 3: Count unconverted
    count = converter.get_unconverted_count()
    assert isinstance(count, int), "Should return int"
    passed += 1

    print(f"PASS: spark_to_brief ({passed} assertions)")
    print(f"Unconverted sparks: {count}")
