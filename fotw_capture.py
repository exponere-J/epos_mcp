#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
fotw_capture.py — Fly on the Wall Passive Capture System
=========================================================
Constitutional Authority: EPOS Constitution v3.1

The organism's ears during live interactions.
Captures, classifies, and routes session intelligence
from discovery calls, webinars, client meetings, and support.

Every captured session becomes:
  1. A transcript in the CMS
  2. Learning events for agent knowledge bases
  3. Signal updates to the Context Graph
  4. Lead intelligence for the CRM pipeline
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault, get_logs_dir
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from epos_cms import EPOSContentManagement


# ── Data Structures ─────────────────────────────────────────

@dataclass
class CaptureSegment:
    """A single segment of captured speech/text."""
    segment_id: str
    speaker: str          # "host" | "prospect" | "participant" | "unknown"
    text: str
    timestamp: str
    duration_seconds: float = 0.0
    signals_detected: List[str] = field(default_factory=list)
    intent_classified: str = ""
    confidence: float = 0.0


@dataclass
class FOTWSession:
    """A complete capture session."""
    session_id: str
    session_type: str     # "discovery_call" | "webinar" | "client_meeting" | "support" | "reading"
    started_at: str
    ended_at: Optional[str] = None
    segments: List[CaptureSegment] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    contact_id: Optional[str] = None
    niche_id: Optional[str] = None
    signals_summary: Dict[str, int] = field(default_factory=dict)
    insights_extracted: List[str] = field(default_factory=list)
    learning_events_fired: int = 0
    status: str = "active"  # "active" | "completed" | "archived"


# ── Signal Detection ────────────────────────────────────────

SIGNAL_PATTERNS = {
    "purchase_intent": [
        "how much", "what does it cost", "pricing", "investment",
        "how do i start", "when can we begin", "sign up", "get started",
        "what's the next step", "ready to", "let's do",
    ],
    "pain_expression": [
        "struggling with", "the problem is", "frustrated", "overwhelmed",
        "can't keep up", "falling behind", "losing", "wasting time",
        "don't have time", "too much manual", "nothing works",
    ],
    "objection": [
        "not sure", "concerned about", "what if", "too expensive",
        "already tried", "skeptical", "don't know if", "but what about",
        "how do i know", "what's the risk",
    ],
    "decision_readiness": [
        "makes sense", "i see the value", "that's exactly what",
        "how do we proceed", "what would that look like", "tell me more about",
        "when could we start", "what's included",
    ],
    "expertise_signal": [
        "in my experience", "we've found that", "typically what works",
        "the industry standard", "best practice", "from our data",
        "years of", "we learned that",
    ],
    "emotional_peak": [
        "exactly", "yes", "absolutely", "that's it", "finally",
        "someone who understands", "been looking for", "needed this",
    ],
    "question_asked": [
        "how do you", "what is", "can you explain", "why does",
        "what's the difference", "how does that work", "is it possible",
    ],
}


# ── Main Capture Engine ─────────────────────────────────────

