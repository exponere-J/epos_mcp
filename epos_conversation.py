#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_conversation.py — Consultative Conversation Engine
=========================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/epos_conversation.py

Conducts conversations that reveal what the human actually needs —
not just what they asked for.

Principle: Ask before answering. Reveal before recommending.
           Verify before closing.

The organism breathes in conversations. It exhales content.
Every breath compounds into knowledge.
"""

import json
import uuid
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from groq_router import GroqRouter
from epos_live_query import EPOSLiveQuery
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from path_utils import get_context_vault


@dataclass
class ConversationTurn:
    turn_id: str
    speaker: str              # "human" | "epos"
    content: str
    intent_detected: str
    depth_level: int          # 1=surface, 2=operational, 3=root_cause
    follow_up_question: Optional[str] = None
    synthesis_triggered: bool = False
    timestamp: str = ""


@dataclass
class ConversationState:
    conversation_id: str
    session_type: str         # discovery|support|onboarding|webinar
    segment: Optional[str] = None
    niche: Optional[str] = None
    stage: str = "opening"    # opening|exploring|diagnosing|synthesizing|closing
    turns: List[dict] = field(default_factory=list)
    detected_needs: List[str] = field(default_factory=list)
    unresolved_threads: List[str] = field(default_factory=list)
    synthesis_ready: bool = False
    context_summary: str = ""
    created_at: str = ""
    updated_at: str = ""


class EPOSConversation:
    """
    The consultative conversation engine.
    Three patterns: DISCOVERY, DIAGNOSTIC, SUPPORT.
    Asks before answering. Reveals before recommending.
    """

    INTENT_TAXONOMY = {
        "surface_pain": ["i need", "i want", "looking for", "help with",
                         "struggling with", "can't keep up", "don't have time"],
        "operational_gap": ["how do i", "what's the best way", "is there a way",
                            "can you help me", "how should i"],
        "root_cause_signal": ["the real problem", "what's actually happening",
                              "i've tried", "nothing works", "keeps happening",
                              "frustrated", "overwhelmed"],
        "decision_ready": ["how much", "what does it cost", "how do i start",
                           "when can we", "what's next", "i'm ready"],
        "objection": ["but", "however", "i'm not sure", "what if",
                      "concerned about", "worried that"],
    }

    CLARIFYING_QUESTIONS = {
        "discovery_opener": [
            "Before I tell you anything about what we do, I'd love to understand your situation. What brought you here today?",
            "Tell me about the business. What are you building and where are you trying to take it?",
            "What's the most pressing problem you're trying to solve right now?",
        ],
        "surface_pain_content": [
            "What does a productive content week look like for you — what would you have produced and where would it have gone?",
            "When you think about the gap between what you're producing and what you want to produce, what's the biggest constraint?",
            "Tell me about the last piece of content you were genuinely proud of. What made it work?",
        ],
        "surface_pain_business": [
            "Walk me through what your current process looks like when a new lead comes in.",
            "What's the part of running your business you find yourself doing manually that should be automated?",
            "If you had to point to one thing preventing you from growing at the rate you know is possible, what would it be?",
        ],
        "operational_gap_content": [
            "What tools are you currently using in your content workflow, and where do they hand off to manual work?",
            "How are you currently deciding what content to create?",
            "When content doesn't perform as expected, what's your process for understanding why?",
        ],
        "operational_gap_business": [
            "What does your current system look like for following up with prospects?",
            "How are you currently measuring the ROI of your content efforts?",
            "What information do you wish you had about your prospects before getting on a call?",
        ],
        "root_cause_signal": [
            "It sounds like you've put real effort into this. What have you tried that came closest to working?",
            "When you imagine this problem fully solved, what's different about your day?",
            "What would need to be true for the solution to actually stick this time?",
        ],
        "objection": [
            "That's a fair concern. Can you tell me more about what specifically worries you?",
            "What would need to be true for that concern to not be a barrier?",
            "I want to make sure I understand — is this a question of fit, timing, or something else?",
        ],
    }

    def __init__(self, session_type: str, segment: str = None, niche: str = None):
        self.vault = get_context_vault()
        self.router = GroqRouter()
        self.live_query = EPOSLiveQuery()
        self.bus = EPOSEventBus()
        self.state = ConversationState(
            conversation_id=f"CONV-{uuid.uuid4().hex[:8]}",
            session_type=session_type,
            segment=segment,
            niche=niche,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def receive(self, human_input: str) -> str:
        """
        Primary method. Receive human input. Return consultative response.
        Response is: clarifying question, synthesized answer, or confirmation.
        GRAG processes during the conversation.
        """
        intent = self._classify_intent(human_input)
        depth = self._assess_depth(human_input)

        # Record human turn
        turn = {
            "turn_id": f"T{len(self.state.turns)+1:03d}",
            "speaker": "human", "content": human_input,
            "intent_detected": intent, "depth_level": depth,
            "follow_up_question": None, "synthesis_triggered": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.state.turns.append(turn)

        # Update detected needs from what was said
        if intent in ("surface_pain", "operational_gap", "root_cause_signal"):
            self.state.detected_needs.append(human_input[:100])

        self._update_stage()

        # Fire GRAG query (processes while we formulate response)
        grag_result = self.live_query.query(
            question=human_input,
            context={"stage": self.state.stage, "segment": self.state.segment,
                     "needs": self.state.detected_needs[-3:]},
            niche=self.state.niche, mode="synthesized")

        # Determine response type
        synthesis_ready = self._check_synthesis_ready()
        should_ask = self._should_ask_clarifying_question()

        if synthesis_ready:
            response = self._synthesize_response(grag_result, human_input)
            turn["synthesis_triggered"] = True
        elif should_ask:
            question = self._select_clarifying_question(intent)
            response = self._build_consultative_response(human_input, question, grag_result, intent)
            turn["follow_up_question"] = question
        else:
            response = self._build_transition_response(human_input, grag_result)

        # Record EPOS turn
        epos_turn = {
            "turn_id": f"T{len(self.state.turns)+1:03d}",
            "speaker": "epos", "content": response,
            "intent_detected": "response", "depth_level": 0,
            "synthesis_triggered": synthesis_ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.state.turns.append(epos_turn)
        self.state.updated_at = datetime.now(timezone.utc).isoformat()

        self._persist_state()

        try:
            self.bus.publish("conversation.turn.complete",
                             {"conversation_id": self.state.conversation_id,
                              "turn": len(self.state.turns), "stage": self.state.stage,
                              "synthesis": synthesis_ready},
                             "epos_conversation")
        except Exception:
            pass

        return response

    def _classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        for intent, signals in self.INTENT_TAXONOMY.items():
            if any(s in text_lower for s in signals):
                return intent
        return "exploratory"

    def _assess_depth(self, text: str) -> int:
        root = ["frustrated", "overwhelmed", "been trying", "keeps happening",
                "nothing works", "always", "never", "years", "the real problem"]
        ops = ["process", "workflow", "system", "tool", "currently", "right now"]
        if any(s in text.lower() for s in root):
            return 3
        if any(s in text.lower() for s in ops):
            return 2
        return 1

    def _should_ask_clarifying_question(self) -> bool:
        human_turns = [t for t in self.state.turns if t["speaker"] == "human"]
        if len(human_turns) < 2:
            return True
        if human_turns[-1]["depth_level"] == 1:
            return True
        if human_turns[-1]["intent_detected"] == "decision_ready":
            return False
        intents = [t["intent_detected"] for t in human_turns]
        if "root_cause_signal" in intents:
            return False
        return len(human_turns) < 4

    def _check_synthesis_ready(self) -> bool:
        human_turns = [t for t in self.state.turns if t["speaker"] == "human"]
        if len(human_turns) < 2:
            return False
        intents = [t["intent_detected"] for t in human_turns]
        if "decision_ready" in intents:
            return True
        if "root_cause_signal" in intents and len(human_turns) >= 3:
            return True
        depths = [t["depth_level"] for t in human_turns]
        if len(depths) >= 3 and sum(depths) / len(depths) >= 2.5:
            return True
        return False

    def _select_clarifying_question(self, intent: str) -> str:
        stage = self.state.stage
        seg = self.state.segment or "content"

        if stage == "opening":
            questions = self.CLARIFYING_QUESTIONS.get("discovery_opener", [])
        elif intent == "surface_pain":
            key = f"surface_pain_{'content' if 'creator' in seg else 'business'}"
            questions = self.CLARIFYING_QUESTIONS.get(key, [])
        elif intent == "operational_gap":
            key = f"operational_gap_{'content' if 'creator' in seg else 'business'}"
            questions = self.CLARIFYING_QUESTIONS.get(key, [])
        elif intent == "root_cause_signal":
            questions = self.CLARIFYING_QUESTIONS.get("root_cause_signal", [])
        elif intent == "objection":
            questions = self.CLARIFYING_QUESTIONS.get("objection", [])
        else:
            questions = self.CLARIFYING_QUESTIONS.get("discovery_opener", [])

        if not questions:
            return "Can you tell me more about that?"

        asked = {t.get("follow_up_question") for t in self.state.turns if t.get("follow_up_question")}
        available = [q for q in questions if q not in asked]
        return random.choice(available) if available else questions[0]

    def _build_consultative_response(self, human_input, question, grag_result, intent):
        prompt = f"""You are a consultative AI having a business conversation.
