# File: C:\Users\Jamie\workspace\epos_mcp\epos_snapshot.py
import os
from pathlib import Path
import datetime

def generate_snapshot():
    root = Path.cwd()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_file = f"epos_snapshot_{timestamp}.txt"
    
    print(f"🔍 Generating EPOS Snapshot: {snapshot_file}")
    
    with open(snapshot_file, "w", encoding="utf-8") as f:
        f.write(f"EPOS CODEBASE SNAPSHOT - {timestamp}\n")
        f.write("="*40 + "\n\n")
        
        for path in sorted(root.rglob("*")):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            
            if path.is_file():
                f.write(f"FILE: {path.relative_to(root)}\n")
                
                # Scan for misalignment vectors
                try:
                    content = path.read_text(errors='ignore')
                    if "C:/" in content or "C:\\" in content:
                        f.write("  ⚠️ VECTOR: Hardcoded Absolute Path detected\n")
                    if "from " in content and ".py" not in path.name:
                        # Simple check for potential import silos
                        pass 
                except:
                    f.write("  ⚠️ VECTOR: Unreadable/Binary file\n")
                f.write("-" * 20 + "\n")

    print("✅ Snapshot complete. Review for misalignment vectors.")

if __name__ == "__main__":
    generate_snapshot()