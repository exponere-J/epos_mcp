# SQUAD COMMUNICATION PROTOCOL
**Official Language & Message Format for EPOS Agent Coordination**

**Authority:** EPOS_UNIFIED_NERVOUS_SYSTEM.md, EPOS_CONSTITUTION_v3.1.md Article VIII (Unified Nervous System)

---

## Preamble

EPOS agents (Scout, FOTW, Content Lab, Friday) communicate **exclusively through:**

1. **Immutable JSONL event logs** (`context_vault/events/system_events.jsonl`)
2. **File-based artifacts** (scout_output.json, ambient_log.jsonl, etc.)
3. **Dispatch messages** written to Friday's inbox (`friday_orchestrator/logs/friday_inbox.jsonl`)

Agents **do NOT**:
- Make direct function calls to each other
- Share mutable state via shared Python variables
- Send HTTP requests to each other (no inter-agent REST)
- Use stdout for coordination (only logging)

This protocol ensures:
- **Auditability**: Every message is timestamped and immutable
- **Replayability**: Friday can reconstruct the full conversation from logs
- **Decoupling**: Agents can be deployed, replaced, or scaled independently
- **Governance Compliance**: Every message is subject to Article XIV audit

---

## PART 1: EVENT TAXONOMY

All agents append events to `context_vault/events/system_events.jsonl` using **standardized event types**:

### Event Type: `ttlg.scout.started`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:30:00Z",
  "agent": "Scout",
  "event_type": "ttlg.scout.started",
  "severity": "info",
  "payload": {
    "targets": ["governance_gate", "context_vault"],
    "intensity": "light",
    "timeout_seconds": 3600,
    "model_alias": "scout_default"
  }
}
```

### Event Type: `ttlg.scout.completed`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:45:30Z",
  "agent": "Scout",
  "event_type": "ttlg.scout.completed",
  "severity": "info",
  "payload": {
    "findings_count": 12,
    "findings_severity": {
      "critical": 1,
      "high": 3,
      "medium": 5,
      "low": 3
    },
    "output_file": "context_vault/scans/scan_20260311_083000/scout_output.json",
    "overall_health": "degraded",
    "duration_seconds": 930
  }
}
```

### Event Type: `fotw.capture.started`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:45:31Z",
  "agent": "FOTW",
  "event_type": "fotw.capture.started",
  "severity": "info",
  "payload": {
    "target_scan": "scan_20260311_083000",
    "capture_sources": ["scout_output", "logs", "decision_context"]
  }
}
```

### Event Type: `fotw.capture.completed`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:46:15Z",
  "agent": "FOTW",
  "event_type": "fotw.capture.completed",
  "severity": "info",
  "payload": {
    "ambient_log_file": "context_vault/agent_logs/fotw_captures/scan_20260311_083000/ambient_log.jsonl",
    "context_entries": 47,
    "friction_signals_detected": 3,
    "sentiment_summary": "User concerned about governance violations"
  }
}
```

### Event Type: `contentlab.synthesis.started`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:46:16Z",
  "agent": "ContentLab",
  "event_type": "contentlab.synthesis.started",
  "severity": "info",
  "payload": {
    "node_id": "governance_impact_analyzer_v1",
    "input_files": [
      "context_vault/scans/scan_20260311_083000/scout_output.json",
      "context_vault/agent_logs/fotw_captures/scan_20260311_083000/ambient_log.jsonl"
    ]
  }
}
```

### Event Type: `contentlab.synthesis.completed`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:47:30Z",
  "agent": "ContentLab",
  "event_type": "contentlab.synthesis.completed",
  "severity": "info",
  "payload": {
    "node_id": "governance_impact_analyzer_v1",
    "output_file": "context_vault/mission_data/content_lab_output_scan_20260311_083000_governance_analyzer.md",
    "synthesis_quality": "high",
    "research_asset_created": true
  }
}
```

### Event Type: `friday.loop_check`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:47:31Z",
  "agent": "Friday",
  "event_type": "friday.loop_check",
  "severity": "info",
  "payload": {
    "scout_complete": true,
    "fotw_complete": true,
    "contentlab_complete": true,
    "loop_status": "complete",
    "loop_health": "healthy"
  }
}
```

### Event Type: `friday.loop_degradation`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:46:20Z",
  "agent": "Friday",
  "event_type": "friday.loop_degradation",
  "severity": "warning",
  "payload": {
    "missing_component": "fotw",
    "scout_complete": true,
    "fotw_complete": false,
    "contentlab_complete": false,
    "reason": "FOTW timeout after 120 seconds",
    "recovery_action": "Continue with degraded FOTW capture"
  }
}
```

