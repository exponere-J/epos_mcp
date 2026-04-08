#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
rs1_research_brief.py — EPOS Research Brief Generator
======================================================
Constitutional Authority: EPOS Constitution v3.1
Module: RS1 Research Brief (CODE DIRECTIVE Module 3)

Generates structured 7-vector research briefs for ideas triaged as "research".
Vectors: Market, Technical, Competitive, Resource, Risk, Timeline, Sovereignty.

Flow: Triaged idea (verdict=research) → RS1 Brief → Decision gate → Build queue
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict

from path_utils import get_context_vault
from groq_router import GroqRouter
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision


RESEARCH_VECTORS = [
    "market_opportunity",    # Is there demand? What's the TAM?
    "technical_feasibility", # Can we build it? What stack?
    "competitive_landscape", # Who else does this? What's our edge?
    "resource_requirements", # Time, money, skills needed
    "risk_assessment",       # What could go wrong? Mitigations
    "timeline_estimate",     # How long? Dependencies?
    "sovereignty_alignment", # Does it align with EPOS constitution and mission?
]


class RS1ResearchBrief:
    """Generates 7-vector research briefs for idea triage pipeline."""

    def __init__(self):
        self.vault = get_context_vault()
        self.briefs_dir = self.vault / "ideas" / "briefs"
        self.briefs_dir.mkdir(parents=True, exist_ok=True)
        self.router = GroqRouter()
        self.bus = EPOSEventBus()

    def generate_brief(self, idea: dict, depth: str = "standard") -> dict:
        """Generate a 7-vector research brief for an idea.

        Args:
            idea: The idea dict from IdeaLog
            depth: "quick" (3 vectors), "standard" (7 vectors), "deep" (7 + follow-up)
        """
        brief_id = f"RB-{uuid.uuid4().hex[:8]}"
        title = idea.get("title", "Untitled")
        description = idea.get("description", "")
        category = idea.get("category", "feature")
        tags = idea.get("tags", [])

        print(f"  [RS1] Generating brief: {brief_id} for '{title}'")

        vectors_to_run = RESEARCH_VECTORS[:3] if depth == "quick" else RESEARCH_VECTORS
        analyses = {}

        for vector in vectors_to_run:
            analysis = self._analyze_vector(vector, title, description, category, tags)
            analyses[vector] = analysis

        # Generate executive summary
        summary = self._synthesize_summary(title, analyses)

        # Build recommendation
        recommendation = self._generate_recommendation(title, analyses)

        brief = {
            "brief_id": brief_id,
            "idea_id": idea.get("idea_id"),
            "title": title,
            "description": description,
            "category": category,
            "tags": tags,
            "depth": depth,
            "vectors": analyses,
            "executive_summary": summary,
            "recommendation": recommendation,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store brief
        brief_path = self.briefs_dir / f"{brief_id}.json"
        brief_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")

        # Update idea with brief reference
        try:
            from idea_log import IdeaLog
            log = IdeaLog()
            # Read, update, rewrite the idea
            lines = log.log_path.read_text(encoding="utf-8").splitlines()
            new_lines = []
            for line in lines:
                if line.strip():
                    try:
                        i = json.loads(line)
                        if i.get("idea_id") == idea.get("idea_id"):
                            i["research_brief_id"] = brief_id
                            i["updated_at"] = datetime.now(timezone.utc).isoformat()
                        new_lines.append(json.dumps(i))
                    except Exception:
                        new_lines.append(line)
            log.log_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        except Exception:
            pass

        # Publish event
        self.bus.publish("rs1.brief.generated", {
            "brief_id": brief_id,
            "idea_id": idea.get("idea_id"),
            "recommendation": recommendation.get("verdict", "review"),
        }, "rs1_research_brief")

        # Record decision
        record_decision(
            decision_type="rs1.brief.generated",
            description=f"Research brief generated: {title}",
            agent_id="rs1_research_brief",
            outcome="success",
            context={"brief_id": brief_id, "vectors_analyzed": len(analyses)},
        )

        print(f"  [RS1] Brief complete: {brief_id}")
        return brief

    def _analyze_vector(self, vector: str, title: str, description: str,
                        category: str, tags: list) -> dict:
        """Analyze one research vector using Groq."""
        vector_prompts = {
            "market_opportunity": "Analyze the market opportunity. Who needs this? What's the potential TAM? Is there existing demand?",
            "technical_feasibility": "Assess technical feasibility. What technology stack is needed? Are there existing tools/APIs? What's the complexity?",
            "competitive_landscape": "Map the competitive landscape. Who offers similar solutions? What's our differentiation? Open-source alternatives?",
            "resource_requirements": "Estimate resource requirements. Developer time, tools, APIs, costs. What skills are needed?",
            "risk_assessment": "Identify risks. What could go wrong? Dependencies? Vendor lock-in? Technical debt? Mitigations?",
            "timeline_estimate": "Estimate timeline. Quick win (hours) or long build (weeks)? Dependencies on other modules? Phases?",
            "sovereignty_alignment": "Assess alignment with EPOS sovereignty principles. Does this increase autonomy? Open-source preference? Constitutional compliance?",
        }

        prompt = (
            f"You are an intelligence analyst for EPOS/EXPONERE.\n"
            f"IDEA: {title}\n"
            f"DESCRIPTION: {description}\n"
            f"CATEGORY: {category}\n"
            f"TAGS: {', '.join(tags)}\n\n"
            f"VECTOR: {vector}\n"
            f"TASK: {vector_prompts.get(vector, 'Analyze this dimension.')}\n\n"
            f"Respond in JSON:\n"
            f'{{"score": 1-10, "assessment": "2-3 sentences", "key_findings": ["finding1", "finding2"], "action_items": ["item1"]}}\n'
            f"Output ONLY valid JSON."
        )

        try:
            raw = self.router.route("fast", prompt, max_tokens=300, temperature=0.2)
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()
            return json.loads(clean)
        except Exception:
            return {
                "score": 5,
                "assessment": f"Analysis pending for {vector}. Manual review recommended.",
                "key_findings": ["Auto-analysis unavailable"],
                "action_items": ["Review manually"],
            }

    def _synthesize_summary(self, title: str, analyses: dict) -> str:
        """Generate executive summary from vector analyses."""
        scores = {v: a.get("score", 5) for v, a in analyses.items()}
        avg_score = sum(scores.values()) / max(len(scores), 1)

        try:
            vector_text = "\n".join(
                f"{v}: {a.get('score', 5)}/10 — {a.get('assessment', '')[:100]}"
                for v, a in analyses.items()
            )
            raw = self.router.route("fast",
                f"Synthesize a 3-sentence executive summary for this research brief.\n"
                f"IDEA: {title}\nAVG SCORE: {avg_score:.1f}/10\n\n"
                f"VECTOR ANALYSES:\n{vector_text}\n\n"
                f"Be direct, specific, and action-oriented. No fluff.",
                max_tokens=200, temperature=0.3)
            return raw.strip()
        except Exception:
            return f"Research brief for '{title}' — average score {avg_score:.1f}/10 across {len(analyses)} vectors."

    def _generate_recommendation(self, title: str, analyses: dict) -> dict:
        """Generate build/no-build recommendation."""
        scores = {v: a.get("score", 5) for v, a in analyses.items()}
        avg = sum(scores.values()) / max(len(scores), 1)

        if avg >= 7.5:
            verdict = "build"
            urgency = "high"
        elif avg >= 5.5:
            verdict = "build"
            urgency = "medium"
        elif avg >= 4.0:
            verdict = "defer"
            urgency = "low"
        else:
            verdict = "park"
            urgency = "none"

        return {
            "verdict": verdict,
            "urgency": urgency,
            "avg_score": round(avg, 1),
            "highest_vector": max(scores, key=scores.get) if scores else None,
            "lowest_vector": min(scores, key=scores.get) if scores else None,
            "scores": scores,
        }

    def get_brief(self, brief_id: str) -> Optional[dict]:
        """Load a brief by ID."""
        path = self.briefs_dir / f"{brief_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def list_briefs(self, limit: int = 20) -> list:
        """List all research briefs."""
        briefs = []
        for f in sorted(self.briefs_dir.glob("RB-*.json"), reverse=True):
            try:
                briefs.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
            if len(briefs) >= limit:
                break
        return briefs


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile

    py_compile.compile("rs1_research_brief.py", doraise=True)
    print("PASS: rs1_research_brief.py compiles clean")

    gen = RS1ResearchBrief()

    # Test with a mock idea
    test_idea = {
        "idea_id": "IDEA-TEST001",
        "title": "Automated YouTube thumbnail A/B testing",
        "description": "Use open vision models to score thumbnail variants before upload",
        "category": "content",
        "tags": ["youtube", "thumbnails", "ab-testing", "vision"],
        "priority": "high",
    }

    brief = gen.generate_brief(test_idea, depth="quick")
    assert brief["brief_id"].startswith("RB-")
    assert len(brief["vectors"]) == 3  # quick = 3 vectors
    assert brief["recommendation"]["verdict"] in ("build", "defer", "park")
    print(f"PASS: Brief generated — {brief['brief_id']}")
    print(f"  Recommendation: {brief['recommendation']['verdict']} "
          f"(avg {brief['recommendation']['avg_score']}/10)")
    print(f"  Summary: {brief['executive_summary'][:120]}")

    # Test list
    briefs = gen.list_briefs()
    assert len(briefs) >= 1
    print(f"PASS: Listed {len(briefs)} briefs")

    print("\nPASS: RS1ResearchBrief — all tests passed")
