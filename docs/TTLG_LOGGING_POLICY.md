# TTLG Logging Policy
<!-- File: C:\Users\Jamie\workspace\epos\TTLG_LOGGING_POLICY.md -->

**Document authority:** EPOS Constitution v3.1 · TTLG Model & Routing Charter v1.0  
**Steward:** Jamie  
**Audience:** Claude Code, Friday (Gemini), all phase agents

---

## Why This Policy Exists

Logging is the audit trail. It is how you know the system did what it said it did. It is how Friday detects drift. It is how Jamie sees what happened without reading raw code. It is how every failure is traceable to its cause.

A system that logs inconsistently has silent failures waiting to happen. This policy removes all ambiguity about what gets logged, where, in what format, and by whom.

---

## Logging Architecture

Every TTLG run produces logs in two places:

**1. Run log** — `vault/runs/{run_id}/run.log`  
A structured, append-only log of everything that happened during this run. Written by the Logger module. Every phase agent writes to this file. Friday writes to this file. Every entry has a timestamp, component, phase, and message.

**2. Artifact files** — `vault/runs/{run_id}/*.json`  
The structured outputs of each phase. These are not logs — they are deliverables. But they serve a logging function: their existence proves a phase completed. See TTLG_SYSTEMS_CYCLE.md and TTLG_MARKET_CYCLE.md for artifact schemas.

**3. Failure log** — `vault/failures/FailureArtifact_{timestamp}.json`  
Every failure, every time, immediately. Never deleted. This is the constitutional requirement from Article II of the EPOS Constitution: no silent failures.

**4. Friday decision log** — `vault/runs/{run_id}/FridayDecision_{timestamp}.json`  
Every routing and oversight decision Friday makes. Written before the triggered action executes.

---

## Logger Module — Required Implementation

Every `.py` file in TTLG must use the shared Logger module. No `print()` statements in production code.

```python
# File: C:\Users\Jamie\workspace\epos\core\logger.py

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import os

class TTLGLogger:
    """
    Structured logger for TTLG. Writes to both console (rich-formatted)
    and to vault/runs/{run_id}/run.log (JSON-lines format).
    
    Every log entry is structured and includes: timestamp, level, component,
    run_id, phase, and message. No unstructured log entries.
    """
    
    def __init__(self, component: str, run_id: str, phase: Optional[int] = None):
        self.component = component
        self.run_id = run_id
        self.phase = phase
        self.vault_root = Path(os.environ["EPOS_ROOT"]) / "vault"
        self.run_log_path = self.vault_root / "runs" / run_id / "run.log"
        self.run_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _write(self, level: str, message: str, extra: Optional[dict] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "component": self.component,
            "run_id": self.run_id,
            "phase": self.phase,
            "message": message,
        }
        if extra:
            entry["extra"] = extra
        
        # Write to run.log
        with open(self.run_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Write to console (rich formatting optional)
        print(f"[{entry['timestamp']}] [{level}] [{self.component}] {message}")
    
    def info(self, message: str, extra: Optional[dict] = None):
        self._write("INFO", message, extra)
    
    def warn(self, message: str, extra: Optional[dict] = None):
        self._write("WARN", message, extra)
    
    def error(self, message: str, extra: Optional[dict] = None):
        self._write("ERROR", message, extra)
    
    def critical(self, message: str, extra: Optional[dict] = None):
        self._write("CRITICAL", message, extra)
    
    def phase_start(self):
        self.info(f"Phase {self.phase} started", extra={"event": "phase_start"})
    
    def phase_complete(self, artifact_path: str):
        self.info(f"Phase {self.phase} complete", extra={
            "event": "phase_complete",
            "artifact": artifact_path
        })
    
    def phase_halt(self, reason: str):
        self.error(f"Phase {self.phase} halted", extra={
            "event": "phase_halt",
            "reason": reason
        })
```

---

## What Gets Logged — By Component

### All Phase Agents (Scout, Thinker, Surgeon, Analyst, Legacy — both cycles)

Every phase agent must log the following events, in this order:

| Event | Log Level | Message format | Required extra fields |
|-------|-----------|----------------|-----------------------|
| Phase start | INFO | `"Phase {n} started"` | `event: "phase_start"` |
| Input artifact received | INFO | `"Input artifact loaded: {artifact_name}"` | `artifact_path, artifact_size_bytes` |
| Model call initiated | INFO | `"Model call initiated"` | `model, prompt_tokens_estimate` |
| Model call complete | INFO | `"Model call complete"` | `model, response_tokens_estimate, duration_seconds` |
| Model call retry | WARN | `"Model call retry {attempt} of {max}"` | `attempt, max, error_message` |
| Model call failure (all retries exhausted) | ERROR | `"Model call failed after {n} retries"` | `attempts, last_error` |
| Output artifact written | INFO | `"Output artifact written: {artifact_name}"` | `artifact_path` |
| Output artifact confirmed on disk | INFO | `"Output artifact confirmed: {artifact_name}"` | `artifact_path, exists: true` |
| Phase complete | INFO | `"Phase {n} complete"` | `event: "phase_complete", artifact_path` |
| Phase halt | ERROR | `"Phase {n} halted: {reason}"` | `event: "phase_halt", reason, failure_artifact_path` |

### Governance Gate

| Event | Log Level | Message format | Required extra fields |
|-------|-----------|----------------|-----------------------|
| Gate opened | INFO | `"Governance Gate opened"` | `run_id, cycle, heal_list_item_count` |
| Item reviewed | INFO | `"Governance item reviewed"` | `item_id, status (approved/rejected/deferred)` |
| Gate submitted | INFO | `"Governance Gate submitted"` | `approved_count, rejected_count, deferred_count` |
| Empty approval — clean halt | INFO | `"Governance Gate: zero approvals — clean halt"` | `event: "clean_halt", reason: "all_rejected_or_deferred"` |
| Gate artifact written | INFO | `"Approved list written"` | `artifact_path` |

### Friday (Gemini 1.5 Flash)

| Event | Log Level | Message format | Required extra fields |
|-------|-----------|----------------|-----------------------|
| Vault read initiated | INFO | `"Friday: vault read initiated"` | `artifacts_to_read: list` |
| Vault read complete | INFO | `"Friday: vault read complete"` | `artifacts_read: integer, total_tokens_estimate` |
| Decision made | INFO | `"Friday: decision made"` | `decision_type, decision_id` |
| Decision artifact written | INFO | `"Friday: FridayDecision written"` | `artifact_path` |
| Phase triggered | INFO | `"Friday: triggering phase {n}"` | `cycle, phase, agent, model` |
| Escalation raised | WARN | `"Friday: escalating to Jamie"` | `reason, escalation_type, artifacts_consulted` |
| Cross-cycle correlation detected | INFO | `"Friday: cross-cycle correlation detected"` | `correlation_type, description` |
| Scheduled review complete | INFO | `"Friday: scheduled vault review complete"` | `vault_summary_path` |

### Model Client (API calls via OpenRouter or Gemini)

| Event | Log Level | Message format | Required extra fields |
|-------|-----------|----------------|-----------------------|
| API call initiated | INFO | `"API call: {model}"` | `model, run_id, component, phase` |
| API call success | INFO | `"API call success: {model}"` | `duration_seconds, response_length` |
| API call retry | WARN | `"API retry {n}/{max}: {model}"` | `attempt, max, status_code, error_message` |
| API call failure | ERROR | `"API failure after {n} retries: {model}"` | `attempts, status_code, last_error, failure_artifact_path` |

### epos_doctor.py

| Event | Log Level | Message format | Required extra fields |
|-------|-----------|----------------|-----------------------|
| Check started | INFO | `"epos_doctor: check started"` | `check_name` |
| Check passed | INFO | `"epos_doctor: PASS - {check_name}"` | `check_name, details` |
| Check failed | ERROR | `"epos_doctor: FAIL - {check_name}"` | `check_name, failure_reason` |
| All checks passed | INFO | `"epos_doctor: all checks passed — environment clean"` | `total_checks, duration_seconds` |
| Checks failed — halt | CRITICAL | `"epos_doctor: {n} checks failed — halting"` | `failed_checks: list` |