The human just said: "{human_input}"
Their intent: {intent}

Write a 1-2 sentence acknowledgment that shows you heard them and reflects
the core of what they expressed. Do NOT provide a solution yet.

Then ask this question exactly:
"{question}"

Under 100 words total. Warm, direct, conversational."""
        return self.router.route("scripting", prompt, max_tokens=200, temperature=0.5)

    def _synthesize_response(self, grag_result, human_input):
        human_turns = [t for t in self.state.turns if t["speaker"] == "human"]
        summary = "\n".join([f"- {t['content'][:100]}" for t in human_turns])

        prompt = f"""Complete a consultative conversation. Through this conversation you learned:

{summary}

Detected needs: {self.state.detected_needs[-5:]}

Available knowledge: {grag_result.answer[:600] if grag_result else ''}

Synthesize a tailored response that:
1. Reflects what you heard across the whole conversation
2. Names the root problem clearly
3. Presents the specific solution for THEIR situation
4. Makes one clear recommendation

150-200 words. Conversational. Specific to them.
End with: "The next step would be X — does that feel right?" """
        self.state.synthesis_ready = True
        return self.router.route("reasoning", prompt, max_tokens=400, temperature=0.4)

    def _build_transition_response(self, human_input, grag_result):
        prompt = f"""Short bridge response (50-75 words) to: "{human_input}"
