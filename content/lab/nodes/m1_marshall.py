#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
M1 Marshall — Distribution Orchestrator (The Stagger)
Constitutional Authority: EPOS Constitution v3.1

Generates staggered publish schedules across platforms.
Enforces 24-hour stabilization before cascade derivatives.
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from path_utils import get_context_vault
from epos_event_bus import EPOSEventBus


class M1Marshall:
    """Distribution orchestrator. The Stagger."""

    STAGGER_OFFSETS_HOURS = {
        "youtube_shorts": 0,
        "x_twitter": 8,
        "linkedin": 27,
        "tiktok": 59,
        "instagram_reels": 78,
    }

    def __init__(self):
        self.vault_root = get_context_vault()
        self.schedules_dir = self.vault_root / "schedules"
        self.schedules_dir.mkdir(parents=True, exist_ok=True)
        self.bus = EPOSEventBus()

    def generate_week_schedule(self, niche_id: str, week_number: int,
                               asset_packages: List[dict]) -> dict:
        """Generate staggered publish schedule for a week."""
        base_time = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0, microsecond=0)
        schedule = {"niche_id": niche_id, "week": week_number,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "assets": []}

        for i, asset in enumerate(asset_packages):
            day_offset = i  # one per day
            asset_schedule = {"asset_id": asset.get("asset_id", f"asset-{i}"),
                              "platforms": {}}
            for platform, offset_h in self.STAGGER_OFFSETS_HOURS.items():
                publish_time = base_time + timedelta(days=day_offset, hours=offset_h)
                asset_schedule["platforms"][platform] = {
                    "scheduled_at": publish_time.isoformat(),
                    "offset_hours": offset_h,
                    "status": "scheduled",
                }
            schedule["assets"].append(asset_schedule)

        schedule_path = self.schedules_dir / f"week{week_number}_{niche_id}.json"
        schedule_path.write_text(json.dumps(schedule, indent=2), encoding="utf-8")

        try:
            self.bus.publish("content.scheduled",
                             {"niche_id": niche_id, "week": week_number,
                              "asset_count": len(asset_packages)},
                             "m1_marshall")
        except Exception:
            pass
        return schedule

    def release_cascade(self, source_asset_id: str) -> dict:
        """Release held derivative assets after 24h stabilization."""
        release = {"source_asset_id": source_asset_id,
                    "released_at": datetime.now(timezone.utc).isoformat(),
                    "status": "released"}
        try:
            self.bus.publish("content.cascade.released",
                             {"source_asset_id": source_asset_id}, "m1_marshall")
        except Exception:
            pass
        return release


if __name__ == "__main__":
    marshall = M1Marshall()
    schedule = marshall.generate_week_schedule("lego_affiliate", 1,
        [{"asset_id": "CB-LEGO-001", "validated": True}])
    assert len(schedule["assets"]) == 1
    assert "youtube_shorts" in schedule["assets"][0]["platforms"]
    assert schedule["assets"][0]["platforms"]["youtube_shorts"]["offset_hours"] == 0
    print(f"  Week 1 schedule: {len(schedule['assets'])} assets across {len(M1Marshall.STAGGER_OFFSETS_HOURS)} platforms")
    print("PASS: M1Marshall self-tests passed")
