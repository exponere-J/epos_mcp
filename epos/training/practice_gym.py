#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/training/practice_gym.py — SCC Practice Gym & Examination Engine
======================================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-05 (SCC Shadow Protocol)

Sandbox execution environment for SCC training.
Runs 3-try exam protocol with merit-decay scoring.
Generates mission shadow runs for pattern detection.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))
SANDBOX_ROOT = Path("/app/epos/sandbox")
TRAINING_DIR = EPOS_ROOT / "context_vault" / "training"
PAIRS_DIR = TRAINING_DIR / "pairs"
GRADES_DIR = TRAINING_DIR / "grades"
UMEP_REGISTRY_PATH = EPOS_ROOT / "context_vault" / "training" / "umep_registry.json"

# Merit decay per try
TRY_MULTIPLIERS = {
    1: 1.00,   # Try 1 — full merit
    2: 0.85,   # Try 2 — 15% decay
    3: 0.70,   # Try 3 — 30% decay
}

MAX_TRIES = 3
PASSING_MERIT = 75  # Minimum passing score (out of 100)


class PracticeGym:
    """
    Sandbox isolation and examination engine for SCC model training.

    Provides:
    - seed_session(): Initialize sandbox with directive baseline files
    - run_scc_exam(): 3-try exam protocol with merit-decay scoring
    - run_mission_shadow(): Full mission shadow run for pattern detection
    - commit_grade(): Persist grade to UMEP registry + training record
    """

    def __init__(self, model_id: str = "SCC-DEFAULT"):
        self.model_id = model_id
        self.shadow_protocol = self._load_shadow_protocol()
        SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
        TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        PAIRS_DIR.mkdir(parents=True, exist_ok=True)
        GRADES_DIR.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _load_shadow_protocol(self):
        """Lazy-load ShadowProtocol to avoid circular imports."""
        try:
            from epos.training.shadow_protocol import ShadowProtocol
            return ShadowProtocol()
        except ImportError:
            return None

    def _session_sandbox(self, directive_id: str) -> Path:
        """Return (and create) isolated sandbox directory for this session."""
        sandbox = SANDBOX_ROOT / directive_id
        sandbox.mkdir(parents=True, exist_ok=True)
        return sandbox

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _load_umep(self) -> dict:
        if UMEP_REGISTRY_PATH.exists():
            return json.loads(UMEP_REGISTRY_PATH.read_text())
        return {"models": {}, "updated_at": self._now_iso()}

    def _save_umep(self, registry: dict):
        registry["updated_at"] = self._now_iso()
        UMEP_REGISTRY_PATH.write_text(json.dumps(registry, indent=2, default=str))

    def _validate_python_syntax(self, file_path: Path) -> tuple:
        """Check Python syntax. Returns (ok: bool, error: str)."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(file_path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, "syntax OK"
            return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def _check_governance_watermark(self, content: str) -> bool:
        return "EPOS GOVERNANCE WATERMARK" in content

    def _check_bom(self, file_path: Path) -> bool:
        """Returns True if file is BOM-clean."""
        raw = file_path.read_bytes()
        return not raw.startswith(b'\xef\xbb\xbf')

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def seed_session(self, directive_id: str, directive_content: str) -> dict:
        """
        Initialize sandbox for an SCC exam session.

        Writes directive spec to sandbox, records session metadata,
        and returns the session manifest.

        Args:
            directive_id: e.g. "20260413-03A"
            directive_content: Raw directive text (markdown or JSON string)

        Returns:
            {
                "session_id": str,
                "sandbox_path": str,
                "directive_id": str,
                "seeded_at": str,
                "status": "ready"
            }
        """
        session_id = f"GYM-{directive_id}-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        sandbox = self._session_sandbox(directive_id)

        # Write directive spec into sandbox
        spec_path = sandbox / "directive_spec.md"
        spec_path.write_text(directive_content, encoding="utf-8")

        # Session manifest
        manifest = {
            "session_id": session_id,
            "model_id": self.model_id,
            "directive_id": directive_id,
            "sandbox_path": str(sandbox),
            "seeded_at": self._now_iso(),
            "status": "ready",
            "tries_used": 0,
            "current_try": 1,
        }

        manifest_path = sandbox / "session_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        return manifest

    def run_scc_exam(self, directive_id: str, file_specs: list) -> dict:
        """
        Run 3-try exam protocol on a set of SCC-produced files.

        Each file_spec: {"scc_path": str, "baseline_path": str, "name": str}

        Try 1 = 100% merit ceiling
        Try 2 = 85% merit ceiling  (if Try 1 merit < PASSING_MERIT)
        Try 3 = 70% merit ceiling  (if Try 2 merit < PASSING_MERIT)

        Args:
            directive_id: Directive being examined
            file_specs: List of {scc_path, baseline_path, name} dicts

        Returns:
            {
                "exam_id": str,
                "directive_id": str,
                "model_id": str,
                "tries": [try_result, ...],
                "best_try": int,
                "best_merit": int,
                "passed": bool,
                "final_grade": str,
                "file_scores": dict,
                "gaps": [str],
                "completed_at": str
            }
        """
        if not self.shadow_protocol:
            return {"error": "ShadowProtocol not available — check epos/training/shadow_protocol.py"}

        exam_id = f"EXAM-{directive_id}-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        sandbox = self._session_sandbox(directive_id)

        tries = []
        best_merit = 0
        best_try = 1
        final_file_scores = {}
        final_gaps = []

        for try_num in range(1, MAX_TRIES + 1):
            try_multiplier = TRY_MULTIPLIERS[try_num]
            file_scores = {}
            all_gaps = []

            for spec in file_specs:
                scc_path = spec.get("scc_path", "")
                baseline_path = spec.get("baseline_path", "")
                name = spec.get("name", Path(scc_path).name if scc_path else "unknown")

                if not scc_path or not Path(scc_path).exists():
                    file_scores[name] = {
                        "error": f"SCC file not found: {scc_path}",
                        "total": 0, "grade": "F",
                        "gaps": ["file_missing"]
                    }
                    all_gaps.append("file_missing")
                    continue

                if not baseline_path or not Path(baseline_path).exists():
                    # No baseline — do quality-only scoring
                    content = Path(scc_path).read_text(errors="ignore")
                    scc_file = Path(scc_path)

                    quality_score = 100
                    gaps = []

                    if not self._check_governance_watermark(content):
                        quality_score -= 15
                        gaps.append("missing_governance_watermark")
                    if not self._check_bom(scc_file):
                        quality_score -= 10
                        gaps.append("bom_present")

                    syntax_ok, syntax_err = self._validate_python_syntax(scc_file)
                    if not syntax_ok:
                        quality_score -= 40
                        gaps.append(f"syntax_error: {syntax_err[:80]}")

                    raw_merit = max(0, quality_score)
                    decayed_merit = int(raw_merit * try_multiplier)

                    file_scores[name] = {
                        "total": decayed_merit,
                        "raw": raw_merit,
                        "try": try_num,
                        "multiplier": try_multiplier,
                        "grade": self._merit_to_grade(decayed_merit),
                        "gaps": gaps,
                        "note": "quality-only (no baseline)"
                    }
                    all_gaps.extend(gaps)
                    continue

                # Full shadow comparison
                comparison = self.shadow_protocol.compare_files(baseline_path, scc_path)
                score = self.shadow_protocol.score_merit(comparison)

                raw_merit = score["total"]
                decayed_merit = int(raw_merit * try_multiplier)

                file_scores[name] = {
                    "total": decayed_merit,
                    "raw": raw_merit,
                    "try": try_num,
                    "multiplier": try_multiplier,
                    "grade": self._merit_to_grade(decayed_merit),
                    "breakdown": score["breakdown"],
                    "gaps": score["gaps"],
                }
                all_gaps.extend(score["gaps"])

            # Aggregate try score
            if file_scores:
                scores_list = [v["total"] for v in file_scores.values() if "total" in v]
                aggregate_merit = int(sum(scores_list) / len(scores_list)) if scores_list else 0
            else:
                aggregate_merit = 0

            try_result = {
                "try": try_num,
                "multiplier": try_multiplier,
                "aggregate_merit": aggregate_merit,
                "passed": aggregate_merit >= PASSING_MERIT,
                "file_scores": file_scores,
                "gap_count": len(all_gaps),
                "unique_gaps": list(set(all_gaps)),
            }
            tries.append(try_result)

            if aggregate_merit > best_merit:
                best_merit = aggregate_merit
                best_try = try_num
                final_file_scores = file_scores
                final_gaps = list(set(all_gaps))

            # Pass on first try that meets threshold
            if aggregate_merit >= PASSING_MERIT:
                break

        passed = best_merit >= PASSING_MERIT
        final_grade = self._merit_to_grade(best_merit)

        result = {
            "exam_id": exam_id,
            "directive_id": directive_id,
            "model_id": self.model_id,
            "tries": tries,
            "tries_used": len(tries),
            "best_try": best_try,
            "best_merit": best_merit,
            "passed": passed,
            "final_grade": final_grade,
            "file_scores": final_file_scores,
            "gaps": final_gaps,
            "completed_at": self._now_iso(),
        }

        # Persist exam result to sandbox
        exam_path = sandbox / f"exam_{exam_id}.json"
        exam_path.write_text(json.dumps(result, indent=2, default=str))

        return result

    def run_mission_shadow(self, directive_id: str) -> dict:
        """
        Full mission shadow run: compare all SCC-produced files against
        Desktop CODE baselines for a completed directive.

        Discovers file pairs automatically from sandbox directory.
        Runs score_mission() for pattern-level analysis.
        Calls generate_training_pairs() if patterns found.

        Args:
            directive_id: e.g. "20260413-03A"

        Returns:
            {
                "shadow_id": str,
                "directive_id": str,
                "aggregate_merit": int,
                "per_file": dict,
                "patterns": list,
                "qlora_targets": list,
                "training_pairs_written": int,
                "completed_at": str
            }
        """
        if not self.shadow_protocol:
            return {"error": "ShadowProtocol not available"}

        shadow_id = f"SHADOW-{directive_id}-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        sandbox = self._session_sandbox(directive_id)

        # Discover baseline/scc pairs from sandbox
        # Expects: sandbox/{name}.baseline.py and sandbox/{name}.scc.py
        pairs_found = {}
        for baseline_file in sandbox.glob("*.baseline.*"):
            stem = baseline_file.stem.replace(".baseline", "")
            suffix = baseline_file.suffix
            scc_file = sandbox / f"{stem}.scc{suffix}"
            if scc_file.exists():
                pairs_found[stem] = {
                    "baseline": str(baseline_file),
                    "scc": str(scc_file),
                }

        # Also check manifest for explicit file_specs
        manifest_path = sandbox / "session_manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            for spec in manifest.get("file_specs", []):
                name = spec.get("name", "unknown")
                if spec.get("baseline_path") and spec.get("scc_path"):
                    pairs_found[name] = {
                        "baseline": spec["baseline_path"],
                        "scc": spec["scc_path"],
                    }

        if not pairs_found:
            return {
                "shadow_id": shadow_id,
                "directive_id": directive_id,
                "error": "No baseline/scc file pairs found in sandbox",
                "sandbox_path": str(sandbox),
                "completed_at": self._now_iso(),
            }

        # Score all file pairs
        file_scores = {}
        for name, paths in pairs_found.items():
            comparison = self.shadow_protocol.compare_files(paths["baseline"], paths["scc"])
            score = self.shadow_protocol.score_merit(comparison)
            file_scores[name] = score

        # Mission-level analysis
        mission_score = self.shadow_protocol.score_mission(directive_id, file_scores)

        # Generate training pairs if patterns found
        training_pairs_written = 0
        if mission_score.get("patterns"):
            pairs = self.shadow_protocol.generate_training_pairs(
                file_scores,
                mission_score["patterns"],
                directive_id
            )
            training_pairs_written = len(pairs)

        # Track merit in timeline
        aggregate_merit = mission_score.get("aggregate", 0)
        all_gaps = []
        for fs in file_scores.values():
            all_gaps.extend(fs.get("gaps", []))

        self.shadow_protocol.track_merit(
            self.model_id,
            directive_id,
            aggregate_merit,
            list(set(all_gaps))
        )

        result = {
            "shadow_id": shadow_id,
            "directive_id": directive_id,
            "model_id": self.model_id,
            "aggregate_merit": aggregate_merit,
            "per_file": {
                name: {
                    "total": s["total"],
                    "grade": s["grade"],
                    "gaps": s["gaps"],
                }
                for name, s in file_scores.items()
            },
            "patterns": mission_score.get("patterns", []),
            "qlora_targets": mission_score.get("qlora_targets", []),
            "training_pairs_written": training_pairs_written,
            "file_count": len(file_scores),
            "completed_at": self._now_iso(),
        }

        # Persist shadow result
        shadow_path = sandbox / f"shadow_{shadow_id}.json"
        shadow_path.write_text(json.dumps(result, indent=2, default=str))

        return result

    def commit_grade(self, directive_id: str, scores: dict, progress_report: str) -> dict:
        """
        Commit final grade to UMEP registry and training record.

        Updates model's certification level if graduation criteria met.
        Writes grade record to context_vault/training/grades/.

        Args:
            directive_id: Directive that was examined
            scores: {aggregate_merit, per_file, grade, gaps, ...}
            progress_report: Free-text narrative of what was learned

        Returns:
            {
                "grade_id": str,
                "model_id": str,
                "directive_id": str,
                "merit": int,
                "grade": str,
                "certification_level": int,
                "level_changed": bool,
                "committed_at": str
            }
        """
        grade_id = f"GRADE-{self.model_id}-{directive_id}-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        merit = scores.get("aggregate_merit", scores.get("total", scores.get("best_merit", 0)))
        grade = scores.get("final_grade", scores.get("grade", self._merit_to_grade(merit)))

        # Load UMEP registry
        registry = self._load_umep()
        model_entry = registry.get("models", {}).get(self.model_id, {
            "model_id": self.model_id,
            "certification_level": 0,
            "missions_completed": [],
            "merit_history": [],
            "registered_at": self._now_iso(),
        })

        # Update merit history
        model_entry.setdefault("merit_history", []).append({
            "directive_id": directive_id,
            "merit": merit,
            "grade": grade,
            "recorded_at": self._now_iso(),
        })

        # Track mission completion
        if directive_id not in model_entry.get("missions_completed", []):
            model_entry.setdefault("missions_completed", []).append(directive_id)

        # Check graduation criteria
        old_level = model_entry.get("certification_level", 0)
        new_level = self._evaluate_certification(model_entry)
        level_changed = new_level != old_level

        if level_changed:
            model_entry["certification_level"] = new_level
            model_entry["last_promotion"] = self._now_iso()

        model_entry["last_merit"] = merit
        model_entry["last_grade"] = grade
        model_entry["last_directive"] = directive_id
        model_entry["updated_at"] = self._now_iso()

        # Persist back to registry
        registry.setdefault("models", {})[self.model_id] = model_entry
        self._save_umep(registry)

        # Write grade record
        grade_record = {
            "grade_id": grade_id,
            "model_id": self.model_id,
            "directive_id": directive_id,
            "merit": merit,
            "grade": grade,
            "gaps": scores.get("gaps", []),
            "per_file": scores.get("per_file", scores.get("file_scores", {})),
            "progress_report": progress_report,
            "certification_level_before": old_level,
            "certification_level_after": new_level,
            "level_changed": level_changed,
            "committed_at": self._now_iso(),
        }

        grade_path = GRADES_DIR / f"{grade_id}.json"
        grade_path.write_text(json.dumps(grade_record, indent=2, default=str))

        return {
            "grade_id": grade_id,
            "model_id": self.model_id,
            "directive_id": directive_id,
            "merit": merit,
            "grade": grade,
            "certification_level": new_level,
            "level_changed": level_changed,
            "missions_completed": len(model_entry.get("missions_completed", [])),
            "committed_at": self._now_iso(),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Certification evaluation
    # ──────────────────────────────────────────────────────────────────────────

    def _merit_to_grade(self, merit: int) -> str:
        if merit >= 90:
            return "A"
        elif merit >= 80:
            return "B"
        elif merit >= 70:
            return "C"
        elif merit >= 60:
            return "D"
        else:
            return "F"

    def _evaluate_certification(self, model_entry: dict) -> int:
        """
        Evaluate certification level based on merit history.

        Level 0: Unassessed
        Level 1: Attempt — any grade recorded
        Level 2: Junior — 3+ missions, avg merit ≥ 60
        Level 3: Intermediate — 7+ missions, avg merit ≥ 75
        Level 4: Senior — 15+ missions, avg merit ≥ 85
        Level 5: Autonomous — 30+ missions, avg merit ≥ 90, sustained 7 days
        """
        history = model_entry.get("merit_history", [])
        missions = model_entry.get("missions_completed", [])
        n_missions = len(missions)

        if not history:
            return 0

        merits = [h["merit"] for h in history]
        avg_merit = sum(merits) / len(merits) if merits else 0

        # Level 5: Autonomous
        if n_missions >= 30 and avg_merit >= 90:
            # Check 7-day sustainability (last 7 days avg)
            recent = [h for h in history[-10:]]
            if recent:
                recent_avg = sum(h["merit"] for h in recent) / len(recent)
                if recent_avg >= 90:
                    return 5

        # Level 4: Senior
        if n_missions >= 15 and avg_merit >= 85:
            return 4

        # Level 3: Intermediate
        if n_missions >= 7 and avg_merit >= 75:
            return 3

        # Level 2: Junior
        if n_missions >= 3 and avg_merit >= 60:
            return 2

        # Level 1: Attempt
        return 1

    # ──────────────────────────────────────────────────────────────────────────
    # Sandbox utilities
    # ──────────────────────────────────────────────────────────────────────────

    def clean_sandbox(self, directive_id: str) -> dict:
        """Remove sandbox for a directive after exam is committed."""
        sandbox = self._session_sandbox(directive_id)
        if sandbox.exists():
            shutil.rmtree(sandbox)
            return {"cleaned": True, "path": str(sandbox)}
        return {"cleaned": False, "path": str(sandbox), "note": "not found"}

    def list_sessions(self) -> list:
        """List all active sandbox sessions."""
        if not SANDBOX_ROOT.exists():
            return []
        sessions = []
        for d in SANDBOX_ROOT.iterdir():
            if d.is_dir():
                manifest_path = d / "session_manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    sessions.append({
                        "directive_id": manifest.get("directive_id"),
                        "session_id": manifest.get("session_id"),
                        "status": manifest.get("status"),
                        "seeded_at": manifest.get("seeded_at"),
                    })
                else:
                    sessions.append({"directive_id": d.name, "status": "no_manifest"})
        return sessions
