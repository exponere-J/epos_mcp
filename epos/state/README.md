# EPOS Physiology Map — Universal State Graph

## What This Is

`organism_state.json` is the organism's bloodstream. Every EPOS node can read
the current condition of the entire system at any time. Every state change
propagates to the Event Bus so downstream nodes react immediately.

One stimulus → full-body response.

---

## State Fields → Body System Mapping

```
organism_state.json
│
├── meta                        ← Identity (DNA)
│   ├── schema_version
│   ├── created_at
│   ├── last_updated
│   └── session_count
│
├── health                      ← Immune System (EPOSDoctor / Self-Healing)
│   ├── overall                 ← "nominal" | "degraded" | "critical"
│   ├── doctor_last_run
│   ├── checks_passed/warned/failed
│   └── nodes{}                 ← Per-node health (epos_core, litellm, etc.)
│
├── intelligence_layer          ← Brain (LLMs + Nightly Upskill)
│   ├── models_seated[]         ← Currently active models
│   ├── models_pending[]        ← Registry slots not yet filled
│   ├── last_upskill
│   └── upskill_phases_complete
│
├── content_lab                 ← Voice (Content Lab / Echolocation)
│   ├── echolocation_score      ← Current resonance baseline
│   ├── avatars_active
│   ├── content_queued
│   ├── content_published_today
│   └── fotw_signals_today
│
├── pipeline                    ← Heart (Daemon / Friday)
│   ├── missions_active[]
│   ├── missions_completed_today
│   ├── missions_blocked[]
│   ├── daemon_jobs
│   └── last_daemon_heartbeat
│
├── sovereignty                 ← Skeleton (Node Sovereignty)
│   ├── nodes_marketplace_ready
│   ├── nodes_total
│   ├── certifier_last_run
│   ├── governance_gate_blocks_today
│   └── governance_gate_approvals_today
│
├── training                    ← Endocrine System (QLoRA / Nightly Training)
│   ├── qlora_queue_depth
│   ├── last_training_cycle
│   ├── reward_signals_today
│   └── models_in_training[]
│
└── event_bus                   ← Nervous System (EPOSEventBus)
    ├── total_events
    ├── events_today
    ├── last_event_at
    └── bus_size_kb
```

---

## Body System ↔ EPOS Component Cross-Reference

| Human System | EPOS Component | State Field |
|---|---|---|
| **Nervous System** | Event Bus (EPOSEventBus) | `event_bus.*` |
| **Bloodstream** | Universal State Graph (this file) | all fields |
| **Immune System** | Governance Gate + Self-Healing | `sovereignty.*`, `health.*` |
| **Brain** | Context Vault + LLMs | `intelligence_layer.*` |
| **Heart** | Daemon (APScheduler) | `pipeline.*` |
| **Eyes/Ears** | FOTW + Echolocation sensors | `content_lab.fotw_signals_today` |
| **Hands** | Agent Zero + BrowserUse | `pipeline.missions_active` |
| **Voice** | Content Lab | `content_lab.*` |
| **DNA** | CCP + file watermarks | `meta.*` |
| **Hormones** | Friday's daily anchors | `pipeline.last_daemon_heartbeat` |
| **Skeleton** | Node Sovereignty | `sovereignty.*` |
| **Endocrine** | QLoRA training pipeline | `training.*` |

---

## Usage

```python
from epos.state.universal_state_graph import OrganismState

state = OrganismState()

# Read
health = state.query("health.overall")   # → "nominal"

# Write (atomic + Event Bus publish)
state.update("health.overall", "degraded")

# Subscribe to changes
state.subscribe("health.overall", lambda path, val: print(f"{path} → {val}"))

# Full snapshot
snapshot = state.snapshot()

# Increment counters
state.increment("sovereignty.governance_gate_approvals_today")
```

---

*1% daily. 37x annually.*
