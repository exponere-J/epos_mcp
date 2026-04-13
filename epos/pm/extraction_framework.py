#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/pm/extraction_framework.py — PM Extraction Framework
==========================================================
Constitutional Authority: EPOS Constitution v3.1

Converts any conversation string into structured PM elements routed to
the project knowledge store and PM surface (Google Sheets or local JSON).

Prevents uninformed assumptions. Compounds work value. Creates traceable
inputs into every downstream system.

Element types extracted:
  action_item     — Explicit task someone must do
  decision        — A conclusion reached or direction chosen
  idea            — Concept worth capturing for later evaluation
  research_q      — Open question requiring investigation
  blocker         — Something preventing progress
  learning        — Insight or pattern worth remembering
  dependency      — One item waiting on another

Public API:
    result = extract_to_checklist(conversation, priority="P0")
    result["checklist"]        → list of structured items
    result["by_type"]          → items grouped by element type
    result["metadata"]         → extraction metadata

    save_to_pm_surface(result) → writes to local JSON PM surface
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
PM_SURFACE_FILE = EPOS_ROOT / "context_vault" / "pm" / "pm_surface.jsonl"
PROJECT_KNOWLEDGE_FILE = EPOS_ROOT / "context_vault" / "pm" / "project_knowledge.jsonl"
EXTRACTION_LOG = EPOS_ROOT / "context_vault" / "pm" / "extractions.jsonl"


# ── Element type definitions ───────────────────────────────────

ELEMENT_TYPES = {
    "action_item": {
        "keywords": ["need to", "we need", "must", "should", "fix", "build", "create",
                     "add", "update", "deploy", "implement", "configure", "run", "execute"],
        "id_prefix": "ACT",
        "owner": "sovereign_agent",
    },
    "decision": {
        "keywords": ["decision:", "decided", "we decided", "going with", "choosing",
                     "replace", "use", "adopt", "switching to", "confirmed"],
        "id_prefix": "DEC",
        "owner": "jamie",
    },
    "idea": {
        "keywords": ["idea", "what if", "could we", "imagine", "consider", "potential",
                     "eventually", "someday", "vision", "concept"],
        "id_prefix": "IDR",
        "owner": "jamie",
    },
    "research_q": {
        "keywords": ["research", "investigate", "how does", "why does", "what is",
                     "understand", "figure out", "look into", "question", "explore"],
        "id_prefix": "RES",
        "owner": "research_pipeline",
    },
    "blocker": {
        "keywords": ["blocked", "blocking", "waiting on", "can't proceed", "depends on",
                     "prerequisite", "gated on", "requires first"],
        "id_prefix": "BLK",
        "owner": "jamie",
    },
    "learning": {
        "keywords": ["learned", "discovered", "found out", "turns out", "insight",
                     "pattern", "lesson", "note:", "important:", "remember"],
        "id_prefix": "LRN",
        "owner": "knowledge_flywheel",
    },
    "dependency": {
        "keywords": ["depends on", "requires", "after", "before we can", "blocked by",
                     "prerequisite", "first need"],
        "id_prefix": "DEP",
        "owner": "sovereign_agent",
    },
}


# ── Core extraction ────────────────────────────────────────────

