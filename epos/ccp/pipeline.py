#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/ccp/pipeline.py — CCP End-to-End Pipeline Orchestrator
============================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

Orchestrates: raw text → extract → score → route → PM write

Wires together:
  transcriber.save_raw_capture() → CCPPipeline.process_text()
  voice/api.py → CCPPipeline.process_capture()
  Friday morning briefing ← CCPPipeline.get_pm_summary()

Usage:
    pipeline = CCPPipeline()

    # Process raw text directly
    result = pipeline.process_text("TODO: call John. We decided to use FastAPI.")

    # Process an existing raw capture
    result = pipeline.process_capture("CAP-20260414T120000Z")

    # Get PM summary for briefing
    summary = pipeline.get_pm_summary()
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from epos.ccp.extractor import extract_elements, ExtractedElement
from epos.ccp.scorer import score_elements, summarize_scores
from epos.ccp.router import route_elements, RoutingResult, confirm_routing

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
RAW_CAPTURES_DIR = EPOS_ROOT / "context_vault" / "raw_captures"
PM_ROOT = EPOS_ROOT / "context_vault" / "pm"
PIPELINE_LOG = EPOS_ROOT / "context_vault" / "ccp_runs.jsonl"

# ── Reward bus (Directive 20260414-02) ────────────────────────────────────────
try:
    from epos.rewards.publish_reward import publish_reward as _pub_reward
    def _reward(signal_name: str, value: float, signal_type: str = "process",
                context: str = "", needs_review: bool = False) -> None:
        try:
            _pub_reward(signal_name=signal_name, value=value,
                        signal_type=signal_type, source="ccp_pipeline",
                        context=context, needs_review=needs_review)
        except Exception:
            pass
except ImportError:
    def _reward(*a, **kw): pass


