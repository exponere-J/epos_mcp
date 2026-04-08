# File: C:/Users/Jamie/workspace/epos_mcp/engine\epos_doctor.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: C:\Users\Jamie\workspace\epos_mcp\engine\epos_doctor.py
# ═══════════════════════════════════════════════════════════════
# EPOS GOVERNANCE WATERMARK
# ───────────────────────────────────────────────────────────────
# Triage ID:      TRG-20260218-DOCTOR-V32
# First Submitted: 2026-02-18T06:00:00Z
# Triage Result:   PROMOTED (attempt 1 of 1)
# Promoted At:     2026-02-18T06:00:00Z
# Destination:     engine/epos_doctor.py
# Constitutional:  Article II, III, VII, XIV compliant
# Violations:      None
# Watermark Hash:  PENDING_FIRST_TRIAGE
# ═══════════════════════════════════════════════════════════════

"""
EPOS Doctor v3.2 - Comprehensive Environment Validation + Article XIV Governance

Constitutional Authority: EPOS_CONSTITUTION_v3.1.md Article III + Article XIV
Purpose: Automate pre-flight validation, enforce file governance, and self-heal

WHAT'S NEW IN v3.2:
  - Article XIV enforcement: watermark presence, hash integrity, registry completeness
  - Self-healing: missing governance tools auto-restored from engine/
  - Quarantine detection: ungoverned files in production paths flagged
  - Bootstrap mode monitoring: warns if bootstrap active > 4 hours
  - Duplicate detection: flags files existing in both root and engine/
  - Unified launcher check: verifies epos_start.ps1 exists
  - Doctrine file validation: confirms all 3 core doctrine files present
  - Content Lab health: validates C10 attachment status

Exit Codes:
    0 = all pass (proceed with execution)
    1 = failures detected (fix before proceeding)
    2 = critical constitutional violation (immediate intervention required)

Usage:
    python epos_doctor.py                        # Run all checks
    python epos_doctor.py --verbose              # Detailed output
    python epos_doctor.py --check-constitution   # Validate constitutional docs only
    python epos_doctor.py --check-context        # Validate Context Vault only
    python epos_doctor.py --check-governance     # Validate Article XIV only
    python epos_doctor.py --json                 # JSON output for automation
    python epos_doctor.py --cron                 # Daily health check mode
    python epos_doctor.py --self-heal            # Attempt auto-repair of known issues
"""

import sys
import os
import socket
import subprocess
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

