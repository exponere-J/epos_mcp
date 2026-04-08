# EPOS Dev Crew — Autonomous Healing Architecture

> **Project Type:** Isolated Agentic Squad  
> **Sovereign Architect:** Jamie  
> **Status:** Bootstrap Phase  
> **Constitutional Authority:** Article XIV / IPP Protocol

---

## What This Is

A self-contained, document-driven multi-agent development crew that treats the EPOS codebase as a **living organism**. Six specialized agents operate within a closed feedback loop, orchestrated by Friday, executing the TTLG (Through the Looking Glass) healing cycle without manual intervention.

This is not a build project. It is an **agentic onboarding** — the crew learns from every cycle and gets faster.

---

## Topology

```
┌──────────────────────────────────────────────────────┐
│                  FRIDAY (Orchestrator)                │
│         Reads: decision_journal, pattern_library      │
│         Writes: scan_state, dispatch commands          │
│         Role: OBSERVER + DISPATCHER                    │
├──────────────┬───────────┬───────────┬───────────────┤
│              │           │           │               │
▼              ▼           ▼           ▼               ▼
┌──────┐  ┌────────┐  ┌───────┐  ┌──────────┐  ┌──────────┐
│Archit│  │Systems │  │Surgeon│  │  Market  │  │ Content  │
│ ect  │  │ Scout  │  │(CC)   │  │  Scout   │  │   Lab    │
└──┬───┘  └───┬────┘  └──┬────┘  └────┬─────┘  └────┬─────┘
   │          │           │            │              │
   ▼          ▼           ▼            ▼              ▼
 IPP       findings     repairs     market_        synthesis
 check      .json       + AAR      signals         assets
   │          │           │            │              │
   └──────────┴─────┬─────┴────────────┴──────────────┘
                    ▼
            context_vault/  (Common Memory)
```

---

## Agent Roster

| Agent | File | Role | Access |
|---|---|---|---|
| **Architect** | `.claude/agents/architect.md` | Constitutional Compliance, IPP gating | READ: constitution, governance logs |
| **Systems Scout** | `.claude/agents/systems_scout.md` | TTLG diagnostic scans | WRITE: findings/, scan_state/ |
| **Surgeon** | `.claude/agents/surgeon.md` | Code healing, surgical edits | WRITE: api/, tools/ directories ONLY |
| **Market Scout** | `.claude/agents/market_scout.md` | Revenue validation, signal detection | READ: market_signals/, external APIs |
| **Friday** | `.claude/agents/friday_orchestrator.md` | State management, dispatch, learning | READ/WRITE: all context_vault/ |
| **Content Lab** | `.claude/agents/content_lab.md` | Findings → research assets | WRITE: synthesis outputs |

---

## The Healing Cycle (5 Phases)

```
Phase 1: SCOUT      → Systems Scout scans for architectural drift
Phase 2: DELIBERATE  → Friday evaluates findings against pattern_library
Phase 3: HEAL        → Surgeon implements repair with IPP headers
Phase 4: VERIFY      → Architect runs governance gate audit
Phase 5: LEARN       → Friday extracts pattern, updates decision matrix
```

**Single-command trigger:** `bash scripts/epos_full_heal.sh`

---

## Directory Contract

```
epos-dev-crew/
├── .claude/agents/           # Agent manifests (the squad)
│   ├── architect.md
│   ├── systems_scout.md
│   ├── surgeon.md
│   ├── market_scout.md
│   ├── friday_orchestrator.md
│   └── content_lab.md
├── context_vault/            # Common Memory (all agents read/write here)
│   ├── findings/             # Scout output, scan results
│   ├── aar/                  # After Action Reports from Surgeon
│   ├── patterns/             # friday_pattern_library.json lives here
│   └── scan_state/           # Current cycle state, scan IDs
├── governance/               # Constitutional docs, IPP templates
│   └── governance_gate.md    # Hard-fail criteria
├── scripts/                  # Orchestration scripts
│   └── epos_full_heal.sh     # The single-click diagnostic
├── logs/                     # Governance audit trail
│   └── .gitkeep
├── templates/                # AAR, findings, and IPP templates
│   ├── aar_template.md
│   ├── findings_template.json
│   └── ipp_header_template.md
└── README.md                 # You are here
```

---

## Implementation Sequence

### Phase 1: Bootstrap (NOW)

1. Drop the `.claude/agents/` directory into your EPOS project root
2. Seed `context_vault/patterns/friday_pattern_library.json` with known patterns
3. Register MCP tools (litellm_client, filesystem audit) with relevant agents
4. Run `bash scripts/epos_full_heal.sh` to trigger first autonomous cycle

### Phase 2: Orchestration (Friday Takes Point)

1. Friday reads `scan_state/current_cycle.json` on every invocation
2. Friday dispatches to the correct agent based on event type
3. All agent output flows back through `context_vault/` — never direct
4. Friday logs every decision to `friday_decision_journal.jsonl`

### Phase 3: Velocity (Continuous Improvement)

1. Every Surgeon repair generates an AAR in `context_vault/aar/`
2. Friday ingests AARs, extracts patterns, updates `friday_pattern_library.json`
3. Patterns that succeed 3+ times get flagged `AUTO_APPROVE: true`
4. System heals known diseases instantaneously without human review

---

## Velocity Targets

| Metric | Before | After |
|---|---|---|
| Debug cycle | ~10 hours | Near-zero (pattern match) |
| Manual review gates | Every repair | Only novel patterns |
| Context switching | Full codebase in one prompt | Agent-scoped context only |
| Onboarding new instance | Manual setup | Copy `.claude/` folder |

---

## Constitutional Guardrails

All agents operate under Article XIV authority. The Architect agent enforces:

- **IPP Compliance:** Every code change must include failure mode documentation BEFORE implementation
- **Scope Locks:** Surgeon writes ONLY to `api/` and `tools/` — core constitution is immutable
- **Governance Gate:** Hard-fail on any repair that doesn't pass `governance_gate.md` criteria
- **Audit Trail:** Every action logged to `logs/governance_gate_audit.jsonl`

---

## How to Use This

**You (Jamie) do one thing:** Run the heal cycle or ask Friday to report status.

**Friday does the rest:** She dispatches, tracks, learns, and escalates only when she encounters a genuinely novel pattern that hasn't been seen before.

This is your shift from neutral into high gear.
