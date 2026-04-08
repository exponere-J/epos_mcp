#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
fotw_listener.py — Fly on the Wall: Expression Listener
=========================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Engagement Intelligence

Captures expressions from content comments, call transcripts,
and live interactions. Routes signals to Lead Scoring, Sequential
Segmentation, TTLG context enrichment, and content feedback loops.

Architecture:
  1. CAPTURE — Ingest raw expressions from multiple sources
  2. CLASSIFY — Determine intent, emotion, and interest cluster
  3. ROUTE — Feed signals to downstream intelligence nodes
  4. CLUSTER — Group expressions into interest-based segments

Sources:
  - Content comments (YouTube, LinkedIn, X, TikTok, Instagram)
  - Call transcripts (post-TTLG diagnostic)
  - Manual observations (vault riffs about prospect behavior)
  - Form submissions (lead capture, survey responses)
"""

import json
import uuid
import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

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
    from groq_router import GroqRouter
except ImportError:
    GroqRouter = None

from path_utils import get_context_vault


# ── Configuration ───────────────────────────────────────────

FOTW_VAULT = get_context_vault() / "fotw"
EXPRESSIONS_DIR = FOTW_VAULT / "expressions"
CLUSTERS_DIR = FOTW_VAULT / "clusters"
TRANSCRIPTS_DIR = FOTW_VAULT / "transcripts"

# Expression classification taxonomy
INTENT_TYPES = [
    "question",       # Asking for information
    "interest",       # Expressing curiosity about a topic
    "objection",      # Pushing back or expressing concern
    "validation",     # Confirming or agreeing with content
    "pain",           # Expressing frustration or problem
    "desire",         # Expressing want or aspiration
    "referral",       # Pointing others to content
    "complaint",      # Negative feedback
]

EMOTION_SPECTRUM = [
    "curious", "frustrated", "excited", "skeptical",
    "impressed", "confused", "motivated", "anxious",
]

# Interest clusters for segmentation
INTEREST_CLUSTERS = {
    "sovereignty": ["own", "control", "independent", "freedom", "self-hosted", "sovereign"],
    "content_production": ["content", "video", "script", "publish", "audience", "creator"],
    "business_growth": ["revenue", "growth", "scale", "profit", "client", "customer"],
    "technology": ["ai", "automation", "tool", "platform", "software", "api"],
    "marketing": ["marketing", "ads", "seo", "brand", "reach", "engagement"],
    "leadership": ["team", "leadership", "culture", "management", "hire", "delegate"],
}


class FOTWListener:
    """
    Fly on the Wall — captures and classifies expressions from
    content engagement, calls, and direct interactions.
    """

    def __init__(self, vault_path: Path = None):
        self.vault = vault_path or FOTW_VAULT
        self.expressions_dir = self.vault / "expressions"
        self.clusters_dir = self.vault / "clusters"
        self.transcripts_dir = self.vault / "transcripts"
        for d in (self.expressions_dir, self.clusters_dir, self.transcripts_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._journal_path = self.vault / "fotw_journal.jsonl"

    # ── Capture ─────────────────────────────────────────────

    def capture_comment(self, platform: str, content_id: str,
                        author: str, text: str,
                        metadata: dict = None) -> dict:
        """Capture a content comment as an expression."""
        return self._capture_expression(
            source_type="comment",
            source_platform=platform,
            source_id=content_id,
            author=self._anonymize(author),
            raw_text=text,
            metadata=metadata or {},
        )

    def capture_transcript_segment(self, call_id: str,
                                   speaker: str, text: str,
                                   timestamp_seconds: float = 0) -> dict:
        """Capture a segment from a call transcript."""
        return self._capture_expression(
            source_type="transcript",
            source_platform="call",
            source_id=call_id,
            author=self._anonymize(speaker),
            raw_text=text,
            metadata={"timestamp_seconds": timestamp_seconds},
        )

    def capture_observation(self, observer: str, text: str,
                            context: str = "") -> dict:
        """Capture a manual observation about prospect behavior."""
        return self._capture_expression(
            source_type="observation",
            source_platform="manual",
            source_id=f"OBS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            author=observer,
            raw_text=text,
            metadata={"context": context},
        )

    def capture_form_submission(self, form_id: str,
                                email: str, responses: dict) -> dict:
        """Capture survey/form responses as expressions."""
        text = " | ".join(f"{k}: {v}" for k, v in responses.items())
        return self._capture_expression(
            source_type="form",
            source_platform="web",
            source_id=form_id,
            author=self._anonymize(email),
            raw_text=text,
            metadata={"email_hash": hashlib.sha256(email.encode()).hexdigest()[:12],
                       "form_id": form_id},
        )

    def _capture_expression(self, source_type: str, source_platform: str,
                            source_id: str, author: str, raw_text: str,
                            metadata: dict) -> dict:
        """Internal: create, classify, and store an expression."""
        expr_id = f"EXPR-{uuid.uuid4().hex[:8]}"

        # Classify
        classification = self._classify(raw_text)

        expression = {
            "expression_id": expr_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "source_type": source_type,
            "source_platform": source_platform,
            "source_id": source_id,
            "author": author,
            "raw_text": raw_text[:500],
            "intent": classification["intent"],
            "emotion": classification["emotion"],
            "interest_clusters": classification["clusters"],
            "keywords": classification["keywords"],
            "lead_signal_strength": classification["signal_strength"],
            "metadata": metadata,
            "routed_to": [],
        }

        # Save expression
        expr_path = self.expressions_dir / f"{expr_id}.json"
        expr_path.write_text(json.dumps(expression, indent=2), encoding="utf-8")

        # Journal
        self._journal("expression.captured", {
            "expression_id": expr_id, "source_type": source_type,
            "intent": classification["intent"],
            "signal_strength": classification["signal_strength"],
        })

        # Route to downstream systems
        self._route_expression(expression)

        # Publish event
        if _BUS:
            try:
                _BUS.publish("fotw.expression.captured", {
                    "expression_id": expr_id,
                    "source_type": source_type,
                    "intent": classification["intent"],
                    "signal_strength": classification["signal_strength"],
                    "clusters": classification["clusters"],
                }, source_module="fotw_listener")
            except Exception:
                pass

        return expression

    # ── Classification ──────────────────────────────────────

    def _classify(self, text: str) -> dict:
        """Classify expression intent, emotion, and interest clusters."""
        text_lower = text.lower()

        # Intent detection (rule-based, fast)
        if "?" in text:
            intent = "question"
        elif any(w in text_lower for w in ["frustrated", "annoyed", "hate", "terrible", "broken"]):
            intent = "pain"
        elif any(w in text_lower for w in ["want", "need", "wish", "looking for", "how do i"]):
            intent = "desire"
        elif any(w in text_lower for w in ["but", "however", "concern", "worried", "not sure"]):
            intent = "objection"
        elif any(w in text_lower for w in ["amazing", "love", "great", "this is exactly"]):
            intent = "validation"
        elif any(w in text_lower for w in ["check out", "recommend", "try this", "you should"]):
            intent = "referral"
        elif any(w in text_lower for w in ["interesting", "curious", "tell me more", "how does"]):
            intent = "interest"
        else:
            intent = "interest"

        # Emotion detection
        if any(w in text_lower for w in ["excited", "amazing", "love"]):
            emotion = "excited"
        elif any(w in text_lower for w in ["confused", "don't understand", "unclear"]):
            emotion = "confused"
        elif any(w in text_lower for w in ["frustrated", "annoyed", "tired of"]):
            emotion = "frustrated"
        elif any(w in text_lower for w in ["interested", "curious", "wondering"]):
            emotion = "curious"
        elif any(w in text_lower for w in ["impressed", "wow", "incredible"]):
            emotion = "impressed"
        elif any(w in text_lower for w in ["skeptical", "really?", "doubt", "seems too"]):
            emotion = "skeptical"
        else:
            emotion = "curious"

        # Interest cluster matching
        clusters = []
        for cluster_name, keywords in INTEREST_CLUSTERS.items():
            if any(kw in text_lower for kw in keywords):
                clusters.append(cluster_name)

        # Keyword extraction (simple: words > 4 chars, not common)
        stop_words = {"this", "that", "with", "from", "have", "been", "will", "your",
                      "about", "would", "could", "should", "their", "there", "these",
                      "those", "what", "when", "where", "which", "while"}
        words = re.findall(r'\b[a-z]{4,}\b', text_lower)
        keywords = [w for w in set(words) if w not in stop_words][:10]

        # Signal strength (0-100): how actionable is this for Lead Scoring
        strength = 30  # base
        if intent in ("desire", "pain"):
            strength += 30
        elif intent in ("question", "interest"):
            strength += 15
        elif intent == "referral":
            strength += 25
        if emotion in ("excited", "motivated"):
            strength += 15
        elif emotion in ("frustrated", "anxious"):
            strength += 20
        if clusters:
            strength += len(clusters) * 5
        strength = min(strength, 100)

        return {
            "intent": intent,
            "emotion": emotion,
            "clusters": clusters,
            "keywords": keywords,
            "signal_strength": strength,
        }

    # ── Routing ─────────────────────────────────────────────

    def _route_expression(self, expression: dict):
        """Route classified expression to downstream intelligence."""
        routes = []
        strength = expression["lead_signal_strength"]

        # High-signal expressions -> Lead Scoring
        if strength >= 60:
            routes.append("lead_scoring")
            if _BUS:
                try:
                    _BUS.publish("fotw.lead.signal", {
                        "expression_id": expression["expression_id"],
                        "author": expression["author"],
                        "intent": expression["intent"],
                        "signal_strength": strength,
                    }, source_module="fotw_listener")
                except Exception:
                    pass

        # Questions and desires -> Content feedback loop
        if expression["intent"] in ("question", "desire", "pain"):
            routes.append("content_signal_loop")

        # Interest clusters -> Sequential segmentation
        if expression["interest_clusters"]:
            routes.append("segmentation")

        expression["routed_to"] = routes

    # ── Clustering ──────────────────────────────────────────

    def cluster_expressions(self, hours: int = 168) -> dict:
        """Cluster recent expressions by interest for segmentation."""
        cutoff = datetime.now(timezone.utc).isoformat()
        cluster_counts = {c: 0 for c in INTEREST_CLUSTERS}
        cluster_expressions = {c: [] for c in INTEREST_CLUSTERS}

        for expr_path in self.expressions_dir.glob("EXPR-*.json"):
            expr = json.loads(expr_path.read_text(encoding="utf-8"))
            for cluster in expr.get("interest_clusters", []):
                if cluster in cluster_counts:
                    cluster_counts[cluster] += 1
                    cluster_expressions[cluster].append(expr["expression_id"])

        # Save cluster state
        cluster_state = {
            "clustered_at": datetime.now(timezone.utc).isoformat(),
            "window_hours": hours,
            "clusters": {c: {"count": cluster_counts[c],
                              "expressions": cluster_expressions[c][:20]}
                          for c in INTEREST_CLUSTERS},
        }
        cluster_path = self.clusters_dir / "latest_clusters.json"
        cluster_path.write_text(json.dumps(cluster_state, indent=2), encoding="utf-8")

        if _BUS:
            try:
                active = {c: n for c, n in cluster_counts.items() if n > 0}
                _BUS.publish("fotw.clusters.updated", {
                    "active_clusters": len(active),
                    "total_expressions": sum(cluster_counts.values()),
                }, source_module="fotw_listener")
            except Exception:
                pass

        return cluster_state

    # ── Status & Journal ────────────────────────────────────

    def get_status(self) -> dict:
        """FOTW node health summary."""
        expr_count = len(list(self.expressions_dir.glob("EXPR-*.json")))
        transcript_count = len(list(self.transcripts_dir.glob("*.json")))
        journal_lines = 0
        if self._journal_path.exists():
            journal_lines = sum(1 for l in self._journal_path.read_text(encoding="utf-8").splitlines() if l.strip())

        return {
            "expressions_captured": expr_count,
            "transcripts_stored": transcript_count,
            "journal_entries": journal_lines,
            "clusters": list(INTEREST_CLUSTERS.keys()),
            "vault_path": str(self.vault),
        }

    def _journal(self, event_type: str, payload: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    @staticmethod
    def _anonymize(identifier: str) -> str:
        """Anonymize user identifiers for privacy."""
        return f"ANON-{hashlib.sha256(identifier.encode()).hexdigest()[:8]}"


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    listener = FOTWListener()

    # Test 1: Capture a comment
    expr = listener.capture_comment(
        platform="youtube", content_id="VIDEO-001",
        author="john@test.com",
        text="How do I build a content engine like this? I'm frustrated with manual posting.")
    assert expr["intent"] == "pain" or expr["intent"] == "question"
    assert expr["lead_signal_strength"] > 30
    passed += 1

    # Test 2: Capture an observation
    obs = listener.capture_observation("Jamie",
        "PGP Orlando asked about sovereign content engines during the diagnostic call",
        context="TTLG follow-up")
    assert obs["expression_id"].startswith("EXPR-")
    passed += 1

    # Test 3: Classification
    cls = listener._classify("I'm really interested in automating my content pipeline but worried about quality")
    assert cls["intent"] in INTENT_TYPES
    assert cls["emotion"] in EMOTION_SPECTRUM
    assert len(cls["clusters"]) > 0
    passed += 1

    # Test 4: Clustering
    clusters = listener.cluster_expressions()
    assert "clusters" in clusters
    passed += 1

    # Test 5: Status
    status = listener.get_status()
    assert status["expressions_captured"] >= 2
    passed += 1

    print(f"PASS: fotw_listener ({passed} assertions)")
    print(f"Expressions: {status['expressions_captured']}")
    print(f"Clusters: {len([c for c, d in clusters['clusters'].items() if d['count'] > 0])} active")
