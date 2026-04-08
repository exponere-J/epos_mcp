#!/usr/bin/env python3
"""
context_librarian.py — EPOS Context Vault Interface
=====================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Article VII (Context Governance)
Mission ID: EPOS Core Heal — Module 5 of 9
File Location: C:/Users/Jamie/workspace/epos_mcp/context_librarian.py

Single responsibility: Ingest, index, search, and manage the Context Vault.
All large data (>8K tokens) goes through this module — never inline.

Dependencies: path_utils (Module 1), epos_intelligence (Module 4)
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from path_utils import get_epos_root
from epos_intelligence import record_event


# ── Vault Paths ──────────────────────────────────────────────────

def _vault_root() -> Path:
    d = get_epos_root() / "context_vault"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _index_path() -> Path:
    return _vault_root() / "global_index.json"


def _domain_path(domain: str) -> Path:
    d = _vault_root() / domain
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Domains ──────────────────────────────────────────────────────

VALID_DOMAINS = {
    "mission_data",
    "bi_history",
    "market_sentiment",
    "agent_logs",
    "learning",
    "events",
    "governance",
    "large_datasets",
}


# ── Index Management ─────────────────────────────────────────────

def _load_index() -> Dict[str, Any]:
    """Load or create the global vault index."""
    path = _index_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "version": "2.0",
        "entries": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "constitutional_authority": "Article VII",
        },
    }


def _save_index(index: Dict[str, Any]) -> None:
    """Persist the global vault index."""
    index["metadata"]["last_updated"] = datetime.now().isoformat()
    index["metadata"]["entry_count"] = len(index["entries"])
    _index_path().write_text(json.dumps(index, indent=2), encoding="utf-8")


# ── Core API ─────────────────────────────────────────────────────

def ingest(
    content: str,
    domain: str,
    filename: str,
    mission_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 16000,
) -> Dict[str, Any]:
    """
    Ingest content into the Context Vault.

    For content exceeding chunk_size characters, it is split into numbered
    chunks. All content is indexed for symbolic search.

    Args:
        content: The text content to store
        domain: Vault domain (must be in VALID_DOMAINS)
        filename: Name for the stored file(s)
        mission_id: Optional mission this content belongs to
        metadata: Optional structured metadata
        chunk_size: Max chars per chunk (default 16000 ~ 4K tokens)

    Returns:
        {"status": "ingested", "vault_id": ..., "chunk_count": ..., ...}
    """
    if domain not in VALID_DOMAINS:
        return {"status": "error", "error": f"Invalid domain '{domain}'. Valid: {sorted(VALID_DOMAINS)}"}

    vault_id = hashlib.sha256(
        f"{domain}:{filename}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]

    target_dir = _domain_path(domain)
    if mission_id:
        target_dir = target_dir / mission_id
        target_dir.mkdir(parents=True, exist_ok=True)

    # Chunk if needed
    if len(content) <= chunk_size:
        file_path = target_dir / filename
        file_path.write_text(content, encoding="utf-8")
        stored_paths = [str(file_path.relative_to(get_epos_root()))]
    else:
        chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
        stored_paths = []
        stem = Path(filename).stem
        suffix = Path(filename).suffix or ".txt"
        for idx, chunk in enumerate(chunks):
            chunk_file = target_dir / f"{stem}_chunk{idx:03d}{suffix}"
            chunk_file.write_text(chunk, encoding="utf-8")
            stored_paths.append(str(chunk_file.relative_to(get_epos_root())))

    # Update index
    index = _load_index()
    entry = {
        "vault_id": vault_id,
        "domain": domain,
        "filename": filename,
        "mission_id": mission_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
        "paths": stored_paths,
        "size_bytes": len(content.encode("utf-8")),
        "chunk_count": len(stored_paths),
    }
    index["entries"].append(entry)
    _save_index(index)

    # BI event
    record_event({
        "event_type": "vault.ingest",
        "vault_id": vault_id,
        "domain": domain,
        "size_bytes": entry["size_bytes"],
        "chunk_count": entry["chunk_count"],
    })

    return {
        "status": "ingested",
        "vault_id": vault_id,
        "domain": domain,
        "paths": stored_paths,
        "chunk_count": len(stored_paths),
        "size_bytes": entry["size_bytes"],
    }


def retrieve(vault_id: str) -> Optional[str]:
    """
    Retrieve content by vault ID. Reassembles chunks if needed.

    Returns the full content string or None if not found.
    """
    index = _load_index()
    for entry in index["entries"]:
        if entry["vault_id"] == vault_id:
            root = get_epos_root()
            parts = []
            for rel_path in entry["paths"]:
                full = root / rel_path
                if full.exists():
                    parts.append(full.read_text(encoding="utf-8"))
            return "".join(parts) if parts else None
    return None


def search(
    query: str,
    domain: Optional[str] = None,
    mission_id: Optional[str] = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Keyword search across vault index and file contents.

    Args:
        query: Search terms (space-separated keywords)
        domain: Optional domain filter
        mission_id: Optional mission filter
        top_k: Max results to return

    Returns:
        List of matches with vault_id, relevance_score, snippet, metadata
    """
    keywords = query.lower().split()
    if not keywords:
        return []

    index = _load_index()
    results = []

    for entry in index["entries"]:
        # Apply filters
        if domain and entry["domain"] != domain:
            continue
        if mission_id and entry.get("mission_id") != mission_id:
            continue

        # Score by keyword presence in metadata + filename
        searchable = json.dumps(entry["metadata"]).lower() + " " + entry["filename"].lower()
        score = sum(1 for kw in keywords if kw in searchable) / len(keywords)

        # If metadata match, also check file content for snippet
        snippet = ""
        if score > 0:
            root = get_epos_root()
            for rel_path in entry["paths"][:1]:  # Only check first chunk for speed
                full = root / rel_path
                if full.exists():
                    try:
                        text = full.read_text(encoding="utf-8")
                        text_lower = text.lower()
                        # Find first keyword occurrence for snippet
                        for kw in keywords:
                            pos = text_lower.find(kw)
                            if pos >= 0:
                                start = max(0, pos - 100)
                                end = min(len(text), pos + len(kw) + 100)
                                snippet = text[start:end]
                                if start > 0:
                                    snippet = "..." + snippet
                                if end < len(text):
                                    snippet = snippet + "..."
                                break
                        # Boost score with content matches
                        content_hits = sum(text_lower.count(kw) for kw in keywords)
                        score += min(content_hits / 10, 1.0)
                    except OSError:
                        pass

            results.append({
                "vault_id": entry["vault_id"],
                "domain": entry["domain"],
                "filename": entry["filename"],
                "mission_id": entry.get("mission_id"),
                "relevance_score": round(score, 3),
                "snippet": snippet[:300],
                "metadata": entry["metadata"],
                "size_bytes": entry["size_bytes"],
            })

    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    return results[:top_k]


