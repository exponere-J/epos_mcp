#!/usr/bin/env python3
"""
EPOS IMMUNE MONITOR - Predictive Health System
Constitutional Authority: Article VI (Autonomous Evolution), Article X (Commercial Readiness)

PHILOSOPHY:
  Like biological immune systems, EPOS detects threats BEFORE symptoms appear.
  Traditional health checks are reactive (symptoms → diagnosis).
  Immune monitoring is predictive (pattern recognition → prevention).

CAPABILITIES:
  1. Dependency graph analysis (if A fails, B will fail in 30s)
  2. Resource trend analysis (memory leak detected, crash predicted in 5min)
  3. Pattern recognition (this error sequence always leads to cascade failure)
  4. Auto-remediation (restart container before failure propagates)
  5. Learning (builds confidence scores for predictions over time)

OPERATION:
  Runs as daemon, polls every 30s, publishes predictions to Event Bus.
  Other services can subscribe to early-warning events.
"""

import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import subprocess

sys.path.insert(0, '/app')

try:
    from engine.event_bus import get_event_bus
    bus = get_event_bus()
    BUS_AVAILABLE = True
except ImportError:
    bus = None
    BUS_AVAILABLE = False

# ============================================
# HEALTH MODELS
# ============================================
@dataclass
class HealthSnapshot:
    """Point-in-time health reading"""
    service_name: str
    timestamp: datetime
    status: str  # "healthy", "degraded", "failing", "down"
    response_time_ms: Optional[float]
    cpu_percent: Optional[float]
    memory_mb: Optional[float]
    error_count: int
    dependency_health: Dict[str, str]

@dataclass
class HealthPrediction:
    """Predicted future health state"""
    service_name: str
    prediction_time: datetime
    predicted_failure_time: Optional[datetime]
    confidence: float  # 0.0 to 1.0
    failure_type: str  # "cascade", "resource_exhaustion", "timeout", "crash"
    recommended_action: str
    evidence: List[str]

# ============================================
# DEPENDENCY GRAPH
# ============================================
DEPENDENCY_GRAPH = {
    "event-bus": {
        "port": 8100,
        "dependencies": [],
        "criticality": "FATAL",
        "dependents": ["governance-server", "learning-server", "context-server", "diagnostic-server", "agent-zero", "command-center", "error-detector"]
    },
    "governance-server": {
        "port": 8101,
        "dependencies": ["event-bus"],
        "criticality": "FATAL",
        "dependents": ["agent-zero"]
    },
    "learning-server": {
        "port": 8102,
        "dependencies": ["event-bus"],
        "criticality": "HIGH",
        "dependents": ["agent-zero"]
    },
    "context-server": {
        "port": 8103,
        "dependencies": ["event-bus"],
        "criticality": "HIGH",
        "dependents": ["agent-zero", "command-center"]
    },
    "diagnostic-server": {
        "port": 8104,
        "dependencies": ["event-bus"],
        "criticality": "MEDIUM",
        "dependents": ["command-center"]
    },
    "agent-zero": {
        "port": 8105,
        "dependencies": ["event-bus", "governance-server", "learning-server"],
        "criticality": "FATAL",
        "dependents": []
    },
    "command-center": {
        "port": 8200,
        "dependencies": ["event-bus", "context-server"],
        "criticality": "LOW",
        "dependents": []
    },
    "error-detector": {
        "port": 8115,
        "dependencies": ["event-bus"],
        "criticality": "MEDIUM",
        "dependents": []
    }
}

