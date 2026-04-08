#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
crs_scorer.py — Communication Resonance Score (CRS)
====================================================================
Constitutional Authority: EPOS Constitution v3.1 — Communication Layer

Echolocation for 1-to-1 communications. Tracks opens, clicks, replies,
conversions, and sentiment per communication per avatar. Each avatar
carries its own CRS weights (from the avatar profile) — so what counts
as 'high resonance' differs per segment.

Core operations:
  - score_communication(comm_id, avatar_id, metrics) -> score 0-100
  - record_open/click/reply/conversion
  - get_avatar_crs_history(avatar_id)
  - threshold_crossed(avatar_id, threshold) -> bool
  - health_check()
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from path_utils import get_context_vault

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

VAULT = get_context_vault()
CRS_ROOT = VAULT / "crs"
CRS_ROOT.mkdir(parents=True, exist_ok=True)
CRS_LOG = CRS_ROOT / "crs_scores.jsonl"
CRS_EVENTS = CRS_ROOT / "events.jsonl"

# Default CRS weights (used when avatar profile doesn't specify)
DEFAULT_WEIGHTS = {
    "open": 0.15,
    "click": 0.20,
    "reply": 0.30,
    "conversion": 0.25,
    "sentiment": 0.10,
}

# Thresholds for expansion triggers
HIGH_RESONANCE_THRESHOLD = 75.0
CRITICAL_THRESHOLD = 90.0


