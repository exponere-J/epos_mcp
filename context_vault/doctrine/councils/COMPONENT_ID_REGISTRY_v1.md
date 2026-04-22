# COMPONENT ID & VERSION REGISTRY v1

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §1
**Charter:** `COUNCIL_CHARTER_v1.md`
**Ratified:** 2026-04-22 by Sovereign
**Scope:** all operational modules registered in `context_vault/state/organism_state.json`
**Status:** Active

---

## Preamble

Every module in the organism needs a **stable handle** that survives
renames, refactors, and migrations. File paths change; component
identities should not. The Component ID is that handle.

Paired with a version counter, the ID lets any Directive, AAR, or
Reward-Bus signal reference a module unambiguously: "E-0165 v1.2" is
a precise bookmark the organism can resolve decades from now.

## ID format

```
  E - N N N N
  │   └──┬──┘
  │      └── zero-padded 4-digit sequence
  └─── prefix: EPOS component
```

- **Prefix:** `E-`. Reserved for EPOS-registered operational components.
- **Sequence:** `0001`–`9999`. Assigned in **alphabetical path order** at
  the time of initial registration. Once assigned, an ID never changes.
- **Reserved:**
  - `E-0000` — reserved (no component; use for "not applicable" / sentinels).
  - `E-9999` — reserved (the Sovereign's assigned ID, symbolic).

Scheme version at top of registry: `component_id_scheme.format = "E-NNNN"`.
If we ever need to bump scheme (e.g. to `E-NNNNN` for >9999 components),
`scheme_version` increments on each entry and a migration Directive runs.

## Version format

```
  v < major > . < minor >
```

| Bump | Trigger |
|---|---|
| **major** | Public-API / signature change. Callers must update. |
| **minor** | Body / docstring / metadata change. Callers unaffected. |

Initial: all currently-registered components land at `v1.0`.

No patch-level. If the change doesn't affect callers, it's a minor.
If it does, it's a major. Two axes are enough.

## Version history

Every version bump appends to the entry's `version_history`:

```json
"version_history": [
  {"timestamp": "2026-04-22T00:00:00Z", "major": 1, "minor": 0,
   "reason": "Initial component ID assignment under Article XVI §1"},
  {"timestamp": "2026-05-02T14:22:00Z", "major": 1, "minor": 1,
   "reason": "Docstring refresh; no API change"},
  {"timestamp": "2026-05-15T09:00:00Z", "major": 2, "minor": 0,
   "reason": "Added mode_hint parameter to execute(); callers must update"}
]
```

History is **append-only**. Past entries are never edited. Downgrades are
a new entry with a rationale (and usually a Sentinel critical flag).

## Assignment rules

| Event | Rule |
|---|---|
| New file registered | Assign next available ID (`max(existing) + 1`). Version = `v1.0`. |
| File renamed | ID stays with the module; path updates; no version bump. |
| File split into two | Original keeps its ID; new file gets new ID. Major bump on original if API changed. |
| Two files merged | Keep the lower-numbered ID; higher-numbered ID is retired (not reassigned). |
| File deleted | ID is retired. Retired IDs are never reused. Registry entry moves to `history` section. |

## Reserved ID bands

Kept open for future component classes:

| Range | Reserved for |
|---|---|
| `E-0001`–`E-0999` | Foundation (engine, governance, constitutional authorities) |
| `E-1000`–`E-1999` | CCP, voice, PM surface, reward bus, state graph |
| `E-2000`–`E-2999` | Agents and executors |
| `E-3000`–`E-3999` | Execution arms, bridges, simulators |
| `E-4000`–`E-4999` | Content lab, brand, signal detection |
| `E-5000`–`E-5999` | Diagnostics, TTLG, Doctor |
| `E-6000`–`E-9998` | Future expansion |

**Note:** current assignment (E-0001 to E-0197 as of 2026-04-22) is
sequential alphabetical, not band-aligned. A future re-indexing
Directive may rewrite IDs to align with band semantics — at which point
a migration map preserves the original-to-new mapping for audit.

## Usage in artifacts

| Artifact | How to cite |
|---|---|
| Directive | "Update E-0165 to v1.1 to add `headless_override` param." |
| AAR | "E-0190 (ingestion_runner) failed gate on SHA check; verdict REVISE." |
| Reward Bus | `{"component_id": "E-0167", "signal": "conversion_delta", "value": 0.037}` |
| Event Bus | `ttlg.registered` payload includes `component_id`. |
| Morning briefing | "3 components advanced: E-0168 v1.0→v1.1, E-0169 v1.0→v2.0, E-0187 v1.0→v1.1." |

## Registry snapshot (this session)

- Total components: **197**
- ID range: **E-0001 to E-0197**
- REGISTER verdicts: **19** (execution arm + bridge + simulation + SCC persona + today's Friday executors)
- LEGACY_AUDIT: **177** (pre-protocol modules)
- REVISE: **1**
- REJECT: **0**

### Key REGISTER component IDs (for citation)

| ID | v | Path |
|---|---|---|
| E-0165 | 1.0 | nodes/execution_arm/browser_use_arm.py |
| E-0166 | 1.0 | nodes/execution_arm/callable.py |
| E-0167 | 1.0 | nodes/execution_arm/computer_use_arm.py |
| E-0168 | 1.0 | nodes/execution_arm/deletion_gate.py |
| E-0169 | 1.0 | nodes/execution_arm/mode_selector.py |
| E-0187 | 1.0 | containers/mirofish/simulator.py |
| E-0188 | 1.0 | nodes/bridge/__init__.py |
| E-0189 | 1.0 | nodes/bridge/directive_queue.py |
| E-0190 | 1.0 | nodes/bridge/ingestion_runner.py |
| E-0191 | 1.0 | nodes/bridge/persona_reloader.py |
| E-0192 | 1.0 | nodes/execution_arm/firecrawl_arm.py |
| E-0193 | 1.0 | nodes/scc/personas/__init__.py |
| E-0194 | 1.0 | nodes/simulation/__init__.py |
| E-0195 | 1.0 | nodes/simulation/avatars.py |
| E-0196 | 1.0 | nodes/simulation/mirofish_client.py |
| E-0197 | 1.0 | nodes/simulation/scenario.py |

Complete list in `context_vault/state/organism_state.json`.

## Governance

- Assigned by: Architect (inline) or TTLG (live) at registration time.
- Persisted in: `context_vault/state/organism_state.json` per entry.
- Amendable by: Sovereign decision only. Every amendment is logged
  to `context_vault/bi/component_id_changes.jsonl`.

## Amendment

This doctrine is amended only by Sovereign decision logged to the BI
surface with rationale. Version increments on amendment (`v1` → `v2`).

---

**See also:**
- `context_vault/state/organism_state.json` (authoritative ID store)
- `TTLG_ANTI_TRUNCATION_CONTRACT_v1.md` (integrity regime)
- `TTLG_RESUBMISSION_LOOP_v1.md` (version bump triggers)
- `COUNCIL_CHARTER_v1.md` §VII (artifact taxonomy)
