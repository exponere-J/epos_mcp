#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
echolocation_predictor.py — Resonance Predictor (Pre-Publication)
====================================================================
Constitutional Authority: EPOS Constitution v3.1 — Echolocation Subsystem

Companion to the post-publication resonance scorer. Predicts a topic-avatar-
format-angle combination's likely resonance BEFORE publication based on
accumulated echo history.

Cold start (no history) produces a heuristic baseline with LOW confidence.
As echo data accumulates, confidence rises and the model becomes the
authoritative content production filter.

Core operations:
  - predict_resonance(topic, avatar_id, format, angle) -> prediction dict
  - record_outcome(prediction_id, actual_score) -> learning loop
  - suggest_next_topics(avatar_id, count) -> highest-predicted topic queue
  - health_check() -> sovereign health surface

The learning loop:
  R1 signal -> predict -> A1 brief -> publish -> AN1 score -> record_outcome
  -> delta feeds the heuristic -> next prediction is sharper.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
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
ECHOES_ROOT = VAULT / "echoes"
ECHOES_ROOT.mkdir(parents=True, exist_ok=True)
HISTORY_LOG = ECHOES_ROOT / "echolocation_history.jsonl"
PREDICTIONS_LOG = ECHOES_ROOT / "predictions.jsonl"

# Baseline heuristics for cold start
BASELINE_SCORE = 62.0
MIN_CONFIDENCE_SAMPLES = 30
TARGET_ACCURACY_SAMPLES = 100

# Angle baseline affinities per avatar (editable as data accumulates)
ANGLE_BASELINES = {
    "challenger": 68,
    "architect": 72,
    "closer": 65,
}

# Format baseline affinities
FORMAT_BASELINES = {
    "long_form_article": 70,
    "short_form_video": 68,
    "linkedin_post": 74,
    "x_thread": 66,
    "email": 72,
    "newsletter": 71,
    "carousel": 67,
}


