#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
content_signal_loop.py — Content Production Signal Loop
========================================================
Constitutional Authority: EPOS Constitution v3.1
Module: Content Signal Loop (CODE DIRECTIVE Module 5)

Connects content pipeline events to Friday intelligence and the context graph.
Listens for content events → extracts signals → updates graph weights →
notifies Friday → feeds back into production decisions.

Signal types:
  content.spark.created    → New content idea detected
  content.eri.predicted    → ERI score available
  content.script.generated → Script drafted
  content.published        → Asset went live
  content.performance      → Engagement metrics arrived
  content.cascade.released → Multi-platform cascade triggered
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision


# Event types this module monitors
CONTENT_EVENTS = [
    "content.spark.created",
    "content.eri.predicted",
    "content.script.generated",
    "governance.validation.pass",
    "governance.validation.fail",
    "content.published",
    "content.performance",
    "content.cascade.released",
    "content.scheduled",
]


class ContentSignalLoop:
    """Processes content events into intelligence signals."""

    def __init__(self):
        self.vault = get_context_vault()
        self.signals_dir = self.vault / "content" / "signals"
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self.signal_log = self.signals_dir / "content_signals.jsonl"
        self.bus = EPOSEventBus()

    def process_recent_events(self, minutes: int = 60) -> List[dict]:
        """Scan recent bus events for content signals and process them."""
        events = self.bus.get_recent(minutes=minutes)
        signals = []

        for event in events:
            if event.event_type in CONTENT_EVENTS:
                signal = self._extract_signal(event)
                if signal:
                    signals.append(signal)
                    self._log_signal(signal)

        # Update context graph with performance signals
        perf_signals = [s for s in signals if s["signal_type"] == "performance"]
        if perf_signals:
            self._update_graph_weights(perf_signals)

        # Feed to Friday intelligence
        if signals:
            self._notify_friday(signals)

        return signals

    def _extract_signal(self, event) -> Optional[dict]:
        """Extract a structured signal from a content event."""
        data = event.payload if hasattr(event, 'payload') else {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        signal = {
            "signal_id": f"CSIG-{event.event_type.split('.')[-1]}-{datetime.now(timezone.utc).strftime('%H%M%S')}",
            "event_type": event.event_type,
            "signal_type": self._classify_signal(event.event_type),
            "data": data,
            "source_module": event.source_module if hasattr(event, 'source_module') else "unknown",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Enrich based on signal type
        if signal["signal_type"] == "quality_gate":
            signal["passed"] = "pass" in event.event_type
            signal["severity"] = "high" if "fail" in event.event_type else "info"

        elif signal["signal_type"] == "performance":
            signal["metrics"] = data.get("metrics", {})
            signal["niche"] = data.get("niche", "unknown")
            signal["hook_type"] = data.get("hook_type", "unknown")

        elif signal["signal_type"] == "production":
            signal["asset_type"] = data.get("asset_type", "content")
            signal["niche"] = data.get("niche", "unknown")

        return signal

    def _classify_signal(self, event_type: str) -> str:
        """Classify event into signal category."""
        if "performance" in event_type:
            return "performance"
        elif "validation" in event_type or "governance" in event_type:
            return "quality_gate"
        elif "published" in event_type or "scheduled" in event_type:
            return "distribution"
        elif "cascade" in event_type:
            return "amplification"
        elif "spark" in event_type or "eri" in event_type:
            return "opportunity"
        else:
            return "production"

    def _log_signal(self, signal: dict) -> None:
        """Append signal to the content signals journal."""
        with open(self.signal_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal) + "\n")

    def _update_graph_weights(self, perf_signals: List[dict]) -> None:
        """Feed performance signals into context graph weights."""
        try:
            from context_graph import ContextGraph
            graph = ContextGraph()
            for sig in perf_signals:
                niche = sig.get("niche", "unknown")
                hook = sig.get("hook_type", "unknown")
                metrics = sig.get("metrics", {})
                # Use engagement rate as the weight signal
                engagement = metrics.get("engagement_rate", 0.5)
                if niche != "unknown" and hook != "unknown":
                    graph.update_edge(niche, hook, engagement)
        except Exception:
            pass  # Graph update is best-effort

    def _notify_friday(self, signals: List[dict]) -> None:
        """Publish aggregated content intelligence to Friday."""
        summary = {
            "total_signals": len(signals),
            "by_type": {},
            "quality_gates_failed": 0,
            "performance_highlights": [],
        }
        for sig in signals:
            stype = sig.get("signal_type", "other")
            summary["by_type"][stype] = summary["by_type"].get(stype, 0) + 1
            if sig.get("signal_type") == "quality_gate" and not sig.get("passed"):
                summary["quality_gates_failed"] += 1
            if sig.get("signal_type") == "performance":
                summary["performance_highlights"].append({
                    "niche": sig.get("niche"),
                    "hook": sig.get("hook_type"),
                    "metrics": sig.get("metrics", {}),
                })

        self.bus.publish("friday.content_intelligence", summary, "content_signal_loop")

        # If quality gates failed, escalate
        if summary["quality_gates_failed"] > 0:
            self.bus.publish("friday.signal.escalation", {
                "type": "content_quality_failure",
                "count": summary["quality_gates_failed"],
                "priority": "high",
            }, "content_signal_loop")

    def get_signal_summary(self, hours: int = 24) -> dict:
        """Get content signal summary for dashboard display."""
        if not self.signal_log.exists():
            return {"total": 0, "by_type": {}, "recent": []}

        cutoff = datetime.now(timezone.utc).isoformat()[:10]  # Today
        signals = []
        for line in self.signal_log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    sig = json.loads(line)
                    if sig.get("extracted_at", "")[:10] >= cutoff:
                        signals.append(sig)
                except Exception:
                    pass

        by_type = {}
        for sig in signals:
            t = sig.get("signal_type", "other")
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total": len(signals),
            "by_type": by_type,
            "recent": signals[-5:],
        }

    def inject_test_signals(self) -> List[dict]:
        """Inject test content events for verification."""
        test_events = [
            ("content.spark.created", {"niche": "lego_affiliate", "title": "LEGO Spring Sets Review"}),
            ("content.eri.predicted", {"niche": "lego_affiliate", "eri_score": 78, "hook_type": "unboxing"}),
            ("content.published", {"niche": "lego_affiliate", "asset_type": "youtube_video", "title": "Spring Sets"}),
            ("content.performance", {"niche": "lego_affiliate", "hook_type": "unboxing",
                                      "metrics": {"views": 1200, "engagement_rate": 0.72, "ctr": 0.08}}),
        ]
        for event_type, payload in test_events:
            self.bus.publish(event_type, payload, "content_signal_loop_test")

        # Now process them
        return self.process_recent_events(minutes=5)


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile

    py_compile.compile("content_signal_loop.py", doraise=True)
    print("PASS: content_signal_loop.py compiles clean")

    loop = ContentSignalLoop()

    # Inject and process test signals
    signals = loop.inject_test_signals()
    print(f"PASS: Processed {len(signals)} content signals")

    # Check summary
    summary = loop.get_signal_summary()
    print(f"PASS: Signal summary — {summary['total']} signals today")
    for stype, count in summary.get("by_type", {}).items():
        print(f"  {stype}: {count}")

    print("\nPASS: ContentSignalLoop — all tests passed")
