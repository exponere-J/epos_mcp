#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
lead_scoring.py — EPOS Autonomous Lead Scoring Engine
======================================================
Constitutional Authority: EPOS Constitution v3.1
Module: Autonomous Lead Scoring (CODE DIRECTIVE Module 7)

Scores leads based on behavioral signals, engagement data, and fit criteria.
Runs autonomously via event bus triggers or scheduled sweep.

Scoring dimensions (weighted):
  1. Behavioral signals (40%) — page visits, content consumption, form fills
  2. Engagement depth (25%) — time on site, return visits, email opens
  3. Fit criteria (20%) — company size, industry, geography match
  4. Recency (15%) — how recently they engaged

Score bands:
  0-39:  Cold (nurture)
  40-69: Warm (monitor)
  70-84: Hot (engage)
  85-100: Critical (act now)
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision


# Scoring weights
DIMENSION_WEIGHTS = {
    "behavioral": 0.40,
    "engagement": 0.25,
    "fit": 0.20,
    "recency": 0.15,
}

# Behavioral signal scores (0-100 per signal)
BEHAVIORAL_SCORES = {
    "page_visit": 5,
    "content_download": 20,
    "form_fill": 30,
    "demo_request": 50,
    "pricing_page": 25,
    "case_study_view": 15,
    "email_reply": 35,
    "social_engage": 10,
    "referral": 40,
    "return_visit": 15,
}

# Fit criteria scoring
FIT_SCORES = {
    "company_size": {
        "enterprise": 90, "mid-market": 75, "small-business": 50,
        "startup": 40, "individual": 20,
    },
    "industry_match": {
        "exact": 100, "adjacent": 60, "neutral": 30, "mismatch": 10,
    },
    "geography": {
        "local": 90, "national": 70, "international": 40,
    },
}


