# AAR: Module 3 — roles.py (Agent Role Definitions)

**Date**: 2026-03-27
**Mission**: EPOS Core Heal — Module 3 of 9
**Task ID**: 1346c4e1
**Status**: DONE
**Doctor**: 19 PASS / 4 WARN / 0 FAIL — Exit 0

---

## File Created

`C:/Users/Jamie/workspace/epos_mcp/roles.py`

## Design Decisions

1. **Registry, not runtime actor** — `roles.py` defines what agents exist and what they can do. It does not implement any agent logic. The existing implementations in `engine/roles/arbiter.py`, `engine/roles/librarian.py`, and `engine/roles/analyst.py` remain as the runtime actors.

2. **Frozen dataclass** — `AgentRole` is immutable. Roles are constitutional definitions, not runtime-mutable state.

3. **7 agents registered**: Alpha (Arbiter), Sigma (Librarian), Omega (Analyst), Orchestrator, Bridge, Friday, TTLG

4. **13 capabilities defined**: read/write vault, read/write engine, execute mission, governance audit/enforce, BI read/write, propose amendment, manage agents, external API, file system

5. **6 constitutional boundaries**: no write outside EPOS, no delete engine, no bypass gate, no direct DB write without receipt, no unlogged decision, require stasis check

## API Exports

| Function | Purpose |
|----------|---------|
| `get_role(agent_id)` | Look up role by string ID |
| `get_all_roles()` | All roles keyed by string |
| `get_agents_with_capability(cap)` | Find agents with a capability |
| `validate_assignment(agent_id, cap)` | Check if agent can do action |
| `AgentId` enum | Canonical agent identifiers |
| `Capability` enum | All permitted actions |
| `ConstitutionalBoundary` enum | Hard limits |

## Verification

- `py_compile`: PASS
- Self-test: All assertions passed (4/4)
- Doctor: Exit 0, 19 PASS

## Sprint Progress

| Module | Status |
|--------|--------|
| 1. path_utils.py | DONE |
| 2. stasis.py | DONE |
| 3. **roles.py** | **DONE** |
| 4. epos_intelligence.py | NEXT |
| 5. context_librarian.py | backlog |
| 6. constitutional_arbiter.py | backlog |
| 7. flywheel_analyst.py | backlog |
| 8. agent_orchestrator.py | backlog |
| 9. agent_zero_bridge.py | backlog |
