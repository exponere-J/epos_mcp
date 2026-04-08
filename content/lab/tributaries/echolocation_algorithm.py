# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/content/lab/tributaries/echolocation_algorithm.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
EPOS Content Lab - Echolocation Algorithm (Node AN1)
Component: C10_CONTENT_LAB / Tributary Engine
Path: epos_mcp/content/lab/tributaries/echolocation_algorithm.py

Computes Resonance Score (0-100) for captured content using:
  - Engagement signals (likes, shares, comments, saves)
  - Velocity (interactions per hour)
  - Audience quality (follower ratio, verified engagement)
  - Brand alignment (keyword matching)

Constitutional Requirements:
  - All decisions logged to Context Vault
  - No content proceeds without scoring
  - Score > 85 triggers expansion protocol
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent.parent)))
VAULT_PATH = EPOS_ROOT / "context_vault"
DECISION_LOG = VAULT_PATH / "bi_history" / "echolocation_decisions.jsonl"
EVENT_LOG = VAULT_PATH / "events" / "system_events.jsonl"

BRAND_KEYWORDS = [
    "sovereignty", "sovereign", "epos", "exponere", "local-first",
    "constitutional", "governance", "agent zero", "node", "flywheel",
    "data ownership", "air-gapped", "automation", "ai-led",
    "pgp", "pressure washing", "property solutions",
]

# Weights for resonance scoring (must sum to 1.0)
WEIGHTS = {
    "engagement": 0.30,
    "velocity": 0.25,
    "audience_quality": 0.20,
    "brand_alignment": 0.25,
}

# Thresholds
EXPANSION_THRESHOLD = 85
PROMOTION_THRESHOLD = 60
KILL_THRESHOLD = 25


# ---------------------------------------------------------------------------
# Platform-specific normalization curves
# ---------------------------------------------------------------------------

PLATFORM_NORMS = {
    "x": {
        "engagement_base": 100,     # 100 interactions = "good"
        "impressions_base": 1000,
        "velocity_base": 10,        # 10 interactions/hour
    },
    "tiktok": {
        "engagement_base": 500,
        "impressions_base": 5000,
        "velocity_base": 50,
    },
    "linkedin": {
        "engagement_base": 50,
        "impressions_base": 500,
        "velocity_base": 5,
    },
    "youtube": {
        "engagement_base": 200,
        "impressions_base": 2000,
        "velocity_base": 20,
    },
    "instagram": {
        "engagement_base": 300,
        "impressions_base": 3000,
        "velocity_base": 30,
    },
}


# ---------------------------------------------------------------------------
# Core Algorithm
# ---------------------------------------------------------------------------