class EcholocationPredictor:
    """Predicts content resonance before publication."""

    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = Path(history_path) if history_path else HISTORY_LOG
        self._model: Optional[dict] = None
        self._loaded_at: Optional[str] = None

    # ── Model Loading ─────────────────────────────────────────────

    def _load_model(self) -> dict:
        """
        Build the in-memory model from echolocation_history.jsonl.

        Model structure:
        {
          "per_avatar": {
             avatar_id: {
                "count": n,
                "mean_score": float,
                "best_angle": str,
                "best_format": str,
                "angle_scores": {angle: [scores]},
                "format_scores": {format: [scores]},
                "topic_clusters": {cluster_key: [scores]},
             }
          },
          "global": {
             "count": n,
             "mean_score": float,
          }
        }
        """
        per_avatar: dict[str, dict] = {}
        global_scores: list[float] = []

        if self.history_path.exists():
            with open(self.history_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    score = rec.get("actual_score")
                    if score is None:
                        continue
                    avatar_id = rec.get("avatar_id", "unknown")
                    angle = rec.get("angle", "architect")
                    fmt = rec.get("format", "linkedin_post")
                    topic = rec.get("topic", "")

                    global_scores.append(float(score))

                    avatar_bucket = per_avatar.setdefault(avatar_id, {
                        "count": 0,
                        "scores": [],
                        "angle_scores": {},
                        "format_scores": {},
                        "topic_clusters": {},
                    })
                    avatar_bucket["count"] += 1
                    avatar_bucket["scores"].append(float(score))
                    avatar_bucket["angle_scores"].setdefault(angle, []).append(float(score))
                    avatar_bucket["format_scores"].setdefault(fmt, []).append(float(score))
                    cluster = self._topic_cluster_key(topic)
                    avatar_bucket["topic_clusters"].setdefault(cluster, []).append(float(score))

        # Compute derived stats
        for aid, bucket in per_avatar.items():
            scores = bucket["scores"]
            bucket["mean_score"] = round(sum(scores) / len(scores), 2) if scores else BASELINE_SCORE
            # Best angle
            best_angle, best_mean = None, -1.0
            for angle, ss in bucket["angle_scores"].items():
                m = sum(ss) / len(ss)
                if m > best_mean:
                    best_mean, best_angle = m, angle
            bucket["best_angle"] = best_angle
            # Best format
            best_format, best_fm = None, -1.0
            for fmt, ss in bucket["format_scores"].items():
                m = sum(ss) / len(ss)
                if m > best_fm:
                    best_fm, best_format = m, fmt
            bucket["best_format"] = best_format

        model = {
            "per_avatar": per_avatar,
            "global": {
                "count": len(global_scores),
                "mean_score": round(sum(global_scores) / len(global_scores), 2) if global_scores else BASELINE_SCORE,
            },
            "built_at": datetime.now(timezone.utc).isoformat(),
        }
        self._model = model
        self._loaded_at = model["built_at"]
        return model

    def _model_ready(self) -> dict:
        if self._model is None:
            return self._load_model()
        return self._model

    # ── Prediction ────────────────────────────────────────────────

    def predict_resonance(self, topic: str, avatar_id: str,
                          format: str = "linkedin_post",
                          angle: str = "architect") -> dict:
        """Predict resonance for a topic-avatar-format-angle combo."""
        model = self._model_ready()
        avatar_bucket = model["per_avatar"].get(avatar_id, {})
        samples = avatar_bucket.get("count", 0)

        # Cold start: blend baselines
        angle_base = ANGLE_BASELINES.get(angle, 68)
        format_base = FORMAT_BASELINES.get(format, 70)

        if samples == 0:
            predicted = round((BASELINE_SCORE + angle_base + format_base) / 3.0, 1)
            confidence = 0.15
            comparable = []
            recommendation = (
                f"Cold start — baseline estimate using global priors. "
                f"Publish, measure, and the next prediction for this avatar sharpens."
            )
        else:
            avatar_mean = avatar_bucket.get("mean_score", BASELINE_SCORE)

            # Pull angle-specific mean if present
            angle_scores = avatar_bucket.get("angle_scores", {}).get(angle, [])
            angle_mean = (sum(angle_scores) / len(angle_scores)) if angle_scores else angle_base

            # Pull format-specific mean if present
            format_scores = avatar_bucket.get("format_scores", {}).get(format, [])
            format_mean = (sum(format_scores) / len(format_scores)) if format_scores else format_base

            # Topic-cluster mean
            cluster = self._topic_cluster_key(topic)
            topic_scores = avatar_bucket.get("topic_clusters", {}).get(cluster, [])
            topic_mean = (sum(topic_scores) / len(topic_scores)) if topic_scores else avatar_mean

            # Weighted blend
            predicted = round(
                (avatar_mean * 0.25 +
                 angle_mean * 0.25 +
                 format_mean * 0.25 +
                 topic_mean * 0.25), 1
            )

            confidence = min(0.95, samples / TARGET_ACCURACY_SAMPLES)

            # Recommendation
            best_angle = avatar_bucket.get("best_angle")
            if best_angle and best_angle != angle:
                best_angle_mean = sum(avatar_bucket["angle_scores"][best_angle]) / len(avatar_bucket["angle_scores"][best_angle])
                delta = round(best_angle_mean - angle_mean, 1)
                if delta > 3:
                    recommendation = (
                        f"Shift to {best_angle} angle — scored {delta} points higher than "
                        f"{angle} for this avatar."
                    )
                else:
                    recommendation = f"Angle {angle} is within 3 points of the best performer."
            else:
                recommendation = f"Angle {angle} is optimal for this avatar based on history."

            comparable = self._top_comparables(avatar_id, cluster, n=3)

        # Optimization suggestions (heuristic based on avatar config)
        suggestions = self._suggest_optimizations(avatar_id, topic, format, angle)

        prediction_id = self._mint_prediction_id(topic, avatar_id, format, angle)
        result = {
            "prediction_id": prediction_id,
            "predicted_score": predicted,
            "confidence": round(confidence, 2),
            "samples_for_avatar": samples,
            "topic": topic,
            "avatar_id": avatar_id,
            "format": format,
            "angle": angle,
            "recommendation": recommendation,
            "optimization_suggestions": suggestions,
            "comparable_pieces": comparable,
            "predicted_at": datetime.now(timezone.utc).isoformat(),
        }

        self._log_prediction(result)

        if _BUS:
            try:
                _BUS.publish("content.eri.predicted", {
                    "prediction_id": prediction_id,
                    "avatar_id": avatar_id,
                    "predicted_score": predicted,
                    "confidence": round(confidence, 2),
                }, source_module="echolocation_predictor")
            except Exception:
                pass

        return result

    def _suggest_optimizations(self, avatar_id: str, topic: str,
                               format: str, angle: str) -> list[str]:
        """Generate avatar-aware optimization suggestions."""
        suggestions: list[str] = []
        try:
            from nodes.avatar_registry import get_registry
            avatar = get_registry().get_avatar(avatar_id) or {}
        except Exception:
            avatar = {}

        comm = avatar.get("communication_preferences", {}) or {}
        proof_type = comm.get("proof_type", "")
        vocab = comm.get("vocabulary", "")
        length = comm.get("length", "")

        if "dollar" in proof_type.lower() or "number" in proof_type.lower():
            suggestions.append("Lead with a dollar amount — this avatar responds to financial framing.")
        if "before/after" in proof_type.lower() or "photo" in proof_type.lower():
            suggestions.append("Include a before/after or visual comparison — this avatar's top performers all had them.")
        if "case stud" in proof_type.lower():
            suggestions.append("Embed a named case study with quantified outcomes.")
        if "screenshot" in proof_type.lower():
            suggestions.append("Attach a screenshot as proof — raw evidence beats explanation.")
        if "short" in length.lower() or "60" in length or "150" in length:
            suggestions.append("Keep it tight — this avatar's dwell time drops fast on long content.")
        if "medium" in length.lower():
            suggestions.append("Aim for medium length — 300-600 words resonates best here.")
        if vocab:
            suggestions.append(f"Use vocabulary the avatar recognizes: {vocab[:80]}")

        if not suggestions:
            suggestions.append("No specific optimizations available — rely on angle/format baseline.")
        return suggestions

    def _top_comparables(self, avatar_id: str, cluster: str, n: int = 3) -> list[dict]:
        """Return top comparable published pieces."""
        if not self.history_path.exists():
            return []
        matches = []
        with open(self.history_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("avatar_id") == avatar_id and rec.get("actual_score"):
                    matches.append(rec)
        matches.sort(key=lambda r: r.get("actual_score", 0), reverse=True)
        return [
            {
                "topic": m.get("topic", ""),
                "avatar": m.get("avatar_id"),
                "score": m.get("actual_score"),
            }
            for m in matches[:n]
        ]

    # ── Learning Loop ─────────────────────────────────────────────

    def record_outcome(self, prediction_id: str, actual_score: float,
                       topic: Optional[str] = None, avatar_id: Optional[str] = None,
                       angle: Optional[str] = None, format: Optional[str] = None) -> dict:
        """Append a training record after publication. Invalidates cached model."""
        # If caller didn't provide topic/avatar, try to recover from predictions log
        recovered = self._lookup_prediction(prediction_id) if prediction_id else None
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_id": prediction_id,
            "topic": topic or (recovered.get("topic") if recovered else None),
            "avatar_id": avatar_id or (recovered.get("avatar_id") if recovered else None),
            "angle": angle or (recovered.get("angle") if recovered else None),
            "format": format or (recovered.get("format") if recovered else None),
            "actual_score": float(actual_score),
            "predicted_score": recovered.get("predicted_score") if recovered else None,
            "delta": round(float(actual_score) - float(recovered.get("predicted_score", actual_score)), 2) if recovered else 0,
        }
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        # Invalidate model cache
        self._model = None

        if _BUS:
            try:
                _BUS.publish("content.eri.recorded", {
                    "prediction_id": prediction_id,
                    "actual_score": actual_score,
                    "delta": record["delta"],
                }, source_module="echolocation_predictor")
            except Exception:
                pass

        return record

    def _lookup_prediction(self, prediction_id: str) -> Optional[dict]:
        if not PREDICTIONS_LOG.exists():
            return None
        with open(PREDICTIONS_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("prediction_id") == prediction_id:
                    return rec
        return None

    # ── Topic Suggestion ──────────────────────────────────────────

    def suggest_next_topics(self, avatar_id: str, count: int = 5) -> list[dict]:
        """Suggest highest-predicted topics for an avatar."""
        model = self._model_ready()
        avatar_bucket = model["per_avatar"].get(avatar_id, {})

        # Seed topics: pull pain points + signal keywords from avatar
        try:
            from nodes.avatar_registry import get_registry
            avatar = get_registry().get_avatar(avatar_id) or {}
        except Exception:
            avatar = {}

        candidates: list[dict] = []
        pains = avatar.get("pain_points", [])
        for p in pains[:count * 2]:
            topic = p.get("pain", "")
            if not topic:
                continue
            pred = self.predict_resonance(
                topic=topic,
                avatar_id=avatar_id,
                format=avatar.get("communication_preferences", {}).get("format", ["linkedin_post"])[0] if avatar.get("communication_preferences", {}).get("format") else "linkedin_post",
                angle=avatar_bucket.get("best_angle") or "architect",
            )
            candidates.append({
                "topic": topic,
                "predicted_score": pred["predicted_score"],
                "severity": p.get("severity", 5),
            })

        candidates.sort(key=lambda c: (c["predicted_score"], c["severity"]), reverse=True)
        return candidates[:count]

    # ── Health ────────────────────────────────────────────────────

    def health_check(self) -> dict:
        try:
            model = self._model_ready()
            return {
                "node": "echolocation_predictor",
                "status": "operational",
                "samples": model["global"]["count"],
                "avatars_tracked": len(model["per_avatar"]),
                "confidence": "cold_start" if model["global"]["count"] < MIN_CONFIDENCE_SAMPLES else "warming",
                "target_samples_for_70pct_accuracy": TARGET_ACCURACY_SAMPLES,
                "history_path": str(self.history_path),
                "loaded_at": self._loaded_at,
            }
        except Exception as e:
            return {"node": "echolocation_predictor", "status": "error", "error": str(e)[:200]}

    # ── Internals ─────────────────────────────────────────────────

    @staticmethod
    def _topic_cluster_key(topic: str) -> str:
        """Quick topic clustering via keyword stems."""
        words = [w.lower() for w in (topic or "").split() if len(w) > 3]
        words.sort()
        key = "-".join(words[:4]) or "uncategorized"
        return key[:80]

    @staticmethod
    def _mint_prediction_id(topic: str, avatar_id: str, fmt: str, angle: str) -> str:
        raw = f"{topic}|{avatar_id}|{fmt}|{angle}|{datetime.now(timezone.utc).timestamp()}"
        return "PRED-" + hashlib.sha1(raw.encode()).hexdigest()[:12]

    def _log_prediction(self, prediction: dict):
        try:
            with open(PREDICTIONS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(prediction) + "\n")
        except Exception:
            pass


# ── Module-level convenience ─────────────────────────────────────

_PREDICTOR: Optional[EcholocationPredictor] = None


def get_predictor() -> EcholocationPredictor:
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = EcholocationPredictor()
    return _PREDICTOR


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    pred = EcholocationPredictor()

    # Test 1: Cold-start prediction
    r = pred.predict_resonance(
        topic="How to automate lead follow-up for service businesses",
        avatar_id="local_champion",
        format="email",
        angle="challenger",
    )
    assert "predicted_score" in r
    assert 0 < r["predicted_score"] < 100
    assert r["confidence"] < 0.5
    print(f"Cold-start prediction: {r['predicted_score']} (confidence {r['confidence']})")
    print(f"  Suggestions: {len(r['optimization_suggestions'])}")
    passed += 1

    # Test 2: Record outcome -> learning loop
    outcome = pred.record_outcome(
        prediction_id=r["prediction_id"],
        actual_score=82,
    )
    assert outcome["actual_score"] == 82
    print(f"Recorded outcome: delta={outcome['delta']}")
    passed += 1

    # Test 3: Second prediction for same avatar uses the recorded sample
    r2 = pred.predict_resonance(
        topic="Lead follow-up automation for local service",
        avatar_id="local_champion",
        format="email",
        angle="challenger",
    )
    assert r2["samples_for_avatar"] >= 1
    print(f"Warmed prediction: {r2['predicted_score']} samples={r2['samples_for_avatar']}")
    passed += 1

    # Test 4: Suggest next topics
    suggestions = pred.suggest_next_topics("local_champion", count=3)
    assert len(suggestions) > 0
    print(f"Top topic suggestions for local_champion:")
    for s in suggestions:
        print(f"  {s['predicted_score']:5.1f}  {s['topic'][:60]}")
    passed += 1

    # Test 5: Health check
    h = pred.health_check()
    assert h["status"] == "operational"
    print(f"Health: {h['status']} samples={h['samples']} confidence={h['confidence']}")
    passed += 1

    # Test 6: Prediction for a different avatar
    r3 = pred.predict_resonance(
        topic="Sovereign AI operating system for technical founders",
        avatar_id="technical_founder_operator",
        format="long_form_article",
        angle="architect",
    )
    assert r3["avatar_id"] == "technical_founder_operator"
    print(f"Tech founder prediction: {r3['predicted_score']}")
    passed += 1

    print(f"\nPASS: echolocation_predictor ({passed} assertions)")
