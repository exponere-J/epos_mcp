#!/usr/bin/env python3
"""
content_lab_producer.py — EPOS Content Lab Script Generator
=============================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/content_lab_producer.py
# EPOS GOVERNANCE WATERMARK

Turns Creative Briefs into production-ready scripts using GroqRouter.
Outputs: markdown script, SEO description, 3 social caption variants.
Does not call HeyGen/ElevenLabs directly (API keys required).
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from groq_router import GroqRouter
from epos_intelligence import record_decision
from path_utils import get_epos_root, get_context_vault
from epos_event_bus import EPOSEventBus

try:
    from multimodal_router import MultimodalRouter
    _MULTIMODAL = MultimodalRouter()
except Exception:
    _MULTIMODAL = None


class ContentLabProducer:
    """Turns Creative Briefs into production-ready scripts via Groq."""

    SCRIPT_SYSTEM_PROMPT = (
        "You are A1 Architect for Echoes Marketing.\n"
        "Your job: write YouTube Shorts scripts that sell without selling.\n"
        "Rules:\n"
        "- Hook in first 3 seconds. No preamble. No 'hey guys'.\n"
        "- Single insight per video. No tangents.\n"
        "- CTA is specific: 'Link in description' or 'Comment below'.\n"
        "- Tone: direct, knowledgeable, no hype.\n"
        "- Duration target: 30-60 seconds when read aloud.\n"
        "- Format: [HOOK] [BODY] [CTA] — label each section.\n"
        "- End with: 'Affiliate link in description.'\n"
    )

    def generate_script(self, brief_path: Path) -> dict:
        """Read a Creative Brief. Generate script + description + captions."""
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        router = GroqRouter()

        # Generate script
        script_prompt = (
            f"Brief ID: {brief['brief_id']}\n"
            f"Angle: {brief['angle_type']}\n"
            f"Hook type: {brief['hook_type']}\n"
            f"Visual mask: {brief['visual_mask']}\n"
            f"Premise: {brief['script_premise']}\n"
            f"Hook line: {brief['hook_line']}\n"
            f"CTA: {brief['cta']}\n"
            f"Affiliate products: {', '.join(brief.get('affiliate_products', []))}\n\n"
            f"Write the complete YouTube Shorts script following the format rules."
        )
        script_text = router.route("scripting", script_prompt,
                                   system_prompt=self.SCRIPT_SYSTEM_PROMPT,
                                   max_tokens=800)

        # Generate SEO description
        desc_prompt = (
            f"Video script:\n{script_text}\n\n"
            f"Write a YouTube description (200-350 words) for this Short.\n"
            f"Include: main topic keyword, affiliate disclosure, subscribe CTA.\n"
            f"SEO-optimized. No markdown headers. Plain paragraphs.\n"
            f"End with: 'Affiliate links in description. As an Amazon Associate "
            f"and LEGO affiliate, I earn from qualifying purchases.'"
        )
        description = router.route("seo", desc_prompt, max_tokens=500)

        # Generate 3 caption variants
        caption_prompt = (
            f"Script premise: {brief['script_premise']}\n"
            f"Hook line: {brief['hook_line']}\n\n"
            f"Write 3 social captions:\n"
            f"1. X/Twitter (max 280 chars, punchy)\n"
            f"2. LinkedIn (professional, 150-200 chars)\n"
            f"3. TikTok (casual, energetic, 100-150 chars, 2-3 hashtags)\n\n"
            f"Format: X: <caption>\\nLinkedIn: <caption>\\nTikTok: <caption>"
        )
        captions = router.route("caption", caption_prompt, max_tokens=400)

        # Save outputs
        brief_id = brief["brief_id"]
        output_dir = (get_epos_root() / "content" / "lab" / "production"
                      / "lego_affiliate" / "scripts")
        output_dir.mkdir(parents=True, exist_ok=True)

        script_path = output_dir / f"{brief_id}_script.md"
        desc_path = output_dir / f"{brief_id}_description.txt"
        caption_path = output_dir / f"{brief_id}_captions.txt"

        script_path.write_text(
            f"# {brief_id} — {brief['angle_type'].upper()} — {brief['hook_type']}\n\n"
            f"**Visual Mask**: {brief['visual_mask']}\n"
            f"**Predicted ERI**: {brief.get('predicted_eri_score', 0)}\n\n"
            f"---\n\n{script_text}",
            encoding="utf-8",
        )
        desc_path.write_text(description, encoding="utf-8")
        caption_path.write_text(captions, encoding="utf-8")

        try:
            EPOSEventBus().publish("content.script.generated",
                {"brief_id": brief_id, "chars": len(script_text)}, "content_lab")
        except Exception:
            pass
        record_decision(
            decision_type="content.script_generated",
            description=f"Script generated for {brief_id}",
            agent_id="content_lab",
            outcome="success",
            context={"brief_id": brief_id, "angle_type": brief["angle_type"],
                     "hook_type": brief["hook_type"], "script_chars": len(script_text)},
        )

        # Generate cover image if multimodal router available
        cover_image_path = None
        if _MULTIMODAL and _MULTIMODAL._hf_available:
            try:
                visual_mask = brief.get("visual_mask", "clean professional")
                img_prompt = (
                    f"Professional YouTube thumbnail, {visual_mask} style, "
                    f"bold text overlay space, high contrast, "
                    f"topic: {brief.get('script_premise', '')[:100]}, "
                    f"modern digital marketing aesthetic, 16:9 aspect ratio"
                )
                cover_image_path = _MULTIMODAL.huggingface_image(
                    "flux.1-schnell", img_prompt,
                    negative_prompt="text, watermark, blurry, low quality, distorted"
                )
            except Exception as e:
                # Image generation is optional — don't block script production
                record_decision(
                    decision_type="content.image_generation_failed",
                    description=f"Cover image failed for {brief_id}: {str(e)[:100]}",
                    agent_id="content_lab", outcome="degraded",
                    context={"brief_id": brief_id, "error": str(e)[:200]},
                )

        return {
            "brief_id": brief_id,
            "script_path": str(script_path),
            "description_path": str(desc_path),
            "caption_path": str(caption_path),
            "script_chars": len(script_text),
            "cover_image_path": str(cover_image_path) if cover_image_path else None,
        }

    def generate_batch(self, niche_id: str, brief_ids: list = None) -> list:
        """Generate scripts for multiple briefs in a niche."""
        briefs_dir = get_context_vault() / "missions" / niche_id
        results = []
        for brief_path in sorted(briefs_dir.glob("CB-*.json")):
            bid = brief_path.stem
            if brief_ids and bid not in brief_ids:
                continue
            result = self.generate_script(brief_path)
            results.append(result)
            print(f"  Generated: {bid} — {result['script_chars']} chars")
        return results


if __name__ == "__main__":
    producer = ContentLabProducer()
    brief_path = get_context_vault() / "missions" / "lego_affiliate" / "CB-LEGO-001.json"
    if brief_path.exists():
        result = producer.generate_script(brief_path)
        assert Path(result["script_path"]).exists()
        assert result["script_chars"] > 50
        print(f"  Script: {result['script_path']}")
        print(f"  Chars: {result['script_chars']}")
        print("PASS: content_lab_producer self-test passed")
    else:
        print("SKIP: CB-LEGO-001.json not found — run Sprint 3 first")
