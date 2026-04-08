#!/usr/bin/env python3
import yaml
import subprocess
import os
from datetime import datetime

class EPOSMissionControl:
    def __init__(self):
        self.registry_path = "agent_registry.yaml"
        self.logs_dir = "logs/missions"
        os.makedirs(self.logs_dir, exist_ok=True)
        self.load_registry()
    
    def load_registry(self):
        if os.path.exists(self.registry_path):
            self.registry = yaml.safe_load(open(self.registry_path))
        else:
            self.registry = {"agents": {}}
    
    def activate_az_tool(self):
        """Resume epos_az container on-demand"""
        subprocess.run(["docker", "start", "epos_az_paused"], 
                      capture_output=True)
        print("🔧 Agent Zero activated: http://localhost:50080")
        return "http://localhost:50080"
    
    def park_az_tool(self):
        """Park AZ when mission complete"""
        subprocess.run(["docker", "stop", "epos_az_paused"], 
                      capture_output=True)
        print("🛑 Agent Zero parked")
    
    def execute_mission(self, mission_name, payload):
        endpoint = self.activate_az_tool()
        
        log_file = f"{self.logs_dir}/{mission_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        print(f"🚀 EPOS Mission '{mission_name}' → Agent Zero")
        print(f"📝 Log: {log_file}")
        print(f"📂 Context: codebase at /epos")
        
        # Simulate AZ API call (replace with real curl when UI ready)
        print("✅ Mission dispatched. Monitor logs.")
        
        self.park_az_tool()
        return log_file

if __name__ == "__main__":
    control = EPOSMissionControl()
    control.execute_mission("epos_system_assessment", 
                           {"codebase": "/epos", "agents": "phi3_marl"})
EOF