class CRSScorer:
    """Communication Resonance Scorer."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = Path(log_path) if log_path else CRS_LOG

    def _get_weights(self, avatar_id: str) -> dict:
        """Pull CRS weights from avatar profile; fall back to defaults.

        The avatar profile's crs_weights describe content-layer weights
        (engagement, intent_keywords, channel_match, timing, social_proof_response).
        For communications we map these to open/click/reply/conversion/sentiment.
        """
        try:
            from nodes.avatar_registry import get_registry
            avatar = get_registry().get_avatar(avatar_id) or {}
        except Exception:
            avatar = {}

        avatar_weights = avatar.get("crs_weights", {}) or {}

        # Preferred: avatar supplies direct comm weights
        if {"open", "click", "reply", "conversion", "sentiment"} & set(avatar_weights.keys()):
            merged = dict(DEFAULT_WEIGHTS)
            merged.update({k: v for k, v in avatar_weights.items() if k in DEFAULT_WEIGHTS})
            return merged

        # Otherwise, map content-layer weights onto comm dimensions
        # engagement -> reply, intent_keywords -> click, channel_match -> open,
        # timing -> sentiment, social_proof_response -> conversion
        mapping = {
            "engagement": "reply",
            "intent_keywords": "click",
            "channel_match": "open",
            "timing": "sentiment",
            "social_proof_response": "conversion",
        }
        mapped = dict(DEFAULT_WEIGHTS)
        for src, dst in mapping.items():
            if src in avatar_weights:
                mapped[dst] = float(avatar_weights[src])
        # Normalize so they sum to 1.0
        total = sum(mapped.values())
        if total > 0:
            mapped = {k: round(v / total, 4) for k, v in mapped.items()}
        return mapped

    def score_communication(self, comm_id: str, avatar_id: str,
                            metrics: dict) -> float:
        """Score a single communication against the avatar's CRS weights."""
        weights = self._get_weights(avatar_id)

        open_bit = 1.0 if metrics.get("open") else 0.0
        click_bit = 1.0 if metrics.get("click") else 0.0
        reply_bit = 1.0 if metrics.get("reply") else 0.0
        converted_bit = 1.0 if metrics.get("converted") or metrics.get("conversion") else 0.0
        sentiment_val = float(metrics.get("sentiment", 0.5))

        raw = (
            open_bit * weights.get("open", 0.15) +
            click_bit * weights.get("click", 0.20) +
            reply_bit * weights.get("reply", 0.30) +
            converted_bit * weights.get("conversion", 0.25) +
            sentiment_val * weights.get("sentiment", 0.10)
        )
        score = round(raw * 100, 2)

        self._log_score(comm_id, avatar_id, score, metrics, weights)

        # Emit high-resonance event
        if score >= HIGH_RESONANCE_THRESHOLD:
            self._emit("crs.threshold.crossed", {
                "comm_id": comm_id,
                "avatar_id": avatar_id,
                "score": score,
                "threshold": HIGH_RESONANCE_THRESHOLD,
            })
        if score >= CRITICAL_THRESHOLD:
            self._emit("crs.critical.resonance", {
                "comm_id": comm_id,
                "avatar_id": avatar_id,
                "score": score,
            })

        return score

    # ── Individual event recorders ───────────────────────────────

    def record_open(self, comm_id: str, avatar_id: str) -> dict:
        return self._record_event(comm_id, avatar_id, "open")

    def record_click(self, comm_id: str, avatar_id: str) -> dict:
        return self._record_event(comm_id, avatar_id, "click")

    def record_reply(self, comm_id: str, avatar_id: str, sentiment: float = 0.5) -> dict:
        return self._record_event(comm_id, avatar_id, "reply", {"sentiment": sentiment})

    def record_conversion(self, comm_id: str, avatar_id: str,
                          value: Optional[float] = None) -> dict:
        return self._record_event(comm_id, avatar_id, "conversion", {"value": value})

    def _record_event(self, comm_id: str, avatar_id: str,
                      event_kind: str, extra: Optional[dict] = None) -> dict:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comm_id": comm_id,
            "avatar_id": avatar_id,
            "event": event_kind,
            **(extra or {}),
        }
        with open(CRS_EVENTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        self._emit(f"comm.{event_kind}", record)
        return record

    # ── History / Analytics ──────────────────────────────────────

    def get_avatar_crs_history(self, avatar_id: str) -> dict:
        """Return CRS performance history for an avatar."""
        scores: list[dict] = []
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    if rec.get("avatar_id") == avatar_id:
                        scores.append(rec)

        if not scores:
            return {
                "avatar_id": avatar_id,
                "sample_count": 0,
                "mean_score": 0.0,
                "high_resonance_count": 0,
                "critical_count": 0,
                "latest": None,
            }

        mean = sum(s["score"] for s in scores) / len(scores)
        return {
            "avatar_id": avatar_id,
            "sample_count": len(scores),
            "mean_score": round(mean, 2),
            "high_resonance_count": sum(1 for s in scores if s["score"] >= HIGH_RESONANCE_THRESHOLD),
            "critical_count": sum(1 for s in scores if s["score"] >= CRITICAL_THRESHOLD),
            "latest": scores[-1],
        }

    def threshold_crossed(self, avatar_id: str,
                          threshold: float = HIGH_RESONANCE_THRESHOLD) -> bool:
        history = self.get_avatar_crs_history(avatar_id)
        return history.get("mean_score", 0) >= threshold and history["sample_count"] >= 3

    # ── Internals ────────────────────────────────────────────────

    def _log_score(self, comm_id: str, avatar_id: str,
                   score: float, metrics: dict, weights: dict):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comm_id": comm_id,
            "avatar_id": avatar_id,
            "score": score,
            "metrics": metrics,
            "weights_applied": weights,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _emit(self, event_type: str, payload: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="crs_scorer")
            except Exception:
                pass

    # ── Health ───────────────────────────────────────────────────

    def health_check(self) -> dict:
        try:
            count = 0
            if self.log_path.exists():
                with open(self.log_path, "r", encoding="utf-8") as f:
                    count = sum(1 for _ in f)
            return {
                "node": "crs_scorer",
                "status": "operational",
                "scores_recorded": count,
                "high_threshold": HIGH_RESONANCE_THRESHOLD,
                "critical_threshold": CRITICAL_THRESHOLD,
                "log_path": str(self.log_path),
            }
        except Exception as e:
            return {"node": "crs_scorer", "status": "error", "error": str(e)[:200]}


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    scorer = CRSScorer()

    # Test 1: Score a communication for local_champion
    score = scorer.score_communication(
        comm_id="COLD-001",
        avatar_id="local_champion",
        metrics={"open": True, "click": True, "reply": False, "converted": False, "sentiment": 0.7}
    )
    assert 0 <= score <= 100
    print(f"CRS Score (local_champion, open+click): {score}")
    passed += 1

    # Test 2: Full-funnel conversion
    score2 = scorer.score_communication(
        comm_id="WELCOME-001",
        avatar_id="solo_strategic_consultant",
        metrics={"open": True, "click": True, "reply": True, "converted": True, "sentiment": 0.9}
    )
    assert score2 > 75
    print(f"CRS Score (full conversion, consultant): {score2}")
    passed += 1

    # Test 3: Record individual events
    scorer.record_open("COLD-002", "boutique_agency_founder")
    scorer.record_click("COLD-002", "boutique_agency_founder")
    scorer.record_reply("COLD-002", "boutique_agency_founder", sentiment=0.8)
    passed += 1

    # Test 4: History
    # Add a few more for a valid history check
    for i in range(3):
        scorer.score_communication(
            comm_id=f"WELCOME-consultant-{i}",
            avatar_id="solo_strategic_consultant",
            metrics={"open": True, "click": True, "reply": True, "converted": False, "sentiment": 0.75}
        )
    hist = scorer.get_avatar_crs_history("solo_strategic_consultant")
    assert hist["sample_count"] >= 4
    print(f"Consultant CRS history: samples={hist['sample_count']} mean={hist['mean_score']}")
    passed += 1

    # Test 5: Threshold crossed detection
    crossed = scorer.threshold_crossed("solo_strategic_consultant", HIGH_RESONANCE_THRESHOLD)
    print(f"Threshold crossed for consultant: {crossed}")
    passed += 1

    # Test 6: Avatar with no data
    empty = scorer.get_avatar_crs_history("nonexistent_avatar")
    assert empty["sample_count"] == 0
    passed += 1

    # Test 7: Health
    h = scorer.health_check()
    assert h["status"] == "operational"
    assert h["scores_recorded"] >= 5
    print(f"Health: {h['status']} scores={h['scores_recorded']}")
    passed += 1

    print(f"\nPASS: crs_scorer ({passed} assertions)")