### Event Type: `governance.violation_detected`

```json
{
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:32:00Z",
  "agent": "governance_gate_audit.py",
  "event_type": "governance.violation_detected",
  "severity": "critical",
  "payload": {
    "violation_code": "HARDCODED_MODEL_LITERAL",
    "violation_description": "Found direct model string instead of env alias",
    "violating_file": "api/ttlg_systems_light_scout.py:45",
    "article_violated": "XIV",
    "required_action": "Resubmit with env alias"
  }
}
```

---

## PART 2: DISPATCH MESSAGES (Friday's Inbox)

When agents need to **signal Friday urgently**, they write to:

```
friday_orchestrator/logs/friday_inbox.jsonl
```

### Message Format: DISPATCH

Used when an agent completes critical work and needs Friday's attention:

```json
{
  "message_id": "msg_20260311_084730",
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:47:30Z",
  "agent": "Scout",
  "message_type": "DISPATCH",
  "priority": "normal|high|critical",
  "subject": "Scout cycle complete for governance_gate target",
  "body": {
    "action_required": "Read scan_state.json and proceed to next phase",
    "output_location": "context_vault/scans/scan_20260311_083000/scout_output.json",
    "findings": {
      "critical": 1,
      "high": 3
    }
  },
  "response_deadline": "2026-03-11T09:00:00Z"
}
```

### Message Format: REPORT

Used when an agent has status to share but doesn't require immediate action:

```json
{
  "message_id": "msg_20260311_084800",
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:48:00Z",
  "agent": "FOTW",
  "message_type": "REPORT",
  "subject": "Ambient capture summary for scan_20260311_083000",
  "body": {
    "context_entries_captured": 47,
    "friction_signals": [
      "User concerned about path resolution errors (3 mentions)",
      "Environment variable missing (2 mentions)",
      "Model routing fallback (1 mention)"
    ],
    "recommendation": "Synthesize around these friction points in Content Lab"
  }
}
```

### Message Format: ESCALATION

Used when an agent encounters a failure it cannot resolve:

```json
{
  "message_id": "msg_20260311_085000",
  "trace_id": "trace-abc123",
  "scan_id": "scan_20260311_083000",
  "timestamp": "2026-03-11T08:50:00Z",
  "agent": "Scout",
  "message_type": "ESCALATION",
  "severity": "critical",
  "subject": "Scout failure: Cannot reach OpenRouter API",
  "body": {
    "error": "Connection timeout to https://openrouter.ai/api/v1",
    "attempted_retries": 3,
    "recommendation": "Check OPENROUTER_API_KEY in .env, verify network connectivity",
    "proposed_action": "Friday should mark loop as FAILED and create incident report"
  },
  "requires_human_review": true
}
```

---

## PART 3: PROTOCOL RULES FOR AGENTS

### Rule 1: Immutability

- All events in `system_events.jsonl` are **write-once, never edited**
- If an event is wrong, append a **compensating event**, not a correction
- Friday reconstructs the full state by replaying all events

Example of correcting a wrong event:

```json
// Original (wrong) event:
{"event_type": "ttlg.scout.completed", "findings_count": 12, ...}

// Compensating event (appended, not replacing):
{"event_type": "correction", "original_event_id": "msg_...", "new_findings_count": 15, ...}
```

### Rule 2: Atomic Writes with Filelock

When appending to shared JSONL files, **always use filelock**:

```python
from filelock import FileLock
import json

def send_event(event: dict, log_path: str = "context_vault/events/system_events.jsonl"):
    lock = FileLock(f"{log_path}.lock")
    with lock:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
```

### Rule 3: Deterministic Trace & Scan IDs

Every agent must use the same `trace_id` and `scan_id` throughout a single diagnostic cycle:

```python
# At Scout startup:
trace_id = str(uuid.uuid4())  # Generated once at cycle start
scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# All subsequent agents inherit these:
# FOTW uses the same trace_id and scan_id
# Content Lab uses the same trace_id and scan_id
# Friday aggregates using trace_id as the join key
```

### Rule 4: No Direct Agent-to-Agent Calls

**FORBIDDEN:**
```python
# ❌ WRONG: Agent calling another agent directly
from api import ttlg_scout
result = ttlg_scout.run(targets)  # Violates decoupling
```

**REQUIRED:**
```python
# ✅ CORRECT: Agent publishes event, Friday coordinates
send_event({
    "event_type": "ttlg.scout.started",
    "trace_id": trace_id,
    "scan_id": scan_id,
    ...
})
# Friday waits for completion event, then triggers next phase
```

### Rule 5: Standard JSON Schema Validation

Before appending any event, validate the schema:

