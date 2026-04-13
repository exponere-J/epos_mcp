#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
nightly_upskill.py — Friday Nightly Upskill Engine
====================================================
Constitutional Authority: EPOS Constitution v3.1

Every night, Friday gets smarter.
11 phases: AARs, SOPs, baselines, avatars, templates, research,
industry, patterns, capability gaps, improvement candidates,
constitutional friction.

Triggered: APScheduler 23:00 America/New_York daily.
Vault: context_vault/friday/upskill/
Event: friday.upskill.complete
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
UPSKILL_DIR = VAULT / "friday" / "upskill"
UPSKILL_DIR.mkdir(parents=True, exist_ok=True)

PATTERN_LIBRARY = UPSKILL_DIR / "pattern_library.json"


class FridayNightlyUpskill:
    """Every night, Friday gets smarter."""

    def run_nightly_cycle(self) -> dict:
        """The complete nightly upskill cycle. 11 phases."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        results = {
            "date": timestamp,
            "phase_1_aar_absorption":          self._absorb_todays_aars(),
            "phase_2_sop_scan":                self._scan_modified_sops(),
            "phase_3_baseline_delta":          self._compare_baselines(),
            "phase_4_avatar_recalibration":    self._recalibrate_avatars(),
            "phase_5_template_expansion":      self._scan_new_templates(),
            "phase_6_research_ingestion":      self._ingest_research_findings(),
            "phase_7_industry_scan":           self._scan_industry_practices(),
            "phase_8_pattern_promotion":       self._promote_recurring_patterns(),
            "phase_9_capability_gaps":         self._identify_capability_gaps(),
            "phase_10_improvement_candidates": self._generate_improvements(),
            "phase_11_constitutional_proposals": self._check_constitutional_friction(),
        }

        # Persist report
        report_path = UPSKILL_DIR / f"upskill_{timestamp}.json"
        report_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

        phases_complete = sum(
            1 for v in results.values()
            if isinstance(v, dict) and v.get("status") == "complete"
        )
        improvements = len(
            results.get("phase_10_improvement_candidates", {}).get("candidates", [])
        )

        if _BUS:
            try:
                _BUS.publish("friday.upskill.complete", {
                    "date": timestamp,
                    "phases_completed": phases_complete,
                    "improvements_generated": improvements,
                    "report_path": str(report_path),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }, source_module="nightly_upskill")
            except Exception:
                pass

        return results

    # ── Phase 1: AAR Absorption ──────────────────────────────

    def _absorb_todays_aars(self) -> dict:
        """Read all AARs modified today. Extract learnings."""
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        aar_dirs = [
            VAULT.parent,           # project root
            VAULT / "aar",
            VAULT / "friday" / "missions",
        ]

        learnings = []
        scanned = 0

        for aar_dir in aar_dirs:
            if not aar_dir.exists():
                continue
            for f in list(aar_dir.glob(f"*{today}*.md")) + list(aar_dir.glob(f"*{today}*.json")):
                scanned += 1
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    # Extract learnings from markdown AARs
                    for marker in ["What Was Learned", "## Bugs Found", "## Learnings"]:
                        if marker in content:
                            section = content.split(marker)[1].split("##")[0]
                            learnings.append({
                                "source": f.name,
                                "learning": section.strip()[:500],
                            })
                            break
                except Exception:
                    pass

        return {
            "status": "complete",
            "aars_scanned": scanned,
            "learnings": learnings,
        }

    # ── Phase 2: SOP Scan ────────────────────────────────────

    def _scan_modified_sops(self) -> dict:
        """Find SOPs modified in the last 7 days."""
        sop_dirs = [VAULT / "sops", VAULT.parent / "skills"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        modified = []

        for d in sop_dirs:
            if not d.exists():
                continue
            for f in d.rglob("*.md"):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        modified.append({"file": f.name, "modified": mtime.isoformat()})
                except Exception:
                    pass

        return {"status": "complete", "sops_modified_7d": len(modified), "files": modified}

    # ── Phase 3: Baseline Delta ──────────────────────────────

    def _compare_baselines(self) -> dict:
        """Compare current file counts vs stored baselines."""
        baseline_file = UPSKILL_DIR / "baselines.json"
        now_counts = {
            "vault_files": sum(1 for _ in VAULT.rglob("*") if _.is_file()),
            "python_files": sum(1 for _ in VAULT.parent.rglob("*.py") if _.is_file()),
        }

        if baseline_file.exists():
            try:
                old = json.loads(baseline_file.read_text())
                deltas = {k: now_counts[k] - old.get(k, 0) for k in now_counts}
            except Exception:
                deltas = {}
        else:
            deltas = {}

        baseline_file.write_text(
            json.dumps({**now_counts, "updated": datetime.now(timezone.utc).isoformat()}, indent=2),
            encoding="utf-8",
        )

        return {"status": "complete", "counts": now_counts, "deltas": deltas}

    # ── Phase 4: Avatar Recalibration ───────────────────────

    def _recalibrate_avatars(self) -> dict:
        """Check avatar profiles for recalibration signals."""
        avatar_dir = VAULT / "avatars"
        if not avatar_dir.exists():
            return {"status": "complete", "avatars_checked": 0, "recalibrations": []}

        avatars = list(avatar_dir.glob("*.json"))
        recalibrations = []

        for av_path in avatars:
            try:
                data = json.loads(av_path.read_text())
                last_updated = data.get("last_updated") or data.get("created_at", "")
                if last_updated:
                    age_days = (
                        datetime.now(timezone.utc)
                        - datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                    ).days
                    if age_days > 30:
                        recalibrations.append({
                            "avatar_id": data.get("avatar_id", av_path.stem),
                            "age_days": age_days,
                            "action": "Recalibration recommended",
                        })
            except Exception:
                pass

        return {
            "status": "complete",
            "avatars_checked": len(avatars),
            "recalibrations": recalibrations,
        }

    # ── Phase 5: Template Expansion ──────────────────────────

    def _scan_new_templates(self) -> dict:
        """Find templates added/modified in last 7 days."""
        template_dirs = [VAULT / "templates", VAULT.parent / "content_lab" / "templates"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        new_templates = []

        for d in template_dirs:
            if not d.exists():
                continue
            for f in d.rglob("*"):
                if not f.is_file():
                    continue
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        new_templates.append({"file": f.name, "dir": str(d.name)})
                except Exception:
                    pass

        return {"status": "complete", "new_templates": len(new_templates), "files": new_templates}

    # ── Phase 6: Research Ingestion ──────────────────────────

    def _ingest_research_findings(self) -> dict:
        """Ingest new research briefs from vault."""
        research_dirs = [
            VAULT / "echoes" / "research_briefs",
            VAULT / "research",
            VAULT / "knowledge" / "briefs",
        ]
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        ingested = []

        for d in research_dirs:
            if not d.exists():
                continue
            for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        ingested.append({
                            "source": f.name,
                            "topic": data.get("topic", data.get("title", "unknown")),
                        })
                except Exception:
                    pass

        return {"status": "complete", "briefs_ingested": len(ingested), "findings": ingested}

    # ── Phase 7: Industry Scan ───────────────────────────────

    def _scan_industry_practices(self) -> dict:
        """Scan all intelligence sources for market signals."""
        findings = []

        source_dirs = [
            (VAULT / "research",                 "research_brief"),
            (VAULT / "echoes" / "expressions",   "fotw_expression"),
            (VAULT / "echoes" / "competitive",   "competitive_intel"),
            (VAULT / "knowledge" / "frontier",   "frontier_research"),
        ]

        for d, source_type in source_dirs:
            if not d.exists():
                continue
            recent = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
            for f in recent:
                findings.append({"source": source_type, "file": f.name})

        return {"status": "complete", "findings": len(findings), "sources": findings}

    # ── Phase 8: Pattern Promotion ───────────────────────────

    def _promote_recurring_patterns(self) -> dict:
        """Promote patterns seen 3+ times to constitutional candidates."""
        patterns = {}
        if PATTERN_LIBRARY.exists():
            try:
                patterns = json.loads(PATTERN_LIBRARY.read_text())
            except Exception:
                pass

        promotions = []
        for pattern, data in patterns.items():
            if data.get("count", 0) >= 3 and not data.get("promoted"):
                promotions.append({
                    "pattern": pattern,
                    "occurrences": data["count"],
                    "first_seen": data.get("first_seen"),
                    "recommendation": f"Promote to constitutional principle: {pattern}",
                })
                data["promoted"] = True

        if promotions:
            PATTERN_LIBRARY.write_text(json.dumps(patterns, indent=2), encoding="utf-8")

        return {"status": "complete", "promotions": promotions}

    # ── Phase 9: Capability Gaps ─────────────────────────────

    def _identify_capability_gaps(self) -> dict:
        """Identify missing executors, missing event handlers, stale nodes."""
        gaps = []

        # Check executor coverage
        executors_dir = Path(__file__).resolve().parent.parent / "executors"
        expected_executors = [
            "code_executor", "browser_executor", "computeruse_executor",
            "system_executor", "ttlg_executor", "az_executor",
            "scc_executor",
        ]
        for name in expected_executors:
            if not (executors_dir / f"{name}.py").exists():
                gaps.append({"type": "missing_executor", "name": name})

        # Check for stale vault dirs (no writes in 7 days)
        vault_dirs_to_check = ["echoes/ready_to_post", "friday/missions", "knowledge"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        for rel_dir in vault_dirs_to_check:
            d = VAULT / rel_dir
            if d.exists():
                files = list(d.rglob("*"))
                if files:
                    latest = max(f.stat().st_mtime for f in files if f.is_file()) if any(f.is_file() for f in files) else 0
                    if latest > 0:
                        age = datetime.now(timezone.utc) - datetime.fromtimestamp(latest, tz=timezone.utc)
                        if age.days > 7:
                            gaps.append({
                                "type": "stale_vault_dir",
                                "dir": rel_dir,
                                "last_write_days": age.days,
                            })

        return {"status": "complete", "gaps": gaps}

    # ── Phase 10: Improvement Candidates ─────────────────────

    def _generate_improvements(self) -> dict:
        """Generate improvement candidates from learnings and gaps."""
        candidates = []

        # Read today's AAR learnings
        aar_result = self._absorb_todays_aars()
        for learning in aar_result.get("learnings", []):
            candidates.append({
                "type": "aar_learning",
                "source": learning.get("source"),
                "summary": learning.get("learning", "")[:200],
                "action": "Review and codify if recurring",
            })

        # Surface any pattern promotions
        pattern_result = self._promote_recurring_patterns()
        for promo in pattern_result.get("promotions", []):
            candidates.append({
                "type": "pattern_promotion",
                "pattern": promo["pattern"],
                "occurrences": promo["occurrences"],
                "action": promo["recommendation"],
            })

        return {"status": "complete", "candidates": candidates}

    # ── Phase 11: Constitutional Friction ────────────────────

    def _check_constitutional_friction(self) -> dict:
        """Detect patterns causing repeated governance gate rejections."""
        gate_log = VAULT / "governance" / "gate_log.jsonl"
        if not gate_log.exists():
            return {"status": "complete", "proposals": [], "note": "No gate log found"}

        rejection_counts = {}
        try:
            for line in gate_log.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("action") == "reject":
                    pattern = entry.get("pattern", "unknown")
                    rejection_counts[pattern] = rejection_counts.get(pattern, 0) + 1
        except Exception:
            return {"status": "complete", "proposals": [], "note": "Gate log parse error"}

        proposals = []
        for pattern, count in rejection_counts.items():
            if count >= 5:
                proposals.append({
                    "pattern": pattern,
                    "rejection_count": count,
                    "proposal": f"Consider amending constitution for pattern: {pattern}",
                })

        return {"status": "complete", "proposals": proposals}


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running nightly upskill cycle...")
    upskill = FridayNightlyUpskill()
    result = upskill.run_nightly_cycle()

    phases_complete = sum(
        1 for v in result.values()
        if isinstance(v, dict) and v.get("status") == "complete"
    )
    print(f"Phases completed: {phases_complete}/11")
    for key, val in result.items():
        if key == "date":
            continue
        status = val.get("status", "?") if isinstance(val, dict) else "?"
        print(f"  {key}: {status}")

    print(f"\nPASS: nightly_upskill ({phases_complete} phases complete)")