class LeadScoringEngine:
    """Autonomous lead scoring with multi-dimensional analysis."""

    def __init__(self):
        self.vault = get_context_vault()
        self.scores_dir = self.vault / "crm" / "lead_scores"
        self.scores_dir.mkdir(parents=True, exist_ok=True)
        self.score_log = self.scores_dir / "score_history.jsonl"
        self.bus = EPOSEventBus()

    def score_lead(self, contact_id: str, signals: List[dict] = None,
                   fit_data: dict = None) -> dict:
        """Score a single lead. Returns score breakdown."""
        signals = signals or []
        fit_data = fit_data or {}

        # Behavioral score (0-100)
        behavioral_raw = 0
        for sig in signals:
            sig_type = sig.get("type", "")
            behavioral_raw += BEHAVIORAL_SCORES.get(sig_type, 5)
        behavioral = min(100, behavioral_raw)

        # Engagement depth (0-100)
        engagement = self._calculate_engagement(signals)

        # Fit score (0-100)
        fit = self._calculate_fit(fit_data)

        # Recency score (0-100)
        recency = self._calculate_recency(signals)

        # Weighted composite
        composite = (
            behavioral * DIMENSION_WEIGHTS["behavioral"] +
            engagement * DIMENSION_WEIGHTS["engagement"] +
            fit * DIMENSION_WEIGHTS["fit"] +
            recency * DIMENSION_WEIGHTS["recency"]
        )
        composite = round(min(100, max(0, composite)))

        # Determine band
        if composite >= 85:
            band = "critical"
        elif composite >= 70:
            band = "hot"
        elif composite >= 40:
            band = "warm"
        else:
            band = "cold"

        result = {
            "contact_id": contact_id,
            "score": composite,
            "band": band,
            "dimensions": {
                "behavioral": round(behavioral, 1),
                "engagement": round(engagement, 1),
                "fit": round(fit, 1),
                "recency": round(recency, 1),
            },
            "signal_count": len(signals),
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

        # Log score
        with open(self.score_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")

        # Publish to event bus
        self.bus.publish("crm.lead.scored", {
            "contact_id": contact_id,
            "score": composite,
            "band": band,
        }, "lead_scoring")

        # Escalate critical leads to Friday
        if band == "critical":
            self.bus.publish("friday.signal.escalation", {
                "type": "hot_lead",
                "contact_id": contact_id,
                "score": composite,
                "priority": "critical",
                "message": f"Critical lead: {contact_id} scored {composite}/100",
            }, "lead_scoring")

        return result

    def _calculate_engagement(self, signals: list) -> float:
        """Calculate engagement depth score."""
        if not signals:
            return 0
        unique_types = len(set(s.get("type", "") for s in signals))
        total_signals = len(signals)
        # More diverse engagement = higher score
        diversity = min(100, unique_types * 15)
        volume = min(100, total_signals * 8)
        return (diversity * 0.6 + volume * 0.4)

    def _calculate_fit(self, fit_data: dict) -> float:
        """Calculate fit criteria score."""
        if not fit_data:
            return 50  # Neutral if unknown

        scores = []
        size = fit_data.get("company_size", "")
        if size:
            scores.append(FIT_SCORES["company_size"].get(size, 30))

        industry = fit_data.get("industry_match", "")
        if industry:
            scores.append(FIT_SCORES["industry_match"].get(industry, 30))

        geo = fit_data.get("geography", "")
        if geo:
            scores.append(FIT_SCORES["geography"].get(geo, 40))

        return sum(scores) / max(len(scores), 1) if scores else 50

    def _calculate_recency(self, signals: list) -> float:
        """Calculate recency score. More recent = higher."""
        if not signals:
            return 0
        # Find most recent signal
        latest = None
        for sig in signals:
            ts = sig.get("timestamp", sig.get("at", ""))
            if ts and (latest is None or ts > latest):
                latest = ts

        if not latest:
            return 30  # Default if no timestamps

        try:
            latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_ago = (now - latest_dt).total_seconds() / 3600
            # Decay: 100 at 0 hours, ~50 at 48 hours, ~0 at 168 hours (1 week)
            return max(0, min(100, 100 - (hours_ago / 168 * 100)))
        except Exception:
            return 30

    def score_all_contacts(self) -> list:
        """Score all contacts in the CRM database."""
        contacts = self._get_contacts_from_db()
        results = []
        for contact in contacts:
            interactions = self._get_interactions(contact.get("id", ""))
            signals = [{"type": i.get("interaction_type", "page_visit"),
                        "timestamp": i.get("created_at", "")}
                       for i in interactions]
            fit_data = {
                "company_size": self._estimate_company_size(contact.get("company", "")),
            }
            result = self.score_lead(str(contact["id"]), signals, fit_data)
            result["name"] = contact.get("name", "")
            result["email"] = contact.get("email", "")
            results.append(result)

        # Update scores in DB
        for r in results:
            self._update_score_in_db(r["contact_id"], r["score"])

        record_decision(
            decision_type="crm.lead_scoring.sweep",
            description=f"Scored {len(results)} contacts",
            agent_id="lead_scoring",
            outcome="success",
            context={"total": len(results),
                     "critical": len([r for r in results if r["band"] == "critical"]),
                     "hot": len([r for r in results if r["band"] == "hot"])},
        )

        return results

    def _estimate_company_size(self, company: str) -> str:
        """Rough company size estimation from name."""
        if not company:
            return "individual"
        company_lower = company.lower()
        if any(w in company_lower for w in ["inc", "corp", "group", "holdings", "global"]):
            return "enterprise"
        elif any(w in company_lower for w in ["llc", "ltd", "consulting", "agency"]):
            return "small-business"
        return "mid-market"

    def _get_contacts_from_db(self) -> list:
        """Get contacts from EPOS DB."""
        try:
            result = subprocess.run(
                ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                 "-t", "-A", "-F", "|",
                 "-c", "SELECT id, name, email, company, lead_score, stage "
                       "FROM epos.contacts ORDER BY id"],
                capture_output=True, text=True, timeout=10)
            rows = []
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    parts = line.split("|")
                    if len(parts) >= 6:
                        rows.append({
                            "id": parts[0], "name": parts[1], "email": parts[2],
                            "company": parts[3], "lead_score": parts[4], "stage": parts[5],
                        })
            return rows
        except Exception:
            return []

    def _get_interactions(self, contact_id: str) -> list:
        """Get interactions for a contact."""
        try:
            result = subprocess.run(
                ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                 "-t", "-A", "-F", "|",
                 "-c", f"SELECT id, interaction_type, channel, created_at "
                       f"FROM epos.interactions WHERE contact_id = {contact_id} "
                       f"ORDER BY created_at DESC LIMIT 50"],
                capture_output=True, text=True, timeout=10)
            rows = []
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    parts = line.split("|")
                    if len(parts) >= 4:
                        rows.append({
                            "id": parts[0], "interaction_type": parts[1],
                            "channel": parts[2], "created_at": parts[3],
                        })
            return rows
        except Exception:
            return []

    def _update_score_in_db(self, contact_id: str, score: int) -> None:
        """Update lead score in DB."""
        try:
            subprocess.run(
                ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                 "-c", f"UPDATE epos.contacts SET lead_score = {score} WHERE id = {contact_id}"],
                capture_output=True, text=True, timeout=10)
        except Exception:
            pass

    def get_score_summary(self) -> dict:
        """Get scoring summary from history."""
        if not self.score_log.exists():
            return {"total": 0, "bands": {}}
        bands = {"cold": 0, "warm": 0, "hot": 0, "critical": 0}
        total = 0
        for line in self.score_log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entry = json.loads(line)
                    band = entry.get("band", "cold")
                    bands[band] = bands.get(band, 0) + 1
                    total += 1
                except Exception:
                    pass
        return {"total": total, "bands": bands}


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile

    py_compile.compile("lead_scoring.py", doraise=True)
    print("PASS: lead_scoring.py compiles clean")

    engine = LeadScoringEngine()

    # Test with synthetic signals
    now = datetime.now(timezone.utc).isoformat()
    signals = [
        {"type": "page_visit", "timestamp": now},
        {"type": "pricing_page", "timestamp": now},
        {"type": "demo_request", "timestamp": now},
        {"type": "content_download", "timestamp": now},
        {"type": "email_reply", "timestamp": now},
    ]
    fit = {"company_size": "mid-market", "industry_match": "exact", "geography": "national"}

    result = engine.score_lead("TEST-001", signals, fit)
    assert result["score"] > 0
    assert result["band"] in ("cold", "warm", "hot", "critical")
    print(f"PASS: Lead scored — {result['score']}/100 ({result['band']})")
    print(f"  Behavioral: {result['dimensions']['behavioral']}")
    print(f"  Engagement: {result['dimensions']['engagement']}")
    print(f"  Fit: {result['dimensions']['fit']}")
    print(f"  Recency: {result['dimensions']['recency']}")

    # Test cold lead
    cold_result = engine.score_lead("TEST-002", [{"type": "page_visit"}], {})
    assert cold_result["score"] < result["score"]
    print(f"PASS: Cold lead — {cold_result['score']}/100 ({cold_result['band']})")

    # Test summary
    summary = engine.get_score_summary()
    assert summary["total"] >= 2
    print(f"PASS: Score summary — {summary['total']} scored, bands: {summary['bands']}")

    print("\nPASS: LeadScoringEngine — all tests passed")