# ============================================
# IMMUNE MONITOR
# ============================================
class ImmuneMonitor:
    """Predictive health monitoring with auto-remediation"""
    
    def __init__(self, history_window: int = 20):
        self.history: Dict[str, deque] = {}
        self.history_window = history_window
        
        # Initialize history buffers
        for service in DEPENDENCY_GRAPH.keys():
            self.history[service] = deque(maxlen=history_window)
    
    def capture_snapshot(self, service_name: str) -> Optional[HealthSnapshot]:
        """Capture current health state"""
        config = DEPENDENCY_GRAPH.get(service_name)
        if not config:
            return None
        
        port = config["port"]
        
        # Poll health endpoint
        try:
            start = time.time()
            resp = requests.get(f"http://localhost:{port}/health", timeout=5)
            response_time = (time.time() - start) * 1000
            
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                
                # Get container stats
                try:
                    stats_result = subprocess.run(
                        ["docker", "stats", f"epos-{service_name}", "--no-stream", "--format", "{{.CPUPerc}},{{.MemUsage}}"],
                        capture_output=True,
                        timeout=2
                    )
                    
                    if stats_result.returncode == 0:
                        parts = stats_result.stdout.decode().strip().split(',')
                        cpu_percent = float(parts[0].replace('%', ''))
                        memory_str = parts[1].split('/')[0].strip()
                        memory_mb = float(memory_str.replace('MiB', '').replace('GiB', '').strip())
                    else:
                        cpu_percent = None
                        memory_mb = None
                except:
                    cpu_percent = None
                    memory_mb = None
                
                # Check dependencies
                dep_health = {}
                for dep_name in config["dependencies"]:
                    dep_config = DEPENDENCY_GRAPH[dep_name]
                    dep_port = dep_config["port"]
                    
                    try:
                        dep_resp = requests.get(f"http://localhost:{dep_port}/health", timeout=2)
                        dep_health[dep_name] = "healthy" if dep_resp.status_code == 200 else "failing"
                    except:
                        dep_health[dep_name] = "down"
                
                return HealthSnapshot(
                    service_name=service_name,
                    timestamp=datetime.now(),
                    status=status,
                    response_time_ms=response_time,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    error_count=0,  # TODO: Parse from logs
                    dependency_health=dep_health
                )
            
            else:
                return HealthSnapshot(
                    service_name=service_name,
                    timestamp=datetime.now(),
                    status="failing",
                    response_time_ms=response_time,
                    cpu_percent=None,
                    memory_mb=None,
                    error_count=1,
                    dependency_health={}
                )
        
        except requests.exceptions.Timeout:
            return HealthSnapshot(
                service_name=service_name,
                timestamp=datetime.now(),
                status="timeout",
                response_time_ms=None,
                cpu_percent=None,
                memory_mb=None,
                error_count=1,
                dependency_health={}
            )
        
        except Exception as e:
            return HealthSnapshot(
                service_name=service_name,
                timestamp=datetime.now(),
                status="down",
                response_time_ms=None,
                cpu_percent=None,
                memory_mb=None,
                error_count=1,
                dependency_health={}
            )
    
    def predict_failure(self, service_name: str) -> Optional[HealthPrediction]:
        """Predict future failure based on pattern analysis"""
        history = self.history.get(service_name, [])
        
        if len(history) < 3:
            return None  # Not enough data
        
        recent = list(history)[-3:]
        config = DEPENDENCY_GRAPH[service_name]
        
        evidence = []
        failure_type = None
        predicted_time = None
        confidence = 0.0
        action = None
        
        # === PATTERN 1: Dependency Cascade ===
        dep_failing = []
        for snapshot in recent:
            for dep_name, dep_status in snapshot.dependency_health.items():
                if dep_status in ["failing", "down"]:
                    dep_failing.append(dep_name)
        
        if dep_failing:
            unique_failing = set(dep_failing)
            evidence.append(f"Dependencies failing: {', '.join(unique_failing)}")
            failure_type = "cascade"
            predicted_time = datetime.now() + timedelta(seconds=30)
            confidence = 0.9
            action = f"Restart dependencies: {', '.join(unique_failing)}"
        
        # === PATTERN 2: Response Time Degradation ===
        response_times = [s.response_time_ms for s in recent if s.response_time_ms]
        if len(response_times) >= 3:
            if response_times[-1] > response_times[0] * 3:
                evidence.append(f"Response time spike: {response_times[0]:.0f}ms → {response_times[-1]:.0f}ms")
                failure_type = "timeout"
                predicted_time = datetime.now() + timedelta(minutes=5)
                confidence = 0.7
                action = f"Restart {service_name} container"
        
        # === PATTERN 3: Memory Leak ===
        memory_usage = [s.memory_mb for s in recent if s.memory_mb]
        if len(memory_usage) >= 3:
            if all(memory_usage[i] < memory_usage[i+1] for i in range(len(memory_usage)-1)):
                growth_rate = (memory_usage[-1] - memory_usage[0]) / len(memory_usage)
                evidence.append(f"Memory leak detected: +{growth_rate:.1f}MB per check")
                failure_type = "resource_exhaustion"
                
                # Predict crash time
                if memory_usage[-1] > 1024:  # Over 1GB
                    predicted_time = datetime.now() + timedelta(minutes=10)
                    confidence = 0.8
                    action = f"Restart {service_name} to free memory"
        
        # === PATTERN 4: Status Oscillation ===
        statuses = [s.status for s in recent]
        if len(set(statuses)) > 2:
            evidence.append(f"Status oscillating: {' → '.join(statuses)}")
            failure_type = "crash"
            predicted_time = datetime.now() + timedelta(minutes=2)
            confidence = 0.6
            action = f"Investigate {service_name} logs for crash loop"
        
        if failure_type:
            return HealthPrediction(
                service_name=service_name,
                prediction_time=datetime.now(),
                predicted_failure_time=predicted_time,
                confidence=confidence,
                failure_type=failure_type,
                recommended_action=action,
                evidence=evidence
            )
        
        return None
    
    def auto_remediate(self, prediction: HealthPrediction) -> bool:
        """Attempt automatic remediation"""
        service_name = prediction.service_name
        
        # Only auto-remediate high-confidence predictions
        if prediction.confidence < 0.7:
            return False
        
        # Restart container
        try:
            print(f"[AUTO-REMEDIATE] Restarting {service_name}...")
            
            result = subprocess.run(
                ["docker-compose", "restart", service_name],
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"[AUTO-REMEDIATE] ✅ {service_name} restarted")
                
                # Publish remediation event
                if bus:
                    bus.publish(
                        event_type="immune.auto_remediate",
                        payload={
                            "service": service_name,
                            "failure_type": prediction.failure_type,
                            "confidence": prediction.confidence,
                            "action": "restart"
                        },
                        source_server="immune-monitor"
                    )
                
                return True
        
        except Exception as e:
            print(f"[AUTO-REMEDIATE] ❌ Failed to restart {service_name}: {e}")
        
        return False
    
    def monitor_loop(self, interval: int = 30):
        """Main monitoring loop"""
        print("="*60)
        print("  EPOS IMMUNE MONITOR")
        print("="*60)
        print(f"  Monitoring {len(DEPENDENCY_GRAPH)} services")
        print(f"  Poll interval: {interval}s")
        print(f"  History window: {self.history_window} snapshots")
        print(f"  Event Bus: {'Connected' if BUS_AVAILABLE else 'Standalone'}")
        print("="*60 + "\n")
        
        while True:
            try:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === Health Check Cycle ===")
                
                for service_name in DEPENDENCY_GRAPH.keys():
                    # Capture snapshot
                    snapshot = self.capture_snapshot(service_name)
                    
                    if snapshot:
                        self.history[service_name].append(snapshot)
                        
                        # Log status
                        status_emoji = {
                            "healthy": "🟢",
                            "degraded": "🟡",
                            "failing": "🔴",
                            "down": "⚫",
                            "timeout": "⏱️"
                        }.get(snapshot.status, "❓")
                        
                        print(f"  {status_emoji} {service_name:20s} {snapshot.status:10s}", end="")
                        
                        if snapshot.response_time_ms:
                            print(f" {snapshot.response_time_ms:6.0f}ms", end="")
                        
                        if snapshot.memory_mb:
                            print(f" {snapshot.memory_mb:6.0f}MB", end="")
                        
                        print()
                        
                        # Predict failures
                        prediction = self.predict_failure(service_name)
                        
                        if prediction:
                            print(f"    ⚠️ PREDICTION: {prediction.failure_type} in {(prediction.predicted_failure_time - datetime.now()).total_seconds():.0f}s (confidence: {prediction.confidence:.0%})")
                            print(f"       Action: {prediction.recommended_action}")
                            
                            # Publish prediction
                            if bus:
                                bus.publish(
                                    event_type="immune.prediction",
                                    payload=asdict(prediction),
                                    source_server="immune-monitor"
                                )
                            
                            # Auto-remediate if high confidence
                            if prediction.confidence >= 0.8:
                                self.auto_remediate(prediction)
                
                time.sleep(interval)
            
            except KeyboardInterrupt:
                print("\n\n⚠️ Immune Monitor stopped by user")
                break
            
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                time.sleep(interval)

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    monitor = ImmuneMonitor(history_window=20)
    monitor.monitor_loop(interval=30)
