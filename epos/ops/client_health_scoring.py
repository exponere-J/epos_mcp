#!/usr/bin/env python3
# EPOS Artifact — BUILD 102 (Client Health Scoring)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""
client_health_scoring.py — Weekly client-health score + churn flagging

Computes a 0–100 health score per client based on:
  - recency_score:      how recently last touchpoint (40%)
  - stage_velocity:     are they progressing vs SLA (25%)
  - engagement_score:   volume of touchpoints vs baseline (20%)
  - sentiment_score:    derived from touchpoint notes (15%)

Stored at: context_vault/clients/<id>_health.json (append-only history
of scores, so the Reward Bus sees trend, not just current state).

Emits 'client.health.scored' and 'client.health.at_risk' when score
drops below 40 with a > 15-point 7-day decline.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
CLIENTS_DIR = Path(os.getenv("EPOS_CLIENTS_DIR", str(REPO / "context_vault" / "clients")))

# Simple sentiment lexicon — lightweight, no external deps
POSITIVE_TERMS = (
    "great", "love", "excited", "ready", "signed", "yes", "thank", "perfect", "helpful",
    "clear", "aligned", "committed", "paid", "renewed", "referral",
)
NEGATIVE_TERMS = (
    "concern", "objection", "pushback", "expensive", "not now", "delay", "cancel",
    "ghost", "silent", "complaint", "unhappy", "wrong", "broken", "disappointed", "refund",
)

RECENCY_BUCKETS_DAYS = [(3, 100), (7, 85), (14, 70), (21, 55), (30, 40), (45, 25), (60, 10)]


@dataclass
class HealthScore:
    client_id: str
    scored_at: str
    score: float
    recency_score: float
    stage_velocity: float
    engagement_score: float
    sentiment_score: float
    decline_7d: float
    at_risk: bool


class ClientHealthScorer:
    def __init__(self) -> None:
        CLIENTS_DIR.mkdir(parents=True, exist_ok=True)

    def _recency_score(self, last_tp: str) -> float:
        if not last_tp:
            return 0.0
        try:
            dt = datetime.fromisoformat(last_tp.replace("Z", "+00:00"))
        except Exception:
            return 0.0
        days = (datetime.now(timezone.utc) - dt).days
        for threshold, score in RECENCY_BUCKETS_DAYS:
            if days <= threshold:
                return float(score)
        return 0.0

    def _stage_velocity(self, client: dict) -> float:
        # Clients in RETAINED stage get 100; stalled ones get scaled by overrun.
        stage = client.get("stage", "LEAD")
        if stage == "RETAINED":
            return 100.0
        if stage in ("CHURNED", "LAPSED"):
            return 0.0
        entered = client.get("entered_stage_at", "")
        if not entered:
            return 60.0
        try:
            dt = datetime.fromisoformat(entered.replace("Z", "+00:00"))
        except Exception:
            return 60.0
        days = (datetime.now(timezone.utc) - dt).days
        # Generic SLA: 14 days. Overrun → proportional decay.
        if days <= 14:
            return 100.0
        overrun = days - 14
        return max(0.0, 100.0 - overrun * 3.0)

    def _engagement_score(self, client: dict) -> float:
        hist = client.get("touchpoint_history", [])
        if not hist:
            return 0.0
        # Touchpoints in the last 30 days
        cutoff = datetime.now(timezone.utc).timestamp() - 30 * 86400
        recent = 0
        for tp in hist:
            try:
                ts = datetime.fromisoformat(tp.get("timestamp", "").replace("Z", "+00:00")).timestamp()
                if ts >= cutoff:
                    recent += 1
            except Exception:
                pass
        # 4+ touchpoints/30d = 100; 1 = 25; 0 = 0
        return min(100.0, recent * 25.0)

    def _sentiment_score(self, client: dict) -> float:
        notes_blob = " ".join(
            [tp.get("note", "") for tp in client.get("touchpoint_history", [])[-10:]]
            + list(client.get("notes", []))[-10:]
        ).lower()
        if not notes_blob.strip():
            return 60.0  # neutral default
        pos = sum(1 for t in POSITIVE_TERMS if re.search(rf"\b{t}\b", notes_blob))
        neg = sum(1 for t in NEGATIVE_TERMS if re.search(rf"\b{t}\b", notes_blob))
        if pos + neg == 0:
            return 60.0
        return 50.0 + (pos - neg) * 10.0  # bounded below by clamp
        # Note: allowed to exceed 100 or go < 0; clamped in score()

    def score(self, client_id: str) -> HealthScore:
        p = CLIENTS_DIR / f"{client_id}.json"
        if not p.exists():
            raise FileNotFoundError(f"no client state for {client_id}")
        client = json.loads(p.read_text())

        recency = self._recency_score(client.get("last_touchpoint_at", ""))
        velocity = self._stage_velocity(client)
        engagement = self._engagement_score(client)
        sentiment = max(0.0, min(100.0, self._sentiment_score(client)))

        composite = (0.40 * recency + 0.25 * velocity
                     + 0.20 * engagement + 0.15 * sentiment)
        composite = max(0.0, min(100.0, composite))

        # Load 7-day-ago score if available for decline calc
        hist_p = CLIENTS_DIR / f"{client_id}_health.jsonl"
        decline_7d = 0.0
        if hist_p.exists():
            cutoff = datetime.now(timezone.utc).timestamp() - 7 * 86400
            prior = None
            for line in hist_p.read_text().splitlines():
                try:
                    rec = json.loads(line)
                    ts = datetime.fromisoformat(rec["scored_at"].replace("Z", "+00:00")).timestamp()
                    if ts <= cutoff:
                        prior = rec["score"]
                except Exception:
                    pass
            if prior is not None:
                decline_7d = float(prior) - composite

        at_risk = composite < 40.0 and decline_7d > 15.0

        result = HealthScore(
            client_id=client_id,
            scored_at=datetime.now(timezone.utc).isoformat(),
            score=round(composite, 2),
            recency_score=round(recency, 2),
            stage_velocity=round(velocity, 2),
            engagement_score=round(engagement, 2),
            sentiment_score=round(sentiment, 2),
            decline_7d=round(decline_7d, 2),
            at_risk=at_risk,
        )

        # Append to history
        with hist_p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(result)) + "\n")

        try:
            from epos_event_bus import EPOSEventBus
            bus = EPOSEventBus()
            bus.publish("client.health.scored", asdict(result), source_module="client_health_scoring")
            if at_risk:
                bus.publish("client.health.at_risk", asdict(result), source_module="client_health_scoring")
        except Exception:
            pass

        return result


def score_all() -> list[dict[str, Any]]:
    scorer = ClientHealthScorer()
    out = []
    for p in sorted(CLIENTS_DIR.glob("*.json")):
        if p.name.endswith("_health.jsonl") or p.name.endswith("_health.json"):
            continue
        cid = p.stem
        try:
            out.append(asdict(scorer.score(cid)))
        except Exception as e:
            out.append({"client_id": cid, "error": f"{type(e).__name__}: {e}"})
    return out


if __name__ == "__main__":
    print(json.dumps(score_all(), indent=2))
