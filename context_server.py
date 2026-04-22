# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/enforcement/context_server.py
"""
EPOS Context Server - Context Injection and RLM Symbolic Search
Constitutional Authority: Article VII (Context Governance)

This server manages the Context Vault and provides:
1. Context injection into agent mission briefings
2. Symbolic search across vault contents (RLM-style)
3. Persistent learning storage
"""

from pathlib import Path
from datetime import datetime
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from event_bus import get_event_bus
except ImportError:
    get_event_bus = None


@dataclass
class SearchResult:
    """A search result from the context vault."""
    file_path: str
    relevance_score: float
    snippet: str
    context_type: str
    metadata: Dict[str, Any]


class ContextVault:
    """Manages the EPOS Context Vault."""
    
    DEFAULT_EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent)))
    MAX_INLINE_TOKENS = 8192
    
    def __init__(self, vault_path: Path = None):
        self.epos_root = Path(os.getenv("EPOS_ROOT", str(self.DEFAULT_EPOS_ROOT)))
        self.vault_path = vault_path or (self.epos_root / "context_vault")
        
        self.domains = {
            "learning": self.vault_path / "learning",
            "market": self.vault_path / "market_sentiment",
            "agent_logs": self.vault_path / "agent_logs",
            "mission_data": self.vault_path / "mission_data",
            "events": self.vault_path / "events",
        }
        
        for domain_path in self.domains.values():
            domain_path.mkdir(parents=True, exist_ok=True)
        
        self.registry_path = self.vault_path / "registry.json"
        self._load_registry()
    
    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
            except:
                self.registry = {"items": [], "last_updated": None}
        else:
            self.registry = {"items": [], "last_updated": None}
    
    def _save_registry(self):
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2)
    
    def store(self, content: str, domain: str, filename: str, metadata: Dict[str, Any] = None) -> str:
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        
        file_path = self.domains[domain] / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        self.registry["items"].append({
            "path": str(file_path),
            "domain": domain,
            "filename": filename,
            "stored_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "size_bytes": len(content.encode("utf-8"))
        })
        self._save_registry()
        
        return str(file_path)
    
    def retrieve(self, file_path: str) -> Optional[str]:
        path = Path(file_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    
    def search(self, query: str, scope: str = "all", max_results: int = 10) -> List[SearchResult]:
        results = []
        keywords = query.lower().split()
        
        if scope == "all":
            domains_to_search = list(self.domains.values())
        elif scope in self.domains:
            domains_to_search = [self.domains[scope]]
        else:
            return []
        
        for domain_path in domains_to_search:
            for file_path in domain_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json", ".jsonl"]:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        content_lower = content.lower()
                        
                        score = sum(content_lower.count(kw) for kw in keywords) / max(len(content), 1)
                        
                        if score > 0:
                            snippet = self._extract_snippet(content, keywords[0])
                            context_type = file_path.parent.name
                            
                            results.append(SearchResult(
                                file_path=str(file_path),
                                relevance_score=score,
                                snippet=snippet,
                                context_type=context_type,
                                metadata={"filename": file_path.name}
                            ))
                    except:
                        pass
        
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:max_results]
    
    def _extract_snippet(self, content: str, keyword: str, context_chars: int = 200) -> str:
        pos = content.lower().find(keyword.lower())
        if pos == -1:
            return content[:context_chars] + "..."
        
        start = max(0, pos - context_chars // 2)
        end = min(len(content), pos + len(keyword) + context_chars // 2)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        context = {
            "agent_id": agent_id,
            "retrieved_at": datetime.now().isoformat(),
            "performance": None,
            "recent_lessons": [],
            "improvement_areas": []
        }
        
        perf_file = self.domains["learning"] / "agent_performance" / f"{agent_id}.jsonl"
        if perf_file.exists():
            records = []
            with open(perf_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except:
                            pass
            
            violations = [r for r in records if r.get("type") == "violation"]
            successes = [r for r in records if r.get("type") == "success"]
            
            total = len(violations) + len(successes)
            context["performance"] = {
                "total_violations": len(violations),
                "total_successes": len(successes),
                "compliance_rate": len(successes) / total if total else 1.0
            }
        
        return context
    
    def health_check(self) -> Dict[str, Any]:
        domain_stats = {}
        for name, path in self.domains.items():
            if path.exists():
                files = list(path.rglob("*"))
                domain_stats[name] = {
                    "exists": True,
                    "file_count": sum(1 for f in files if f.is_file()),
                }
            else:
                domain_stats[name] = {"exists": False}
        
        return {
            "status": "healthy",
            "vault_path": str(self.vault_path),
            "domains": domain_stats,
        }


class ContextServer:
    """Main context server that manages context injection."""
    
    def __init__(self):
        self.event_bus = get_event_bus() if get_event_bus else None
        self.vault = ContextVault()
        self._running = False
    
    def start(self):
        if not self.event_bus:
            print("[ContextServer] Warning: Event bus not available")
            return
        
        self.event_bus.subscribe("learning.remediation_generated", self._handle_remediation)
        self.event_bus.subscribe("agent.mission_started", self._handle_mission_start)
        self.event_bus.start_polling()
        self._running = True
        
        print("[ContextServer] Started")
    
    def stop(self):
        self._running = False
        if self.event_bus:
            self.event_bus.stop_polling()
        print("[ContextServer] Stopped")
    
    def _handle_remediation(self, event: Dict[str, Any]):
        payload = event.get("payload", {})
        metadata = event.get("metadata", {})
        
        agent_id = payload.get("agent_id", "unknown")
        lesson_path = payload.get("lesson_path")
        violations = payload.get("violations", [])
        trace_id = metadata.get("trace_id")
        
        print(f"[ContextServer] Context ready for {agent_id}")
        
        if self.event_bus:
            self.event_bus.publish(
                event_type="context.injected",
                payload={
                    "agent_id": agent_id,
                    "context_type": "remediation",
                    "content_summary": f"Lesson for: {', '.join(violations)}",
                    "lesson_path": lesson_path,
                },
                metadata={"trace_id": trace_id},
                source_server="context_server"
            )
    
    def _handle_mission_start(self, event: Dict[str, Any]):
        payload = event.get("payload", {})
        metadata = event.get("metadata", {})
        
        agent_id = payload.get("agent_id", "unknown")
        mission_id = payload.get("mission_id")
        trace_id = metadata.get("trace_id")
        
        context = self.vault.get_agent_context(agent_id)
        
        context_filename = f"mission_context_{mission_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        context_path = self.vault.store(
            content=json.dumps(context, indent=2),
            domain="mission_data",
            filename=context_filename,
            metadata={"agent_id": agent_id, "mission_id": mission_id}
        )
        
        if self.event_bus:
            self.event_bus.publish(
                event_type="context.stored",
                payload={
                    "agent_id": agent_id,
                    "mission_id": mission_id,
                    "context_path": context_path,
                },
                metadata={"trace_id": trace_id},
                source_server="context_server"
            )


def search_vault(query: str, scope: str = "all", max_results: int = 10) -> List[Dict[str, Any]]:
    vault = ContextVault()
    results = vault.search(query, scope, max_results)
    return [asdict(r) for r in results]


if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="EPOS Context Server")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--health", action="store_true", help="Show health status")
    
    args = parser.parse_args()
    
    if args.health:
        vault = ContextVault()
        health = vault.health_check()
        print("\n🏥 Context Vault Health")
        print("=" * 40)
        for k, v in health.items():
            print(f"  {k}: {v}")
    
    elif args.test:
        print("\n📦 Context Server Self-Test")
        print("=" * 40)
        
        vault = ContextVault()
        path = vault.store("Test content", "learning", "test.txt", {"test": True})
        print(f"  Stored: {path}")
        
        content = vault.retrieve(path)
        print(f"  Retrieved: {content}")
        
        print("\n✅ Self-test complete!")
    
    elif args.daemon:
        server = ContextServer()
        server.start()
        
        print("\n📦 Context Server Running (Ctrl+C to stop)")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
    
    else:
        print("Use --daemon, --test, or --health")
