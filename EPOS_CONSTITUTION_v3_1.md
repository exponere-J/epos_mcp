\# EPOS CONSTITUTION v3.1

\## The Law Governing Agentic Operating System Sovereignty

\### Unified Framework: Pre-Mortem Discipline + Context Governance



\*\*Ratified:\*\* 2026-01-25  

\*\*Authority:\*\* EXPONERE Founder Jamie  

\*\*Supersedes:\*\* EPOS\_CONSTITUTION\_v3.0 (Everest), EPOS\_CONSTITUTION\_v3.0 (Context)  

\*\*Purpose:\*\* Unified governance preventing architectural drift AND enabling unlimited context scaling



---



\## PREAMBLE: THE EVEREST PRINCIPLE



\*"We are climbing Everest, laying the governance that will keep our agentic OS on the road as we climb."\*



This Constitution exists because \*\*architectural misalignment is more dangerous than bugs\*\*. Bugs crash systems; misalignment causes systemic drift, silent failures, and compound workarounds.



EPOS operates under \*\*Pre-Mortem Discipline\*\*: we imagine failure before building, weigh multi-layered consequences before executing, and validate alignment before deployment.



\*\*Dual Mandate:\*\*

1\. \*\*Prevent drift\*\* through constitutional enforcement (Pre-Mortem Framework)

2\. \*\*Enable scale\*\* through context orchestration (RLM Integration)



\*\*Core Philosophy:\*\*

\- Design foresight > Reactive debugging

\- Constitutional frameworks > Ad-hoc solutions

\- Imaginative projection > Trial-and-error iteration

\- Operational sovereignty > Vendor dependency

\- Symbolic context > Token limitations



---



\## Article I: Foundational Principles



\### The Pre-Mortem Mandate



\*\*Before ANY code is written, component is added, or architecture is changed:\*\*



1\. \*\*Imaginative Projection\*\*: Play out 3-5 failure scenarios mentally

2\. \*\*Consequence Mapping\*\*: Document downstream effects of each decision

3\. \*\*Alignment Validation\*\*: Verify compatibility with existing components

4\. \*\*Recovery Planning\*\*: Define rollback procedures

5\. \*\*Success Criteria\*\*: Establish verifiable outcomes



\*\*Violation of this mandate results in immediate rejection by Governance Gate.\*\*



---



\### The Five Constitutional Documents



All EPOS operations require these documents at root:



1\. \*\*`ENVIRONMENT\_SPEC.md`\*\*: Environment canon (shells, Python, paths, services)

2\. \*\*`COMPONENT\_INTERACTION\_MATRIX.md`\*\*: Component dependencies, inputs, outputs, failure modes

3\. \*\*`FAILURE\_SCENARIOS.md`\*\*: Pre-imagined failures with recovery procedures

4\. \*\*`PATH\_CLARITY\_RULES.md`\*\*: Single source of truth for path handling

5\. \*\*`PRE\_FLIGHT\_CHECKLIST.md`\*\*: Step-by-step validation protocol



\*\*These documents are LAW. Code is ENFORCEMENT.\*\*



---



\### The Sovereignty Covenant



EPOS maintains complete operational control through:



\- \*\*Data Sovereignty\*\*: All operational data on local disk, no cloud dependencies

\- \*\*Vendor Replaceability\*\*: External services must be swappable without core functionality loss

\- \*\*Rollback Capability\*\*: All operations must be reversible

\- \*\*Integration Boundaries\*\*: Clear contracts defining what external agents can/cannot do

\- \*\*Constitutional Supremacy\*\*: No code overrides constitutional requirements

\- \*\*Context Sovereignty\*\*: Local context storage, symbolic access, no vendor lock-in



---



\## Article II: Hard Boundaries (Non-Negotiable)



\### Rule 1: Path Absolutism

\*\*Every file path MUST use Windows-style absolute paths in code.\*\*



```python

\# CORRECT

from pathlib import Path

EPOS\_ROOT = Path("C:/Users/Jamie/workspace/epos\_mcp")

mission\_file = EPOS\_ROOT / "engine" / "missions" / "mission\_001.json"



\# WRONG - Ambiguous

mission\_file = "missions/mission\_001.json"  # Relative to what?

```



\*\*Reason\*\*: Prevents path mixing (`C:\\` vs `/c/`), shell confusion, silent failures.



---



\### Rule 2: No Silent Failures

\*\*All file I/O operations MUST log and validate.\*\*



```python

\# CORRECT

log\_path = EPOS\_ROOT / "logs" / "mission\_001.log"

try:

&nbsp;   log\_path.write\_text(log\_data)

&nbsp;   logger.info(f"Log written: {log\_path}")

&nbsp;   assert log\_path.exists(), "Log file not created"

except Exception as e:

&nbsp;   logger.error(f"Log write failed: {e}")

&nbsp;   raise



\# WRONG

log\_path.write\_text(log\_data)  # Silent failure if disk full

```



