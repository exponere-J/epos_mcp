#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
reputation_manager.py — EPOS Reputation Management Node
==========================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Review Monitoring, Response, Sentiment Tracking

Manages online reputation for EPOS clients:
  - Monitor reviews across Google Business, Yelp, industry platforms
  - Generate response templates based on sentiment
  - Track reputation score over time
  - Route review signals to Lead Scoring and FOTW
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


REP_VAULT = get_context_vault() / "reputation"

SENTIMENT_KEYWORDS = {
    "positive": ["great", "excellent", "amazing", "love", "best", "recommend",
                 "professional", "helpful", "outstanding", "fantastic", "perfect"],
    "negative": ["terrible", "worst", "awful", "rude", "unprofessional", "scam",
                 "disappointing", "waste", "horrible", "never again", "avoid"],
    "neutral": ["okay", "fine", "average", "decent", "alright", "expected"],
}


class ReputationManager:
    """
    Monitors, analyzes, and responds to online reviews.
    Tracks reputation score and routes signals to intelligence.
    """

    def __init__(self, client_id: str = "default", vault_path: Path = None):
        self.client_id = client_id
        self.vault = vault_path or REP_VAULT / client_id
        self.vault.mkdir(parents=True, exist_ok=True)
        self._journal_path = self.vault / "reputation_journal.jsonl"

    def ingest_review(self, platform: str, reviewer: str, rating: int,
                      text: str, review_date: str = None) -> dict:
        """Ingest and analyze a review."""
        review_id = f"REV-{uuid.uuid4().hex[:8]}"
        sentiment = self._analyze_sentiment(text, rating)

        review = {
            "review_id": review_id,
            "client_id": self.client_id,
            "platform": platform,
            "reviewer": reviewer,
            "rating": rating,
            "text": text[:500],
            "review_date": review_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "sentiment": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "keywords": sentiment["keywords"],
            "response_needed": rating <= 3 or sentiment["label"] == "negative",
            "response_generated": False,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save review
        reviews_dir = self.vault / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)
        (reviews_dir / f"{review_id}.json").write_text(
            json.dumps(review, indent=2), encoding="utf-8")

        # Journal
        self._journal("review.ingested", {
            "review_id": review_id, "platform": platform,
            "rating": rating, "sentiment": sentiment["label"]})

        # Publish event
        if _BUS:
            try:
                _BUS.publish("reputation.review.received", {
                    "review_id": review_id, "client_id": self.client_id,
                    "platform": platform, "rating": rating,
                    "sentiment": sentiment["label"],
                }, source_module="reputation_manager")
            except Exception:
                pass

        # Auto-generate response for negative reviews
        if review["response_needed"]:
            review["suggested_response"] = self._generate_response(review)
            review["response_generated"] = True
            (reviews_dir / f"{review_id}.json").write_text(
                json.dumps(review, indent=2), encoding="utf-8")

        return review

    def _analyze_sentiment(self, text: str, rating: int) -> dict:
        """Analyze review sentiment from text and rating."""
        text_lower = text.lower()
        pos = sum(1 for w in SENTIMENT_KEYWORDS["positive"] if w in text_lower)
        neg = sum(1 for w in SENTIMENT_KEYWORDS["negative"] if w in text_lower)

        # Combined signal from text and rating
        text_score = (pos - neg) / max(pos + neg, 1)
        rating_score = (rating - 3) / 2  # Normalize 1-5 to -1 to +1
        combined = (text_score * 0.4 + rating_score * 0.6)

        if combined > 0.2:
            label = "positive"
        elif combined < -0.2:
            label = "negative"
        else:
            label = "neutral"

        keywords = [w for w in SENTIMENT_KEYWORDS["positive"] if w in text_lower]
        keywords += [w for w in SENTIMENT_KEYWORDS["negative"] if w in text_lower]

        return {"label": label, "score": round(combined, 2), "keywords": keywords}

    def _generate_response(self, review: dict) -> str:
        """Generate a response template for a review."""
        if GroqRouter:
            try:
                router = GroqRouter()
                prompt = (
                    f"Write a professional, empathetic response to this {review['rating']}-star review:\n"
                    f"\"{review['text'][:300]}\"\n\n"
                    f"Rules:\n"
                    f"- Acknowledge their experience\n"
                    f"- Don't be defensive\n"
                    f"- Offer to resolve if negative\n"
                    f"- Keep under 100 words\n"
                    f"- Be warm and genuine"
                )
                return router.route("summarization", prompt, max_tokens=200, temperature=0.5)
            except Exception:
                pass

        # Template fallback
        if review["rating"] <= 2:
            return (f"Thank you for sharing your experience. We take this feedback seriously "
                    f"and would like to make this right. Please reach out directly so we "
                    f"can address your concerns.")
        elif review["rating"] == 3:
            return (f"Thank you for your honest feedback. We're always working to improve "
                    f"and appreciate you taking the time to share your thoughts.")
        else:
            return f"Thank you for the kind words! We appreciate your trust."

    def get_reputation_score(self) -> dict:
        """Calculate aggregate reputation score for client."""
        reviews_dir = self.vault / "reviews"
        if not reviews_dir.exists():
            return {"score": 0, "total_reviews": 0, "avg_rating": 0, "by_platform": {}}

        ratings = []
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        by_platform = {}

        for f in reviews_dir.glob("REV-*.json"):
            r = json.loads(f.read_text(encoding="utf-8"))
            ratings.append(r["rating"])
            sentiments[r.get("sentiment", "neutral")] += 1
            p = r["platform"]
            if p not in by_platform:
                by_platform[p] = {"count": 0, "avg_rating": 0, "total": 0}
            by_platform[p]["count"] += 1
            by_platform[p]["total"] += r["rating"]

        for p in by_platform:
            by_platform[p]["avg_rating"] = round(by_platform[p]["total"] / by_platform[p]["count"], 1)

        avg = sum(ratings) / len(ratings) if ratings else 0
        # Reputation score: weighted average of rating and sentiment
        rep_score = (avg / 5 * 70) + (sentiments["positive"] / max(len(ratings), 1) * 30)

        return {
            "score": round(rep_score, 1),
            "total_reviews": len(ratings),
            "avg_rating": round(avg, 1),
            "sentiments": sentiments,
            "by_platform": by_platform,
        }

    def get_pending_responses(self) -> list:
        """Get reviews that need responses."""
        reviews_dir = self.vault / "reviews"
        if not reviews_dir.exists():
            return []
        pending = []
        for f in reviews_dir.glob("REV-*.json"):
            r = json.loads(f.read_text(encoding="utf-8"))
            if r.get("response_needed") and not r.get("response_posted"):
                pending.append(r)
        return pending

    def _journal(self, event_type: str, payload: dict):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "event_type": event_type, "payload": payload}
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    passed = 0
    rm = ReputationManager(client_id="test_client")

    # Test 1: Ingest positive review
    r1 = rm.ingest_review("google", "Jane D", 5,
                           "Amazing service! Professional team, highly recommend.")
    assert r1["sentiment"] == "positive"
    assert not r1["response_needed"]
    passed += 1

    # Test 2: Ingest negative review (should auto-generate response)
    r2 = rm.ingest_review("yelp", "Bob S", 2,
                           "Terrible experience. Unprofessional and disappointing.")
    assert r2["sentiment"] == "negative"
    assert r2["response_needed"]
    assert r2["response_generated"]
    passed += 1

    # Test 3: Reputation score
    score = rm.get_reputation_score()
    assert score["total_reviews"] == 2
    assert 0 <= score["score"] <= 100
    passed += 1

    # Test 4: Pending responses
    pending = rm.get_pending_responses()
    assert len(pending) >= 1
    passed += 1

    print(f"PASS: reputation_manager ({passed} assertions)")
    print(f"Score: {score['score']}/100 | Reviews: {score['total_reviews']} | Avg: {score['avg_rating']}/5")
