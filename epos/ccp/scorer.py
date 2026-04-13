#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/ccp/scorer.py — CCP Confidence Scoring Engine
===================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

Two-tier confidence scoring:

  Tier 1 — Heuristic (fast, free):
    Uses keyword patterns from extractor.py.
    High confidence (>0.90): keyword match + structural cue → accept as-is.
    Low confidence (<0.70): flag for human review.

  Tier 2 — LLM (Qwen3-32B via LiteLLM):
    Medium confidence (0.70–0.90): sent to LLM for classification.
    LLM returns revised element type + confidence score.
    Falls back gracefully if LLM unavailable.

Confidence bands:
    ≥ 0.90  → HIGH    — accept, route directly
    0.70–0.89 → MEDIUM — LLM review
    0.60–0.69 → LOW    — human confirmation required
    < 0.60  → SKIP    — discard (below extraction threshold)
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# Allow import from /app root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from epos.ccp.extractor import ExtractedElement, ElementType

# ──────────────────────────────────────────────────────────────────────────────
# Confidence bands
# ──────────────────────────────────────────────────────────────────────────────

HIGH_CONFIDENCE   = 0.90
MEDIUM_CONFIDENCE = 0.70
LOW_CONFIDENCE    = 0.60

BAND_HIGH   = "high"
BAND_MEDIUM = "medium"
BAND_LOW    = "low"

# LLM model for classification (Qwen3-32B via Groq or local)
CLASSIFICATION_MODEL = os.getenv("CCP_CLASSIFIER_MODEL", "groq/qwen-qwq-32b")


# ──────────────────────────────────────────────────────────────────────────────
# LLM classification prompt
# ──────────────────────────────────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """You are a business intelligence classifier for the EPOS organism.

Classify the following sentence into exactly ONE of these 9 element types:
  action_item, decision, research_question, idea, client_insight,
  content_seed, learning_moment, constitutional_proposal, blocker

Rules:
- Choose the single best type. If genuinely ambiguous, choose the highest-value type.
- Return ONLY valid JSON, no explanation.

Response format:
{{"type": "<element_type>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}}

Sentence to classify:
"{sentence}"

Current heuristic classification: {heuristic_type} (confidence: {heuristic_conf:.2f})
"""


# ──────────────────────────────────────────────────────────────────────────────
# LLM caller (lazy import, graceful fallback)
# ──────────────────────────────────────────────────────────────────────────────

def _llm_classify(element: ExtractedElement) -> Optional[dict]:
    """
    Call LLM to classify an ambiguous element.
    Returns {"type": str, "confidence": float, "reasoning": str} or None on failure.
    """
    try:
        from tools.litellm_client import run_model, ModelTarget

        prompt = CLASSIFICATION_PROMPT.format(
            sentence=element.content[:500],
            heuristic_type=element.type.value,
            heuristic_conf=element.confidence,
        )

        raw = run_model(prompt, target=ModelTarget.REASONING, max_tokens=150)

        # Parse JSON from LLM response (handle markdown code blocks)
        raw_stripped = raw.strip()
        if raw_stripped.startswith("```"):
            raw_stripped = raw_stripped.split("```")[1]
            if raw_stripped.startswith("json"):
                raw_stripped = raw_stripped[4:]
        raw_stripped = raw_stripped.strip()

        result = json.loads(raw_stripped)
        # Validate type
        valid_types = {e.value for e in ElementType}
        if result.get("type") not in valid_types:
            return None
        result["confidence"] = float(result.get("confidence", element.confidence))
        return result

    except Exception:
        # LLM unavailable or parse failure — return None, keep heuristic
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Scoring logic
# ──────────────────────────────────────────────────────────────────────────────

def confidence_band(confidence: float) -> str:
    """Return human-readable confidence band."""
    if confidence >= HIGH_CONFIDENCE:
        return BAND_HIGH
    elif confidence >= MEDIUM_CONFIDENCE:
        return BAND_MEDIUM
    else:
        return BAND_LOW


def score_element(element: ExtractedElement, use_llm: bool = True) -> ExtractedElement:
    """
    Refine confidence score for a single extracted element.

    For high-confidence elements (≥0.90): no action needed.
    For medium-confidence elements (0.70–0.89): optionally call LLM.
    For low-confidence elements (<0.70): flag for human review.

    Modifies element in-place and returns it.

    Args:
        element: ExtractedElement with heuristic confidence
        use_llm: Whether to call LLM for medium-confidence elements

    Returns:
        Updated ExtractedElement with refined confidence
    """
    band = confidence_band(element.confidence)

    if band == BAND_HIGH:
        # Already confident — nothing to do
        element.needs_llm_review = False
        return element

    if band == BAND_MEDIUM and use_llm:
        # Call LLM for classification
        llm_result = _llm_classify(element)
        if llm_result:
            # Apply LLM refinement
            try:
                element.type = ElementType(llm_result["type"])
                element.confidence = max(element.confidence, llm_result["confidence"])
                # Update destination if type changed
                from epos.ccp.extractor import SUGGESTED_DESTINATIONS
                element.suggested_destination = SUGGESTED_DESTINATIONS.get(
                    element.type, element.suggested_destination
                )
                element.needs_llm_review = False
            except (ValueError, KeyError):
                pass
        else:
            # LLM failed — keep heuristic, still flag for review if still medium
            element.needs_llm_review = element.confidence < HIGH_CONFIDENCE

    if band == BAND_LOW:
        # Low confidence — always needs human review
        element.needs_llm_review = True

    return element


def score_elements(
    elements: List[ExtractedElement],
    use_llm: bool = True,
    llm_only_for_medium: bool = True,
) -> List[ExtractedElement]:
    """
    Score a batch of extracted elements.

    Applies LLM classification only for medium-confidence elements
    to minimize LLM calls (high confidence needs no LLM, low confidence
    goes straight to human review).

    Args:
        elements: List of ExtractedElement
        use_llm: Whether to enable LLM scoring
        llm_only_for_medium: Only call LLM for medium-confidence (0.70–0.89)

    Returns:
        List of scored ExtractedElement
    """
    scored = []
    for element in elements:
        should_use_llm = use_llm
        if llm_only_for_medium:
            band = confidence_band(element.confidence)
            should_use_llm = use_llm and (band == BAND_MEDIUM)
        scored.append(score_element(element, use_llm=should_use_llm))
    return scored


def summarize_scores(elements: List[ExtractedElement]) -> dict:
    """Return score distribution summary for a batch."""
    bands = {BAND_HIGH: 0, BAND_MEDIUM: 0, BAND_LOW: 0}
    by_type: dict = {}

    for e in elements:
        band = confidence_band(e.confidence)
        bands[band] += 1
        by_type[e.type.value] = by_type.get(e.type.value, 0) + 1

    return {
        "total": len(elements),
        "by_band": bands,
        "by_type": by_type,
        "needs_llm_review": sum(1 for e in elements if e.needs_llm_review),
        "auto_route_ready": sum(
            1 for e in elements
            if confidence_band(e.confidence) == BAND_HIGH and not e.needs_llm_review
        ),
    }