def extract_to_checklist(
    conversation: str,
    priority: str = "P0",
    source: str = "manual",
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract structured PM elements from a conversation string.

    Uses:
    1. LLM-based extraction if engine.llm_client is available
    2. Rules-based keyword extraction as fallback

    Returns a structured result dict with checklist, by_type, metadata.
    """
    if not conversation or not conversation.strip():
        return _empty_result(priority, source, session_id)

    sid = session_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    # Try LLM extraction first
    elements = _extract_via_llm(conversation, priority)

    # Fallback: rules-based extraction
    if not elements:
        elements = _extract_via_rules(conversation)

    # Build structured checklist
    checklist = _build_checklist(elements, priority)

    result = {
        "extraction_id": f"EXT-{sid}",
        "priority": priority,
        "source": source,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "input_length": len(conversation),
        "total_items": len(checklist),
        "checklist": checklist,
        "by_type": _group_by_type(checklist),
        "metadata": {
            "extraction_method": "llm" if elements else "rules",
            "session_id": sid,
        },
    }

    # Persist
    _append_to_log(result)
    _append_to_project_knowledge(result)

    # Publish to Event Bus
    _publish_extraction_event(result)

    return result


def save_to_pm_surface(result: Dict[str, Any]) -> Path:
    """
    Write checklist to the PM surface (local JSONL).
    Returns the path written to.
    """
    PM_SURFACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PM_SURFACE_FILE, "a") as f:
        f.write(json.dumps(result) + "\n")
    return PM_SURFACE_FILE


# ── LLM extraction ────────────────────────────────────────────

def _extract_via_llm(conversation: str, priority: str) -> List[Dict]:
    """
    Use the EPOS LLM client to extract structured elements.
    Returns list of element dicts, or empty list on failure.
    """
    try:
        from engine.llm_client import complete
        prompt = _build_extraction_prompt(conversation, priority)
        response = complete(
            system=_EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2,
        )
        return _parse_llm_response(response)
    except Exception:
        return []


_EXTRACTION_SYSTEM_PROMPT = """You are an EPOS PM Extraction Engine.
Extract structured project management elements from conversations.

Output ONLY valid JSON — a list of objects with these fields:
  type: one of: action_item, decision, idea, research_q, blocker, learning, dependency
  description: concise, imperative sentence (max 100 chars)
  owner: who should action this (jamie, sovereign_agent, research_pipeline, knowledge_flywheel)
  urgency: high, medium, low
  notes: any relevant context (optional, max 100 chars)

Example output:
[
  {"type": "action_item", "description": "Fix reactor position file byte offset tracking", "owner": "sovereign_agent", "urgency": "high", "notes": "causes daemon to reprocess full event bus on restart"},
  {"type": "decision", "description": "Replace Llama 3.3 with Qwen3-32B in TTLG", "owner": "jamie", "urgency": "medium", "notes": "same family as coding model, single fine-tune pipeline"},
  {"type": "research_q", "description": "How does Fireworks handle context window scaling", "owner": "research_pipeline", "urgency": "low", "notes": ""}
]

Output ONLY the JSON array, no other text."""


def _build_extraction_prompt(conversation: str, priority: str) -> str:
    # Truncate very long conversations to prevent token overflow
    max_chars = 8000
    if len(conversation) > max_chars:
        conversation = conversation[:max_chars] + "\n\n[... truncated ...]"

    return f"""Priority context: {priority}

Conversation to extract from:
---
{conversation}
---

Extract all actionable elements as JSON."""


def _parse_llm_response(response: str) -> List[Dict]:
    """Parse LLM JSON response, handling markdown code blocks."""
    text = response.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    # Find JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return []


# ── Rules-based extraction ─────────────────────────────────────

def _extract_via_rules(conversation: str) -> List[Dict]:
    """
    Keyword-based extraction fallback.
    Splits conversation into sentences and classifies each.
    """
    elements = []
    sentences = re.split(r"(?<=[.!?])\s+|(?:\n+)", conversation)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue

        matched_type = _classify_sentence(sentence)
        if matched_type:
            defn = ELEMENT_TYPES[matched_type]
            elements.append({
                "type": matched_type,
                "description": sentence[:100],
                "owner": defn["owner"],
                "urgency": "medium",
                "notes": "",
            })

    return elements


def _classify_sentence(sentence: str) -> Optional[str]:
    """Return the best-matching element type for a sentence, or None."""
    lower = sentence.lower()
    best_type = None
    best_score = 0

    for elem_type, defn in ELEMENT_TYPES.items():
        score = sum(1 for kw in defn["keywords"] if kw in lower)
        if score > best_score:
            best_score = score
            best_type = elem_type

    return best_type if best_score > 0 else None


# ── Checklist builder ─────────────────────────────────────────

def _build_checklist(elements: List[Dict], priority: str) -> List[Dict]:
    """Convert raw elements to structured checklist items with IDs."""
    checklist = []
    type_counters: Dict[str, int] = {}

    for elem in elements:
        elem_type = elem.get("type", "action_item")
        if elem_type not in ELEMENT_TYPES:
            elem_type = "action_item"

        defn = ELEMENT_TYPES[elem_type]
        type_counters[elem_type] = type_counters.get(elem_type, 0) + 1
        count = type_counters[elem_type]

        item = {
            "id": f"{priority}.{defn['id_prefix']}-{count:03d}",
            "type": elem_type,
            "description": elem.get("description", "")[:100],
            "owner": elem.get("owner", defn["owner"]),
            "urgency": elem.get("urgency", "medium"),
            "status": "pending",
            "notes": elem.get("notes", "")[:100],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        checklist.append(item)

    return checklist


def _group_by_type(checklist: List[Dict]) -> Dict[str, List[Dict]]:
    """Group checklist items by element type."""
    groups: Dict[str, List] = {}
    for item in checklist:
        t = item["type"]
        if t not in groups:
            groups[t] = []
        groups[t].append(item)
    return groups


# ── Persistence ───────────────────────────────────────────────

def _append_to_log(result: Dict) -> None:
    EXTRACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EXTRACTION_LOG, "a") as f:
        f.write(json.dumps(result) + "\n")


def _append_to_project_knowledge(result: Dict) -> None:
    """
    Append structured inputs to project knowledge store.
    Prevents uninformed assumptions in future sessions.
    """
    PROJECT_KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "type": "pm_extraction",
        "extraction_id": result["extraction_id"],
        "priority": result["priority"],
        "extracted_at": result["extracted_at"],
        "items": result["checklist"],
    }
    with open(PROJECT_KNOWLEDGE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _publish_extraction_event(result: Dict) -> None:
    try:
        from epos_event_bus import EPOSEventBus
        bus = EPOSEventBus()
        bus.publish(
            "pm.extraction.complete",
            {
                "extraction_id": result["extraction_id"],
                "total_items": result["total_items"],
                "priority": result["priority"],
            },
            source_module="extraction_framework",
        )
    except Exception:
        pass


def _empty_result(priority: str, source: str, session_id: Optional[str]) -> Dict:
    return {
        "extraction_id": f"EXT-{session_id or 'empty'}",
        "priority": priority,
        "source": source,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "input_length": 0,
        "total_items": 0,
        "checklist": [],
        "by_type": {},
        "metadata": {"extraction_method": "none", "session_id": session_id},
    }


# ── Self-test ─────────────────────────────────────────────────

if __name__ == "__main__":
    TEST_CONVERSATION = """
    We need to fix the reactor position file. The daemon reprocesses the full
    event bus on restart because the position file is missing.

    Also, research how Fireworks handles context window scaling for Qwen3-Coder.

    Decision: replace Llama with Qwen3-32B in TTLG. Same family as the coding
    model means one fine-tuning pipeline serves both.

    I had an idea — what if we built a visual dashboard showing the organism state
    in real time? It could use the universal_state_graph as the data source.

    We are blocked on the SCC proxy route because Groq free tier is only
    12k TPM which is 6x too small for the SCC context window.

    Learned: LiteLLM's main-latest image enables spend logging by default which
    requires a database. Disable with disable_spend_logs: true.
    """

    result = extract_to_checklist(TEST_CONVERSATION, priority="P0")

    assert result["total_items"] > 0, "No items extracted"
    print(f"Extracted {len(result['checklist'])} items")

    for item in result["checklist"]:
        print(f"  {item['id']}: [{item['type']}] {item['description'][:60]}")

    assert "checklist" in result
    assert "by_type" in result
    assert result["extraction_id"].startswith("EXT-")
    print(f"\nBy type: {list(result['by_type'].keys())}")
    print("\nPASS: extract_to_checklist — all assertions passed")
