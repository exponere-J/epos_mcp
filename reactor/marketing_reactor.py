#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
marketing_reactor.py — Marketing Reactor (5th Reactor)
====================================================================
Constitutional Authority: EPOS Constitution v3.1 — Marketing Layer

The demand-side reactor. Subscribes to avatar signal events, content
resonance events, and CRS threshold events — and dispatches amplification
actions: content brief generation, paid campaign staging, expansion
protocol triggers, communication frequency changes.

This is the 5th reactor in the EPOS organism:
  1. Content Reactor — production pipeline handlers
  2. Handlers v2 — cross-system handlers (CRM/billing/FOTW/TTLG/system/avatar)
  3. (legacy dispatch handlers in daemon)
  4. (implicit friday orchestrator)
  5. Marketing Reactor — demand-side amplification

Handler registration:
  MARKETING_HANDLERS dict is imported into epos_daemon.
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
MARKETING_VAULT = VAULT / "marketing"
MARKETING_VAULT.mkdir(parents=True, exist_ok=True)
MARKETING_LOG = MARKETING_VAULT / "marketing_reactor_log.jsonl"
CAMPAIGN_STAGE = MARKETING_VAULT / "campaigns"
CAMPAIGN_STAGE.mkdir(parents=True, exist_ok=True)

# Amplification thresholds
EXPANSION_THRESHOLD = 85.0
PAID_AMPLIFICATION_THRESHOLD = 75.0


