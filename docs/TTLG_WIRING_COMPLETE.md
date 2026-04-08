# TTLG WIRING COMPLETE

**System Architecture Overview & Execution Readiness**

---

## STATUS: 🟢 SYSTEM READY FOR PHASE 1

All components are wired, chartered, and ready for the first diagnostic cycle. This document is your systems overview.

---

## WHAT YOU HAVE (Complete System)

### 1. Constitutional Framework

| Document | Purpose | Status |
|----------|---------|--------|
| `EPOS_CONSTITUTION_v3.1.md` | Governance rules (no silent failures, sovereignty, transparency) | ✓ Existing |
| `NODE_SOVEREIGNTY_CONSTITUTION.md` | Node operating principles | ✓ Existing |
| `CLAUDE.md` | TTLG Diagnostics identity & 6-phase cycle | ✓ Created |
| `CLAUDE_CODE_CHARTER.md` | Implementation agent constraints | ✓ Created |
| `FRIDAY_ORCHESTRATION_CHARTER.md` | Decision agent authority & scope | ✓ Created |

### 2. Decision & Learning Intelligence

| Document | Purpose | Status |
|----------|---------|--------|
| `FRIDAY_LEARNING_FRAMEWORK.md` | How Friday learns from outcomes | ✓ Created |
| `AGENTIC_ROLE_MAPPING.md` | Friday & Claude Code explicit roles | ✓ Created |
| `ENTRYPOINT_SPECIFICATIONS.md` | Exact CLI signatures (4 entrypoints) | ✓ Created |

### 3. Operational Documents

| Document | Purpose | Status |
|----------|---------|--------|
| `TTLG_SYSTEMS_CYCLE.md` | Internal architecture scanning | ✓ Existing |
| `TTLG_MARKET_CYCLE.md` | Market listening & validation | ✓ Existing |
| `TTLG_MODEL_ROUTING_CHARTER.md` | How Google models are selected | ✓ Existing |
| `TTLG_LOGGING_POLICY.md` | Audit trail & governance logging | ✓ Existing |
| `TTLG_LAUNCH_CHECKLIST.md` | Pre-scan verification | ✓ Existing |

### 4. Configuration & Scripts

| Component | Purpose | Status |
|-----------|---------|--------|
| `.env` (updated) | Google-exclusive API keys + configuration | ✓ Template created |
| `schemas/aar_v1.json` | After Action Review schema | ✓ Created |
| `scripts/ttlg_systems_light_scout.sh` | Phase 1 entrypoint | ✓ Template created |
| `scripts/ttlg_market_light_scout.sh` | Market Phase 1 entrypoint | ✓ Template created |
| `scripts/friday_vault_summary.sh` | Vault query entrypoint | ✓ Template created |
| `scripts/friday_check_ttlg_health.sh` | Health check entrypoint | ✓ Template created |

---

## HOW THE SYSTEM WORKS (End-to-End Flow)

### The Cycle

```
┌──────────────────────────────────────────────────────────────┐
│ FRIDAY DECISION AGENT (24/7 autonomous)                      │
├──────────────────────────────────────────────────────────────┤
│ • Observes: Systems metrics, market signals, outcomes         │
│ • Decides: Which workflow to run? When? How aggressive?      │
│ • Learns: Each scan improves her decision-making             │
│ • Governs: All decisions logged, auditable, constitutional   │
└──────────────────────────────────────────────────────────────┘
                           ↓
                   (Calls entrypoint)
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ CLAUDE CODE IMPLEMENTATION AGENT (builds when needed)         │
├──────────────────────────────────────────────────────────────┤
│ • Plans: How to execute Friday's decision                    │
│ • Builds: New tools, scripts, integrations                  │
│ • Tests: All code tested before staging                      │
│ • Awaits: Governance Gate approval for production            │
└──────────────────────────────────────────────────────────────┘
                           ↓
              (Executes with full constitution)
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ TTLG DIAGNOSTICS (Phase 1-6 autonomous cycle)                │
├──────────────────────────────────────────────────────────────┤
│ Phase 1: DECONSTRUCT (Scout scans architecture)              │
│ Phase 2: EVALUATE (Thinker prioritizes issues)              │
│ Phase 3: GOVERNANCE GATE (Jamie approves fixes)              │
│ Phase 4: RECONFIGURE (Claude Code builds fixes)             │
│ Phase 5: RECONSTRUCT (Analyst verifies results)             │
│ Phase 6: AAR (Captures learning → feeds Friday)             │
└──────────────────────────────────────────────────────────────┘
                           ↓
                  (Produces learning)
                           ↓
              (Back to FRIDAY, cycle continues)
```