\*\*Reason\*\*: Prevents "logged vs executed" confusion, ensures audit trail.



---



\### Rule 3: Environment Explicitness

\*\*Python version and environment MUST be validated before execution.\*\*



```python

\# CORRECT - In all entrypoints

import sys

from dotenv import load\_dotenv



REQUIRED\_PYTHON = (3, 11)

if sys.version\_info\[:2] < REQUIRED\_PYTHON:

&nbsp;   raise EnvironmentError(f"Python {REQUIRED\_PYTHON\[0]}.{REQUIRED\_PYTHON\[1]}+ required")



load\_dotenv(Path(\_\_file\_\_).parent / ".env")

```



\*\*Violations\*\*:

\- ❌ Assuming Python version

\- ❌ Not calling `load\_dotenv()`

\- ❌ Using `shell=True` without path validation



---



\### Rule 4: Separation of Concerns

\*\*Logging ≠ Execution. Status reports MUST reflect actual work done.\*\*



```python

\# CORRECT

def execute\_mission(mission\_id):

&nbsp;   logger.info(f"Starting mission {mission\_id}")

&nbsp;   

&nbsp;   result = agent\_zero.run(mission\_id)

&nbsp;   

&nbsp;   if result.success:

&nbsp;       logger.info(f"Mission {mission\_id} COMPLETED")

&nbsp;       return {"status": "executed", "proof": result.output\_path}

&nbsp;   else:

&nbsp;       logger.error(f"Mission {mission\_id} FAILED: {result.error}")

&nbsp;       return {"status": "failed", "error": result.error}



\# WRONG

def execute\_mission(mission\_id):

&nbsp;   logger.info(f"Executing mission {mission\_id}")

&nbsp;   return {"status": "executed"}  # LIE - nothing happened

```



---



\### Rule 5: No Destructive Defaults

\*\*Destructive operations require explicit confirmation.\*\*



\*\*Blocked without confirmation\*\*:

\- File deletion (`rm -rf`, `del /s`)

\- Disk operations (`format`, `diskpart`)

\- System commands (`shutdown`, `reboot`)

\- Overwriting files without backup



\*\*Implementation\*\*: Command allowlist in `engine/command\_validator.py`



---



\### Rule 6: Configuration Explicitness

\*\*All configuration MUST be loaded explicitly via `python-dotenv`.\*\*



```python

\# CORRECT - At entrypoint

from dotenv import load\_dotenv

from pathlib import Path



env\_path = Path(\_\_file\_\_).parent / ".env"

load\_dotenv(env\_path)



\# WRONG - Assumes auto-loading

import os

agent\_path = os.getenv("AGENT\_ZERO\_PATH")  # May be None

```



\*\*Violation symptom\*\*: "It worked yesterday" (environment drift)



---



\### Rule 7: Context Vault Mandate (NEW)

\*\*Data exceeding 8,192 tokens MUST use Context Vault, not inline.\*\*



```python

\# CORRECT - Large data in vault

mission = {

&nbsp;   "mission\_id": "analysis-001",

&nbsp;   "objective": "Analyze Q1-Q4 2025 market data",

&nbsp;   "context\_vault\_path": "context\_vault/market\_data/2025\_full.txt",

&nbsp;   "success\_criteria": \["Insights extracted via symbolic search"]

}



\# WRONG - Inline data > 8K tokens

mission = {

&nbsp;   "mission\_id": "analysis-001",

&nbsp;   "data": "\[... 50,000 tokens of data ...]"  # VIOLATION

}

```



\*\*Reason\*\*: Prevents token overflow, enables RLM scaling, maintains governance.



---



\## Article III: Quality Gates



\### Pre-Flight Validation

\*\*Before ANY execution, `epos\_doctor.py` MUST pass:\*\*



```bash

python epos\_doctor.py

\# Exit code 0: Proceed

\# Exit code 1: Fix issues, re-validate

```



\*\*10 Critical Checks:\*\*

1\. ✅ Python 3.11.x confirmed

2\. ✅ EPOS root exists and accessible

3\. ✅ Agent Zero path valid

4\. ✅ Required directories present (engine/, logs/, inbox/, context\_vault/)

5\. ✅ Ollama service running on :11434

6\. ✅ `.env` loaded successfully

7\. ✅ All dependencies installed (`pip check`)

8\. ✅ Port 8001 available

9\. ✅ Log directories writable

10\. ✅ Constitutional documents present



---



\### Schema Validation

