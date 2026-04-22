# EPOS GOVERNANCE WATERMARK
# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/roles/analyst.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/roles/analyst.py
"""
Flywheel Analyst (Agent Omega)
Turns BI logs into strategic intelligence and governance proposals.

Authority: Article VIII (Decision Logging), Strategic Analysis
Monetization: $149/mo (Governance-aware BI Dashboard)
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# Path setup
EPOS_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(EPOS_ROOT / "engine"))


class FlywheelAnalyst:
    """
    Agent Omega: Strategic intelligence and pattern detection.
    
    Responsibilities:
    - Detect failure patterns from BI logs
    - Track 4 flywheel metrics (Content, Revenue, Data Moat, Sovereign Scaling)
    - Propose constitutional amendments
    """
    
    def __init__(self):
        self.bi_log = EPOS_ROOT / "ops" / "logs" / "bi_decision_log.jsonl"
        self.reports_dir = EPOS_ROOT / "ops" / "flywheel_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def detect_failure_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow 1: Parse BI logs for recurring failure patterns.
        
        Args:
            params: {
                "lookback_days": int (default 7),
                "threshold": int (default 3)  # Min occurrences to flag
            }
        
        Returns:
            {
                "status": "complete",
                "patterns": [
                    {
                        "error_code": str,
                        "count": int,
                        "missions": [str],
                        "suggested_fix": str
                    }
                ],
                "proposed_checks": [str]
            }
        """
        lookback = params.get("lookback_days", 7)
        threshold = params.get("threshold", 3)
        
        if not self.bi_log.exists():
            return {"status": "no_data", "patterns": [], "proposed_checks": []}
        
        # Load recent logs
        cutoff = datetime.now() - timedelta(days=lookback)
        entries = []
        
        with self.bi_log.open("r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff:
                        entries.append(entry)
                except:
                    continue
        
        # Detect patterns
        error_counts = Counter()
        error_missions = defaultdict(list)
        
        for entry in entries:
            if entry.get("status") == "failed":
                error = entry.get("output", {}).get("error", "UNKNOWN")
                # Extract error code (e.g., ERR-PATH-001)
                error_code = error.split(":")[0] if ":" in error else error[:20]
                error_counts[error_code] += 1
                error_missions[error_code].append(entry["mission_id"])
        
        # Flag patterns above threshold
        patterns = []
        proposed_checks = []
        
        for error_code, count in error_counts.items():
            if count >= threshold:
                patterns.append({
                    "error_code": error_code,
                    "count": count,
                    "missions": error_missions[error_code][:5],  # First 5
                    "suggested_fix": self._suggest_fix(error_code)
                })
                
                # Propose new doctor check
                if "PATH" in error_code:
                    proposed_checks.append(f"epos_doctor: Add path validation for {error_code}")
                elif "CONTEXT" in error_code:
                    proposed_checks.append(f"governance_gate: Enforce vault migration for >8K data")
        
        # Save report
        report_file = self.reports_dir / f"patterns_{datetime.now():%Y%m%d}.json"
        report_file.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "lookback_days": lookback,
            "patterns": patterns,
            "proposed_checks": proposed_checks
        }, indent=2))
        
        return {
            "status": "complete",
            "patterns": patterns,
            "proposed_checks": proposed_checks
        }
    
    def calculate_flywheel_metrics(self) -> Dict[str, Any]:
        """
        Workflow 2: Track the 4 EPOS flywheels.
        
        Returns:
            {
                "status": "complete",
                "flywheels": {
                    "content": {...},
                    "revenue": {...},
                    "data_moat": {...},
                    "sovereign_scaling": {...}
                }
            }
        """
        # Content Flywheel (output per week)
        content_output = self._calculate_content_output()
        
        # Revenue Flywheel (node monetization)
        revenue_metrics = self._calculate_revenue_metrics()
        
        # Data Moat (vault growth)
        vault_metrics = self._calculate_vault_metrics()
        
        # Sovereign Scaling (node independence)
        sovereignty_metrics = self._calculate_sovereignty_metrics()
        
        flywheels = {
            "content": content_output,
            "revenue": revenue_metrics,
            "data_moat": vault_metrics,
            "sovereign_scaling": sovereignty_metrics,
            "calculated_at": datetime.now().isoformat()
        }
        
        # Save report
        report_file = self.reports_dir / f"flywheel_{datetime.now():%Y%m%d}.json"
        report_file.write_text(json.dumps(flywheels, indent=2))
        
        return {
            "status": "complete",
            "flywheels": flywheels
        }
    
    def propose_constitutional_amendment(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow 3: Draft amendment proposal based on recurring patterns.
        
        Args:
            evidence: {
                "pattern": str,
                "occurrences": int,
                "impact": str
            }
        
        Returns:
            {
                "status": "drafted",
                "amendment_file": str,
                "content": str
            }
        """
        pattern = evidence.get("pattern", "Unknown")
        occurrences = evidence.get("occurrences", 0)
        impact = evidence.get("impact", "Unknown")
        
        amendment = f"""
# EPOS Constitution Amendment Proposal
**Date**: {datetime.now():%Y-%m-%d}
**Proposed By**: Flywheel Analyst (Agent Omega)

## Evidence
- **Pattern Detected**: {pattern}
- **Occurrences**: {occurrences} instances in last 30 days
- **Impact**: {impact}

## Proposed Amendment

### Article [TBD]: [New Rule Title]

**Rule**: [Describe new constitutional requirement]

**Rationale**: This pattern indicates a systematic failure mode that current governance does not address. By encoding this check into the constitution, we prevent future occurrences.

**Implementation**:
1. Update `epos_doctor.py` with new check
2. Update `governance_gate.py` with new violation code
3. Run full audit on `/engine` to identify existing violations

## Predicted Impact
- Reduction in {pattern} failures: [Estimate]%
- Governance score improvement: [Estimate]%

## Rollout Plan
1. Draft PR with code changes
2. Test on staging environment
3. Deploy to production with 1-week monitoring period

---
**Status**: DRAFT - Awaiting review by Chief Strategist
"""
        
        # Save proposal
        proposal_file = self.reports_dir / f"amendment_{datetime.now():%Y%m%d_%H%M}.md"
        proposal_file.write_text(amendment)
        
        return {
            "status": "drafted",
            "amendment_file": str(proposal_file.relative_to(EPOS_ROOT)),
            "content": amendment
        }
    
    # Helper methods
    
    def _suggest_fix(self, error_code: str) -> str:
        """Map error codes to suggested fixes"""
        fixes = {
            "ERR-PATH": "Use pathlib.Path with absolute Windows-style paths",
            "ERR-CONTEXT": "Migrate inline data >8K to Context Vault",
            "ERR-HEADER": "Add '# File: C:\\...' header to all Python files",
            "ERR-CONFIG": "Use load_dotenv() with explicit path"
        }
        
        for key, fix in fixes.items():
            if key in error_code:
                return fix
        return "Review EPOS Constitution for relevant article"
    
    def _calculate_content_output(self) -> Dict:
        """Content Lab output metrics"""
        # Placeholder - integrate with Content Lab nodes
        return {
            "pieces_per_week": 0,
            "platforms": 0,
            "multiplier": "0x"
        }
    
    def _calculate_revenue_metrics(self) -> Dict:
        """Node monetization tracking"""
        # Placeholder - integrate with billing system
        return {
            "active_nodes": 3,
            "mrr": 0,
            "arr": 0
        }
    
    def _calculate_vault_metrics(self) -> Dict:
        """Data moat growth"""
        vault_reports = list((EPOS_ROOT / "ops" / "vault_reports").glob("*.json"))
        if not vault_reports:
            return {"size_mb": 0, "missions": 0, "growth_rate": "N/A"}
        
        latest = max(vault_reports, key=lambda p: p.stat().st_mtime)
        return json.loads(latest.read_text())
    
    def _calculate_sovereignty_metrics(self) -> Dict:
        """Node independence scores"""
        # Placeholder - integrate with sovereignty tests
        return {
            "nodes_tested": 0,
            "passing_tests": 0,
            "independence_score": "N/A"
        }


if __name__ == "__main__":
    # Test mode
    analyst = FlywheelAnalyst()
    patterns = analyst.detect_failure_patterns({"lookback_days": 30})
    print(f"Detected {len(patterns['patterns'])} failure patterns")
