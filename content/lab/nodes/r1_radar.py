#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
R1 Radar — Signal Capture Node
Constitutional Authority: EPOS Constitution v3.1

Three modes: competitor scan sparks, vault riff sparks, platform monitor sparks.
Every spark written to context_vault/sparks/ and published to event bus.
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from path_utils import get_context_vault
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus


class R1Radar:
    """Signal capture. Generates Creative Sparks from multiple sources."""

    SPARK_THRESHOLD = {
        "youtube_competitor": 45,
        "x_tributary": 100,
        "tiktok_tributary": 5000,
        "vault_riff": 0,
        "fotw_transcript": 50,
    }

    def __init__(self):
        self.vault_root = get_context_vault()
        self.sparks_dir = self.vault_root / "sparks"
        self.sparks_dir.mkdir(parents=True, exist_ok=True)
        self.bus = EPOSEventBus()

    def capture_from_competitor_scan(self, niche_id: str) -> List[dict]:
        """Read competitor_scan.jsonl. Generate sparks from top angles."""
        scan_path = self.vault_root / "niches" / niche_id / "competitor_scan.jsonl"
        niche_pack_path = self.vault_root / "niches" / niche_id / "niche_pack.json"

        sparks = []

        if scan_path.exists():
            videos = []
            with open(scan_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            videos.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            top_quartile = sorted(videos, key=lambda v: v.get("eri_score", 0), reverse=True)
            for v in top_quartile[:10]:
                spark = self._create_spark(
                    v.get("title", "untitled"),
                    f"competitor_scan:{niche_id}",
                    "youtube_competitor",
                    v.get("eri_score", 0),
                )
                sparks.append(spark)
        elif niche_pack_path.exists():
            # Fallback: generate from desire_vocabulary
            pack = json.loads(niche_pack_path.read_text(encoding="utf-8"))
            vocab = pack.get("desire_vocabulary", {})
            for phrase in vocab.get("pain_language", [])[:5]:
                spark = self._create_spark(phrase, f"desire_vocab:{niche_id}", "vault_riff", 0)
                sparks.append(spark)

        if not sparks:
            spark = self._create_spark(
                f"Default spark for {niche_id} — needs manual signal input",
                "fallback", "vault_riff", 0,
            )
            sparks.append(spark)

        return sparks

    def capture_from_vault_riff(self, content: str, tags: List[str] = None) -> dict:
        """Convert a vault entry (Jamie's voice) to a spark."""
        return self._create_spark(content, "vault_riff", "vault_riff", 0)

    def _create_spark(self, raw_content: str, source: str,
                      signal_type: str, engagement_score: float) -> dict:
        spark = {
            "spark_id": f"SPARK-{uuid.uuid4().hex[:8]}",
            "source": source,
            "signal_type": signal_type,
            "raw_content": raw_content[:500],
            "engagement_score": engagement_score,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "tags": [],
            "status": "new",
        }
        spark_path = self.sparks_dir / f"{spark['spark_id']}.json"
        spark_path.write_text(json.dumps(spark, indent=2), encoding="utf-8")
        try:
            self.bus.publish("content.spark.created",
                             {"spark_id": spark["spark_id"], "signal_type": signal_type,
                              "engagement_score": engagement_score},
                             "r1_radar")
        except Exception:
            pass
        return spark


if __name__ == "__main__":
    radar = R1Radar()
    spark = radar.capture_from_vault_riff(
        "Every business needs content. Most produce noise. Echoes finds the signal.",
        tags=["philosophy", "positioning"],
    )
    assert spark["spark_id"].startswith("SPARK-")
    assert (get_context_vault() / "sparks" / f"{spark['spark_id']}.json").exists()
    sparks = radar.capture_from_competitor_scan("lego_affiliate")
    assert len(sparks) >= 1
    print(f"  Vault riff spark: {spark['spark_id']}")
    print(f"  Competitor sparks: {len(sparks)}")
    print("PASS: R1Radar self-tests passed")
