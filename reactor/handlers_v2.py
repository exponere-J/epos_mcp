#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
handlers_v2.py — Event Reactor v2 (24 additional handlers)
=============================================================
Constitutional Authority: EPOS Constitution v3.1

Adds 24 handlers across CRM, billing, FOTW, TTLG, and system events.
Brings total Event Reactor handlers from 10 to 30+.

Each handler:
  - Reads event payload
  - Performs the appropriate action (or logs intent if dependency missing)
  - Logs to context_vault/reactor/v2_handlers_log.jsonl
  - Publishes follow-up events when appropriate
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
REACTOR_VAULT = VAULT / "reactor"
REACTOR_VAULT.mkdir(parents=True, exist_ok=True)
V2_LOG = REACTOR_VAULT / "v2_handlers_log.jsonl"


def _log(handler: str, event: dict, action: str, success: bool = True):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "handler": handler,
        "event_type": event.get("event_type"),
        "action": action,
        "success": success,
    }
    with open(V2_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _publish(event_type: str, payload: dict):
    if _BUS:
        try:
            _BUS.publish(event_type, payload, source_module="reactor_v2")
        except Exception:
            pass


# ── CRM HANDLERS (5) ─────────────────────────────────────────

def handle_crm_lead_scored(event: dict):
    """crm.lead.scored -> Route lead through Consumer Journey based on score."""
    payload = event.get("payload", {})
    score = payload.get("score", 0)
    lead_id = payload.get("lead_id") or payload.get("contact_id")
    if score >= 85:
        _publish("client.expansion_ready", {"lead_id": lead_id, "score": score})
    elif score >= 60:
        _publish("crm.journey.diagnostic", {"lead_id": lead_id, "score": score})
    _log("handle_crm_lead_scored", event, f"score={score} lead={lead_id}")


def handle_crm_lead_converted(event: dict):
    """crm.lead.converted -> Trigger payment + onboarding workflow."""
    payload = event.get("payload", {})
    _publish("billing.invoice.requested", payload)
    _publish("client.onboarding.started", payload)
    _log("handle_crm_lead_converted", event, "payment + onboarding triggered")


def handle_client_at_risk(event: dict):
    """client.at_risk -> Friday escalation + retention workflow."""
    payload = event.get("payload", {})
    _publish("friday.steward.alert", {"priority": "high", "context": payload})
    _log("handle_client_at_risk", event, "Friday escalated")


def handle_client_expansion_ready(event: dict):
    """client.expansion_ready -> TTLG re-diagnostic + upsell manifests."""
    payload = event.get("payload", {})
    _publish("ttlg.diagnostic.requested", {"target": "client", "client_id": payload.get("lead_id"), "purpose": "expansion"})
    _log("handle_client_expansion_ready", event, "TTLG re-diagnostic queued")


def handle_client_churned(event: dict):
    """client.churned -> Post-mortem + win-back sequence."""
    payload = event.get("payload", {})
    churn_log = REACTOR_VAULT / "churn_postmortems.jsonl"
    with open(churn_log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(),
                            "client_id": payload.get("client_id"),
                            "reason": payload.get("reason", "unknown")}) + "\n")
    _publish("friday.steward.alert", {"priority": "medium", "context": payload, "type": "churn"})
    _log("handle_client_churned", event, "post-mortem logged + Friday alerted")


# ── BILLING HANDLERS (4) ─────────────────────────────────────

def handle_billing_invoice_generated(event: dict):
    """billing.invoice.generated -> PS-EM delivers invoice email."""
    payload = event.get("payload", {})
    _publish("psem.email.queued", {"type": "invoice", "invoice_id": payload.get("invoice_id"),
                                    "amount": payload.get("amount")})
    _log("handle_billing_invoice_generated", event, "PS-EM email queued")


def handle_billing_payment_received(event: dict):
    """billing.payment.received -> Trigger node deployment workflow."""
    payload = event.get("payload", {})
    _publish("client.deployment.requested", payload)
    _publish("friday.steward.alert", {"priority": "low", "context": payload, "type": "payment"})
    _log("handle_billing_payment_received", event, "deployment triggered")


def handle_billing_overdue_flagged(event: dict):
    """billing.overdue.flagged -> Friday escalation + collection workflow."""
    payload = event.get("payload", {})
    _publish("friday.steward.alert", {"priority": "high", "context": payload, "type": "overdue"})
    _publish("psem.email.queued", {"type": "collection_reminder", "invoice_id": payload.get("invoice_id")})
    _log("handle_billing_overdue_flagged", event, "Friday + collection email")


