# FORGE DIRECTIVE — AZ EXECUTION ARMS (2026-04-21)

**Issued by:** The Architect (Claude)
**Assigned to:** The Forge (Desktop Code) → Agent Zero (executor)
**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §3
**Directive ID:** `FORGE_DIR_AZ_ARMS_20260421`
**Status:** Code written; container rebuild + deployment pending

---

## Sovereign directive (verbatim)

> "build all four agents as an execution arm with shell permissions and capabilities to read and write. Deletion only upon approval. Headed and headless with reasoning that determines when each is necessary. Callable by any component, agent or process in the ecosystem"

## Scope

Deliver four operational variants of the execution arm, selectable by a
reasoning router, guarded by a Sovereign-approved deletion gate, callable
from any component via three surfaces (in-process Python, event bus, REST).

| # | Variant | Purpose |
|---|---|---|
| 1 | `browser_use.headless` | Default web automation; scheduled scrapes, background form fills |
| 2 | `browser_use.headed` | Supervised web flows; CAPTCHA, MFA, Sovereign observability |
| 3 | `computer_use.headless` | Virtual-display OS/desktop ops (via Xvfb :99) |
| 4 | `computer_use.headed` | Real-display OS/desktop ops; Sovereign watching |

## Artifacts delivered (written this session)

| File | Role |
|---|---|
| `nodes/execution_arm/__init__.py` | Package entrypoint — exports `execute`, `select`, `guard`, `health` |
| `nodes/execution_arm/deletion_gate.py` | Sovereign-approval check; refuses unapproved deletions; logs every attempt to `context_vault/bi/deletion_attempts.jsonl` |
| `nodes/execution_arm/mode_selector.py` | Rule-based reasoner picks one of four variants; accepts overrides |
| `nodes/execution_arm/browser_use_arm.py` | BrowserUse arm; both modes behind one class; Xvfb fallback when no display |
| `nodes/execution_arm/computer_use_arm.py` | ComputerUse arm; Anthropic tool loop (computer + bash + str_replace_editor); Xvfb-managed for headless |
| `nodes/execution_arm/callable.py` | Universal `execute()`; sync + async; optional event-bus auto-subscribe |
| `containers/agent-zero/az_bridge.py` | Rewritten — HTTP server on 8105 (`/api/health`, `/api/execute`, `/api/message_async`); event-bus subscriber for `execution.arm.request`; inbox router; tool-bearing missions route to `execute()` |
| `containers/agent-zero/Dockerfile` | Rewritten — Playwright+Chromium, Xvfb, xdotool, scrot, fonts, locales, HEALTHCHECK on `/api/health` |
| `friday/executors/browser_executor.py` | Delegates to `execution_arm.execute`; AZ HTTP fallback |
| `friday/executors/computeruse_executor.py` | Delegates to `execution_arm.execute`; preserves `computeruse_approved` gate |

## Deletion governance (Article XVI §3 compliance)

- **Default:** deny.
- **Explicit approval:** `context["deletion_approved"] = ["/path", "db:key"]`.
- **Blanket override:** `context["deletion_approved"] = "*"` (logged as SEVERE).
- **ComputerUse bash tool:** destructive-pattern heuristic (`rm -rf`, `DROP TABLE`, etc.) triggers `enforce()` before execution.
- **ComputerUse editor tool:** `create`, `str_replace`, `insert` commands treated as deletion of prior state; require approval.
- **BrowserUse:** deletion guard exposed via `deletion_gate.enforce`; arms call it at the destructive step (Gumroad listing removal, record delete, etc.).

Every deletion attempt (approved or denied) is logged to
`context_vault/bi/deletion_attempts.jsonl` for Reward Bus scoring and audit.

## Mode-selection reasoning

Rule-based (deterministic). Inputs: task text + context.

**Arm (browser vs computer):** regex score on URL/browser vs desktop/OS hints.
**Mode (headless vs headed):** `captcha_expected`, `visual_verify`, `scheduled` context flags; then regex on "show me / watch" vs "scheduled / cron / bulk".
**Default:** `browser_use.headless`.
**Overrides:** `mode_hint` accepts `auto`, `headless`, `headed`, arm names,
or full variants (`browser_use.headed`, etc.).

## Universal call surface

```python
# 1. In-process
from nodes.execution_arm import execute
result = execute(task="...", mode_hint="auto", context={...})

# 2. Event bus
bus.publish("execution.arm.request",
            {"task": "...", "mode_hint": "auto", "context": {...},
             "reply_to": "my.custom.topic"})
# listen: "execution.arm.response"

# 3. REST (via AZ bridge)
POST http://agent-zero:8105/api/execute
{ "task": "...", "mode_hint": "auto", "context": {...} }
```

## Verification (Forge must produce these)

Per the TTLG Post-Completion Diagnostic (Scout → Thinker → Gate → Surgeon → Analyst):

1. `docker compose build agent-zero` — image builds clean.
2. `docker compose up -d agent-zero` — container healthy within 30s.
3. `curl http://localhost:${AZ_PORT:-50080}/api/health` — returns JSON with
   `arm_available: true` and per-arm health reporting `operational`.
4. **Four-variant smoke** — POST `/api/execute` four times with hints
   forcing each variant; receipt must show the right `mode` and `arm` and
   `success: true` (or a `headed_fallback` / `mode_warning` note with
   explanation).
5. **Deletion gate test** — POST a task that would delete; without
   `deletion_approved`, result contains `"BLOCKED"` and
   `context_vault/bi/deletion_attempts.jsonl` gains a `"approved": false`
   entry.
6. **Reasoner test** — POST 5 diverse tasks with `mode_hint: "auto"`;
   selection rationale in result matches the intent.
7. **Register to organism state** (per Article XVI §1) — new component
   entry: `agent_zero.execution_arm` with capability tags
   `[web_automation, os_automation, headless, headed, deletion_gated]`.

## Out of scope

- Training-pair generation from run logs (separate QLoRA directive).
- Process Matrix Publisher (separate directive — held pending Sovereign).
- Migrating legacy `nodes/browser_use_node.py` callers (executors already
  point at the new arm; legacy file remains importable for back-compat).

## Rollback

- Revert `containers/agent-zero/Dockerfile` and `az_bridge.py` to prior
  commit; rebuild AZ container. Execution arm package is self-contained
  under `nodes/execution_arm/` — safe to delete in one step if needed.

## Idempotency

The directive is idempotent at the artifact level — re-running the code
writes produces identical files. Docker image rebuild is cacheable.

## Next

- Forge runs verification §1–§7.
- On pass: register to organism state; AAR to `context_vault/aar/`.
- On fail: blocker memo to `context_vault/bi/az_arms/` and Sovereign escalation.
