# EPOS EXECUTION PACKAGE — Complete Installation & Execution Guide

**Generated:** February 19, 2026  
**Authority:** EPOS Constitution v3.1 + Agent Zero as Execution Spine  
**Execution Model:** Agent Zero (deterministic) orchestrated by Phi-3 (strategic)

---

## 📦 Package Contents

This execution package contains everything needed to deploy EPOS:

### Core Installation

- `epos_master_installer.py` — Master installer (runs environment checks, installs packages, creates structure)
- `az_mission_executor.py` — Agent Zero mission wrapper (feeds EPOS missions to AZ)
- `phi3_command_center.py` — Phi-3 strategic console (chat GUI for orchestration)
- `browseruse_airtable_setup.py` — AirTable base creation automation

### Startup Scripts

- `start_epos.sh` — Daily startup (Linux/Mac)
- `start_epos.bat` — Daily startup (Windows)

### Documentation

- `EPOS_4Week_Execution_Plan.html` — Complete 4-week roadmap with pre-mortem analysis
- `EPOS_Architecture_Decisions_v3_1.html` — System architecture decisions document
- `EPOS_Trust_Family_Planning.html` — S-Corp + trust structure attorney briefing

---

## 🚀 Quick Start (30 Minutes)

### Prerequisites

```bash
# Required
- Python 3.11.x
- Git
- Ollama (for Phi-3)
- 10GB free disk space

# Optional (for full functionality)
- n8n (for AirTable sync)
- Node.js 18+ (for BrowserUse)
```

### Installation Steps

```bash
# 1. Navigate to EPOS workspace
cd ~/workspace  # or your workspace directory

# 2. Run master installer
python epos_master_installer.py --mode full

# 3. Fill in API keys in .env
nano .env  # or use your editor
# Add: ANTHROPIC_API_KEY, OPENAI_API_KEY, AIRTABLE_EMAIL, AIRTABLE_PASSWORD

# 4. Pull Phi-3 model
ollama pull phi3.5:3.8b-mini-instruct-q4_K_M

# 5. Start EPOS
./start_epos.sh  # Linux/Mac
# or
start_epos.bat   # Windows
```

Your browser will open to `http://localhost:8501` with the Phi-3 Command Center.

---

## 📋 Installation Modes

```bash
# Full installation (recommended first run)
python epos_master_installer.py --mode full

# Environment validation only (no installation)
python epos_master_installer.py --mode validate

# Skip AirTable setup (do manually later)
python epos_master_installer.py --mode full --skip-airtable
```

### What Gets Installed

**Core Packages:**
- `python-dotenv`, `requests`, `fastapi`, `uvicorn`, `pydantic`, `aiofiles`

**Agent Packages:**
- `ollama`, `anthropic`, `openai`, `duckduckgo-search`

**GUI Packages:**
- `streamlit`, `plotly`, `pandas`

**BrowserUse Packages (optional):**
- `browser-use`, `playwright`, `langchain-openai`

**Directory Structure Created:**

```
workspace/
├── context_vault/
│   ├── missions/          # Agent Zero mission files
│   ├── doctrine/          # Constitutional documents
│   ├── intelligence/      # Market research
│   ├── diagnostics/       # TTLG reports
│   ├── financial/         # Transaction logs
│   ├── crm/              # Lead data
│   ├── tools/            # Tool outputs
│   └── airtable/         # Base manifests
├── logs/
│   ├── az/               # Agent Zero execution logs
│   ├── phi3/             # Phi-3 session logs
│   └── mcp/              # MCP server logs
├── .env                  # Configuration (API keys)
├── epos_config.json      # Master configuration
└── EPOS_INSTALL_VALIDATION.md  # Installation report
```

---

## 🤖 Agent Zero Missions

After installation, execute missions in order:

### Week 1 Missions

```bash
# Mission 1: Deploy Unified Nervous System (4 hours)
python az_mission_executor.py --mission AZ-001-NERVOUS-SYSTEM

# Mission 2: Create AirTable Bases (2 hours)
python az_mission_executor.py --mission AZ-002-AIRTABLE-BASES
```

### Week 2 Missions

```bash
# Mission 3: Deploy Phi-3 Command Center (1 hour)
python az_mission_executor.py --mission AZ-003-PHI3-DEPLOY
```

### Week 3 Missions

```bash
# Mission 4: Build 3-Tier Sovereignty Stack (6 hours)
python az_mission_executor.py --mission AZ-004-GOOGLE-SHEETS-SYNC
```

### Week 4 Missions

```bash
# Mission 5: Operationalize CRM + Project Management (8 hours)
python az_mission_executor.py --mission AZ-005-CRM-PM-INTEGRATION
```

### Mission Management Commands

```bash
# List all available missions
python az_mission_executor.py --list

# Dry-run (simulate without executing)
python az_mission_executor.py --mission AZ-001-NERVOUS-SYSTEM --dry-run

# View mission details
cat context_vault/missions/AZ-001-NERVOUS-SYSTEM.json | jq
```

---