class EcholocationAlgorithm:
    """
    Algorithmic Echolocation: scores content resonance and recommends actions.

    Usage:
        algo = EcholocationAlgorithm()
        result = algo.analyze(content_metrics)
        # result.score, result.action, result.transformations
    """

    def __init__(self, weights: Optional[dict] = None):
        self.weights = weights or WEIGHTS
        self._validate_weights()

    def _validate_weights(self):
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def analyze(self, metrics: dict) -> dict:
        """
        Analyze a single content unit and return resonance assessment.

        Args:
            metrics: {
                "content_id": str,
                "platform": "x" | "tiktok" | "linkedin" | "youtube" | "instagram",
                "text": str,                     # content text / transcript
                "likes": int,
                "shares": int,                   # retweets, reposts, etc.
                "comments": int,
                "saves": int,
                "impressions": int,
                "hours_live": float,              # hours since publish
                "follower_count": int,            # of the account
                "verified_engagers": int,         # optional
            }

        Returns:
            {
                "content_id": str,
                "platform": str,
                "score": float (0-100),
                "components": { engagement, velocity, audience, brand },
                "action": "expand" | "promote" | "hold" | "kill",
                "transformations": [str],         # recommended derivative formats
                "predicted_engagement": { platform: int },
                "reasoning": str,
                "timestamp": str,
            }
        """
        platform = metrics.get("platform", "x")
        norms = PLATFORM_NORMS.get(platform, PLATFORM_NORMS["x"])

        # Component scores (each 0-100)
        engagement_score = self._score_engagement(metrics, norms)
        velocity_score = self._score_velocity(metrics, norms)
        audience_score = self._score_audience_quality(metrics)
        brand_score = self._score_brand_alignment(metrics)

        # Weighted composite
        composite = (
            engagement_score * self.weights["engagement"]
            + velocity_score * self.weights["velocity"]
            + audience_score * self.weights["audience_quality"]
            + brand_score * self.weights["brand_alignment"]
        )
        score = round(min(max(composite, 0), 100), 1)

        # Determine action
        action = self._determine_action(score)

        # Generate transformation recommendations
        transformations = self._recommend_transformations(score, platform)

        # Predict engagement for derivatives
        predicted = self._predict_derivative_engagement(metrics, score)

        # Build reasoning string
        reasoning = self._build_reasoning(
            score, engagement_score, velocity_score,
            audience_score, brand_score, action, platform,
        )

        result = {
            "content_id": metrics.get("content_id", "unknown"),
            "platform": platform,
            "score": score,
            "components": {
                "engagement": round(engagement_score, 1),
                "velocity": round(velocity_score, 1),
                "audience_quality": round(audience_score, 1),
                "brand_alignment": round(brand_score, 1),
            },
            "action": action,
            "transformations": transformations,
            "predicted_engagement": predicted,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Log decision (constitutional requirement)
        self._log_decision(result)

        return result

    def batch_analyze(self, metrics_list: list[dict]) -> list[dict]:
        """Analyze multiple content units. Returns sorted by score descending."""
        results = [self.analyze(m) for m in metrics_list]
        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    # -------------------------------------------------------------------
    # Scoring components
    # -------------------------------------------------------------------

    def _score_engagement(self, metrics: dict, norms: dict) -> float:
        total = (
            metrics.get("likes", 0)
            + metrics.get("shares", 0) * 2    # shares worth 2x
            + metrics.get("comments", 0) * 3  # comments worth 3x
            + metrics.get("saves", 0) * 4     # saves worth 4x
        )
        ratio = total / max(norms["engagement_base"], 1)
        return min(ratio * 50, 100)  # 2x base = 100

    def _score_velocity(self, metrics: dict, norms: dict) -> float:
        hours = max(metrics.get("hours_live", 1), 0.1)
        total_engagement = (
            metrics.get("likes", 0)
            + metrics.get("shares", 0)
            + metrics.get("comments", 0)
            + metrics.get("saves", 0)
        )
        velocity = total_engagement / hours
        ratio = velocity / max(norms["velocity_base"], 1)
        return min(ratio * 50, 100)

    def _score_audience_quality(self, metrics: dict) -> float:
        impressions = max(metrics.get("impressions", 1), 1)
        total_eng = (
            metrics.get("likes", 0)
            + metrics.get("shares", 0)
            + metrics.get("comments", 0)
        )
        engagement_rate = total_eng / impressions

        # Baseline: 2% engagement rate = 50 score
        base_score = min((engagement_rate / 0.02) * 50, 80)

        # Bonus for verified engagers
        verified = metrics.get("verified_engagers", 0)
        verified_bonus = min(verified * 2, 20)

        return min(base_score + verified_bonus, 100)

    def _score_brand_alignment(self, metrics: dict) -> float:
        text = (metrics.get("text", "") or "").lower()
        if not text:
            return 30  # Neutral if no text available

        matches = sum(1 for kw in BRAND_KEYWORDS if kw in text)
        # 1 match = 40, 2 = 60, 3 = 75, 4+ = 85+
        if matches == 0:
            return 20
        elif matches == 1:
            return 40
        elif matches == 2:
            return 60
        elif matches == 3:
            return 75
        else:
            return min(85 + (matches - 4) * 3, 100)

    # -------------------------------------------------------------------
    # Action determination
    # -------------------------------------------------------------------

    def _determine_action(self, score: float) -> str:
        if score >= EXPANSION_THRESHOLD:
            return "expand"     # Trigger expansion protocol
        elif score >= PROMOTION_THRESHOLD:
            return "promote"    # Move to production queue
        elif score >= KILL_THRESHOLD:
            return "hold"       # Keep monitoring
        else:
            return "kill"       # Archive, stop tracking

    def _recommend_transformations(self, score: float, platform: str) -> list[str]:
        if score < PROMOTION_THRESHOLD:
            return []

        # Base recommendations by source platform
        recs = {
            "x": ["linkedin_post", "blog_outline", "youtube_script_segment", "email_section"],
            "tiktok": ["youtube_short", "instagram_reel", "linkedin_video", "blog_post"],
            "linkedin": ["x_thread", "tiktok_script", "email_newsletter", "youtube_segment"],
            "youtube": ["x_thread", "linkedin_carousel", "tiktok_clips", "blog_post", "email"],
            "instagram": ["tiktok_remix", "x_post", "linkedin_post"],
        }

        base = recs.get(platform, recs["x"])

        # Higher scores unlock more transformations
        if score >= EXPANSION_THRESHOLD:
            base.append("whitepaper_section")
            base.append("layer_6_prospectus")
        if score >= 90:
            base.append("case_study")
            base.append("webinar_segment")

        return base

    def _predict_derivative_engagement(self, metrics: dict, score: float) -> dict:
        """Predict engagement for derivative content based on source performance."""
        base_eng = (
            metrics.get("likes", 0)
            + metrics.get("shares", 0)
            + metrics.get("comments", 0)
        )
        multiplier = score / 100

        return {
            "linkedin": int(base_eng * 0.4 * multiplier),
            "x": int(base_eng * 0.6 * multiplier),
            "tiktok": int(base_eng * 1.5 * multiplier),
            "youtube": int(base_eng * 0.8 * multiplier),
            "email": int(base_eng * 0.2 * multiplier),
        }

    # -------------------------------------------------------------------
    # Reasoning and logging
    # -------------------------------------------------------------------

    def _build_reasoning(self, score, eng, vel, aud, brand, action, platform) -> str:
        parts = [f"Resonance={score}/100 on {platform}."]
        top = max(
            ("engagement", eng), ("velocity", vel),
            ("audience", aud), ("brand", brand),
            key=lambda x: x[1],
        )
        parts.append(f"Strongest signal: {top[0]} ({top[1]}/100).")

        if action == "expand":
            parts.append("EXPANSION TRIGGERED: score exceeds 85. Deploy cascade + Layer 6.")
        elif action == "promote":
            parts.append("Promote to production queue for derivative generation.")
        elif action == "hold":
            parts.append("Below promotion threshold. Continue monitoring.")
        else:
            parts.append("Below kill threshold. Archive and stop tracking.")

        return " ".join(parts)

    def _log_decision(self, result: dict):
        """Log to Context Vault for constitutional compliance."""
        DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event_type": "echolocation.decision",
            "content_id": result["content_id"],
            "score": result["score"],
            "action": result["action"],
            "platform": result["platform"],
            "timestamp": result["timestamp"],
        }
        try:
            with open(DECISION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass  # Graceful degradation per constitution

        # Also emit to event bus
        self._emit_event(result)

    def _emit_event(self, result: dict):
        """Emit event to EPOS Unified Event Bus."""
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "event_type": f"content.echolocation.{result['action']}",
            "payload": {
                "content_id": result["content_id"],
                "score": result["score"],
                "platform": result["platform"],
                "transformations": result["transformations"],
            },
            "timestamp": result["timestamp"],
            "source": "AN1_echolocation",
        }
        try:
            with open(EVENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Health check (for EPOS Doctor integration)
# ---------------------------------------------------------------------------

def health_check() -> dict:
    """Return health status for C10 tributary subsystem."""
    checks = {
        "algorithm_importable": True,
        "vault_path_exists": VAULT_PATH.exists(),
        "decision_log_writable": _check_writable(DECISION_LOG),
        "event_log_writable": _check_writable(EVENT_LOG),
        "weights_valid": abs(sum(WEIGHTS.values()) - 1.0) < 0.01,
    }
    status = "healthy" if all(checks.values()) else "degraded"
    return {"component": "echolocation_algorithm", "status": status, "checks": checks}


def _check_writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            pass
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# CLI for manual testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    algo = EcholocationAlgorithm()

    # Test with sample data
    test_metrics = {
        "content_id": "TEST_001",
        "platform": "x",
        "text": "Your AI strategy is a high-interest loan from OpenAI. Sovereignty isn't a feature. It's survival. #EPOS",
        "likes": 150,
        "shares": 45,
        "comments": 22,
        "saves": 18,
        "impressions": 3500,
        "hours_live": 4.0,
        "follower_count": 1200,
        "verified_engagers": 3,
    }

    result = algo.analyze(test_metrics)
    print(json.dumps(result, indent=2))
    print(f"\nHealth: {json.dumps(health_check(), indent=2)}")
