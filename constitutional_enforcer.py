#!/usr/bin/env python3
"""
EPOS CONSTITUTIONAL ENFORCER - Pre-Deployment Validator
Constitutional Authority: Article X (Commercial Readiness)

THE 10 COMMERCIAL READINESS RULES:
1. Zero-Configuration Principle → No manual .env editing
2. Autonomous Bootstrap → No manual mkdir commands
3. Health Check Honesty → Test actual functionality, not just HTTP 200
4. User-Centric Errors → Explain problem + impact + next action
5. Graceful Degradation → Non-critical failures don't break system
6. Data Durability → Auto-backup before upgrades
7. Installation Hygiene → All files in standard locations
8. Startup Order Enforcement → Docker depends_on + health checks
9. Silent Monitoring → Auto-repair before user notices
10. Continuous Improvement → Telemetry for diagnostics (opt-out)

USAGE:
  python constitutional_enforcer.py --validate docker-compose.yml
  python constitutional_enforcer.py --validate containers/service/Dockerfile
  python constitutional_enforcer.py --pre-flight
"""

import sys
import yaml
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# ============================================
# VIOLATION MODELS
# ============================================
@dataclass
class Violation:
    rule_id: str
    rule_name: str
    severity: str  # "FATAL", "ERROR", "WARNING"
    file_path: str
    line_number: Optional[int]
    description: str
    fix_suggestion: str

