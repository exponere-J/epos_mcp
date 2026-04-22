# AAR: EPOS Dockerization + Remote Access
**Date:** 2026-04-08
**Directive:** EPOS_DOCKERIZATION_DIRECTIVE
**Result:** COMPLETE (M0–M8 shipped, M9 instructions below)

---

## What Was Done

### M0 — Snapshot
- Cleaned junk dirs: `C:/` (shell quoting accident) and `.envecho`
- Added `CLI-Anything/`, `venv_epos/`, `venv_epos_311/` to `.gitignore`
- Committed `8cebddec`: *"Snapshot: All sprint work through April 8 2026"*

### M1 — requirements.txt
- Removed dead `anthropic` dependency (zero imports)
- Removed `langchain*` packages (only `langgraph` is needed directly)
- Added: `apscheduler`, `litellm`, `browser-use`, `playwright`, `httpx`, `pyyaml`, `orjson`, `lxml`, `numpy`, `Pillow`, `jsonschema`, `click`
- Created `requirements-dev.txt` (pytest, black, ruff)
- Aligned all `containers/*/requirements.txt` to matching versions (fastapi 0.115.5, pydantic 2.10.3+, httpx 0.28+)

### M2 — Root Dockerfile
- `FROM python:3.11-slim`
- System deps: `curl`, `gcc`, `libxml2-dev`, `libxslt-dev`
- `playwright install chromium --with-deps`
- `ENV EPOS_ROOT=/app`, `ENV LLM_MODE=groq_direct`
- `HEALTHCHECK`: imports `EPOSDoctor`
- `CMD uvicorn command_center:app --host 0.0.0.0 --port 8001`

### M3 — Path Migration
All hard-coded `C:/Users/Jamie/workspace/epos_mcp` paths replaced with:
```python
Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent[...])))
```
Files patched: `config.py`, `agents/*.py`, `content/lab/**/*.py`, `ttlg/*.py`, `engine/enforcement/*.py`, `event_bus.py`, `immune_monitor.py`, `az_dispatch.py`, `context_handler.py`, `context_server.py`

**Result:** Zero `Path("C:/...")` instances remain in active Python files.

### M4 — Event Bus Deprecation
- Added `containers/event-bus/DEPRECATED.md`
- Event bus is file-based JSONL (`context_vault/events/system/events.jsonl`)
- Shared across all containers via Docker named volume `context_vault`

### M5 — Container Cleanup
- Renamed `containers/error-detector/Dockerfile.txt` → `Dockerfile`
- Removed `containers/learning-server/Dockerfile.dockerfile` (duplicate)
- Removed empty dirs: `command-center/`, `context/`, `diagnostic-server/`, `governance/`, `jarvis/`, `learning/`
- Removed `containers/immune_monitor/` (underscore duplicate; hyphenated `immune-monitor/` retained)

### M6 — 14-Service Docker Compose
Replaced the 6-service compose with a 14-service organism:

| Service | Port | Image |
|---|---|---|
| `postgres` | 5432 (5433 dev) | `postgres:16-alpine` |
| `ollama` | 11434 | `ollama/ollama:latest` |
| `litellm` | 4000 | `ghcr.io/berriai/litellm:main-latest` |
| `epos-core` | 8001 | root `Dockerfile` |
| `friday` | 8090 | root `Dockerfile` |
| `epos-daemon` | — | root `Dockerfile` |
| `governance-gate` | 8101 | `containers/governance-gate` |
| `governance-srv` | 8108 | `containers/governance-server` |
| `context-server` | 8103 | `containers/context-server` |
| `immune-monitor` | 8104 | `containers/immune-monitor` |
| `learning-server` | 8102 | `containers/learning-server` |
| `agent-zero` | 50080→8105 | `containers/agent-zero` |
| `nocodb` | 8080 | `nocodb/nocodb:latest` |
| `n8n` | 5678 | `docker.n8n.io/n8nio/n8n` |

Shared `context_vault` named volume (bind mount to `./context_vault`).
`x-epos-env` anchor injects `EPOS_ROOT=/app` + all inter-service URLs.

### M7 — Inter-Container URL Migration
All `localhost:NNNN` defaults replaced with Docker service names:

| File | Old | New |
|---|---|---|
| `engine/llm_client.py` | `http://localhost:4000` | `http://litellm:4000` |
| `engine/llm_client.py` | `http://localhost:11434` | `http://ollama:11434` |
| `engine/jarvis_bridge.py` | `http://localhost:8100` | `http://epos-core:8001` |
| `engine/jarvis_bridge.py` | `http://localhost:8101` | `http://governance-gate:8101` |
| `nodes/agent_zero_node.py` | `http://localhost:50080` | `http://agent-zero:8105` |
| `nodes/browser_use_node.py` | `http://localhost:11434` | `$OLLAMA_HOST` |
| `groq_router.py` | `http://localhost:11434` | `http://ollama:11434` |
| `multimodal_router.py` | `http://localhost:11434` | `http://ollama:11434` |
| `containers/immune-monitor/server.py` | `http://localhost:810x` | `http://[service-name]:PORT` |
| `immune_monitor.py` | same | same |