def list_domain(domain: str) -> List[Dict[str, Any]]:
    """List all entries in a specific domain."""
    if domain not in VALID_DOMAINS:
        return []
    index = _load_index()
    return [
        {
            "vault_id": e["vault_id"],
            "filename": e["filename"],
            "mission_id": e.get("mission_id"),
            "timestamp": e["timestamp"],
            "size_bytes": e["size_bytes"],
        }
        for e in index["entries"]
        if e["domain"] == domain
    ]


def vault_stats() -> Dict[str, Any]:
    """Get vault statistics."""
    index = _load_index()
    entries = index["entries"]

    if not entries:
        return {"total_entries": 0, "total_bytes": 0, "domains": {}}

    by_domain: Dict[str, Dict[str, int]] = {}
    total_bytes = 0

    for e in entries:
        d = e["domain"]
        if d not in by_domain:
            by_domain[d] = {"count": 0, "bytes": 0}
        by_domain[d]["count"] += 1
        by_domain[d]["bytes"] += e.get("size_bytes", 0)
        total_bytes += e.get("size_bytes", 0)

    return {
        "total_entries": len(entries),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "domains": by_domain,
        "index_path": str(_index_path()),
    }


def delete_entry(vault_id: str) -> Dict[str, Any]:
    """Remove an entry from the vault (index and files)."""
    index = _load_index()
    root = get_epos_root()
    found = None

    for i, entry in enumerate(index["entries"]):
        if entry["vault_id"] == vault_id:
            found = index["entries"].pop(i)
            break

    if not found:
        return {"status": "not_found", "vault_id": vault_id}

    # Delete files
    deleted_files = []
    for rel_path in found["paths"]:
        full = root / rel_path
        if full.exists():
            full.unlink()
            deleted_files.append(rel_path)

    _save_index(index)

    record_event({
        "event_type": "vault.delete",
        "vault_id": vault_id,
        "deleted_files": deleted_files,
    })

    return {"status": "deleted", "vault_id": vault_id, "files_removed": len(deleted_files)}


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EPOS Context Librarian v2.0")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("stats", help="Vault statistics")

    p_search = sub.add_parser("search", help="Search vault")
    p_search.add_argument("query", help="Search terms")
    p_search.add_argument("--domain", help="Filter by domain")

    p_list = sub.add_parser("list", help="List domain entries")
    p_list.add_argument("domain", help="Domain name")

    args = parser.parse_args()

    if args.command == "stats":
        stats = vault_stats()
        print("Context Vault Statistics")
        print("=" * 40)
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Total size: {stats['total_mb']} MB")
        for d, s in stats.get("domains", {}).items():
            print(f"    {d}: {s['count']} entries, {s['bytes']:,} bytes")
    elif args.command == "search":
        results = search(args.query, domain=args.domain)
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  [{r['relevance_score']}] {r['filename']} ({r['domain']})")
            if r["snippet"]:
                print(f"    {r['snippet'][:120]}")
    elif args.command == "list":
        entries = list_domain(args.domain)
        print(f"{args.domain}: {len(entries)} entries")
        for e in entries:
            print(f"  {e['vault_id'][:8]}  {e['filename']}  {e['size_bytes']:,}b")
    else:
        # Self-test
        print("Context Librarian v2.0 — Self-test")
        print("=" * 40)

        r = ingest("Test content for self-test validation", "learning", "selftest.txt", metadata={"purpose": "selftest validation"})
        assert r["status"] == "ingested", f"Ingest failed: {r}"
        vid = r["vault_id"]
        print(f"  Ingest: OK (vault_id={vid})")

        content = retrieve(vid)
        assert content == "Test content for self-test validation"
        print(f"  Retrieve: OK")

        results = search("selftest validation", domain="learning")
        assert len(results) >= 1
        print(f"  Search: OK ({len(results)} results)")

        stats = vault_stats()
        assert stats["total_entries"] >= 1
        print(f"  Stats: OK ({stats['total_entries']} entries)")

        d = delete_entry(vid)
        assert d["status"] == "deleted"
        print(f"  Delete: OK")

        print("\n  All assertions passed.")
