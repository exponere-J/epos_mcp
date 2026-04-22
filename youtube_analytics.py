#!/usr/bin/env python3
"""
youtube_analytics.py — EPOS YouTube Analytics & ERI Feedback Loop
==================================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/youtube_analytics.py
# EPOS GOVERNANCE WATERMARK

After videos publish, pulls real engagement data from YouTube Data API
and computes actual ERI scores for comparison against predictions.
Core feedback loop of the Binding pilot.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_intelligence import record_decision


class YouTubeAnalytics:
    """Pulls real engagement data and computes actual ERI scores."""

    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "YOUTUBE_API_KEY not found in .env. "
                "Add it to run analytics."
            )

    def get_video_stats(self, video_id: str) -> Dict:
        """Fetch current stats for a published video."""
        url = f"{self.YOUTUBE_API_BASE}/videos"
        params = {
            "id": video_id,
            "part": "statistics,contentDetails,snippet",
            "key": self.api_key,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("items"):
            return {}
        return data["items"][0]

    def compute_actual_eri(
        self, video_id: str, days_since_publish: int = 7
    ) -> Dict:
        """
        Compute actual ERI from real engagement data.
        Compare to predicted_eri_score from the brief.
        """
        video = self.get_video_stats(video_id)
        if not video:
            return {"error": f"Video {video_id} not found"}

        stats = video.get("statistics", {})
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        estimated_saves = int(likes * 0.15)

        engagement_rate = (likes + comments) / max(views, 1)
        velocity = views / max(days_since_publish, 1)

        # ERI formula (same as ma1_niche_scanner)
        raw_eri = (
            (likes * 1.0 + estimated_saves * 4.0 +
             comments * 2.0 + views * 0.01) *
            (min(velocity / 1000, 5.0) * 0.4 +
             engagement_rate * 100 * 0.3 +
             1.0 * 0.3)
        )
        eri_score = min(raw_eri / 100, 100.0)

        result = {
            "video_id": video_id,
            "views": views,
            "likes": likes,
            "comments": comments,
            "estimated_saves": estimated_saves,
            "engagement_rate": round(engagement_rate, 4),
            "velocity_score": round(velocity, 1),
            "actual_eri": round(eri_score, 1),
            "days_since_publish": days_since_publish,
            "pulled_at": datetime.now(timezone.utc).isoformat(),
        }

        record_decision(
            decision_type="content.eri_actual",
            description=f"Actual ERI for {video_id}: {eri_score:.1f}",
            agent_id="youtube_analytics",
            outcome="success",
            context=result,
        )
        return result

    def compare_prediction(
        self, video_id: str, predicted_eri: float, days: int = 7
    ) -> Dict:
        """Compare actual vs predicted ERI."""
        actual = self.compute_actual_eri(video_id, days)
        if "error" in actual:
            return actual

        delta = actual["actual_eri"] - predicted_eri
        accuracy = max(0, 100 - abs(delta / max(predicted_eri, 1) * 100))

        return {
            **actual,
            "predicted_eri": predicted_eri,
            "delta": round(delta, 1),
            "accuracy_pct": round(accuracy, 1),
        }

    def week1_report(self, video_data: List[Dict]) -> Dict:
        """
        Run ERI actual vs predicted for Week 1 videos.
        video_data: list of {"video_id": str, "predicted_eri": float}
        """
        results = []
        for vd in video_data:
            comparison = self.compare_prediction(
                vd["video_id"], vd["predicted_eri"], days=7
            )
            results.append(comparison)

        valid = [r for r in results if "error" not in r]
        avg_accuracy = (
            sum(r["accuracy_pct"] for r in valid) / len(valid)
            if valid else 0
        )

        report = {
            "week": 1,
            "videos_analyzed": len(results),
            "valid_comparisons": len(valid),
            "average_accuracy_pct": round(avg_accuracy, 1),
            "target_accuracy": 50.0,
            "target_met": avg_accuracy >= 50.0,
            "results": results,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save report
        report_path = (get_context_vault() / "niches" / "lego_affiliate"
                       / "week1_eri_report.json")
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)

        record_decision(
            decision_type="content.week1_eri_report",
            description=f"Week 1 ERI report: {avg_accuracy:.1f}% avg accuracy",
            agent_id="youtube_analytics",
            outcome="success" if report["target_met"] else "below_target",
            context={"average_accuracy": avg_accuracy, "videos": len(valid)},
        )
        return report


if __name__ == "__main__":
    try:
        analytics = YouTubeAnalytics()
        print("  YouTubeAnalytics initialized — API key present")
        print("  (No published videos to analyze yet — SKIP live test)")
        print("PASS: youtube_analytics init test passed")
    except EnvironmentError as e:
        print(f"  SKIP: {e}")
        print("  Add YOUTUBE_API_KEY to .env to enable analytics")