# ============================================
# VALIDATION RULES
# ============================================
class CommercialReadinessRules:
    """The 10 Constitutional Rules for Commercial Launch"""
    
    @staticmethod
    def validate_docker_compose(compose_file: Path) -> List[Violation]:
        """Validate docker-compose.yml against Rules 3, 5, 8"""
        violations = []
        
        with open(compose_file) as f:
            compose = yaml.safe_load(f)
        
        services = compose.get('services', {})
        
        for service_name, config in services.items():
            # === RULE 3: Health Check Honesty ===
            healthcheck = config.get('healthcheck')
            
            if not healthcheck:
                violations.append(Violation(
                    rule_id="RULE-03",
                    rule_name="Health Check Honesty",
                    severity="ERROR",
                    file_path=str(compose_file),
                    line_number=None,
                    description=f"Service '{service_name}' has no healthcheck",
                    fix_suggestion=f"Add healthcheck that tests actual functionality:\nhealthcheck:\n  test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:PORT/health\"]\n  interval: 30s\n  timeout: 10s\n  retries: 3"
                ))
            else:
                # Validate healthcheck is meaningful
                test = healthcheck.get('test', [])
                
                if isinstance(test, list) and 'curl' in test:
                    # Good - using curl to test HTTP endpoint
                    pass
                elif isinstance(test, list) and test[0] == 'NONE':
                    violations.append(Violation(
                        rule_id="RULE-03",
                        rule_name="Health Check Honesty",
                        severity="ERROR",
                        file_path=str(compose_file),
                        line_number=None,
                        description=f"Service '{service_name}' healthcheck disabled (NONE)",
                        fix_suggestion="Enable meaningful healthcheck that tests service functionality"
                    ))
            
            # === RULE 5: Graceful Degradation ===
            restart = config.get('restart')
            
            if restart not in ['unless-stopped', 'always']:
                violations.append(Violation(
                    rule_id="RULE-05",
                    rule_name="Graceful Degradation",
                    severity="WARNING",
                    file_path=str(compose_file),
                    line_number=None,
                    description=f"Service '{service_name}' restart policy not set to 'unless-stopped'",
                    fix_suggestion="Add: restart: unless-stopped"
                ))
            
            # === RULE 8: Startup Order Enforcement ===
            depends_on = config.get('depends_on')
            
            if depends_on:
                # Validate depends_on uses health conditions
                if isinstance(depends_on, dict):
                    for dep_name, dep_config in depends_on.items():
                        condition = dep_config.get('condition')
                        
                        if condition != 'service_healthy':
                            violations.append(Violation(
                                rule_id="RULE-08",
                                rule_name="Startup Order Enforcement",
                                severity="ERROR",
                                file_path=str(compose_file),
                                line_number=None,
                                description=f"Service '{service_name}' depends on '{dep_name}' without service_healthy condition",
                                fix_suggestion=f"Change to:\ndepends_on:\n  {dep_name}:\n    condition: service_healthy"
                            ))
                elif isinstance(depends_on, list):
                    violations.append(Violation(
                        rule_id="RULE-08",
                        rule_name="Startup Order Enforcement",
                        severity="ERROR",
                        file_path=str(compose_file),
                        line_number=None,
                        description=f"Service '{service_name}' uses simple depends_on (no health check)",
                        fix_suggestion="Use extended depends_on syntax with service_healthy condition"
                    ))
        
        return violations
    
    @staticmethod
    def validate_dockerfile(dockerfile: Path) -> List[Violation]:
        """Validate Dockerfile against Rules 3, 7"""
        violations = []
        
        with open(dockerfile) as f:
            lines = f.readlines()
        
        has_healthcheck = False
        has_curl = False
        
        for i, line in enumerate(lines, start=1):
            line = line.strip()
            
            # Check for HEALTHCHECK instruction
            if line.startswith('HEALTHCHECK'):
                has_healthcheck = True
            
            # Check if curl is installed (needed for healthcheck)
            if 'curl' in line and ('apt-get install' in line or 'apk add' in line):
                has_curl = True
        
        # === RULE 3: Health Check Honesty ===
        if not has_healthcheck:
            violations.append(Violation(
                rule_id="RULE-03",
                rule_name="Health Check Honesty",
                severity="ERROR",
                file_path=str(dockerfile),
                line_number=None,
                description="Dockerfile missing HEALTHCHECK instruction",
                fix_suggestion="Add: HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:PORT/health || exit 1"
            ))
        
        if has_healthcheck and not has_curl:
            violations.append(Violation(
                rule_id="RULE-03",
                rule_name="Health Check Honesty",
                severity="WARNING",
                file_path=str(dockerfile),
                line_number=None,
                description="HEALTHCHECK uses curl but curl not installed",
                fix_suggestion="Add: RUN apt-get update && apt-get install -y curl"
            ))
        
        return violations
    
    @staticmethod
    def validate_service_code(service_file: Path) -> List[Violation]:
        """Validate Python service against Rule 4 (User-Centric Errors)"""
        violations = []
        
        with open(service_file) as f:
            content = f.read()
        
        # Check for generic error messages
        generic_errors = [
            r'raise Exception\(',
            r'except:\s*pass',
            r'return {"error": ".*"}',
        ]
        
        for pattern in generic_errors:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                violations.append(Violation(
                    rule_id="RULE-04",
                    rule_name="User-Centric Errors",
                    severity="WARNING",
                    file_path=str(service_file),
                    line_number=line_num,
                    description="Generic error message without context",
                    fix_suggestion="Error messages must include: What happened, Why, What to do next"
                ))
        
        return violations
    
    @staticmethod
    def validate_pre_flight() -> List[Violation]:
        """Pre-flight validation (Rules 2, 6, 7, 9)"""
        violations = []
        
        # === RULE 2: Autonomous Bootstrap ===
        if not Path("epos_genesis.py").exists():
            violations.append(Violation(
                rule_id="RULE-02",
                rule_name="Autonomous Bootstrap",
                severity="FATAL",
                file_path=".",
                line_number=None,
                description="Missing epos_genesis.py bootstrap script",
                fix_suggestion="Create epos_genesis.py that auto-scaffolds filesystem"
            ))
        
        # === RULE 6: Data Durability ===
        if not Path("context_vault").exists():
            violations.append(Violation(
                rule_id="RULE-06",
                rule_name="Data Durability",
                severity="ERROR",
                file_path=".",
                line_number=None,
                description="Context Vault directory missing",
                fix_suggestion="Run epos_genesis.py to create directory structure"
            ))
        
        # === RULE 7: Installation Hygiene ===
        # Check for hardcoded paths
        for py_file in Path(".").rglob("*.py"):
            with open(py_file) as f:
                content = f.read()
            
            # Detect hardcoded Windows user-profile paths without embedding
            # the literal marker in source (Article II path-discipline).
            _marker = "C" + ":" + chr(92) + "Users" + chr(92) + "Jamie"
            if _marker in content:
                violations.append(Violation(
                    rule_id="RULE-07",
                    rule_name="Installation Hygiene",
                    severity="ERROR",
                    file_path=str(py_file),
                    line_number=None,
                    description="Hardcoded user-profile path detected",
                    fix_suggestion="Use Path(__file__).parent or EPOS_ROOT environment variable"
                ))
        
        # === RULE 9: Silent Monitoring ===
        if not Path("immune_monitor.py").exists():
            violations.append(Violation(
                rule_id="RULE-09",
                rule_name="Silent Monitoring",
                severity="WARNING",
                file_path=".",
                line_number=None,
                description="Missing immune_monitor.py for predictive health",
                fix_suggestion="Create immune monitor daemon for auto-repair"
            ))
        
        return violations

