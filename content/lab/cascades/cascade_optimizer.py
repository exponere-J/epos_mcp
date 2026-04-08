# EPOS GOVERNANCE WATERMARK
"""
EPOS Content Lab - Cascade Optimizer (Node M1 support)
Component: C10_CONTENT_LAB / Cascade Engine
Path: epos_mcp/content/lab/cascades/cascade_optimizer.py

Generates derivative content specs from long-form sources:
  - YouTube long-form -> 5 Shorts + 3 LinkedIn + 2 X threads + 1 newsletter
  - LinkedIn article -> 3 X threads + 2 IG carousels + 1 TikTok + 1 email

Constitutional Requirements:
  - 24-hour stabilization before cascading
  - Source attribution maintained on all derivatives
  - Brand validation required before publish
  - All decisions logged
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
VAULT_PATH = EPOS_ROOT / "context_vault"
CASCADE_LOG = VAULT_PATH / "bi_history" / "cascade_decisions.jsonl"
EVENT_LOG = VAULT_PATH / "events" / "system_events.jsonl"

# Minimum hours before cascading (constitutional requirement)
STABILIZATION_HOURS = 24


# ---------------------------------------------------------------------------
# Derivative templates by source type
# ---------------------------------------------------------------------------

DERIVATIVE_TEMPLATES = {
    "youtube": [
        {"type": "youtube_short", "count": 5, "format": "vertical_video", "max_seconds": 60,
         "extraction": "peak_moments", "description": "Short clips from highest-retention segments"},
        {"type": "linkedin_post", "count": 3, "format": "text_with_image",
         "extraction": "business_insights", "description": "Key business takeaways as LinkedIn posts"},
        {"type": "x_thread", "count": 2, "format": "thread_5_8_tweets",
         "extraction": "actionable_steps", "description": "Step-by-step threads from tutorial segments"},
        {"type": "newsletter_section", "count": 1, "format": "email_block",
         "extraction": "summary_with_cta", "description": "Newsletter digest with link to full video"},
    ],
    "linkedin_article": [
        {"type": "x_thread", "count": 3, "format": "thread_5_8_tweets",
         "extraction": "key_arguments", "description": "Core arguments as X threads"},
        {"type": "instagram_carousel", "count": 2, "format": "carousel_slides",
         "extraction": "visual_quotes", "description": "Quote cards + data points as carousel"},
        {"type": "tiktok_script", "count": 1, "format": "vertical_video_script",
         "extraction": "hook_and_payoff", "description": "Opening hook + conclusion as TikTok"},
        {"type": "email_excerpt", "count": 1, "format": "email_block",
         "extraction": "teaser_with_link", "description": "First paragraph + CTA to full article"},
    ],
    "blog_post": [
        {"type": "x_thread", "count": 2, "format": "thread_5_8_tweets",
         "extraction": "key_points", "description": "Main points as X thread"},
        {"type": "linkedin_post", "count": 2, "format": "text_with_image",
         "extraction": "professional_angle", "description": "B2B angle of the blog content"},
        {"type": "tiktok_script", "count": 1, "format": "vertical_video_script",
         "extraction": "hook_and_payoff", "description": "Provocative hook from blog into 30s script"},
        {"type": "instagram_carousel", "count": 1, "format": "carousel_slides",
         "extraction": "step_by_step", "description": "How-to steps as carousel slides"},
    ],
}


# ---------------------------------------------------------------------------
# Extraction strategies
# ---------------------------------------------------------------------------

class ExtractionStrategy:
    """Extracts derivative content specs from source material."""

    @staticmethod
    def peak_moments(source: dict) -> list[dict]:
        """Identify highest-retention segments from video content."""
        transcript = source.get("transcript", "")
        timestamps = source.get("timestamps", [])
        retention = source.get("retention_data", [])

        segments = []
        if retention:
            # Sort by retention, take top segments
            sorted_ret = sorted(retention, key=lambda r: r.get("retention", 0), reverse=True)
            for seg in sorted_ret[:5]:
                segments.append({
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 60),
                    "retention": seg.get("retention", 0),
                    "text_excerpt": _extract_text_window(transcript, seg.get("start", 0), 200),
                })
        elif transcript:
            # Fallback: split transcript into chunks
            words = transcript.split()
            chunk_size = len(words) // 5 or 1
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                if chunk.strip():
                    segments.append({"text_excerpt": chunk[:300], "estimated_seconds": 60})

        return segments

    @staticmethod
    def business_insights(source: dict) -> list[dict]:
        """Extract business-relevant takeaways."""
        text = source.get("transcript", "") or source.get("body", "")
        insights = []

        # Look for insight patterns
        patterns = [
            r"(?:the key (?:insight|takeaway|lesson) is[:\s]+)(.{50,200})",
            r"(?:what this means for (?:your )?business[:\s]+)(.{50,200})",
            r"(?:the bottom line[:\s]+)(.{50,200})",
            r"(?:here(?:'s| is) (?:the|what) .{5,30}?[:\s]+)(.{50,200})",
        ]
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                insights.append({"text": match.group(1).strip(), "type": "extracted_insight"})

        # Fallback: first and last paragraphs often contain key points
        if not insights and text:
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if paragraphs:
                insights.append({"text": paragraphs[0][:300], "type": "opening_thesis"})
            if len(paragraphs) > 1:
                insights.append({"text": paragraphs[-1][:300], "type": "closing_argument"})

        return insights[:3]

    @staticmethod
    def actionable_steps(source: dict) -> list[dict]:
        """Extract step-by-step instructions."""
        text = source.get("transcript", "") or source.get("body", "")
        steps = []

        # Look for numbered/bulleted steps
        step_patterns = [
            r"(?:step\s+\d+[:\s]+)(.{20,200})",
            r"(?:\d+\.\s+)(.{20,200})",
            r"(?:first|second|third|next|finally)[,:\s]+(.{20,200})",
        ]
        for pat in step_patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                steps.append({"text": match.group(1).strip(), "type": "action_step"})

        return steps[:8]  # Max 8 steps for a thread

    @staticmethod
    def hook_and_payoff(source: dict) -> dict:
        """Extract opening hook and closing payoff for short-form."""
        text = source.get("transcript", "") or source.get("body", "")
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        hook = paragraphs[0][:150] if paragraphs else "No hook found"
        payoff = paragraphs[-1][:150] if len(paragraphs) > 1 else hook

        return {"hook": hook, "payoff": payoff, "type": "hook_payoff"}


# ---------------------------------------------------------------------------
# Core Optimizer
# ---------------------------------------------------------------------------

class CascadeOptimizer:
    """
    Top-down cascade engine: breaks long-form into platform-native derivatives.

    Usage:
        optimizer = CascadeOptimizer()
        result = optimizer.generate_derivatives(source_content)
    """

    def __init__(self):
        self.extractor = ExtractionStrategy()

    def generate_derivatives(self, source: dict) -> dict:
        """
        Generate derivative content specs from source.

        Args:
            source: {
                "source_id": str,
                "source_type": "youtube" | "linkedin_article" | "blog_post",
                "title": str,
                "body": str,              # or "transcript" for video
                "transcript": str,        # for video sources
                "url": str,
                "published_at": str,      # ISO timestamp
                "retention_data": [...],  # optional, for YouTube
                "timestamps": [...],      # optional
                "metrics": { likes, shares, comments, impressions },
            }

        Returns:
            {
                "source_id": str,
                "source_type": str,
                "stabilization_ok": bool,
                "derivatives": [
                    {
                        "derivative_id": str,
                        "type": str,
                        "format": str,
                        "content_spec": { ... },
                        "source_attribution": str,
                        "status": "pending_validation",
                    }
                ],
                "total_derivatives": int,
                "timestamp": str,
            }
        """
        source_type = source.get("source_type", "youtube")
        source_id = source.get("source_id", "unknown")

        # Constitutional check: stabilization period
        stabilization_ok = self._check_stabilization(source)

        templates = DERIVATIVE_TEMPLATES.get(source_type, DERIVATIVE_TEMPLATES["youtube"])

        derivatives = []
        for template in templates:
            extraction_method = getattr(
                self.extractor, template["extraction"], None
            )
            if not extraction_method:
                continue

            extracted = extraction_method(source)
            count = min(template["count"], max(len(extracted) if isinstance(extracted, list) else 1, 1))

            for i in range(count):
                content_data = extracted[i] if isinstance(extracted, list) and i < len(extracted) else extracted
                derivative = {
                    "derivative_id": f"{source_id}_CAS_{template['type']}_{i+1:02d}",
                    "type": template["type"],
                    "format": template["format"],
                    "description": template["description"],
                    "content_spec": content_data,
                    "source_attribution": f"Source: {source.get('title', source_id)} ({source.get('url', 'N/A')})",
                    "status": "pending_validation" if stabilization_ok else "awaiting_stabilization",
                }
                derivatives.append(derivative)

        result = {
            "source_id": source_id,
            "source_type": source_type,
            "stabilization_ok": stabilization_ok,
            "derivatives": derivatives,
            "total_derivatives": len(derivatives),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._log_cascade(result)
        return result

    def _check_stabilization(self, source: dict) -> bool:
        """Enforce 24-hour stabilization before cascading."""
        published_str = source.get("published_at")
        if not published_str:
            return True  # If no publish date, allow (manual override)

        try:
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - published) >= timedelta(hours=STABILIZATION_HOURS)
        except (ValueError, TypeError):
            return True

    def _log_cascade(self, result: dict):
        """Log cascade decision to Context Vault."""
        CASCADE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event_type": "cascade.generated",
            "source_id": result["source_id"],
            "total_derivatives": result["total_derivatives"],
            "stabilization_ok": result["stabilization_ok"],
            "timestamp": result["timestamp"],
        }
        try:
            with open(CASCADE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass

        # Emit event
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "event_type": "content.cascade.generated",
            "payload": {
                "source_id": result["source_id"],
                "derivative_count": result["total_derivatives"],
                "types": list(set(d["type"] for d in result["derivatives"])),
            },
            "timestamp": result["timestamp"],
            "source": "cascade_optimizer",
        }
        try:
            with open(EVENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _extract_text_window(text: str, start_seconds: int, max_chars: int) -> str:
    """Rough extraction of text around a timestamp (assumes ~3 words/sec)."""
    words = text.split()
    start_word = min(start_seconds * 3, len(words))
    window = words[start_word:start_word + 50]
    return " ".join(window)[:max_chars]


def health_check() -> dict:
    """Health check for cascade subsystem."""
    checks = {
        "optimizer_importable": True,
        "vault_path_exists": VAULT_PATH.exists(),
        "cascade_log_writable": _check_writable(CASCADE_LOG),
        "templates_loaded": len(DERIVATIVE_TEMPLATES) > 0,
    }
    status = "healthy" if all(checks.values()) else "degraded"
    return {"component": "cascade_optimizer", "status": status, "checks": checks}


def _check_writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a"):
            pass
        return True
    except OSError:
        return False


if __name__ == "__main__":
    optimizer = CascadeOptimizer()

    test_source = {
        "source_id": "YT_TEST_001",
        "source_type": "youtube",
        "title": "Why Sovereign AI is the Only Defensible Moat",
        "transcript": "Step 1: Stop renting intelligence from OpenAI. Step 2: Build your own sovereign node architecture. Step 3: Deploy constitutional governance. The key insight is that data sovereignty is not a feature, it is the entire business model. Here is the EPOS blueprint for building an air-gapped AI system. The bottom line is that if your AI cannot run without an internet connection, you do not own it.",
        "url": "https://youtube.com/watch?v=test",
        "published_at": "2026-02-13T10:00:00Z",
        "metrics": {"likes": 340, "shares": 89, "comments": 45, "impressions": 12000},
    }

    result = optimizer.generate_derivatives(test_source)
    print(json.dumps(result, indent=2))
    print(f"\nHealth: {json.dumps(health_check(), indent=2)}")
