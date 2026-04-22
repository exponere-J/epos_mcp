# `nodes.execution_arm` — EPOS Execution Arm

Four operational variants, one interface, one governance surface.

```
browser_use.headless    browser_use.headed
computer_use.headless   computer_use.headed
```

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §3

---

## Quick start

```python
from nodes.execution_arm import execute

# Auto mode — reasoner picks the variant
result = execute(task="Scrape top Gumroad products for 'prompt engineering'")

# Force a specific variant
result = execute(
    task="Log into LinkedIn and publish the scheduled post",
    mode_hint="browser_use.headed",
    context={"mission_id": "post-001"},
)

# Authorize deletion
result = execute(
    task="Archive last month's invoices in Wave",
    mode_hint="computer_use.headless",
    context={
        "mission_id": "archive-42",
        "deletion_approved": ["wave:invoice:2026-03-*"],
    },
)
```

Result shape:
```json
{
  "success": true,
  "arm": "browser_use",
  "mode": "headless",
  "task": "...",
  "output": "...",
  "selection": {"arm": "...", "mode": "...", "reason": "...", "confidence": 0.7},
  "started_at": "...", "finished_at": "...",
  "mission_id": "..."
}
```

## Mode selection

| Signal | Chooses |
|---|---|
| Task mentions "URL / browser / gmail / linkedin / form / login" | `browser_use` |
| Task mentions "desktop / finder / terminal / cross-app" | `computer_use` |
| Task mentions "show me / watch / visually verify / screencast" | `headed` |
| `context.captcha_expected=True` or `visual_verify=True` | `headed` |
| `context.scheduled=True` and Sovereign not active | `headless` |
| Task mentions "scheduled / cron / bulk / ci / scrape" | `headless` |
| Default | `browser_use.headless` |

## Deletion gate

**Hard rule:** `Deletion only upon approval.`

- Arms call `deletion_gate.enforce(target, context)` at every destructive step.
- Approval via `context["deletion_approved"]`:
  - `["/path/a", "db:users/42"]` — explicit targets.
  - `"*"` — blanket (logged SEVERE).
- Every attempt (approved or blocked) logged to
  `context_vault/bi/deletion_attempts.jsonl`.

ComputerUse bash tool applies a destructive-pattern heuristic to raw
commands (`rm -rf`, `DROP TABLE`, `docker rm`, `dd of=...`, etc.) and
gates them before execution.

## Callable from anywhere

### 1. In-process Python
```python
from nodes.execution_arm import execute
```

### 2. Event bus
```python
bus.publish("execution.arm.request",
            {"task": "...", "mode_hint": "auto",
             "context": {...}, "reply_to": "my.topic"})
# listen for "execution.arm.response"
```

### 3. REST (Agent Zero bridge)
```bash
curl -X POST http://agent-zero:8105/api/execute \
     -H "Content-Type: application/json" \
     -d '{"task": "...", "mode_hint": "auto"}'
```

## Headed on a headless host

ComputerUse auto-starts Xvfb on `:99` when no DISPLAY is set. BrowserUse
headed does the same when `xvfb-run`/`Xvfb` is on PATH; otherwise it
falls back to headless and annotates the receipt with
`"headed_fallback": "...reason..."`.

## Health

```python
from nodes.execution_arm import health
h = health()
# {"browser_use": {...}, "computer_use": {...}, "timestamp": "..."}
```

## Environment

| Variable | Effect |
|---|---|
| `ANTHROPIC_API_KEY` | Required for ComputerUse arm |
| `GROQ_API_KEY` | BrowserUse LLM backend (preferred) |
| `OLLAMA_HOST` | BrowserUse LLM fallback |
| `COMPUTER_USE_MODEL` | Override computer-use model (default `claude-opus-4-7`) |
| `COMPUTER_USE_WIDTH`, `COMPUTER_USE_HEIGHT` | Display size for computer tool |
| `EPOS_XVFB_DISPLAY` | Virtual display name (default `:99`) |
| `EPOS_ARM_LOG_DIR` | Arm-level run logs |
| `EPOS_DELETION_LOG` | Deletion attempts log |
| `EPOS_ARM_AUTOSUBSCRIBE` | `0` to disable event-bus auto-subscribe |

## Governance

- Every arm run appends a JSON line to `context_vault/execution_arm/<arm>.jsonl`.
- Every deletion attempt appends to `context_vault/bi/deletion_attempts.jsonl`.
- Organism-state registration is performed by the TTLG Post-Completion
  Diagnostic after the Forge Directive's verification block passes.
