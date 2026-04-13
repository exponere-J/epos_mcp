#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/ccp/extractor.py — CCP Element Extraction Engine
======================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

Extracts 9 business element types from raw text using sentence-level
analysis with keyword heuristics. Returns ExtractedElement list with
raw confidence scores for downstream scoring refinement.

Element types:
    1. action_item          — something that needs to be done
    2. decision             — a choice made or to be made
    3. research_question    — something needing investigation
    4. idea                 — a concept worth exploring
    5. client_insight       — information about a client/prospect
    6. content_seed         — raw material for content creation
    7. learning_moment      — something the organism should remember
    8. constitutional_proposal — a suggested rule change
    9. blocker              — something preventing progress
"""

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Element Type Enum
# ──────────────────────────────────────────────────────────────────────────────

class ElementType(str, Enum):
    ACTION_ITEM           = "action_item"
    DECISION              = "decision"
    RESEARCH_QUESTION     = "research_question"
    IDEA                  = "idea"
    CLIENT_INSIGHT        = "client_insight"
    CONTENT_SEED          = "content_seed"
    LEARNING_MOMENT       = "learning_moment"
    CONSTITUTIONAL_PROPOSAL = "constitutional_proposal"
    BLOCKER               = "blocker"


# ──────────────────────────────────────────────────────────────────────────────
# Routing destinations per type
# ──────────────────────────────────────────────────────────────────────────────

SUGGESTED_DESTINATIONS = {
    ElementType.ACTION_ITEM:             "context_vault/pm/action_items.json",
    ElementType.DECISION:                "context_vault/pm/decisions.json",
    ElementType.RESEARCH_QUESTION:       "context_vault/pm/research_queue.json",
    ElementType.IDEA:                    "context_vault/pm/idea_pipeline.json",
    ElementType.CLIENT_INSIGHT:          "context_vault/pm/client_insights.json",
    ElementType.CONTENT_SEED:            "content_lab/inbox",
    ElementType.LEARNING_MOMENT:         "context_vault/training/",
    ElementType.CONSTITUTIONAL_PROPOSAL: "governance/proposals/",
    ElementType.BLOCKER:                 "context_vault/pm/blockers.json",
}


# ──────────────────────────────────────────────────────────────────────────────
# Keyword patterns per element type
# Format: (pattern, base_confidence)
# ──────────────────────────────────────────────────────────────────────────────

KEYWORD_PATTERNS: dict = {
    ElementType.ACTION_ITEM: [
        (r"\bTODO[:\s]",                        0.97),
        (r"\bACTION[:\s]",                      0.96),
        (r"\bfollow[\s\-]up\b",                 0.91),
        (r"\b(need|needs) to\b",                0.82),
        (r"\b(must|should|shall|will)\s+\w+",   0.78),
        (r"\b(assign|assigned|delegate)\b",      0.80),
        (r"\b(schedule|book|send|write|build|fix|update|deploy|review)\b",  0.72),
        (r"\bby (end of|EOD|Monday|Tuesday|Wednesday|Thursday|Friday|next week)\b", 0.88),
        (r"\breminder[:\s]",                    0.90),
    ],
    ElementType.DECISION: [
        (r"\bwe decided\b",                     0.95),
        (r"\bwe['']re going with\b",            0.94),
        (r"\bdecision[:\s]",                    0.96),
        (r"\bgoing forward\b",                  0.85),
        (r"\bwe['']ll (use|go|adopt|move|stick)\b", 0.87),
        (r"\bchose\b",                          0.83),
        (r"\bfinal answer\b",                   0.92),
        (r"\bagreed[:\s]",                      0.88),
        (r"\bresolved[:\s]",                    0.86),
        (r"\bapproved[:\s]",                    0.91),
    ],
    ElementType.RESEARCH_QUESTION: [
        (r"\bwe need to research\b",            0.93),
        (r"\binvestigate\b",                    0.88),
        (r"\bresearch[:\s]",                    0.89),
        (r"\bworth looking into\b",             0.87),
        (r"\bopen question[:\s]",               0.91),
        (r"\bI wonder\b",                       0.75),
        (r"\bhow does\b",                       0.68),
        (r"\bwhat if\b",                        0.65),
        (r"\bunknown[:\s]",                     0.82),
        (r"\bfind out\b",                       0.79),
        (r"\bwhy (is|does|did|would)\b",        0.70),
    ],
    ElementType.IDEA: [
        (r"\bIDEA[:\s]",                        0.97),
        (r"\bwhat if we\b",                     0.82),
        (r"\bwe could\b",                       0.74),
        (r"\bwhat about\b",                     0.71),
        (r"\bwould be (cool|interesting|worth)\b", 0.80),
        (r"\bconcept[:\s]",                     0.84),
        (r"\bpotentially\b",                    0.68),
        (r"\bimagine if\b",                     0.85),
        (r"\bexplore\b",                        0.70),
        (r"\bbrainstorm\b",                     0.86),
    ],
    ElementType.CLIENT_INSIGHT: [
        (r"\bclient (said|mentioned|asked|wants|needs|told us)\b",  0.92),
        (r"\bprospect\b",                       0.78),
        (r"\bcustomer (pain|feedback|said|wants)\b",  0.90),
        (r"\bthey (said|mentioned|told|need|want)\b", 0.74),
        (r"\bpain point\b",                     0.88),
        (r"\bclient insight[:\s]",              0.97),
        (r"\b(their|their team|their process)\b", 0.62),
        (r"\bin their words\b",                 0.88),
    ],
    ElementType.CONTENT_SEED: [
        (r"\bcontent (idea|seed|angle|hook)[:\s]",  0.96),
        (r"\bwould make (a|an) (good|great|excellent) post\b",  0.91),
        (r"\bstory[:\s]",                       0.72),
        (r"\bhook[:\s]",                        0.80),
        (r"\bvideo (idea|concept|topic)[:\s]",  0.90),
        (r"\bepisode (idea|topic)[:\s]",        0.88),
        (r"\bwrite about\b",                    0.77),
        (r"\bpublish\b",                        0.68),
        (r"\bnewsletter\b",                     0.74),
        (r"\bthread[:\s]",                      0.71),
    ],
    ElementType.LEARNING_MOMENT: [
        (r"\blearning[:\s]",                    0.96),
        (r"\bI (learned|realized|discovered)\b", 0.90),
        (r"\bkey (insight|takeaway|lesson)\b",  0.89),
        (r"\bremember (that|this|for next)\b",  0.88),
        (r"\bnote to self\b",                   0.94),
        (r"\binsight[:\s]",                     0.80),
        (r"\btakeaway[:\s]",                    0.90),
        (r"\bmistake I made\b",                 0.87),
        (r"\bnever again\b",                    0.80),
        (r"\bthe organism (should|must|needs to) know\b",  0.95),
    ],
    ElementType.CONSTITUTIONAL_PROPOSAL: [
        (r"\bconstitutional (proposal|change|update|rule)[:\s]",  0.97),
        (r"\bwe should (always|never|require|enforce)\b",  0.84),
        (r"\badd (to|a) (rule|governance|constitution|policy)\b", 0.86),
        (r"\bnew rule[:\s]",                    0.88),
        (r"\bpolicy change[:\s]",               0.89),
        (r"\bshould be (required|mandatory|forbidden|prohibited)\b", 0.82),
        (r"\bgovernance\b",                     0.72),
        (r"\bconstitution (v\d|should|must)\b", 0.90),
    ],
    ElementType.BLOCKER: [
        (r"\bBLOCKER[:\s]",                     0.97),
        (r"\bblocked (by|on|until)\b",          0.93),
        (r"\bblocking\b",                       0.88),
        (r"\bcan['']t (proceed|continue|move forward) (until|without)\b", 0.91),
        (r"\bwaiting (on|for)\b",               0.78),
        (r"\bdependency[:\s]",                  0.82),
        (r"\bstuck (on|until|at)\b",            0.85),
        (r"\bimpediment[:\s]",                  0.90),
        (r"\bpreventing\b",                     0.82),
        (r"\bgate[d]? (by|on)\b",               0.79),
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExtractedElement:
    """A single business element extracted from text."""
    element_id: str
    type: ElementType
    content: str
    confidence: float                      # raw heuristic confidence
    source_capture_id: Optional[str]       # links back to raw capture
    suggested_destination: str
    context_refs: List[str] = field(default_factory=list)
    matched_pattern: Optional[str] = None  # which pattern fired
    sentence_index: int = 0               # position in source text
    needs_llm_review: bool = False         # flagged for LLM classification

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "type": self.type.value,
            "content": self.content,
            "confidence": round(self.confidence, 4),
            "source_capture_id": self.source_capture_id,
            "suggested_destination": self.suggested_destination,
            "context_refs": self.context_refs,
            "matched_pattern": self.matched_pattern,
            "sentence_index": self.sentence_index,
            "needs_llm_review": self.needs_llm_review,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Sentence splitter
# ──────────────────────────────────────────────────────────────────────────────

def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving list items and bullets."""
    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    sentences = []
    # Split on newlines first (each line may be its own item)
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Further split long lines on sentence boundaries
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', line)
        sentences.extend(p.strip() for p in parts if p.strip())

    return sentences


