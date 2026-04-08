# TTLG Diagnostics v0.1: System Overview & Quick Start

**Status:** 🟢 ACTIVE  
**Version:** 0.1  
**Last Updated:** 2026-02-28

---

## What is TTLG?

TTLG Diagnostics is the **autonomous healing brain** of EPOS. It continuously scans the system for architectural disease, proposes cures grounded in evidence, and learns from every diagnosis to improve future decisions.

**Core thesis:** If you can heal yourself, you can heal anyone.

---

## The 6-Phase Diagnostic Cycle

Every diagnosis follows the same sequence:

```
PHASE 1: DECONSTRUCT (Scout)
  ↓ What's broken?
  
PHASE 2: EVALUATE (Thinker)
  ↓ Which problems matter most?
  
PHASE 3: GOVERNANCE GATE (Jamie)
  ↓ Is Jamie comfortable with these fixes?
  
PHASE 4: RECONFIGURE (Surgeon)
  ↓ How do we fix this?
  
PHASE 5: RECONSTRUCT (Analyst)
  ↓ Did we actually fix it?
  
PHASE 6: AAR (Legacy)
  ↓ What do we learn?
```

---

## Quick Start (First Scan)

### Prerequisites

1. **API Keys** (get these before running):
   - Together AI: https://www.together.ai (for Scout)
   - DeepSeek: https://www.deepseek.com (for Thinker)
   - Anthropic: https://console.anthropic.com (for Surgeon)
   - Google: https://console.cloud.google.com (for Analyst)

2. **Files in place**:
   - [ ] `.env` (this directory, with your API keys)
   - [ ] `CLAUDE.md` (constitutional charter)
   - [ ] `schemas/aar_v1.json` (AAR schema)
   - [ ] `scripts/ttlg_phase1_scout.sh` (Phase 1 script)

3. **Directories created**:
   ```bash
   mkdir -p context_vault/internal_diagnostics/aars
   mkdir -p context_vault/scans
   mkdir -p logs
   mkdir -p dashboards
   ```

### Step 1: Populate `.env` with Your API Keys

```bash
# Open .env in your editor
nano .env

# Replace these placeholders with your actual API keys:
TOGETHER_API_KEY="your_actual_key"
DEEPSEEK_API_KEY="your_actual_key"
ANTHROPIC_API_KEY="your_actual_key"
GOOGLE_API_KEY="your_actual_key"
```

### Step 2: Verify Setup

```bash
# Check that .env is readable
cat .env | grep SCOUT_PROVIDER
# Should output: SCOUT_PROVIDER=together_ai

# Check directories exist
ls -la context_vault/
ls -la logs/
ls -la schemas/
```

### Step 3: Run Phase 1 (Scout Scan)

```bash
# Make script executable
chmod +x scripts/ttlg_phase1_scout.sh

# Run the scan
bash scripts/ttlg_phase1_scout.sh
```

**Expected output:**
```
🔍 TTLG Diagnostics Phase 1: DECONSTRUCT
========================================

Scout Configuration:
  Provider: together_ai
  Model: meta-llama/Llama-3.3-70b-instruct
  Context window: 10000000

✓ API key loaded (masked)

📋 Scan ID: scan_20260228_141530
📁 Output: context_vault/scans/scan_20260228_141530

🚀 Triggering Scout scan...
⏳ Scanning repository...

✓ Scout output saved to: context_vault/scans/scan_20260228_141530/scout_output.json

📊 Phase 1 Summary:
  Files scanned: 47
  Dependencies mapped: 156
  Brittle points found: 2

✅ Phase 1 COMPLETE
```

### Step 4: Review Scout Output

```bash
# View the dependency graph and brittle points
cat context_vault/scans/scan_*/scout_output.json | jq '.'
```

You should see:
- `files_scanned`: Total files analyzed
- `dependencies_mapped`: Nodes in the architecture
- `brittle_points_found`: Issues that need attention

### Step 5: Next Steps