class CCPPipeline:
    """
    End-to-end CCP pipeline: raw text → business elements → PM.

    This is the organism's cognitive bloodstream. Every intake surface
    (Voice, Reader, FOTW) flows through this pipeline.
    """

    def __init__(
        self,
        use_llm: bool = True,
        auto_threshold: float = 0.90,
        min_confidence: float = 0.60,
    ):
        """
        Args:
            use_llm: Whether to call LLM for medium-confidence elements
            auto_threshold: Confidence above which to auto-route (no human confirmation)
            min_confidence: Minimum confidence to extract an element
        """
        self.use_llm = use_llm
        self.auto_threshold = auto_threshold
        self.min_confidence = min_confidence

    # ──────────────────────────────────────────────────────────────────────────
    # Core processing
    # ──────────────────────────────────────────────────────────────────────────

    def process_text(
        self,
        text: str,
        source_capture_id: Optional[str] = None,
        source_type: str = "direct_paste",
    ) -> dict:
        """
        Full pipeline: text → extract → score → route.

        Args:
            text: Raw input text
            source_capture_id: Optional capture ID for traceability
            source_type: "voice_capture" | "direct_paste" | "fotw" | "reader"

        Returns:
            {
                "run_id": str,
                "source_type": str,
                "text_length": int,
                "elements_extracted": int,
                "score_summary": dict,
                "routing": {
                    "auto_routed": [dict, ...],
                    "pending_confirmation": [dict, ...],
                    "summary": dict,
                },
                "processed_at": str,
            }
        """
        run_id = f"CCP-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        # Step 1: Extract
        elements = extract_elements(
            text,
            source_capture_id=source_capture_id,
            min_confidence=self.min_confidence,
        )

        if not elements:
            _reward("ccp_run_empty", -0.1, signal_type="negative",
                    context=f"{source_type} run={run_id} — 0 elements extracted from {len(text)}c")
            result = {
                "run_id": run_id,
                "source_type": source_type,
                "source_capture_id": source_capture_id,
                "text_length": len(text),
                "elements_extracted": 0,
                "score_summary": {},
                "routing": {"auto_routed": [], "pending_confirmation": [], "summary": {"total": 0}},
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            self._log_run(result)
            return result

        # Step 2: Score
        scored = score_elements(elements, use_llm=self.use_llm)
        score_summary = summarize_scores(scored)

        # Step 3: Route
        routing = route_elements(scored, auto_threshold=self.auto_threshold)

        result = {
            "run_id": run_id,
            "source_type": source_type,
            "source_capture_id": source_capture_id,
            "text_length": len(text),
            "elements_extracted": len(elements),
            "score_summary": score_summary,
            "routing": {
                "auto_routed": [r.to_dict() for r in routing["auto_routed"]],
                "pending_confirmation": [r.to_dict() for r in routing["pending_confirmation"]],
                "summary": routing["summary"],
            },
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Step 3.5: Write auto-routed elements to PM (single writer — M4, 20260414-03)
        pm_written = 0
        try:
            from epos.pm.store import PMStore
            pm_ingest = PMStore().ingest_ccp_result(result)
            pm_written = pm_ingest.get("written", 0)
        except Exception:
            pass
        result["pm_written"] = pm_written

        # ── Reward signals (Directive 20260414-02) ────────────────────────────
        _auto = routing["summary"].get("auto_routed", 0)
        _pending = routing["summary"].get("pending_confirmation", 0)

        # Process: elements extracted (0.05 per element, capped at 0.50)
        _reward("ccp_elements_extracted",
                round(min(len(elements) * 0.05, 0.50), 4),
                signal_type="process",
                context=f"{run_id} extracted={len(elements)} src={source_type}")

        # Outcome: auto-routed elements reach PM without friction
        if _auto > 0:
            _reward("ccp_auto_routed",
                    round(min(_auto * 0.10, 0.50), 4),
                    signal_type="outcome",
                    context=f"{run_id} auto_routed={_auto}/{len(elements)}")

        # Process: pending elements need human review (lighter positive — work remains)
        if _pending > 0:
            _reward("ccp_pending_review",
                    round(min(_pending * 0.02, 0.10), 4),
                    signal_type="process",
                    context=f"{run_id} pending={_pending} awaiting confirmation")

        self._log_run(result)
        return result

    def process_capture(self, capture_id: str) -> dict:
        """
        Load a raw capture by ID and run full CCP pipeline.

        Args:
            capture_id: e.g. "CAP-20260414T120000Z"

        Returns:
            Same structure as process_text()
        """
        capture_path = RAW_CAPTURES_DIR / f"{capture_id}.json"
        if not capture_path.exists():
            raise FileNotFoundError(f"Capture not found: {capture_id}")

        data = json.loads(capture_path.read_text())
        transcript = data.get("raw_transcript", "")

        result = self.process_text(
            transcript,
            source_capture_id=capture_id,
            source_type="voice_capture",
        )

        # Mark capture as processed
        data["processed"] = True
        data["ccp_run_id"] = result["run_id"]
        data["processed_at"] = result["processed_at"]
        capture_path.write_text(json.dumps(data, indent=2))

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Confirmation API
    # ──────────────────────────────────────────────────────────────────────────

    def confirm_element(
        self,
        run_result: dict,
        element_id: str,
        action: str,                       # "confirm" | "override" | "discard"
        override_type: Optional[str] = None,
        override_destination: Optional[str] = None,
    ) -> dict:
        """
        Apply Jamie's confirmation to a pending element.

        Args:
            run_result: Result dict from process_text()
            element_id: element_id of the pending element
            action: "confirm" | "override" | "discard"
            override_type: New element type string (if overriding)
            override_destination: Custom destination path (if overriding)

        Returns:
            Updated routing result dict
        """
        from epos.ccp.extractor import ElementType, SUGGESTED_DESTINATIONS

        # Find the pending element
        pending = run_result["routing"].get("pending_confirmation", [])
        target = next((p for p in pending if p["element_id"] == element_id), None)
        if not target:
            return {"error": f"Element {element_id} not found in pending"}

        # Reconstruct ExtractedElement
        from epos.ccp.extractor import ExtractedElement
        element = ExtractedElement(
            element_id=target["element_id"],
            type=ElementType(target["element_type"]),
            content=target["content"],
            confidence=target["confidence"],
            source_capture_id=target.get("source_capture_id"),
            suggested_destination=target.get("suggested_destination", ""),
        )

        routing_result = RoutingResult(element, action="pending_confirmation")
        routing_result.routing_id = target["routing_id"]

        updated = confirm_routing(
            routing_result,
            action=action,
            override_type=override_type,
            override_destination=override_destination,
        )

        return updated.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # PM summary (for Friday briefing)
    # ──────────────────────────────────────────────────────────────────────────

    def get_pm_summary(self) -> dict:
        """
        Return counts per PM tab per status.
        Feeds Friday morning briefing.

        Returns:
            {
                "action_items": {"total": N, "pending": N, "in_progress": N, ...},
                "decisions": {...},
                "research_queue": {...},
                "blockers": {...},
                "total_pending": N,
            }
        """
        pm_files = {
            "action_items":  PM_ROOT / "action_items.json",
            "decisions":     PM_ROOT / "decisions.json",
            "research_queue": PM_ROOT / "research_queue.json",
            "blockers":      PM_ROOT / "blockers.json",
            "idea_pipeline": PM_ROOT / "idea_pipeline.json",
            "client_insights": PM_ROOT / "client_insights.json",
        }

        summary = {}
        total_pending = 0

        for tab_name, path in pm_files.items():
            if not path.exists():
                summary[tab_name] = {"total": 0, "pending": 0}
                continue

            try:
                data = json.loads(path.read_text())
                items = data if isinstance(data, list) else data.get("items", [])
            except Exception:
                items = []

            status_counts: dict = {}
            for item in items:
                status = item.get("status", "pending")
                status_counts[status] = status_counts.get(status, 0) + 1

            tab_summary = {"total": len(items), **status_counts}
            summary[tab_name] = tab_summary
            total_pending += status_counts.get("pending", 0)

        summary["total_pending"] = total_pending
        summary["generated_at"] = datetime.now(timezone.utc).isoformat()
        return summary

    # ──────────────────────────────────────────────────────────────────────────
    # Pipeline run logging
    # ──────────────────────────────────────────────────────────────────────────

    def _log_run(self, result: dict):
        """Append pipeline run to ccp_runs.jsonl."""
        PIPELINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "run_id": result["run_id"],
            "source_type": result.get("source_type"),
            "text_length": result.get("text_length", 0),
            "elements_extracted": result.get("elements_extracted", 0),
            "auto_routed": result["routing"]["summary"].get("auto_routed", 0),
            "pending": result["routing"]["summary"].get("pending_confirmation", 0),
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(PIPELINE_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
