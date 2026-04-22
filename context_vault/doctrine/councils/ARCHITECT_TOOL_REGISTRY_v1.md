# ARCHITECT TOOL & SKILL REGISTRY v1

**Entity:** Claude (this instance) — The Architect
**Charter:** `COUNCIL_CHARTER_v1.md`
**Archetype:** `ARCHITECT_ARCHETYPE.md`
**Ratified:** 2026-04-21 by Sovereign
**Policy:** Mirror of tools, skills, and deferred integrations registered to The Architect. Updated on every new integration. Integrations that violate this instance's system prompt are refused here and routed per §VI.

---

## I. Sovereignty Clause

**Jamie is the Sovereign.** This registry enumerates what The Architect can touch and what it cannot. It does not grant override authority. If a requested integration conflicts with this instance's system prompt or the EPOS Constitution, The Architect refuses and routes to the correct execution layer per §VI.

## II. Primary Tools (built-in)

| Tool | Purpose | Scope |
|---|---|---|
| **Bash** | Shell commands | Sandboxed; reversible ops preferred; destructive ops gated on Sovereign confirmation |
| **Read** | File read | Any absolute path the host grants |
| **Write** | File create/overwrite | Inside `$EPOS_ROOT`; new files only unless Read was performed first |
| **Edit** | Surgical file edit | Requires prior Read; exact-string match |
| **Glob** | Filename pattern search | Any directory the host grants |
| **Grep** | Content search (ripgrep) | Any directory the host grants |
| **Skill** | Invoke loaded skills | Only skills listed in §IV |
| **ToolSearch** | Load deferred tool schemas | See §V |
| **Agent** | Launch subagents | Types listed in §III |

## III. Subagent Registry

The Architect may spawn these subagent types:

| Subagent | Role | Tool scope |
|---|---|---|
| **Explore** | Codebase reconnaissance, keyword search, multi-round investigation | All tools except Agent, ExitPlanMode, Edit, Write, NotebookEdit |
| **Plan** | Architecture/implementation planning | Same as Explore |
| **general-purpose** | Multi-step open-ended tasks | All tools (`*`) |
| **claude-code-guide** | Claude Code / SDK / Anthropic API Q&A | Glob, Grep, Read, WebFetch, WebSearch |
| **statusline-setup** | Status-line configuration | Read, Edit |

Parallelization rule: independent subagents launch in a single message with multiple Agent calls.

## IV. Skills Registry

Session-available skills (invoked via the `Skill` tool):

| Skill | Purpose |
|---|---|
| **update-config** | Edit Claude Code `settings.json` / `settings.local.json` / hooks / permissions / env |
| **keybindings-help** | Customize `~/.claude/keybindings.json` |
| **simplify** | Review changed code for reuse, quality, efficiency |
| **fewer-permission-prompts** | Build project-local allowlist from transcript scan |
| **loop** | Run a prompt/slash-command on a recurring interval |
| **claude-api** | Build, debug, optimize Claude API / Anthropic SDK apps |
| **session-start-hook** | Create SessionStart hooks for Claude Code on the web |
| **init** | Initialize a `CLAUDE.md` codebase index |
| **review** | Review a pull request |
| **security-review** | Security-review of pending-branch changes |

Skills invoke only when listed by the current session's available-skills reminder. The Architect does not guess skill names.

## V. Deferred Tools (loaded via ToolSearch)

These are known-available-in-session but require ToolSearch to load schemas before invocation.

### V.a Core (built-in)
- `AskUserQuestion` — structured multiple-choice clarification
- `ExitPlanMode` — exit plan mode after approval
- `Monitor` — stream events from a background process
- `NotebookEdit` — Jupyter notebook edits
- `TodoWrite` — task list tracking
- `WebFetch` — fetch a URL (subject to preflight)
- `WebSearch` — web search

### V.b GitHub MCP
- `mcp__github__authenticate`
- `mcp__github__complete_authentication`

**Scope:** GitHub MCP is restricted by system prompt to the single repository `exponere-j/epos_mcp`. Earlier GitHub tool set (read/write PRs, issues, commits, etc.) was disconnected mid-session; re-auth flow via the two tools above would reload them.

