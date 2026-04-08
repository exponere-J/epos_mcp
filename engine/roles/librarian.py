# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/engine\roles\librarian.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: C:\Users\Jamie\workspace\epos_mcp\engine\roles\librarian.py
"""
Context Librarian (Agent Sigma)
Custodian of Context Vault with symbolic search capabilities.

Authority: Article VII (Context Governance)
Monetization: $497/mo (Enterprise Data Sovereignty Engine)
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

# Path setup
EPOS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(EPOS_ROOT / "engine"))

VAULT_ROOT = EPOS_ROOT / "context_vault" / "mission_data"
VAULT_ROOT.mkdir(parents=True, exist_ok=True)


class ContextLibrarian:
    """
    Agent Sigma: Context Vault manager.
    
    Responsibilities:
    - Ingest large artifacts into vault
    - Maintain symbolic search indices
    - Provide vault references (never raw dumps)
    - Vault hygiene and archival
    """
    
    def __init__(self):
        self.vault_root = VAULT_ROOT
        self.index_path = self.vault_root / "vault_index.json"
        self.logs_dir = EPOS_ROOT / "ops" / "logs" / "librarian"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create index
        if self.index_path.exists():
            self.index = json.loads(self.index_path.read_text())
        else:
            self.index = {"entries": [], "metadata": {"version": "1.0"}}
            self._save_index()
    
    def ingest_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow 1: Large-input triage.
        Chunks and stores content > 8K tokens in vault.
        
        Args:
            content_data: {
                "mission_id": str,
                "raw_content": str,
                "metadata": {
                    "source": str,
                    "entity": str,
                    "timestamp": str
                }
            }
        
        Returns:
            {
                "status": "ingested",
                "vault_id": str,
                "storage_path": str,
                "index_status": "updated",
                "chunk_count": int
            }
        """
        mission_id = content_data.get("mission_id")
        raw_content = content_data.get("raw_content", "")
        metadata = content_data.get("metadata", {})
        
        # Generate vault ID
        vault_id = hashlib.sha256(f"{mission_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # Create mission directory
        mission_dir = self.vault_root / mission_id
        mission_dir.mkdir(exist_ok=True)
        
        # Chunk content (simple chunking by 4K tokens ~ 16K chars)
        chunk_size = 16000
        chunks = [raw_content[i:i+chunk_size] for i in range(0, len(raw_content), chunk_size)]
        
        # Store chunks
        chunk_paths = []
        for idx, chunk in enumerate(chunks):
            chunk_file = mission_dir / f"{vault_id}_chunk_{idx}.txt"
            chunk_file.write_text(chunk, encoding="utf-8")
            chunk_paths.append(str(chunk_file.relative_to(EPOS_ROOT)))
        
        # Update index
        entry = {
            "vault_id": vault_id,
            "mission_id": mission_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "chunks": chunk_paths,
            "total_size": len(raw_content)
        }
        
        self.index["entries"].append(entry)
        self._save_index()
        
        # Log
        log_file = self.logs_dir / f"ingest_{vault_id}.json"
        log_file.write_text(json.dumps(entry, indent=2))
        
        return {
            "status": "ingested",
            "vault_id": vault_id,
            "storage_path": str(mission_dir.relative_to(EPOS_ROOT)),
            "index_status": "updated",
            "chunk_count": len(chunks)
        }
    
    def search_vault(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow 2: Context retrieval via symbolic search.
        
        Args:
            search_data: {
                "query": str,
                "mission_id": str (optional),
                "top_k": int (default 5)
            }
        
        Returns:
            {
                "status": "found" | "not_found",
                "results": [
                    {
                        "vault_id": str,
                        "mission_id": str,
                        "relevance_score": float,
                        "summary": str,
                        "vault_refs": [str]
                    }
                ]
            }
        """
        query = search_data.get("query", "").lower()
        mission_filter = search_data.get("mission_id")
        top_k = search_data.get("top_k", 5)
        
        # Simple keyword matching (replace with vector search in production)
        results = []
        
        for entry in self.index["entries"]:
            if mission_filter and entry["mission_id"] != mission_filter:
                continue
            
            # Score by keyword presence in metadata
            metadata_str = json.dumps(entry["metadata"]).lower()
            score = sum(1 for word in query.split() if word in metadata_str)
            
            if score > 0:
                results.append({
                    "vault_id": entry["vault_id"],
                    "mission_id": entry["mission_id"],
                    "relevance_score": score / len(query.split()),
                    "summary": entry["metadata"].get("source", "Unknown")[:100],
                    "vault_refs": entry["chunks"]
                })
        
        # Sort and limit
        results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
        
        return {
            "status": "found" if len(results) > 0 else "not_found",
            "results": results
        }
    
    def vault_hygiene(self) -> Dict[str, Any]:
        """
        Workflow 3: Nightly vault maintenance.
        
        Returns:
            {
                "status": "complete",
                "vault_size_mb": float,
                "total_entries": int,
                "missions": int,
                "growth_rate": str
            }
        """
        # Calculate vault size
        total_size = sum(f.stat().st_size for f in self.vault_root.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        # Count missions
        missions = set(entry["mission_id"] for entry in self.index["entries"])
        
        # Simple growth rate (entries per day)
        if len(self.index["entries"]) > 0:
            first_entry = self.index["entries"][0]
            days_active = (datetime.now() - datetime.fromisoformat(first_entry["timestamp"])).days or 1
            growth_rate = f"{len(self.index['entries']) / days_active:.1f} entries/day"
        else:
            growth_rate = "N/A"
        
        report = {
            "status": "complete",
            "vault_size_mb": round(size_mb, 2),
            "total_entries": len(self.index["entries"]),
            "missions": len(missions),
            "growth_rate": growth_rate
        }
        
        # Log for Flywheel Analyst
        report_file = EPOS_ROOT / "ops" / "vault_reports" / f"hygiene_{datetime.now():%Y%m%d}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))
        
        return report
    
    def _save_index(self):
        """Persist index to disk"""
        self.index_path.write_text(json.dumps(self.index, indent=2))


if __name__ == "__main__":
    # Test mode
    librarian = ContextLibrarian()
    report = librarian.vault_hygiene()
    print(f"Vault: {report['vault_size_mb']} MB, {report['total_entries']} entries")
