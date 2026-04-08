# EPOS Coding Skill

## When to use
Apply when building any EPOS module, node, or integration.

## Rules
1. Every new module MUST publish events to the Event Bus
2. Every new module MUST have a vault path for its data
3. Every new module MUST have a Doctor health check
4. Every new module MUST be registered in the sovereignty certifier
5. Every new module MUST have CLI commands in epos.py
6. Every new module MUST have a LangGraph-compatible node function
7. No feature ships without a run trigger (daemon job or reactor handler)

## File patterns
- Node: `nodes/{node_name}.py` with class, health_check, execute_task
- Executor: `friday/executors/{name}_executor.py` or inline in friday_graph.py with route_to_{name} function
- Vault: `context_vault/{node_name}/` with events.jsonl
- Test: verify import, verify run, verify Doctor check

## Pre-mortem (always check before building)
- Can the module import all its dependencies?
- Does the vault directory exist?
- Is the Event Bus path correct?
- Does Doctor know about this module?
- Is there a run trigger (cron job or event handler)?

## Sovereign Node Pattern (canonical)
```python
# nodes/{node_name}.py
from epos_event_bus import EPOSEventBus
from path_utils import get_context_vault

VAULT = get_context_vault() / "{node_name}"
VAULT.mkdir(parents=True, exist_ok=True)

class {NodeName}:
    def health_check(self) -> dict: ...
    def execute(self, task: str) -> dict: ...
    def _log_event(self, event_type, payload): ...
```

## Verification checklist before marking complete
- [ ] File exists
- [ ] Imported by at least one other module
- [ ] Runs successfully when invoked
- [ ] Doctor check added and PASSING
- [ ] Event Bus entry confirms operation

*1% daily. 37x annually.*
