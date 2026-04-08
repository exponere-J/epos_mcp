# File: C:\Users\Jamie\workspace\epos_mcp\agents\context_librarian.py

"""
Context Librarian (Agent Sigma) v1.0.0
======================================

Constitutional Authority: EPOS_CONSTITUTION_v3.1.md Article VII
Purpose: Custodian of Context Vault; enable unlimited context through symbolic search

This agent implements RLM (Recursive Language Model) techniques to bypass context
window limits by treating large data as an external environment that can be
queried symbolically rather than loaded entirely into prompts.

Key Principle: "Prompt as External Variable" - Agent Zero receives search tools,
not the full context. This enables million+ token working context while staying
within 8K token API windows.

Exit Codes:
    0 = Operation successful
    1 = Operation failed with recoverable error
    2 = Critical vault corruption detected
"""

import sys
import os
import json
import re
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from hashlib import sha256

# Ensure Python 3.11+
if sys.version_info[:2] < (3, 11):
    print("❌ CRITICAL: Python 3.11+ required (Article II Rule 3)")
    sys.exit(2)


@dataclass
class VaultFile:
    """Metadata for a vault file."""
    vault_id: str
    file_path: str
    original_name: str
    size_bytes: int
    estimated_tokens: int
    created: str
    last_accessed: str
    access_count: int
    checksum: str
    category: str
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SearchResult:
    """Result from a symbolic search."""
    vault_id: str
    matches: List[str]
    positions: List[int]
    context_windows: List[str]
    total_matches: int
    search_time_ms: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class VaultManifest:
    """Manifest for a chunked mission vault."""
    mission_id: str
    created: str
    total_chunks: int
    total_tokens: int
    chunk_files: List[str]
    summary: str
    search_hints: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ContextVault:
    """
    Context Vault - Symbolic search interface for large files.
    
    Implements RLM techniques for unlimited effective context.
    """
    
    def __init__(self, file_path: Path):
        """Initialize vault for a specific file."""
        self.file_path = Path(file_path)
        self._content: Optional[str] = None
        self._metadata: Optional[Dict] = None
    
    def _load_content(self) -> str:
        """Lazy load file content."""
        if self._content is None:
            self._content = self.file_path.read_text(encoding='utf-8', errors='ignore')
        return self._content
    
    def get_metadata(self) -> Dict:
        """Get vault file metadata without loading full content."""
        if self._metadata is None:
            stat = self.file_path.stat()
            content = self._load_content()
            
            self._metadata = {
                "file_path": str(self.file_path),
                "size_bytes": stat.st_size,
                "estimated_tokens": len(content) // 4,
                "line_count": content.count('\n') + 1,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        
        return self._metadata
    
    def regex_search(self, pattern: str, flags: int = 0) -> List[str]:
        """
        Find all matches for regex pattern.
        
        RLM Technique: Pattern-based retrieval
        Constitutional Reference: Article VII Section 2.3
        """
        content = self._load_content()
        return re.findall(pattern, content, flags)
    
    def window_search(self, query: str, window_chars: int = 4000) -> List[str]:
        """
        Extract context windows around query matches.
        
        RLM Technique: Context window extraction
        Constitutional Reference: Article VII Section 2.3
        """
        content = self._load_content()
        windows = []
        
        start = 0
        while True:
            idx = content.find(query, start)
            if idx == -1:
                break
            
            window_start = max(0, idx - window_chars // 2)
            window_end = min(len(content), idx + window_chars // 2)
            
            window = content[window_start:window_end]
            windows.append(window)
            
            start = idx + len(query)
        
        return windows
    
    def chunk_search(self, query: str, chunk_size: int = 2000) -> List[Dict]:
        """
        Location-aware chunked search with position metadata.
        
        RLM Technique: Chunked location-aware search
        Constitutional Reference: Article VII Section 2.3
        """
        content = self._load_content()
        results = []
        
        # Split into chunks
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            if query.lower() in chunk.lower():
                results.append({
                    "chunk_index": i,
                    "position_start": i * chunk_size,
                    "position_end": min((i + 1) * chunk_size, len(content)),
                    "content": chunk,
                    "has_match": True
                })
        
        return results
    
    def extract_json_objects(self, key_filter: Optional[str] = None) -> List[Dict]:
        """
        Extract JSON objects from content.
        
        RLM Technique: Structured data extraction
        Constitutional Reference: Article VII Section 2.3
        """
        content = self._load_content()
        objects = []
        
        # Find JSON-like patterns
        json_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')
        
        for match in json_pattern.finditer(content):
            try:
                obj = json.loads(match.group())
                if key_filter is None or key_filter in obj:
                    objects.append(obj)
            except json.JSONDecodeError:
                continue
        
        return objects


class ContextLibrarian:
    """
    Context Librarian - Agent Sigma
    
    Manages the Context Vault system for EPOS.
    """
    
    def __init__(self, epos_root: Optional[Path] = None, verbose: bool = False):
        """Initialize the Context Librarian."""
        self.epos_root = epos_root or Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
        self.verbose = verbose
        self.vault_root = self.epos_root / "context_vault"
        
        # Load environment
        self._load_environment()
        
        # Ensure vault structure exists
        self._ensure_vault_structure()
    
    def _load_environment(self):
        """Load .env file."""
        try:
            from dotenv import load_dotenv
            env_path = self.epos_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass
    
    def _log(self, message: str):
        """Print message if verbose."""
        if self.verbose:
            print(f"[Librarian] {message}")
    
    def _ensure_vault_structure(self):
        """Ensure vault directory structure exists."""
        subdirs = ["mission_data", "bi_history", "market_sentiment", "agent_logs", "archive"]
        
        for subdir in subdirs:
            (self.vault_root / subdir).mkdir(parents=True, exist_ok=True)
        
        # Ensure registry exists
        registry_path = self.vault_root / "registry.json"
        if not registry_path.exists():
            registry = {
                "vaults": {},
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
            }
            registry_path.write_text(json.dumps(registry, indent=2))
    
    def _get_registry(self) -> Dict:
        """Load vault registry."""
        registry_path = self.vault_root / "registry.json"
        return json.loads(registry_path.read_text())
    
    def _save_registry(self, registry: Dict):
        """Save vault registry."""
        registry_path = self.vault_root / "registry.json"
        registry_path.write_text(json.dumps(registry, indent=2))
    
    def _generate_vault_id(self, content: str) -> str:
        """Generate unique vault ID from content hash."""
        return sha256(content.encode()).hexdigest()[:16]
    
    # =========================================================================
    # LARGE INPUT TRIAGE
    # =========================================================================
    
    def estimate_tokens(self, content: str) -> int:
        """Estimate token count (1 token ≈ 4 characters)."""
        return len(content) // 4
    
    def should_use_vault(self, content: str, threshold: int = 8192) -> bool:
        """Check if content exceeds token threshold."""
        return self.estimate_tokens(content) > threshold
    
    def ingest_large_input(
        self,
        content: str,
        mission_id: str,
        category: str = "mission_data",
        tags: Optional[List[str]] = None,
        chunk_size: int = 4000
    ) -> VaultManifest:
        """
        Ingest large content into vault with chunking.
        
        Workflow: large_input_triage
        Constitutional Reference: Article VII Section 1.3
        """
        self._log(f"Ingesting content for mission: {mission_id}")
        
        tags = tags or []
        estimated_tokens = self.estimate_tokens(content)
        
        # Create mission directory
        mission_dir = self.vault_root / category / mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)
        
        # Chunk content
        chunks = []
        chunk_files = []
        
        for i, start in enumerate(range(0, len(content), chunk_size)):
            chunk_content = content[start:start + chunk_size]
            chunk_file = mission_dir / f"chunk_{i:04d}.txt"
            chunk_file.write_text(chunk_content, encoding='utf-8')
            
            chunks.append(chunk_content)
            chunk_files.append(str(chunk_file.relative_to(self.vault_root)))
        
        # Generate summary (first 500 chars)
        summary = content[:500] + "..." if len(content) > 500 else content
        
        # Generate search hints (extract key terms)
        words = re.findall(r'\b\w{4,}\b', content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        search_hints = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:20]
        
        # Create manifest
        manifest = VaultManifest(
            mission_id=mission_id,
            created=datetime.now().isoformat(),
            total_chunks=len(chunks),
            total_tokens=estimated_tokens,
            chunk_files=chunk_files,
            summary=summary,
            search_hints=search_hints
        )
        
        # Save manifest
        manifest_path = mission_dir / "vault_manifest.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))
        
        # Update registry
        registry = self._get_registry()
        vault_id = self._generate_vault_id(content)
        
        registry["vaults"][vault_id] = VaultFile(
            vault_id=vault_id,
            file_path=str(mission_dir.relative_to(self.vault_root)),
            original_name=f"mission_{mission_id}",
            size_bytes=len(content.encode()),
            estimated_tokens=estimated_tokens,
            created=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=0,
            checksum=sha256(content.encode()).hexdigest(),
            category=category,
            tags=tags
        ).to_dict()
        
        self._save_registry(registry)
        
        self._log(f"  Ingested: {len(chunks)} chunks, {estimated_tokens} tokens")
        
        return manifest
    
    # =========================================================================
    # CONTEXT RETRIEVAL
    # =========================================================================
    
    def get_vault(self, vault_path: str) -> ContextVault:
        """
        Get a ContextVault instance for symbolic search.
        
        Workflow: context_retrieval
        Constitutional Reference: Article VII Section 3
        """
        full_path = self.vault_root / vault_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Vault file not found: {vault_path}")
        
        # Update access tracking
        self._update_access_tracking(vault_path)
        
        return ContextVault(full_path)
    
    def search_vaults(
        self,
        query: str,
        category: Optional[str] = None,
        method: str = "window",
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Search across multiple vaults.
        
        Workflow: context_retrieval
        Constitutional Reference: Article VII Section 3
        """
        import time
        start_time = time.time()
        
        results = []
        registry = self._get_registry()
        
        # Filter vaults by category
        vaults = registry.get("vaults", {})
        if category:
            vaults = {k: v for k, v in vaults.items() if v.get("category") == category}
        
        for vault_id, vault_info in vaults.items():
            try:
                vault_path = vault_info["file_path"]
                
                # For chunked vaults, search manifest
                manifest_path = self.vault_root / vault_path / "vault_manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    
                    # Search each chunk
                    matches = []
                    positions = []
                    windows = []
                    
                    for i, chunk_file in enumerate(manifest["chunk_files"]):
                        chunk_path = self.vault_root / chunk_file
                        vault = ContextVault(chunk_path)
                        
                        if method == "window":
                            chunk_windows = vault.window_search(query, window_chars=2000)
                        elif method == "regex":
                            chunk_windows = vault.regex_search(query)
                        else:
                            chunk_windows = vault.window_search(query)
                        
                        if chunk_windows:
                            matches.extend(chunk_windows[:3])  # Limit per chunk
                            positions.append(i)
                            windows.extend(chunk_windows[:3])
                    
                    if matches:
                        results.append(SearchResult(
                            vault_id=vault_id,
                            matches=matches[:top_k],
                            positions=positions,
                            context_windows=windows[:top_k],
                            total_matches=len(matches),
                            search_time_ms=(time.time() - start_time) * 1000
                        ))
                
                else:
                    # Single file vault
                    for file_path in (self.vault_root / vault_path).glob("*.txt"):
                        vault = ContextVault(file_path)
                        
                        if method == "window":
                            windows = vault.window_search(query, window_chars=2000)
                        elif method == "regex":
                            windows = vault.regex_search(query)
                        else:
                            windows = vault.window_search(query)
                        
                        if windows:
                            results.append(SearchResult(
                                vault_id=vault_id,
                                matches=windows[:top_k],
                                positions=[],
                                context_windows=windows[:top_k],
                                total_matches=len(windows),
                                search_time_ms=(time.time() - start_time) * 1000
                            ))
                
            except Exception as e:
                self._log(f"  Warning: Error searching vault {vault_id}: {e}")
        
        # Sort by match count and limit
        results.sort(key=lambda x: x.total_matches, reverse=True)
        return results[:top_k]
    
    def _update_access_tracking(self, vault_path: str):
        """Update access timestamp and count for a vault."""
        registry = self._get_registry()
        
        for vault_id, vault_info in registry.get("vaults", {}).items():
            if vault_info.get("file_path") == vault_path:
                vault_info["last_accessed"] = datetime.now().isoformat()
                vault_info["access_count"] = vault_info.get("access_count", 0) + 1
                break
        
        self._save_registry(registry)
    
    # =========================================================================
    # VAULT HYGIENE
    # =========================================================================
    
    def detect_cold_data(self, days_threshold: int = 30, query_threshold: int = 5) -> List[Dict]:
        """
        Detect cold (unused) vault data.
        
        Workflow: vault_hygiene
        """
        cold_vaults = []
        registry = self._get_registry()
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        for vault_id, vault_info in registry.get("vaults", {}).items():
            last_accessed = datetime.fromisoformat(vault_info.get("last_accessed", "2020-01-01"))
            access_count = vault_info.get("access_count", 0)
            
            if last_accessed < cutoff_date and access_count < query_threshold:
                cold_vaults.append({
                    "vault_id": vault_id,
                    "file_path": vault_info.get("file_path"),
                    "last_accessed": vault_info.get("last_accessed"),
                    "access_count": access_count,
                    "size_bytes": vault_info.get("size_bytes", 0)
                })
        
        return cold_vaults
    
    def archive_vault(self, vault_id: str) -> Optional[str]:
        """
        Compress and archive a cold vault.
        
        Workflow: vault_hygiene
        """
        registry = self._get_registry()
        vault_info = registry.get("vaults", {}).get(vault_id)
        
        if not vault_info:
            return None
        
        source_path = self.vault_root / vault_info["file_path"]
        archive_dir = self.vault_root / "archive"
        
        if source_path.is_dir():
            # Archive directory
            archive_path = archive_dir / f"{vault_id}.tar.gz"
            
            import tarfile
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(source_path, arcname=vault_id)
            
            # Remove original
            shutil.rmtree(source_path)
            
        elif source_path.is_file():
            # Archive single file
            archive_path = archive_dir / f"{source_path.stem}.gz"
            
            with open(source_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remove original
            source_path.unlink()
        
        else:
            return None
        
        # Update registry
        vault_info["archived"] = True
        vault_info["archive_path"] = str(archive_path.relative_to(self.vault_root))
        vault_info["archived_date"] = datetime.now().isoformat()
        
        self._save_registry(registry)
        
        self._log(f"Archived: {vault_id} → {archive_path}")
        
        return str(archive_path)
    
    def run_hygiene(self, dry_run: bool = False) -> Dict:
        """
        Run full vault hygiene process.
        
        Workflow: vault_hygiene (nightly cron)
        """
        self._log("Running vault hygiene...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "cold_detected": [],
            "archived": [],
            "space_recovered_bytes": 0
        }
        
        # Detect cold data
        cold_vaults = self.detect_cold_data()
        results["cold_detected"] = cold_vaults
        
        self._log(f"  Found {len(cold_vaults)} cold vaults")
        
        # Archive cold vaults
        for vault in cold_vaults:
            if not dry_run:
                archive_path = self.archive_vault(vault["vault_id"])
                if archive_path:
                    results["archived"].append(vault["vault_id"])
                    results["space_recovered_bytes"] += vault.get("size_bytes", 0) * 0.7  # Estimate compression
        
        # Save report
        reports_dir = self.epos_root / "ops" / "vault_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / f"{datetime.now().strftime('%Y%m%d')}.json"
        report_path.write_text(json.dumps(results, indent=2))
        
        # Log to BI
        self._log_to_bi(results)
        
        return results
    
    def _log_to_bi(self, hygiene_results: Dict):
        """Log hygiene results to BI decision log."""
        bi_log_path = self.epos_root / "bi_decision_log.json"
        
        try:
            if bi_log_path.exists():
                bi_data = json.loads(bi_log_path.read_text())
            else:
                bi_data = {"decisions": []}
            
            # Calculate vault metrics
            registry = self._get_registry()
            total_vaults = len(registry.get("vaults", {}))
            total_bytes = sum(v.get("size_bytes", 0) for v in registry.get("vaults", {}).values())
            
            bi_data["decisions"].append({
                "agent": "context_librarian",
                "action": "vault_hygiene",
                "timestamp": hygiene_results["timestamp"],
                "cold_vaults_found": len(hygiene_results["cold_detected"]),
                "vaults_archived": len(hygiene_results["archived"]),
                "space_recovered_mb": round(hygiene_results["space_recovered_bytes"] / (1024*1024), 2),
                "vault_metrics": {
                    "total_vaults": total_vaults,
                    "total_size_mb": round(total_bytes / (1024*1024), 2)
                }
            })
            
            bi_log_path.write_text(json.dumps(bi_data, indent=2))
        except Exception as e:
            self._log(f"Warning: Could not log to BI: {e}")
    
    # =========================================================================
    # AGENT ZERO INTEGRATION
    # =========================================================================
    
    def create_agent_zero_tools(self, vault_path: str) -> Dict:
        """
        Create tool specifications for Agent Zero integration.
        
        Constitutional Reference: Article VII Section 3.1
        """
        vault = self.get_vault(vault_path)
        
        return {
            "search_context": {
                "function": vault.regex_search,
                "description": "Search vault content using regex pattern",
                "parameters": {"pattern": "string", "flags": "int (optional)"}
            },
            "get_context_window": {
                "function": vault.window_search,
                "description": "Get context windows around query matches",
                "parameters": {"query": "string", "window_chars": "int (default 4000)"}
            },
            "get_chunks": {
                "function": vault.chunk_search,
                "description": "Get location-aware chunks containing query",
                "parameters": {"query": "string", "chunk_size": "int (default 2000)"}
            },
            "get_metadata": {
                "function": vault.get_metadata,
                "description": "Get vault file metadata without loading content",
                "parameters": {}
            }
        }
    
    def get_vault_status(self) -> Dict:
        """Get overall vault status for health checks."""
        registry = self._get_registry()
        vaults = registry.get("vaults", {})
        
        total_size = sum(v.get("size_bytes", 0) for v in vaults.values())
        total_tokens = sum(v.get("estimated_tokens", 0) for v in vaults.values())
        
        return {
            "total_vaults": len(vaults),
            "total_size_mb": round(total_size / (1024*1024), 2),
            "total_tokens": total_tokens,
            "categories": list(set(v.get("category", "unknown") for v in vaults.values())),
            "registry_version": registry.get("version", "unknown"),
            "constitutional_authority": registry.get("constitutional_authority", "unknown")
        }


def main():
    """CLI entrypoint for Context Librarian."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Librarian (Agent Sigma)")
    parser.add_argument("--ingest", type=str, help="Ingest a file into vault")
    parser.add_argument("--mission-id", type=str, help="Mission ID for ingestion")
    parser.add_argument("--search", type=str, help="Search vaults for query")
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--hygiene", action="store_true", help="Run vault hygiene")
    parser.add_argument("--status", action="store_true", help="Show vault status")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    librarian = ContextLibrarian(verbose=args.verbose)
    
    if args.ingest:
        if not args.mission_id:
            print("❌ --mission-id required for ingestion")
            sys.exit(1)
        
        file_path = Path(args.ingest)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        
        content = file_path.read_text()
        manifest = librarian.ingest_large_input(content, args.mission_id)
        
        if args.json:
            print(json.dumps(manifest.to_dict(), indent=2))
        else:
            print(f"✅ Ingested: {manifest.total_chunks} chunks, {manifest.total_tokens} tokens")
        
        sys.exit(0)
    
    elif args.search:
        results = librarian.search_vaults(args.search, category=args.category)
        
        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print(f"Found {len(results)} vault(s) with matches:")
            for r in results:
                print(f"  - {r.vault_id}: {r.total_matches} matches")
        
        sys.exit(0)
    
    elif args.hygiene:
        results = librarian.run_hygiene(dry_run=args.dry_run)
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Hygiene Results:")
            print(f"  Cold vaults: {len(results['cold_detected'])}")
            print(f"  Archived: {len(results['archived'])}")
            print(f"  Space recovered: {results['space_recovered_bytes'] / (1024*1024):.2f} MB")
        
        sys.exit(0)
    
    elif args.status:
        status = librarian.get_vault_status()
        
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("📚 Context Vault Status")
            print(f"   Vaults: {status['total_vaults']}")
            print(f"   Size: {status['total_size_mb']} MB")
            print(f"   Tokens: {status['total_tokens']:,}")
            print(f"   Categories: {', '.join(status['categories'])}")
        
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