\*\*All mission JSONs MUST validate against `EPOSAgentMission` schema.\*\*



```python

from agent\_mission\_spec import EPOSAgentMission



mission = EPOSAgentMission(\*\*json\_data)

mission.validate()  # Raises ValidationError if invalid

```



\*\*Required fields\*\*:

\- `mission\_id` (UUID)

\- `objective` (clear statement)

\- `constraints` (environment, paths, risk level)

\- `success\_criteria` (verifiable outcomes)

\- `failure\_modes` (pre-imagined scenarios)

\- `context\_vault\_path` (optional, required if data > 8K tokens)



---



\### Governance Gate Triage

\*\*All code enters via `/inbox`, triaged by `governance\_gate.py`:\*\*



\*\*Promoted to `/engine`\*\* if:

\- ✅ Passes constitutional checks (no violations of Article II)

\- ✅ Includes absolute path header

\- ✅ Has pre-mortem analysis (if component)

\- ✅ Validates against schema (if mission)



\*\*Rejected to `/quarantine`\*\* if:

\- ❌ Constitutional violations detected

\- ❌ Missing required fields

\- ❌ Security risks identified



\*\*Educational receipt provided\*\* with:

\- Specific violations

\- Remediation steps

\- Constitutional references



---



\## Article IX: Enforcement



\### Immediate Rejection



\*\*Violations of Article II (Hard Boundaries) result in:\*\*



1\. Immediate execution halt

2\. Governance Gate rejection

3\. Educational receipt generated

4\. No execution until fixed



\*\*Non-negotiable violations:\*\*

\- Path ambiguity

\- Silent failures

\- Missing environment validation

\- Status lies (logged ≠ executed)

\- Destructive operations without confirmation

\- Configuration assumptions

\- Inline data > 8K tokens



---



\### Monitoring \& Alerts



\*\*Continuous validation via:\*\*



1\. \*\*Health Checks\*\*: `/health` endpoint every 60s

2\. \*\*Log Analysis\*\*: Daily scan for constitutional violations

3\. \*\*Metric Tracking\*\*: Compliance rate, rejection rate, pivot frequency, context vault usage

4\. \*\*Alert Thresholds\*\*:

&nbsp;  - Compliance < 95% → Warning

&nbsp;  - Compliance < 85% → System review required

&nbsp;  - 3+ violations in 24h → Architecture audit

&nbsp;  - Context vault file > 100MB → Optimization review



---



\### Compliance Metrics



\*\*Tracked in `compliance\_report.json`:\*\*



```json

{

&nbsp; "date": "2026-01-25",

&nbsp; "total\_submissions": 47,

&nbsp; "promoted": 42,

&nbsp; "rejected": 5,

&nbsp; "compliance\_rate": 0.89,

&nbsp; "top\_violations": \[

&nbsp;   {"rule": "Article II, Rule 1", "count": 3},

&nbsp;   {"rule": "Article VII, Rule 7", "count": 2}

&nbsp; ],

&nbsp; "context\_vault\_usage": {

&nbsp;   "missions\_using\_vault": 12,

&nbsp;   "avg\_vault\_size\_mb": 1.2,

&nbsp;   "total\_symbolic\_queries": 157

&nbsp; }

}

```



\*\*Target\*\*: 95%+ compliance rate



---



\## Article X: Vendor Integration Framework



\### External Agent Contracts



\*\*All external agents (Agent Zero, Claude Code, Abacus) MUST:\*\*



1\. Operate within defined sandboxes

2\. Report status explicitly (no silent failures)

3\. Provide rollback mechanisms

4\. Respect data sovereignty (local-only)

5\. Accept governance boundaries

6\. Use Context Vault for large data (no inline)



\*\*Example: Agent Zero Contract\*\*



```yaml

vendor: Agent Zero

version: 1.0

sandbox: C:\\Users\\Jamie\\workspace\\agent-zero

permissions:

&nbsp; - read: C:\\Users\\Jamie\\epos\_workspace

&nbsp; - write: C:\\Users\\Jamie\\epos\_workspace\\outputs

&nbsp; - execute: python, git, npm

data\_flow: local\_only

reporting: structured\_json

rollback: git\_reset

context\_access: vault\_symbolic\_only  # NEW

```



---



\### Integration Boundaries



\*\*What external agents CAN do:\*\*

\- Execute tasks within sandbox

\- Read/write to designated workspace

\- Report structured results

\- Query Context Vault symbolically



\*\*What external agents CANNOT do:\*\*

\- Modify EPOS core (`/engine`)

\- Change constitutional files

\- Access other vendor sandboxes

\- Make irreversible changes

\- Execute without governance approval

\- Load full vault files into context (symbolic only)