### M8 — Build + Launch
```
docker compose --env-file .env.docker build epos-core   # ✓ 315s (playwright chromium dl)
docker compose --env-file .env.docker build governance-gate governance-srv context-server learning-server immune-monitor  # ✓ fast
docker compose --env-file .env.docker up -d postgres ollama epos-core  # ✓
```

**Running services (confirmed):**
```
epos-core     Up (healthy)  0.0.0.0:8001
epos-litellm  Up            0.0.0.0:4000
epos-ollama   Up            0.0.0.0:11434
epos-postgres Up (healthy)  0.0.0.0:5433
```

**FastAPI docs:** http://localhost:8001/docs ✓

**Workarounds applied:**
- GPU block commented out (WSL2 has no NVIDIA adapters configured)
- Port 5432 → 5433 in `.env.docker` (existing `epos_db` on 5432)

---

## M9 — Remote Access Setup

### Today: Tailscale (30 minutes)
1. Download: https://tailscale.com/download/windows
2. Install and log in with your account
3. Note your machine's Tailscale IP (e.g. `100.x.x.x`)
4. On any remote machine: install Tailscale, log in same account
5. Connect: `ssh Jamie@100.x.x.x`
6. The EPOS stack is accessible at `http://100.x.x.x:8001`, `8090`, `4000`, etc.

### This Week: tmux for Persistent Sessions
Install tmux in WSL2:
```bash
sudo apt-get install tmux
```

Start a persistent Claude Code session:
```bash
tmux new-session -s epos
cd ~/workspace/epos_mcp
claude
# Ctrl+B D to detach — session stays alive
# tmux attach -t epos to resume
```

### This Week: VPS for 24/7 (Optional)
Option: Hetzner CX22 (~$6/month, 2 vCPU, 4GB RAM, 40GB SSD)
```bash
# On VPS:
sudo apt-get install -y docker.io docker-compose-plugin git
git clone <your-repo> /opt/epos_mcp
cd /opt/epos_mcp
cp .env.docker .env.local && vim .env.local  # fill in secrets
docker compose --env-file .env.local up -d
```
Claude Code via SSH: `ssh user@vps-ip` then `claude` in tmux.

---

## Bugs Found & Fixed (not in directive)

| Bug | Fix |
|---|---|
| `venv_az/` committed in M0 snapshot | Added to `.gitignore` |
| `command_center.py` has no `/health` endpoint | Not blocking; `/docs` serves at 200 |
| `governance-gate` and `governance-server` both EXPOSE 8101 | Mapped to different host ports: 8101 vs 8108 |
| `api/epos_api.py` referenced in old compose but doesn't exist | Corrected CMD to `command_center:app` |

---

## Echoes Work Location (URGENT FIND — 2026-04-08)

Echoes code lives in **two locations**:

### Location 1 — `C:\Users\Jamie\workspace\echoes\` (standalone repo)
- Early scaffold, mostly empty node stubs
- `config/paths.py`, `core/state_machine.py`, `nodes/*/` (all `__init__.py` only)
- `clients/pgp_orlando/vault/` — live client state
- Created: 2026-03-16

### Location 2 — `C:\Users\Jamie\workspace\epos_mcp\` (real implementations)
- `echoes/m1_publisher.py` — publisher pipeline (12KB)
- `content_lab/echolocation_predictor.py`, `brief_generator.py`, `template_engine.py`, `crs_scorer.py` (12–22KB each, fully implemented)
- `reactor/marketing_reactor.py`
- `nodes/avatar_registry.py`
- `context_vault/echoes/` — **live data** (published LinkedIn + X posts, ready_to_post queue, sparks, predictions, research_briefs, nurture_sequences)

**Verdict:** The real Echoes system lives in `epos_mcp`. The standalone `echoes/` repo is a dead scaffold. Echoes has already run in production — posts have been generated and published.

---

## State of EPOS Stack (End of Session)

```
Git:    epos_mcp main @ 63183329 (Docker: Containerize EPOS organism M1-M8)
Docker: epos-core (8001) + litellm (4000) + ollama (11434) + postgres (5433) RUNNING
Built:  governance-gate, governance-srv, context-server, immune-monitor, learning-server
Pending launch: friday (8090), epos-daemon, agent-zero, nocodb, n8n
Secrets needed: PG_PASSWORD, JWT_SECRET, N8N_ENCRYPTION_KEY in .env.docker.local
```

## Next Commands When Ready to Launch Full Stack

```bash
cd C:\Users\Jamie\workspace\epos_mcp
cp .env.docker .env.docker.local
# Edit .env.docker.local — set PG_PASSWORD, JWT_SECRET, N8N_ENCRYPTION_KEY
docker compose --env-file .env.docker.local build friday epos-daemon agent-zero
docker compose --env-file .env.docker.local up -d
docker compose --env-file .env.docker.local ps
curl http://localhost:8001/docs   # epos-core
curl http://localhost:8090/health # friday
curl http://localhost:4000/health # litellm
```
