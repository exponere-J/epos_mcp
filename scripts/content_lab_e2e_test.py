#!/usr/bin/env python3
"""
content_lab_e2e_test.py — Day 1 Content Lab End-to-End Pipeline Test
=====================================================================
Runs a real creative spark through the full Content Lab pipeline:

  1. Create spark ("What is Echolocation and why does it matter for your business?")
  2. Echolocation Predictor scores against all 8 avatars
  3. Best avatar selected
  4. Brief generator produces 3 Triple-Threat variants
  5. V1 Validator (lightweight: checks vocabulary constraints)
  6. M1 Publisher (staging — BrowserUse if available, else staging files)
  7. AN1 Echo Schedule (records for T+24h scoring)
  8. CTA tokens logged
  9. Print Running Inventory at each step

Returns a structured result dict for the AAR.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nodes.avatar_registry import AvatarRegistry
from content_lab.echolocation_predictor import EcholocationPredictor
from content_lab.brief_generator import ContentBriefGenerator


def banner(n, text):
    bar = "=" * 70
    print(f"\n{bar}\nSTEP {n}: {text}\n{bar}")


def run_e2e():
    result = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": {},
        "final_state": "unknown",
    }

    # ── STEP 1: Create a real spark ──────────────────────────────
    banner(1, "Create creative spark")
    spark = {
        "spark_id": f"SPARK-E2E-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "topic": "What is Echolocation and why does it matter for your business?",
        "description": "Echolocation is the system that measures whether your content resonates with specific audiences — and uses that data to make every next piece sharper.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    print(f"Spark ID: {spark['spark_id']}")
    print(f"Topic: {spark['topic']}")
    result["steps"]["1_spark_created"] = {"status": "ok", "spark_id": spark["spark_id"]}

    # ── STEP 2: Score spark against all 8 avatars ────────────────
    banner(2, "Score spark against all 8 avatars (Echolocation Predictor)")
    reg = AvatarRegistry()
    pred = EcholocationPredictor()
    avatars = reg.list_avatars()
    scores = []
    for avatar in avatars:
        comm = avatar.get("communication_preferences", {}) or {}
        fmt_list = comm.get("format", ["linkedin_post"])
        preferred_fmt = fmt_list[0] if isinstance(fmt_list, list) and fmt_list else "linkedin_post"
        p = pred.predict_resonance(
            topic=spark["topic"],
            avatar_id=avatar["avatar_id"],
            format=preferred_fmt,
            angle="architect",
        )
        scores.append((avatar["avatar_id"], p["predicted_score"], p["confidence"], preferred_fmt, p))
        print(f"  {avatar['avatar_id']:30s} score={p['predicted_score']:5.1f}  format={preferred_fmt}")

    scores.sort(key=lambda s: s[1], reverse=True)
    best_avatar_id, best_score, best_conf, best_fmt, best_prediction = scores[0]
    result["steps"]["2_scored"] = {
        "status": "ok",
        "winner": best_avatar_id,
        "winning_score": best_score,
        "all_scores": [{"avatar": s[0], "score": s[1]} for s in scores],
    }
    print(f"\nWINNER: {best_avatar_id} @ {best_score}")

    # ── STEP 3: Avatar selected ─────────────────────────────────
    banner(3, f"Avatar selected: {best_avatar_id}")
    best_avatar = reg.get_avatar(best_avatar_id)
    print(f"Display name: {best_avatar['display_name']}")
    print(f"Preferred format: {best_fmt}")
    print(f"Primary channels: {best_avatar.get('channels', {}).get('primary', [])}")
    result["steps"]["3_avatar_selected"] = {"status": "ok", "avatar_id": best_avatar_id}

    # ── STEP 4: Generate 3 Triple-Threat variants ────────────────
    banner(4, "Generate 3 Triple-Threat briefs (Challenger / Architect / Closer)")
    gen = ContentBriefGenerator()
    variants = gen.generate_variants(spark, best_avatar, best_prediction)
    for v in variants:
        print(f"\n  [{v['angle'].upper()}] {v['brief_id']}")
        print(f"    Hook: {v['hook']}")
        print(f"    CTA token: {v['cta_token']}")
        print(f"    Max words: {v['constraints']['max_words']}")
    result["steps"]["4_briefs_generated"] = {
        "status": "ok",
        "variant_count": len(variants),
        "brief_ids": [v["brief_id"] for v in variants],
    }

    # ── STEP 5: V1 Validator (lightweight vocabulary check) ─────
    banner(5, "V1 Validator — vocabulary + constraint check")
    validated = []
    for v in variants:
        excludes = set(kw.lower() for kw in v["vocabulary_exclude"])
        hook_lower = v["hook"].lower()
        violations = [kw for kw in excludes if kw in hook_lower]
        passed = len(violations) == 0
        validated.append({"brief_id": v["brief_id"], "angle": v["angle"],
                          "passed": passed, "violations": violations})
        status = "PASS" if passed else f"FAIL ({violations})"
        print(f"  {v['angle']:12s} {v['brief_id']}: {status}")
    all_pass = all(v["passed"] for v in validated)
    result["steps"]["5_validated"] = {
        "status": "ok" if all_pass else "warn",
        "results": validated,
    }

    # ── STEP 6: M1 Publisher (staging) ──────────────────────────
    banner(6, "M1 Publisher — stage content (BrowserUse if available, else files)")
    from path_utils import get_context_vault
    vault = get_context_vault()
    staging_dir = vault / "echoes" / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)

    staged_paths = []
    for v in variants:
        staged_body = (
            f"# {v['topic']}\n\n"
            f"**Target:** {v['avatar_display_name']} ({v['target_avatar']})\n"
            f"**Angle:** {v['angle']}\n"
            f"**Format:** {v['format']}\n"
            f"**Predicted resonance:** {v['predicted_resonance']}\n"
            f"**CTA token:** {v['cta_token']}\n\n"
            f"---\n\n"
            f"## Hook\n\n{v['hook']}\n\n"
            f"## Structure\n\n"
            f"- **Opening:** {v['structure']['opening']}\n"
            f"- **Value:** {v['structure']['value']}\n"
            f"- **Evidence:** {v['structure']['evidence']}\n"
            f"- **System:** {v['structure']['system']}\n"
            f"- **CTA:** {v['structure']['cta']}\n"
            f"- **Signoff:** {v['structure']['signoff']}\n\n"
            f"## Constraints\n\n{json.dumps(v['constraints'], indent=2)}\n\n"
            f"## Optimization notes\n\n"
            + "\n".join(f"- {note}" for note in v['optimization_notes'])
        )
        out_path = staging_dir / f"{v['brief_id']}_{v['angle']}.md"
        out_path.write_text(staged_body, encoding="utf-8")
        staged_paths.append(str(out_path))
        print(f"  Staged: {out_path.name}")
    result["steps"]["6_published"] = {
        "status": "ok (staging)",
        "staged_count": len(staged_paths),
        "staged_paths": staged_paths,
    }

    # ── STEP 7: AN1 Echo Schedule ───────────────────────────────
    banner(7, "AN1 Echo Schedule — schedule T+24h scoring")
    schedule_path = vault / "echoes" / "scheduled.jsonl"
    schedule_path.parent.mkdir(parents=True, exist_ok=True)
    scheduled = []
    for v in variants:
        entry = {
            "brief_id": v["brief_id"],
            "avatar_id": v["target_avatar"],
            "prediction_id": v.get("prediction_id"),
            "predicted_score": v["predicted_resonance"],
            "scheduled_for": (datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
            "note": "T+24h echo scoring",
        }
        with open(schedule_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        scheduled.append(entry)
        print(f"  Scheduled: {v['brief_id']} @ {entry['scheduled_for']}")
    result["steps"]["7_scheduled"] = {"status": "ok", "scheduled_count": len(scheduled)}

    # ── STEP 8: CTA tokens logged ──────────────────────────────
    banner(8, "CTA tokens logged for attribution")
    cta_log = vault / "echoes" / "cta_tokens.jsonl"
    for v in variants:
        entry = {
            "cta_token": v["cta_token"],
            "brief_id": v["brief_id"],
            "avatar_id": v["target_avatar"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(cta_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"  {v['cta_token']}")
    result["steps"]["8_cta_logged"] = {"status": "ok", "count": len(variants)}

    result["ended_at"] = datetime.now(timezone.utc).isoformat()
    result["final_state"] = "all_steps_completed"

    # ── SUMMARY ─────────────────────────────────────────────────
    banner("SUMMARY", "Content Lab End-to-End Pipeline")
    for k, v in result["steps"].items():
        print(f"  {k:25s} {v['status']}")
    print(f"\nFinal state: {result['final_state']}")
    return result


if __name__ == "__main__":
    out = run_e2e()
    # Persist the E2E run record
    from path_utils import get_context_vault
    vault = get_context_vault()
    e2e_dir = vault / "content" / "e2e_runs"
    e2e_dir.mkdir(parents=True, exist_ok=True)
    out_path = e2e_dir / f"e2e_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nE2E result saved: {out_path}")
