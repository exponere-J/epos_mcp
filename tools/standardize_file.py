#!/usr/bin/env python3
# File: C:/Users/Jamie/workspace/epos_mcp/tools\standardize_file.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
"""
FILE: /tools/standardize_file.py
PROJECT: EPOS Dev Crew
AUTH: Article XIV / Autonomous Squad
DESCRIPTION: Mechanical enforcement of Absolute Path Headers for zero-shot agent context.
"""

import os
import sys
from pathlib import Path

def inject_header(file_path: str):
    target = Path(file_path).resolve()
    
    if not target.exists():
        print(f"❌ Error: File {target} does not exist.")
        return False

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if header already exists
    if "FILE:" in content and "AUTH: Article XIV" in content:
        print(f"✅ {target.name} is already standardized.")
        return True

    # Construct the header
    header = f""""""
    # For Python/Bash files, use appropriate comment blocks instead of HTML comments
    if target.suffix == '.py':
        header = f'"""\nFILE: {target}\nPROJECT: EPOS Dev Crew\nAUTH: Article XIV / Autonomous Squad\nDESCRIPTION: Constitutional enforcement component\n"""\n'
    elif target.suffix == '.sh':
        header = f'# FILE: {target}\n# PROJECT: EPOS Dev Crew\n# AUTH: Article XIV / Autonomous Squad\n# DESCRIPTION: Constitutional enforcement component\n'

    # Write the standardized file
    with open(target, 'w', encoding='utf-8') as f:
        f.write(header + content)
    
    print(f"🔧 Standardized: {target}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/standardize_file.py <file_path>")
        sys.exit(1)
    
    for arg in sys.argv[1:]:
        inject_header(arg)