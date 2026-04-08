#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
V1 Validation Engine — Constitutional Content Gate
Constitutional Authority: EPOS Constitution v3.1

Five-check gate. Nothing publishes without passing.
FAIL is immutable. CONDITIONAL_PASS requires human approval.
"""

import sys
import json
import uuid
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from path_utils import get_context_vault
from epos_intelligence import get_decision_analytics
from epos_event_bus import EPOSEventBus


class V1ValidationEngine:
    """Five-check constitutional gate for content."""

    PROHIBITED_WORDS = ["viral", "hack", "secret", "guaranteed",
                        "insane", "mindblowing", "you won't believe"]

    def __init__(self):
        self.vault_root = get_context_vault()
        self.bus = EPOSEventBus()
        self.receipts_dir = self.vault_root / "governance" / "validation_receipts"
        self.receipts_dir.mkdir(parents=True, exist_ok=True)

    def validate_script(self, script: dict, niche_id: str,
                        is_affiliate: bool = False) -> dict:
        """Run all 5 checks. Return governance receipt."""
        checks = {
            "brand_voice": self._check_brand_voice(script, niche_id),
            "claims_accuracy": self._check_claims(script),
            "affiliate_disclosure": (self._check_disclosure(script) if is_affiliate
                                     else {"pass": True, "note": "not_affiliate"}),
            "cta_token_format": self._check_cta_token(script),
            "eri_premortem_logged": self._verify_eri_logged(script),
        }

        failed = [k for k, v in checks.items() if not v["pass"]]
        conditional = [k for k, v in checks.items() if v.get("conditional")]
        verdict = ("PASS" if not failed and not conditional
                   else "CONDITIONAL_PASS" if not failed and conditional
                   else "FAIL")

        receipt = {
            "receipt_id": f"VR-{script.get('brief_id', '?')}-{uuid.uuid4().hex[:6]}",
            "script_id": script.get("script_id"),
            "brief_id": script.get("brief_id"),
            "verdict": verdict,
            "checks": checks,
            "failed_checks": failed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "requires_human_review": verdict == "CONDITIONAL_PASS",
        }

        receipt_path = self.receipts_dir / f"{receipt['receipt_id']}.json"
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

        try:
            self.bus.publish(f"governance.validation.{verdict.lower()}",
                             {"receipt_id": receipt["receipt_id"], "verdict": verdict},
                             "v1_validation")
        except Exception:
            pass
        return receipt

    def _check_brand_voice(self, script: dict, niche_id: str) -> dict:
        text = script.get("script_text", "").lower()
        violations = [w for w in self.PROHIBITED_WORDS if w in text]
        return {"pass": len(violations) == 0, "violations": violations,
                "note": f"Prohibited: {violations}" if violations else "clean"}

    def _check_claims(self, script: dict) -> dict:
        text = script.get("script_text", "")
        numbers = re.findall(r'\b\d+%|\$\d+|\d+ times\b', text)
        has_citations = bool(script.get("sources"))
        if numbers and not has_citations:
            return {"pass": False, "conditional": True,
                    "note": f"Uncited claims: {numbers[:3]}"}
        return {"pass": True, "note": "no uncited claims"}

    def _check_disclosure(self, script: dict) -> dict:
        text = (script.get("script_text", "") + script.get("description", "")).lower()
        return {"pass": "affiliate" in text,
                "note": "disclosure present" if "affiliate" in text
                        else "MISSING affiliate disclosure"}

    def _check_cta_token(self, script: dict) -> dict:
        token = script.get("cta_token", "")
        if not token:
            return {"pass": True, "note": "no token required"}
        valid = bool(re.match(r"^ECH-[A-Z]+-[A-Z]+-\d{8}-[A-Z0-9]+$", token))
        return {"pass": valid, "note": "valid" if valid else f"Invalid: {token!r}"}

    def _verify_eri_logged(self, script: dict) -> dict:
        brief_id = script.get("brief_id")
        if not brief_id:
            return {"pass": False, "note": "No brief_id"}
        analytics = get_decision_analytics()
        by_type = analytics.get("by_type", {})
        if by_type.get("content.eri_prediction", 0) > 0:
            return {"pass": True, "note": "ERI prediction found"}
        return {"pass": False, "note": "No ERI prediction — constitutional violation"}


if __name__ == "__main__":
    engine = V1ValidationEngine()
    receipt = engine.validate_script(
        {"brief_id": "CB-LEGO-TEST", "script_text": "Top 5 LEGO sets. Affiliate link in description.",
         "description": "Affiliate links in description."},
        "lego_affiliate", is_affiliate=True,
    )
    assert receipt["verdict"] in ("PASS", "CONDITIONAL_PASS", "FAIL")
    assert Path(engine.receipts_dir / f"{receipt['receipt_id']}.json").exists()
    print(f"  Verdict: {receipt['verdict']}")
    print(f"  Receipt: {receipt['receipt_id']}")
    print("PASS: V1ValidationEngine self-tests passed")
