#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/ccp/__init__.py — Command Capture Protocol Package
========================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-01 (Raw Capture Layer + CCP Business Element Extraction)

CCP is the organism's cognitive bloodstream:
  Raw text → element extraction → confidence scoring → situational routing

Exports:
    CCPPipeline — end-to-end orchestrator
    extract_elements — standalone extraction
    score_element — standalone scoring
    route_element — standalone routing
"""

from epos.ccp.extractor import extract_elements, ElementType, ExtractedElement
from epos.ccp.scorer import score_element, score_elements
from epos.ccp.router import route_element, route_elements
from epos.ccp.pipeline import CCPPipeline

__all__ = [
    "CCPPipeline",
    "extract_elements",
    "score_element",
    "score_elements",
    "route_element",
    "route_elements",
    "ElementType",
    "ExtractedElement",
]