Acknowledge it, add one insight from: "{grag_result.answer[:200] if grag_result else ''}"
Signal you want to understand more. Warm and direct."""
        return self.router.route("scripting", prompt, max_tokens=150, temperature=0.5)

    def _update_stage(self):
        human_turns = [t for t in self.state.turns if t["speaker"] == "human"]
        n = len(human_turns)
        intents = [t["intent_detected"] for t in human_turns]
        if n <= 1:
            self.state.stage = "opening"
        elif n <= 3 and "decision_ready" not in intents:
            self.state.stage = "exploring"
        elif "root_cause_signal" in intents or n >= 3:
            self.state.stage = "diagnosing"
        if self.state.synthesis_ready:
            self.state.stage = "synthesizing"

    def _persist_state(self):
        conv_path = self.vault / "cms" / "conversations" / f"{self.state.conversation_id}.json"
        conv_path.parent.mkdir(parents=True, exist_ok=True)
        conv_path.write_text(json.dumps(asdict(self.state), indent=2, default=str), encoding="utf-8")

    def get_transcript(self) -> str:
        """Return human-readable transcript."""
        lines = []
        for t in self.state.turns:
            speaker = "Human" if t["speaker"] == "human" else "EPOS"
            lines.append(f"[{speaker}]: {t['content']}")
        return "\n\n".join(lines)


if __name__ == "__main__":
    conv = EPOSConversation(session_type="discovery_call", segment="small_business")
    print(f"  Conversation: {conv.state.conversation_id}")
    print(f"  Stage: {conv.state.stage}")

    # Turn 1: Opening
    r1 = conv.receive("Hi, I run a pressure washing business in Orlando and I need help with marketing.")
    print(f"\n  [Turn 1] Stage: {conv.state.stage}")
    print(f"  EPOS: {r1[:150]}...")

    # Turn 2: Exploring
    r2 = conv.receive("I've been posting on Facebook but nothing seems to get traction. I'm frustrated because I know my work is good.")
    print(f"\n  [Turn 2] Stage: {conv.state.stage}")
    print(f"  Intent: {conv.state.turns[-2]['intent_detected']}")
    print(f"  EPOS: {r2[:150]}...")

    # Turn 3: Root cause
    r3 = conv.receive("The real problem is I don't have a system. Every week I start from scratch. Nothing builds on itself.")
    print(f"\n  [Turn 3] Stage: {conv.state.stage}")
    print(f"  Intent: {conv.state.turns[-2]['intent_detected']}")
    print(f"  Synthesis ready: {conv.state.synthesis_ready}")
    print(f"  EPOS: {r3[:200]}...")

    # Verify state persisted
    conv_path = conv.vault / "cms" / "conversations" / f"{conv.state.conversation_id}.json"
    assert conv_path.exists()
    print(f"\n  State persisted: {conv_path}")
    print(f"  Total turns: {len(conv.state.turns)}")
    print(f"  Detected needs: {len(conv.state.detected_needs)}")

    print("\nPASS: EPOSConversation — consultative engine operational")