Once Phase 1 completes, you can manually proceed to Phase 2, or wait for automated scheduling.

---

## File Structure

```
Friday Root/
├── .env                          # API keys + TTLG config
├── CLAUDE.md                     # Constitutional charter
├── README_TTLG.md               # This file
├── ttlg_node_definition.json    # Node registry entry
│
├── schemas/
│   └── aar_v1.json             # After Action Review schema
│
├── scripts/
│   └── ttlg_phase1_scout.sh    # Phase 1: Deconstruct
│
├── context_vault/
│   ├── internal_diagnostics/
│   │   └── aars/               # After Action Review artifacts
│   └── scans/                  # Scan outputs (by scan_id)
│
├── logs/
│   └── ttlg_diagnostics.jsonl  # Immutable audit trail
│
└── dashboards/
    └── ttlg_health.json        # Metrics dashboard
```

---

## Configuration Reference

### API Providers

| Phase | Provider | Model | Cost | Context |
|-------|----------|-------|------|---------|
| 1 | Together AI | Llama 3.3 70B | ~$0.10/scan | 10M tokens |
| 2 | DeepSeek | DeepSeek-Reasoner | ~$0.05/scan | ~128K tokens |
| 4 | Anthropic | Claude Opus | ~$0.20/scan | 200K tokens |
| 5 | Google | Gemini 1.5 Flash | ~$0.05/scan | 1M tokens |

**Estimated total cost per scan:** ~$0.40 (very cheap compared to consultant)

### Governance Settings

```bash
# All of these MUST be enabled for constitutional compliance:

GOVERNANCE_GATE_APPROVAL_REQUIRED="true"         # Require Jamie's approval
GOVERNANCE_GATE_CONSTITUTIONAL_CHECK="true"     # Validate against constitution
AUDIT_LOG_IMMUTABLE="true"                       # Never delete logs
LEARNING_FEEDBACK_TO_THINKER="true"             # Patterns feed back into guardrails
```

### Scheduling

By default, TTLG scans daily at 2am UTC (9pm EST):

```bash
TTLG_SCAN_SCHEDULE="0 2 * * *"  # Cron format
```

To run on-demand, manually trigger:
```bash
bash scripts/ttlg_phase1_scout.sh
```

---

## Understanding the Output

### Scout Output (`scout_output.json`)

```json
{
  "scan_id": "scan_20260228_141530",
  "files_scanned": 47,
  "dependencies_mapped": 156,
  "brittle_points_found": [
    {
      "id": "BP-001",
      "severity": "high",
      "description": "Hardcoded paths in governance.py",
      "file_reference": "governance.py:42",
      "remediation_effort": "easy"
    }
  ]
}
```

**What to look for:**
- `severity: "critical"` → Blocks autonomy (fix immediately)
- `severity: "high"` → Violates rules (fix this sprint)
- `severity: "medium"` → Technical debt (prioritize by ROI)
- `severity: "low"` → Nice-to-have (consider for future)

### Audit Log (`logs/ttlg_diagnostics.jsonl`)

```json
{"phase": 1, "stage": "started", "timestamp": "2026-02-28T14:15:30Z", "scan_id": "scan_20260228_141530"}
{"phase": 1, "stage": "completed", "timestamp": "2026-02-28T14:25:15Z", "scan_id": "scan_20260228_141530", "files_scanned": 47, "brittle_points": 2}
{"phase": 3, "stage": "approval_required", "timestamp": "2026-02-28T14:30:00Z", "approver": "jamie", "heal_list_id": "HL-001"}
```

Every action is logged in chronological order. These logs are immutable (once written, never deleted). This is how we prove governance.

---

## Common Tasks

### Run a full diagnostic cycle (all 6 phases)

