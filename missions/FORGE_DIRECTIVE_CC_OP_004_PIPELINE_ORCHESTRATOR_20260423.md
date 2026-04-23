# FORGE DIRECTIVE — CC-OP-004 — Pipeline Orchestrator (Signal-to-Shelf)

**Directive ID:** `FORGE_DIR_CC_OP_004_20260423`
**Constitutional Authority:** Articles V, X, XIV, XVI

---

## Scope

Build `epos/pipeline/signal_to_shelf.py` — the **master conductor** of the 6-phase pipeline. Async phase transitions, Sovereign-gate handling (Pricing Review + Copy Approval), failure routing back to upstream phases, Reward Bus scoring.

## Files

1. `epos/pipeline/__init__.py`
2. `epos/pipeline/signal_to_shelf.py`
3. `epos/pipeline/phase_contracts.py` (per-phase input/output schemas)
4. `epos/pipeline/state_machine.py` (phase transition rules)

## Contract

```python
class PipelineOrchestrator:
    async def run_once(self) -> PipelineRun:
        """Pull top-N signals from buffer, run each through all 6 phases."""
    async def advance_one(self, signal_id: str) -> PhaseTransition:
        """Advance a single signal one phase."""
    def pause_for_sovereign(self, signal_id: str, gate: str) -> None:
        """Emit sovereign.approval.requested and pause the signal."""
    def resume(self, signal_id: str, approval: dict) -> None:
        """Sovereign approved; continue the signal's pipeline."""
```

## Phase transition map

| From | To | Condition |
|---|---|---|
| sensing | staging | priority ≥ 4 |
| staging | synthesis | buffer advances (cron or event) |
| synthesis | fortification | candidate emitted |
| fortification | sovereign_pricing_gate | MiroFish 4 cycles complete |
| sovereign_pricing_gate | implantation | Sovereign approved pricing |
| implantation | sovereign_copy_gate | listing drafted |
| sovereign_copy_gate | stewardship | Sovereign approved copy |
| stewardship | (terminal) | 90d retention reached OR lapsed |

## Sovereign gates

Two and only two. Both emit events and WAIT.

- `sovereign.approval.requested` payload: `{signal_id, gate, artifact_path, timeout_s}`
- `sovereign.approval.granted` / `sovereign.approval.denied` resume the signal.

## Failure routing

- **Cycle 1 fail** (emotional resonance < 7) → back to Synthesis (Content Lab rewrites)
- **Cycle 2 fail** (no recovery path) → Cycle 3 generates Bridge Tool; if Cycle 3 fails, escalate to Sovereign
- **Implantation fail** (API error AND Playwright fallback fail) → escalate; do not auto-retry
- **Stewardship fail** (at-risk client) → Steward alert, not pipeline-level fail

## Orchestration loop

```python
async def run_forever():
    while True:
        run = await orchestrator.run_once()
        log_to_bi(run)
        await asyncio.sleep(ORCHESTRATOR_TICK_S)
```

## Verification

1. Insert 3 test signals into the buffer (via CC-OP-003 API).
2. Start orchestrator in one-shot mode: `await orchestrator.run_once()`.
3. Verify each signal advances at least one phase.
4. Emit fake `sovereign.approval.granted` for a signal at the Pricing gate; verify it advances to Implantation.

## Dependencies

- CC-OP-003 Signal Buffer
- Stage-A MiroFish 4-Cycle orchestrator
- Stage-C CC-OP-001 Gumroad client
- Event bus