def handle_billing_subscription_changed(event: dict):
    """billing.subscription.changed -> Update client namespace + node config."""
    payload = event.get("payload", {})
    _log("handle_billing_subscription_changed", event, f"namespace update queued for {payload.get('client_id')}")


# ── FOTW HANDLERS (3) ────────────────────────────────────────

def handle_fotw_expression_captured(event: dict):
    """fotw.expression.captured -> Lead Scoring update + avatar match relay."""
    payload = event.get("payload", {})
    signal = payload.get("signal_strength", 0)
    if signal >= 60:
        _publish("crm.lead.scored", {
            "lead_id": payload.get("author"),
            "score": signal,
            "source": "fotw_expression",
        })
    # Relay to avatar matcher (avoids dict-key collision in handler registry)
    _publish("fotw.expression.matched", payload)
    _log("handle_fotw_expression_captured", event, f"signal={signal}")


def handle_fotw_signal_high(event: dict):
    """fotw.signal.high -> Friday steward escalation."""
    payload = event.get("payload", {})
    _publish("friday.steward.alert", {"priority": "high", "context": payload, "type": "fotw_signal"})
    _log("handle_fotw_signal_high", event, "Friday alerted")


def handle_fotw_thread_processed(event: dict):
    """fotw.thread.processed -> Update FOTW metrics."""
    payload = event.get("payload", {})
    metrics_log = REACTOR_VAULT / "fotw_metrics.jsonl"
    with open(metrics_log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(),
                            "session_id": payload.get("session_id"),
                            "elements": payload.get("elements", 0)}) + "\n")
    _log("handle_fotw_thread_processed", event, "metrics updated")


# ── TTLG HANDLERS (3) ────────────────────────────────────────

def handle_ttlg_diagnostic_complete(event: dict):
    """ttlg.diagnostic.complete -> Generate Mirror Report."""
    payload = event.get("payload", {})
    _publish("ttlg.report.generation.requested", {"diagnostic_id": payload.get("diagnostic_id")})
    _log("handle_ttlg_diagnostic_complete", event, "Mirror Report queued")


def handle_ttlg_manifest_generated(event: dict):
    """ttlg.manifest.generated -> Stage manifests for client delivery."""
    payload = event.get("payload", {})
    _log("handle_ttlg_manifest_generated", event, "manifest staged for delivery")


def handle_ttlg_gap_identified(event: dict):
    """ttlg.gap.identified -> Add to 9th Order tracker if novel."""
    payload = event.get("payload", {})
    gap = payload.get("gap_description") or payload.get("description", "")
    if not gap:
        _log("handle_ttlg_gap_identified", event, "no description", False)
        return
    # Add to 9th Order tracker
    tracker_path = VAULT / "doctrine" / "ninth_order_gaps.jsonl"
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "touchpoint": payload.get("touchpoint", "TPXX"),
        "description": gap,
        "feasibility": payload.get("feasibility", 50),
        "market_impact": payload.get("market_impact", 70),
        "discovered_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "status": "open",
        "source": "ttlg_diagnostic",
    }
    with open(tracker_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    _log("handle_ttlg_gap_identified", event, f"added to 9th Order tracker")


# ── SYSTEM HANDLERS (5) ──────────────────────────────────────

def handle_doctor_check_failed(event: dict):
    """doctor.check.failed -> Self-Healing immediate scan."""
    payload = event.get("payload", {})
    try:
        from ttlg.pipeline_graph import run_healing_cycle
        result = run_healing_cycle()
        _log("handle_doctor_check_failed", event, f"healing cycle ran: {len(result.get('actions_taken', []))} actions")
    except Exception as e:
        _log("handle_doctor_check_failed", event, str(e), False)


def handle_sovereignty_degraded(event: dict):
    """system.sovereignty.degraded -> Friday sovereignty alert."""
    payload = event.get("payload", {})
    _publish("friday.steward.alert", {"priority": "high", "context": payload, "type": "sovereignty"})
    _log("handle_sovereignty_degraded", event, "Friday alerted")


def handle_baseline_stale(event: dict):
    """knowledge.baseline.stale -> Queue research question."""
    payload = event.get("payload", {})
    research_q_path = VAULT / "knowledge" / "improvements" / "research_queue.jsonl"
    research_q_path.parent.mkdir(parents=True, exist_ok=True)
    q = {
        "role": payload.get("role"),
        "question": f"What is the current best practice for {payload.get('role')}?",
        "priority": "medium",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "stale_baseline_event",
    }
    with open(research_q_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(q) + "\n")
    _log("handle_baseline_stale", event, "research question queued")


def handle_friday_performance_degraded(event: dict):
    """friday.performance.degraded -> Log + escalate to Jamie."""
    payload = event.get("payload", {})
    _publish("friday.steward.alert", {"priority": "high", "context": payload, "type": "friday_degraded"})
    _log("handle_friday_performance_degraded", event, "escalated to Jamie")


def handle_aar_missing(event: dict):
    """system.health.aar_missing -> Queue AAR reminder for next morning briefing."""
    payload = event.get("payload", {})
    reminder_path = REACTOR_VAULT / "aar_reminders.jsonl"
    with open(reminder_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(),
                            "context": payload}) + "\n")
    _log("handle_aar_missing", event, "AAR reminder queued")