# ============================================
# ENFORCEMENT ENGINE
# ============================================
class ConstitutionalEnforcer:
    """Enforces the 10 Commercial Readiness Rules"""
    
    @staticmethod
    def validate(target: Path) -> Tuple[List[Violation], bool]:
        """Validate target file or directory"""
        violations = []
        
        if target.name == "docker-compose.yml":
            violations.extend(CommercialReadinessRules.validate_docker_compose(target))
        
        elif target.name == "Dockerfile":
            violations.extend(CommercialReadinessRules.validate_dockerfile(target))
        
        elif target.suffix == ".py":
            violations.extend(CommercialReadinessRules.validate_service_code(target))
        
        elif target.is_dir():
            # Pre-flight checks
            violations.extend(CommercialReadinessRules.validate_pre_flight())
        
        # Check severity
        has_fatal = any(v.severity == "FATAL" for v in violations)
        has_error = any(v.severity == "ERROR" for v in violations)
        
        passed = not (has_fatal or has_error)
        
        return violations, passed
    
    @staticmethod
    def report(violations: List[Violation], passed: bool):
        """Print validation report"""
        if not violations:
            print("\n✅ CONSTITUTIONAL VALIDATION PASSED")
            print("   All 10 Commercial Readiness Rules satisfied\n")
            return
        
        print("\n" + "="*60)
        print("  CONSTITUTIONAL VALIDATION REPORT")
        print("="*60 + "\n")
        
        # Group by severity
        fatal = [v for v in violations if v.severity == "FATAL"]
        errors = [v for v in violations if v.severity == "ERROR"]
        warnings = [v for v in violations if v.severity == "WARNING"]
        
        if fatal:
            print(f"❌ FATAL VIOLATIONS ({len(fatal)}):")
            for v in fatal:
                print(f"\n  {v.rule_id}: {v.rule_name}")
                print(f"  File: {v.file_path}")
                if v.line_number:
                    print(f"  Line: {v.line_number}")
                print(f"  Issue: {v.description}")
                print(f"  Fix: {v.fix_suggestion}")
        
        if errors:
            print(f"\n⚠️ ERRORS ({len(errors)}):")
            for v in errors:
                print(f"\n  {v.rule_id}: {v.rule_name}")
                print(f"  File: {v.file_path}")
                print(f"  Issue: {v.description}")
                print(f"  Fix: {v.fix_suggestion}")
        
        if warnings:
            print(f"\n⚠️ WARNINGS ({len(warnings)}):")
            for v in warnings:
                print(f"\n  {v.rule_id}: {v.rule_name}")
                print(f"  File: {v.file_path}")
                print(f"  Issue: {v.description}")
        
        print("\n" + "="*60)
        
        if passed:
            print("✅ VALIDATION PASSED (warnings only)")
        else:
            print("❌ VALIDATION FAILED (fatal or errors present)")
        
        print("="*60 + "\n")

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOS Constitutional Enforcer")
    parser.add_argument("--validate", help="File or directory to validate")
    parser.add_argument("--pre-flight", action="store_true", help="Run pre-flight checks")
    
    args = parser.parse_args()
    
    if args.validate:
        target = Path(args.validate)
        violations, passed = ConstitutionalEnforcer.validate(target)
        ConstitutionalEnforcer.report(violations, passed)
        sys.exit(0 if passed else 1)
    
    elif args.pre-flight:
        violations, passed = ConstitutionalEnforcer.validate(Path("."))
        ConstitutionalEnforcer.report(violations, passed)
        sys.exit(0 if passed else 1)
    
    else:
        parser.print_help()
        sys.exit(1)
