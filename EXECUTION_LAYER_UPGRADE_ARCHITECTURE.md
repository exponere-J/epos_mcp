# EPOS Execution Layer Upgrade — Complete Gap Closure Architecture
## Date: April 6, 2026 | Authority: Jamie Purdue
## Target: 30/100 Execution -> 88/100 in one focused session

## FIVE-GAP INVENTORY
1. BrowserUse: Wrong package name. Fix: `pip install browser-use` (with hyphen)
2. Agent Zero: Docker container not running. Fix: docker compose up -d
3. Friday: No scheduler, no delegation. Fix: APScheduler + Event Reactor
4. Claude Code: 0/100 between sessions by design. Fix: daemon artifacts that persist
5. ComputerUse: Available via MCP but not wired. Fix: mission type registration

## CRITICAL PATH
1. Install browser-use (one command)
2. Deploy Agent Zero Docker container
3. Build APScheduler heartbeat for Friday
4. Build Event Reactor daemon (tail JSONL, dispatch on pattern match)
5. Wire ComputerUse to M1 Publisher for immediate content publishing
6. Wrap daemon as Windows Service via NSSM for persistence

## KEY INSIGHT
BrowserUse = autonomous path (runs without Claude session)
ComputerUse = on-demand path (requires active Claude session)
Both serve the organism. Not alternatives — primary and fallback.

## CONSTITUTIONAL RULE
No feature ships without a run trigger. Every CODE session produces the feature AND its scheduler entry.

*1% daily. 37x annually.*