## 🧠 Phi-3 Command Center

### Features

- **Chat with Phi-3 Mini** — Local LLM via Ollama
- **7 EPOS Roles** — R1 Radar, S1 Sales Brain, TTLG, MA1, A1 Architect, Growth Steward
- **Internet Search** — DuckDuckGo integration (automatic on keywords)
- **Context Vault Query** — Search through EPOS knowledge base
- **Node Health Monitoring** — Real-time status of all EPOS nodes
- **Session Logging** — Every chat turn saved to Context Vault

### Usage

```bash
# Start Phi-3 Command Center
streamlit run phi3_command_center.py

# Or use startup script
./start_epos.sh  # Opens browser automatically
```

### Role Selection

Use the sidebar dropdown to switch between roles:

- **Default Assistant** — General purpose chat
- **R1 Radar** — Market intelligence and trend analysis
- **S1 Sales Brain** — Quick sales replies with clear next steps
- **TTLG Diagnostic** — Business analysis and 10-layer reports
- **MA1 Market Awareness** — Trend forecasting and early warnings
- **A1 Architect** — System design and pre-mortem analysis
- **Growth Steward** — 9th order strategic advice

### Example Queries

```
"What are the top 3 AI automation trends for agencies?"
→ Triggers Internet Search, returns results with citations

"Find recent diagnostic reports in the vault"
→ Queries Context Vault, returns file paths

"As R1 Radar, analyze competitor positioning in content automation"
→ Switches to R1 role, provides strategic intelligence

"Generate a TTLG diagnostic for a solo creator struggling with content velocity"
→ Switches to TTLG role, creates 10-layer analysis
```

---

## 🏗️ Week 1-4 Execution Plan

Complete roadmap in `EPOS_4Week_Execution_Plan.html`. Summary:

### Week 1 (Feb 19-25): Foundation

**Constitutional:**
- Write Article XII (GRAG Tool Governance)
- Write Article XIII (Personal/Business Data Firewall)

**Financial:**
- File S-Corp Form 2553 (Deadline: March 15)
- Open business checking account
- Salary: $2,759/week retroactive to 1/1/2026

**Technical:**
- Create 4 AirTable bases via BrowserUse
- Create tool manifest for Phi-3 tools

**Exit Criteria:**
✅ Articles written  
✅ Form 2553 ready to file  
✅ Business account open  
✅ AirTable bases created  

### Week 2 (Feb 26-Mar 4): Phi-3 + Search

**Agent Zero Missions:**
- AZ-001: Deploy Unified Nervous System
- AZ-003: Deploy Phi-3 Command Center

**Internet Search Tool:**
- DuckDuckGo API integration
- Context Vault logging
- Event Bus publishing

**Critical Deadline:**
- File Form 2553 with IRS (Day 5)

**Exit Criteria:**
✅ Phi-3 GUI operational  
✅ Internet Search working  
✅ Context Vault integrated  
✅ Form 2553 filed  

### Week 3 (Mar 5-11): 3-Tier Stack

**Agent Zero Mission:**
- AZ-004: Build Google Sheets Sync

**3-Tier Sovereignty Stack:**
- Tier 1: AirTable (primary)
- Tier 2: Google Sheets (mirror)
- Tier 3: Context Vault JSONL (sovereign)

**Financial:**
- First payroll run: $2,759

**Exit Criteria:**
✅ Real-time sync working  
✅ Daily reconciliation passing  
✅ First payroll logged to all 3 tiers  

### Week 4 (Mar 12-19): CRM + PM Live

**Agent Zero Mission:**
- AZ-005: CRM + Project Management Integration

**Operational Systems:**
- Lead intake form → AirTable
- TTLG diagnostic automation
- Auto-proposal engine
- Project milestone tracking

**Test:**
- First real client end-to-end

**Exit Criteria:**
✅ Lead form → proposal → project working  
✅ Zero manual data entry  
✅ All tiers synchronized  

---

## ⚙️ Configuration Files

### `.env` (API Keys & Paths)

```bash
# Workspace
EPOS_ROOT=/path/to/workspace
CONTEXT_VAULT=/path/to/workspace/context_vault

# Agent Zero
AGENT_ZERO_PATH=/path/to/agent-zero
AGENT_ZERO_MODEL=phi3.5:3.8b-mini-instruct-q4_K_M

# Ollama
OLLAMA_HOST=http://localhost:11434

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
AIRTABLE_EMAIL=your.email@domain.com
AIRTABLE_PASSWORD=your_password

# MCP Server Ports
MCP_CONTEXT_PORT=8009
MCP_EVENT_BUS_PORT=8008
MCP_GOVERNANCE_PORT=8007
MCP_LEARNING_PORT=8006
```

### `epos_config.json` (Master Config)

Contains:
- Agent configurations
- MCP server ports
- Node registry
- AirTable base IDs
- S-Corp election data

Auto-generated by installer. Edit to update system configuration.

---

## 🔍 Troubleshooting

### Python Version Error

```
Error: Python 3.11.x required
Fix: Install Python 3.11 and create new virtual environment
```

