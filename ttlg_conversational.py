#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
ttlg_conversational.py — Conversational TTLG Diagnostic Interface
===================================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Interactive Diagnostic Conversations

Wraps the TTLG Diagnostic state machine in a conversational interface
that guides prospects through discovery, captures expressions for FOTW,
and produces Mirror Reports interactively.

Flow:
  1. INTAKE — Gather basic client context through conversation
  2. SCOUT — Run focused questions to assess each track
  3. REVEAL — Present findings conversationally (Mirror Report preview)
  4. PRESCRIBE — Recommend engagement tier with pricing
  5. CAPTURE — Feed all expressions to FOTW for intelligence

Uses GroqRouter for conversational generation.
TTLG state machine for actual diagnostic scoring.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

try:
    from groq_router import GroqRouter
except ImportError:
    GroqRouter = None

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass

try:
    from fotw_listener import FOTWListener
except ImportError:
    FOTWListener = None

from path_utils import get_context_vault


CONV_VAULT = get_context_vault() / "ttlg" / "conversations"

TTLG_PERSONA = """You are the Through the Looking Glass diagnostic consultant.
Your role: help business owners see their operation as it actually is — then show what it could become.
Personality: warm, direct, knowledgeable. Like a trusted advisor who asks the hard questions gently.
You never oversell. You never use hype. You ask questions that make people think.
Keep responses under 100 words. Be specific, not generic. Reference their answers."""

TRACK_QUESTIONS = {
    "marketing": [
        "What's your primary way of getting new clients right now?",
        "How much of your content is produced by a system vs. done manually?",
        "If your top marketing person quit tomorrow, would content production stop?",
    ],
    "sales": [
        "Walk me through what happens when someone expresses interest in working with you.",
        "How do you know which leads are worth your time vs. just browsing?",
        "What's your close rate on qualified conversations?",
    ],
    "service": [
        "After a client signs, what does the first 30 days look like?",
        "How do you measure whether a client is getting value from your work?",
        "What's your biggest operational bottleneck right now?",
    ],
    "governance": [
        "If you had to hand your business operations to someone for a month, how long would the handoff take?",
        "Where does your critical business data live? Is it in one place or scattered?",
        "What happens when something breaks at 2am — is there a process, or is it you?",
    ],
}


