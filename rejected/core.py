import json
import sys
import os
from playwright.sync_api import sync_playwright

# Dynamically import platform skills
# Ensure your project root is in PYTHONPATH or run as module
from workers.huntsman.platforms import gumroad

class Huntsman:
    def __init__(self):
        self.name = "Huntsman"
        self.status = "standby"

    def read_intel(self, mission_path):
        """Ingests the mission JSON."""
        if not os.path.exists(mission_path):
            raise FileNotFoundError(f"Intel file not found: {mission_path}")
        with open(mission_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def execute(self, mission_path):
        intel = self.read_intel(mission_path)
        print(f"\n🕷️  [{self.name}] Intel received: {intel['mission_id']}")
        print(f"🎯 Directive: {intel['directive']}")
        
        platforms = intel['parameters']['platforms']
        payload = intel['payload']
        results = {}

        # LAUNCH THE BROWSER (The "Body")
        with sync_playwright() as p:
            # headless=False so you can verify it working visibly
            print(f"⚙️  [{self.name}] Spinnning up Chromium Engine...")
            browser = p.chromium.launch(headless=False) 
            context = browser.new_context()
            
            for platform in platforms:
                print(f"🚀 [{self.name}] Deploying to sector: {platform.upper()}")
                
                try:
                    if platform == 'gumroad':
                        results[platform] = gumroad.deploy(context, payload)
                    # Add elif for lemon_squeezy here later
                    
                    print(f"✅ [{self.name}] {platform} deployment successful.")
                    
                except Exception as e:
                    print(f"❌ [{self.name}] FAILURE in sector {platform}: {e}")
                    results[platform] = {"status": "failed", "error": str(e)}

            browser.close()
            print(f"🏁 [{self.name}] Mission Complete.\n")
            
        return results

if __name__ == "__main__":
    # Usage: python -m workers.huntsman.core missions/active/intel_gumroad_rewardbus.json
    mission_file = sys.argv[1] if len(sys.argv) > 1 else "missions/active/intel_gumroad_rewardbus.json"
    agent = Huntsman()
    agent.execute(mission_file)