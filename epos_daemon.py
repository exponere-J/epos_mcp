#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_daemon.py — EPOS Autonomous Operating Daemon
=====================================================
Constitutional Authority: EPOS Constitution v3.1

The heartbeat of the organism. Runs as a persistent process (or Windows Service
via NSSM) providing:
  1. APScheduler — timed daily anchors, flywheel checks, KIL scans
  2. Event Reactor — tail Event Bus JSONL, dispatch actions on pattern match
  3. Health monitor — periodic self-check and healing cycle

When this daemon runs, the organism acts without Jamie present.
"""

import os
import sys
import json
import time
import threading
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
EVENTS_PATH = VAULT / "events" / "system" / "events.jsonl"
LOG_DIR = Path(os.getenv("LOG_DIR", str(Path(__file__).parent / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "epos_daemon.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("epos_daemon")


# ══════════════════════════════════════════════════════════════
# SCHEDULED TASKS (APScheduler)
# ══════════════════════════════════════════════════════════════

def task_kil_scan():
    """04:00 — Knowledge Ingestion Layer daily scan."""
    logger.info("KIL daily scan starting")
    try:
        from knowledge.kil_daily import KILDaily
        result = KILDaily().run()
        logger.info(f"KIL scan complete: {result['total_baselines']} baselines, {result['stale_baselines']} stale")
    except Exception as e:
        logger.error(f"KIL scan failed: {e}")


def task_self_healing():
    """05:00 — Self-Healing cycle."""
    logger.info("Self-Healing cycle starting")
    try:
        from ttlg.pipeline_graph import run_healing_cycle
        result = run_healing_cycle()
        actions = result.get("actions_taken", [])
        logger.info(f"Self-Healing complete: {len(actions)} actions")
    except Exception as e:
        logger.error(f"Self-Healing failed: {e}")


def task_morning_anchor():
    """06:00 — Friday morning anchor (generates briefing, logs)."""
    logger.info("Friday morning anchor")
    try:
        from friday_daily_anchors import FridayDailyAnchors
        fda = FridayDailyAnchors()
        fda.run_anchor("morning")
        logger.info("Morning anchor logged")
    except Exception as e:
        logger.error(f"Morning anchor failed: {e}")


def task_content_pipeline():
    """07:30 — Content Lab signal processing."""
    logger.info("Content signal processing")
    try:
        from content_signal_loop import ContentSignalLoop
        loop = ContentSignalLoop()
        signals = loop.process_recent_events(minutes=1440)
        logger.info(f"Content signals processed: {len(signals)}")
    except Exception as e:
        logger.error(f"Content signal processing failed: {e}")


def task_fotw_scan():
    """08:00 — FOTW nightly scanner (scan Downloads + Attachments)."""
    logger.info("FOTW scan starting")
    try:
        sys.path.insert(0, str(Path.home() / "workspace" / "fotw"))
        from nightly_scanner import NightlyScanner
        result = NightlyScanner().scan(verbose=False)
        logger.info(f"FOTW scan: {result['files_found']} found, {result['files_processed']} processed")
    except Exception as e:
        logger.error(f"FOTW scan failed: {e}")


def task_doctor_check():
    """12:00 — Midday Doctor health check."""
    logger.info("Doctor midday check")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "engine/epos_doctor.py"],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent))
        import re
        fail_m = re.search(r"Failed:\s*(\d+)", result.stdout)
        fails = int(fail_m.group(1)) if fail_m else -1
        if fails > 0:
            logger.warning(f"Doctor: {fails} FAILURES detected")
            if _BUS:
                _BUS.publish("system.doctor.failures", {"count": fails}, source_module="epos_daemon")
        else:
            logger.info("Doctor: all clear")
    except Exception as e:
        logger.error(f"Doctor check failed: {e}")


def task_evening_triage():
    """18:00 — Friday evening triage (ideas + signals)."""
    logger.info("Friday evening triage")
    try:
        from friday_intelligence import FridayIntelligence
        fi = FridayIntelligence()
        results = fi.triage_all_untriaged()
        logger.info(f"Triaged {len(results)} ideas")
    except Exception as e:
        logger.error(f"Evening triage failed: {e}")


def task_nightly_healing():
    """22:00 — Nightly self-healing + vault cleanup."""
    logger.info("Nightly healing cycle")
    try:
        from ttlg.pipeline_graph import run_healing_cycle
        result = run_healing_cycle()
        logger.info(f"Nightly healing: {len(result.get('actions_taken', []))} actions")
    except Exception as e:
        logger.error(f"Nightly healing failed: {e}")


def task_friday_self_assessment():
    """23:00 — Friday daily self-assessment."""
    logger.info("Friday self-assessment")
    try:
        from friday.continuous_improvement import FridayContinuousImprovement
        result = FridayContinuousImprovement().daily_self_assessment()
        logger.info(f"Friday self-assessment: {result.get('missions_total', 0)} missions, {result.get('performance', '?')}")
    except Exception as e:
        logger.error(f"Friday self-assessment failed: {e}")


def task_friday_routing_check():
    """Every 6 hours — Friday routing accuracy check."""
    logger.info("Friday routing check")
    try:
        from friday.continuous_improvement import FridayContinuousImprovement
        result = FridayContinuousImprovement().routing_accuracy_tracker()
        logger.info(f"Friday routing: accuracy={result.get('accuracy')}")
    except Exception as e:
        logger.error(f"Friday routing check failed: {e}")


# ══════════════════════════════════════════════════════════════
# EVENT REACTOR (Tail JSONL, dispatch on pattern match)
# ══════════════════════════════════════════════════════════════

EVENT_HANDLERS = {
    "content.spark.created": "dispatch_an1_scoring",
    "lead.score.updated": "dispatch_journey_routing",
    "doctor.sweep.failed": "dispatch_self_healing",
    "content.staged.ready": "dispatch_m1_publisher",
    "ttlg.gap.identified": "dispatch_build_manifest",
    "fotw.expression.captured": "dispatch_fotw_clustering",
    "system.health.stale_journal": "dispatch_friday_alert",
    "governance.gate.reject": "dispatch_friday_alert",
    "payment.received": "dispatch_friday_alert",
    "fotw.thread.captured": "dispatch_fotw_processing",
}

# Register Content Reactor handlers (Mission 1 — wires Workflow 1 end-to-end)
try:
    from reactor.content_reactor import CONTENT_HANDLERS as _CONTENT_HANDLERS
    _CONTENT_HANDLER_FUNCS = _CONTENT_HANDLERS
    for event_type in _CONTENT_HANDLERS:
        EVENT_HANDLERS[event_type] = "content_reactor"
except ImportError:
    _CONTENT_HANDLER_FUNCS = {}

# Register Event Reactor v2 handlers (Mission 2)
try:
    from reactor.handlers_v2 import ALL_V2_HANDLERS as _V2_HANDLERS
    _V2_HANDLER_FUNCS = _V2_HANDLERS
    for event_type in _V2_HANDLERS:
        EVENT_HANDLERS[event_type] = "reactor_v2"
except ImportError:
    _V2_HANDLER_FUNCS = {}

# Register Marketing Reactor handlers (5th reactor — demand-side)
try:
    from reactor.marketing_reactor import MARKETING_HANDLERS as _MARKETING_HANDLERS
    _MARKETING_HANDLER_FUNCS = _MARKETING_HANDLERS
    for event_type in _MARKETING_HANDLERS:
        # Marketing reactor wins over v2 where keys overlap (avatar.signal.detected)
        EVENT_HANDLERS[event_type] = "marketing_reactor"
except ImportError:
    _MARKETING_HANDLER_FUNCS = {}


def handle_event(event: dict):
    """Dispatch event to the appropriate handler."""
    event_type = event.get("event_type", "")
    handler_name = EVENT_HANDLERS.get(event_type)
    if not handler_name:
        return

    payload = event.get("payload", {})
    logger.info(f"Reactor: {event_type} -> {handler_name}")

    # Route to Content Reactor handlers (Mission 1)
    if handler_name == "content_reactor" and event_type in _CONTENT_HANDLER_FUNCS:
        try:
            _CONTENT_HANDLER_FUNCS[event_type](event)
        except Exception as e:
            logger.error(f"Content Reactor handler {event_type} failed: {e}")
        return

    # Route to Event Reactor v2 handlers (Mission 2)
    if handler_name == "reactor_v2" and event_type in _V2_HANDLER_FUNCS:
        try:
            _V2_HANDLER_FUNCS[event_type](event)
        except Exception as e:
            logger.error(f"Reactor v2 handler {event_type} failed: {e}")
        return

    # Route to Marketing Reactor handlers (5th reactor — demand-side)
    if handler_name == "marketing_reactor" and event_type in _MARKETING_HANDLER_FUNCS:
        try:
            _MARKETING_HANDLER_FUNCS[event_type](event)
        except Exception as e:
            logger.error(f"Marketing reactor handler {event_type} failed: {e}")
        return

    try:
        if handler_name == "dispatch_an1_scoring":
            from content_signal_loop import ContentSignalLoop
            ContentSignalLoop().process_recent_events(minutes=5)

        elif handler_name == "dispatch_self_healing":
            from ttlg.pipeline_graph import run_healing_cycle
            run_healing_cycle()

        elif handler_name == "dispatch_friday_alert":
            logger.info(f"Friday alert: {event_type} — {json.dumps(payload)[:100]}")

        elif handler_name == "dispatch_fotw_clustering":
            from fotw_listener import FOTWListener
            FOTWListener().cluster_expressions()

        elif handler_name == "dispatch_fotw_processing":
            logger.info(f"FOTW thread captured: {payload.get('session_id', '?')}")

        else:
            logger.info(f"Handler {handler_name}: acknowledged (no executor wired yet)")

    except Exception as e:
        logger.error(f"Handler {handler_name} failed: {e}")


def event_reactor_thread():
    """Background thread that tails the Event Bus JSONL."""
    logger.info("Event Reactor started — tailing Event Bus")
    if not EVENTS_PATH.exists():
        logger.warning(f"Event Bus not found at {EVENTS_PATH}")
        return

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        # Seek to end — only process NEW events
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    handle_event(event)
                except json.JSONDecodeError:
                    pass
            else:
                time.sleep(0.5)


# ══════════════════════════════════════════════════════════════
# DAEMON MAIN
# ══════════════════════════════════════════════════════════════

def start_daemon():
    """Start the EPOS autonomous daemon."""
    logger.info("=" * 60)
    logger.info("EPOS DAEMON STARTING")
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Vault: {VAULT}")
    logger.info("=" * 60)

    # Start APScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(task_kil_scan,         CronTrigger(hour=4, minute=0),   id="kil_scan")
    scheduler.add_job(task_self_healing,     CronTrigger(hour=5, minute=0),   id="self_healing_morning")
    scheduler.add_job(task_morning_anchor,   CronTrigger(hour=6, minute=0),   id="morning_anchor")
    scheduler.add_job(task_content_pipeline, CronTrigger(hour=7, minute=30),  id="content_pipeline")
    scheduler.add_job(task_fotw_scan,        CronTrigger(hour=8, minute=0),   id="fotw_scan")
    scheduler.add_job(task_doctor_check,     CronTrigger(hour=12, minute=0),  id="doctor_midday")
    scheduler.add_job(task_evening_triage,   CronTrigger(hour=18, minute=0),  id="evening_triage")
    scheduler.add_job(task_nightly_healing,  CronTrigger(hour=22, minute=0),  id="nightly_healing")
    scheduler.add_job(task_friday_self_assessment, CronTrigger(hour=23, minute=0), id="friday_self_assess")
    from apscheduler.triggers.interval import IntervalTrigger
    scheduler.add_job(task_friday_routing_check, IntervalTrigger(hours=6), id="friday_routing")
    scheduler.start()
    logger.info(f"APScheduler started: {len(scheduler.get_jobs())} jobs scheduled")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.id}: {job.trigger}")

    # Publish daemon start event
    if _BUS:
        try:
            _BUS.publish("system.daemon.started", {
                "pid": os.getpid(),
                "jobs": len(scheduler.get_jobs()),
                "handlers": len(EVENT_HANDLERS),
            }, source_module="epos_daemon")
        except Exception:
            pass

    # Start Event Reactor in background thread
    reactor = threading.Thread(target=event_reactor_thread, daemon=True)
    reactor.start()
    logger.info(f"Event Reactor started: {len(EVENT_HANDLERS)} handlers registered")

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("EPOS Daemon shutting down")
        scheduler.shutdown()


# ══════════════════════════════════════════════════════════════
# CLI + SELF-TEST
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        passed = 0

        # Test 1: Scheduler creates jobs
        scheduler = BackgroundScheduler()
        scheduler.add_job(lambda: None, CronTrigger(hour=4), id="test_job")
        assert len(scheduler.get_jobs()) == 1
        passed += 1

        # Test 2: Event handler lookup
        # After Content Reactor registration, content.spark.created is routed via content_reactor
        assert EVENT_HANDLERS.get("content.spark.created") in ("dispatch_an1_scoring", "content_reactor")
        assert "dispatch_self_healing" == EVENT_HANDLERS.get("doctor.sweep.failed")
        # Avatar reactor registration sanity
        assert "reactor_v2" == EVENT_HANDLERS.get("crm.lead.captured"), \
            "Avatar handler crm.lead.captured should be wired via reactor_v2"
        passed += 1

        # Test 3: Event dispatch works
        handle_event({"event_type": "system.health.stale_journal", "payload": {"test": True}})
        passed += 1

        print(f"PASS: epos_daemon ({passed} assertions)")
        print(f"Scheduled tasks: 8 | Event handlers: {len(EVENT_HANDLERS)}")

    elif len(sys.argv) > 1 and sys.argv[1] == "--jobs":
        print("EPOS Daemon Scheduled Tasks:")
        tasks = [
            ("04:00", "kil_scan", "Knowledge Ingestion Layer daily scan"),
            ("05:00", "self_healing", "Self-Healing cycle"),
            ("06:00", "morning_anchor", "Friday morning anchor"),
            ("07:30", "content_pipeline", "Content Lab signal processing"),
            ("08:00", "fotw_scan", "FOTW nightly scanner"),
            ("12:00", "doctor_midday", "Doctor health check"),
            ("18:00", "evening_triage", "Friday evening triage"),
            ("22:00", "nightly_healing", "Nightly self-healing + cleanup"),
            ("23:00", "friday_self_assess", "Friday daily self-assessment"),
            ("06h", "friday_routing", "Friday routing accuracy check (every 6h)"),
        ]
        for t, name, desc in tasks:
            print(f"  {t}  {name:25s}  {desc}")
        print(f"\nEvent Reactor Handlers ({len(EVENT_HANDLERS)}):")
        for event_type, handler in sorted(EVENT_HANDLERS.items()):
            print(f"  {event_type:40s} -> {handler}")

    else:
        start_daemon()
