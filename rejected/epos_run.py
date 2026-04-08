from epos_planner import plan
from epos_computeruse import execute_plan

import sys

if len(sys.argv) < 2:
    print("Usage: python epos_run.py \"task description\"")
    exit()

task = " ".join(sys.argv[1:])
print("\n🧬 EPOS.Local.ComputerUse online")
print(f"Planning: {task}\n")

p = plan(task)
print("Generated plan:")
print(p)

confirm = input("\nExecute plan? [y/N] ").lower().strip()
if confirm != "y":
    print("Aborted.")
    exit()

execute_plan(p)
print("\n✔ Mission complete.\n")