```python
def validate_event(event: dict) -> bool:
    required_fields = ["trace_id", "scan_id", "timestamp", "agent", "event_type", "severity"]
    for field in required_fields:
        assert field in event, f"Missing required field: {field}"
    
    valid_severities = ["debug", "info", "warning", "error", "critical"]
    assert event["severity"] in valid_severities, f"Invalid severity: {event['severity']}"
    
    return True
```

---

## PART 4: FRIDAY'S COORDINATION LOGIC

Friday reads from **three inputs** to orchestrate the loop:

### Input 1: System Events Log

```python
def read_system_events(scan_id: str) -> list:
    """Read all events for a scan, in order"""
    with open("context_vault/events/system_events.jsonl", "r") as f:
        events = [json.loads(line) for line in f]
    return [e for e in events if e["scan_id"] == scan_id]
```

### Input 2: Dispatch Messages Inbox

```python
def read_inbox(scan_id: str) -> list:
    """Read all dispatches, reports, escalations for a scan"""
    with open("friday_orchestrator/logs/friday_inbox.jsonl", "r") as f:
        messages = [json.loads(line) for line in f]
    return [m for m in messages if m["scan_id"] == scan_id]
```

### Input 3: File Artifacts

```python
def check_artifacts(scan_id: str) -> dict:
    """Check if expected output files exist"""
    return {
        "scout_output": Path(f"context_vault/scans/{scan_id}/scout_output.json").exists(),
        "ambient_log": Path(f"context_vault/agent_logs/fotw_captures/{scan_id}/ambient_log.jsonl").exists(),
        "contentlab_asset": Path(f"context_vault/mission_data/content_lab_output_{scan_id}*.md").exists(),
    }
```

### Friday's Decision Logic

```python
def orchestrate_loop(scan_id: str) -> str:
    """Determine loop status and next action"""
    events = read_system_events(scan_id)
    messages = read_inbox(scan_id)
    artifacts = check_artifacts(scan_id)
    
    scout_done = any(e["event_type"] == "ttlg.scout.completed" for e in events)
    fotw_done = any(e["event_type"] == "fotw.capture.completed" for e in events)
    contentlab_done = any(e["event_type"] == "contentlab.synthesis.completed" for e in events)
    
    escalations = [m for m in messages if m["message_type"] == "ESCALATION"]
    
    if escalations:
        return "LOOP_FAILED"  # Critical error, human review needed
    elif scout_done and fotw_done and contentlab_done:
        return "LOOP_COMPLETE"  # All phases succeeded
    elif scout_done and fotw_done:
        return "WAITING_FOR_CONTENTLAB"  # Content Lab still running
    elif scout_done:
        return "WAITING_FOR_FOTW"  # FOTW should start
    else:
        return "WAITING_FOR_SCOUT"  # Scout should have started
```

---

## PART 5: TROUBLESHOOTING & RECOVERY

### Scenario: Message Never Arrives

```
Symptom: Friday expected a dispatch but it never came

Cause: Agent crashed or network issue

Recovery:
1. Friday checks system_events.jsonl for the agent's last event
2. If "started" but no "completed", Friday escalates to "LOOP_DEGRADATION"
3. Human review required to restart the failed agent
```

### Scenario: Corrupted JSONL Line

```
Symptom: json.loads() fails because a line is truncated

Cause: Two agents appended simultaneously without filelock

Recovery:
1. governance_gate_audit.py detects and logs the corruption
2. Friday marks the scan as "CORRUPTED_STATE"
3. Scan must be restarted from scratch (immutability violated)

Prevention:
- Always use filelock before appending to shared JSONL files
```

### Scenario: Circular Dependency

```
Symptom: Agent A waits for Agent B, Agent B waits for Agent A

Cause: Misconfigured orchestration logic

Prevention:
- Protocol enforces strict ordering: Scout → FOTW → Content Lab → Friday Summary
- Agents cannot declare dependencies on later phases
```

---

## References

- **EPOS_UNIFIED_NERVOUS_SYSTEM.md** — System event taxonomy
- **IPP_TEMPLATE.md** — Communication protocols enforced by IPP Step 1 (Touchpoints)
- **AAR_TEMPLATE.md** — How pattern learning is communicated through AAR
- **EPOS_CONSTITUTION_v3.1.md** — Article VIII (Unified Nervous System)
- **friday_pattern_library.json** — Friday's memory of communication patterns

---

**Last Updated:** 2026-03-11
**Constitutional Authority:** Article VIII, EPOS Constitution v3.1
**Next Evolution:** GOVERNANCE_GATE_CHARTER.md (Hard-stop rules for DISPATCH/REPORT/ESCALATION)