---

## Failure Artifact — Required on Every Error

Every error in the system — API timeout, missing file, governance violation, path error — must produce a `FailureArtifact` written to `vault/failures/` before the exception is raised.

**Filename:** `FailureArtifact_{component}_{timestamp}.json`

```json
{
  "failure_id": "string — FA-{YYYYMMDD}-{sequence}",
  "run_id": "string",
  "component": "string — Scout | Thinker | Governance | Surgeon | Analyst | Legacy | Friday | ModelClient | epos_doctor",
  "phase": "integer or null",
  "cycle": "A | B | null",
  "error_type": "string — named exception class",
  "error_message": "string — exact error message",
  "failed_at": "ISO 8601 timestamp",
  "payload_snapshot": "object or null — relevant context at time of failure",
  "stack_trace": "string or null — Python traceback if available",
  "resolution_required": "boolean — true if human action needed"
}
```

**Failure artifacts are never deleted.** They are the permanent record of what went wrong. Friday reads them during scheduled vault reviews to detect systemic issues.

---

## Log Entry Format — JSON Lines

All entries in `vault/runs/{run_id}/run.log` are JSON Lines format (one JSON object per line, no commas between lines):

```
{"timestamp":"2026-03-01T14:32:00.123Z","level":"INFO","component":"Scout","run_id":"20260301_143158_a3b7c","phase":1,"message":"Phase 1 started","extra":{"event":"phase_start"}}
{"timestamp":"2026-03-01T14:32:01.456Z","level":"INFO","component":"Scout","run_id":"20260301_143158_a3b7c","phase":1,"message":"Input artifact loaded: target_directory","extra":{"artifact_path":"C:\\Users\\Jamie\\workspace\\target","artifact_size_bytes":204800}}
{"timestamp":"2026-03-01T14:34:22.789Z","level":"INFO","component":"Scout","run_id":"20260301_143158_a3b7c","phase":1,"message":"Output artifact written: Scout_Map.json","extra":{"artifact_path":"C:\\Users\\Jamie\\workspace\\epos\\vault\\runs\\20260301_143158_a3b7c\\Scout_Map.json"}}
```

This format is machine-readable by Friday and human-readable with `cat run.log | python -m json.tool | head -50`.

---

## What Is NOT Logged

To keep logs useful and scannable:

- Do not log the full content of model responses — log token counts and artifact paths only
- Do not log raw API request bodies — log model name, component, and duration
- Do not log sensitive values from `.env` — log key names only (never API key values)
- Do not log intermediate computation steps within a model prompt — log phase start, model call, and phase complete only

---

## Log Retention Policy

| Log type | Retention | Location |
|----------|-----------|----------|
| `run.log` per run | Permanent — never deleted | `vault/runs/{run_id}/run.log` |
| `FailureArtifact` | Permanent — never deleted | `vault/failures/` |
| `FridayDecision` | Permanent — never deleted | `vault/runs/{run_id}/` |
| Phase artifacts (Scout_Map, Heal_List, etc.) | Permanent — never deleted | `vault/runs/{run_id}/` |
| `FridayVaultSummary` | Permanent — never deleted | `vault/` |

No log is ever deleted. Disk space is managed by archiving old runs to cold storage after 90 days (manual process, Jamie decides when).

---

## Drift Detection — How Logging Prevents It

Friday's scheduled vault review reads all `run.log` files since the last review and checks for:

1. **Missing phase_complete events** — a phase_start with no corresponding phase_complete indicates a stalled run
2. **Repeated error_type values** — the same `error_type` appearing in 3+ `FailureArtifact` files indicates a systemic issue
3. **Model call retry patterns** — frequent retries on the same model indicate API degradation or model availability issues
4. **Governance Gate clean_halt frequency** — repeated zero-approval gates on the same system indicate scope or communication problems

When Friday detects any of these, it writes a `cross_cycle_correlation` or `pattern_alert` `FridayDecision` and escalates to Jamie.

---

*Last updated: 2026-03-01 · Authority: TTLG Model & Routing Charter v1.0*
