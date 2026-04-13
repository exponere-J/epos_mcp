#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/models/model_registry.py — EPOS Model Registry
=====================================================
Constitutional Authority: EPOS Constitution v3.1

30-slot model registry across 5 modalities.
Tracks what is seated, what is pending, and what should be seated next.

Public API:
    reg = ModelRegistry()
    reg.list_slots()                    → list of all 30 slot dicts
    reg.get_slot("A1")                  → single slot dict
    reg.seat_model("A1", config)        → marks seated + publishes event
    reg.unseat_model("A1", reason)      → marks vacant + archives
    reg.get_next_priority()             → next slot to fill
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
REGISTRY_FILE = EPOS_ROOT / "context_vault" / "state" / "model_registry.json"

# ── 30 Slot Definitions ────────────────────────────────────────
# Format: slot_id, modality, role, selected_model, provider, context_window,
#         priority, status, notes
_SLOT_DEFINITIONS: List[Dict[str, Any]] = [
    # ── TEXT / CODE (18 slots) ────────────────────────────────
    {
        "slot_id": "A1", "modality": "code",
        "role": "Primary Script Generator / Sovereign Coding Agent",
        "selected_model": "qwen3-coder-30b-a3b-instruct",
        "provider": "Fireworks AI",
        "context_window": "262K",
        "priority": "P0",
        "status": "harness_ready",
        "replaces": "Desktop CODE (legacy bootstrap)",
        "notes": "SCC operational via OpenRouter. Model seated.",
    },
    {
        "slot_id": "A2", "modality": "text",
        "role": "Diagnostic Reasoning — TTLG Scout",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P0.5",
        "status": "pending",
        "replaces": "llama-3.3-70b-versatile (Groq)",
        "notes": "TTLG Scout phase. Replace after Fireworks key.",
    },
    {
        "slot_id": "A3", "modality": "text",
        "role": "Diagnostic Reasoning — TTLG Thinker",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P0.5",
        "status": "pending",
        "replaces": "llama-3.3-70b-versatile (Groq)",
        "notes": "TTLG Thinker constitutional evaluation.",
    },
    {
        "slot_id": "A4", "modality": "text",
        "role": "Diagnostic Reasoning — TTLG Surgeon",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P0.5",
        "status": "pending",
        "replaces": "llama-3.3-70b-versatile (Groq)",
        "notes": "TTLG Surgeon refactor proposals.",
    },
    {
        "slot_id": "A5", "modality": "text",
        "role": "Diagnostic Reasoning — TTLG Analyst",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P0.5",
        "status": "pending",
        "replaces": "llama-3.3-70b-versatile (Groq)",
        "notes": "TTLG Analyst verification + benchmarking.",
    },
    {
        "slot_id": "A6", "modality": "text",
        "role": "General Reasoning — EPOS Core Services",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P1",
        "status": "pending",
        "replaces": "llama-3.3-70b-versatile (Groq)",
        "notes": "epos_daemon, friday orchestration, governance.",
    },
    {
        "slot_id": "A7", "modality": "text",
        "role": "Classification / Routing",
        "selected_model": "qwen3-8b",
        "provider": "Fireworks AI",
        "context_window": "32K",
        "priority": "P1",
        "status": "pending",
        "replaces": "llama-3.1-8b-instant (Groq)",
        "notes": "Fast classification: tags, routes, summarization.",
    },
    {
        "slot_id": "A8", "modality": "text",
        "role": "Content Generation — Avatar-Calibrated",
        "selected_model": "qwen3-32b + avatar-lora",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P1",
        "status": "pending",
        "replaces": "llama-3.3-70b-versatile (Groq)",
        "notes": "Content Lab. LoRA adapter per avatar after 30 days data.",
    },
    {
        "slot_id": "A9", "modality": "text",
        "role": "Morning Briefing Narrative Generator",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P2",
        "status": "pending",
        "replaces": "None (unwired slot)",
        "notes": "Converts 22 metrics → executive prose for 06:00 briefing.",
    },
    {
        "slot_id": "A10", "modality": "text",
        "role": "Anomaly Root Cause Explanation",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P2",
        "status": "pending",
        "replaces": "None (unwired slot)",
        "notes": "Explains why metric moved, not just that it moved.",
    },
    {
        "slot_id": "A11", "modality": "text",
        "role": "Research Scanner + Market Brief Generation",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P2",
        "status": "wired_groq",
        "replaces": "llama-3.3-70b-versatile (Groq) — already wired",
        "notes": "friday/skills/research_scanner.py. Upgrade to Fireworks for context.",
    },
    {
        "slot_id": "A12", "modality": "text",
        "role": "Thread Staleness Semantic Classifier",
        "selected_model": "qwen3-8b",
        "provider": "Fireworks AI",
        "context_window": "32K",
        "priority": "P2",
        "status": "pending",
        "replaces": "None (rules-based, unwired)",
        "notes": "Distinguishes intentional deferral from forgotten threads.",
    },
    {
        "slot_id": "A13", "modality": "text",
        "role": "FOTW Engagement Intent Classifier",
        "selected_model": "qwen3-8b",
        "provider": "Fireworks AI",
        "context_window": "32K",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (keyword rules, unwired)",
        "notes": "Question vs skepticism vs enthusiasm vs 'not for me'.",
    },
    {
        "slot_id": "A14", "modality": "text",
        "role": "AAR Insight Abstractor",
        "selected_model": "qwen3-32b",
        "provider": "Fireworks AI",
        "context_window": "131K",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (regex/keyword, unwired)",
        "notes": "Extracts the ONE insight that matters from each AAR.",
    },
    {
        "slot_id": "A15", "modality": "text",
        "role": "Long-Document RAG / Research Frontier",
        "selected_model": "llama-4-scout-17b-16e-instruct",
        "provider": "Fireworks AI",
        "context_window": "10M",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (unwired)",
        "notes": "10M context for deep document analysis, FOTW corpora.",
    },
    {
        "slot_id": "A16", "modality": "text",
        "role": "Scout Depth Router",
        "selected_model": "qwen3-8b",
        "provider": "Fireworks AI",
        "context_window": "32K",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (always full scan, unwired)",
        "notes": "Quick health check vs deep overhaul routing decision.",
    },
    {
        "slot_id": "A17", "modality": "text",
        "role": "SOP Semantic Drift Detector",
        "selected_model": "qwen3-8b",
        "provider": "Fireworks AI",
        "context_window": "32K",
        "priority": "P4",
        "status": "pending",
        "replaces": "None (line-by-line compare, unwired)",
        "notes": "Detects when process changed but written SOP hasn't.",
    },
    {
        "slot_id": "A18", "modality": "text",
        "role": "Fallback Reasoning (Groq tier)",
        "selected_model": "llama-3.3-70b-versatile",
        "provider": "Groq (free tier)",
        "context_window": "128K",
        "priority": "P0 (fallback)",
        "status": "seated",
        "replaces": "N/A — tertiary fallback",
        "notes": "Active now. Stays as tertiary behind Fireworks.",
    },
    # ── IMAGE (3 slots) ───────────────────────────────────────
    {
        "slot_id": "V1", "modality": "image",
        "role": "Brand Image Generation",
        "selected_model": "FLUX.1-schnell + brand-lora",
        "provider": "Local (Ollama / ComfyUI)",
        "context_window": "N/A",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (new capability)",
        "notes": "Brand LoRA after visual identity lock.",
    },
    {
        "slot_id": "V2", "modality": "image",
        "role": "Content Image Generation",
        "selected_model": "FLUX.1-schnell",
        "provider": "Local",
        "context_window": "N/A",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (new capability)",
        "notes": "Content Lab posts, thumbnails.",
    },
    {
        "slot_id": "V3", "modality": "image",
        "role": "Video Thumbnail / Storyboard",
        "selected_model": "FLUX.1-schnell",
        "provider": "Local",
        "context_window": "N/A",
        "priority": "P4",
        "status": "pending",
        "replaces": "None (new capability)",
        "notes": "Feeds Wan 2.2 video pipeline.",
    },
    # ── VIDEO (2 slots) ───────────────────────────────────────
    {
        "slot_id": "W1", "modality": "video",
        "role": "Hero Content Video",
        "selected_model": "Wan-2.2",
        "provider": "Local (GPU)",
        "context_window": "N/A",
        "priority": "P4",
        "status": "pending",
        "replaces": "None (new capability)",
        "notes": "Long-form brand video. Requires GPU.",
    },
    {
        "slot_id": "W2", "modality": "video",
        "role": "Short-Form / Reels",
        "selected_model": "Wan-2.2",
        "provider": "Local (GPU)",
        "context_window": "N/A",
        "priority": "P4",
        "status": "pending",
        "replaces": "None (new capability)",
        "notes": "Social short-form content.",
    },
    # ── AUDIO (1 slot) ────────────────────────────────────────
    {
        "slot_id": "S1", "modality": "audio",
        "role": "TTS Voiceover / Briefing Audio",
        "selected_model": "TBD",
        "provider": "TBD",
        "context_window": "N/A",
        "priority": "P5",
        "status": "research_required",
        "replaces": "None (new capability)",
        "notes": "Voice-native output for Friday briefings. Accessibility priority.",
    },
    # ── EMBEDDING (3 slots) ───────────────────────────────────
    {
        "slot_id": "E1", "modality": "embedding",
        "role": "Vault Encoder (Context Vault semantic search)",
        "selected_model": "nomic-embed-text",
        "provider": "Ollama (local)",
        "context_window": "8K",
        "priority": "P2",
        "status": "pending",
        "replaces": "None (unwired)",
        "notes": "Pull: docker exec epos-ollama ollama pull nomic-embed-text",
    },
    {
        "slot_id": "E2", "modality": "embedding",
        "role": "Semantic Search across AAR + SOP corpus",
        "selected_model": "bge-m3",
        "provider": "Ollama (local)",
        "context_window": "8K",
        "priority": "P2",
        "status": "pending",
        "replaces": "None (unwired)",
        "notes": "Multilingual, strong zero-shot retrieval.",
    },
    {
        "slot_id": "E3", "modality": "embedding",
        "role": "Avatar Drift Embedding Tracker",
        "selected_model": "nomic-embed-text",
        "provider": "Ollama (local)",
        "context_window": "8K",
        "priority": "P3",
        "status": "pending",
        "replaces": "None (structural, unwired)",
        "notes": "Embeds avatar response history → detects behavioral drift.",
    },
    # ── SPECIALIZED / CUSTOM FINE-TUNED (3 slots) ─────────────
    {
        "slot_id": "C1", "modality": "text-specialized",
        "role": "Constitutional Classifier",
        "selected_model": "qwen3-8b + constitutional-lora",
        "provider": "Local (QLoRA fine-tune)",
        "context_window": "32K",
        "priority": "P6",
        "status": "awaiting_training_data",
        "replaces": "governance_gate.py ruleset (20+ rules)",
        "notes": "Train after 30 days of gate decisions. Learns constitutional intent.",
    },
    {
        "slot_id": "I1", "modality": "text-specialized",
        "role": "Impact Predictor",
        "selected_model": "qwen3-8b + impact-lora",
        "provider": "Local (QLoRA fine-tune)",
        "context_window": "32K",
        "priority": "P6",
        "status": "awaiting_training_data",
        "replaces": "Rules-based impact scoring (heuristic)",
        "notes": "Train on AAR before/after metrics after 30 missions.",
    },
    {
        "slot_id": "P1", "modality": "text-specialized",
        "role": "Pattern Signal Discriminator",
        "selected_model": "qwen3-8b + pattern-lora",
        "provider": "Local (QLoRA fine-tune)",
        "context_window": "32K",
        "priority": "P6",
        "status": "awaiting_training_data",
        "replaces": "Count-based pattern promotion (3+ occurrences)",
        "notes": "Train on constitution changelog + mission outcomes.",
    },
]