### Ollama Not Running

```
Error: Cannot connect to Ollama
Fix: Start Ollama service
  Windows: Start Ollama app
  Linux: ollama serve
  Mac: Ollama app auto-starts
```

### Package Installation Fails

```
Error: pip install failed
Fix: Use --break-system-packages flag
  pip install <package> --break-system-packages
```

### Playwright Browser Missing

```
Error: Browser not found
Fix: Install Chromium
  playwright install chromium
```

### Port Already in Use

```
Error: Port 8501 in use
Fix: Kill existing process or use different port
  streamlit run phi3_command_center.py --server.port 8502
```

### Agent Zero Not Found

```
Error: Agent Zero path invalid
Fix: Set correct path in .env
  AGENT_ZERO_PATH=/correct/path/to/agent-zero
```

---

## 📊 Validation & Health Checks

### Post-Installation Validation

```bash
# Check installation report
cat EPOS_INSTALL_VALIDATION.md

# Verify Context Vault structure
ls -la context_vault/

# Check mission files created
ls context_vault/missions/AZ-*.json

# Test Ollama connection
ollama list

# Test Phi-3 model
ollama run phi3.5:3.8b-mini-instruct-q4_K_M "test"
```

### Daily Health Checks

```bash
# Phi-3 Command Center sidebar shows node health
# Green = healthy, Red = offline, Gray = CLI only

# Check logs
tail -f logs/az/az_execution_*.jsonl
tail -f logs/phi3/phi3_session_*.jsonl
```

---

## 🎯 Success Criteria

### Week 1 Complete When:

- [ ] Article XII & XIII written and in Constitution
- [ ] S-Corp Form 2553 assembled (CPA reviewed)
- [ ] Business checking account open
- [ ] 4 AirTable bases created
- [ ] Tool manifest created

### Week 2 Complete When:

- [ ] Phi-3 GUI loads and chats successfully
- [ ] Internet Search returns results
- [ ] Context Vault queries work
- [ ] Form 2553 filed with IRS

### Week 3 Complete When:

- [ ] AirTable → Sheets sync working (< 30 sec)
- [ ] Daily reconciliation shows 0 mismatch
- [ ] First payroll ($2,759) logged to all 3 tiers

### Week 4 Complete When:

- [ ] Test client tracked end-to-end
- [ ] Lead form → TTLG → proposal → project
- [ ] Zero manual data entry required
- [ ] All systems operational

---

## 🆘 Support & Documentation

**Installation Issues:**
- Check: `EPOS_INSTALL_VALIDATION.md`
- Logs: `logs/epos_install_*.jsonl`

**Agent Zero Missions:**
- Mission files: `context_vault/missions/AZ-*.json`
- Execution logs: `logs/az/az_execution_*.jsonl`

**Phi-3 Sessions:**
- Session logs: `context_vault/missions/phi3_sessions/`
- Search logs: `context_vault/tools/search/search_log.jsonl`

**Architecture Decisions:**
- Full document: `EPOS_Architecture_Decisions_v3_1.html`
- Constitutional amendments required before Week 2

**Financial Planning:**
- S-Corp + trust structure: `EPOS_Trust_Family_Planning.html`
- Deadline tracker: Form 2553 due March 15, 2026

---

## 🚦 Critical Deadlines

| Date | Deadline | Action Required |
|------|----------|-----------------|
| **Mar 15, 2026** | S-Corp Election | File Form 2553 with IRS (Week 2, Day 5) |
| **Feb 25, 2026** | Week 1 Exit | Constitutional amendments + AirTable bases |
| **Mar 4, 2026** | Week 2 Exit | Phi-3 operational + Search tool working |
| **Mar 11, 2026** | Week 3 Exit | 3-tier stack + first payroll |
| **Mar 19, 2026** | Week 4 Exit | CRM/PM operational + first client test |

---

## 📞 Next Steps

1. **Run Installer:**
   ```bash
   python epos_master_installer.py --mode full
   ```

2. **Fill API Keys:**
   - Edit `.env` with your keys
   - Required: ANTHROPIC_API_KEY, OPENAI_API_KEY
   - Optional: AIRTABLE credentials (for BrowserUse)

3. **Write Amendments:**
   - Article XII: GRAP Tool Governance
   - Article XIII: Data Firewall
   - Append to `EPOS_CONSTITUTION_v3_1.md`

4. **Execute Week 1:**
   ```bash
   python az_mission_executor.py --list
   python az_mission_executor.py --mission AZ-001-NERVOUS-SYSTEM
   ```

5. **Daily Startup:**
   ```bash
   ./start_epos.sh  # or start_epos.bat on Windows
   ```

---

**EPOS Execution Package v1.0**  
**Constitutional Authority:** EPOS v3.1 + Node Sovereignty v1.0  
**Execution Architecture:** Agent Zero (motor system) + Phi-3 (strategic cortex)  
**Installation Time:** 30 minutes  
**Full Deployment:** 4 weeks  
**Operational Readiness:** March 19, 2026
