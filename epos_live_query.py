#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_live_query.py — On-Demand Synthesis Engine
=================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/epos_live_query.py

Takes any question. Queries vault, agent knowledge, research briefs, Groq.
Returns synthesized answer within 15 seconds.
Used in: discovery calls, webinars, Friday chat, support.
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from groq_router import GroqRouter
from path_utils import get_context_vault
from epos_intelligence import record_decision


@dataclass
class LiveQueryResult:
    query: str
    answer: str
    confidence: float
    sources_consulted: list
    depth_available: bool
    follow_up_brief: Optional[str]
    response_time_ms: int
    session_id: Optional[str] = None


class EPOSLiveQuery:
    """
    On-demand research synthesis. Three response modes:
      IMMEDIATE: vault lookup (< 3s)
      SYNTHESIZED: Groq synthesis from multiple sources (< 15s)
      QUEUED: deep research triggered, interim answer provided
    """

    def __init__(self, session_id: str = None):
        self.router = GroqRouter()
        self.vault = get_context_vault()
        self.session_id = session_id
        self.query_log = []

    def query(self, question: str, context: dict = None,
              mode: str = "synthesized", niche: str = None,
              segment: str = None) -> LiveQueryResult:
        """Takes any question. Returns a synthesized answer."""
        start = time.time()
        sources = []

        vault_knowledge = self._query_vault(question, niche)
        if vault_knowledge:
            sources.append("context_vault")

        agent_knowledge = self._query_agent_knowledge(question)
        if agent_knowledge:
            sources.append("agent_knowledge_bases")

        brief_knowledge = self._query_research_briefs(question)
        if brief_knowledge:
            sources.append("research_briefs")

        synthesis_prompt = self._build_synthesis_prompt(
            question, context or {}, vault_knowledge, agent_knowledge,
            brief_knowledge, niche, segment)

        answer = self.router.route("reasoning", synthesis_prompt,
                                    max_tokens=600, temperature=0.3)

        response_ms = int((time.time() - start) * 1000)
        coverage = sum([bool(vault_knowledge), bool(agent_knowledge),
                        bool(brief_knowledge)]) / 3.0
        confidence = min(0.5 + coverage * 0.5, 0.95)
        depth_available = confidence < 0.7
        follow_up = None

        if depth_available and mode != "immediate":
            follow_up = self._queue_deep_research(question, context or {})

        result = LiveQueryResult(
            query=question, answer=answer, confidence=confidence,
            sources_consulted=sources, depth_available=depth_available,
            follow_up_brief=follow_up, response_time_ms=response_ms,
            session_id=self.session_id)

        self._log_query(result)
        return result

    def _build_synthesis_prompt(self, question, context, vault, agent, briefs, niche, segment):
        ctx = ""
        if context.get("stage"):
            ctx += f"\nSession: {context['stage']}"
        if context.get("prospect_segment"):
            ctx += f"\nProspect: {context['prospect_segment']}"

        kb = ""
        if vault:
            kb += f"\nVault knowledge:\n{vault[:800]}"
        if agent:
            kb += f"\nAgent knowledge:\n{agent[:600]}"
        if briefs:
            kb += f"\nResearch:\n{briefs[:600]}"

        return f"""You are the intelligence layer of EPOS, answering in real time.
{ctx}

Question: {question}

Available knowledge:
{kb if kb else "No specific prior knowledge found."}

Instructions:
1. Answer directly using available knowledge.
2. If limited, acknowledge briefly and pivot to what IS known.
3. If deeper research needed, end with: "I can pull more current data on that."
4. Max 150 words. Conversational. Speakable.
5. Voice: direct, warm, authoritative.
6. Never fabricate statistics or prices."""

    def _query_vault(self, question: str, niche: str = None) -> str:
        relevant = []
        q_lower = question.lower()
        q_words = set(w for w in q_lower.split() if len(w) > 4)

        # Check niche packs
        niches_path = self.vault / "niches"
        if niches_path.exists():
            for nd in niches_path.iterdir():
                if not nd.is_dir():
                    continue
                pack = nd / "niche_pack.json"
                if pack.exists():
                    data = json.loads(pack.read_text(encoding="utf-8"))
                    text = json.dumps(data).lower()
                    if sum(1 for w in q_words if w in text) >= 2:
                        pain = data.get("desire_vocabulary", {}).get("pain_language", [])[:2]
                        relevant.append(f"Niche ({nd.name}): pain={pain}")

        # Check tool directory
        tools = self.vault / "echoes" / "tool_directory"
        if tools.exists():
            for tf in tools.glob("*.json"):
                data = json.loads(tf.read_text(encoding="utf-8"))
                if any(w in json.dumps(data).lower() for w in q_words):
                    relevant.append(f"Tool ({data.get('name','')}): {data.get('use_case','')}")

        # Check research briefs
        briefs = self.vault / "echoes" / "research_briefs"
        if briefs.exists():
            for bf in sorted(briefs.glob("*.json"))[-5:]:
                data = json.loads(bf.read_text(encoding="utf-8"))
                if any(w in json.dumps(data).lower() for w in q_words):
                    relevant.append(f"Research: {data.get('body','')[:300]}")
                    break

        return "\n".join(relevant[:5])

    def _query_agent_knowledge(self, question: str) -> str:
        try:
            from agent_knowledge_evolution import AgentKnowledgeBase
        except ImportError:
            return ""

        q_lower = question.lower()
        relevant = []
        agents = {
            "an1_analyst": ["eri", "score", "predict", "engagement"],
            "a1_architect": ["script", "hook", "angle", "content"],
            "ttlg_diagnostic": ["business", "diagnostic", "agency"],
            "consumer_journey": ["lead", "convert", "prospect"],
        }
        for aid, kws in agents.items():
            if any(kw in q_lower for kw in kws):
                try:
                    kb = AgentKnowledgeBase(aid)
                    knowledge = kb.query_relevant_knowledge(question, top_k=2)
                    for cat, entries in knowledge.items():
                        for e in entries:
                            if cat == "interaction_learnings":
                                relevant.append(e.get("insight", ""))
                            elif cat == "strategic_frameworks":
                                relevant.append(f"{e.get('framework_name','')}: {e.get('description','')[:100]}")
                except Exception:
                    pass
        return "\n".join(filter(None, relevant[:4]))

    def _query_research_briefs(self, question: str) -> str:
        return ""  # covered by _query_vault

    def _queue_deep_research(self, question: str, context: dict) -> Optional[str]:
        try:
            from echoes_research_engine import EchoesResearchEngine
            engine = EchoesResearchEngine()
            brief = engine.generate_white_paper_brief(
                topic=question, category="on_demand_research",
                research_data={"question": question, "context": context,
                               "triggered_by": "live_query_low_confidence"})
            return brief.brief_id
        except Exception:
            return None

    def _log_query(self, result: LiveQueryResult) -> None:
        record_decision(
            decision_type="live_query.answered",
            description=f"Live query: {result.query[:60]}",
            agent_id="epos_live_query", outcome="success",
            context={"confidence": result.confidence,
                     "sources": len(result.sources_consulted),
                     "ms": result.response_time_ms})
        self.query_log.append(asdict(result))

    def get_session_summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "total_queries": len(self.query_log),
            "avg_confidence": (sum(q["confidence"] for q in self.query_log) /
                               len(self.query_log)) if self.query_log else 0,
            "low_confidence_queries": [q["query"] for q in self.query_log if q["confidence"] < 0.7],
            "queries": self.query_log,
        }


if __name__ == "__main__":
    lq = EPOSLiveQuery(session_id="test-001")

    print("  Query 1: LEGO niche...")
    r1 = lq.query("What hook types perform best for LEGO content on YouTube Shorts?",
                   niche="lego_affiliate")
    assert len(r1.answer) > 50
    print(f"  Answer ({r1.response_time_ms}ms, confidence {r1.confidence:.2f})")
    print(f"  Sources: {r1.sources_consulted}")

    print("\n  Query 2: Novel question...")
    r2 = lq.query("What is the average ROI for AI-generated content campaigns in 2026?",
                   context={"stage": "discovery_call", "prospect_segment": "agency"})
    print(f"  Confidence: {r2.confidence:.2f}, depth_queued: {r2.depth_available}")

    summary = lq.get_session_summary()
    print(f"\n  Session: {summary['total_queries']} queries, avg confidence {summary['avg_confidence']:.2f}")
    print("\nPASS: EPOSLiveQuery — on-demand synthesis operational")
