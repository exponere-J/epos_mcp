# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/engine\roles\arbiter.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: C:\Users\Jamie\workspace\epos_mcp\engine\roles\arbiter.py
"""
Constitutional Arbiter (Agent Alpha)
Enforces EPOS Constitution v3.1 on all code changes.

Authority: Article II (Path Discipline), Article VII (Context Governance)
Monetization: $297/mo per repository (Governance-as-a-Service)
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Path setup
EPOS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(EPOS_ROOT / "engine"))

from governance_gate import GovernanceGate
from epos_doctor import EPOSDoctor


class ConstitutionalArbiter:
    """
    Agent Alpha: Constitutional enforcement officer.
    
    Responsibilities:
    - Pre-flight PR scans
    - Merge gate enforcement
    - Sprint boundary audits
    - Compliance scoring
    """
    
    def __init__(self):
        self.gate = GovernanceGate(verbose=True)
        self.doctor = EPOSDoctor(silent=True)
        self.logs_dir = EPOS_ROOT / "ops" / "logs" / "arbiter"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def scan_pull_request(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow 1: Pre-flight PR scan (dry-run mode).
        
        Args:
            pr_data: {
                "pr_id": str,
                "changed_files": [str],
                "branch": str
            }
        
        Returns:
            {
                "status": "pass" | "fail",
                "compliance_score": int,
                "violations": [{"file": str, "errors": [str]}],
                "log_path": str
            }
        """
        pr_id = pr_data.get("pr_id", "unknown")
        changed_files = pr_data.get("changed_files", [])
        
        log_file = self.logs_dir / f"pr_{pr_id}_{datetime.now():%Y%m%d_%H%M%S}.log"
        
        # Environment check
        if not self.doctor.run_all_checks():
            return {
                "status": "fail",
                "compliance_score": 0,
                "violations": [{"file": "environment", "errors": ["Environment not aligned"]}],
                "log_path": str(log_file)
            }
        
        # Scan each changed file
        violations = []
        total_files = len(changed_files)
        passed_files = 0
        
        for file_path in changed_files:
            file = EPOS_ROOT / file_path
            if not file.exists() or file.suffix != ".py":
                continue
            
            audit = self.gate.audit_file(file)
            if audit["status"] == "rejected":
                violations.append({
                    "file": file_path,
                    "errors": [self.gate.VIOLATIONS[v]["title"] for v in audit["violations"]]
                })
            else:
                passed_files += 1
        
        compliance_score = int((passed_files / total_files * 100)) if total_files > 0 else 100
        
        result = {
            "status": "pass" if len(violations) == 0 else "fail",
            "compliance_score": compliance_score,
            "violations": violations,
            "log_path": str(log_file)
        }
        
        # Write log
        log_file.write_text(f"PR Scan {pr_id}\n{'-'*40}\n{result}")
        
        return result
    
    def run_merge_gate(self, merge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow 2: Merge gate (active mode).
        Rejects non-compliant code, promotes compliant code to /engine.
        
        Args:
            merge_data: {
                "pr_id": str,
                "files_to_merge": [str]
            }
        
        Returns:
            {
                "status": "merged" | "blocked",
                "promoted": [str],
                "rejected": [str],
                "receipts": [str]
            }
        """
        # Re-scan in active mode
        self.gate.dry_run = False
        self.gate.process_inbox()  # Processes all files in inbox
        
        return {
            "status": "merged" if len(self.gate.rejected) == 0 else "blocked",
            "promoted": [str(p[1]) for p in self.gate.promoted],
            "rejected": [str(r[1]) for r in self.gate.rejected],
            "receipts": [str(r[2]) for r in self.gate.rejected]
        }
    
    def audit_engine(self) -> Dict[str, Any]:
        """
        Workflow 3: Sprint boundary audit.
        Scans entire /engine directory for lingering violations.
        
        Returns:
            {
                "status": "clean" | "violations_found",
                "governance_score": int,
                "files_audited": int,
                "violations": [{"file": str, "errors": [str]}]
            }
        """
        engine_dir = EPOS_ROOT / "engine"
        violations = []
        files_audited = 0
        passed = 0
        
        for py_file in engine_dir.rglob("*.py"):
            files_audited += 1
            audit = self.gate.audit_file(py_file)
            
            if audit["status"] == "rejected":
                violations.append({
                    "file": str(py_file.relative_to(EPOS_ROOT)),
                    "errors": [self.gate.VIOLATIONS[v]["title"] for v in audit["violations"]]
                })
            else:
                passed += 1
        
        score = int((passed / files_audited * 100)) if files_audited > 0 else 100
        
        # Log for Flywheel Analyst
        audit_log = self.logs_dir / f"sprint_audit_{datetime.now():%Y%m%d}.json"
        import json
        audit_log.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "governance_score": score,
            "files_audited": files_audited,
            "violations": violations
        }, indent=2))
        
        return {
            "status": "clean" if len(violations) == 0 else "violations_found",
            "governance_score": score,
            "files_audited": files_audited,
            "violations": violations
        }


if __name__ == "__main__":
    # Test mode
    arbiter = ConstitutionalArbiter()
    result = arbiter.audit_engine()
    print(f"Engine Audit: {result['governance_score']}% compliant")
