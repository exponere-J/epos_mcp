# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/engine/jarvis_bridge.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
"""
JARVIS Bridge - Agent Zero Integration Layer
Connects Agent Zero to EPOS Event Bus, Governance, Learning, and Context servers
"""

from pathlib import Path
import asyncio
import websockets
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import os

class JARVISBridge:
    def __init__(self, epos_root: Path, az_root: Path):
        self.epos_root = Path(epos_root)
        self.az_root = Path(az_root)
        
        # Service URLs from environment or Docker service-name defaults
        self.event_bus_url = os.getenv("EVENT_BUS_URL", os.getenv("EPOS_CORE_URL", "http://epos-core:8001"))
        self.governance_url = os.getenv("GOVERNANCE_URL", os.getenv("GOVERNANCE_GATE_URL", "http://governance-gate:8101"))
        self.learning_url = os.getenv("LEARNING_URL", "http://learning-server:8102")
        self.context_url = os.getenv("CONTEXT_URL", "http://context-server:8103")
        
        # Setup logging
        log_dir = self.epos_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"jarvis_bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # State
        self.connected = False
        self.mission_queue = []
        self.confidence_threshold = 0.8
        
    async def connect_event_bus(self):
        """Connect to EPOS Event Bus via WebSocket"""
        ws_url = self.event_bus_url.replace("http://", "ws://") + "/ws"
        
        self.logger.info(f"🔌 Connecting to Event Bus: {ws_url}")
        
        try:
            async with websockets.connect(ws_url) as websocket:
                self.connected = True
                self.logger.info("✅ Connected to Event Bus")
                
                # Subscribe to all events
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "pattern": "*"
                }))
                
                # Listen for events
                async for message in websocket:
                    await self.handle_event(json.loads(message))
                    
        except Exception as e:
            self.logger.error(f"❌ Event Bus connection failed: {e}")
            self.connected = False
    
    async def handle_event(self, event: Dict):
        """Handle incoming events from Event Bus"""
        event_type = event.get("event_type", "unknown")
        payload = event.get("payload", {})
        
        self.logger.info(f"📨 Received event: {event_type}")
        
        # Route events to handlers
        if event_type == "mission.new":
            await self.handle_new_mission(payload)
        elif event_type == "governance.violation":
            await self.handle_violation(payload)
        elif event_type == "learning.insight":
            await self.handle_insight(payload)
        elif event_type == "immune.alert":
            await self.handle_health_alert(payload)
    
    async def handle_new_mission(self, mission: Dict):
        """Handle new mission request"""
        mission_id = mission.get("mission_id", "unknown")
        self.logger.info(f"🎯 New mission: {mission_id}")
        
        # Validate with governance first
        validation = self.validate_mission(mission)
        
        if not validation["passed"]:
            self.logger.warning(f"⚠️  Mission failed governance: {validation['violations']}")
            self.publish_event("mission.rejected", {
                "mission_id": mission_id,
                "reason": "governance_failure",
                "violations": validation["violations"]
            })
            return
        
        # Queue mission for Agent Zero
        self.mission_queue.append(mission)
        self.logger.info(f"✅ Mission queued: {mission_id}")
        
        # If high confidence, execute immediately
        confidence = mission.get("confidence", 0.5)
        if confidence >= self.confidence_threshold:
            await self.execute_mission(mission)
        else:
            self.logger.info(f"⏸️  Mission queued for review (confidence: {confidence})")
    
    def validate_mission(self, mission: Dict) -> Dict:
        """Validate mission against constitutional rules"""
        try:
            response = requests.post(
                f"{self.governance_url}/validate",
                json=mission,
                timeout=5
            )
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"❌ Governance validation failed: {e}")
            return {
                "passed": False,
                "violations": [{"code": "ERR-GOVERNANCE-UNREACHABLE", "message": str(e)}]
            }
    
    async def execute_mission(self, mission: Dict):
        """Execute mission via Agent Zero"""
        mission_id = mission.get("mission_id", "unknown")
        self.logger.info(f"🚀 Executing mission: {mission_id}")
        
        # Write mission to Agent Zero work directory
        mission_file = self.az_root / "work_dir" / f"{mission_id}.json"
        mission_file.write_text(json.dumps(mission, indent=2), encoding='utf-8')
        
        # Log episode start
        self.log_episode({
            "mission_id": mission_id,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
        
        # In production, this would invoke Agent Zero's API or CLI
        # For now, we log that we would execute
        self.logger.info(f"Would execute: python {self.az_root}/run.py --task {mission_file}")
        
        # Publish execution event
        self.publish_event("mission.executing", {
            "mission_id": mission_id,
            "executor": "agent_zero"
        })
    
    async def handle_violation(self, violation: Dict):
        """Handle constitutional violation alerts"""
        self.logger.warning(f"⚠️  Constitutional violation: {violation.get('code')}")
        
        # Log to Context Vault
        self.log_to_context_vault("violations", violation)
    
    async def handle_insight(self, insight: Dict):
        """Handle learning insights from meta-agents"""
        self.logger.info(f"💡 Learning insight: {insight.get('type')}")
        
        # Store in semantic memory
        self.log_to_context_vault("meta/semantic", insight)
    
    async def handle_health_alert(self, alert: Dict):
        """Handle health/immune system alerts"""
        self.logger.warning(f"🩺 Health alert: {alert.get('failing_service')}")
        
        # If critical service down, pause new missions
        if alert.get("cascade_risk") == "HIGH":
            self.logger.warning("⏸️  Pausing mission execution due to cascade risk")
            self.mission_queue.clear()
    
    def publish_event(self, event_type: str, payload: Dict):
        """Publish event to Event Bus"""
        try:
            requests.post(
                f"{self.event_bus_url}/publish",
                json={
                    "event_type": event_type,
                    "payload": payload
                },
                timeout=3
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to publish event: {e}")
    
    def log_episode(self, episode: Dict):
        """Log mission episode to Context Vault"""
        episodes_file = self.epos_root / "context_vault" / "missions" / "EPISODES.jsonl"
        
        with open(episodes_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(episode) + '\n')
    
    def log_to_context_vault(self, namespace: str, data: Dict):
        """Write data to Context Vault namespace"""
        vault_dir = self.epos_root / "context_vault" / namespace
        vault_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{data.get('type', 'entry')}_{timestamp}.json"
        
        vault_file = vault_dir / file_name
        vault_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    async def run(self):
        """Start JARVIS bridge service"""
        self.logger.info("=" * 60)
        self.logger.info("🤖 JARVIS Bridge Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"EPOS Root: {self.epos_root}")
        self.logger.info(f"Agent Zero Root: {self.az_root}")
        self.logger.info(f"Event Bus: {self.event_bus_url}")
        self.logger.info("")
        
        # Connect to Event Bus
        await self.connect_event_bus()

def main():
    """CLI entry point"""
    import sys
    
    epos_root = Path(os.getenv("EPOS_ROOT", Path.cwd()))
    az_root = Path(os.getenv("AGENT_ZERO_ROOT", Path.cwd().parent / "agent-zero"))
    
    if len(sys.argv) > 1:
        epos_root = Path(sys.argv[1])
    if len(sys.argv) > 2:
        az_root = Path(sys.argv[2])
    
    bridge = JARVISBridge(epos_root, az_root)
    asyncio.run(bridge.run())

if __name__ == "__main__":
    main()