### Decision Trigger Points

**Friday decides to run:**
- **Light Scout** when brittle points are medium/low severity
- **Full Cycle** when severity is high + success rate > 90%
- **Market Scout** when signal strength is growing
- **Monitoring Only** when signal is weak

**All decisions are:**
- ✅ Logged to immutable audit trail
- ✅ Traceable back to decision rules or patterns
- ✅ Governed by constitutional principles
- ✅ Visible in daily learning reports to Jamie

---

## YOUR NEXT STEPS (3 Actions)

### ACTION 1: Populate `.env` (15 min)

```bash
cd /path/to/epos_mcp
nano .env

# Add your actual OpenRouter API key:
OPENROUTER_API_KEY="sk-or-xxxxx..."

# Verify models are set:
grep SCOUT_MODEL .env
# Should output: SCOUT_MODEL=gemini-2.5-flash:free
```

**Files needed:**
- Copy `.env` template from `/mnt/user-data/outputs/.env`
- Add your OpenRouter API key
- Place in Friday root

### ACTION 2: Review Charters (30 min)

**Read these in order:**
1. `CLAUDE.md` — Understand TTLG's 6-phase cycle
2. `FRIDAY_ORCHESTRATION_CHARTER.md` — Understand Friday's decision authority
3. `FRIDAY_LEARNING_FRAMEWORK.md` — Understand how Friday learns
4. `AGENTIC_ROLE_MAPPING.md` — Understand Friday & Claude Code roles

