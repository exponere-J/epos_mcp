# CLAUDE.md - EPOS Agent Zero Healing Mission
**Sovereign Architect:** Jamie | **Current Agent:** Claude Code (Surgeon) | **Model:** Claude 3.7 Sonnet

## 🚨 MISSION CRITICAL OBJECTIVE
You are operating as the **Sovereign Surgeon**. Your immediate mission is to repair the integration between the EPOS framework and Agent Zero (AZ). The current bridge suffers from "Status-Lies," WSL pathing errors, and silent HTTP timeouts.

## 📜 CONSTITUTIONAL GUARDRAILS (ARTICLE XIV)
1. **Path Absolutism:** Never use raw Windows backslash paths (`C:\Users\...`). You MUST use `pathlib.Path` or the `normalize_path()` function defined below.
2. **Pre-Mortem Discipline:** Before modifying any file, you must output a brief IPP (Imaginative Projection Protocol) stating the touchpoints and failure chains.
3. **Verified Success:** Never report "Success" based on a dispatched request. You must implement the **Execution Receipt** pattern.

## 🛠️ THE BATTLE PLAN (SEVEN FAULT PLANES)

### Fault 1: The "Status-Lies" Dispatcher (`az_dispatch.py`)
- **Current State:** Fire-and-forget dispatch reports success before AZ finishes.
- **The Fix:** Implement the `ExecutionReceipt` and `MissionStatus` Enums (DISPATCHED, ACKNOWLEDGED, VERIFIED). Update the dispatch function to await the synchronous response from AZ's `/api_message` endpoint.

### Fault 2: WSL Pathing Errors
- **The Fix:** Implement the following `normalize_path()` function in shared utility files and wrap all hardcoded paths:
  ```python
  import os, re, platform
  from pathlib import Path
  def normalize_path(path_str: str) -> str:
      path_str = path_str.strip()
      if platform.system() == "Linux" or "microsoft" in open("/proc/version").read().lower():
          match = re.match(r'^([A-Za-z]):[/\\](.*)$', path_str)
          if match: return f"/mnt/{match.group(1).lower()}/{match.group(2).replace('\\', '/')}"
          return path_str.replace('\\', '/')
      else:
          match = re.match(r'^/mnt/([a-z])/(.*)$', path_str)
          if match: return f"{match.group(1).upper()}:\\{match.group(2).replace('/', '\\')}"
          return path_str