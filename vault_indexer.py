#!/usr/bin/env python3
"""
vault_indexer.py — EPOS Context Vault Global Index Builder
===========================================================
Constitutional Authority: EPOS Constitution v3.1
File: C:/Users/Jamie/workspace/epos_mcp/vault_indexer.py
# EPOS GOVERNANCE WATERMARK

Scans all context_vault/ namespaces and rebuilds global_index.json.
Enables cross-agent search across the entire vault.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_intelligence import record_decision


class VaultIndexer:
    """Rebuilds the global vault index for cross-agent search."""

    NAMESPACES = [
        "missions", "bi_history", "agent_comms", "niches",
        "governance", "checkpoints", "index", "learning",
        "market_sentiment", "agent_logs", "mission_data",
        "events", "scans", "validation",
    ]

    def rebuild_index(self) -> dict:
        """
        Walk all vault namespaces. Build index entry per file.
        Write to context_vault/index/global_index.json.
        Log to epos_intelligence. Returns the index dict.
        """
        vault_root = get_context_vault()
        index = {
            "version": "1.0",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": 0,
            "entries": [],
        }

        for ns in self.NAMESPACES:
            ns_dir = vault_root / ns
            if not ns_dir.exists():
                continue
            for f in ns_dir.rglob("*"):
                if f.is_file() and f.name != "global_index.json":
                    try:
                        entry = {
                            "vault_id": str(f.relative_to(vault_root)),
                            "namespace": ns,
                            "filename": f.name,
                            "size_bytes": f.stat().st_size,
                            "modified_at": datetime.fromtimestamp(
                                f.stat().st_mtime, tz=timezone.utc
                            ).isoformat(),
                            "extension": f.suffix,
                        }
                        index["entries"].append(entry)
                    except Exception:
                        pass

        index["total_entries"] = len(index["entries"])

        index_path = vault_root / "index" / "global_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

        record_decision(
            decision_type="vault.index_rebuilt",
            description=f"Global index rebuilt: {index['total_entries']} entries",
            agent_id="vault_indexer",
            outcome="success",
        )
        return index


if __name__ == "__main__":
    indexer = VaultIndexer()
    index = indexer.rebuild_index()
    assert index["total_entries"] > 0, "Index is empty"
    vault_root = get_context_vault()
    index_path = vault_root / "index" / "global_index.json"
    assert index_path.exists(), "global_index.json not written"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert data["total_entries"] == index["total_entries"]

    # Show namespace breakdown
    by_ns = {}
    for e in index["entries"]:
        ns = e["namespace"]
        by_ns[ns] = by_ns.get(ns, 0) + 1

    print(f"  Total entries: {index['total_entries']}")
    for ns, count in sorted(by_ns.items()):
        print(f"    {ns}: {count}")
    print(f"  Index path: {index_path}")
    print("PASS: vault_indexer self-test passed")
