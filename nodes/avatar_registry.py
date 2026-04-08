#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
avatar_registry.py — EPOS 12-Avatar Signal Architecture Registry
====================================================================
Constitutional Authority: EPOS Constitution v3.1 — 12-Avatar Signal Architecture

Sovereign node that loads avatar JSON profiles from context_vault/avatars/
and provides signal-based lookup, scoring, and routing.

Consumed by:
  - Lead Scoring (avatar_match contributes to lead score)
  - Content Reactor (avatar-aware content angle selection)
  - Consumer Journey (per-avatar conversion path routing)
  - Marketing Reactor (planned — avatar-targeted amplification)

Core operations:
  - load_avatars(tier=None)
  - match_signal(text, tier=None) -> ranked list of avatar matches
  - get_avatar(avatar_id)
  - score_lead_against_avatars(lead_payload)
  - health_check()
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from path_utils import get_context_vault

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

VAULT = get_context_vault()
AVATARS_ROOT = VAULT / "avatars"
AVATAR_LOG = AVATARS_ROOT / "events.jsonl"


class AvatarRegistry:
    """Sovereign registry for the 12-Avatar Signal Architecture."""

    def __init__(self, vault_path: Optional[Path] = None):
        self.root = Path(vault_path) if vault_path else AVATARS_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict] = {}
        self._loaded_at: Optional[str] = None

    # ── Loading ──────────────────────────────────────────────────

    def load_avatars(self, tier: Optional[int] = None, force: bool = False) -> dict[str, dict]:
        """Load all avatar JSON files. Optionally filter by tier."""
        if self._cache and not force:
            if tier is None:
                return dict(self._cache)
            return {k: v for k, v in self._cache.items() if v.get("tier") == tier}

        avatars: dict[str, dict] = {}
        for tier_dir in sorted(self.root.glob("tier*")):
            if not tier_dir.is_dir():
                continue
            for f in sorted(tier_dir.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    aid = data.get("avatar_id")
                    if aid:
                        avatars[aid] = data
                except Exception as e:
                    print(f"WARN: Could not load {f.name}: {e}")

        self._cache = avatars
        self._loaded_at = datetime.now(timezone.utc).isoformat()

        if tier is None:
            return dict(avatars)
        return {k: v for k, v in avatars.items() if v.get("tier") == tier}

    def get_avatar(self, avatar_id: str) -> Optional[dict]:
        if not self._cache:
            self.load_avatars()
        return self._cache.get(avatar_id)

    def list_ids(self, tier: Optional[int] = None) -> list[str]:
        return list(self.load_avatars(tier=tier).keys())

    def list_avatars(self, tier: Optional[int] = None) -> list[dict]:
        """Return list of avatar dicts with 'avatar_id' and 'name' keys exposed."""
        avatars = self.load_avatars(tier=tier)
        out = []
        for aid, a in avatars.items():
            out.append({
                "avatar_id": aid,
                "name": a.get("display_name", aid),
                "tier": a.get("tier"),
                **a,
            })
        return out

    # ── Signal Matching ──────────────────────────────────────────

    def match_signal(self, text: str, tier: Optional[int] = None,
                     min_score: float = 0.0) -> list[dict]:
        """
        Match arbitrary text (post, message, lead form, etc.) against avatar
        signal_keywords / exclusion_keywords. Returns ranked list of matches.
        """
        if not text:
            return []
        text_lower = text.lower()
        avatars = self.load_avatars(tier=tier)
        results = []

        for aid, avatar in avatars.items():
            keywords = avatar.get("signal_keywords", [])
            excludes = avatar.get("exclusion_keywords", [])

            hits = [kw for kw in keywords if kw.lower() in text_lower]
            negatives = [kw for kw in excludes if kw.lower() in text_lower]

            if not hits:
                continue

            # Score: hit ratio minus exclusion penalty
            hit_ratio = len(hits) / max(len(keywords), 1)
            penalty = len(negatives) * 0.15
            score = max(0.0, hit_ratio - penalty)

            if score < min_score:
                continue

            results.append({
                "avatar_id": aid,
                "display_name": avatar.get("display_name"),
                "tier": avatar.get("tier"),
                "score": round(score, 4),
                "hits": hits,
                "negatives": negatives,
            })

        results.sort(key=lambda r: r["score"], reverse=True)

        # Emit event if bus available
        if results and _BUS:
            try:
                _BUS.publish("avatar.signal.detected", {
                    "top_match": results[0]["avatar_id"],
                    "top_score": results[0]["score"],
                    "candidates": len(results),
                    "text_preview": text[:120],
                }, source_module="avatar_registry")
            except Exception:
                pass

        self._log_event("signal_match", {
            "matches": len(results),
            "top": results[0]["avatar_id"] if results else None,
        })

        return results

    def score_lead_against_avatars(self, lead_payload: dict) -> dict:
        """
        Given a lead payload (dict with role, company_size, signals, source, etc.)
        score it against every avatar and return the best fit + per-avatar scores.
        """
        avatars = self.load_avatars()
        scores: dict[str, float] = {}

        # Build a synthetic text blob from the lead payload
        blob_parts = []
        for k in ("role", "title", "company_size", "headline", "bio",
                  "message", "form_response", "source", "industry"):
            v = lead_payload.get(k)
            if v:
                blob_parts.append(str(v))
        # Include any list-of-strings fields
        for k in ("signals", "tags", "interests"):
            v = lead_payload.get(k)
            if isinstance(v, list):
                blob_parts.extend(str(x) for x in v)
        blob = " ".join(blob_parts).lower()

        for aid, avatar in avatars.items():
            score = 0.0

            # Signal keyword hits
            for kw in avatar.get("signal_keywords", []):
                if kw.lower() in blob:
                    score += 1.0

            # Exclusion penalties
            for kw in avatar.get("exclusion_keywords", []):
                if kw.lower() in blob:
                    score -= 1.5

            # Role title match (high signal)
            for title in avatar.get("demographics", {}).get("role_titles", []):
                if title.lower() in blob:
                    score += 3.0

            # Channel match
            source = str(lead_payload.get("source", "")).lower()
            for ch in avatar.get("channels", {}).get("primary", []):
                if ch.lower() in source:
                    score += 2.0
            for ch in avatar.get("channels", {}).get("avoided", []):
                if ch.lower() in source:
                    score -= 2.0

            scores[aid] = round(score, 2)

        # Best match
        if scores:
            best_id = max(scores, key=scores.get)
            best_score = scores[best_id]
        else:
            best_id, best_score = None, 0.0

        result = {
            "best_match": best_id,
            "best_score": best_score,
            "all_scores": scores,
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

        if _BUS and best_id and best_score > 0:
            try:
                _BUS.publish("avatar.lead.scored", {
                    "best_match": best_id,
                    "best_score": best_score,
                    "lead_id": lead_payload.get("lead_id"),
                }, source_module="avatar_registry")
            except Exception:
                pass

        self._log_event("lead_scored", {
            "best_match": best_id,
            "best_score": best_score,
        })

        return result

    # ── Health ───────────────────────────────────────────────────

    def health_check(self) -> dict:
        """Sovereign health surface."""
        try:
            avatars = self.load_avatars()
            tiers = {}
            for a in avatars.values():
                t = a.get("tier", 0)
                tiers[t] = tiers.get(t, 0) + 1
            return {
                "node": "avatar_registry",
                "status": "operational" if avatars else "degraded",
                "avatar_count": len(avatars),
                "tiers": tiers,
                "vault_path": str(self.root),
                "loaded_at": self._loaded_at,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "node": "avatar_registry",
                "status": "error",
                "error": str(e)[:200],
            }

    # ── Internals ────────────────────────────────────────────────

    def _log_event(self, event_type: str, payload: dict):
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "payload": payload,
            }
            with open(AVATAR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass


# ── Module-level convenience ─────────────────────────────────────

_REGISTRY: Optional[AvatarRegistry] = None


def get_registry() -> AvatarRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AvatarRegistry()
    return _REGISTRY


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    reg = AvatarRegistry()

    # Test 1: Load
    avatars = reg.load_avatars()
    assert len(avatars) >= 4, f"Expected >=4 avatars, got {len(avatars)}"
    print(f"Loaded: {len(avatars)} avatars")
    for aid in avatars:
        print(f"  - {aid} (tier {avatars[aid].get('tier')})")
    passed += 1

    # Test 2: Tier filter
    tier1 = reg.load_avatars(tier=1)
    assert len(tier1) >= 4
    passed += 1

    # Test 3: get_avatar
    a = reg.get_avatar("solo_strategic_consultant")
    assert a is not None
    assert a["tier"] == 1
    passed += 1

    # Test 4: Signal matching — consultant text
    matches = reg.match_signal(
        "I am a solo consultant burned out and drowning in delivery work. "
        "Need leverage and a way to productize my expertise."
    )
    assert matches, "Expected matches for consultant text"
    assert matches[0]["avatar_id"] == "solo_strategic_consultant"
    print(f"Signal match top: {matches[0]['avatar_id']} score={matches[0]['score']}")
    passed += 1

    # Test 5: Signal matching — agency text
    matches = reg.match_signal(
        "Our boutique agency is bleeding margin. PMs reinvent the wheel and "
        "a senior just left taking client knowledge. Need delivery standardization."
    )
    assert matches[0]["avatar_id"] == "boutique_agency_founder"
    print(f"Signal match top: {matches[0]['avatar_id']} score={matches[0]['score']}")
    passed += 1

    # Test 6: Lead scoring against payload
    lead = {
        "lead_id": "test-001",
        "role": "Fractional CMO",
        "headline": "Fractional CMO running a portfolio of 5 SaaS clients",
        "source": "LinkedIn",
        "signals": ["context switching", "spread thin"],
    }
    result = reg.score_lead_against_avatars(lead)
    assert result["best_match"] == "fractional_executive"
    print(f"Lead scored: best={result['best_match']} score={result['best_score']}")
    passed += 1

    # Test 7: Technical founder match
    matches = reg.match_signal(
        "Indie hacker tired of saas tax and vendor lock-in. Want a self-hosted "
        "sovereign system. Bring my own ollama and postgres."
    )
    assert matches[0]["avatar_id"] == "technical_founder_operator"
    print(f"Signal match top: {matches[0]['avatar_id']} score={matches[0]['score']}")
    passed += 1

    # Test 8: Health check
    h = reg.health_check()
    assert h["status"] == "operational"
    assert h["avatar_count"] >= 4
    print(f"Health: {h['status']} ({h['avatar_count']} avatars)")
    passed += 1

    print(f"\nPASS: avatar_registry ({passed} assertions)")
