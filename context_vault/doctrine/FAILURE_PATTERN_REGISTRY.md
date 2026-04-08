# EPOS Failure Pattern Registry
## Constitutional Authority: EPOS Constitution v3.1
## Evidence base: Screenshot analysis 2026-03-30

Every failure pattern below was observed in production sessions. Each has a detection method and a prevention step that maps to the Sprint Checklist.

---

## FP-001: Port Assumption Mismatch
**Evidence**: Browser hit port 8200, service ran on 3001/8000
**Root cause**: Code assumed one port, script assumed another, neither verified
**Detection**: `curl -s localhost:PORT` before opening browser
**Prevention**: Checklist item "Ports verified" in Section A
**Cost when missed**: Session restart + debugging time

## FP-002: Wrong File Type in Execution Context
**Evidence**: Python docstring placed at top of Dockerfile
**Root cause**: File content not reviewed before being passed to Docker
**Detection**: Read first line of every generated file before execution
**Prevention**: Checklist item "For each MODIFY file: read it first"
**Cost when missed**: Build failure + context switch to diagnose

## FP-003: Service Name Mismatch (Hyphen vs Underscore)
**Evidence**: docker-compose had `event_bus`, script called `event-bus`
**Root cause**: Docker is literal — no fuzzy matching on service names
**Detection**: `docker compose config --services` before startup
**Prevention**: Checklist pre-mortem "Failure mode: service name mismatch"
**Cost when missed**: Service silently not started + cascade failures

## FP-004: Health Check Before Service Ready
**Evidence**: Health check at :8100 timed out because container never started
**Root cause**: Check fired without verifying container was running
**Detection**: `docker ps | grep SERVICE` before hitting health endpoint
**Prevention**: Startup scripts must verify container state before health check
**Cost when missed**: False "service down" diagnosis

## FP-005: Unicode Smart Quote Encoding
**Evidence**: PowerShell `TerminatorExpectedAtEndOfString` at line 321
**Root cause**: Smart quotes from document copy-paste, not plain ASCII quotes
**Detection**: `grep -P "[\x{2018}-\x{201F}]" SCRIPT` before execution
**Prevention**: All scripts generated in editors with smart quotes disabled
**Cost when missed**: Script completely non-functional, repeated failed runs

## FP-006: Same Error Run Multiple Times Without Inspection
**Evidence**: PowerShell activation script run 3 times with same error
**Root cause**: Retry without reading the error message or inspecting the file
**Detection**: Human discipline — read error before retry
**Prevention**: Checklist Section B: "Each change records command + expected + actual"
**Cost when missed**: N * (time per failed run) with zero information gain

## FP-007: Import Path Assumption
**Evidence**: `from epos_doctor import EPOSDoctor` fails — file is in engine/
**Root cause**: Import path assumed without verifying module location
**Detection**: `find . -name "MODULE.py"` before writing import
**Prevention**: Checklist "For each dependency: verify import chain resolves"
**Cost when missed**: ImportError at runtime, blocks all downstream code

## FP-008: fcntl Unix-Only Module on Windows
**Evidence**: `import fcntl` crashes on Windows — Unix-only
**Root cause**: Platform-specific code without conditional import
**Detection**: `python -c "import MODULE"` on target platform before deploy
**Prevention**: All system-level imports wrapped in try/except with fallback
**Cost when missed**: Module completely non-importable on Windows

## FP-009: Code Execution at Import Time
**Evidence**: `EPOSDoctor().run()` on import line blocks all module imports
**Root cause**: Side effects in module-level code
**Detection**: `py_compile` catches syntax but not runtime import behavior
**Prevention**: Never execute logic at module level — defer to __main__ or function call
**Cost when missed**: Entire module chain blocked from importing

## FP-010: Backslash in Python Docstring as Unicode Escape
**Evidence**: `C:\Users` in docstring parsed as `\U` unicode escape
**Root cause**: Windows paths with backslashes in triple-quoted strings
**Detection**: `py_compile` catches this as SyntaxError
**Prevention**: Always use forward slashes in docstrings and comments
**Cost when missed**: SyntaxError, module completely non-importable

## FP-011: Diverged Duplicate Files
**Evidence**: 7 files existed at both root and engine/ with different content
**Root cause**: Files copied to new location without removing original
**Detection**: `epos_doctor.py` duplicate check
**Prevention**: When creating canonical version, immediately delete or deprecate old version
**Cost when missed**: Wrong version imported depending on sys.path order

## FP-012: Version Gate Too Strict
**Evidence**: `sys.version_info[:2] < (3, 11)` blocks Python 3.12+
**Root cause**: Exact version match instead of minimum version
**Detection**: Test with actual Python version on target system
**Prevention**: Use `>=` not `==` for version checks
**Cost when missed**: Working Python blocked, all code fails to start

---

## How to Use This Registry

1. Before each sprint: review FP-001 through FP-012
2. In Section A pre-mortem: cite the FP number for each anticipated failure
3. When a new failure pattern is discovered: add it here with evidence
4. EVL1 weekly review: check if any FP was triggered this week