---



\## Article XI: Emergency Procedures



\### Stasis Mode



\*\*Trigger stasis if:\*\*

\- Compliance rate < 75%

\- Critical constitutional violation detected

\- Vendor agent goes rogue

\- Data sovereignty breach

\- Context vault corruption detected



\*\*Stasis protocol:\*\*

1\. Halt all autonomous operations

2\. Snapshot current state

3\. Generate diagnostic report

4\. Human intervention required

5\. Root cause analysis before resuming



\*\*File\*\*: `engine/stasis.py`



---



\### Rollback Authority



\*\*Any operation can be rolled back within 24 hours:\*\*



```bash

\# Rollback mission

python engine/rollback.py --mission mission\_001



\# Rollback component

python engine/rollback.py --component research\_node



\# Full system rollback

python engine/rollback.py --snapshot snapshot\_20260125



\# Rollback context vault file

python engine/rollback.py --vault context\_vault/mission\_data/corrupted.txt

```



\*\*Retention\*\*: 30 days of rollback snapshots



---



\### Constitutional Override



\*\*Emergency override (human-only):\*\*



```bash

\# Bypass governance gate (requires justification)

python governance\_gate.py --override --reason "critical\_bug\_fix"



\# Skip pre-flight (requires approval)

python meta\_orchestrator.py --skip-doctor --approved-by Jamie



\# Emergency context vault bypass (temporary)

python execution\_bridge.py --allow-inline-context --emergency --approved-by Jamie

```



\*\*Logging\*\*: All overrides logged to `override\_log.json` with justification



---



\## APPENDIX A: Glossary



\- \*\*Pre-Mortem\*\*: Imagining failure before building

\- \*\*Constitutional Document\*\*: One of the 5 foundational governance files

\- \*\*Governance Gate\*\*: Validation system for code/mission submissions

\- \*\*Educational Receipt\*\*: Rejection notice with specific fix guidance

\- \*\*Pivot Cooldown\*\*: 72-hour period before architectural changes allowed

\- \*\*Data Sovereignty\*\*: All operational data on local disk

\- \*\*Vendor Replaceability\*\*: Ability to swap external services without loss

\- \*\*Stasis Mode\*\*: Emergency halt of autonomous operations

\- \*\*Context Vault\*\*: Local storage for large datasets (>8K tokens)

\- \*\*Symbolic Search\*\*: RLM pattern-based context retrieval without full load

\- \*\*RLM\*\*: Recursive Language Model (context scaling technique)



---



\## APPENDIX B: Quick Reference



\*\*Before writing code:\*\*

1\. Read relevant constitutional articles

2\. Document 3-5 failure scenarios

3\. Update Component Interaction Matrix

4\. Run `python epos\_doctor.py`

5\. Determine if Context Vault needed (data > 8K tokens)



\*\*Before deploying:\*\*

1\. Submit to Governance Gate

2\. Pass pre-flight checks

3\. Verify constitutional compliance

4\. Create rollback snapshot

5\. Validate context vault paths (if used)



\*\*When things break:\*\*

1\. Check `logs/\*.log`

2\. Run `python epos\_doctor.py`

3\. Consult `FAILURE\_SCENARIOS.md`

4\. Execute recovery procedure

5\. Check context vault integrity (if used)



---



\## APPENDIX C: Failure Mode Cross-Reference



\### Pre-Mortem Framework Failures (FS-PM)

\- \*\*FS-PM01\*\*: Path mixing (Article II, Rule 1)

\- \*\*FS-PM02\*\*: Silent file I/O (Article II, Rule 2)

\- \*\*FS-PM03\*\*: Environment drift (Article II, Rule 3)

\- \*\*FS-PM04\*\*: Status lies (Article II, Rule 4)

\- \*\*FS-PM05\*\*: Destructive defaults (Article II, Rule 5)

\- \*\*FS-PM06\*\*: Config assumptions (Article II, Rule 6)



\### Context Vault Failures (FS-CV)

\- \*\*FS-CV01\*\*: Vault file missing (Article VII, Section 4)

\- \*\*FS-CV02\*\*: Invalid vault path (Article VII, Section 4)

\- \*\*FS-CV03\*\*: Vault size exceeded (Article VII, Section 4)

\- \*\*FS-CV04\*\*: Invalid regex pattern (Article VII, Section 2)

\- \*\*FS-CV05\*\*: Inline data > 8K tokens (Article II, Rule 7)



---



\*\*END OF CONSTITUTION\*\*



\*Ratified 2026-01-25 by EXPONERE Founder Jamie\*  

\*Next Review: 2026-02-25 (30 days)\*  

\*Version: 3.1.0 (Unified Framework)\*