class FOTWCapture:
    """
    Passive capture and intelligence extraction engine.

    Three modes:
      LIVE: processes transcript chunks in real-time (3-5s intervals)
      BATCH: processes a complete transcript post-session
      READING: processes reading session data from the Reader extension
    """

    def __init__(self):
        self.vault = get_context_vault()
        self.bus = EPOSEventBus()
        self.cms = EPOSContentManagement()
        self.sessions_dir = self.vault / "fotw" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.active_sessions: Dict[str, FOTWSession] = {}

    def start_session(self, session_type: str,
                      contact_id: str = None,
                      niche_id: str = None,
                      participants: List[str] = None) -> FOTWSession:
        """Begin a new capture session."""
        session = FOTWSession(
            session_id=f"FOTW-{uuid.uuid4().hex[:8]}",
            session_type=session_type,
            started_at=datetime.now(timezone.utc).isoformat(),
            participants=participants or [],
            contact_id=contact_id,
            niche_id=niche_id,
        )
        self.active_sessions[session.session_id] = session
        self._persist_session(session)

        record_decision(
            decision_type="fotw.session.started",
            description=f"FOTW {session_type} session started",
            agent_id="fotw_capture",
            outcome="active",
            context={"session_id": session.session_id,
                     "session_type": session_type,
                     "contact_id": contact_id},
        )
        self.bus.publish("fotw.session.started",
                         {"session_id": session.session_id,
                          "type": session_type},
                         "fotw_capture")
        return session

    def capture_segment(self, session_id: str, text: str,
                        speaker: str = "unknown",
                        duration_seconds: float = 0.0) -> CaptureSegment:
        """
        Process a single segment of captured speech/text.
        Detects signals. Classifies intent. Routes intelligence.
        Called every 3-5 seconds during live sessions.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            # Try to load from disk
            session = self._load_session(session_id)
            if session:
                self.active_sessions[session_id] = session
            else:
                raise ValueError(f"Session not found: {session_id}")

        # Detect signals in this segment
        signals = self._detect_signals(text)

        # Classify intent
        intent, confidence = self._classify_intent(text, signals)

        segment = CaptureSegment(
            segment_id=f"SEG-{uuid.uuid4().hex[:6]}",
            speaker=speaker,
            text=text,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=duration_seconds,
            signals_detected=signals,
            intent_classified=intent,
            confidence=confidence,
        )

        session.segments.append(segment)

        # Update session signal summary
        for signal in signals:
            session.signals_summary[signal] = (
                session.signals_summary.get(signal, 0) + 1
            )

        # Route high-value signals immediately
        if "purchase_intent" in signals:
            self.bus.publish("fotw.signal.purchase_intent",
                             {"session_id": session_id,
                              "text": text[:100],
                              "speaker": speaker},
                             "fotw_capture")

        if "pain_expression" in signals:
            self._route_to_desire_vocabulary(text, session.niche_id)

        if "question_asked" in signals:
            self.bus.publish("fotw.signal.question",
                             {"session_id": session_id,
                              "text": text[:200],
                              "speaker": speaker},
                             "fotw_capture")

        # Persist updated session
        self._persist_session(session)

        return segment

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        Complete a capture session. Generate session intelligence.
        Route all accumulated signals to their destinations.
        Returns session summary.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.ended_at = datetime.now(timezone.utc).isoformat()
        session.status = "completed"

        # Extract insights from full session
        insights = self._extract_session_insights(session)
        session.insights_extracted = insights

        # Fire learning events
        learning_count = self._fire_learning_events(session)
        session.learning_events_fired = learning_count

        # Save transcript to CMS
        transcript_text = "\n\n".join([
            f"[{seg.speaker}] ({seg.timestamp[:19]}): {seg.text}"
            for seg in session.segments
        ])
        asset = self.cms.create_asset(
            asset_type="conversation_transcript",
            title=f"FOTW Session — {session.session_type} — {session.session_id}",
            body=transcript_text,
            author_agent="fotw_capture",
            tags=[session.session_type, session.session_id],
        )

        # Persist final session
        self._persist_session(session)

        # Summary
        summary = {
            "session_id": session.session_id,
            "session_type": session.session_type,
            "duration_minutes": self._calc_duration(session),
            "total_segments": len(session.segments),
            "signals_detected": session.signals_summary,
            "insights_extracted": len(insights),
            "learning_events_fired": learning_count,
            "transcript_asset_id": asset.asset_id,
            "contact_id": session.contact_id,
        }

        record_decision(
            decision_type="fotw.session.completed",
            description=f"FOTW session completed: {session.session_type}",
            agent_id="fotw_capture",
            outcome="complete",
            context=summary,
        )
        self.bus.publish("fotw.session.completed", summary, "fotw_capture")

        # Clean up active sessions
        self.active_sessions.pop(session_id, None)

        return summary

    def process_batch_transcript(self, transcript: str,
                                  session_type: str = "discovery_call",
                                  contact_id: str = None,
                                  niche_id: str = None) -> Dict[str, Any]:
        """
        Process a complete transcript post-session.
        Splits into segments, processes each, then ends session.
        Used when live capture wasn't available.
        """
        session = self.start_session(session_type, contact_id, niche_id)

        # Split transcript into segments (by speaker labels or paragraphs)
        segments = self._split_transcript(transcript)

        for text, speaker in segments:
            self.capture_segment(session.session_id, text, speaker)

        return self.end_session(session.session_id)

    def ingest_reading_session(self, reading_data: dict) -> Dict[str, Any]:
        """
        Receive a reading session from the Exponere Reader.
        reading_data contains: document_url, words_read,
        pronunciation_corrections, session_duration, domain_classified.
        Routes to agent knowledge bases for CCP calibration.
        """
        session = self.start_session(
            "reading",
            contact_id=reading_data.get("user_id"),
        )

        # Create a summary segment
        summary_text = (
            f"Reading session: {reading_data.get('document_url', 'unknown')}. "
            f"Words read: {reading_data.get('words_read', 0)}. "
            f"Domain: {reading_data.get('domain_classified', 'general')}. "
            f"Corrections: {reading_data.get('pronunciation_corrections', 0)}."
        )
        self.capture_segment(session.session_id, summary_text, "reader")

        # Route pronunciation corrections to homograph rules learning
        corrections = reading_data.get("correction_details", [])
        if corrections:
            self.bus.publish("fotw.reading.corrections",
                             {"corrections": corrections[:20],
                              "domain": reading_data.get("domain_classified"),
                              "session_id": session.session_id},
                             "fotw_capture")

        return self.end_session(session.session_id)

    # ── Signal Detection ────────────────────────────────────

    def _detect_signals(self, text: str) -> List[str]:
        """Detect all signal types present in text."""
        text_lower = text.lower()
        detected = []
        for signal_type, patterns in SIGNAL_PATTERNS.items():
            if any(p in text_lower for p in patterns):
                detected.append(signal_type)
        return detected

    def _classify_intent(self, text: str,
                         signals: List[str]) -> tuple:
        """Classify the primary intent of this segment."""
        if "purchase_intent" in signals or "decision_readiness" in signals:
            return "buying_signal", 0.85
        if "pain_expression" in signals:
            return "pain_expression", 0.80
        if "objection" in signals:
            return "objection_handling", 0.75
        if "question_asked" in signals:
            return "information_seeking", 0.70
        if "expertise_signal" in signals:
            return "expertise_sharing", 0.65
        if "emotional_peak" in signals:
            return "engagement_peak", 0.80
        return "general_conversation", 0.50

    # ── Intelligence Routing ────────────────────────────────

    def _route_to_desire_vocabulary(self, text: str,
                                     niche_id: str = None) -> None:
        """Route pain expressions to niche pack vocabulary."""
        if not niche_id:
            return
        try:
            pack_path = (
                self.vault / "niches" / niche_id / "niche_pack.json"
            )
            if pack_path.exists():
                pack = json.loads(pack_path.read_text(encoding="utf-8"))
                vocab = pack.get("desire_vocabulary", {})
                pain = vocab.get("pain_language", [])
                # Extract key phrases
                words = text.lower().split()
                phrases = [
                    " ".join(words[i:i+3])
                    for i in range(len(words) - 2)
                    if len(words[i]) > 3
                ]
                new_phrases = [p for p in phrases[:3] if p not in pain]
                if new_phrases:
                    pain.extend(new_phrases)
                    vocab["pain_language"] = pain
                    pack["desire_vocabulary"] = vocab
                    pack["live_vocabulary_updates"] = (
                        pack.get("live_vocabulary_updates", 0) + 1
                    )
                    pack_path.write_text(
                        json.dumps(pack, indent=2), encoding="utf-8"
                    )
        except Exception:
            pass

    def _extract_session_insights(self, session: FOTWSession) -> List[str]:
        """Extract key insights from completed session."""
        insights = []
        total = session.signals_summary

        if total.get("purchase_intent", 0) >= 2:
            insights.append(
                "Strong purchase intent detected — multiple buying signals"
            )
        if total.get("pain_expression", 0) >= 3:
            insights.append(
                "Deep pain expressed — prospect is actively suffering"
            )
        if total.get("objection", 0) >= 2:
            insights.append(
                "Multiple objections raised — needs addressed before close"
            )
        if total.get("question_asked", 0) >= 5:
            insights.append(
                "High question volume — prospect is engaged and evaluating"
            )
        if total.get("emotional_peak", 0) >= 2:
            insights.append(
                "Emotional resonance achieved — messaging is landing"
            )

        if not insights:
            insights.append(
                "Standard interaction — no exceptional signals detected"
            )
        return insights

    def _fire_learning_events(self, session: FOTWSession) -> int:
        """Route session intelligence to agent knowledge bases."""
        from agent_knowledge_evolution import AgentKnowledgeBase
        count = 0

        # TTLG learns from diagnostic conversations
        if session.session_type == "discovery_call":
            kb = AgentKnowledgeBase("ttlg_diagnostic")
            signals = session.signals_summary
            kb.record_interaction_learning(
                situation=f"Discovery call ({session.contact_id or 'unknown'})",
                action_taken="Passive capture during call",
                outcome=f"Signals: {json.dumps(signals)}",
                insight=(
                    f"This {session.niche_id or 'unknown'} prospect "
                    f"showed {'strong' if signals.get('purchase_intent', 0) >= 2 else 'moderate'} "
                    f"buying signals with {signals.get('pain_expression', 0)} pain expressions"
                ),
                outcome_score=min(
                    signals.get("purchase_intent", 0) * 0.3 +
                    signals.get("decision_readiness", 0) * 0.4, 1.0
                ),
            )
            count += 1

        # Consumer journey learns from all sessions
        if session.contact_id:
            kb = AgentKnowledgeBase("consumer_journey")
            kb.record_interaction_learning(
                situation=f"{session.session_type} session",
                action_taken="FOTW passive capture",
                outcome=f"{len(session.segments)} segments captured",
                insight="; ".join(session.insights_extracted[:3]),
                outcome_score=0.7,
            )
            count += 1

        # Context graph update for niche signal patterns
        if session.niche_id and session.signals_summary:
            from context_graph import ContextGraph, GraphEdge
            graph = ContextGraph()
            for signal_type, signal_count in session.signals_summary.items():
                if signal_count >= 2:  # Only meaningful patterns
                    graph.upsert_edge(GraphEdge(
                        edge_id=f"fotw_{session.niche_id}_{signal_type}",
                        source_id=f"niche_{session.niche_id}",
                        target_id=f"signal_{signal_type}",
                        relationship="session_signal_frequency",
                        weight=min(signal_count / 10.0, 1.0),
                        evidence_count=1,
                        last_updated=datetime.now(timezone.utc).isoformat(),
                    ))
                    count += 1

        return count

    # ── Persistence ─────────────────────────────────────────

    def _persist_session(self, session: FOTWSession) -> None:
        """Save session to vault."""
        path = self.sessions_dir / f"{session.session_id}.json"
        data = asdict(session)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_session(self, session_id: str) -> Optional[FOTWSession]:
        """Load session from vault."""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        segments = [CaptureSegment(**s) for s in data.pop("segments", [])]
        session = FOTWSession(**data)
        session.segments = segments
        return session

    def _split_transcript(self, transcript: str) -> List[tuple]:
        """Split transcript into (text, speaker) tuples."""
        segments = []
        for paragraph in transcript.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            # Try to detect speaker labels like "[Host]:" or "Jamie:"
            if ":" in paragraph[:30]:
                parts = paragraph.split(":", 1)
                speaker = parts[0].strip().strip("[]").lower()
                text = parts[1].strip()
                segments.append((text, speaker))
            else:
                segments.append((paragraph, "unknown"))
        return segments if segments else [(transcript, "unknown")]

    def _calc_duration(self, session: FOTWSession) -> float:
        """Calculate session duration in minutes."""
        if not session.ended_at or not session.started_at:
            return 0.0
        try:
            start = datetime.fromisoformat(session.started_at)
            end = datetime.fromisoformat(session.ended_at)
            return (end - start).total_seconds() / 60.0
        except Exception:
            return 0.0

    # ── Dashboard Interface ─────────────────────────────────

    def get_recent_sessions(self, hours: int = 168) -> List[dict]:
        """Get sessions from the last N hours for dashboard."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=hours)
        ).isoformat()
        sessions = []
        for f in sorted(self.sessions_dir.glob("FOTW-*.json"), reverse=True)[:20]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("started_at", "") >= cutoff:
                    sessions.append({
                        "session_id": data["session_id"],
                        "session_type": data["session_type"],
                        "started_at": data["started_at"],
                        "status": data.get("status", "unknown"),
                        "segments": len(data.get("segments", [])),
                        "signals": data.get("signals_summary", {}),
                        "insights": len(data.get("insights_extracted", [])),
                    })
            except Exception:
                pass
        return sessions

    def get_signal_summary(self, hours: int = 168) -> Dict[str, int]:
        """Aggregate signal counts across recent sessions."""
        sessions = self.get_recent_sessions(hours)
        total = {}
        for s in sessions:
            for signal, count in s.get("signals", {}).items():
                total[signal] = total.get(signal, 0) + count
        return total


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile
    py_compile.compile("fotw_capture.py", doraise=True)

    fotw = FOTWCapture()

    # Test 1: Start a discovery call session
    session = fotw.start_session(
        "discovery_call",
        contact_id="pgp_orlando",
        niche_id="local_service",
        participants=["jamie", "pgp_owner"],
    )
    print(f"  Session started: {session.session_id}")

    # Test 2: Capture segments with signals
    seg1 = fotw.capture_segment(
        session.session_id,
        "The problem is we're losing leads because we can't keep up with follow-ups",
        speaker="prospect",
    )
    assert "pain_expression" in seg1.signals_detected
    print(f"  Segment 1: {seg1.signals_detected}")

    seg2 = fotw.capture_segment(
        session.session_id,
        "How much does this cost? What would the investment look like?",
        speaker="prospect",
    )
    assert "purchase_intent" in seg2.signals_detected
    print(f"  Segment 2: {seg2.signals_detected}")

    seg3 = fotw.capture_segment(
        session.session_id,
        "That makes sense. How do we get started?",
        speaker="prospect",
    )
    assert "decision_readiness" in seg3.signals_detected
    print(f"  Segment 3: {seg3.signals_detected}")

    # Test 3: End session and get summary
    summary = fotw.end_session(session.session_id)
    assert summary["total_segments"] == 3
    assert summary["learning_events_fired"] >= 1
    print(f"  Session ended: {summary['total_segments']} segments")
    print(f"  Signals: {summary['signals_detected']}")
    print(f"  Insights: {summary['insights_extracted']}")
    print(f"  Learning events: {summary['learning_events_fired']}")
    print(f"  Transcript asset: {summary['transcript_asset_id']}")

    # Test 4: Batch transcript processing
    batch_result = fotw.process_batch_transcript(
        "Host: Tell me about your current content process.\n\n"
        "Prospect: We're struggling with consistency. Nothing works.\n\n"
        "Host: What have you tried that came closest to working?\n\n"
        "Prospect: We tried scheduling tools but they don't create the content.\n\n"
        "Prospect: How much would a full production service cost?",
        session_type="discovery_call",
        niche_id="local_service",
    )
    assert batch_result["total_segments"] >= 4
    print(f"\n  Batch processed: {batch_result['total_segments']} segments")
    print(f"  Batch signals: {batch_result['signals_detected']}")

    # Test 5: Reading session ingestion
    reading = fotw.ingest_reading_session({
        "document_url": "https://example.com/article",
        "words_read": 1500,
        "domain_classified": "technical",
        "pronunciation_corrections": 3,
        "correction_details": [
            {"word": "read", "context": "past tense", "corrected_to": "/red/"},
        ],
        "session_duration": 420,
    })
    print(f"\n  Reading session: {reading['session_id']}")

    # Test 6: Dashboard interface
    recent = fotw.get_recent_sessions(hours=1)
    signal_summary = fotw.get_signal_summary(hours=1)
    print(f"\n  Recent sessions: {len(recent)}")
    print(f"  Signal summary: {signal_summary}")

    print("\nPASS: FOTWCapture — passive session intelligence operational")
    print("The organism hears everything and learns from it.")
