#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
cta_attribution.py — CTA Attribution Loop
============================================
Constitutional Authority: EPOS Constitution v3.1

Closes the data flow gap from Scan 7 finding: CTA tracking has no consumer.

Reads context_vault/echoes/cta_tracking.jsonl, matches CTA tokens to
engagement signals, and feeds attribution data to Lead Scoring.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
CTA_TRACKING = VAULT / "echoes" / "cta_tracking.jsonl"
ATTRIBUTION_LOG = VAULT / "reactor" / "cta_attribution.jsonl"


class CTAAttribution:
    """CTA Attribution Engine — closes the content -> engagement -> lead loop."""

    def load_cta_tokens(self) -> dict:
        """Load all CTA tokens from tracking journal."""
        tokens = {}
        if not CTA_TRACKING.exists():
            return tokens
        for line in CTA_TRACKING.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entry = json.loads(line)
                    token = entry.get("cta_token")
                    if token:
                        tokens[token] = entry
                except Exception:
                    pass
        return tokens

    def attribute_engagement(self, cta_token: str, engagement_data: dict) -> dict:
        """Attribute an engagement signal to a specific CTA token."""
        tokens = self.load_cta_tokens()
        if cta_token not in tokens:
            return {"success": False, "reason": "Unknown CTA token"}

        original = tokens[cta_token]
        attribution = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cta_token": cta_token,
            "post_id": original.get("post_id"),
            "platform": original.get("platform"),
            "engagement": engagement_data,
            "attributed": True,
        }

        ATTRIBUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ATTRIBUTION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(attribution) + "\n")

        if _BUS:
            try:
                _BUS.publish("content.attribution.recorded", attribution,
                             source_module="cta_attribution")
                # Feed Lead Scoring if engagement has user identifier
                if engagement_data.get("user_id"):
                    _BUS.publish("crm.lead.scored", {
                        "lead_id": engagement_data["user_id"],
                        "score": min(60 + engagement_data.get("intensity", 0), 100),
                        "source": "cta_attribution",
                        "cta_token": cta_token,
                    }, source_module="cta_attribution")
            except Exception:
                pass

        return {"success": True, "attribution": attribution}

    def get_attribution_summary(self) -> dict:
        """Aggregate attribution data."""
        if not ATTRIBUTION_LOG.exists():
            return {"total_attributions": 0, "by_platform": {}}

        by_platform = {}
        total = 0
        for line in ATTRIBUTION_LOG.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entry = json.loads(line)
                    platform = entry.get("platform", "unknown")
                    by_platform[platform] = by_platform.get(platform, 0) + 1
                    total += 1
                except Exception:
                    pass
        return {"total_attributions": total, "by_platform": by_platform}


# ── Self-Test ────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    cta = CTAAttribution()

    # Test 1: Load tokens (may be empty)
    tokens = cta.load_cta_tokens()
    print(f"CTA tokens loaded: {len(tokens)}")
    passed += 1

    # Test 2: Create a test CTA and attribute engagement
    CTA_TRACKING.parent.mkdir(parents=True, exist_ok=True)
    test_cta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "post_id": "test-post-001",
        "platform": "linkedin",
        "cta_token": "TEST-CTA-ATTR-001",
    }
    with open(CTA_TRACKING, "a", encoding="utf-8") as f:
        f.write(json.dumps(test_cta) + "\n")

    result = cta.attribute_engagement("TEST-CTA-ATTR-001", {
        "user_id": "test-user-001",
        "intensity": 25,
        "type": "click",
    })
    assert result["success"]
    passed += 1

    # Test 3: Summary
    summary = cta.get_attribution_summary()
    assert summary["total_attributions"] >= 1
    print(f"Attribution summary: {summary}")
    passed += 1

    print(f"\nPASS: cta_attribution ({passed} assertions)")