class TTLGConversational:
    """
    Interactive diagnostic conversation engine.
    Guides prospects through TTLG discovery conversationally.
    """

    def __init__(self, vault_path: Path = None):
        self.vault = vault_path or CONV_VAULT
        self.vault.mkdir(parents=True, exist_ok=True)
        self.fotw = FOTWListener() if FOTWListener else None

    def start_session(self, client_id: str, client_name: str = "",
                      industry: str = "") -> dict:
        """Initialize a conversational diagnostic session."""
        session_id = f"CONV-{uuid.uuid4().hex[:8]}"
        session = {
            "session_id": session_id,
            "client_id": client_id,
            "client_name": client_name,
            "industry": industry,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "phase": "intake",
            "current_track": None,
            "track_index": 0,
            "responses": {},
            "track_scores": {},
            "conversation_log": [],
            "status": "active",
        }

        # Generate opening
        opening = self._generate_opening(client_name, industry)
        session["conversation_log"].append({
            "role": "consultant", "text": opening,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        self._save_session(session)
        self._publish("ttlg.conversation.started", {
            "session_id": session_id, "client_id": client_id})

        return {"session_id": session_id, "message": opening}

    def respond(self, session_id: str, user_message: str) -> dict:
        """Process user response and advance the conversation."""
        session = self._load_session(session_id)
        if not session:
            return {"error": f"Session not found: {session_id}"}

        # Log user message
        session["conversation_log"].append({
            "role": "client", "text": user_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Capture expression for FOTW
        if self.fotw:
            self.fotw.capture_transcript_segment(
                session_id, session.get("client_name", "client"), user_message)

        phase = session["phase"]

        if phase == "intake":
            response = self._handle_intake(session, user_message)
        elif phase == "scouting":
            response = self._handle_scouting(session, user_message)
        elif phase == "reveal":
            response = self._handle_reveal(session)
        elif phase == "prescribe":
            response = self._handle_prescribe(session)
        else:
            response = "This session has concluded. Start a new session to continue."

        session["conversation_log"].append({
            "role": "consultant", "text": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        self._save_session(session)
        return {"session_id": session_id, "message": response, "phase": session["phase"]}

    def _handle_intake(self, session: dict, message: str) -> str:
        """Intake phase: gather context, then transition to scouting."""
        # Store intake response
        session["responses"]["intake"] = message

        # Transition to scouting
        session["phase"] = "scouting"
        session["current_track"] = "marketing"
        session["track_index"] = 0

        question = TRACK_QUESTIONS["marketing"][0]
        return (f"Thank you. Let's start with your marketing.\n\n{question}")

    def _handle_scouting(self, session: dict, message: str) -> str:
        """Scouting phase: ask track questions, score responses."""
        track = session["current_track"]
        idx = session["track_index"]

        # Store response
        key = f"{track}_{idx}"
        session["responses"][key] = message

        # Score this response (simple heuristic)
        score = self._score_response(message, track)
        if track not in session["track_scores"]:
            session["track_scores"][track] = []
        session["track_scores"][track].append(score)

        # Advance to next question or next track
        questions = TRACK_QUESTIONS[track]
        if idx + 1 < len(questions):
            session["track_index"] = idx + 1
            next_q = questions[idx + 1]

            # Generate contextual bridge using LLM if available
            bridge = self._contextual_bridge(message, next_q, track)
            return bridge
        else:
            # Move to next track
            tracks = list(TRACK_QUESTIONS.keys())
            current_idx = tracks.index(track)
            if current_idx + 1 < len(tracks):
                next_track = tracks[current_idx + 1]
                session["current_track"] = next_track
                session["track_index"] = 0
                first_q = TRACK_QUESTIONS[next_track][0]
                return f"Good. Let's look at your {next_track}.\n\n{first_q}"
            else:
                # All tracks complete — move to reveal
                session["phase"] = "reveal"
                return self._handle_reveal(session)

    def _handle_reveal(self, session: dict) -> str:
        """Reveal phase: present findings as a conversational Mirror Report."""
        scores = session["track_scores"]
        total = 0
        track_summaries = []

        for track, track_scores in scores.items():
            avg = sum(track_scores) / len(track_scores) if track_scores else 0
            total += avg
            level = "strong" if avg >= 7 else "developing" if avg >= 4 else "needs attention"
            track_summaries.append(f"  {track.title()}: {level} ({avg:.0f}/10)")

        composite = total / len(scores) if scores else 0

        # Generate reveal
        reveal = (
            f"Here's what I see.\n\n"
            f"Sovereign Alignment Score: {composite:.0f}/10\n\n"
            + "\n".join(track_summaries)
            + f"\n\nYour strongest area is {max(scores, key=lambda t: sum(scores[t])/len(scores[t])).title()}. "
            f"The area that needs the most attention is {min(scores, key=lambda t: sum(scores[t])/len(scores[t])).title()}."
            f"\n\nWould you like to see the specific recommendations?"
        )

        session["phase"] = "prescribe"
        self._publish("ttlg.conversation.reveal", {
            "session_id": session["session_id"],
            "composite_score": composite,
        })
        return reveal

    def _handle_prescribe(self, session: dict) -> str:
        """Prescribe phase: recommend engagement tier."""
        scores = session["track_scores"]
        composite = sum(sum(s)/len(s) for s in scores.values()) / len(scores)

        if composite < 4:
            tier = "ttlg_enterprise"
            desc = "Full Enterprise Build (Layers 1-20)"
            price = "$9,997"
        elif composite < 7:
            tier = "ttlg_blueprint"
            desc = "Full Blueprint (Layers 1-15)"
            price = "$4,997"
        else:
            tier = "ttlg_audit"
            desc = "Sovereign Alignment Audit"
            price = "$497"

        session["phase"] = "complete"
        session["status"] = "complete"
        session["recommended_tier"] = tier

        self._publish("ttlg.conversation.complete", {
            "session_id": session["session_id"],
            "client_id": session["client_id"],
            "recommended_tier": tier,
            "composite_score": composite,
        })

        return (
            f"Based on what we've discussed, here's what I'd recommend:\n\n"
            f"**{desc}** — {price}\n\n"
            f"This covers a deep-dive into the areas we identified, "
            f"with a full Mirror Report, consequence chains, and a build roadmap.\n\n"
            f"The next step is a 30-minute strategy call to scope the engagement. "
            f"Shall I send you the booking link?"
        )

    # ── Scoring ────────���────────────────────────────────────

    def _score_response(self, response: str, track: str) -> float:
        """Score a response on a 0-10 scale based on sophistication signals."""
        score = 5.0  # baseline
        response_lower = response.lower()

        # Positive signals (system/process thinking)
        positive = ["system", "process", "automated", "documented", "measured",
                     "dashboard", "kpi", "metric", "pipeline", "workflow"]
        for word in positive:
            if word in response_lower:
                score += 1.0

        # Negative signals (ad-hoc/manual)
        negative = ["manually", "i do it", "no process", "don't have", "haven't",
                     "scattered", "depends on me", "gut feeling", "random"]
        for word in negative:
            if word in response_lower:
                score -= 1.0

        return max(0, min(10, score))

    def _contextual_bridge(self, previous_answer: str, next_question: str, track: str) -> str:
        """Generate a contextual transition between questions."""
        if GroqRouter:
            try:
                router = GroqRouter()
                prompt = (
                    f"The client just said: \"{previous_answer[:200]}\"\n\n"
                    f"Acknowledge their answer briefly (1 sentence), then ask: {next_question}\n"
                    f"Be warm and specific. Under 50 words total."
                )
                bridge = router.route("summarization", prompt,
                                       system_prompt=TTLG_PERSONA,
                                       max_tokens=100, temperature=0.6)
                return bridge
            except Exception:
                pass
        return f"Got it.\n\n{next_question}"

    def _generate_opening(self, name: str, industry: str) -> str:
        """Generate personalized session opening."""
        name_str = f", {name}" if name else ""
        industry_str = f" in {industry}" if industry else ""
        return (
            f"Welcome{name_str}. I'm here to help you see your business{industry_str} "
            f"as it actually is — then show you what it could become.\n\n"
            f"Before we dive into the diagnostic, tell me: what's the one thing "
            f"about your business operations that keeps you up at night?"
        )

    # ── Session Persistence ─────────────────────────────────

    def _save_session(self, session: dict):
        path = self.vault / f"{session['session_id']}.json"
        path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    def _load_session(self, session_id: str) -> Optional[dict]:
        path = self.vault / f"{session_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def list_sessions(self, status: str = None) -> list:
        sessions = []
        for f in self.vault.glob("CONV-*.json"):
            s = json.loads(f.read_text(encoding="utf-8"))
            if status and s.get("status") != status:
                continue
            sessions.append({
                "session_id": s["session_id"],
                "client_id": s["client_id"],
                "phase": s["phase"],
                "status": s["status"],
                "started_at": s["started_at"],
            })
        return sessions

    def _publish(self, event_type: str, payload: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="ttlg_conversational")
            except Exception:
                pass
        record_decision(decision_type=event_type, description=f"Conv TTLG: {event_type}",
                        agent_id="ttlg_conversational", outcome="success", context=payload)


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    conv = TTLGConversational()

    # Test 1: Start session
    result = conv.start_session("test-client", "Test Corp", "marketing agency")
    assert "session_id" in result
    assert "message" in result
    sid = result["session_id"]
    passed += 1

    # Test 2: Intake response
    r2 = conv.respond(sid, "Our biggest issue is we can't produce content consistently. It's all manual.")
    assert r2["phase"] == "scouting"
    passed += 1

    # Test 3: Scout through questions
    for i in range(12):  # 4 tracks x 3 questions
        r = conv.respond(sid, "We handle it manually, no real system in place.")
        if r["phase"] in ("reveal", "prescribe", "complete"):
            break
    assert r["phase"] in ("reveal", "prescribe", "complete")
    passed += 1

    # Test 4: Session persistence
    sessions = conv.list_sessions()
    assert len(sessions) >= 1
    passed += 1

    # Test 5: Scoring
    score = conv._score_response("We have a documented process with KPIs and automated workflows", "marketing")
    assert score > 5, f"Expected > 5, got {score}"
    score2 = conv._score_response("I do it manually, no process really", "marketing")
    assert score2 < 5, f"Expected < 5, got {score2}"
    passed += 1

    print(f"PASS: ttlg_conversational ({passed} assertions)")
