# DEPRECATED — containers/event-bus/

**Status:** DEPRECATED as of 2026-04-08 (M4 Docker migration)

## Why

The EPOS event bus is **file-based**, not network-based. The canonical design
principle is: *"No Docker ports. No network. One file. One truth."*

The single source of truth is:

```
context_vault/events/system/events.jsonl
```

All services communicate through this JSONL file, which is shared via a Docker
named volume (`context_vault`). There is no need for a separate container
running an HTTP event-bus service — that would contradict the architecture.

## Migration

All services that previously called the event-bus container should use:

```python
from epos_event_bus import get_event_bus

bus = get_event_bus()
bus.publish({"event_type": "...", "payload": {...}})
```

The `epos_event_bus.py` module reads `EPOS_ROOT` from the environment and
writes directly to `$EPOS_ROOT/context_vault/events/system/events.jsonl`,
which is mounted as a shared volume across all containers.

## What to do with this directory

This directory is retained for reference only. Do not build or deploy the
`event-bus` container. The `docker-compose.yml` does not include it.
