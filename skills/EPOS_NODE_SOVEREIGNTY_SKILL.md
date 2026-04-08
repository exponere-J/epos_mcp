# EPOS Node Sovereignty Skill

## When to use
Apply when creating any new sovereign node.

## The 7 Sovereignty Criteria (105 points total, 85+ for MARKETPLACE_READY)
1. **Standalone Import** (15 pts) — imports without pulling the full organism
2. **Self-Test** (15 pts) — has assertion-based __main__ self-test
3. **API Surface** (15 pts) — clean, documentable public API
4. **Event Bus** (15 pts) — publishes and/or subscribes to events
5. **Data Sovereignty** (15 pts) — owns vault path + JSONL journal
6. **Configuration** (15 pts) — env-configurable with init params
7. **Value Proposition** (15 pts) — clear, action-verb-driven description

## Checklist for new sovereign node
- [ ] Own vault path at `context_vault/{node_name}/`
- [ ] Own event log at `context_vault/{node_name}/events.jsonl`
- [ ] Own CLI commands under `epos {node_name}`
- [ ] Health check callable by Doctor
- [ ] Registered in `node_sovereignty_certifier.py` BUILDING_BLOCKS
- [ ] LangGraph-compatible node function (for Friday integration)
- [ ] No cross-node imports — communicate via Event Bus and vault only
- [ ] Sovereignty score target: 85+ MARKETPLACE_READY
- [ ] Self-test PASS with assertion count

## Anti-patterns
- Importing from another node directly (use Event Bus instead)
- Writing to another node's vault path (use Event Bus events)
- Hardcoded paths (use path_utils.get_context_vault())
- LLM in routing logic (deterministic lookup tables only)
- Sync calls to expensive operations from Doctor checks (use fast importability check)

## Constitutional boundaries
- No node can modify .env files
- No node can modify constitutional documents
- No node can delete data — archive, compress, or flag only
- Tier 2/3 actions require human approval

*1% daily. 37x annually.*
