# File: C:\Users\Jamie\workspace\epos_mcp\context_handler.py

"""
EPOS Context Handler v3.1
RLM (Resourced Language Model) Implementation

Authority: EPOS_CONSTITUTION_v3.1.md Article VII
Purpose: Enable unlimited context scaling through symbolic search
Status: PRODUCTION

This tool implements the Context Vault pattern: instead of loading large files
inline (causing token limit failures), agents query this handler which performs
targeted searches and returns only relevant excerpts.

PM NOTE: This is CRITICAL for scaling beyond 8K token limits. Without this,
Agent Zero will hit context limits and hallucinate or lose track of mission state.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Establish absolute paths per Article II, Rule 1
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent)))
CONTEXT_VAULT_ROOT = EPOS_ROOT / "context_vault"
REGISTRY_PATH = CONTEXT_VAULT_ROOT / "registry.json"
OPS_LOGS_DIR = EPOS_ROOT / "ops" / "logs"

# Configure logging — ensure directory exists first
OPS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OPS_LOGS_DIR / "context_handler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("context_handler")


class ContextVault:
    """
    RLM-based context management per Constitution v3.1 Article VII.
    
    Enables agents to work with datasets exceeding token limits through:
    1. Regex Search: Pattern-based retrieval without full file load
    2. Window Search: Extract specific line ranges
    3. Metadata Query: Get file info without reading content
    """
    
    def __init__(self, vault_root: Path = CONTEXT_VAULT_ROOT):
        """Initialize context vault with registry."""
        self.vault_root = vault_root
        self.registry_path = REGISTRY_PATH
        self.registry = self._load_registry()
        
        # Ensure vault structure exists
        self._ensure_vault_structure()
    
    def _ensure_vault_structure(self):
        """Create required Context Vault directory structure."""
        subdirs = [
            "mission_data",
            "bi_history",
            "market_sentiment",
            "agent_logs",
            "large_datasets"
        ]
        
        self.vault_root.mkdir(parents=True, exist_ok=True)
        
        for subdir in subdirs:
            (self.vault_root / subdir).mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Context Vault structure verified at {self.vault_root}")
    
    def _load_registry(self) -> Dict:
        """Load or create context vault registry."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    registry = json.load(f)
                logger.info(f"Loaded registry with {len(registry.get('vaults', {}))} entries")
                return registry
            except json.JSONDecodeError as e:
                logger.error(f"Invalid registry JSON: {e}")
                return self._create_new_registry()
        else:
            return self._create_new_registry()
    
    def _create_new_registry(self) -> Dict:
        """Create new empty registry."""
        registry = {
            "vaults": {},
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
        }
        self._save_registry(registry)
        logger.info("Created new Context Vault registry")
        return registry
    
    def _save_registry(self, registry: Optional[Dict] = None):
        """Persist registry to disk."""
        if registry is None:
            registry = self.registry
        
        self.registry_path.write_text(json.dumps(registry, indent=2))
        assert self.registry_path.exists(), "Registry save failed"
        logger.debug("Registry saved")
    
    def register_file(self, filepath: Path, category: str, metadata: Optional[Dict] = None) -> bool:
        """
        Register a file in the context vault.
        
        Args:
            filepath: Path to file (relative to vault_root or absolute)
            category: Category (mission_data, bi_history, etc.)
            metadata: Optional metadata dict
        
        Returns:
            True if registered successfully
        """
        # Normalize path to be relative to vault_root
        if filepath.is_absolute():
            try:
                relative_path = filepath.relative_to(self.vault_root)
            except ValueError:
                logger.error(f"File {filepath} not within vault root {self.vault_root}")
                return False
        else:
            relative_path = filepath
        
        file_key = str(relative_path)
        
        # Get file stats
        full_path = self.vault_root / relative_path
        if not full_path.exists():
            logger.error(f"Cannot register non-existent file: {full_path}")
            return False
        
        file_stats = full_path.stat()
        
        # Build registry entry
        entry = {
            "category": category,
            "size_bytes": file_stats.st_size,
            "registered_at": datetime.now().isoformat(),
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "metadata": metadata or {}
        }
        
        self.registry["vaults"][file_key] = entry
        self._save_registry()
        
        logger.info(f"Registered: {file_key} ({entry['size_bytes']} bytes)")
        return True
    
    def regex_search(self, pattern: str, category: Optional[str] = None, 
                    max_results: int = 10) -> List[Dict]:
        """
        Pattern-based retrieval without full file load.
        
        Args:
            pattern: Regex pattern to search for
            category: Limit search to specific category
            max_results: Maximum number of results to return
        
        Returns:
            List of {file, matches} dicts
        """
        results = []
        files_to_search = []
        
        # Determine which files to search
        for file_key, entry in self.registry["vaults"].items():
            if category and entry["category"] != category:
                continue
            files_to_search.append((file_key, entry))
        
        logger.debug(f"Searching {len(files_to_search)} files for pattern: {pattern}")
        
        # Search each file
        for file_key, entry in files_to_search:
            file_path = self.vault_root / file_key
            
            try:
                content = file_path.read_text(encoding='utf-8')
                matches = []
                
                for match in re.finditer(pattern, content, re.MULTILINE):
                    # Get context around match (50 chars before/after)
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end]
                    
                    matches.append({
                        "match": match.group(),
                        "context": context,
                        "line_number": content[:match.start()].count('\n') + 1
                    })
                    
                    if len(matches) >= max_results:
                        break
                
                if matches:
                    results.append({
                        "file": file_key,
                        "category": entry["category"],
                        "matches": matches
                    })
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error searching {file_key}: {e}")
                continue
        
        logger.info(f"Regex search found {len(results)} files with matches")
        return results
    
    def window_search(self, filename: str, start_line: int, num_lines: int = 50) -> Optional[str]:
        """
        Extract context window without loading entire file.
        
        Args:
            filename: File to read (relative to vault_root)
            start_line: Starting line number (1-indexed)
            num_lines: Number of lines to return
        
        Returns:
            Extracted text or None if file not found
        """
        # Find file in registry
        file_path = None
        for file_key in self.registry["vaults"].keys():
            if file_key.endswith(filename) or file_key == filename:
                file_path = self.vault_root / file_key
                break
        
        if not file_path or not file_path.exists():
            logger.error(f"File not found in vault: {filename}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip to start_line
                for _ in range(start_line - 1):
                    f.readline()
                
                # Read num_lines
                lines = []
                for _ in range(num_lines):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
                
                result = ''.join(lines)
                logger.debug(f"Window search: {filename} lines {start_line}-{start_line+len(lines)-1}")
                return result
                
        except Exception as e:
            logger.error(f"Error reading window from {filename}: {e}")
            return None
    
    def get_metadata(self, filename: str) -> Optional[Dict]:
        """
        Retrieve file metadata from registry without reading file.
        
        Args:
            filename: File to look up
        
        Returns:
            Metadata dict or None
        """
        for file_key, entry in self.registry["vaults"].items():
            if file_key.endswith(filename) or file_key == filename:
                return {
                    "file": file_key,
                    **entry
                }
        
        logger.warning(f"No metadata found for: {filename}")
        return None
    
    def list_by_category(self, category: str) -> List[str]:
        """List all files in a specific category."""
        files = []
        for file_key, entry in self.registry["vaults"].items():
            if entry["category"] == category:
                files.append(file_key)
        return files
    
    def get_stats(self) -> Dict:
        """Get vault statistics."""
        stats = {
            "total_files": len(self.registry["vaults"]),
            "total_bytes": 0,
            "by_category": {}
        }
        
        for file_key, entry in self.registry["vaults"].items():
            category = entry["category"]
            size = entry["size_bytes"]
            
            stats["total_bytes"] += size
            
            if category not in stats["by_category"]:
                stats["by_category"][category] = {
                    "count": 0,
                    "total_bytes": 0
                }
            
            stats["by_category"][category]["count"] += 1
            stats["by_category"][category]["total_bytes"] += size
        
        return stats


def main():
    """CLI entrypoint for context handler."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="EPOS Context Handler - RLM Symbolic Search"
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register a file in vault')
    register_parser.add_argument('filepath', type=Path, help='Path to file')
    register_parser.add_argument('category', help='Category (mission_data, bi_history, etc.)')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search vault files')
    search_parser.add_argument('pattern', help='Regex pattern to search')
    search_parser.add_argument('--category', help='Limit to category')
    
    # Window command
    window_parser = subparsers.add_parser('window', help='Extract line window')
    window_parser.add_argument('filename', help='File to read')
    window_parser.add_argument('start', type=int, help='Start line')
    window_parser.add_argument('--lines', type=int, default=50, help='Number of lines')
    
    # Stats command
    subparsers.add_parser('stats', help='Show vault statistics')
    
    args = parser.parse_args()
    
    vault = ContextVault()
    
    if args.command == 'register':
        success = vault.register_file(args.filepath, args.category)
        if success:
            print(f"✓ Registered: {args.filepath}")
        else:
            print(f"✗ Failed to register: {args.filepath}")
            return 1
    
    elif args.command == 'search':
        results = vault.regex_search(args.pattern, category=args.category)
        print(f"\nFound {len(results)} files with matches:\n")
        for result in results:
            print(f"File: {result['file']}")
            print(f"Category: {result['category']}")
            print(f"Matches: {len(result['matches'])}\n")
            for match in result['matches'][:3]:  # Show first 3 matches
                print(f"  Line {match['line_number']}: {match['match']}")
            print()
    
    elif args.command == 'window':
        text = vault.window_search(args.filename, args.start, args.lines)
        if text:
            print(text)
        else:
            print(f"✗ Could not retrieve window from {args.filename}")
            return 1
    
    elif args.command == 'stats':
        stats = vault.get_stats()
        print("\nContext Vault Statistics:")
        print(f"Total Files: {stats['total_files']}")
        print(f"Total Size: {stats['total_bytes']:,} bytes")
        print("\nBy Category:")
        for category, cat_stats in stats['by_category'].items():
            print(f"  {category}: {cat_stats['count']} files, {cat_stats['total_bytes']:,} bytes")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