# ──────────────────────────────────────────────────────────────────────────────
# Core extraction
# ──────────────────────────────────────────────────────────────────────────────

def _classify_sentence(sentence: str) -> List[tuple]:
    """
    Check sentence against all keyword patterns.
    Returns list of (ElementType, confidence, matched_pattern) sorted by confidence desc.
    """
    matches = []
    sentence_lower = sentence.lower()

    for element_type, patterns in KEYWORD_PATTERNS.items():
        best_confidence = 0.0
        best_pattern = None
        for pattern_str, base_conf in patterns:
            if re.search(pattern_str, sentence, re.IGNORECASE):
                if base_conf > best_confidence:
                    best_confidence = base_conf
                    best_pattern = pattern_str

        if best_confidence > 0:
            matches.append((element_type, best_confidence, best_pattern))

    # Sort by confidence descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def extract_elements(
    text: str,
    source_capture_id: Optional[str] = None,
    min_confidence: float = 0.60,
    max_per_sentence: int = 2,
) -> List[ExtractedElement]:
    """
    Extract business elements from raw text.

    Splits text into sentences, classifies each sentence against 9
    element types using keyword heuristics. Returns all matches above
    min_confidence threshold.

    Args:
        text: Raw input text (transcript, paste, FOTW capture, etc.)
        source_capture_id: ID of the raw capture this text came from
        min_confidence: Minimum heuristic confidence to include
        max_per_sentence: Max element types to extract per sentence

    Returns:
        List of ExtractedElement (may include multiple per sentence if
        sentence triggers multiple pattern types)
    """
    if not text or not text.strip():
        return []

    sentences = _split_sentences(text)
    elements: List[ExtractedElement] = []

    for idx, sentence in enumerate(sentences):
        if len(sentence) < 8:  # too short to be meaningful
            continue

        matches = _classify_sentence(sentence)
        if not matches:
            continue

        # Take top N matches per sentence
        for element_type, confidence, pattern in matches[:max_per_sentence]:
            if confidence < min_confidence:
                continue

            destination = SUGGESTED_DESTINATIONS.get(element_type, "context_vault/pm/")
            needs_llm = 0.60 <= confidence < 0.90

            element = ExtractedElement(
                element_id=f"ELM-{uuid.uuid4().hex[:12].upper()}",
                type=element_type,
                content=sentence,
                confidence=confidence,
                source_capture_id=source_capture_id,
                suggested_destination=destination,
                matched_pattern=pattern,
                sentence_index=idx,
                needs_llm_review=needs_llm,
            )
            elements.append(element)

    return elements


def extract_from_capture(capture_path: str) -> List[ExtractedElement]:
    """
    Load a raw capture JSON file and extract elements from its transcript.

    Args:
        capture_path: Path to capture .json file in context_vault/raw_captures/

    Returns:
        List of ExtractedElement
    """
    import json
    path = Path(capture_path)
    if not path.exists():
        raise FileNotFoundError(f"Capture not found: {capture_path}")

    data = json.loads(path.read_text())
    transcript = data.get("raw_transcript", "")
    capture_id = data.get("capture_id", path.stem)

    return extract_elements(transcript, source_capture_id=capture_id)