# Priority order for seating
_PRIORITY_ORDER = ["P0", "P0.5", "P1", "P2", "P3", "P4", "P5", "P6"]
_SEATEABLE_STATUSES = {"pending", "harness_ready", "research_required"}


class ModelRegistry:
    """
    EPOS 30-slot model registry.
    Persists seating state to context_vault/state/model_registry.json.
    Every seat/unseat action publishes to the Event Bus.
    """

    def __init__(self):
        self._slots: Dict[str, Dict] = {}
        self._load()

        self._bus = None
        try:
            from epos_event_bus import EPOSEventBus
            self._bus = EPOSEventBus()
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────

    def list_slots(self) -> List[Dict[str, Any]]:
        """Return all 30 slots with current status."""
        return list(self._slots.values())

    def get_slot(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Return a single slot dict, or None."""
        return self._slots.get(slot_id.upper())

    def seat_model(self, slot_id: str, model_config: Optional[Dict] = None) -> Dict:
        """
        Mark a slot as seated. Optionally override model config fields.
        Publishes model.seated event.
        """
        sid = slot_id.upper()
        if sid not in self._slots:
            return {"error": f"Slot {sid} not found"}

        slot = self._slots[sid]
        if model_config:
            slot.update(model_config)
        slot["status"] = "seated"
        slot["seated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

        self._publish("model.seated", {"slot_id": sid, "model": slot["selected_model"]})

        # Update organism state
        try:
            from epos.state.universal_state_graph import OrganismState
            state = OrganismState()
            seated = state.query("intelligence_layer.models_seated") or []
            if slot["selected_model"] not in seated:
                seated.append(slot["selected_model"])
                state.update("intelligence_layer.models_seated", seated)
        except Exception:
            pass

        return {"status": "seated", "slot": slot}

    def unseat_model(self, slot_id: str, reason: str = "manually unseated") -> Dict:
        """Mark a slot vacant and archive previous config."""
        sid = slot_id.upper()
        if sid not in self._slots:
            return {"error": f"Slot {sid} not found"}

        slot = self._slots[sid]
        archive = {
            "slot_id": sid,
            "model": slot["selected_model"],
            "unseated_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }
        slot["status"] = "pending"
        slot["last_unseated"] = archive
        self._save()

        self._publish("model.unseated", archive)
        return {"status": "unseated", "archive": archive}

    def get_next_priority(self) -> Optional[Dict[str, Any]]:
        """Return the highest-priority slot that is not yet seated."""
        for priority in _PRIORITY_ORDER:
            for slot in self._slots.values():
                if slot["priority"] == priority and slot["status"] in _SEATEABLE_STATUSES:
                    return slot
        return None

    def summary(self) -> Dict[str, Any]:
        """Return counts by status."""
        counts: Dict[str, int] = {}
        for slot in self._slots.values():
            counts[slot["status"]] = counts.get(slot["status"], 0) + 1
        return {
            "total": len(self._slots),
            "by_status": counts,
            "next_priority": (self.get_next_priority() or {}).get("slot_id"),
        }

    # ── Internals ─────────────────────────────────────────────

    def _load(self) -> None:
        """Load from file if it exists, otherwise seed from definitions."""
        if REGISTRY_FILE.exists():
            try:
                saved = json.loads(REGISTRY_FILE.read_text())
                self._slots = {s["slot_id"]: s for s in saved}
                # Merge any new slot definitions not yet in the file
                for defn in _SLOT_DEFINITIONS:
                    if defn["slot_id"] not in self._slots:
                        self._slots[defn["slot_id"]] = dict(defn)
                return
            except Exception:
                pass
        # First run — seed from definitions
        self._slots = {d["slot_id"]: dict(d) for d in _SLOT_DEFINITIONS}
        self._save()

    def _save(self) -> None:
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = REGISTRY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(list(self._slots.values()), indent=2))
        tmp.replace(REGISTRY_FILE)

    def _publish(self, event_type: str, payload: Dict) -> None:
        if self._bus:
            try:
                self._bus.publish(event_type, payload, source_module="model_registry")
            except Exception:
                pass


# ── Self-test ─────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(
            __import__("epos.models.model_registry", fromlist=["REGISTRY_FILE"]),
            "REGISTRY_FILE",
            Path(tmp) / "state" / "model_registry.json",
        ):
            reg = ModelRegistry()

            assert len(reg.list_slots()) == 30, f"Expected 30 slots, got {len(reg.list_slots())}"
            print(f"Total slots: {len(reg.list_slots())} ✓")

            next_p = reg.get_next_priority()
            assert next_p is not None
            print(f"Next priority: {next_p['slot_id']} ({next_p['priority']}) ✓")

            result = reg.seat_model("A18")
            assert result["status"] == "seated"
            print(f"seat_model A18: {result['status']} ✓")

            unseat = reg.unseat_model("A18", "test")
            assert unseat["status"] == "unseated"
            print(f"unseat_model A18: {unseat['status']} ✓")

            summary = reg.summary()
            print(f"Summary: {summary} ✓")

    print("\nPASS: ModelRegistry — all assertions passed")