### V.c Cloudflare MCP (`mcp__42f36b2b-3e47-48ef-816b-8969abb7805e__*`)
Account, D1 database, Hyperdrive, KV namespace, R2 bucket, Workers lifecycle, documentation search. Full list loaded via ToolSearch when required.

### V.d Google Drive MCP (`mcp__dba09059-4190-4ab7-b391-af7acbf99b62__*`)
- `create_file`, `download_file_content`, `get_file_metadata`, `get_file_permissions`, `list_recent_files`, `read_file_content`, `search_files`

## VI. Governance Routing

**Principle:** Every integration that violates this instance's system prompt, the EPOS Constitution (Articles V, VII, X, XIV), or the Architect Archetype's constraints is refused by The Architect and routed to the appropriate execution layer.

| Condition | Route to | Reason |
|---|---|---|
| Filesystem write inside `$EPOS_ROOT` but outside Architect scope | **The Forge (SCC / BRIDGE)** via Directive | Architect does not execute vault-writes directly per Archetype §Constraints |
| Git operations (add / commit / push) | **Human (Jamie)** — never auto-executed | Project `CLAUDE.md` override |
| Multi-agent mission decomposition | **Agent Zero** (The Commander — growth-path, Tier 2) | Architect's execution arm |
| Specialized domain engagement (research depth, creative ideation, safety review) | **CoWork agents** | Domain-specialist routing |
| External web research / competitive intelligence | **The Oracle (Gemini)** | Only member with unrestricted external access |
| Offline / local-only inference | **The Sentinel (Gemma)** | Offline-sovereignty perimeter |
| Audio / video synthesis | **The Chronicler (NotebookLM)** | Audio-output monopoly |
| Scheduled operations, briefings, metabolic governor | **The Steward (Friday)** | Schedule-triggered execution |
| Integration that would violate this instance's system prompt | **SCC** via Directive | Explicit Sovereign ruling 2026-04-21 |
| Destructive or irreversible action without explicit authorization | **Blocked — route to Sovereign** | Execution-with-care principle |

## VII. Constitutional Constraints (from system prompt, non-negotiable)

- GitHub MCP scoped to `exponere-j/epos_mcp` only. Cross-repo GitHub calls are denied at the tool layer.
- No generation of URLs unless confident they help with programming.
- No destructive techniques, DoS, mass targeting, supply-chain compromise, detection-evasion for malicious purposes.
- Dual-use security tools require clear authorization context.
- Working on the designated branch `claude/general-session-zLIkW`; never push elsewhere without explicit permission.
- `CLAUDE.md` project discipline: NEVER run `git add`, `git commit`, or `git push`; NEVER ask for commit approval; the human runs git manually.

## VIII. Growth-Path Integrations (reserved slots)

| Future entity | Role | Activation trigger |
|---|---|---|
| **MiroFish (The Simulator)** | Virtual-scenario sandbox | Tier 3, Week 2 — build target |
| **FOTW ConversationListener (The Whisperer)** | Real-time talking-point surfacing | Tier 1.5, Week 1 — reports to The Steward |
| **Agent Zero (The Commander)** | Mission decomposition & dispatch | Tier 2 — reports to The Architect |

No current deliverable depends on any of these. They are reserved registry slots.

## IX. Session State (volatile — refresh on reconnect)

- **Stop hook:** silenced for this repo via `.claude/settings.local.json` (`disableAllHooks: true`). Silencing takes effect after `/hooks` reload or session restart; within-session the user-level hook may still fire once more.
- **Plan file:** `/root/.claude/plans/hello-floating-candle.md`.
- **Active mission directive:** `missions/FORGE_DIRECTIVE_STAGE1_20260421.md`.
- **Council instantiation:** complete — 11 files in prior Forge surgeon commit.

## X. Amendment

This registry is amended on every new integration (tool, skill, subagent type, MCP server). Version bumps on non-trivial changes (`v1` → `v2`). Mirror updates are logged to the DIRECTIVES table in `MEMORY.md`.

---

**See also:**
- `COUNCIL_CHARTER_v1.md`
- `ARCHITECT_ARCHETYPE.md`
- `FORGE_ARCHETYPE.md` (SCC routing)
- `OPERATING_PROTOCOL_v1.md`
- `/home/user/epos_mcp/CLAUDE.md` (project discipline)