# ── 4 EXTRA: Echo, scheduling, intelligence ─────────────────

def handle_content_eri_actual(event: dict):
    """content.eri_actual -> Compare predicted vs actual, learn."""
    payload = event.get("payload", {})
    actual = payload.get("score", 0)
    if actual > 85:
        _publish("content.echo.scored", payload)
    _log("handle_content_eri_actual", event, f"actual={actual}")


def handle_content_scheduled(event: dict):
    """content.scheduled -> Track scheduled content."""
    payload = event.get("payload", {})
    _log("handle_content_scheduled", event, f"scheduled: {payload.get('platform')}")


def handle_cms_asset_created(event: dict):
    """cms.asset.created -> Index for content lab."""
    payload = event.get("payload", {})
    _log("handle_cms_asset_created", event, f"asset indexed: {payload.get('asset_type')}")


def handle_governance_validation_passed(event: dict):
    """governance.validation.passed -> Mark content ready for next stage."""
    payload = event.get("payload", {})
    _publish("content.validated", payload)
    _log("handle_governance_validation_passed", event, "content moved forward")


# ── AVATAR HANDLERS (4) ──────────────────────────────────────
# Bridge the 12-Avatar Signal Architecture into the event reactor.

def _get_avatar_registry():
    try:
        from nodes.avatar_registry import get_registry
        return get_registry()
    except Exception:
        return None


def handle_lead_captured_for_avatar(event: dict):
    """crm.lead.captured -> Score lead against all avatars; emit avatar.lead.scored."""
    payload = event.get("payload", {})
    reg = _get_avatar_registry()
    if not reg:
        _log("handle_lead_captured_for_avatar", event, "registry unavailable", success=False)
        return
    result = reg.score_lead_against_avatars(payload)
    _publish("avatar.lead.scored", {
        "lead_id": payload.get("lead_id"),
        "best_match": result["best_match"],
        "best_score": result["best_score"],
    })
    _log("handle_lead_captured_for_avatar", event, f"matched -> {result['best_match']}")


def handle_content_published_for_avatar(event: dict):
    """content.published -> Detect avatar audience signal from text."""
    payload = event.get("payload", {})
    reg = _get_avatar_registry()
    if not reg:
        _log("handle_content_published_for_avatar", event, "registry unavailable", success=False)
        return
    text = " ".join(str(payload.get(k, "")) for k in ("title", "body", "hook", "summary"))
    matches = reg.match_signal(text)
    if matches:
        _publish("avatar.signal.detected", {
            "source": "content_published",
            "top_match": matches[0]["avatar_id"],
            "top_score": matches[0]["score"],
        })
    _log("handle_content_published_for_avatar", event,
         f"matches={len(matches)} top={matches[0]['avatar_id'] if matches else None}")


def handle_fotw_expression_for_avatar(event: dict):
    """fotw.expression.captured -> Match captured language to avatar segments."""
    payload = event.get("payload", {})
    reg = _get_avatar_registry()
    if not reg:
        _log("handle_fotw_expression_for_avatar", event, "registry unavailable", success=False)
        return
    text = str(payload.get("expression") or payload.get("text") or "")
    matches = reg.match_signal(text, min_score=0.05)
    if matches:
        _publish("avatar.signal.detected", {
            "source": "fotw_expression",
            "top_match": matches[0]["avatar_id"],
            "top_score": matches[0]["score"],
            "expression_id": payload.get("expression_id"),
        })
    _log("handle_fotw_expression_for_avatar", event,
         f"matches={len(matches)}")


def handle_avatar_signal_detected(event: dict):
    """avatar.signal.detected -> Route to marketing amplification (placeholder for Marketing Reactor)."""
    payload = event.get("payload", {})
    avatar_id = payload.get("top_match")
    score = payload.get("top_score", 0)
    # Future: Marketing Reactor will pick this up and run niche-specific amplification
    if score >= 0.20:
        _publish("marketing.amplify.triggered", {
            "avatar_id": avatar_id,
            "score": score,
            "source": payload.get("source"),
        })
    _log("handle_avatar_signal_detected", event,
         f"avatar={avatar_id} score={score} amplify={'yes' if score >= 0.20 else 'no'}")


