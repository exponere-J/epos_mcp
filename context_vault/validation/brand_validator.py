# File: /mnt/c/Users/Jamie/workspace/epos_mcp/context_vault/validation/brand_validator.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
EPOS Content Lab - Brand Validator (Node V1)
Component: C10_CONTENT_LAB / Validation Engine
Path: epos_mcp/content/lab/validation/brand_validator.py

Validates content against brand rules before publication:
  - Brand voice consistency
  - Claim verification
  - Platform format compliance
  - Legal/compliance screening
  - Quality scoring

Constitutional: NO content publishes without passing validation.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
VAULT_PATH = EPOS_ROOT / "context_vault"
VALIDATION_LOG = VAULT_PATH / "bi_history" / "validation_decisions.jsonl"
EVENT_LOG = VAULT_PATH / "events" / "system_events.jsonl"

# ---------------------------------------------------------------------------
# Brand Rules
# ---------------------------------------------------------------------------

BRAND_VOICE = {
    "tone": ["authentic", "adaptive", "grounded", "peer-level", "witty"],
    "prohibited_words": [
        "synergy", "leverage", "paradigm", "disrupt",  # corporate jargon
        "guaranteed", "promise", "100%", "never fails",  # unverifiable claims
        "hack", "trick", "secret",  # clickbait
    ],
    "required_cta_patterns": [
        r"CTA-\w+-\w+",  # Must have CTA token
    ],
    "max_hashtags": {"x": 3, "tiktok": 5, "linkedin": 5, "instagram": 10, "youtube": 3},
}

PLATFORM_FORMATS = {
    "x": {"max_chars": 280, "thread_max": 8, "media_types": ["image", "video", "gif"]},
    "tiktok": {"max_seconds": 180, "orientation": "vertical", "captions_required": True},
    "linkedin": {"max_chars": 3000, "media_types": ["image", "video", "carousel", "document"]},
    "youtube": {"title_max": 100, "description_max": 5000},
    "instagram": {"caption_max": 2200, "carousel_max_slides": 10},
}

# Prohibited content patterns (PERMISSION GATE: flag for human review)
FLAGGED_PATTERNS = [
    r"(?:competitor|rival)\s+(?:sucks|is\s+(?:bad|terrible|awful))",
    r"(?:guarantee|promise)\s+(?:results|revenue|income)",
    r"(?:financial|investment)\s+advice",
    r"(?:medical|health)\s+(?:advice|recommendation)",
]


