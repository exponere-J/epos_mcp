# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/engine\autonomy.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: C:\Users\Jamie\workspace\epos_mcp\engine\autonomy.py

import time
import sys
from pathlib import Path

# Constitutional Imports
try:
    from stasis import StasisEngine
except ImportError:
    print("❌ CRITICAL: stasis.py not found in engine/ or PYTHONPATH not set.")
    sys.exit(1)

def autonomous_loop():
    """
    The Heartbeat of EPOS. 
    Maintains Homeostasis by monitoring the environment and engine purity.
    """
    print("========================================")
    print("   EPOS AUTONOMY: HEARTBEAT ACTIVATED   ")
    print("========================================\n")
    
    stasis = StasisEngine()
    
    while True:
        try:
            # 1. Attempt to achieve stasis (Triage inbox + Run Doctor)
            status = stasis.achieve_stasis()
            
            # 2. Log current state
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] {status}")
            
            # 3. Behavioral Logic
            if status == "STASIS ACHIEVED":
                print("🟢 System Aligned. Engine is Pure. Ready for Missions.")
            elif "PENDING" in status:
                print("🟡 Imbalance Detected. Attempting Homeostatic Correction...")
            else:
                print("🔴 CRITICAL MISALIGNMENT: Manual intervention required.")
                
            # Pulse interval (30 seconds)
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n[!] Heartbeat stopped by Chief Engineer. Standing down.")
            break
        except Exception as e:
            print(f"\n[!] AUTONOMY ERROR: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    autonomous_loop()