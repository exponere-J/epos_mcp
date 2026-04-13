#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/voice/vault_search.py — Vault Semantic Search
====================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Indexes vault documents via nomic-embed-text (Ollama local).
Returns top-k semantically relevant documents for any query.
"""

import json
import os
import numpy as np
from pathlib import Path
from datetime import datetime
import requests

EPOS_ROOT = Path("/app")
VAULT_DIR = EPOS_ROOT / "context_vault"
INDEX_DIR = VAULT_DIR / "voice" / "embeddings"
INDEX_FILE = INDEX_DIR / "vault_index.json"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://epos-ollama:11434")


def embed_text(text: str) -> list:
    """Get embedding vector from nomic-embed-text via Ollama."""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text[:2000]},
        timeout=30
    )
    response.raise_for_status()
    return response.json()["embedding"]


def build_index(force_rebuild: bool = False) -> dict:
    """Index all vault documents. Incremental by default.

    Returns:
        {"total": int, "new": int}
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    existing = {}
    if INDEX_FILE.exists() and not force_rebuild:
        existing = json.loads(INDEX_FILE.read_text())

    indexed_paths = set(existing.get("documents", {}).keys())

    extensions = {".md", ".json", ".txt", ".py"}
    exclude_dirs = {"__pycache__", ".git", "node_modules", "raw_captures", "audio", "embeddings"}

    documents = {}
    new_count = 0

    for ext in extensions:
        for file_path in VAULT_DIR.rglob(f"*{ext}"):
            if any(ex in file_path.parts for ex in exclude_dirs):
                continue

            rel_path = str(file_path.relative_to(VAULT_DIR))

            if rel_path in indexed_paths:
                documents[rel_path] = existing["documents"][rel_path]
                continue

            try:
                content = file_path.read_text(errors="ignore")[:2000]
                if len(content.strip()) < 50:
                    continue

                embedding = embed_text(content)
                documents[rel_path] = {
                    "path": str(file_path),
                    "content_preview": content[:500],
                    "embedding": embedding,
                    "indexed_at": datetime.utcnow().isoformat() + "Z"
                }
                new_count += 1
            except Exception:
                continue

    index = {
        "total_documents": len(documents),
        "new_indexed": new_count,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "documents": documents
    }

    INDEX_FILE.write_text(json.dumps(index, default=str))
    return {"total": len(documents), "new": new_count}


def search_vault(query: str, top_k: int = 5) -> list:
    """Semantic search across vault. Returns top_k most relevant docs.

    Returns:
        [{"path": str, "content_preview": str, "relevance": float}, ...]
    """
    if not INDEX_FILE.exists():
        build_index()

    index = json.loads(INDEX_FILE.read_text())
    query_embedding = np.array(embed_text(query))

    results = []
    for rel_path, doc in index.get("documents", {}).items():
        doc_embedding = np.array(doc["embedding"])
        similarity = float(np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-10
        ))
        results.append({
            "path": rel_path,
            "content_preview": doc["content_preview"],
            "relevance": similarity
        })

    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:top_k]
