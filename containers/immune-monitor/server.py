# File: /mnt/c/Users/Jamie/workspace/epos_mcp/containers/immune-monitor/server.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
Immune Monitor - EPOS Predictive Health System
Monitors service health and predicts cascade failures before they happen
"""

import os
from pathlib import Path
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

_GOVERNANCE_GATE_URL = os.getenv("GOVERNANCE_GATE_URL", "http://governance-gate:8101")
_GOVERNANCE_SRV_URL = os.getenv("GOVERNANCE_SERVER_URL", "http://governance-srv:8101")
_LEARNING_URL = os.getenv("LEARNING_URL", "http://learning-server:8102")
_CONTEXT_URL = os.getenv("CONTEXT_URL", "http://context-server:8103")
_EPOS_CORE_URL = os.getenv("EPOS_CORE_URL", "http://epos-core:8001")

class ImmuneMonitor:
    def __init__(self, epos_root: Path, event_bus_url: str = _EPOS_CORE_URL):
        self.epos_root = Path(epos_root)
        self.event_bus_url = event_bus_url
        self.log_dir = self.epos_root / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Setup logging
        log_file = self.log_dir / f"immune_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Service definitions — use Docker service names, not localhost
        self.services = {
            "governance-gate": {"url": f"{_GOVERNANCE_GATE_URL}/health", "critical": True},
            "governance-srv": {"url": f"{_GOVERNANCE_SRV_URL}/health", "critical": True},
            "learning": {"url": f"{_LEARNING_URL}/health", "critical": True},
            "context": {"url": f"{_CONTEXT_URL}/health", "critical": True},
            "epos-core": {"url": f"{_EPOS_CORE_URL}/health", "critical": True},
        }
        
        self.health_history = {name: [] for name in self.services.keys()}
        self.alert_threshold = 3  # Failed checks before alert
        
    def check_service_health(self, service_name: str, config: Dict) -> Dict:
        """Check health of a single service"""
        try:
            response = requests.get(config["url"], timeout=5)
            
            health_status = {
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat(),
                "response_time_ms": int(response.elapsed.total_seconds() * 1000)
            }
            
            # Try to parse JSON response
            try:
                health_status["details"] = response.json()
            except:
                health_status["details"] = {"raw": response.text[:200]}
                
            return health_status
            
        except requests.exceptions.ConnectionError:
            return {
                "service": service_name,
                "status": "down",
                "error": "Connection refused",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.Timeout:
            return {
                "service": service_name,
                "status": "timeout",
                "error": "Request timeout after 5s",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def predict_cascade_failure(self, service_name: str, config: Dict) -> Optional[Dict]:
        """Predict if service failure will cascade to dependents"""
        # Check recent history
        recent_failures = sum(1 for h in self.health_history[service_name][-5:] 
                             if h.get("status") != "healthy")
        
        if recent_failures >= self.alert_threshold:
            # Find dependent services
            dependents = [name for name, svc in self.services.items() 
                         if service_name in svc.get("depends_on", [])]
            
            if dependents:
                return {
                    "failing_service": service_name,
                    "cascade_risk": "HIGH",
                    "affected_services": dependents,
                    "prediction": f"{service_name} failure will cascade to {len(dependents)} dependent services in ~30s",
                    "recommended_action": "Restart failing service immediately or prepare dependent service fallbacks"
                }
        
        return None
    
    def auto_remediate(self, service_name: str) -> bool:
        """Attempt automatic remediation"""
        self.logger.warning(f"🔧 Attempting auto-remediation for {service_name}")
        
        # For now, just log the attempt
        # In production, this would trigger docker restart, etc.
        self.logger.info(f"Would execute: docker restart epos-{service_name}")
        
        return True
    
    def publish_alert(self, alert: Dict):
        """Publish alert to Event Bus"""
        try:
            requests.post(
                f"{self.event_bus_url}/publish",
                json={
                    "event_type": "immune.alert",
                    "payload": alert
                },
                timeout=3
            )
        except Exception as e:
            self.logger.error(f"Failed to publish alert: {e}")
    
    def monitor_cycle(self):
        """Run one monitoring cycle"""
        self.logger.info("🔍 Starting health check cycle")
        
        all_healthy = True
        
        for service_name, config in self.services.items():
            health = self.check_service_health(service_name, config)
            self.health_history[service_name].append(health)
            
            # Keep only last 10 checks
            if len(self.health_history[service_name]) > 10:
                self.health_history[service_name].pop(0)
            
            status_icon = "✅" if health["status"] == "healthy" else "❌"
            self.logger.info(f"{status_icon} {service_name}: {health['status']}")
            
            if health["status"] != "healthy":
                all_healthy = False
                
                # Check for cascade risk
                cascade = self.predict_cascade_failure(service_name, config)
                if cascade:
                    self.logger.warning(f"⚠️  CASCADE PREDICTION: {cascade['prediction']}")
                    self.publish_alert(cascade)
                    
                    # Auto-remediate if service is critical
                    if config.get("critical", False):
                        self.auto_remediate(service_name)
        
        if all_healthy:
            self.logger.info("✅ All services healthy")
        
        return all_healthy
    
    def run(self, interval_seconds: int = 30):
        """Run continuous monitoring"""
        self.logger.info(f"🚀 Immune Monitor started (check interval: {interval_seconds}s)")
        
        try:
            while True:
                self.monitor_cycle()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Immune Monitor stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Immune Monitor crashed: {e}")
            raise

def main():
    """CLI entry point"""
    import sys

    epos_root = Path(os.getenv("EPOS_ROOT", Path.cwd()))
    if len(sys.argv) > 1:
        epos_root = Path(sys.argv[1])

    monitor = ImmuneMonitor(epos_root)
    monitor.run(interval_seconds=30)

if __name__ == "__main__":
    main()