# ════════════════════════════════════════════════════════════════
# PYTHON VERSION GATE (Article II Rule 3)
# ════════════════════════════════════════════════════════════════
REQUIRED_PYTHON = (3, 11)
if sys.version_info[:2] < REQUIRED_PYTHON:
    print(f"CRITICAL: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required")
    print(f"   Current: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"   Constitutional Authority: Article II Rule 3 (Environment Explicitness)")
    sys.exit(2)


class EPOSDoctor:
    """Comprehensive EPOS environment validator for Constitution v3.2
    
    Enforces Articles I-IX (original) + Article XIV (File Governance).
    Supports self-healing mode for automatic repair of known issues.
    """
    
    VERSION = "3.3.0"
    CONSTITUTIONAL_VERSION = "v3.3"
    
    # ════════════════════════════════════════════════════════════
    # CONSTITUTIONAL REQUIREMENTS
    # ════════════════════════════════════════════════════════════
    
    REQUIRED_CONSTITUTIONAL_DOCS = [
        "EPOS_CONSTITUTION_v3.1.md",
        "ENVIRONMENT_SPEC.md",
        "COMPONENT_INTERACTION_MATRIX.md",
        "FAILURE_SCENARIOS.md",
        "PATH_CLARITY_RULES.md",
        "PRE_FLIGHT_CHECKLIST.md",
    ]
    
    REQUIRED_DIRECTORIES = [
        "inbox",
        "engine",
        "rejected/receipts",
        "quarantine",
        "ops/logs",
        "market",
        "context_vault/mission_data",
        "context_vault/bi_history",
        "context_vault/market_sentiment",
        "context_vault/agent_logs",
        "context_vault/doctrine",
        "context_vault/roles",
        "context_vault/governance",
        "context_vault/events",
        "context_vault/niches",
    ]
    
    REQUIRED_DOCTRINE_FILES = [
        "context_vault/doctrine/EPOS_COMPLETION_PROSPECTUS_v2.md",
        "context_vault/doctrine/EPOS_CONSUMER_JOURNEY_MAP_v3.md",
        "context_vault/doctrine/EPOS_Architecture_Decisions_v3_1.html",
    ]
    
    # Governance tools and their canonical locations (for self-healing)
    GOVERNANCE_TOOL_SEARCH_PATHS = {
        "governance_gate.py": [
            "engine/enforcement/governance_gate.py",
            "engine/governance_gate.py",
            "rejected/governance_gate.py",
        ],
        "epos_snapshot.py": [
            "engine/epos_snapshot.py",
            "rejected/epos_snapshot.py",
        ],
        "epos_doctor.py": [
            "engine/epos_doctor.py",
        ],
    }
    
    # Production paths that require governance watermarks (Article XIV)
    GOVERNED_PATHS = [
        "engine",
        "context_vault/doctrine",
        "context_vault/roles",
        "content/lab",
        "missions",
    ]
    
    def __init__(self, verbose: bool = False, silent: bool = False, self_heal: bool = False):
        self.verbose = verbose
        self.silent = silent
        self.self_heal = self_heal
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warned = 0
        self.checks_info = 0
        self.failures: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []
        self.healed: List[Dict] = []
        self.epos_root = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
        
        self._load_environment()
    
    # ════════════════════════════════════════════════════════════
    # INFRASTRUCTURE
    # ════════════════════════════════════════════════════════════
    
    def _load_environment(self):
        """Load .env file if exists."""
        try:
            from dotenv import load_dotenv
            env_path = self.epos_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                if self.verbose:
                    self._log("  Loaded .env from", env_path)
        except ImportError:
            if self.verbose:
                self._log("  python-dotenv not installed (will use environment variables)")
    
    def _log(self, *args):
        """Print if not silent."""
        if not self.silent:
            print(*args)
    
    def _check(self, name: str, test_func, critical: bool = False, info_only: bool = False) -> bool:
        """Run a check and track results."""
        try:
            success, details = test_func()
            
            if success:
                self.checks_passed += 1
                if not self.silent:
                    print(f"  PASS: {name}")
                    if self.verbose and details:
                        print(f"         {details}")
            elif info_only:
                self.checks_info += 1
                if not self.silent:
                    print(f"  INFO: {name}")
                    if details:
                        print(f"         {details}")
                self.info.append({"check": name, "details": details, "severity": "info"})
            elif critical:
                self.checks_failed += 1
                if not self.silent:
                    print(f"  CRITICAL FAIL: {name}")
                    if details:
                        print(f"         {details}")
                self.failures.append({"check": name, "details": details, "severity": "critical"})
            else:
                self.checks_warned += 1
                if not self.silent:
                    print(f"  WARN: {name}")
                    if details:
                        print(f"         {details}")
                self.warnings.append({"check": name, "details": details, "severity": "warning"})
            
            return success
        except Exception as e:
            self.checks_failed += 1
            if not self.silent:
                print(f"  ERROR: {name}")
                print(f"         Exception: {e}")
            self.failures.append({"check": name, "details": f"Exception: {e}", "severity": "error"})
            return False
    
    def _heal(self, action: str, description: str, func) -> bool:
        """Attempt a self-healing action if self_heal mode is active."""
        if not self.self_heal:
            return False
        try:
            result = func()
            if result:
                self.healed.append({
                    "action": action,
                    "description": description,
                    "timestamp": datetime.now().isoformat(),
                    "result": "success"
                })
                if not self.silent:
                    print(f"  HEALED: {description}")
                return True
            return False
        except Exception as e:
            self.healed.append({
                "action": action,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "result": f"failed: {e}"
            })
            return False
    
    @staticmethod
    def _file_hash(filepath: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        h.update(filepath.read_bytes())
        return f"sha256:{h.hexdigest()[:16]}"
    
    # ════════════════════════════════════════════════════════════
    # SECTION A: ORIGINAL v3.1 CHECKS (Checks 1-15)
    # ════════════════════════════════════════════════════════════
    
    def check_python_version(self) -> Tuple[bool, str]:
        """CHECK 1: Verify Python 3.11.x is installed. (Article II Rule 3)"""
        v = sys.version_info
        if v[:2] >= REQUIRED_PYTHON:
            return True, f"Python {v.major}.{v.minor}.{v.micro}"
        return False, f"Python {v.major}.{v.minor}.{v.micro} detected, need 3.11+ (Article II Rule 3)"
    
    def check_epos_root(self) -> Tuple[bool, str]:
        """CHECK 2: Verify EPOS root directory exists. (Article II Rule 1)"""
        if not self.epos_root.exists():
            return False, f"EPOS root not found: {self.epos_root}"
        if not self.epos_root.is_dir():
            return False, f"EPOS root is not a directory: {self.epos_root}"
        return True, f"EPOS root: {self.epos_root}"
    
    def check_constitutional_docs(self) -> Tuple[bool, str]:
        """CHECK 3: Verify all constitutional documents exist. (Article I)"""
        missing = [d for d in self.REQUIRED_CONSTITUTIONAL_DOCS if not (self.epos_root / d).exists()]
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, f"All {len(self.REQUIRED_CONSTITUTIONAL_DOCS)} constitutional documents present"
    
    def check_required_directories(self) -> Tuple[bool, str]:
        """CHECK 4: Verify all required directories exist. (Article VII)"""
        missing = []
        created = []
        for d in self.REQUIRED_DIRECTORIES:
            dp = self.epos_root / d
            if not dp.exists():
                if self.self_heal:
                    dp.mkdir(parents=True, exist_ok=True)
                    created.append(d)
                else:
                    missing.append(d)
        
        if created and not self.silent:
            print(f"         Self-healed: created {len(created)} directories")
        if missing:
            return False, f"Missing directories: {', '.join(missing)}"
        return True, f"All {len(self.REQUIRED_DIRECTORIES)} required directories present"
    
    def check_agent_zero(self) -> Tuple[bool, str]:
        """CHECK 5: Verify Agent Zero is accessible. (Article II Rule 1)"""
        agent_path = Path(os.getenv("AGENT_ZERO_PATH", "C:/Users/Jamie/workspace/agent-zero"))
        if not agent_path.exists():
            return False, f"Agent Zero not found: {agent_path}"
        # AZ v0.8+: agent.py is at repo root (not python/agent.py)
        agent_file = agent_path / "agent.py"
        if not agent_file.exists():
            # Fallback: check legacy location
            agent_file = agent_path / "python" / "agent.py"
        if not agent_file.exists():
            return False, f"Agent Zero corrupted (missing agent.py): {agent_path}"
        return True, f"Agent Zero: {agent_path}"
    
    def check_ollama(self) -> Tuple[bool, str]:
        """CHECK 6: Verify Ollama service is running."""
        port = 11434
        try:
            port = int(os.getenv("OLLAMA_HOST", "http://localhost:11434").split(":")[-1])
        except (ValueError, IndexError):
            pass
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            return True, f"Ollama responding on :{port}"
        return False, f"Ollama not responding on :{port} (start with: ollama serve)"
    
    def check_env_loaded(self) -> Tuple[bool, str]:
        """CHECK 7: Verify required environment variables. (Article II Rule 6)"""
        required = ["EPOS_ROOT", "AGENT_ZERO_PATH", "OLLAMA_HOST"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            return False, f"Missing env vars: {', '.join(missing)}"
        return True, f".env loaded ({len(required)} required variables)"
    
    def check_dependencies(self) -> Tuple[bool, str]:
        """CHECK 8: Verify critical Python dependencies."""
        critical = ["fastapi", "uvicorn", "pydantic", "dotenv"]
        missing = []
        for pkg in critical:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            return False, f"Missing: {', '.join(missing)} (run: pip install {' '.join(missing)})"
        return True, f"All {len(critical)} critical dependencies installed"
    
    def check_port_availability(self) -> Tuple[bool, str]:
        """CHECK 9: Verify EPOS API port status."""
        port = int(os.getenv("EPOS_API_PORT", "8001"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            return False, f"Port {port} already in use (may be the running orchestrator)"
        return True, f"Port {port} available"
    
    def check_logs_writable(self) -> Tuple[bool, str]:
        """CHECK 10: Verify log directory is writable. (Article II Rule 2)"""
        logs_dir = self.epos_root / "logs"
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create logs directory: {e}"
        test_file = logs_dir / ".test_write"
        try:
            test_file.write_text("test")
            test_file.unlink()
            return True, f"Log directory writable: {logs_dir}"
        except Exception as e:
            return False, f"Log directory not writable: {e}"
    
    def check_context_vault_structure(self) -> Tuple[bool, str]:
        """CHECK 11: Verify Context Vault directory structure. (Article VII)"""
        vault = self.epos_root / "context_vault"
        registry = vault / "registry.json"
        if not registry.exists():
            if self.self_heal:
                # Create minimal registry
                registry.parent.mkdir(parents=True, exist_ok=True)
                registry.write_text(json.dumps({
                    "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII",
                    "vaults": {},
                    "created_by": "epos_doctor_v3.2_self_heal",
                    "created_at": datetime.now().isoformat()
                }, indent=2))
                if not self.silent:
                    print(f"         Self-healed: created registry.json")
            else:
                return False, f"Context Vault registry missing: {registry}"
        try:
            data = json.loads(registry.read_text())
            if "vaults" not in data:
                return False, "Registry malformed (missing 'vaults' key)"
            if "constitutional_authority" not in data:
                return False, "Registry missing constitutional authority"
        except json.JSONDecodeError:
            return False, "Registry corrupted (invalid JSON)"
        
        required_subdirs = ["mission_data", "bi_history", "market_sentiment", "agent_logs",
                           "doctrine", "roles", "governance", "events", "niches"]
        missing = [s for s in required_subdirs if not (vault / s).exists()]
        if missing:
            if self.self_heal:
                for s in missing:
                    (vault / s).mkdir(parents=True, exist_ok=True)
                if not self.silent:
                    print(f"         Self-healed: created {len(missing)} vault subdirectories")
            else:
                return False, f"Missing vault subdirectories: {', '.join(missing)}"
        
        return True, f"Context Vault structure valid ({len(required_subdirs)} subdirs + registry)"
    
    def check_context_vault_compliance(self) -> Tuple[bool, str]:
        """CHECK 12: Check for inline data violations. (Article II Rule 7)"""
        violations = []
        for directory in ["engine", "inbox"]:
            dir_path = self.epos_root / directory
            if not dir_path.exists():
                continue
            for fp in dir_path.glob("*.json"):
                try:
                    content = fp.read_text()
                    estimated_tokens = len(content) / 4
                    if estimated_tokens > 8192:
                        data = json.loads(content)
                        if "context_vault_path" not in data:
                            violations.append(f"{fp.name} ({int(estimated_tokens)} tokens)")
                except Exception:
                    pass
        if violations:
            return False, f"Inline data violations: {'; '.join(violations)}"
        return True, "No inline data >8K tokens detected"
    
    def check_context_handler(self) -> Tuple[bool, str]:
        """CHECK 13: Verify context_handler.py exists. (Article VII)"""
        handler = self.epos_root / "context_handler.py"
        if not handler.exists():
            return False, "context_handler.py missing (required for RLM support)"
        try:
            sys.path.insert(0, str(self.epos_root))
            from context_handler import ContextVault
            return True, "Context Handler functional (ContextVault importable)"
        except ImportError as e:
            return False, f"Context Handler import failed: {e}"
    
    def check_governance_tools(self) -> Tuple[bool, str]:
        """CHECK 14: Verify governance tools exist. Self-heals if possible. (Article III)"""
        required = ["governance_gate.py", "epos_snapshot.py"]
        missing = []
        
        for tool in required:
            if not (self.epos_root / tool).exists():
                # Self-healing: search known locations
                healed = False
                if self.self_heal and tool in self.GOVERNANCE_TOOL_SEARCH_PATHS:
                    for search_path in self.GOVERNANCE_TOOL_SEARCH_PATHS[tool]:
                        candidate = self.epos_root / search_path
                        if candidate.exists():
                            shutil.copy2(candidate, self.epos_root / tool)
                            self._log(f"         Self-healed: copied {search_path} -> {tool}")
                            self._emit_event("system.self_heal.governance_restored", {
                                "tool": tool,
                                "source": search_path,
                                "destination": tool
                            })
                            healed = True
                            break
                if not healed:
                    missing.append(tool)
        
        if missing:
            return False, f"Missing governance tools: {', '.join(missing)} (Article III)"
        return True, f"All governance tools present"
    
    def check_flywheel_metrics(self) -> Tuple[bool, str]:
        """CHECK 15: Verify BI tracking infrastructure."""
        bi_log = self.epos_root / "bi_decision_log.json"
        if not bi_log.exists():
            if self.self_heal:
                bi_log.write_text(json.dumps({
                    "decisions": [],
                    "created_by": "epos_doctor_v3.2_self_heal",
                    "created_at": datetime.now().isoformat()
                }, indent=2))
                if not self.silent:
                    print(f"         Self-healed: created bi_decision_log.json")
            else:
                return False, "BI decision log missing"
        try:
            data = json.loads(bi_log.read_text())
            if "decisions" not in data:
                return False, "BI decision log malformed (missing 'decisions' array)"
        except json.JSONDecodeError:
            return False, "BI decision log corrupted (invalid JSON)"
        return True, "Flywheel metrics tracking operational"
    
    # ════════════════════════════════════════════════════════════
    # SECTION B: NEW v3.2 CHECKS (Article XIV Enforcement)
    # ════════════════════════════════════════════════════════════
    
    def check_doctrine_files(self) -> Tuple[bool, str]:
        """CHECK 16: Verify core doctrine files are present. (Article XIV)"""
        missing = [d for d in self.REQUIRED_DOCTRINE_FILES if not (self.epos_root / d).exists()]
        if missing:
            names = [Path(d).name for d in missing]
            return False, f"Missing doctrine: {', '.join(names)}"
        return True, f"All {len(self.REQUIRED_DOCTRINE_FILES)} core doctrine files present"
    
    def check_file_registry(self) -> Tuple[bool, str]:
        """CHECK 17: Verify file governance registry exists and is valid. (Article XIV.3)"""
        registry_path = self.epos_root / "context_vault" / "governance" / "file_registry.jsonl"
        
        if not registry_path.exists():
            if self.self_heal:
                registry_path.parent.mkdir(parents=True, exist_ok=True)
                registry_path.write_text("")  # Empty but present
                if not self.silent:
                    print(f"         Self-healed: created file_registry.jsonl")
            else:
                return False, f"File registry missing: {registry_path} (Article XIV.3)"
        
        # Count entries
        try:
            content = registry_path.read_text().strip()
            if content:
                lines = content.splitlines()
                valid = 0
                invalid = 0
                for line in lines:
                    try:
                        json.loads(line)
                        valid += 1
                    except json.JSONDecodeError:
                        invalid += 1
                if invalid > 0:
                    return False, f"Registry has {invalid} corrupt entries out of {valid + invalid}"
                return True, f"File registry valid ({valid} entries)"
            else:
                return True, "File registry present (empty — no files triaged yet)"
        except Exception as e:
            return False, f"Cannot read file registry: {e}"
    
    def check_watermark_presence(self) -> Tuple[bool, str]:
        """CHECK 18: Scan production paths for ungoverned files. (Article XIV.2)"""
        ungoverned = []
        
        for governed_path in self.GOVERNED_PATHS:
            gp = self.epos_root / governed_path
            if not gp.exists():
                continue
            
            for fp in gp.rglob("*"):
                if fp.is_dir():
                    continue
                if fp.name.startswith(".") or fp.name == "__init__.py":
                    continue
                if fp.suffix not in (".py", ".json", ".md", ".html"):
                    continue
                
                # Check for watermark
                try:
                    content = fp.read_text(encoding="utf-8", errors="replace")
                    has_watermark = False
                    
                    if fp.suffix == ".py":
                        has_watermark = "EPOS GOVERNANCE WATERMARK" in content
                    elif fp.suffix == ".json":
                        try:
                            data = json.loads(content)
                            has_watermark = "_governance" in data
                        except json.JSONDecodeError:
                            pass
                    elif fp.suffix in (".md", ".html"):
                        has_watermark = ("triage_id:" in content or 
                                        "EPOS GOVERNANCE WATERMARK" in content or
                                        "governance:" in content[:500])
                    
                    if not has_watermark:
                        rel = fp.relative_to(self.epos_root)
                        ungoverned.append(str(rel))
                except Exception:
                    pass
        
        if ungoverned:
            count = len(ungoverned)
            sample = ungoverned[:5]
            extra = f" (+{count - 5} more)" if count > 5 else ""
            return False, f"{count} ungoverned files: {', '.join(sample)}{extra} (Article XIV.2 - ERR-WATERMARK-001)"
        return True, "All files in governed paths have watermarks"
    
    def check_bootstrap_mode(self) -> Tuple[bool, str]:
        """CHECK 19: Monitor bootstrap mode duration. (Article XIV.1.3)"""
        lock_file = self.epos_root / "BOOTSTRAP_MODE.lock"
        
        if not lock_file.exists():
            return True, "Normal operation (no bootstrap mode)"
        
        try:
            lock_data = json.loads(lock_file.read_text())
            activated = datetime.fromisoformat(lock_data.get("activated_at", ""))
            expiration = datetime.fromisoformat(lock_data.get("expires_at", ""))
            now = datetime.now()
            
            if now > expiration:
                if self.self_heal:
                    lock_file.unlink()
                    self._emit_event("bootstrap.expired", {
                        "activated_at": lock_data.get("activated_at"),
                        "expired_at": lock_data.get("expires_at"),
                        "removed_by": "epos_doctor_v3.2_self_heal"
                    })
                    if not self.silent:
                        print(f"         Self-healed: removed expired bootstrap lock")
                    return True, "Bootstrap lock expired and removed"
                return False, f"Bootstrap mode EXPIRED (was {lock_data.get('expires_at')}). Remove lock or run retroactive triage."
            
            hours_active = (now - activated).total_seconds() / 3600
            if hours_active > 4:
                return False, f"Bootstrap mode active {hours_active:.1f}h (max recommended: 4h) — ERR-BOOTSTRAP-001"
            
            return True, f"Bootstrap mode active ({hours_active:.1f}h, expires {expiration.isoformat()})"
        except (json.JSONDecodeError, ValueError) as e:
            return False, f"Bootstrap lock file corrupted: {e}"
    
    def check_duplicate_files(self) -> Tuple[bool, str]:
        """CHECK 20: Detect files existing in both root and engine/. (Article XIV)"""
        duplicates = []
        engine_dir = self.epos_root / "engine"
        
        if not engine_dir.exists():
            return True, "No engine/ directory (skip duplicate check)"
        
        for root_file in self.epos_root.glob("*.py"):
            engine_candidate = engine_dir / root_file.name
            if engine_candidate.exists():
                root_size = root_file.stat().st_size
                engine_size = engine_candidate.stat().st_size
                status = "identical" if root_size == engine_size else "DIVERGED"
                duplicates.append(f"{root_file.name} ({status})")
        
        # Also check engine/enforcement/
        enforcement_dir = engine_dir / "enforcement"
        if enforcement_dir.exists():
            for root_file in self.epos_root.glob("*.py"):
                enf_candidate = enforcement_dir / root_file.name
                if enf_candidate.exists():
                    root_size = root_file.stat().st_size
                    enf_size = enf_candidate.stat().st_size
                    status = "identical" if root_size == enf_size else "DIVERGED"
                    entry = f"{root_file.name} (root vs enforcement/ — {status})"
                    if entry not in duplicates:
                        duplicates.append(entry)
        
        if duplicates:
            return False, f"{len(duplicates)} duplicates: {'; '.join(duplicates)} — ERR-DUPLICATE-001"
        return True, "No duplicate files between root and engine/"
    
    def check_content_lab_health(self) -> Tuple[bool, str]:
        """CHECK 21: Verify C10 Content Lab attachment. (Operational)"""
        reg_file = self.epos_root / "content" / "lab" / "component_registration.json"
        if not reg_file.exists():
            return False, "Content Lab not attached (component_registration.json missing)"
        
        try:
            reg = json.loads(reg_file.read_text())
            status = reg.get("status", "unknown")
            if status != "operational":
                return False, f"Content Lab status: {status} (expected: operational)"
            return True, f"Content Lab: {reg.get('name', 'C10')} — {status}"
        except (json.JSONDecodeError, Exception) as e:
            return False, f"Content Lab registration corrupted: {e}"
    
    def check_unified_launcher(self) -> Tuple[bool, str]:
        """CHECK 22: Verify unified launcher exists. (Operational)"""
        launcher = self.epos_root / "epos_start.ps1"
        if not launcher.exists():
            return False, "Unified launcher (epos_start.ps1) not found"
        return True, f"Unified launcher present ({launcher.stat().st_size} bytes)"
    
    def check_quarantine_population(self) -> Tuple[bool, str]:
        """CHECK 23: Report quarantine status. (Article XIV.1.2)"""
        quarantine = self.epos_root / "quarantine"
        if not quarantine.exists():
            return True, "Quarantine directory absent (no quarantined files)"
        
        items = list(quarantine.rglob("*"))
        files = [i for i in items if i.is_file()]
        if files:
            return False, f"{len(files)} files in quarantine awaiting triage"
        return True, "Quarantine empty"
    
    # ════════════════════════════════════════════════════════════
    # EVENT BUS INTEGRATION
    # ════════════════════════════════════════════════════════════
    
    def _emit_event(self, event_type: str, payload: dict):
        """Write event to JSONL and publish via EPOSEventBus."""
        events_dir = self.epos_root / "context_vault" / "events"
        events_dir.mkdir(parents=True, exist_ok=True)

        event = {
            "event_type": event_type,
            "source": f"epos_doctor_v{self.VERSION}",
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }

        log_path = events_dir / "doctor_events.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        # Also publish via event bus (sovereign — degrades gracefully)
        try:
            from epos_event_bus import EPOSEventBus
            EPOSEventBus().publish(event_type, payload,
                                   source_module=f"epos_doctor_v{self.VERSION}")
        except Exception:
            pass  # Bus unavailable — standalone mode
    
    # ════════════════════════════════════════════════════════════
    # SECTION C: ORGANISM HEALTH CHECKS (v3.3)
    # ════════════════════════════════════════════════════════════

    def check_idea_log(self) -> Tuple[bool, str]:
        """CHECK C1: Verify Idea Log module is importable and operational."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from idea_log import IdeaLog
            log = IdeaLog()
            stats = log.stats()
            return True, f"IdeaLog operational — {stats['total']} ideas captured"
        except Exception as e:
            return False, f"IdeaLog import failed: {e}"

    def check_friday_anchors(self) -> Tuple[bool, str]:
        """CHECK C2: Verify Friday Daily Anchors system."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from friday_daily_anchors import FridayDailyAnchors
            fda = FridayDailyAnchors()
            streak = fda.get_streak()
            return True, f"Anchors operational — {streak['total_anchors']} executed"
        except Exception as e:
            return False, f"FridayDailyAnchors import failed: {e}"

    def check_content_signal_loop(self) -> Tuple[bool, str]:
        """CHECK C3: Verify Content Signal Loop."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from content_signal_loop import ContentSignalLoop
            loop = ContentSignalLoop()
            summary = loop.get_signal_summary()
            return True, f"Signal loop operational — {summary['total']} signals today"
        except Exception as e:
            return False, f"ContentSignalLoop import failed: {e}"

    def check_lead_scoring(self) -> Tuple[bool, str]:
        """CHECK C4: Verify Lead Scoring Engine."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from lead_scoring import LeadScoringEngine
            engine = LeadScoringEngine()
            summary = engine.get_score_summary()
            return True, f"Lead scoring operational — {summary['total']} scored"
        except Exception as e:
            return False, f"LeadScoringEngine import failed: {e}"

    def check_rs1_research_brief(self) -> Tuple[bool, str]:
        """CHECK C5: Verify RS1 Research Brief Generator."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from rs1_research_brief import RS1ResearchBrief
            gen = RS1ResearchBrief()
            briefs = gen.list_briefs()
            return True, f"RS1 briefs operational — {len(briefs)} briefs generated"
        except Exception as e:
            return False, f"RS1ResearchBrief import failed: {e}"

    def check_sheets_sync(self) -> Tuple[bool, str]:
        """CHECK C6: Verify Google Sheets Sync Layer."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from sheets_sync import SheetsSync
            sync = SheetsSync()
            configured = sync.is_configured()
            status = "configured" if configured else "CSV fallback (configure API for full sync)"
            return True, f"SheetsSync importable — {status}"
        except Exception as e:
            return False, f"SheetsSync import failed: {e}"

    def check_friday_mandate(self) -> Tuple[bool, str]:
        """CHECK C7: Verify Friday Constitutional Mandate v2.1 exists."""
        mandate_path = self.epos_root / "context_vault" / "doctrine" / "FRIDAY_CONSTITUTIONAL_MANDATE_v2.1.md"
        if mandate_path.exists():
            size = mandate_path.stat().st_size
            return True, f"Friday Mandate v2.1 present ({size} bytes)"
        # Check for v2.0 fallback
        v2_path = self.epos_root / "context_vault" / "doctrine" / "FRIDAY_CONSTITUTIONAL_MANDATE_v2.md"
        if v2_path.exists():
            return True, "Friday Mandate v2.0 present (v2.1 upgrade recommended)"
        return False, "Friday Constitutional Mandate not found"

    def check_event_bus_health(self) -> Tuple[bool, str]:
        """CHECK C8: Verify Event Bus is operational with recent events."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from epos_event_bus import EPOSEventBus
            bus = EPOSEventBus()
            count = bus.event_count()
            if count == 0:
                return False, "Event bus has 0 events — may indicate initialization issue"
            return True, f"Event bus operational — {count} events"
        except Exception as e:
            return False, f"Event bus check failed: {e}"

    def check_lifeos_sovereignty(self) -> Tuple[bool, str]:
        """CHECK C9: Verify LifeOS Sovereignty layer."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from lifeos_sovereignty import LifeOSSovereignty
            sov = LifeOSSovereignty()
            surface = sov.get_pm_surface()
            energy = surface.get("energy", 0)
            goals = surface.get("active_goals", 0)
            return True, f"LifeOS operational — energy {energy}/10, {goals} goals"
        except Exception as e:
            return False, f"LifeOS import failed: {e}"

    def check_ttlg_props(self) -> Tuple[bool, str]:
        """CHECK D1: Verify TTLG Props loader — all presets valid."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from ttlg.props.schema import list_presets, load_props
            presets = list_presets()
            if not presets:
                return False, "No TTLG presets found"
            for name in presets:
                load_props(name)
            return True, f"TTLG Props: {len(presets)} presets valid"
        except Exception as e:
            return False, f"TTLG Props failed: {str(e)[:80]}"

    def check_self_healing(self) -> Tuple[bool, str]:
        """CHECK D2: Verify Self-Healing Engine importable and vault exists."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from ttlg.self_healing_scout import SelfHealingScout
            from ttlg.remediation_runbook import RemediationRunbook
            # Fast check: verify classes instantiate and vault exists
            scout = SelfHealingScout()
            runbook = RemediationRunbook()
            vault = self.epos_root / "context_vault" / "self_healing"
            if not vault.exists():
                return False, "Self-Healing vault missing"
            return True, f"Self-Healing: scout + runbook importable, vault present"
        except Exception as e:
            return False, f"Self-Healing failed: {str(e)[:80]}"

    def check_aar_freshness(self) -> Tuple[bool, str]:
        """CHECK D3: Verify AAR freshness relative to code changes."""
        try:
            aar_dir = self.epos_root / "context_vault" / "aar"
            if not aar_dir.exists():
                return False, "No AAR directory found"
            aars = sorted(aar_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
            if not aars:
                return False, "No AAR files found — constitutional violation"
            latest_aar_time = aars[0].stat().st_mtime
            # Check most recent code change
            latest_code = 0
            for ext in ("*.py",):
                for f in self.epos_root.glob(ext):
                    if f.stat().st_mtime > latest_code:
                        latest_code = f.stat().st_mtime
            if latest_code > 0 and (latest_code - latest_aar_time) > 172800:  # 48 hours
                return False, f"AAR stale: code changed {(latest_code - latest_aar_time)/3600:.0f}h after last AAR"
            return True, f"AAR fresh: {aars[0].name}"
        except Exception as e:
            return False, f"AAR check failed: {str(e)[:80]}"

    def check_agent_zero(self) -> Tuple[bool, str]:
        """CHECK D6: Verify Agent Zero container responding."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from nodes.agent_zero_node import AgentZeroNode
            node = AgentZeroNode()
            health = node.health_check()
            if health["status"] == "operational":
                return True, f"Agent Zero: operational at {health['url']}"
            else:
                return False, f"Agent Zero: {health['status']} — {health.get('reason', '?')[:60]}"
        except Exception as e:
            return False, f"Agent Zero check failed: {str(e)[:80]}"

    def check_browser_use(self) -> Tuple[bool, str]:
        """CHECK D5: Verify BrowserUse node operational."""
        try:
            sys.path.insert(0, str(self.epos_root))
            from nodes.browser_use_node import BrowserUseNode
            node = BrowserUseNode()
            health = node.health_check()
            if health["status"] == "operational":
                backends = health.get("llm_backends", [])
                return True, f"BrowserUse: operational ({', '.join(backends)})"
            else:
                return False, f"BrowserUse: {health['status']} — {health.get('reason', '?')[:60]}"
        except Exception as e:
            return False, f"BrowserUse check failed: {str(e)[:80]}"

    def check_ninth_order(self) -> Tuple[bool, str]:
        """CHECK D4: Verify 9th Order gap tracker initialized."""
        try:
            tracker = self.epos_root / "context_vault" / "doctrine" / "ninth_order_gaps.jsonl"
            if not tracker.exists():
                return False, "9th Order gap tracker not found"
            return True, f"9th Order tracker: {tracker.stat().st_size} bytes"
        except Exception as e:
            return False, f"9th Order check failed: {str(e)[:80]}"

    # ════════════════════════════════════════════════════════════
    # MAIN EXECUTION
    # ════════════════════════════════════════════════════════════

    def run_all_checks(self) -> bool:
        """Run all validation checks (v3.1 + v3.2 Article XIV)."""
        if not self.silent:
            print()
            print("=" * 70)
            print(f"  EPOS ENVIRONMENT DIAGNOSTIC v{self.VERSION}")
            print(f"  Constitutional Authority: EPOS_CONSTITUTION_{self.CONSTITUTIONAL_VERSION}")
            if self.self_heal:
                print("  Mode: SELF-HEALING ACTIVE")
            print("=" * 70)
            print()
            print("  --- Section A: Core Environment (v3.1) ---")
            print()
        
        # Section A: Original v3.1 checks
        self._check("Python Version (Article II Rule 3)", self.check_python_version, critical=True)
        self._check("EPOS Root (Article II Rule 1)", self.check_epos_root, critical=True)
        self._check("Constitutional Documents (Article I)", self.check_constitutional_docs, critical=True)
        self._check("Required Directories (Article VII)", self.check_required_directories, critical=True)
        self._check("Agent Zero Path", self.check_agent_zero)
        self._check("Ollama Service", self.check_ollama)
        self._check(".env Loaded (Article II Rule 6)", self.check_env_loaded)
        self._check("Dependencies Installed", self.check_dependencies)
        self._check("Port Availability", self.check_port_availability)
        self._check("Log Directory Writable (Article II Rule 2)", self.check_logs_writable)
        self._check("Context Vault Structure (Article VII)", self.check_context_vault_structure, critical=True)
        self._check("Context Vault Compliance (Article II Rule 7)", self.check_context_vault_compliance)
        self._check("Context Handler Available (Article VII)", self.check_context_handler)
        self._check("Governance Tools Present (Article III)", self.check_governance_tools, critical=True)
        self._check("Flywheel Metrics Tracking", self.check_flywheel_metrics)
        
        if not self.silent:
            print()
            print("  --- Section B: File Governance (v3.2 — Article XIV) ---")
            print()
        
        # Section B: New v3.2 Article XIV checks
        self._check("Doctrine Files Present (Article XIV)", self.check_doctrine_files, critical=True)
        self._check("File Governance Registry (Article XIV.3)", self.check_file_registry)
        self._check("Watermark Presence (Article XIV.2)", self.check_watermark_presence)
        self._check("Bootstrap Mode (Article XIV.1.3)", self.check_bootstrap_mode)
        self._check("Duplicate File Detection (Article XIV)", self.check_duplicate_files)
        self._check("Content Lab Health (C10)", self.check_content_lab_health)
        self._check("Unified Launcher Present", self.check_unified_launcher)
        self._check("Quarantine Status (Article XIV.1.2)", self.check_quarantine_population, info_only=True)

        if not self.silent:
            print()
            print("  --- Section C: EPOS Organism Health (v3.3) ---")
            print()

        # Section C: New organism-level checks
        self._check("Idea Log Operational", self.check_idea_log)
        self._check("Friday Daily Anchors", self.check_friday_anchors)
        self._check("Content Signal Loop", self.check_content_signal_loop)
        self._check("Lead Scoring Engine", self.check_lead_scoring)
        self._check("RS1 Research Brief Generator", self.check_rs1_research_brief)
        self._check("Google Sheets Sync Layer", self.check_sheets_sync)
        self._check("Friday Constitution v2.1", self.check_friday_mandate)
        self._check("Event Bus Health", self.check_event_bus_health)
        self._check("LifeOS Sovereignty", self.check_lifeos_sovereignty)

        if not self.silent:
            print()
            print("  --- Section D: TTLG v2 + Self-Healing (v3.4) ---")
            print()

        self._check("TTLG Props Loader", self.check_ttlg_props)
        self._check("Self-Healing Engine", self.check_self_healing)
        self._check("AAR Freshness", self.check_aar_freshness)
        self._check("BrowserUse Node", self.check_browser_use)
        self._check("Agent Zero Container", self.check_agent_zero)
        self._check("9th Order Gap Tracker", self.check_ninth_order)

        # Summary
        total = self.checks_passed + self.checks_warned + self.checks_failed
        if not self.silent:
            print()
            print("=" * 70)
            print(f"  Passed:   {self.checks_passed}")
            print(f"  Warnings: {self.checks_warned}")
            print(f"  Failed:   {self.checks_failed}")
            if self.checks_info > 0:
                print(f"  Info:     {self.checks_info}")
            if self.healed:
                print(f"  Healed:   {len(self.healed)}")
            print(f"  Total:    {total} checks")
            print("=" * 70)
            print()
        
        if self.checks_failed == 0:
            if not self.silent:
                print("  ENVIRONMENT VALIDATED — Ready for operations")
                print(f"  Constitutional Compliance: v{self.VERSION} CONFIRMED")
                print(f"  Article XIV Governance: ENFORCED")
                if self.healed:
                    print(f"  Self-Healing Actions: {len(self.healed)} repairs applied")
                print()
            
            self._emit_event("doctor.sweep.passed", {
                "version": self.VERSION,
                "passed": self.checks_passed,
                "warnings": self.checks_warned,
                "healed": len(self.healed)
            })
            return True
        else:
            if not self.silent:
                print("  ENVIRONMENT ISSUES DETECTED — Fix failures before proceeding")
                print()
                print("  Critical Failures:")
                for f in self.failures:
                    print(f"    * {f['check']}: {f['details']}")
                if self.warnings:
                    print()
                    print("  Warnings:")
                    for w in self.warnings:
                        print(f"    * {w['check']}: {w['details']}")
                if self.self_heal and not self.healed:
                    print()
                    print("  Self-healing found no automatic fixes for remaining issues.")
                print()
            
            self._emit_event("doctor.sweep.failed", {
                "version": self.VERSION,
                "passed": self.checks_passed,
                "failed": self.checks_failed,
                "warnings": self.checks_warned,
                "failure_details": self.failures
            })
            return False
    
    def run_governance_checks(self) -> bool:
        """Run only Article XIV governance checks."""
        if not self.silent:
            print()
            print("=" * 70)
            print(f"  EPOS GOVERNANCE AUDIT (Article XIV) v{self.VERSION}")
            print("=" * 70)
            print()
        
        self._check("Doctrine Files Present", self.check_doctrine_files, critical=True)
        self._check("File Governance Registry", self.check_file_registry)
        self._check("Watermark Presence", self.check_watermark_presence)
        self._check("Bootstrap Mode", self.check_bootstrap_mode)
        self._check("Duplicate File Detection", self.check_duplicate_files)
        self._check("Quarantine Status", self.check_quarantine_population, info_only=True)
        
        if not self.silent:
            print()
            print(f"  Passed: {self.checks_passed} | Warned: {self.checks_warned} | Failed: {self.checks_failed}")
            print()
        
        return self.checks_failed == 0
    
    def get_report_json(self) -> str:
        """Get validation report as JSON."""
        total = self.checks_passed + self.checks_failed + self.checks_warned
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "doctor_version": self.VERSION,
            "constitutional_version": self.CONSTITUTIONAL_VERSION,
            "checks_passed": self.checks_passed,
            "checks_warned": self.checks_warned,
            "checks_failed": self.checks_failed,
            "checks_info": self.checks_info,
            "total_checks": total,
            "success": self.checks_failed == 0,
            "compliance_rate": round(self.checks_passed / total, 3) if total > 0 else 0,
            "failures": self.failures,
            "warnings": self.warnings,
            "info": self.info,
            "healed": self.healed
        }, indent=2)


# ════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ════════════════════════════════════════════════════════════════

def main():
    """Main CLI entrypoint."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description=f"EPOS Environment Validator v{EPOSDoctor.VERSION}"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output for automation")
    parser.add_argument("--check-constitution", action="store_true", help="Only check constitutional docs")
    parser.add_argument("--check-context", action="store_true", help="Only check Context Vault")
    parser.add_argument("--check-governance", action="store_true", help="Only check Article XIV governance")
    parser.add_argument("--cron", action="store_true", help="Daily health check mode (brief output)")
    parser.add_argument("--self-heal", action="store_true", help="Attempt auto-repair of known issues")
    
    args = parser.parse_args()
    
    if args.cron:
        args.verbose = False
    
    doctor = EPOSDoctor(
        verbose=args.verbose,
        silent=args.cron,
        self_heal=args.self_heal
    )
    
    if args.check_constitution:
        success, details = doctor.check_constitutional_docs()
        print(f"{'PASS' if success else 'FAIL'}: {details}")
        sys.exit(0 if success else 1)
    
    if args.check_context:
        print("Context Vault Validation:")
        s1, d1 = doctor.check_context_vault_structure()
        print(f"  Structure:  {'PASS' if s1 else 'FAIL'} {d1}")
        s2, d2 = doctor.check_context_vault_compliance()
        print(f"  Compliance: {'PASS' if s2 else 'FAIL'} {d2}")
        s3, d3 = doctor.check_context_handler()
        print(f"  Handler:    {'PASS' if s3 else 'FAIL'} {d3}")
        sys.exit(0 if (s1 and s2 and s3) else 1)
    
    if args.check_governance:
        success = doctor.run_governance_checks()
        if args.json:
            print(doctor.get_report_json())
        sys.exit(0 if success else 1)
    
    # Run all checks
    success = doctor.run_all_checks()
    
    if args.json:
        print(doctor.get_report_json())
    
    if args.cron and not success:
        print(f"EPOS Health: DEGRADED ({doctor.checks_failed} failures, {doctor.checks_warned} warnings)")
    
    if success:
        sys.exit(0)
    elif any(f.get("severity") == "critical" for f in doctor.failures):
        sys.exit(2)
    else:
        sys.exit(1)


def _self_test():
    """Assertion-based self-test for sovereignty certification."""
    passed = 0

    # Test 1: Doctor instantiates
    doctor = EPOSDoctor(verbose=False, silent=True)
    assert hasattr(doctor, "run_all_checks"), "Missing run_all_checks"
    assert hasattr(doctor, "get_report_json"), "Missing get_report_json"
    passed += 1

    # Test 2: Run all checks — must return bool
    result = doctor.run_all_checks()
    assert isinstance(result, bool), f"run_all_checks should return bool, got {type(result)}"
    passed += 1

    # Test 3: Check counts are integers and pass count > 0
    assert isinstance(doctor.checks_passed, int), "checks_passed should be int"
    assert doctor.checks_passed > 0, "Should have at least 1 passing check"
    passed += 1

    # Test 4: JSON report is valid
    report_json = doctor.get_report_json()
    report = json.loads(report_json)
    assert "checks_passed" in report, "Report missing checks_passed"
    assert "doctor_version" in report, "Report missing doctor_version"
    passed += 1

    # Test 5: Event was emitted (JSONL file should exist)
    events_dir = doctor.epos_root / "context_vault" / "events"
    journal = events_dir / "doctor_events.jsonl"
    assert journal.exists(), "Doctor event journal should exist after run"
    passed += 1

    print(f"PASS: epos_doctor ({passed} assertions)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test-only":
        _self_test()
    else:
        main()
