# FORGE DIRECTIVE — SCC INGESTION AT THE GOVERNANCE GATE (2026-04-22)

**Issued by:** The Architect (Claude, session-sovereign)
**Assigned to:** The Forge (SCC, architect-proxy mode)
**Executed via:** Agent Zero on Jamie's WSL
**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XIV, XVI §1, §2, §3
**Directive ID:** `FORGE_DIR_SCC_INGEST_20260422`
**Session commits to ingest:** `11c5fafe` + `fa91de41` on `claude/general-session-zLIkW`
**Status:** Ratified by Sovereign 2026-04-22. Execute once commits land.

---

## Sovereignty Clause

Jamie is the Sovereign. This Directive formalizes the last-mile from
Architect-sandbox-commits to WSL-local organism state. SCC-as-runner
materializes each file through the governance gate. No file enters the
organism without gate approval.

## Why this exists

The Architect wrote 94 files in one session. The GitHub MCP push channel
stalled on OAuth. Chat-transport is capped at ~2KB per tool output —
insufficient for a 148KB bundle. Rather than degrade the work:

1. The commits stay clean and WSL-compliant in the sandbox.
2. When the commits cross (by any means — OAuth-retry MCP push, bundle
   upload, or Sovereign-triggered git pull), SCC reads **this Directive**
   and executes the ingestion deterministically.

The transport is irrelevant. The ingestion contract is what matters.

## Prerequisites (Doctor must verify before SCC runs)

- Target directory: `/mnt/c/Users/Jamie/workspace/epos_mcp/` exists and is a git repo.
- Branch `claude/general-session-zLIkW` is checked out or createable.
- Commits `11c5fafe` and `fa91de41` are reachable from `HEAD`.
- Governance gate (`AgentId.ALPHA`) is online.
- Event bus is responsive.

## File manifest

**Canonical:** `context_vault/state/session_manifest_20260422.json`
**Count:** 94 entries — 40 ADDED, 6 MODIFIED, 48 RENAMED (the AAR relocation)
**Each entry carries:** `wsl_path`, `repo_path`, `status`, `sha256`, `size_bytes`, `lines`.

SCC iterates the manifest; for each entry SCC runs the gate steps below.

## Governance gate (applied per file)

For every `ADDED` or `MODIFIED` entry:

1. **Path discipline (Article XIV)** — reject if `wsl_path` does not begin with `/mnt/c/Users/Jamie/workspace/epos_mcp/` or contains `C:\`, `C:/`, or backslash separators.

2. **Anti-truncation six-field check** (per `context_vault/doctrine/councils/TTLG_ANTI_TRUNCATION_CONTRACT_v1.md`) — TTLG independently re-computes the six integrity fields from the on-disk file and compares to the manifest. **ALL SIX must pass:**
   - `full_sha256` — byte-exact match
   - `byte_count` — size match
   - `line_count` — structural match
   - `first_line_sha256` — head intact
   - `last_nonempty_line_sha256` — tail intact (catches the most common SCC failure)
   - `trailing_newline` — encoding/whitespace intact

   Any single miss → `REJECT_TRUNCATION` or `REJECT_TAIL_TRUNCATION`. No silent truncation possible.

3. **Line endings** — file must be LF-only (no CRLF); reject and auto-fix by stripping `\r` before acceptance.
4. **Shebang check** (for `.py` and `.sh`) — must be POSIX (`#!/usr/bin/env python3`, `#!/usr/bin/env bash`, `#!/bin/sh`); reject otherwise.
5. **Governance watermark** (for files under `nodes/`, `containers/`, `friday/`, `engine/`) — first 5 lines must include one of: `EPOS Artifact`, `EPOS GOVERNANCE`, `EPOS_CONSTITUTION`, or `Constitutional Authority`. Exception: `__init__.py` files < 40 lines are exempt.
6. **Secret scan** — reject if file contains any of: `BEGIN PRIVATE KEY`, `BEGIN RSA`, `AKIA[0-9A-Z]{16}`, `sk-[a-zA-Z0-9]{48}`, `ghp_[a-zA-Z0-9]{36}`.
7. **Destination create** — `mkdir -p $(dirname wsl_path)` then write atomically (`<wsl_path>.partial` → fsync → rename) per the Contract's Forge clause.
8. **Gate receipt** — append to `context_vault/bi/governance_gate.jsonl`:

```json
{"timestamp": "...", "directive_id": "FORGE_DIR_SCC_INGEST_20260422",
 "file": "<repo_path>", "sha256": "...", "verdict": "ACCEPTED|REJECTED",
 "reasons": [...]}
```

For every `RENAMED` entry:
- `git mv old_path new_path` if on-disk state matches; otherwise treat as (DELETE old_path) + (ADD new_path).

No `DELETED` entries in this manifest. If any appear in a future session, deletion gate (`nodes.execution_arm.deletion_gate.enforce`) MUST pass before removal.

