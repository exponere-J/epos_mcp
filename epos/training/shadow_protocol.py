#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/training/shadow_protocol.py — SCC Shadow Protocol + Merit Scoring
========================================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-05 (SCC Shadow Protocol — Merit-Based Education)

Structured comparison, merit scoring, pattern analysis, and training
pair generation for model education. Operates at pattern level —
one training target per recurring gap type, not per individual file.
"""

from __future__ import annotations

import json
import re
import difflib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EPOS_ROOT = Path("/app")
MERIT_FILE = EPOS_ROOT / "context_vault" / "training" / "merit_timeline.jsonl"
PAIRS_DIR = EPOS_ROOT / "context_vault" / "training" / "pairs"

# ── Reward bus (Directive 20260414-02) ────────────────────────────────────────
try:
    from epos.rewards.publish_reward import publish_reward as _pub_reward
    def _reward(signal_name: str, value: float, signal_type: str = "process",
                context: str = "", needs_review: bool = False) -> None:
        try:
            _pub_reward(signal_name=signal_name, value=value,
                        signal_type=signal_type, source="shadow_protocol",
                        context=context, needs_review=needs_review)
        except Exception:
            pass
except ImportError:
    def _reward(*a, **kw): pass

# ── Divergence classification weights ──────────────────────────
DIVERGENCE_TYPES = {
    "missing_implementation": {"weight": 0.40, "category": "functional"},
    "stub_instead_of_implementation": {"weight": 0.40, "category": "functional"},
    "missing_error_handling": {"weight": 0.20, "category": "quality"},
    "missing_governance_watermark": {"weight": 0.15, "category": "compliance"},
    "missing_event_publishing": {"weight": 0.10, "category": "compliance"},
    "missing_posix_path": {"weight": 0.10, "category": "compliance"},
    "missing_docstring": {"weight": 0.08, "category": "quality"},
    "missing_type_hints": {"weight": 0.05, "category": "quality"},
    "wrong_pattern": {"weight": 0.15, "category": "compliance"},
    "extra_code": {"weight": 0.02, "category": "style"},
    "style_divergence": {"weight": 0.01, "category": "style"},
}

# Merit score weights
MERIT_WEIGHTS = {
    "functional_correctness": 0.40,
    "code_quality": 0.25,
    "epos_compliance": 0.20,
    "completeness": 0.15,
}


class ShadowProtocol:
    """
    Audits SCC-produced files against Desktop CODE baselines.
    Scores merit, identifies patterns, generates training pairs.
    """

    def compare_files(self, baseline_path: str, scc_path: str) -> dict:
        """Line-by-line structured diff with divergence classification.

        Returns:
            {
                matching_lines_pct: float,
                divergences: [{type, baseline_line, scc_line, line_num}],
                missing_features: [str],
                quality_checks: {docstrings, type_hints, error_handling,
                                  governance_watermark, event_publishing,
                                  posix_paths}
            }
        """
        baseline = Path(baseline_path)
        scc = Path(scc_path)

        if not baseline.exists():
            return {"error": f"Baseline not found: {baseline_path}"}
        if not scc.exists():
            return {"error": f"SCC file not found: {scc_path}", "stub": True}

        base_lines = baseline.read_text(errors="ignore").splitlines()
        scc_lines = scc.read_text(errors="ignore").splitlines()
        base_text = baseline.read_text(errors="ignore")
        scc_text = scc.read_text(errors="ignore")

        # Line-level matching
        matcher = difflib.SequenceMatcher(None, base_lines, scc_lines, autojunk=False)
        matching = sum(block.size for block in matcher.get_matching_blocks())
        total = max(len(base_lines), 1)
        matching_pct = round((matching / total) * 100, 1)

        # Classify divergences
        divergences = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            base_chunk = "\n".join(base_lines[i1:i2])
            scc_chunk = "\n".join(scc_lines[j1:j2])
            dtype = self._classify_divergence(base_chunk, scc_chunk)
            divergences.append({
                "type": dtype,
                "baseline_lines": f"{i1+1}-{i2}",
                "scc_lines": f"{j1+1}-{j2}",
                "baseline_excerpt": base_chunk[:200],
                "scc_excerpt": scc_chunk[:200],
            })

        # Quality checks (binary)
        quality_checks = {
            "has_governance_watermark": "EPOS GOVERNANCE WATERMARK" in scc_text,
            "has_docstrings": '"""' in scc_text or "'''" in scc_text,
            "has_type_hints": "->" in scc_text or ": str" in scc_text or ": dict" in scc_text,
            "has_error_handling": "try:" in scc_text and "except" in scc_text,
            "has_event_publishing": "_BUS" in scc_text or "publish(" in scc_text or "event_bus" in scc_text.lower(),
            "has_posix_paths": "os.getenv" in scc_text and "EPOS_ROOT" in scc_text,
            "no_windows_paths": not bool(re.search(r'["\'][A-Za-z]:[/\\]', scc_text)),
            "no_bom": not scc_text.startswith("\ufeff"),
        }

        # Missing features: things in baseline not at all in scc
        missing_features = []
        base_funcs = set(re.findall(r'def (\w+)\(', base_text))
        scc_funcs = set(re.findall(r'def (\w+)\(', scc_text))
        missing_funcs = base_funcs - scc_funcs
        if missing_funcs:
            missing_features.append(f"Missing functions: {sorted(missing_funcs)}")

        base_classes = set(re.findall(r'class (\w+)', base_text))
        scc_classes = set(re.findall(r'class (\w+)', scc_text))
        missing_classes = base_classes - scc_classes
        if missing_classes:
            missing_features.append(f"Missing classes: {sorted(missing_classes)}")

        # Stub detection
        is_stub = (
            len(scc_lines) < 5 or
            (len(scc_lines) < len(base_lines) * 0.2 and len(base_lines) > 10) or
            (scc_text.strip().endswith("#!/usr/bin/env python3") and len(scc_lines) <= 3)
        )

        return {
            "baseline_path": baseline_path,
            "scc_path": scc_path,
            "matching_lines_pct": matching_pct,
            "baseline_lines": len(base_lines),
            "scc_lines": len(scc_lines),
            "is_stub": is_stub,
            "divergences": divergences,
            "missing_features": missing_features,
            "quality_checks": quality_checks,
        }

    def _classify_divergence(self, base_chunk: str, scc_chunk: str) -> str:
        """Classify a divergence block into a training-relevant type."""
        if not scc_chunk.strip():
            return "missing_implementation"
        if not base_chunk.strip():
            return "extra_code"
        if "try:" in base_chunk and "try:" not in scc_chunk:
            return "missing_error_handling"
        if "EPOS GOVERNANCE WATERMARK" in base_chunk and "EPOS GOVERNANCE WATERMARK" not in scc_chunk:
            return "missing_governance_watermark"
        if "publish(" in base_chunk and "publish(" not in scc_chunk:
            return "missing_event_publishing"
        if "os.getenv" in base_chunk and "os.getenv" not in scc_chunk:
            return "wrong_pattern"
        if '"""' in base_chunk and '"""' not in scc_chunk:
            return "missing_docstring"
        if "->" in base_chunk and "->" not in scc_chunk:
            return "missing_type_hints"
        return "style_divergence"

    def score_merit(self, comparison: dict) -> dict:
        """Weighted merit score 0-100 across 4 dimensions.

        Returns:
            {total: int, breakdown: {}, grade: str, gaps: [str]}
        """
        if "error" in comparison:
            return {"total": 0, "breakdown": {}, "grade": "F",
                    "gaps": [comparison.get("error", "File missing")]}

        if comparison.get("is_stub"):
            _scc_stub = Path(comparison.get("scc_path", "unknown")).name
            _reward("scc_produced_stub", -0.5, signal_type="negative",
                    context=f"{_scc_stub} — stub file detected (≤5 lines or <20% of baseline)",
                    needs_review=True)
            _reward("scc_file_merit", 0.05, signal_type="outcome",
                    context=f"{_scc_stub} merit=5/100 grade=F (stub)")
            return {
                "total": 5,
                "breakdown": {"functional_correctness": 0, "code_quality": 5,
                               "epos_compliance": 0, "completeness": 0},
                "grade": "F",
                "gaps": ["STUB — no implementation produced"]
            }

        qc = comparison.get("quality_checks", {})
        divergences = comparison.get("divergences", [])
        missing = comparison.get("missing_features", [])

        # Functional correctness (40%): penalize by divergence weight
        func_penalty = sum(
            DIVERGENCE_TYPES.get(d["type"], {}).get("weight", 0.05)
            for d in divergences
            if DIVERGENCE_TYPES.get(d["type"], {}).get("category") == "functional"
        )
        functional = max(0, 100 - (func_penalty * 100))

        # Code quality (25%): docstrings, types, error handling
        quality_score = sum([
            qc.get("has_docstrings", False) * 35,
            qc.get("has_type_hints", False) * 25,
            qc.get("has_error_handling", False) * 40,
        ])

        # EPOS compliance (20%): governance, events, POSIX
        compliance_score = sum([
            qc.get("has_governance_watermark", False) * 30,
            qc.get("has_posix_paths", False) * 30,
            qc.get("no_windows_paths", True) * 25,
            qc.get("has_event_publishing", False) * 15,
        ])

        # Completeness (15%): matching lines + no missing features
        completeness = comparison.get("matching_lines_pct", 0)
        if missing:
            completeness *= 0.5

        total = round(
            functional * MERIT_WEIGHTS["functional_correctness"] +
            quality_score * MERIT_WEIGHTS["code_quality"] +
            compliance_score * MERIT_WEIGHTS["epos_compliance"] +
            completeness * MERIT_WEIGHTS["completeness"]
        )
        total = min(100, max(0, total))

        # Identify gaps
        gaps = []
        if not qc.get("has_governance_watermark"):
            gaps.append("missing_governance_watermark")
        if not qc.get("has_error_handling"):
            gaps.append("missing_error_handling")
        if not qc.get("has_docstrings"):
            gaps.append("missing_docstrings")
        if not qc.get("has_type_hints"):
            gaps.append("missing_type_hints")
        if not qc.get("has_posix_paths"):
            gaps.append("missing_posix_paths")
        if not qc.get("has_event_publishing"):
            gaps.append("missing_event_publishing")
        for d in divergences:
            if d["type"] not in gaps:
                gaps.append(d["type"])

        grade_map = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]
        grade = next((g for threshold, g in grade_map if total >= threshold), "F")

        # ── Reward signals (Directive 20260414-02) ────────────────────────────
        _scc_name = Path(comparison.get("scc_path", "unknown")).name

        # 5 process signals — one per quality dimension
        _process_map = [
            ("scc_has_watermark",       0.15, qc.get("has_governance_watermark", False)),
            ("scc_has_error_handling",  0.15, qc.get("has_error_handling", False)),
            ("scc_has_docstrings",      0.10, qc.get("has_docstrings", False)),
            ("scc_has_type_hints",      0.05, qc.get("has_type_hints", False)),
            ("scc_has_posix_paths",     0.15, qc.get("has_posix_paths", False)),
        ]
        process_total = 0.0
        for _sig, _val, _check in _process_map:
            _earned = _val if _check else 0.0
            _reward(_sig, _earned, signal_type="process",
                    context=f"{_scc_name} {'PASS' if _check else 'FAIL'}")
            process_total += _earned

        # Outcome: file merit (0.0 – 1.0)
        merit_outcome = round(total / 100, 4)
        _reward("scc_file_merit", merit_outcome, signal_type="outcome",
                context=f"{_scc_name} merit={total}/100 grade={grade}")

        # Compound: process_total × outcome (non-linear quality signal for QLoRA)
        compound_value = round(process_total * merit_outcome, 4)
        _reward("scc_merit_compound", compound_value, signal_type="compound",
                context=f"{_scc_name} process={process_total:.2f} × outcome={merit_outcome:.2f}")

        return {
            "total": total,
            "breakdown": {
                "functional_correctness": round(functional),
                "code_quality": round(quality_score),
                "epos_compliance": round(compliance_score),
                "completeness": round(completeness),
            },
            "grade": grade,
            "gaps": gaps[:10],
        }

    def score_mission(self, directive_id: str, file_scores: dict) -> dict:
        """Aggregate merit across all files. Identify common gap patterns.

        Returns:
            {aggregate, per_file, patterns, qlora_targets}
        """
        scores = list(file_scores.values())
        if not scores:
            return {"aggregate": 0, "per_file": {}, "patterns": [], "qlora_targets": []}

        aggregate = round(sum(s["total"] for s in scores) / len(scores))

        # Count gap patterns across files
        pattern_counts: Dict[str, int] = {}
        for score in scores:
            for gap in score.get("gaps", []):
                pattern_counts[gap] = pattern_counts.get(gap, 0) + 1

        # Sort by frequency, require 2+ files for a pattern
        patterns = sorted(
            [{"pattern": k, "frequency": v, "files_pct": round(v / len(scores) * 100)}
             for k, v in pattern_counts.items() if v >= 2],
            key=lambda x: x["frequency"],
            reverse=True,
        )

        qlora_targets = [p["pattern"] for p in patterns[:3]]

        return {
            "directive_id": directive_id,
            "aggregate": aggregate,
            "file_count": len(scores),
            "per_file": {k: {"total": v["total"], "grade": v["grade"]} for k, v in file_scores.items()},
            "patterns": patterns,
            "qlora_targets": qlora_targets,
        }

    def generate_training_pairs(self, file_scores: dict, patterns: list,
                                 directive_id: str) -> list:
        """Generate ONE training pair per pattern (not per file).

        Pattern-level targeting: if 7/10 files miss error handling,
        generate ONE lesson on the error handling PATTERN.
        """
        PATTERN_LESSONS = {
            "missing_error_handling": {
                "lesson": "All external API calls must be wrapped in try/except with typed exceptions and graceful fallback returning error dict. Article II: No Silent Failures.",
                "bad_example": "response = await client.post(url, headers=headers, ...)\nresult = response.json()",
                "good_example": "try:\n    response = await client.post(url, headers=headers, ...)\n    response.raise_for_status()\n    return response.json()\nexcept httpx.TimeoutException:\n    return {'error': 'API timeout', 'fallback': True}\nexcept httpx.HTTPStatusError as e:\n    return {'error': f'HTTP {e.response.status_code}', 'fallback': True}\nexcept Exception as e:\n    return {'error': str(e), 'fallback': True}",
                "epos_principle": "Article II — No Silent Failures",
            },
            "missing_governance_watermark": {
                "lesson": "Every EPOS Python file must begin with the governance watermark comment block immediately after the shebang. This enables provenance tracking.",
                "bad_example": "#!/usr/bin/env python3\n\nimport os",
                "good_example": '#!/usr/bin/env python3\n# EPOS GOVERNANCE WATERMARK\n"""\nmodule_name.py — Description\n==================\nConstitutional Authority: EPOS Constitution v3.1\nDirective: YYYYMMDD-XX\n"""',
                "epos_principle": "Article XIV — Directive ID in every file header",
            },
            "missing_event_publishing": {
                "lesson": "All significant operations must publish to the Event Bus. Wire EPOSEventBus lazily (try/except import) and call _publish() at start, completion, and failure.",
                "bad_example": "def process():\n    result = do_work()\n    return result",
                "good_example": "_BUS = None\ntry:\n    from epos_event_bus import EPOSEventBus\n    _BUS = EPOSEventBus()\nexcept Exception:\n    pass\n\ndef _publish(event, payload):\n    if _BUS:\n        try: _BUS.publish(event, payload, source_module='module_name')\n        except Exception: pass\n\ndef process():\n    _publish('module.process.start', {})\n    result = do_work()\n    _publish('module.process.complete', {'result': str(result)[:100]})\n    return result",
                "epos_principle": "Event Bus: every operation is observable",
            },
            "missing_posix_paths": {
                "lesson": "Never hardcode absolute paths. Always use Path(os.getenv('EPOS_ROOT', '/app')) as the root. This ensures container portability.",
                "bad_example": "VAULT = Path('/app/context_vault')\nROOT = Path(local_dev_path)  # local dev path hardcoded — breaks in container",
                "good_example": "import os\nfrom pathlib import Path\nEPOS_ROOT = Path(os.getenv('EPOS_ROOT', '/app'))\nVAULT = EPOS_ROOT / 'context_vault'",
                "epos_principle": "AD-009 — POSIX-clean codebase, cloud-ready",
            },
            "missing_docstrings": {
                "lesson": "Every public function and class must have a docstring. Args and returns documented. This is constitutional — AARs and QLoRA training depend on readable code.",
                "bad_example": "def transcribe(audio_bytes, filename):\n    url = '...'\n    response = client.post(url, ...)\n    return response.json()",
                "good_example": 'def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:\n    """Send audio to Groq Whisper API. Returns transcript dict.\n\n    Args:\n        audio_bytes: Raw audio file bytes\n        filename: Original filename for MIME type detection\n\n    Returns:\n        {"text": str, ...} — Groq Whisper response\n    """\n    ...',
                "epos_principle": "Article IV — Institutional legibility",
            },
            "missing_type_hints": {
                "lesson": "All function signatures must include type hints for parameters and return types. This enables static analysis and improves QLoRA training signal quality.",
                "bad_example": "def correct_transcript(raw_transcript):\n    vocab = load_vocabulary()\n    return vocab, []",
                "good_example": "def correct_transcript(raw_transcript: str) -> tuple[str, list]:\n    vocab = load_vocabulary()\n    return vocab, []",
                "epos_principle": "Code quality — type safety improves reasoning",
            },
            "stub_instead_of_implementation": {
                "lesson": "When given a full spec with code examples, SCC must implement the complete function body. A stub (shebang only or pass-only) is a constitutional violation — Article III: Nothing done until it runs.",
                "bad_example": "#!/usr/bin/env python3\n# (empty or shebang only)",
                "good_example": "Implement every function specified in the directive. If a spec provides code, use it. If it describes behavior, write the implementation. Never return an empty file.",
                "epos_principle": "Article III — Nothing done until it runs",
            },
            "wrong_pattern": {
                "lesson": "Use os.getenv() for all configuration values. Never hardcode URLs, ports, or paths as literals. This enables environment-specific deployment without code changes.",
                "bad_example": 'LITELLM_URL = "http://localhost:4000"\nOLLAMA_URL = "http://localhost:11434"',
                "good_example": 'LITELLM_URL = os.getenv("LITELLM_BASE_URL", "http://litellm:4000")\nOLLAMA_URL = os.getenv("OLLAMA_URL", "http://epos-ollama:11434")',
                "epos_principle": "AD-009 — External config, not hardcoded values",
            },
        }

        pairs = []
        files_per_pattern: Dict[str, list] = {}

        # Map files to patterns
        for filename, score_data in file_scores.items():
            for gap in score_data.get("gaps", []):
                files_per_pattern.setdefault(gap, []).append(filename)

        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            lesson_data = PATTERN_LESSONS.get(pattern, {
                "lesson": f"Address {pattern} in all EPOS files",
                "bad_example": f"# Missing: {pattern}",
                "good_example": f"# Implement: {pattern}",
                "epos_principle": "EPOS Constitution v3.1",
            })

            pair = {
                "pattern": pattern,
                "frequency": f"{pattern_info['frequency']}/{len(file_scores)} files ({pattern_info['files_pct']}%)",
                "lesson": lesson_data["lesson"],
                "bad_example": lesson_data["bad_example"],
                "good_example": lesson_data["good_example"],
                "epos_principle": lesson_data["epos_principle"],
                "files_affected": files_per_pattern.get(pattern, []),
                "directive_id": directive_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            pairs.append(pair)

        # Save to vault
        PAIRS_DIR.mkdir(parents=True, exist_ok=True)
        pairs_file = PAIRS_DIR / f"{directive_id}_patterns.jsonl"
        with open(pairs_file, "w") as f:
            for pair in pairs:
                f.write(json.dumps(pair) + "\n")

        return pairs

    def track_merit(self, model_id: str, directive_id: str, score: int,
                    gaps: list) -> dict:
        """Append to merit timeline. Calculate trend and graduation projection.

        Returns:
            {sessions, trend, projected_graduation_date, current_score}
        """
        MERIT_FILE.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "model_id": model_id,
            "directive_id": directive_id,
            "score": score,
            "gaps": gaps,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with open(MERIT_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Load all history for this model
        history = []
        if MERIT_FILE.exists():
            for line in MERIT_FILE.read_text().splitlines():
                try:
                    rec = json.loads(line)
                    if rec.get("model_id") == model_id:
                        history.append(rec)
                except Exception:
                    pass

        # Calculate trend
        if len(history) >= 2:
            delta = history[-1]["score"] - history[-2]["score"]
            trend = "positive" if delta > 2 else ("negative" if delta < -2 else "flat")
        else:
            trend = "baseline — session 1"

        # Project graduation (90% target)
        projected = None
        if len(history) >= 2:
            avg_gain = (history[-1]["score"] - history[0]["score"]) / len(history)
            if avg_gain > 0:
                sessions_needed = max(0, (90 - score) / avg_gain)
                from datetime import timedelta
                proj_date = datetime.now(timezone.utc) + timedelta(days=sessions_needed)
                projected = proj_date.strftime("%Y-%m-%d")

        return {
            "model_id": model_id,
            "sessions": len(history),
            "current_score": score,
            "trend": trend,
            "projected_graduation": projected or "Insufficient data (need 2+ sessions)",
        }
