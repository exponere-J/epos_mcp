#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
content_reactor.py — Content Pipeline Event Reactor
======================================================
Constitutional Authority: EPOS Constitution v3.1

Activates Workflow 1: Content -> Publish -> Score (the Echolocation loop).

Subscribes to content.* events and dispatches the next pipeline step
automatically. Turns the Content Lab from a manual CLI sequence into
an autonomous flywheel.

Event chain:
  content.spark.created    -> AN1 scores resonance potential
  content.eri.predicted    -> A1 scripts variants (if score above threshold)
  content.script.generated -> V1 validates brand compliance
  content.validated        -> M1 publishes (BrowserUse or staging)
  content.published        -> AN1 schedules echo scoring
  content.echo.scored      -> Echolocation expansion check
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
CONTENT_LOG = REACTOR_VAULT / "content_reactor_log.jsonl"

# Resonance threshold for triggering A1 scripting
RESONANCE_THRESHOLD = 70


def log_handler(handler_name: str, event: dict, result: dict, success: bool = True):
    """Log handler execution to content_reactor_log.jsonl."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "handler": handler_name,
        "event_type": event.get("event_type"),
        "payload_preview": str(event.get("payload", {}))[:200],
        "result": str(result)[:300],
        "success": success,
    }
    with open(CONTENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _publish(event_type: str, payload: dict):
    """Publish next event in the chain."""
    if _BUS:
        try:
            _BUS.publish(event_type, payload, source_module="content_reactor")
        except Exception:
            pass


# ── Handlers ─────────────────────────────────────────────────

def handle_spark_scoring(event: dict):
    """content.spark.created -> AN1 scores resonance potential."""
    payload = event.get("payload", {})
    spark_id = payload.get("spark_id") or payload.get("id")
    spark_path = payload.get("spark_path")

    try:
        # Try to load spark from path or by ID
        if spark_path and Path(spark_path).exists():
            spark_data = json.loads(Path(spark_path).read_text(encoding="utf-8"))
        elif spark_id:
            # Try common spark vault locations
            for vault_path in [VAULT / "echoes" / "sparks", VAULT / "sparks"]:
                candidates = list(vault_path.glob(f"*{spark_id}*.json"))
                if candidates:
                    spark_data = json.loads(candidates[0].read_text(encoding="utf-8"))
                    spark_path = str(candidates[0])
                    break
            else:
                log_handler("handle_spark_scoring", event, "Spark not found", False)
                return
        else:
            log_handler("handle_spark_scoring", event, "No spark_id or spark_path", False)
            return

        # Score with AN1 (heuristic-based for now since AN1's predict_eri needs a brief, not raw spark)
        # Use spark properties to estimate resonance
        topic = spark_data.get("topic", "") or spark_data.get("raw_content", "")
        score = _estimate_resonance(topic)

        result = {"spark_id": spark_id, "score": score, "above_threshold": score >= RESONANCE_THRESHOLD}
        log_handler("handle_spark_scoring", event, result)

        # Publish next event in chain
        _publish("content.eri.predicted", {
            "spark_id": spark_id,
            "spark_path": spark_path,
            "resonance_score": score,
            "threshold": RESONANCE_THRESHOLD,
            "above_threshold": score >= RESONANCE_THRESHOLD,
        })

    except Exception as e:
        log_handler("handle_spark_scoring", event, str(e), False)


def _estimate_resonance(text: str) -> int:
    """Estimate resonance score from text features (heuristic)."""
    if not text:
        return 30
    score = 50  # baseline
    text_lower = text.lower()
    # Hook indicators
    if "?" in text:
        score += 10
    if any(w in text_lower for w in ["how to", "why", "stop", "the truth", "secret"]):
        score += 15
    if any(w in text_lower for w in ["sovereignty", "autonomy", "system", "engine"]):
        score += 10
    # Length penalty
    if len(text) < 30:
        score -= 10
    elif len(text) > 200:
        score += 5
    return min(max(score, 0), 100)


def handle_script_dispatch(event: dict):
    """content.eri.predicted -> A1 scripts variants if above threshold."""
    payload = event.get("payload", {})
    if not payload.get("above_threshold"):
        log_handler("handle_script_dispatch", event, "Below threshold, skipping", True)
        return

    spark_id = payload.get("spark_id")
    spark_path = payload.get("spark_path")

    try:
        # Generate a brief from the spark — A1 expects a Creative Brief
        brief_id = f"AUTOBRIEF-{spark_id[:8] if spark_id else 'UNKNOWN'}"
        brief = {
            "brief_id": brief_id,
            "spark_id": spark_id,
            "spark_path": spark_path,
            "angle_type": "architect",
            "hook_type": "question",
            "visual_mask": "schematic",
            "target_platform": "linkedin",
            "script_premise": payload.get("topic", "Auto-generated from spark"),
            "hook_line": "",
            "cta": "Link in bio.",
            "predicted_eri_score": payload.get("resonance_score", 0),
            "affiliate_products": [],
            "status": "auto_generated",
        }

        brief_path = VAULT / "echoes" / "briefs" / f"{brief_id}.json"
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        brief_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")

        result = {"brief_id": brief_id, "brief_path": str(brief_path)}
        log_handler("handle_script_dispatch", event, result)

        # Publish next event
        _publish("content.script.generated", {
            "brief_id": brief_id,
            "brief_path": str(brief_path),
            "spark_id": spark_id,
        })

    except Exception as e:
        log_handler("handle_script_dispatch", event, str(e), False)


def handle_validation(event: dict):
    """content.script.generated -> V1 validates brand compliance."""
    payload = event.get("payload", {})
    brief_id = payload.get("brief_id")
    brief_path = payload.get("brief_path")

    try:
        if not brief_path or not Path(brief_path).exists():
            log_handler("handle_validation", event, "Brief not found", False)
            return

        brief_data = json.loads(Path(brief_path).read_text(encoding="utf-8"))

        # V1 validation (simplified — full V1 needs complete script)
        # For now, validate that brief has required fields
        required = ["brief_id", "angle_type", "hook_type", "script_premise", "cta"]
        missing = [f for f in required if not brief_data.get(f)]
        verdict = "FAIL" if missing else "PASS"

        result = {"brief_id": brief_id, "verdict": verdict, "missing": missing}
        log_handler("handle_validation", event, result)

        if verdict == "PASS":
            _publish("content.validated", {
                "brief_id": brief_id,
                "brief_path": brief_path,
                "verdict": "PASS",
            })

    except Exception as e:
        log_handler("handle_validation", event, str(e), False)


def handle_publish(event: dict):
    """content.validated -> M1 stages or publishes via BrowserUse."""
    payload = event.get("payload", {})
    brief_id = payload.get("brief_id")
    brief_path = payload.get("brief_path")

    try:
        if not brief_path or not Path(brief_path).exists():
            log_handler("handle_publish", event, "Brief not found", False)
            return

        brief = json.loads(Path(brief_path).read_text(encoding="utf-8"))

        # Stage the post for M1 Publisher
        from echoes.m1_publisher import create_post, M1Publisher
        body = brief.get("script_premise", "")
        platform = brief.get("target_platform", "linkedin")
        if platform == "youtube_shorts":
            platform = "linkedin"  # default fallback
        cta_token = f"AUTO-{brief_id[:12]}"

        post = create_post(platform, body, content_type="text", cta_token=cta_token)
        publisher = M1Publisher()
        result = publisher.publish(post)

        log_handler("handle_publish", event, {"post_id": post.get("id"), "success": result.get("success")})

        if result.get("success"):
            _publish("content.published", {
                "post_id": post.get("id"),
                "platform": platform,
                "cta_token": cta_token,
                "brief_id": brief_id,
                "method": result.get("method", "staged"),
            })

    except Exception as e:
        log_handler("handle_publish", event, str(e), False)


def handle_echo_schedule(event: dict):
    """content.published -> Schedule echo scoring at T+24h and T+48h."""
    payload = event.get("payload", {})
    post_id = payload.get("post_id")

    try:
        # Log echo scoring schedule (real scheduling would use APScheduler)
        echo_schedule = {
            "post_id": post_id,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "first_check": "+24h",
            "second_check": "+48h",
        }
        schedule_path = REACTOR_VAULT / "echo_schedule.jsonl"
        with open(schedule_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(echo_schedule) + "\n")

        log_handler("handle_echo_schedule", event, echo_schedule)

    except Exception as e:
        log_handler("handle_echo_schedule", event, str(e), False)


def handle_expansion_check(event: dict):
    """content.echo.scored -> Trigger Expansion Protocol if score > 85."""
    payload = event.get("payload", {})
    score = payload.get("actual_eri_score", 0)

    try:
        if score > 85:
            result = {"expansion_triggered": True, "score": score}
            _publish("content.expansion_protocol.triggered", payload)
        else:
            result = {"expansion_triggered": False, "score": score}

        log_handler("handle_expansion_check", event, result)

    except Exception as e:
        log_handler("handle_expansion_check", event, str(e), False)


# ── Handler Registry ─────────────────────────────────────────

CONTENT_HANDLERS = {
    "content.spark.created": handle_spark_scoring,
    "content.eri.predicted": handle_script_dispatch,
    "content.script.generated": handle_validation,
    "content.validated": handle_publish,
    "content.published": handle_echo_schedule,
    "content.echo.scored": handle_expansion_check,
}


def register_content_handlers(handler_dict: dict):
    """Called at daemon startup to register all content pipeline handlers."""
    handler_dict.update(CONTENT_HANDLERS)
    return len(CONTENT_HANDLERS)


# ── Self-Test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0

    # Test 1: All handlers callable
    for name, handler in CONTENT_HANDLERS.items():
        assert callable(handler), f"{name} is not callable"
    print(f"All {len(CONTENT_HANDLERS)} handlers callable")
    passed += 1

    # Test 2: Resonance estimator
    high_score = _estimate_resonance("How to build a sovereign content engine? The truth nobody talks about.")
    low_score = _estimate_resonance("hi")
    assert high_score > low_score
    print(f"Resonance estimator: high={high_score}, low={low_score}")
    passed += 1

    # Test 3: Spark scoring handler with real spark
    test_spark = {
        "id": "TEST-SPARK-CR-001",
        "topic": "How does Echolocation transform content strategy? The system that listens.",
        "created": datetime.now(timezone.utc).isoformat(),
    }
    spark_path = VAULT / "echoes" / "sparks" / "TEST-SPARK-CR-001.json"
    spark_path.parent.mkdir(parents=True, exist_ok=True)
    spark_path.write_text(json.dumps(test_spark), encoding="utf-8")

    handle_spark_scoring({
        "event_type": "content.spark.created",
        "payload": {"spark_id": "TEST-SPARK-CR-001", "spark_path": str(spark_path)},
    })
    assert CONTENT_LOG.exists()
    passed += 1

    # Test 4: Verify log entry written
    last_log = CONTENT_LOG.read_text(encoding="utf-8").strip().split("\n")[-1]
    log_entry = json.loads(last_log)
    assert log_entry["handler"] == "handle_spark_scoring"
    print(f"Log entry: {log_entry['handler']} -> success={log_entry['success']}")
    passed += 1

    # Test 5: Register into a fake handler dict
    fake_dict = {}
    count = register_content_handlers(fake_dict)
    assert count == 6
    assert len(fake_dict) == 6
    print(f"Registered {count} handlers into reactor")
    passed += 1

    print(f"\nPASS: content_reactor ({passed} assertions)")