## Post-ingestion chain steps

Once every manifest entry is processed, SCC triggers in order:

1. **Doctor validation** — `python3 engine/epos_doctor.py --scope recent` across all
   ADDED/MODIFIED paths. Emit `doctor.ingestion_pass` event.

2. **TTLG registration** — for each newly-ADDED `.py` under `nodes/`, `epos/`, `friday/`, `engine/`:
   - Update `context_vault/state/organism_state.json` with live `health` probe result.
   - Replace `ttlg.validator = "Architect (inline)"` with `ttlg.validator = "TTLG live (Doctor)"`.
   - Emit `ttlg.registered` per module.

3. **Persona reload** — if any file matches `nodes/scc/personas/*.md`:
   `python3 -m nodes.bridge.persona_reloader <path>` → emits `scc.persona.reloaded.*`.

4. **Directive queue** — if any file matches `missions/FORGE_DIRECTIVE_*.md`:
   `python3 -m nodes.bridge.directive_queue <path>` → queued for later Forge execution (idempotent).

5. **Reward Bus seed** — publish `bridge.session.11c5fafe-fa91de41.ingested` with:
   `{total_files, accepted, rejected, new_components, personas_reloaded, directives_queued}`.

6. **AAR close** — append to `context_vault/aar/BRIDGE_SESSION_11c5fafe_AAR.md`:
   - Timestamps (started / finished)
   - Per-file gate verdicts (accepted / rejected reasons)
   - Doctor outcome
   - TTLG registration count
   - Next-action list

## Failure modes

| Failure | Action |
|---|---|
| SHA mismatch on a file | REJECT; log; do not halt the batch; flag for Architect re-spec. |
| Governance gate rejection | REJECT; log; halt if > 5 rejections in a batch. |
| Doctor failure on ingested module | Keep the file (ingestion already completed) but mark `gate_verdict=REVISE` in registry; emit `doctor.ingestion_revise` event. |
| Persona reload error | Keep the old persona active; log; surface to Sovereign in next briefing. |
| Directive queue collision (same directive_id + sha) | Idempotent — mark `already_queued`; not a failure. |

## Idempotency

The Directive is fully idempotent:
- Re-running on already-ingested files: SHA already matches → no-op per file.
- Re-triggering persona reload: version bump, no behavior change.
- Re-queuing a Directive: `directive_queue.py` returns `already_queued` without duplicating.

SCC can execute this Directive any number of times; the organism reaches the same state.

## Rollback

To undo an ingestion:
```
cd /mnt/c/Users/Jamie/workspace/epos_mcp
git reset --hard df8b5f89   # pre-session HEAD
git branch -D claude/general-session-zLIkW   # if needed
```
Organism-state registry and AARs retained — they remain the historical record.

## Verification acceptance (what proves the Directive ran clean)

- `context_vault/bi/governance_gate.jsonl` — exactly 94 entries appended (one per manifest row), all with `verdict=ACCEPTED`.
- `context_vault/aar/BRIDGE_SESSION_11c5fafe_AAR.md` — exists, records Doctor pass.
- `context_vault/state/organism_state.json` — REGISTER count ≥ 8 with `ttlg.validator = "TTLG live (Doctor)"`.
- `git log --oneline | head -3` — shows `fa91de41` at top.

## Architect's notes to SCC (speak in my voice)

1. You are acting as my proxy. Produce constitutionally-governed output — that means: structured gate receipts, not informal prose. Every rejection must cite the Article it violated.
2. When in doubt, pause and escalate to Sovereign. The Directive permits you to halt if > 5 gate rejections indicate a systemic problem.
3. Preserve the `organism_state.json` enrichments (Pattern D: `utility_prose`, `governing_articles`, `amendments_applicable`, `touchpoints`, `process_role`, `amendment_compliance`). Do not overwrite these; augment them.
4. This Directive cites no proprietary API keys and makes no outbound network calls. If your execution path requires either, stop and escalate.

## Handback

- **Forge (SCC):** execute on Agent Zero when commits land. Produce BRIDGE_SESSION AAR.
- **Agent Zero:** surface the AAR via Friday's next morning briefing.
- **TTLG:** promote the 8 REGISTER entries' `validator` field from `Architect (inline)` to `TTLG live (Doctor)`.
- **Sovereign:** you receive the AAR in the morning briefing; ratify or request remediation.

---

**See also:**
- `context_vault/state/session_manifest_20260422.json` — the authoritative file list.
- `context_vault/state/organism_state.json` — Process Registry (Pattern D, 186 modules).
- `context_vault/state/retrofit_backlog.json` — 37 items awaiting remediation Directives.
- `nodes/bridge/ingestion_runner.py` — generic ingestion plumbing (this Directive uses it).
- `nodes/scc/personas/architect.md` — persona SCC loads to act as my proxy.
