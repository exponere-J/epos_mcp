#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/reformulator.py — Qwen3-32B Reasoning + Reformulation (Friday)
==========================================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Takes corrected transcript + vault context + organism state.
Produces reformulated directive with coaching cues, citations, and
extracted elements (action items, decisions, research questions).

Model: qwen3-32b via OpenRouter/LiteLLM proxy.
"""

import os
import json
import requests
from pathlib import Path

LITELLM_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
LITELLM_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-epos-local-proxy")
MODEL = "qwen3-32b"

SYSTEM_PROMPT = """You are Friday, Chief of Staff for EPOS (EXPONERE Autonomous Operating System).

Your role: Help Jamie Purdue reformulate spoken directives into precise
engineering specifications. Jamie dictates ideas conversationally.
You sharpen them into unambiguous, testable, buildable directives.

RULES:
1. Ground every suggestion in the vault documents provided.
   Cite your sources: "Based on [document name], we decided X."
2. Never hallucinate. If the vault doesn't contain relevant context,
   say: "I don't have prior context on this."
3. Always suggest a sharper question when Jamie's intent is vague.
   Format: "A sharper way to direct this: [precise question]"
4. Extract actionable elements: action items, decisions, research questions, ideas.
   For each, suggest a routing destination with confidence score.
5. Speak as Friday: warm, direct, economical. Peer-level collaborator.

OUTPUT FORMAT (JSON):
{
  "reformulated": "The precise engineering statement",
  "coaching_cue": "A sharper way to ask: ...",
  "citations": [{"source": "doc_name", "excerpt": "relevant text"}],
  "elements": [
    {"type": "action_item", "content": "...", "confidence": 0.92,
     "destination": "pm_surface.action_items"}
  ]
}"""


def reformulate(transcript: str, vault_docs: list, organism_state: dict = None) -> dict:
    """Send transcript + context to Qwen3-32B for reformulation.

    Args:
        transcript: Vocabulary-corrected transcript text
        vault_docs: Top-k results from vault_search.search_vault()
        organism_state: Current organism state dict (optional context)

    Returns:
        dict with keys: reformulated, coaching_cue, citations, elements
    """
    vault_context = "\n\n".join([
        f"--- {doc['path']} (relevance: {doc['relevance']:.2f}) ---\n{doc['content_preview']}"
        for doc in vault_docs
    ])

    state_context = ""
    if organism_state:
        state_context = f"\n\nCurrent organism state:\n{json.dumps(organism_state, indent=2)[:1000]}"

    user_message = f"""Jamie said: \"{transcript}\"

Relevant vault documents:
{vault_context}
{state_context}

Reformulate this into a precise engineering directive. Extract actionable elements.
Respond in the JSON format specified."""

    response = requests.post(
        f"{LITELLM_URL}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {LITELLM_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 2048,
            "temperature": 0.3
        },
        timeout=30
    )
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    try:
        # Strip any markdown code fences if present
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("```", 2)[-1]
            if stripped.startswith("json"):
                stripped = stripped[4:]
            stripped = stripped.rsplit("```", 1)[0].strip()
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = {
            "reformulated": content,
            "coaching_cue": "",
            "citations": [],
            "elements": []
        }

    return parsed