class BrandValidator:
    """
    Validates content against brand constitution before publication.

    Usage:
        validator = BrandValidator()
        result = validator.validate(content)
        if result["passed"]:
            # proceed to publish
        else:
            # fix issues or flag for human review
    """

    def validate(self, content: dict) -> dict:
        """
        Validate a content unit.

        Args:
            content: {
                "content_id": str,
                "platform": str,
                "text": str,
                "media_type": str (optional),
                "hashtags": list[str] (optional),
                "cta_token": str (optional),
                "duration_seconds": int (optional, for video),
                "source_attribution": str (optional),
            }

        Returns:
            {
                "content_id": str,
                "passed": bool,
                "requires_human_review": bool,
                "score": int (0-100),
                "checks": { check_name: {passed, detail} },
                "issues": [str],
                "timestamp": str,
            }
        """
        checks = {}
        issues = []

        # Run all checks
        checks["voice_tone"] = self._check_voice(content)
        checks["prohibited_words"] = self._check_prohibited(content)
        checks["platform_format"] = self._check_format(content)
        checks["hashtag_limit"] = self._check_hashtags(content)
        checks["cta_present"] = self._check_cta(content)
        checks["source_attribution"] = self._check_attribution(content)
        checks["flagged_content"] = self._check_flagged(content)

        # Collect issues
        for name, check in checks.items():
            if not check["passed"]:
                issues.append(f"{name}: {check['detail']}")

        # Calculate score
        passed_count = sum(1 for c in checks.values() if c["passed"])
        score = int((passed_count / len(checks)) * 100)

        # Determine overall pass
        hard_fails = ["prohibited_words", "flagged_content"]
        hard_fail = any(not checks[hf]["passed"] for hf in hard_fails if hf in checks)
        requires_human = not checks.get("flagged_content", {}).get("passed", True)

        passed = not hard_fail and score >= 70

        result = {
            "content_id": content.get("content_id", "unknown"),
            "passed": passed,
            "requires_human_review": requires_human,
            "score": score,
            "checks": checks,
            "issues": issues,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._log_validation(result)
        return result

    # -------------------------------------------------------------------
    # Individual checks
    # -------------------------------------------------------------------

    def _check_voice(self, content: dict) -> dict:
        text = (content.get("text", "") or "").lower()
        if not text:
            return {"passed": False, "detail": "No text content to validate"}

        # Simple heuristic: check for overly corporate or aggressive tone
        corporate_count = sum(1 for word in ["synergy", "leverage", "paradigm", "ecosystem",
                                              "ideation", "deliverable", "bandwidth"]
                             if word in text)
        if corporate_count >= 2:
            return {"passed": False, "detail": f"Corporate jargon detected ({corporate_count} instances)"}

        return {"passed": True, "detail": "Voice check passed"}

    def _check_prohibited(self, content: dict) -> dict:
        text = (content.get("text", "") or "").lower()
        found = [w for w in BRAND_VOICE["prohibited_words"] if w in text]
        if found:
            return {"passed": False, "detail": f"Prohibited words: {', '.join(found)}"}
        return {"passed": True, "detail": "No prohibited words found"}

    def _check_format(self, content: dict) -> dict:
        platform = content.get("platform", "x")
        fmt = PLATFORM_FORMATS.get(platform)
        if not fmt:
            return {"passed": True, "detail": f"No format rules for {platform}"}

        text = content.get("text", "") or ""

        if "max_chars" in fmt and len(text) > fmt["max_chars"]:
            return {"passed": False,
                    "detail": f"Text length {len(text)} exceeds {platform} limit of {fmt['max_chars']}"}

        if "max_seconds" in fmt:
            duration = content.get("duration_seconds", 0)
            if duration and duration > fmt["max_seconds"]:
                return {"passed": False,
                        "detail": f"Duration {duration}s exceeds {platform} limit of {fmt['max_seconds']}s"}

        return {"passed": True, "detail": f"Format compliant for {platform}"}

    def _check_hashtags(self, content: dict) -> dict:
        platform = content.get("platform", "x")
        hashtags = content.get("hashtags", [])
        max_tags = BRAND_VOICE["max_hashtags"].get(platform, 5)

        if len(hashtags) > max_tags:
            return {"passed": False,
                    "detail": f"{len(hashtags)} hashtags exceeds {platform} limit of {max_tags}"}
        return {"passed": True, "detail": f"Hashtag count OK ({len(hashtags)}/{max_tags})"}

    def _check_cta(self, content: dict) -> dict:
        cta = content.get("cta_token", "")
        if not cta:
            return {"passed": False, "detail": "No CTA token assigned"}

        if re.match(r"CTA-\w+-\w+", cta):
            return {"passed": True, "detail": f"CTA token valid: {cta}"}
        return {"passed": False, "detail": f"CTA token malformed: {cta}"}

    def _check_attribution(self, content: dict) -> dict:
        attr = content.get("source_attribution", "")
        if content.get("is_derivative", False) and not attr:
            return {"passed": False, "detail": "Derivative content missing source attribution"}
        return {"passed": True, "detail": "Attribution check passed"}

    def _check_flagged(self, content: dict) -> dict:
        """PERMISSION GATE: content matching these patterns requires human review."""
        text = (content.get("text", "") or "")
        for pattern in FLAGGED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return {"passed": False,
                        "detail": f"HUMAN REVIEW REQUIRED: flagged pattern detected"}
        return {"passed": True, "detail": "No flagged content detected"}

    # -------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------

    def _log_validation(self, result: dict):
        VALIDATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event_type": "content.validation",
            "content_id": result["content_id"],
            "passed": result["passed"],
            "score": result["score"],
            "requires_human_review": result["requires_human_review"],
            "issues": result["issues"],
            "timestamp": result["timestamp"],
        }
        try:
            with open(VALIDATION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass


def health_check() -> dict:
    checks = {
        "validator_importable": True,
        "vault_path_exists": VAULT_PATH.exists(),
        "brand_rules_loaded": len(BRAND_VOICE["prohibited_words"]) > 0,
        "platform_formats_loaded": len(PLATFORM_FORMATS) > 0,
    }
    return {"component": "brand_validator", "status": "healthy" if all(checks.values()) else "degraded", "checks": checks}


if __name__ == "__main__":
    validator = BrandValidator()

    test_content = {
        "content_id": "DERIV_TEST_001",
        "platform": "x",
        "text": "Your AI strategy is a subscription to a cage. EPOS gives you the title to the land. Build sovereign. Build local. #EPOS #DataSovereignty",
        "hashtags": ["EPOS", "DataSovereignty"],
        "cta_token": "CTA-BOOK-SOVEREIGNTY-CALL",
        "is_derivative": True,
        "source_attribution": "Source: Sovereign Intelligence Manifesto (exponere.com)",
    }

    result = validator.validate(test_content)
    print(json.dumps(result, indent=2))