```bash
# Phase 1: Scout scan
bash scripts/ttlg_phase1_scout.sh

# Phase 2: Thinker evaluation (automatic, or manual trigger)
# [Wait for Phase 2 to complete]

# Phase 3: Review Heal List and approve (Jamie's decision)
# [Jamie reviews and approves in .env or via webhook]

# Phases 4-6: Auto-execute once approved
# [Monitor dashboards/ttlg_health.json for progress]
```

### Check diagnostic health

```bash
# See latest scan results
tail -20 logs/ttlg_diagnostics.jsonl

# See metrics dashboard
cat dashboards/ttlg_health.json | jq '.'

# See most recent AAR
ls -lrt context_vault/internal_diagnostics/aars/ | tail -1
```

### Review a specific AAR (After Action Review)

```bash
# Find all AARs
ls context_vault/internal_diagnostics/aars/

# View a specific AAR
cat context_vault/internal_diagnostics/aars/AAR-2026-02-28-T14-25-00Z.json | jq '.'
```

### Extract learning patterns

The patterns are automatically extracted and fed to Thinker guardrails. To review:

```bash
# See captured patterns
ls context_vault/patterns/

# View a pattern
cat context_vault/patterns/pattern_hardcoded_paths.json
```

---

## Troubleshooting

### "TOGETHER_API_KEY not set in .env"

**Fix:** Make sure you populated `.env` with your actual API keys (not the placeholder text).

```bash
grep TOGETHER_API_KEY .env
# Should show your actual key, not "your_actual_together_api_key_here"
```

### "Phase 1 timed out (60 minutes exceeded)"

**Fix:** Large repos may need more time. Increase timeout in `.env`:

```bash
TTLG_SCAN_TIMEOUT_MINUTES=120  # Double it
```

Or, exclude large directories:

```bash
SCAN_EXCLUDE=".git,node_modules,venv,__pycache__,*.log,vendor,dist"
```

### "Governance Gate rejected the fix"

**Fix:** Phase 3 approval failed because a fix violates the constitution. Check the approval notes:

```bash
tail -5 logs/ttlg_diagnostics.jsonl | grep approval
```

Look for the reason (e.g., "introduces vendor lock-in"). Either:
- Redesign the fix to comply, or
- Ask Jamie to approve an exception (documented in logs)

### "No API keys loaded"

**Fix:** Make sure `.env` is in the Friday root directory:

```bash
ls -la .env
# Should show: .env (readable)
```

---

## Compliance & Governance

TTLG is designed with three constitutional requirements:

### 1. No Silent Failures
Every finding is logged. Every decision is traceable.

```bash
# Verify: Check audit log for completeness
wc -l logs/ttlg_diagnostics.jsonl
# Should have entries for every phase transition
```

### 2. Permission-Gated Autonomy
Phase 3 (Governance Gate) requires Jamie's approval before any code changes.

```bash
# Verify: Check that no Phase 4 started without Phase 3 approval
grep "phase.*4" logs/ttlg_diagnostics.jsonl | head -1
# Should show "approval_granted" in prior line
```

### 3. Transparent Learning
Every AAR captures patterns that feed back into future scans.

```bash
# Verify: Check that patterns are extracted
ls context_vault/patterns/ | wc -l
# Should have at least 1 pattern per AAR
```

---

## Integration with EPOS

TTLG emits events into the Unified Nervous System:

- `diagnostic.started` → Phase 1 begins
- `diagnostic.evaluation_complete` → Phase 2 done
- `governance.approval_required` → Phase 3 waits for Jamie
- `agent.missioncompleted` → Phase 4 finishes
- `context.stored` → AAR written to vault

These events allow Friday and other nodes to react to TTLG's findings in real-time.

---

## Support & Questions

For issues or questions about TTLG:

1. **Check CLAUDE.md** — The constitutional charter explains your operating philosophy
2. **Review past AARs** — Learn from what's been fixed before
3. **Check the logs** — Audit trail shows what happened at each step
4. **Contact Jamie** — For approval, escalations, or constitutional questions

---

**Status:** 🟢 System Ready  
**Next action:** Populate `.env` with your API keys and run Phase 1