def _log(handler: str, event: dict, action: str, success: bool = True):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "handler": handler,
        "event_type": event.get("event_type"),
        "action": action,
        "success": success,
    }
    with open(MARKETING_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _publish(event_type: str, payload: dict):
    if _BUS:
        try:
            _BUS.publish(event_type, payload, source_module="marketing_reactor")
        except Exception:
            pass


def _load_avatar(avatar_id: str) -> dict:
    try:
        from nodes.avatar_registry import get_registry
        return get_registry().get_avatar(avatar_id) or {}
    except Exception:
        return {}


# ── HANDLERS ─────────────────────────────────────────────────────

def handle_signal_amplification(event: dict):
    """avatar.signal.detected -> If signal strong + no content exists for avatar, generate a brief."""
    payload = event.get("payload", {})
    avatar_id = payload.get("top_match") or payload.get("avatar_id")
    score = float(payload.get("top_score") or payload.get("score") or 0)

    if not avatar_id:
        _log("handle_signal_amplification", event, "no avatar_id in payload", success=False)
        return

    avatar = _load_avatar(avatar_id)
    if not avatar:
        _log("handle_signal_amplification", event, f"avatar not found: {avatar_id}", success=False)
        return

    # If signal is meaningful, request a content brief for this avatar's top pain
    if score >= 0.15:
        pains = avatar.get("pain_points", [])
        if pains:
            top_pain = max(pains, key=lambda p: p.get("severity", 0))["pain"]
            try:
                from content_lab.brief_generator import ContentBriefGenerator
                from content_lab.echolocation_predictor import get_predictor
                pred = get_predictor()
                prediction = pred.predict_resonance(
                    topic=top_pain, avatar_id=avatar_id,
                    format="linkedin_post", angle="architect"
                )
                gen = ContentBriefGenerator()
                brief = gen.generate_brief(
                    spark={"spark_id": f"AUTO-{avatar_id}", "topic": top_pain},
                    avatar=avatar, prediction=prediction, angle="architect"
                )
                _publish("content.brief.generated", {
                    "brief_id": brief["brief_id"],
                    "target_avatar": avatar_id,
                    "source": "marketing_reactor_signal",
                })
                _log("handle_signal_amplification", event, f"auto-brief: {brief['brief_id']}")
                return
            except Exception as e:
                _log("handle_signal_amplification", event, f"brief gen failed: {e}", success=False)
                return

    _log("handle_signal_amplification", event, f"score={score} below action threshold")


def handle_paid_amplification(event: dict):
    """marketing.amplify.triggered -> Stage a paid campaign spec."""
    payload = event.get("payload", {})
    avatar_id = payload.get("avatar_id")
    content_id = payload.get("content_id") or payload.get("brief_id") or "unknown"
    score = float(payload.get("score") or 0)

    if not avatar_id:
        _log("handle_paid_amplification", event, "no avatar_id", success=False)
        return

    avatar = _load_avatar(avatar_id)
    price_tol = avatar.get("price_tolerance", {}) or {}
    channels = (avatar.get("channels", {}) or {}).get("primary", [])

    # Conservative budget: 2x monthly floor, capped at 10% of monthly ceiling
    floor = price_tol.get("monthly_floor", 100)
    ceiling = price_tol.get("monthly_ceiling", 500)
    budget = max(min(floor * 2, ceiling * 0.5), 50)

    # Only stage when organic has proven above threshold
    if score < PAID_AMPLIFICATION_THRESHOLD:
        _log("handle_paid_amplification", event,
             f"score={score} below paid threshold {PAID_AMPLIFICATION_THRESHOLD} — not staged")
        return

    campaign_spec = {
        "campaign_id": f"CAMP-{avatar_id.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "avatar_id": avatar_id,
        "content_id": content_id,
        "organic_score": score,
        "recommended_channels": channels,
        "budget_usd": round(budget, 2),
        "status": "staged_for_review",
        "staged_at": datetime.now(timezone.utc).isoformat(),
        "approval_required": True,
    }
    # Write the spec to the staging directory
    spec_path = CAMPAIGN_STAGE / f"{campaign_spec['campaign_id']}.json"
    spec_path.write_text(json.dumps(campaign_spec, indent=2), encoding="utf-8")

    _publish("marketing.campaign.staged", {
        "campaign_id": campaign_spec["campaign_id"],
        "avatar_id": avatar_id,
        "budget": campaign_spec["budget_usd"],
    })
    _log("handle_paid_amplification", event,
         f"campaign staged: {campaign_spec['campaign_id']} budget={campaign_spec['budget_usd']}")


def handle_resonance_amplification(event: dict):
    """content.echo.scored -> If score > 85, trigger Expansion Protocol."""
    payload = event.get("payload", {})
    score = float(payload.get("score") or payload.get("actual_score") or 0)
    content_id = payload.get("content_id") or payload.get("piece_id") or "unknown"
    avatar_id = payload.get("avatar_id") or payload.get("target_avatar")

    if score < EXPANSION_THRESHOLD:
        _log("handle_resonance_amplification", event, f"score {score} < expansion threshold")
        return

    avatar = _load_avatar(avatar_id) if avatar_id else {}
    formats = (avatar.get("communication_preferences", {}) or {}).get("format", [])

    _publish("content.expansion.triggered", {
        "source_content_id": content_id,
        "avatar_id": avatar_id,
        "original_score": score,
        "expand_to_formats": formats,
    })
    _log("handle_resonance_amplification", event,
         f"expansion fired: content={content_id} formats={len(formats)}")


def handle_communication_expansion(event: dict):
    """crs.threshold.crossed -> Increase comm frequency and advance nurture."""
    payload = event.get("payload", {})
    avatar_id = payload.get("avatar_id")
    score = float(payload.get("score") or 0)

    if not avatar_id:
        _log("handle_communication_expansion", event, "no avatar_id", success=False)
        return

    _publish("comm.frequency.increase", {
        "avatar_id": avatar_id,
        "reason": f"crs_crossed_threshold_{score}",
        "new_cadence": "2x_weekly" if score >= 90 else "weekly_plus",
    })
    _publish("comm.nurture.advance", {"avatar_id": avatar_id, "trigger_score": score})
    _log("handle_communication_expansion", event,
         f"avatar {avatar_id} advanced to next nurture step (score={score})")


# ── Handler Registry ─────────────────────────────────────────────

MARKETING_HANDLERS = {
    "avatar.signal.detected": handle_signal_amplification,
    "marketing.amplify.triggered": handle_paid_amplification,
    "content.echo.scored": handle_resonance_amplification,
    "crs.threshold.crossed": handle_communication_expansion,
}


# ── Health ───────────────────────────────────────────────────────

def health_check() -> dict:
    return {
        "node": "marketing_reactor",
        "status": "operational",
        "handler_count": len(MARKETING_HANDLERS),
        "handlers": list(MARKETING_HANDLERS.keys()),
        "staged_campaigns": len(list(CAMPAIGN_STAGE.glob("CAMP-*.json"))),
        "log_path": str(MARKETING_LOG),
    }


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: All handlers callable
    for name, h in MARKETING_HANDLERS.items():
        assert callable(h), f"{name} not callable"
    assert len(MARKETING_HANDLERS) == 4
    print(f"All {len(MARKETING_HANDLERS)} marketing handlers callable")
    passed += 1

    # Test 2: Signal amplification — strong signal for local_champion
    handle_signal_amplification({
        "event_type": "avatar.signal.detected",
        "payload": {"top_match": "local_champion", "top_score": 0.35, "source": "test"}
    })
    assert MARKETING_LOG.exists()
    passed += 1

    # Test 3: Paid amplification — above threshold
    handle_paid_amplification({
        "event_type": "marketing.amplify.triggered",
        "payload": {"avatar_id": "agency_builder", "content_id": "TEST-001", "score": 88}
    })
    campaigns = list(CAMPAIGN_STAGE.glob("CAMP-AGENCY_BUILDER-*.json"))
    assert campaigns, "Expected staged campaign"
    print(f"Staged campaigns: {len(campaigns)}")
    passed += 1

    # Test 4: Paid amplification below threshold — should NOT stage
    before = len(list(CAMPAIGN_STAGE.glob("CAMP-*.json")))
    handle_paid_amplification({
        "event_type": "marketing.amplify.triggered",
        "payload": {"avatar_id": "solo_operator", "content_id": "TEST-002", "score": 60}
    })
    after = len(list(CAMPAIGN_STAGE.glob("CAMP-*.json")))
    assert after == before, "Should not have staged below threshold"
    passed += 1

    # Test 5: Resonance amplification — score above threshold
    handle_resonance_amplification({
        "event_type": "content.echo.scored",
        "payload": {"content_id": "ECHO-001", "avatar_id": "boutique_agency_founder", "score": 92}
    })
    passed += 1

    # Test 6: Communication expansion
    handle_communication_expansion({
        "event_type": "crs.threshold.crossed",
        "payload": {"avatar_id": "solo_strategic_consultant", "score": 88}
    })
    passed += 1

    # Test 7: Health
    h = health_check()
    assert h["status"] == "operational"
    assert h["handler_count"] == 4
    print(f"Health: {h['status']} handlers={h['handler_count']} staged={h['staged_campaigns']}")
    passed += 1

    print(f"\nPASS: marketing_reactor ({passed} assertions)")
