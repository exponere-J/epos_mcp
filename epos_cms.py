#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_cms.py — EPOS Content Management System
==============================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/epos_cms.py

Every content asset — scripts, white papers, conversations —
has a lifecycle here. The exhale side of the organism.

Lifecycle: draft -> review -> approved -> scheduled -> published -> archived
Feedback loop: published -> measured -> learned -> next draft improved
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus

LIFECYCLE_STAGES = ["draft", "review", "approved", "scheduled", "published", "archived"]

ASSET_TYPES = [
    "script", "white_paper", "newsletter_item", "social_caption",
    "email_sequence", "mirror_report", "tool_review", "case_study",
    "research_brief", "conversation_transcript", "benchmark_report",
]


@dataclass
class ContentAsset:
    asset_id: str
    asset_type: str
    title: str
    body: str
    status: str
    niche_id: Optional[str] = None
    segment_id: Optional[str] = None
    author_agent: str = ""
    platform_targets: List[str] = None
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    eri_predicted: Optional[float] = None
    eri_actual: Optional[float] = None
    version: int = 1
    tags: List[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.platform_targets is None:
            self.platform_targets = []
        if self.tags is None:
            self.tags = []


class EPOSContentManagement:
    """
    CMS for the EPOS ecosystem. Every content asset has a lifecycle.
    The exhale side — organized, versioned, searchable.
    Feedback hooks baked in: published assets track ERI for learning.
    """

    def __init__(self):
        self.vault = get_context_vault()
        self.cms_root = self.vault / "cms"
        self.bus = EPOSEventBus()
        self._initialize_structure()

    def _initialize_structure(self) -> None:
        dirs = [
            "assets/scripts", "assets/white_papers", "assets/newsletter_items",
            "assets/social_captions", "assets/email_sequences",
            "assets/mirror_reports", "assets/tool_reviews", "assets/case_studies",
            "assets/research_briefs", "assets/conversations",
            "drafts", "review_queue", "approved", "scheduled", "published", "archived",
        ]
        for d in dirs:
            (self.cms_root / d).mkdir(parents=True, exist_ok=True)

        index_path = self.cms_root / "asset_index.json"
        if not index_path.exists():
            index_path.write_text(json.dumps({
                "version": "1.0", "total_assets": 0,
                "by_status": {}, "by_type": {}, "by_niche": {},
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }, indent=2), encoding="utf-8")

    def create_asset(self, asset_type: str, title: str, body: str,
                     author_agent: str, niche_id: str = None,
                     segment_id: str = None, platform_targets: list = None,
                     tags: list = None) -> ContentAsset:
        """Create a new content asset. Starts in 'draft'."""
        asset = ContentAsset(
            asset_id=f"ASSET-{uuid.uuid4().hex[:8]}",
            asset_type=asset_type, title=title, body=body, status="draft",
            niche_id=niche_id, segment_id=segment_id, author_agent=author_agent,
            platform_targets=platform_targets or [], tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save to type folder
        type_name = f"{asset_type}s" if not asset_type.endswith("s") else asset_type
        type_folder = self.cms_root / "assets" / type_name
        type_folder.mkdir(parents=True, exist_ok=True)
        (type_folder / f"{asset.asset_id}.json").write_text(
            json.dumps(asdict(asset), indent=2), encoding="utf-8")

        # Write to drafts
        (self.cms_root / "drafts" / f"{asset.asset_id}.json").write_text(
            json.dumps({"asset_id": asset.asset_id, "type": asset_type, "title": title}, indent=2),
            encoding="utf-8")

        self._update_index(asset)

        record_decision(
            decision_type="cms.asset_created",
            description=f"{asset_type}: {title[:60]}",
            agent_id=author_agent, outcome="draft",
            context={"asset_id": asset.asset_id, "niche": niche_id})

        try:
            self.bus.publish("cms.asset.created",
                             {"asset_id": asset.asset_id, "type": asset_type, "status": "draft"},
                             "epos_cms")
        except Exception:
            pass
        return asset

    def advance_lifecycle(self, asset_id: str, new_status: str,
                          notes: str = None) -> ContentAsset:
        """Move asset through lifecycle. Logs every transition."""
        asset = self.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")

        old_status = asset.status
        asset.status = new_status
        asset.updated_at = datetime.now(timezone.utc).isoformat()
        if new_status == "published":
            asset.published_at = asset.updated_at

        # Update type folder
        type_name = f"{asset.asset_type}s" if not asset.asset_type.endswith("s") else asset.asset_type
        asset_path = self.cms_root / "assets" / type_name / f"{asset_id}.json"
        if asset_path.exists():
            asset_path.write_text(json.dumps(asdict(asset), indent=2), encoding="utf-8")

        # Move stage folder pointer
        for stage in LIFECYCLE_STAGES:
            old = self.cms_root / stage / f"{asset_id}.json"
            if old.exists():
                old.unlink()
        stage_dir = self.cms_root / new_status
        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / f"{asset_id}.json").write_text(
            json.dumps({"asset_id": asset_id, "type": asset.asset_type,
                         "title": asset.title, "moved_at": asset.updated_at}, indent=2),
            encoding="utf-8")

        # Log lifecycle event
        with open(self.cms_root / "lifecycle_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"asset_id": asset_id, "from": old_status,
                                 "to": new_status, "notes": notes,
                                 "timestamp": asset.updated_at}) + "\n")

        try:
            self.bus.publish(f"cms.asset.{new_status}",
                             {"asset_id": asset_id, "from": old_status, "to": new_status},
                             "epos_cms")
        except Exception:
            pass
        return asset

    def search(self, query: str = None, asset_type: str = None,
               status: str = None, niche_id: str = None, limit: int = 20) -> list:
        """Search CMS by any filter combination."""
        results = []
        for type_dir in (self.cms_root / "assets").iterdir():
            if not type_dir.is_dir():
                continue
            if asset_type and not type_dir.name.startswith(asset_type):
                continue
            for f in type_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if status and data.get("status") != status:
                        continue
                    if niche_id and data.get("niche_id") != niche_id:
                        continue
                    if query:
                        searchable = f"{data.get('title','')} {data.get('body','')} {' '.join(data.get('tags',[]))}".lower()
                        if not all(w.lower() in searchable for w in query.split() if len(w) > 3):
                            continue
                    results.append(data)
                except Exception:
                    continue
        return sorted(results, key=lambda x: x.get("updated_at", ""), reverse=True)[:limit]

    def get_asset(self, asset_id: str) -> Optional[ContentAsset]:
        for type_dir in (self.cms_root / "assets").iterdir():
            if not type_dir.is_dir():
                continue
            p = type_dir / f"{asset_id}.json"
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return ContentAsset(**data)
        return None

    def get_dashboard_stats(self) -> dict:
        stats = {"by_status": {}, "by_type": {}, "total": 0}
        for stage in LIFECYCLE_STAGES:
            d = self.cms_root / stage
            count = len(list(d.glob("*.json"))) if d.exists() else 0
            stats["by_status"][stage] = count
            stats["total"] += count
        return stats

    def _update_index(self, asset: ContentAsset) -> None:
        index_path = self.cms_root / "asset_index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["total_assets"] += 1
        index["by_type"][asset.asset_type] = index["by_type"].get(asset.asset_type, 0) + 1
        if asset.niche_id:
            index["by_niche"][asset.niche_id] = index["by_niche"].get(asset.niche_id, 0) + 1
        index["last_updated"] = datetime.now(timezone.utc).isoformat()
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    cms = EPOSContentManagement()

    assert (cms.cms_root / "assets" / "scripts").exists()
    assert (cms.cms_root / "asset_index.json").exists()
    print("  CMS structure: initialized")

    asset = cms.create_asset(
        asset_type="script",
        title="Top 5 LEGO sets under $50 — Architect angle",
        body="[HOOK] You've been buying LEGO sets wrong. [BODY] Here are the 5 sets...",
        author_agent="a1_architect",
        niche_id="lego_affiliate",
        tags=["lego", "list", "architect"])
    assert asset.status == "draft"
    print(f"  Asset created: {asset.asset_id} ({asset.status})")

    cms.advance_lifecycle(asset.asset_id, "review")
    cms.advance_lifecycle(asset.asset_id, "approved")
    updated = cms.get_asset(asset.asset_id)
    assert updated.status == "approved"
    print(f"  Lifecycle: draft -> review -> approved")

    results = cms.search(query="LEGO", asset_type="script")
    assert len(results) >= 1
    print(f"  Search 'LEGO scripts': {len(results)} found")

    stats = cms.get_dashboard_stats()
    print(f"  CMS stats: {stats['total']} total, by_status: {stats['by_status']}")

    print("\nPASS: EPOSContentManagement — CMS operational")
