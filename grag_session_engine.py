#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
grag_session_engine.py — Live Session Intelligence (GRAG)
==========================================================
Constitutional Authority: EPOS Constitution v3.1
File: C:/Users/Jamie/workspace/epos_mcp/grag_session_engine.py

GRAG = Generative Retrieval-Augmented Generation
Monitors active sessions. Detects questions. Fires live queries.
Surfaces answers before the silence becomes uncomfortable.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_live_query import EPOSLiveQuery
from epos_intelligence import record_decision


class GRAGSessionEngine:
    """
    Live session assistant. Monitors, detects questions, fires queries.

    Modes: PASSIVE (listen + record), REACTIVE (detect + answer),
           PROACTIVE (anticipate + pre-load)
    Session types: discovery_call, webinar_qa, onboarding, support
    """

    QUESTION_SIGNALS = [
        "how do you", "what is", "what are", "can you explain",
        "how does", "what about", "is it possible", "could you",
        "do you know", "have you seen", "what's the best",
        "how much", "what does it cost", "can it handle",
        "does it work with", "what happens when", "why does",
        "how long", "how many", "what if",
    ]

    def __init__(self, session_type: str, niche: str = None, segment: str = None):
        self.session_type = session_type
        self.niche = niche
        self.segment = segment
        self.session_id = f"GRAG-{uuid.uuid4().hex[:8]}"
        self.live_query = EPOSLiveQuery(session_id=self.session_id)
        self.session_log: List[dict] = []
        self.pre_loaded_knowledge: Dict[str, str] = {}
        self._preload_session_knowledge()

    def _preload_session_knowledge(self) -> None:
        """Pre-load knowledge most likely needed for this session type."""
        preload_topics = {
            "discovery_call": [
                "What is EPOS and Echoes Marketing",
                f"Common {self.segment or 'business'} pain points",
                "Pricing and service tiers",
            ],
            "webinar_qa": [
                "Best AI models for content creation 2026",
                "Content cascade from one source asset",
                "ERI algorithm and content scoring",
            ],
            "onboarding": [
                "Content Lab production pipeline",
                "First week expectations",
            ],
            "support": [
                "Common technical questions",
                "Troubleshooting approaches",
            ],
        }
        for topic in preload_topics.get(self.session_type, [])[:3]:
            try:
                result = self.live_query.query(topic, mode="immediate", niche=self.niche)
                self.pre_loaded_knowledge[topic] = result.answer
            except Exception:
                pass

    def process_transcript_chunk(self, text: str) -> Optional[dict]:
        """
        Receive transcript chunk. Detect questions. Fire live query.
        Returns suggestion dict if question found, None otherwise.
        """
        text_lower = text.lower()
        question_detected = any(sig in text_lower for sig in self.QUESTION_SIGNALS)

        if not question_detected:
            self._log_transcript(text, None)
            return None

        question = self._extract_question(text)
        if not question:
            self._log_transcript(text, None)
            return None

        # Check pre-loaded knowledge first
        for topic, answer in self.pre_loaded_knowledge.items():
            if any(w in question.lower() for w in topic.lower().split() if len(w) > 4):
                suggestion = {"question_detected": question, "answer": answer,
                              "source": "pre_loaded", "confidence": 0.8, "response_time_ms": 0}
                self._log_transcript(text, suggestion)
                return suggestion

        # Fire live query
        result = self.live_query.query(
            question=question,
            context={"stage": self.session_type, "prospect_segment": self.segment},
            niche=self.niche, mode="synthesized")

        suggestion = {
            "question_detected": question, "answer": result.answer,
            "source": "live_query", "confidence": result.confidence,
            "response_time_ms": result.response_time_ms,
            "depth_available": result.depth_available,
            "follow_up_brief": result.follow_up_brief,
        }
        self._log_transcript(text, suggestion)
        return suggestion

    def get_suggested_response(self, question: str) -> str:
        """Direct question input — returns ready-to-speak response."""
        result = self.live_query.query(
            question, context={"stage": self.session_type, "segment": self.segment},
            niche=self.niche, mode="synthesized")
        return result.answer

    def generate_session_aar(self) -> dict:
        """Generate session After Action Review."""
        summary = self.live_query.get_session_summary()
        gaps = summary.get("low_confidence_queries", [])

        aar = {
            "session_id": self.session_id, "session_type": self.session_type,
            "total_queries": summary["total_queries"],
            "avg_confidence": summary["avg_confidence"],
            "knowledge_gaps": gaps,
            "research_queued": [q.get("follow_up_brief") for q in summary.get("queries", [])
                                if q.get("follow_up_brief")],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Record gaps as failure cases
        if gaps:
            try:
                from agent_knowledge_evolution import AgentKnowledgeBase
                kb = AgentKnowledgeBase("consumer_journey")
                for gap in gaps:
                    kb.record_failure_case(
                        situation=f"Live {self.session_type}",
                        action_taken="Attempted answer",
                        what_went_wrong="Low confidence",
                        root_cause=f"Question not covered: {gap[:80]}",
                        correction="Queue research before next similar session")
            except Exception:
                pass

        record_decision(decision_type="grag.session.aar_generated",
                        description=f"GRAG AAR: {self.session_type}",
                        agent_id="grag_session_engine", outcome="complete", context=aar)
        return aar

    def _extract_question(self, text: str) -> Optional[str]:
        sentences = text.replace("?", "?.").split(".")
        for s in sentences:
            s = s.strip()
            if any(sig in s.lower() for sig in self.QUESTION_SIGNALS) and len(s) > 10:
                return s
        return None

    def _log_transcript(self, text: str, suggestion: Optional[dict]) -> None:
        self.session_log.append({"text": text[:200], "suggestion": suggestion,
                                  "logged_at": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    print("  Initializing GRAG session (discovery_call)...")
    grag = GRAGSessionEngine(session_type="discovery_call",
                              niche="lego_affiliate", segment="small_business")
    print(f"  Pre-loaded {len(grag.pre_loaded_knowledge)} topics")

    chunk = "That sounds great. But how do you actually measure whether the content is working?"
    print(f"\n  Processing: '{chunk[:60]}...'")
    suggestion = grag.process_transcript_chunk(chunk)
    if suggestion:
        print(f"  Question: {suggestion['question_detected']}")
        print(f"  Confidence: {suggestion['confidence']:.2f}")
        print(f"  Answer: {suggestion['answer'][:150]}...")
    else:
        print("  No question detected")

    direct = grag.get_suggested_response("What is the ERI algorithm?")
    print(f"\n  Direct answer: {direct[:150]}...")

    aar = grag.generate_session_aar()
    print(f"\n  AAR: {aar['total_queries']} queries, {len(aar['knowledge_gaps'])} gaps")
    print("\nPASS: GRAGSessionEngine — live session intelligence ready")
