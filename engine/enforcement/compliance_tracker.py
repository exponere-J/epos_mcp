# EPOS GOVERNANCE WATERMARK
"""
File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/enforcement/compliance_tracker.py
Purpose: Tracks agent learning and performance over time
Constitutional Authority: EPOS_CONSTITUTION_v3.1.md Article V

Maintains JSONL ledgers for each agent showing:
- Violation history
- Success history
- Compliance score trends
- Improvement trajectories
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json


class ComplianceTracker:
    """
    Maintains agent performance ledgers in context_vault.
    
    Ledger format (JSONL):
    {"timestamp": "2026-02-05T10:00:00", "event_type": "violation", "violation_code": "ERR-PATH-001", "mission_id": "M001"}
    {"timestamp": "2026-02-05T10:15:00", "event_type": "success", "mission_id": "M002"}
    """
    
    def __init__(self, epos_root: Path = None):
        """Initialize tracker with ledger path."""
        self.epos_root = epos_root or Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
        self.ledger_path = self.epos_root / "context_vault/learning/agent_performance"
        self.ledger_path.mkdir(parents=True, exist_ok=True)
    
    def record_violation(
        self, 
        agent_id: str, 
        violation_code: str,
        mission_id: Optional[str] = None
    ):
        """Record a violation event for an agent."""
        ledger = self._get_ledger_file(agent_id)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "violation",
            "violation_code": violation_code,
            "mission_id": mission_id
        }
        
        with open(ledger, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def record_success(
        self, 
        agent_id: str,
        mission_id: Optional[str] = None
    ):
        """Record a successful validation for an agent."""
        ledger = self._get_ledger_file(agent_id)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "success",
            "mission_id": mission_id
        }
        
        with open(ledger, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_compliance_score(
        self, 
        agent_id: str, 
        window_days: int = 30
    ) -> float:
        """
        Calculate compliance score (0.0-1.0) over time window.
        
        Score = successes / (violations + successes)
        """
        ledger = self._get_ledger_file(agent_id)
        
        if not ledger.exists():
            return 0.0
        
        violations = 0
        successes = 0
        cutoff = datetime.now() - timedelta(days=window_days)
        
        with open(ledger, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    if entry_time < cutoff:
                        continue  # Outside window
                    
                    if entry["event_type"] == "violation":
                        violations += 1
                    elif entry["event_type"] == "success":
                        successes += 1
                except:
                    continue
        
        total = violations + successes
        if total == 0:
            return 0.0
        
        return successes / total
    
    def get_improvement_trend(self, agent_id: str) -> str:
        """
        Analyze whether agent is improving over time.
        
        Returns: "improving", "stable", "declining"
        """
        ledger = self._get_ledger_file(agent_id)
        
        if not ledger.exists():
            return "unknown"
        
        # Compare last 7 days vs previous 7 days
        now = datetime.now()
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)
        
        recent_score = self._score_for_period(ledger, recent_start, now)
        previous_score = self._score_for_period(ledger, previous_start, recent_start)
        
        if recent_score is None or previous_score is None:
            return "insufficient_data"
        
        diff = recent_score - previous_score
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    def get_violation_count(self, agent_id: str, window_days: int = 30) -> int:
        """Get total violation count within time window."""
        ledger = self._get_ledger_file(agent_id)
        
        if not ledger.exists():
            return 0
        
        count = 0
        cutoff = datetime.now() - timedelta(days=window_days)
        
        with open(ledger, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    if entry_time >= cutoff and entry["event_type"] == "violation":
                        count += 1
                except:
                    continue
        
        return count
    
    def get_success_count(self, agent_id: str, window_days: int = 30) -> int:
        """Get total success count within time window."""
        ledger = self._get_ledger_file(agent_id)
        
        if not ledger.exists():
            return 0
        
        count = 0
        cutoff = datetime.now() - timedelta(days=window_days)
        
        with open(ledger, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    if entry_time >= cutoff and entry["event_type"] == "success":
                        count += 1
                except:
                    continue
        
        return count
    
    def _get_ledger_file(self, agent_id: str) -> Path:
        """Get ledger file path for agent."""
        return self.ledger_path / f"{agent_id}.jsonl"
    
    def _score_for_period(
        self, 
        ledger: Path, 
        start: datetime, 
        end: datetime
    ) -> Optional[float]:
        """Calculate score for a specific time period."""
        violations = 0
        successes = 0
        
        if not ledger.exists():
            return None
        
        with open(ledger, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    if start <= entry_time < end:
                        if entry["event_type"] == "violation":
                            violations += 1
                        elif entry["event_type"] == "success":
                            successes += 1
                except:
                    continue
        
        total = violations + successes
        if total == 0:
            return None
        
        return successes / total


if __name__ == "__main__":
    # Test compliance tracker
    print("Testing Compliance Tracker...")
    
    tracker = ComplianceTracker()
    
    # Record some violations
    tracker.record_violation("agent_zero", "ERR-PATH-001", "M001")
    tracker.record_violation("agent_zero", "ERR-HEADER-001", "M002")
    
    # Record some successes
    tracker.record_success("agent_zero", "M003")
    tracker.record_success("agent_zero", "M004")
    tracker.record_success("agent_zero", "M005")
    
    # Check metrics
    score = tracker.get_compliance_score("agent_zero")
    trend = tracker.get_improvement_trend("agent_zero")
    violations = tracker.get_violation_count("agent_zero")
    successes = tracker.get_success_count("agent_zero")
    
    print(f"\nAgent Zero Status:")
    print(f"  Compliance Score: {score:.1%}")
    print(f"  Trend: {trend}")
    print(f"  Violations: {violations}")
    print(f"  Successes: {successes}")