**What to look for:**
- ✅ Where does human (Jamie) authority sit? (Phase 3 Governance Gate)
- ✅ What can each agent do autonomously? (mapped in AGENTIC_ROLE_MAPPING.md)
- ✅ How are decisions logged? (immutable audit trail)
- ✅ How does learning happen? (AAR → patterns → Friday's guardrails)

### ACTION 3: Run Pre-Scan Checklist (30 min)

```bash
# Complete all 8 sections of PRE_SCAN_VERIFICATION_CHECKLIST.md
# This verifies:
# - Environment is healthy
# - Config is valid
# - Governance is enforced
# - APIs are accessible
# - Entrypoints are ready
# - Learning framework is wired

# Run epos_doctor.py first
python epos_doctor.py --mode quick
# Should show all green

# Then verify each section of checklist
# Section 1: Environment health
# Section 2: Configuration
# ... (8 sections total)

# Final step: Get Jamie's sign-off
# Once all pass, Jamie approves and we trigger Phase 1
```

---

## CRITICAL DECISION POINTS (What You Need to Approve)

### Before Phase 1 Runs

**Jamie must approve:**
- [ ] Environment is clean and constitutional checks pass
- [ ] API keys are correct (OpenRouter account has quota)
- [ ] Governance rules are understood (no bypassing Phase 3)
- [ ] Learning framework is acceptable (how Friday improves decisions)
- [ ] Entrypoint specifications are clear (Friday can call Claude Code)

### After Phase 1 Completes

**Jamie must review:**
- Scout output (what was scanned, what was found)
- Brittle points identified (severity, file locations)
- Ready to proceed to Phase 2? (or pause for investigation?)

### After Phase 2 Completes

**Jamie must approve:**
- Heal List (proposed fixes, ROI impact, constitutional alignment)
- Authorization: Proceed to Phase 4? (or reject/redesign?)
- Approval timeline: Standard (24 hrs) or expedited (4 hrs)?

### After Phase 6 Completes

**Jamie will review:**
- AAR (what was learned from this cycle)
- New patterns discovered (how Friday's future decisions improve)
- Learning quality assessment

---

## MONITORING & HEALTH CHECKS

### Daily

**Friday automatically runs:**
```bash
06:00 AM: friday_check_ttlg_health          # Verify systems operational
06:05 AM: friday_vault_summary             # Get context
06:10 AM: ttlg_systems_light_scout         # Quick scan (or full cycle)
06:30 AM: ttlg_market_light_scout          # Market listening
14:00 PM: friday_check_ttlg_health         # Afternoon check
20:00 PM: friday_vault_summary             # Evening context for report
```

### What You See Each Morning

Friday generates a daily learning report:
- Decisions made (14 decisions logged, 100% compliant)
- Top patterns (confidence scores, uses)
- Surprises (anything unexpected)
- Recommendations (next actions)
- Learning velocity (improving? stable? declining?)

---

## MODEL SELECTION (Google-Exclusive Architecture)

All models are from Google's Gemini family, accessed via OpenRouter:

| Phase | Model | Purpose | Context |
|-------|-------|---------|---------|
| **Scout (Phase 1)** | `gemini-2.5-flash:free` | Rapid architecture scan | 1M tokens |
| **Thinker (Phase 2)** | `gemini-3.1-pro-preview:free` | Complex reasoning + ROI | 128K tokens |
| **Analyst (Phase 5)** | `gemini-2.5-flash:free` | Fast verification | 1M tokens |
| **Nervous System** | `gemma-3-27b-it:free` | Event classification | 64K tokens |

**Benefits:**
- ✅ Single provider (Google), easy to maintain
- ✅ All models accessed via OpenRouter (one API key)
- ✅ `:free` variants available (cost-effective)
- ✅ Compatible with TTLG charter constraints

---

## AUDIT & GOVERNANCE PROOF

Everything is logged to immutable audit trail:

```
logs/ttlg_diagnostics.jsonl

# Every entry includes:
# - Timestamp (ISO 8601)
# - Phase (1-6 or decision/learning)
# - Actor (scout, thinker, friday, claude code)
# - Decision/action taken
# - Constitutional check result
# - Outcome

# Example:
{"phase": 1, "stage": "started", "timestamp": "2026-02-28T14:00:00Z", ...}
{"phase": 1, "stage": "completed", "timestamp": "2026-02-28T14:30:00Z", ...}
{"phase": 2, "stage": "started", "timestamp": "2026-02-28T14:30:00Z", ...}
{"phase": 3, "stage": "approval_required", "timestamp": "2026-02-28T14:45:00Z", ...}
```

**Proof that you maintain control:**
- ✅ Every decision logged (no secret operations)
- ✅ Governance checks validated (constitution enforced)
- ✅ Approval gates recorded (Jamie's decisions captured)
- ✅ Audit trail immutable (once logged, never deleted)

---

## GOVERNANCE GUARANTEE

TTLG **cannot:**
- ❌ Execute code without Phase 3 approval
- ❌ Bypass governance rules
- ❌ Make decisions without logging
- ❌ Hide findings from audit trail
- ❌ Violate constitutional principles

TTLG **will:**
- ✅ Report every finding (even low-severity issues)
- ✅ Log every decision (immutable record)
- ✅ Respect Jamie's authority (approval gate enforced)
- ✅ Maintain constitutional alignment (rules engine validates)
- ✅ Improve over time (learning compounds)

---

## ESTIMATED OUTCOMES (First 30 Days)

### Week 1
- Phase 1 Scout completes (identify 2-3 brittle points)
- Phase 2 Thinker evaluates (generate Heal List)
- Phase 3 Governance Gate (Jamie approves fixes)
- Phase 4-5 Execute & verify (fixes deployed, verified)
- Phase 6 AAR (learning captured)

**Result:** EPOS healthier, Friday's first 2-3 patterns discovered

### Week 2-3
- Light scout cycle runs (quicker now, Friday recognizes patterns)
- Market listening kicks in (signal tracking starts)
- Friday's learning updates (confidence scores improve)
- Decision journal accumulates (10-15 logged decisions)

**Result:** Friday's confidence increases (patterns validated)

### Week 4
- Full cycle completes (comprehensive EPOS health check)
- Learning report generated (patterns ranked by confidence)
- Market concepts tested (echolocation validation)
- Jamie reviews learning quality

**Result:** System stability improves, Friday's decisions become predictive

---

## FILES TO COPY TO FRIDAY ROOT

**From `/mnt/user-data/outputs/`, copy to `/path/to/epos_mcp/`:**

```
.env                                     → .env
CLAUDE.md                                → CLAUDE.md
FRIDAY_LEARNING_FRAMEWORK.md             → FRIDAY_LEARNING_FRAMEWORK.md
AGENTIC_ROLE_MAPPING.md                  → AGENTIC_ROLE_MAPPING.md
ENTRYPOINT_SPECIFICATIONS.md             → ENTRYPOINT_SPECIFICATIONS.md
PRE_SCAN_VERIFICATION_CHECKLIST.md       → PRE_SCAN_VERIFICATION_CHECKLIST.md
TTLG_WIRING_COMPLETE.md                  → TTLG_WIRING_COMPLETE.md
aar_v1.json                              → schemas/aar_v1.json
ttlg_phase1_scout.sh                     → scripts/ttlg_systems_light_scout.sh
```

---

## COMMANDS TO RUN

### Step 1: Setup
```bash
cd /path/to/epos_mcp
python epos_doctor.py --mode quick
# Should show all green
```

### Step 2: Verify Configuration
```bash
source .env
echo "Scout: $SCOUT_MODEL"
# Should show: gemini-2.5-flash:free
```

### Step 3: Complete Pre-Scan Checklist
```bash
# Read PRE_SCAN_VERIFICATION_CHECKLIST.md
# Run all 8 sections
# Get Jamie's sign-off
```

### Step 4: Trigger Phase 1
```bash
bash scripts/ttlg_systems_light_scout.sh \
  --targets "governance_gate,context_vault" \
  --scan-id "scan_$(date +%Y%m%d_%H%M%S)" \
  --intensity "light" \
  --timeout-minutes 60
```

### Step 5: Monitor
```bash
tail -f logs/ttlg_diagnostics.jsonl
# Watch scan progress in real-time
```

---

## WHAT HAPPENS WHEN PHASE 1 COMPLETES

Scout will produce:
- ✅ `context_vault/scans/scan_*/scout_output.json` (dependency graph)
- ✅ Brittle points identified with severity levels
- ✅ Log entries in `logs/ttlg_diagnostics.jsonl`
- ✅ Ready for Phase 2 (Thinker evaluation)

You will see:
```
🔍 TTLG Diagnostics Phase 1: DECONSTRUCT
========================================
✓ Environment loaded
📋 Scan ID: scan_20260228_140000
🚀 Triggering Scout scan...
✓ Scout output saved
📊 Phase 1 Summary:
  Files scanned: 12
  Dependencies mapped: 45
  Brittle points found: 2
✅ Phase 1 COMPLETE
```

---

## RISK MITIGATION

### If Phase 1 Fails
- Entire cycle halts
- Governance Gate prevents Phase 2 execution
- Error logged with full context
- Jamie investigates, approves next steps

### If Phase 4 (Fix) Causes Regressions
- Phase 5 (Analyst) detects it
- Fix is flagged as failed
- Governance Gate blocks production deployment
- Claude Code reverts to staging

### If Learning is Invalid
- Confidence score automatically decays
- Jamie can reject pattern ratification
- Pattern not used in future decisions
- System errs on side of caution

---

## SUCCESS CRITERIA

TTLG is successful when:

✅ **Phase 1:** Scans 100% of target codebase (no blind spots)  
✅ **Phase 2:** Every issue traces to constitutional principle or ROI  
✅ **Phase 3:** Jamie approves/rejects fixes (not auto-approved)  
✅ **Phase 4:** Fixes pass regression tests (no new problems)  
✅ **Phase 5:** Verification passes market benchmarks  
✅ **Phase 6:** Each scan produces 1+ actionable learning pattern  
✅ **Governance:** 100% audit trail, immutable logs  
✅ **Learning:** Friday's confidence improves over time  

---

## FINAL CHECKLIST (Jamie's Decision Gate)

Before we trigger Phase 1, confirm:

- [ ] All charter files are in place and understood
- [ ] `.env` is populated with valid OpenRouter API key
- [ ] Pre-scan verification checklist completed (all 8 sections pass)
- [ ] epos_doctor.py shows clean environment
- [ ] Governance Gate approval required (enforced)
- [ ] Audit logging enabled (immutable)
- [ ] Learning framework understood (Friday improves decisions)
- [ ] Ready to proceed to Phase 1

**Jamie's sign-off:**
- [ ] I have read the charters and understand the system
- [ ] I approve proceeding to Phase 1 Scout scan
- [ ] I understand my authority (Phase 3 approval gate)
- [ ] Timestamp: _________________
- [ ] Signature: _______________________

---

**STATUS: 🟢 READY FOR PHASE 1**

Once Jamie approves above, run:
```bash
bash scripts/ttlg_systems_light_scout.sh --targets "governance_gate,context_vault" --scan-id "scan_$(date +%Y%m%d_%H%M%S)" --intensity "light" --timeout-minutes 60
```

**The autonomous healing loop begins.**

