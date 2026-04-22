#!/usr/bin/env python3
# File: /mnt/c/Users/Jamie/workspace/epos_mcp/tools/governance_gate_audit.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
r"""
File: /mnt/c/Users/Jamie/workspace/epos_mcp/tools/governance_gate_audit.py

GOVERNANCE GATE AUDIT SCRIPT (FIXED)
"""

import os, sys, re, json
from pathlib import Path
from datetime import datetime
from typing import List

CRITICAL_CHECKS = [
    ("alignment_assertion", r'ALIGNMENT ASSERTION \(IPP Step 6\)'),
    ("step_1_touchpoints", r'STEP 1.*?TOUCHPOINTS'),
    ("step_2_failure_chains", r'STEP 2.*?FAILURE'),
    ("step_3_dependencies", r'STEP 3.*?DEPENDENCIES'),
    ("step_4_failure_scenarios", r'STEP 4.*?FAILURE'),
    ("step_5_constitutional", r'STEP 5.*?CONSTITUTIONAL'),
    ("step_6_proof", r'STEP 6.*?PROOF'),
    ("path_clarity", r'File: C:\\Users\\Jamie\\workspace'),
]

class GovernanceGateValidator:
    def __init__(self, files_to_validate: List[Path]):
        self.files = files_to_validate
        self.audit_log = Path("logs/governance_gate_audit.jsonl")
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
        self.all_passed = True
    
    def validate_all(self) -> bool:
        if not self.files:
            self._log_audit({"action": "no_files_to_validate", "timestamp": datetime.utcnow().isoformat() + "Z", "status": "PASS"})
            return True
        
        for file_path in self.files:
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                self.all_passed = False
                continue
            
            with open(file_path, "r") as f:
                content = f.read()
            
            file_passed = self._validate_file(file_path, content)
            if not file_passed:
                self.all_passed = False
        
        return self.all_passed
    
    def _validate_file(self, file_path: Path, content: str) -> bool:
        print(f"\n🔍 Validating: {file_path}")
        passed = True
        failures = []
        
        for check_name, pattern in CRITICAL_CHECKS:
            if not re.search(pattern, content, re.DOTALL):
                msg = f"❌ CRITICAL: Missing '{check_name}'"
                print(msg)
                failures.append(msg)
                passed = False
        
        if "litellm.completion" in content or "litellm.chat_completion" in content:
            if "from tools.litellm_client import run_model" not in content:
                msg = "❌ CRITICAL: Direct litellm call. Use tools.litellm_client.run_model()"
                print(msg)
                failures.append(msg)
                passed = False
        
        if passed:
            print(f"✅ PASSED: All Article XIV checks")
            self._log_audit({"file": str(file_path), "action": "validation_passed", "timestamp": datetime.utcnow().isoformat() + "Z", "status": "APPROVED"})
        else:
            self._log_audit({"file": str(file_path), "action": "validation_failed", "failures": failures, "timestamp": datetime.utcnow().isoformat() + "Z", "status": "REJECTED"})
        
        return passed
    
    def _log_audit(self, entry: dict):
        with open(self.audit_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/governance_gate_audit.py <file1> [file2] ...")
        sys.exit(1)
    files_to_validate = [Path(f) for f in sys.argv[1:]]
    print("=" * 80)
    print("🏛️  GOVERNANCE GATE AUDIT (Article XIV Enforcement)")
    print("=" * 80)
    validator = GovernanceGateValidator(files_to_validate)
    all_passed = validator.validate_all()
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ GOVERNANCE GATE RESULT: ALL FILES APPROVED")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ GOVERNANCE GATE RESULT: SUBMISSION REJECTED")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()
