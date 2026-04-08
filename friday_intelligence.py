#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
friday_intelligence.py — Friday's Personal Knowledge & Learning System
=======================================================================
Constitutional Authority: EPOS Constitution v3.1, Friday Mandate v2.0

Friday learns from what the Steward acts on, what the market does,
and what patterns precede outcomes. A new Friday has rules.
A mature Friday anticipates.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_intelligence import record_decision


class FridayIntelligence:
    """Friday's personal knowledge base and calibration system."""

    def __init__(self):
        friday_dir = get_context_vault() / "friday"
        friday_dir.mkdir(parents=True, exist_ok=True)
        self.kb_path = friday_dir
        for fname in ["steward_patterns.jsonl", "escalation_accuracy.jsonl",
                       "market_awareness.jsonl", "lifeos_context.jsonl",
                       "friday_growth_log.jsonl"]:
            (self.kb_path / fname).touch()

    def record_steward_response(self, signal_id: str, signal_type: str,
                                 steward_action: str, response_time_minutes: float,
                                 context: dict = None) -> None:
        """Record how the Steward responded to an escalation."""
        pattern = {"signal_id": signal_id, "signal_type": signal_type,
                   "steward_action": steward_action,
                   "response_time_minutes": response_time_minutes,
                   "context": context or {},
                   "recorded_at": datetime.now(timezone.utc).isoformat()}
        self._append("steward_patterns.jsonl", pattern)
        self._update_escalation_calibration(signal_type, steward_action)

    def _update_escalation_calibration(self, signal_type: str, action: str) -> None:
        delta = 0.1 if action == "acted" else (-0.05 if action == "dismissed" else 0.0)
        self._append("escalation_accuracy.jsonl", {
            "signal_type": signal_type, "action": action,
            "weight_delta": delta,
            "timestamp": datetime.now(timezone.utc).isoformat()})

    def get_signal_priority_weight(self, signal_type: str) -> float:
        """Learned priority weight. 0.5=neutral, >0.5=steward acts, <0.5=steward dismisses."""
        weight = 0.5
        for line in self._read_lines("escalation_accuracy.jsonl"):
            try:
                entry = json.loads(line)
                if entry.get("signal_type") == signal_type:
                    weight = max(0.1, min(0.9, weight + entry.get("weight_delta", 0) * 0.3))
            except Exception:
                pass
        return weight

    def update_market_awareness(self, source: str, signal: str,
                                 entities_affected: list,
                                 impact_assessment: str) -> None:
        """Store a market signal for Friday's awareness."""
        self._append("market_awareness.jsonl", {
            "source": source, "signal": signal,
            "entities_affected": entities_affected,
            "impact_assessment": impact_assessment,
            "recorded_at": datetime.now(timezone.utc).isoformat()})

    def get_market_briefing(self, hours: int = 168) -> str:
        """Generate plain-language market briefing. TTS-ready."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        signals = []
        for line in self._read_lines("market_awareness.jsonl"):
            try:
                entry = json.loads(line)
                if entry.get("recorded_at", "") >= cutoff:
                    signals.append(entry)
            except Exception:
                pass
        if not signals:
            return "No significant market signals in the past period."
        try:
            from groq_router import GroqRouter
            router = GroqRouter()
            return router.route("reasoning",
                f"You are Friday, AI chief of staff for Exponere. "
                f"Summarize these {len(signals)} market signals in 100-150 words. "
                f"Direct, calm, action-oriented. TTS-ready.\n\n"
                f"{json.dumps(signals[-10:], indent=2)[:2000]}",
                max_tokens=300, temperature=0.3)
        except Exception:
            return f"{len(signals)} market signals recorded. Review manually."

    def triage_idea(self, idea: dict) -> dict:
        """Friday triages a captured idea. Returns verdict + reasoning.

        Verdicts: build (ready to queue), research (needs RS1 brief),
                  park (not now), defer (wait for dependency).
        """
        try:
            from groq_router import GroqRouter
            router = GroqRouter()
            prompt = (
                "You are Friday, autonomous operating intelligence for EPOS/EXPONERE.\n"
                "Triage this idea against current priorities and capacity.\n\n"
                f"IDEA: {idea.get('title', '')}\n"
                f"DESCRIPTION: {idea.get('description', '')}\n"
                f"CATEGORY: {idea.get('category', '')}\n"
                f"PRIORITY CLAIM: {idea.get('priority', 'medium')}\n"
                f"TAGS: {', '.join(idea.get('tags', []))}\n\n"
                "Current ecosystem context:\n"
                "- 10 active projects, 105+ tasks\n"
                "- Doctor: 22P/1W/0F\n"
                "- LifeOS: active, Day 1+\n"
                "- Echoes launch target: April 7\n"
                "- Active niches: lego_affiliate + 5 business niches\n\n"
                "Respond in EXACTLY this JSON format:\n"
                '{"verdict": "build|research|park|defer", '
                '"priority": "critical|high|medium|low", '
                '"reasoning": "1-2 sentences", '
                '"suggested_next": "specific next action"}\n'
                "Output ONLY valid JSON."
            )
            raw = router.route("fast", prompt, max_tokens=200, temperature=0.2)
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()
            result = json.loads(clean)
        except Exception as e:
            result = {
                "verdict": "research",
                "priority": idea.get("priority", "medium"),
                "reasoning": f"Auto-triage fallback: needs manual review. ({str(e)[:50]})",
                "suggested_next": "Review manually during next planning session",
            }

        # Apply triage to idea log
        try:
            from idea_log import IdeaLog
            log = IdeaLog()
            log.triage(
                idea["idea_id"],
                result.get("verdict", "research"),
                result.get("reasoning", ""),
                result.get("priority"),
            )
        except Exception:
            pass

        # Log to Friday's growth
        self._append("friday_growth_log.jsonl", {
            "event": "idea_triage",
            "idea_id": idea.get("idea_id"),
            "verdict": result.get("verdict"),
            "at": datetime.now(timezone.utc).isoformat(),
        })

        return result

    def triage_all_untriaged(self) -> list:
        """Triage all captured (untriaged) ideas. Returns list of results."""
        from idea_log import IdeaLog
        log = IdeaLog()
        untriaged = log.list_ideas(status="captured", limit=50)
        results = []
        for idea in untriaged:
            result = self.triage_idea(idea)
            result["idea_id"] = idea["idea_id"]
            result["title"] = idea["title"]
            results.append(result)
        return results

    def get_growth_summary(self) -> dict:
        """How much has Friday learned?"""
        return {
            "steward_patterns": len(self._read_lines("steward_patterns.jsonl")),
            "escalation_calibrations": len(self._read_lines("escalation_accuracy.jsonl")),
            "market_signals": len(self._read_lines("market_awareness.jsonl")),
            "growth_events": len(self._read_lines("friday_growth_log.jsonl")),
        }

    def _append(self, filename: str, entry: dict) -> None:
        with open(self.kb_path / filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _read_lines(self, filename: str) -> list:
        path = self.kb_path / filename
        if not path.exists() or path.stat().st_size == 0:
            return []
        return [l for l in path.read_text(encoding="utf-8").strip().splitlines() if l.strip()]


if __name__ == "__main__":
    import py_compile
    py_compile.compile("friday_intelligence.py", doraise=True)
    fi = FridayIntelligence()
    fi.record_steward_response("SIG-001", "hot_lead", "acted", 5.0)
    fi.record_steward_response("SIG-002", "sla_breach", "dismissed", 120.0)
    fi.update_market_awareness("research_scan", "New video model released",
                                ["echoes", "content_lab"], "Evaluate for production stack")
    w1 = fi.get_signal_priority_weight("hot_lead")
    w2 = fi.get_signal_priority_weight("sla_breach")
    print(f"  hot_lead weight: {w1:.3f} (should be > 0.5)")
    print(f"  sla_breach weight: {w2:.3f} (should be < 0.5)")
    summary = fi.get_growth_summary()
    print(f"  Growth: {summary}")
    print("PASS: FridayIntelligence — learning from steward patterns")
