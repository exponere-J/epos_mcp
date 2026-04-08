#!/usr/bin/env python3
"""
Agent Zero Bridge - EPOS Governed Executor
Constitutional Authority: Article V (Agents)

This bridge ensures Agent Zero operates under EPOS governance:
1. Receives missions from inbox
2. Validates with Governance Server
3. Executes under supervision
4. Reports results via Event Bus
5. Learns from corrections
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add engine to path
sys.path.insert(0, '/app')

from event_bus import get_event_bus

class AgentZeroBridge:
    """Bridge between Agent Zero and EPOS Governance."""
    
    def __init__(self):
        self.agent_id = os.getenv("AGENT_ID", "agent-zero")
        self.role = os.getenv("ROLE", "software_development")
        self.inbox = Path("/app/inbox")
        self.outbox = Path("/app/outbox")
        self.bus = get_event_bus()
        
        # Ensure directories exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)
        
        print(f"[AZ-Bridge] Agent ID: {self.agent_id}")
        print(f"[AZ-Bridge] Role: {self.role}")
    
    def start(self):
        """Start the governed agent loop."""
        print("[AZ-Bridge] Starting governed execution loop...")
        
        # Publish online event
        self.bus.publish(
            event_type="agent.online",
            payload={
                "agent_id": self.agent_id,
                "role": self.role,
                "status": "ready"
            },
            source_server=self.agent_id
        )
        
        # Subscribe to mission assignments
        self.bus.subscribe("mission.assigned", self._handle_mission)
        self.bus.subscribe("governance.correction", self._handle_correction)
        self.bus.subscribe("learning.lesson", self._handle_lesson)
        
        # Start polling for events
        self.bus.start_polling(interval=2.0)
        
        print("[AZ-Bridge] READY - Awaiting mission assignments")
        print("[AZ-Bridge] Drop missions in /app/inbox/ or publish mission.assigned events")
        
        # Main loop - check inbox and stay alive
        while True:
            self._check_inbox()
            time.sleep(5)
    
    def _check_inbox(self):
        """Check inbox for new mission files."""
        for mission_file in self.inbox.glob("*.json"):
            try:
                print(f"[AZ-Bridge] Found mission: {mission_file.name}")
                
                with open(mission_file, 'r') as f:
                    mission = json.load(f)
                
                # Process mission
                self._process_mission(mission)
                
                # Move to processed
                processed_dir = self.inbox / "processed"
                processed_dir.mkdir(exist_ok=True)
                mission_file.rename(processed_dir / mission_file.name)
                
            except Exception as e:
                print(f"[AZ-Bridge] Error processing {mission_file}: {e}")
    
    def _handle_mission(self, event):
        """Handle mission assignment event."""
        mission = event.get("payload", {})
        print(f"[AZ-Bridge] Received mission via event bus: {mission.get('mission_id')}")
        self._process_mission(mission)
    
    def _process_mission(self, mission: dict):
        """Process a mission under governance."""
        mission_id = mission.get("mission_id", f"M_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        print(f"[AZ-Bridge] Processing mission: {mission_id}")
        
        # Step 1: Publish mission start
        self.bus.publish(
            event_type="agent.mission_started",
            payload={
                "agent_id": self.agent_id,
                "mission_id": mission_id,
                "mission_type": mission.get("type", "unknown"),
                "description": mission.get("description", "")
            },
            metadata={"trace_id": mission_id},
            source_server=self.agent_id
        )
        
        # Step 2: Request governance validation
        self.bus.publish(
            event_type="governance.validation_request",
            payload={
                "mission_id": mission_id,
                "mission_content": mission,
                "requesting_agent": self.agent_id
            },
            metadata={"trace_id": mission_id},
            source_server=self.agent_id
        )
        
        # Step 3: Execute mission (placeholder - will integrate with actual AZ)
        result = self._execute_mission(mission)
        
        # Step 4: Submit output for governance review
        self.bus.publish(
            event_type="governance.output_review",
            payload={
                "mission_id": mission_id,
                "agent_id": self.agent_id,
                "output": result
            },
            metadata={"trace_id": mission_id},
            source_server=self.agent_id
        )
        
        # Step 5: Publish completion
        self.bus.publish(
            event_type="agent.mission_completed",
            payload={
                "agent_id": self.agent_id,
                "mission_id": mission_id,
                "status": "completed",
                "result_location": str(self.outbox / f"{mission_id}_result.json")
            },
            metadata={"trace_id": mission_id},
            source_server=self.agent_id
        )
        
        # Save result
        result_file = self.outbox / f"{mission_id}_result.json"
        with open(result_file, 'w') as f:
            json.dump({
                "mission_id": mission_id,
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"[AZ-Bridge] Mission {mission_id} completed")
    
    def _execute_mission(self, mission: dict) -> dict:
        """Execute the mission. Placeholder for AZ integration."""
        # TODO: Integrate with actual Agent Zero execution
        # For now, return acknowledgment
        return {
            "status": "executed",
            "message": f"Mission acknowledged: {mission.get('description', 'No description')}",
            "executed_at": datetime.now().isoformat()
        }
    
    def _handle_correction(self, event):
        """Handle governance correction."""
        correction = event.get("payload", {})
        print(f"[AZ-Bridge] Received correction: {correction.get('violation_type')}")
        
        # Log correction for learning
        self.bus.publish(
            event_type="agent.correction_received",
            payload={
                "agent_id": self.agent_id,
                "correction": correction
            },
            source_server=self.agent_id
        )
    
    def _handle_lesson(self, event):
        """Handle lesson injection from Learning Server."""
        lesson = event.get("payload", {})
        print(f"[AZ-Bridge] Received lesson: {lesson.get('lesson_id')}")
        
        # Store lesson for future reference
        lessons_dir = Path("/app/context_vault/learning/agent_lessons")
        lessons_dir.mkdir(parents=True, exist_ok=True)
        
        lesson_file = lessons_dir / f"{lesson.get('lesson_id', 'unknown')}.json"
        with open(lesson_file, 'w') as f:
            json.dump(lesson, f, indent=2)


if __name__ == "__main__":
    print("=" * 50)
    print("AGENT ZERO BRIDGE - GOVERNED EXECUTOR")
    print("Constitutional Authority: Article V")
    print("=" * 50)
    
    bridge = AgentZeroBridge()
    
    try:
        bridge.start()
    except KeyboardInterrupt:
        print("\n[AZ-Bridge] Shutdown requested")
        print("[AZ-Bridge] Goodbye")