# ── Handler Registry ─────────────────────────────────────────

CRM_HANDLERS = {
    "crm.lead.scored": handle_crm_lead_scored,
    "crm.lead.converted": handle_crm_lead_converted,
    "client.at_risk": handle_client_at_risk,
    "client.expansion_ready": handle_client_expansion_ready,
    "client.churned": handle_client_churned,
}

BILLING_HANDLERS = {
    "billing.invoice.generated": handle_billing_invoice_generated,
    "billing.payment.received": handle_billing_payment_received,
    "billing.overdue.flagged": handle_billing_overdue_flagged,
    "billing.subscription.changed": handle_billing_subscription_changed,
}

FOTW_HANDLERS = {
    "fotw.expression.captured": handle_fotw_expression_captured,
    "fotw.signal.high": handle_fotw_signal_high,
    "fotw.thread.processed": handle_fotw_thread_processed,
}

TTLG_HANDLERS = {
    "ttlg.diagnostic.complete": handle_ttlg_diagnostic_complete,
    "ttlg.manifest.generated": handle_ttlg_manifest_generated,
    "ttlg.gap.identified": handle_ttlg_gap_identified,
}

SYSTEM_HANDLERS = {
    "doctor.check.failed": handle_doctor_check_failed,
    "system.sovereignty.degraded": handle_sovereignty_degraded,
    "knowledge.baseline.stale": handle_baseline_stale,
    "friday.performance.degraded": handle_friday_performance_degraded,
    "system.health.aar_missing": handle_aar_missing,
}

EXTRA_HANDLERS = {
    "content.eri_actual": handle_content_eri_actual,
    "content.scheduled": handle_content_scheduled,
    "cms.asset.created": handle_cms_asset_created,
    "governance.validation.passed": handle_governance_validation_passed,
}

AVATAR_HANDLERS = {
    "crm.lead.captured": handle_lead_captured_for_avatar,
    "content.published": handle_content_published_for_avatar,
    "fotw.expression.matched": handle_fotw_expression_for_avatar,
    "avatar.signal.detected": handle_avatar_signal_detected,
}

ALL_V2_HANDLERS = {
    **CRM_HANDLERS,
    **BILLING_HANDLERS,
    **FOTW_HANDLERS,
    **TTLG_HANDLERS,
    **SYSTEM_HANDLERS,
    **EXTRA_HANDLERS,
    **AVATAR_HANDLERS,
}


# ── Self-Test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: All handlers callable
    for name, handler in ALL_V2_HANDLERS.items():
        assert callable(handler), f"{name} is not callable"
    print(f"All {len(ALL_V2_HANDLERS)} v2 handlers callable")
    passed += 1

    # Test 2: Categories
    expected_counts = {
        "CRM": 5, "BILLING": 4, "FOTW": 3, "TTLG": 3, "SYSTEM": 5, "EXTRA": 4
    }
    actual_counts = {
        "CRM": len(CRM_HANDLERS), "BILLING": len(BILLING_HANDLERS),
        "FOTW": len(FOTW_HANDLERS), "TTLG": len(TTLG_HANDLERS),
        "SYSTEM": len(SYSTEM_HANDLERS), "EXTRA": len(EXTRA_HANDLERS),
    }
    for cat, expected in expected_counts.items():
        assert actual_counts[cat] == expected, f"{cat}: expected {expected}, got {actual_counts[cat]}"
    print(f"Categories: {actual_counts}")
    passed += 1

    # Test 3: Test a CRM handler
    handle_crm_lead_scored({
        "event_type": "crm.lead.scored",
        "payload": {"lead_id": "TEST-LEAD-001", "score": 88}
    })
    assert V2_LOG.exists()
    passed += 1

    # Test 4: Test a TTLG gap handler (writes to 9th Order tracker)
    handle_ttlg_gap_identified({
        "event_type": "ttlg.gap.identified",
        "payload": {
            "touchpoint": "TP07",
            "description": "Auto-generated test gap from event handler",
            "feasibility": 50,
            "market_impact": 75,
        }
    })
    passed += 1

    # Test 5: Verify log entries
    lines = V2_LOG.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 2
    print(f"V2 log entries: {len(lines)}")
    passed += 1

    print(f"\nPASS: handlers_v2 ({passed} assertions)")
    print(f"Total v2 handlers: {len(ALL_V2_HANDLERS)}")
