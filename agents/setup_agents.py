# File: /mnt/c/Users/Jamie/workspace/epos_mcp/agents/setup_agents.py

"""
EPOS Agent System Setup Script
==============================

This script sets up the agent system by:
1. Creating required directory structure
2. Initializing BI decision log
3. Validating environment
4. Running initial health check

Usage:
    python setup_agents.py              # Full setup
    python setup_agents.py --validate   # Validate only
    python setup_agents.py --init-bi    # Initialize BI log only
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Ensure Python 3.11+
if sys.version_info[:2] < (3, 11):
    print("❌ CRITICAL: Python 3.11+ required")
    print(f"   Current: Python {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(2)


def setup_directories(epos_root: Path) -> bool:
    """Create required directory structure."""
    print("\n📁 Setting up directories...")
    
    directories = [
        "inbox",
        "engine",
        "rejected/receipts",
        "ops/logs/arbiter",
        "ops/logs/content_lab",
        "ops/flywheel_reports",
        "ops/vault_reports",
        "market",
        "context_vault/mission_data",
        "context_vault/bi_history",
        "context_vault/market_sentiment",
        "context_vault/agent_logs",
        "context_vault/archive",
        "nodes",
        "agents",
        "inbox/amendments"
    ]
    
    created = 0
    for dir_path in directories:
        full_path = epos_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {dir_path}")
            created += 1
        else:
            print(f"   ⏭️  Exists: {dir_path}")
    
    print(f"\n   Created {created} new directories")
    return True


def init_bi_log(epos_root: Path) -> bool:
    """Initialize BI decision log."""
    print("\n📊 Initializing BI decision log...")
    
    bi_log_path = epos_root / "bi_decision_log.json"
    
    if bi_log_path.exists():
        print(f"   ⏭️  BI log exists: {bi_log_path}")
        return True
    
    bi_data = {
        "created": datetime.now().isoformat(),
        "version": "1.0",
        "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md",
        "decisions": []
    }
    
    bi_log_path.write_text(json.dumps(bi_data, indent=2))
    print(f"   ✅ Created: {bi_log_path}")
    
    return True


def init_vault_registry(epos_root: Path) -> bool:
    """Initialize Context Vault registry."""
    print("\n📚 Initializing Context Vault registry...")
    
    registry_path = epos_root / "context_vault" / "registry.json"
    
    if registry_path.exists():
        print(f"   ⏭️  Registry exists: {registry_path}")
        return True
    
    registry = {
        "vaults": {},
        "created": datetime.now().isoformat(),
        "version": "1.0",
        "constitutional_authority": "EPOS_CONSTITUTION_v3.1.md Article VII"
    }
    
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2))
    print(f"   ✅ Created: {registry_path}")
    
    return True


def validate_environment(epos_root: Path) -> bool:
    """Validate environment requirements."""
    print("\n🔍 Validating environment...")
    
    issues = []
    
    # Check Python version
    if sys.version_info[:2] >= (3, 11):
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.11+)")
        issues.append("Python version")
    
    # Check EPOS root
    if epos_root.exists():
        print(f"   ✅ EPOS root: {epos_root}")
    else:
        print(f"   ❌ EPOS root not found: {epos_root}")
        issues.append("EPOS root")
    
    # Check Agent Zero
    agent_zero_path = Path(os.getenv("AGENT_ZERO_PATH", str(Path(__file__).resolve().parent.parent.parent / "agent-zero")))
    if agent_zero_path.exists():
        print(f"   ✅ Agent Zero: {agent_zero_path}")
    else:
        print(f"   ⚠️  Agent Zero not found: {agent_zero_path}")
        # Not critical - agents can work without Agent Zero
    
    # Check dependencies
    deps = ["fastapi", "uvicorn", "pydantic"]
    for dep in deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ⚠️  {dep} not installed")
    
    # Check dotenv
    try:
        from dotenv import load_dotenv
        print(f"   ✅ python-dotenv")
    except ImportError:
        print(f"   ⚠️  python-dotenv not installed")
    
    if issues:
        print(f"\n   ❌ {len(issues)} critical issues found")
        return False
    
    print(f"\n   ✅ Environment validated")
    return True


def copy_agents(epos_root: Path, source_dir: Path) -> bool:
    """Copy agent files to EPOS agents directory."""
    print("\n📋 Installing agent files...")
    
    agents_dir = epos_root / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    agent_files = [
        "constitutional_arbiter.py",
        "context_librarian.py",
        "flywheel_analyst.py",
        "agent_orchestrator.py",
        "agent_registry.json"
    ]
    
    copied = 0
    for filename in agent_files:
        source = source_dir / filename
        dest = agents_dir / filename
        
        if source.exists():
            import shutil
            shutil.copy2(source, dest)
            print(f"   ✅ Installed: {filename}")
            copied += 1
        else:
            print(f"   ⚠️  Source not found: {filename}")
    
    print(f"\n   Installed {copied} agent files")
    return copied > 0


def run_health_check(epos_root: Path) -> bool:
    """Run initial health check."""
    print("\n🏥 Running health check...")
    
    # Add agents dir to path
    sys.path.insert(0, str(epos_root / "agents"))
    
    try:
        from agent_orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(epos_root, verbose=False)
        health = orchestrator.health_check()
        
        print(f"   Orchestrator: {health['orchestrator']}")
        
        for agent, status in health['agents'].items():
            if isinstance(status, dict):
                emoji = "✅" if status.get("status") == "healthy" else "⚠️"
                print(f"   {emoji} {agent}: {status.get('status', 'unknown')}")
            else:
                emoji = "✅" if status == "healthy" else "⚠️"
                print(f"   {emoji} {agent}: {status}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False


def main():
    """Main setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOS Agent System Setup")
    parser.add_argument("--validate", action="store_true", help="Validate only")
    parser.add_argument("--init-bi", action="store_true", help="Initialize BI log only")
    parser.add_argument("--epos-root", type=str, help="EPOS root directory")
    
    args = parser.parse_args()
    
    # Determine EPOS root
    epos_root = Path(args.epos_root) if args.epos_root else Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent)))
    
    print("=" * 60)
    print("🚀 EPOS AGENT SYSTEM SETUP")
    print("=" * 60)
    print(f"\nEPOS Root: {epos_root}")
    
    if args.validate:
        success = validate_environment(epos_root)
        sys.exit(0 if success else 1)
    
    if args.init_bi:
        success = init_bi_log(epos_root)
        sys.exit(0 if success else 1)
    
    # Full setup
    steps = [
        ("Directories", lambda: setup_directories(epos_root)),
        ("BI Log", lambda: init_bi_log(epos_root)),
        ("Vault Registry", lambda: init_vault_registry(epos_root)),
        ("Environment", lambda: validate_environment(epos_root)),
    ]
    
    # Check if we should copy agents (when running from download location)
    current_dir = Path(__file__).parent
    if (current_dir / "constitutional_arbiter.py").exists():
        steps.append(("Agents", lambda: copy_agents(epos_root, current_dir)))
    
    steps.append(("Health Check", lambda: run_health_check(epos_root)))
    
    results = {}
    for name, func in steps:
        try:
            results[name] = func()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SETUP SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        emoji = "✅" if success else "❌"
        print(f"   {emoji} {name}")
    
    print(f"\n   {passed}/{total} steps completed successfully")
    
    if passed == total:
        print("\n🎉 SETUP COMPLETE!")
        print("\nNext steps:")
        print("   1. Run: python agents/agent_orchestrator.py --health")
        print("   2. Run: python agents/constitutional_arbiter.py --triage-inbox")
        print("   3. Run: python agents/flywheel_analyst.py --flywheels")
    else:
        print("\n⚠️  Some steps failed. Please review and retry.")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
