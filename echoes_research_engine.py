#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
echoes_research_engine.py — Echoes Authority Content Engine
=============================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/echoes_research_engine.py

The L1 Intelligence layer. Generates white papers, newsletter briefs,
tool reviews, and model benchmarks. Builds audience and authority.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from groq_router import GroqRouter
from path_utils import get_context_vault
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus


@dataclass
class ResearchBrief:
    brief_id: str
    title: str
    category: str
    body: str
    key_findings: list
    recommendation: str
    sources: list
    output_formats: list
    generated_at: str
    ready_for_publication: bool = False


class EchoesResearchEngine:
    """
    Generates white papers, newsletter briefs, tool reviews.
    Scheduled via EVL1/TTLGScheduler. On-demand via LiveQuery.
    """

    CONFIG_PATH = Path(__file__).resolve().parent / "context_vault" / "echoes" / "intelligence_config.json"

    def __init__(self):
        self.router = GroqRouter()
        self.vault = get_context_vault()
        self.briefs_path = self.vault / "echoes" / "research_briefs"
        self.briefs_path.mkdir(parents=True, exist_ok=True)
        self.bus = EPOSEventBus()
        if self.CONFIG_PATH.exists():
            self.config = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        else:
            self.config = {"version": "1.0", "monitoring_streams": {}}

    def generate_white_paper_brief(self, topic: str, category: str,
                                    research_data: dict,
                                    audience: str = "content creators and marketing professionals") -> ResearchBrief:
        prompt = f"""You are the chief research analyst for Echoes Marketing.
Echoes is the leading authority on content creation, AI tools, and digital marketing.

Topic: {topic}
Category: {category}
Target audience: {audience}
Research data:
{json.dumps(research_data, indent=2)[:3000]}

Write a research brief:

TITLE: [compelling title]

EXECUTIVE SUMMARY:
[3 sentences. What, what changed, why it matters. Plain language. TTS-friendly.]

KEY FINDINGS:
[5 findings. Each a complete sentence. No bullet points.]

PRACTICAL IMPLICATIONS:
[What changes for creators and businesses. 2-3 sentences.]

ECHOES RECOMMENDATION:
[One clear recommendation. One sentence.]

WHAT TO WATCH NEXT:
[One sentence.]

Voice: direct, authoritative, no hype, accessible."""

        body = self.router.route("reasoning", prompt, max_tokens=1200, temperature=0.4)

        brief = ResearchBrief(
            brief_id=f"WP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}",
            title=topic, category=category, body=body,
            key_findings=self._extract_findings(body),
            recommendation=self._extract_recommendation(body),
            sources=list(research_data.keys()),
            output_formats=self.config.get("monitoring_streams", {}).get(
                category, {}).get("output_formats", ["white_paper_brief"]),
            generated_at=datetime.now(timezone.utc).isoformat(),
            ready_for_publication=True,
        )

        path = self.briefs_path / f"{brief.brief_id}.json"
        path.write_text(json.dumps(asdict(brief), indent=2), encoding="utf-8")

        record_decision(
            decision_type="research.brief_generated",
            description=f"White paper brief: {topic[:60]}",
            agent_id="echoes_research", outcome="success",
            context={"brief_id": brief.brief_id, "category": category},
        )
        try:
            self.bus.publish("research.brief.generated",
                             {"brief_id": brief.brief_id, "topic": topic}, "echoes_research_engine")
        except Exception:
            pass
        return brief

    def generate_newsletter_item(self, topic: str, signal: str) -> str:
        prompt = f"""Write a newsletter item for The Signal — Echoes Marketing's weekly brief.

Topic: {topic}
Signal: {signal}

Format: [Opening: the development] [2-3 sentences: what it means] [1 sentence: what to do]
150-200 words max. Voice: direct, warm, intelligent. Like a trusted colleague."""
        return self.router.route("reasoning", prompt, max_tokens=400, temperature=0.5)

    def generate_tool_review(self, tool_name: str, tool_data: dict) -> dict:
        prompt = f"""Write a concise tool review for the Echoes tool directory.

Tool: {tool_name}
Data: {json.dumps(tool_data, indent=2)[:1500]}

Structure: WHAT IT DOES | BEST FOR | NOT FOR | COST | ECHOES VERDICT
Voice: honest, specific, no affiliate bias."""
        review = self.router.route("reasoning", prompt, max_tokens=400, temperature=0.3)
        return {"tool_id": tool_name.lower().replace(" ", "_"), "tool_name": tool_name,
                "review": review, "reviewed_at": datetime.now(timezone.utc).isoformat()}

    def _extract_findings(self, body: str) -> list:
        findings = []
        in_findings = False
        for line in body.splitlines():
            if "KEY FINDINGS" in line.upper():
                in_findings = True
                continue
            if "PRACTICAL" in line.upper() or "IMPLICATIONS" in line.upper():
                break
            if in_findings and line.strip():
                findings.append(line.strip())
        return findings[:5]

    def _extract_recommendation(self, body: str) -> str:
        in_rec = False
        for line in body.splitlines():
            if "RECOMMENDATION" in line.upper():
                in_rec = True
                continue
            if "WATCH" in line.upper():
                break
            if in_rec and line.strip():
                return line.strip()
        return ""


if __name__ == "__main__":
    engine = EchoesResearchEngine()

    assert engine.config["version"] == "1.0"
    print("  Config: loaded")

    brief = engine.generate_white_paper_brief(
        topic="Why fal.ai is the unified API gateway for all AI production",
        category="model_releases",
        research_data={"fal_ai_models": "1000+ models", "pricing": "pay-per-use",
                       "key_advantage": "single API key accesses every major model"})
    assert brief.brief_id.startswith("WP-")
    assert len(brief.body) > 200
    print(f"  Brief: {brief.brief_id} ({len(brief.body)} chars)")
    print(f"  Recommendation: {brief.recommendation[:80]}")

    item = engine.generate_newsletter_item(
        "Runway Gen-4.5 sets new cinematic benchmark", "1247 Elo score")
    assert len(item) > 100
    print(f"  Newsletter: {len(item)} chars")

    review = engine.generate_tool_review("fal.ai",
        {"models": "1000+", "pricing": "pay-per-use", "api": "single_key"})
    assert "review" in review
    print(f"  Tool review: generated")

    print("\nPASS: EchoesResearchEngine — L1 authority layer ready")
