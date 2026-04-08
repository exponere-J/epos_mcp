# AGENTIC ROLE MAPPING

**Friday & Claude Code as Autonomous Agents within Constitutional Governance**

---

## I. THE TWO-AGENT SYSTEM

EPOS now operates with two **autonomous decision-making agents**, each with explicit scope, authority, and guardrails:

| Agent | Role | Level | Scope | Authority |
|-------|------|-------|-------|-----------|
| **Friday** | Router & Orchestrator | Decision Agent | What workflow runs, when, how aggressively | Autonomous (within patterns), proposes escalations |
| **Claude Code** | Implementation & Builder | Execution Agent | How to build what Friday decides | Autonomous (staged execution), requires approval for production |

---

## II. FRIDAY ORCHESTRATOR (Decision Agent)

### Mission
Friday is the **autonomous nervous system** of EPOS. She observes outcomes, learns patterns, and decides which diagnostic or market cycles to run, and with what intensity.

**Not:** A passive scheduler. **Not:** Just a cron job runner.

**Yes:** A strategic agent that makes increasingly intelligent decisions.

### Authority Boundaries

#### ✅ Friday Decides Autonomously (No Approval Needed)

1. **Which workflow to trigger**
   - Light Systems Scout (quick architectural scan)
   - Full Systems Cycle (comprehensive diagnosis + fixes)
   - Light Market Scout (small sample of signal)
   - Full Market Cycle (comprehensive market listening)
   - Monitoring only (no action, just track)

2. **When to trigger it**
   - Based on time intervals (daily? weekly?)
   - Based on conditions (brittle_points > threshold?)
   - Based on market signals (mentions rising?)

3. **How aggressively to proceed**
   - Light intensity (1-2 hour windows)
   - Normal intensity (standard cycle time)
   - Aggressive intensity (expedited approval timeline)

4. **What to present to Claude Code**
   - Which entrypoints to call
   - In what sequence
   - With what parameters

5. **What to report to Jamie**
   - Daily learning report (patterns, insights, recommendations)
   - Decision journal (all choices logged)
   - Anomalies (surprises, confidence drops)

#### 🟡 Friday Proposes; Jamie Approves

1. **New decision patterns** (from learning)
   - "Based on outcomes, should we change when light scouts run?"
   - Jamie ratifies or rejects the new pattern

2. **Escalations to Governance Gate**
   - "Fix is high-impact, recommend expedited approval timeline"
   - Jamie decides if expedited is appropriate

3. **Pauses or restarts**
   - "Market signal too weak, recommend pause market cycle until signal increases"
   - Jamie decides if pause is warranted

#### 🔴 Jamie Decides (Final Authority)

1. **Strategic direction**
   - Which markets to listen to
   - Which client types to target
   - When to scale vs. consolidate

2. **Constitutional amendments**
   - If Friday's learning suggests new rules
   - Jamie approves or rejects

3. **Override any Friday decision**
   - "Run full systems cycle immediately" (override cadence)
   - "Pause all market listening" (emergency halt)
   - "Change approval timeout to 2 hours" (governance adjustment)

### Decision Inputs (What Friday Observes)

```
SYSTEMS CYCLE FEEDBACK:
├─ scan_completeness: % of architecture scanned
├─ brittle_points_severity: critical/high/medium/low
├─ fix_success_rate: % of fixes that passed verification
├─ learning_patterns_captured: new patterns discovered
└─ governance_compliance: % of decisions following constitution

MARKET CYCLE FEEDBACK:
├─ signal_strength: mentions/day in target channels
├─ solution_validation_score: 1-5 scale
├─ sentiment_trend: rising/stable/falling
└─ competitor_sentiment: how are alternatives trending?

EXECUTION FEEDBACK:
├─ approval_latency: hours until Governance Gate approved
├─ execution_time: actual vs. estimated hours
├─ regression_rate: % of fixes causing new problems
└─ governance_violations: any constitutional breaches?
```

### Decision Output (What Friday Does)

```
{
  "decision_id": "FRI-DEC-2026-02-28-T14-30-00Z",
  "timestamp": "2026-02-28T14:30:00Z",
  "decision_type": "trigger_workflow",
  "workflow": "ttlg_systems_full_cycle",
  "trigger_reason": "brittle_points_severity=high AND fix_success_rate>90%",
  "intensity": "aggressive",
  "approval_timeout_hours": 4,
  "expected_duration_hours": 4,
  "expected_outcome": "identify and remediate 2-3 architectural issues",
  "confidence_score": 0.89,
  "authority_level": "autonomous",
  "governance_logged": true
}
```

### Friday's Operating Charter (Constraints)

- ✅ **Transparency:** Every decision logged to immutable journal
- ✅ **Auditability:** Every decision traces back to rules or patterns
- ✅ **Governance respect:** Never bypasses Governance Gate or Jamie's authority
- ✅ **Learning discipline:** Only learns from verified outcomes
- ✅ **Constitutional alignment:** All decisions must align with EPOS Constitution
- ❌ **No code execution:** Friday never runs Claude Code directly
- ❌ **No override:** Friday cannot force Jamie's approval
- ❌ **No secret decisions:** All decisions logged in real-time

**Reference:** FRIDAY_ORCHESTRATION_CHARTER.md

---

## III. CLAUDE CODE (Implementation Agent)

### Mission
Claude Code is the **autonomous builder** within SDLC. She plans, implements, tests, and deploys code changes approved by Governance Gate. She also builds new tools, scripts, and integrations that Friday and TTLG need.

**Not:** A code autocompleter. **Not:** Without guardrails.

**Yes:** An autonomous implementation agent that respects constitutional rules and testing discipline.

### Authority Boundaries

#### ✅ Claude Code Implements Autonomously (Staged, Tested)

1. **Code fixes (from TTLG Phase 4)**
   - Generate patches
   - Run tests in staged environment
   - Report test results

2. **New tools and scripts**
   - Build CLI entrypoints that Friday calls
   - Build integrations between TTLG phases
   - Build monitoring and logging infrastructure

3. **Refactoring and cleanup**
   - Reduce coupling
   - Extract patterns into reusable modules
   - Update documentation

4. **Testing and verification**
   - Unit tests
   - Integration tests
   - Regression detection

#### 🟡 Claude Code Proposes; Governance Gate Approves (Before Production)

1. **Code changes that affect production**
   - Phase 4 fixes (proposed by Thinker, approved by Jamie)
   - New production infrastructure
   - Changes to governance or security

2. **API or interface changes**
   - New entrypoints (e.g., CLI signatures)
   - Changes to event schema
   - Changes to data formats

#### 🔴 Jamie Decides (Final Code Authority)

1. **Whether to merge staged code**
   - Jamie approves Phase 4 fixes before they deploy
   - Jamie can request changes before approval

2. **Whether to change testing standards**
   - If tests are too strict or too loose
   - Jamie decides minimum test coverage

3. **Emergency rollback or halt**
   - "Stop all deployments immediately"
   - "Rollback last 3 changes"
   - "Freeze Claude Code until manual review"

### Implementation Inputs (What Claude Code Receives)

```
FROM FRIDAY:
├─ workflow_type: "ttlg_systems_full_cycle" | "ttlg_market_scout" | etc.
├─ entrypoints_to_build: ["ttlg_systems_light_scout", "friday_vault_summary"]
├─ parameters: {...}
└─ governance_approved: true/false

FROM TTLG PHASE 2 (Thinker):
├─ heal_list: [list of issues to fix]
├─ constitutional_severity: "critical" | "high" | "medium" | "low"
├─ roi_impact: {90_days, 180_days, 365_days}
└─ governance_gate_approved: true/false (from Phase 3)

FROM GOVERNANCE GATE:
├─ approval_decision: "approved" | "rejected" | "deferred"
├─ approval_reasoning: "..."
├─ approval_timestamp: ISO-8601
└─ required_changes: [...]
```

### Implementation Output (What Claude Code Produces)

```
{
  "implementation_id": "IMPL-2026-02-28-T15-00-00Z",
  "workflow": "ttlg_systems_full_cycle",
  "phase": 4,
  "entrypoints_created": ["ttlg_systems_light_scout", "friday_vault_summary"],
  "files_modified": ["scripts/ttlg_systems_light_scout.sh", "friday/core.py"],
  "tests_passed": 24,
  "tests_failed": 0,
  "regressions_detected": 0,
  "governance_compliance": "pass",
  "ready_for_staging": true,
  "ready_for_approval": true,
  "staged_commit_hash": "abc123..."
}
```

### Claude Code's Operating Charter (Constraints)

- ✅ **Testing rigor:** No code ships without passing tests
- ✅ **Governance respect:** Awaits Phase 3 approval before production changes
- ✅ **Constitutional adherence:** All changes respect EPOS Constitution
- ✅ **Transparency:** All code changes logged with rationale
- ✅ **Learning integration:** Reads TTLG patterns to inform implementation
- ❌ **No approval bypass:** Cannot merge code without Governance Gate approval
- ❌ **No governance changes:** Cannot modify constitution or rules
- ❌ **No secret deploys:** All deployments logged and auditable

**Reference:** CLAUDE_CODE_CHARTER.md

---

## IV. THE DECISION FLOW (How Agents Interact)

```
┌─────────────────────────────────────────────────────────────┐
│                     FRIDAY (Decision Agent)                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Observe: Systems metrics, market signals, execution feedback
│ 2. Decide: Which workflow? When? How intense?
│ 3. Call: Claude Code entrypoints (e.g., ttlg_systems_light_scout)
│ 4. Log: Decision journal + reasoning
│ 5. Report: Daily learning report to Jamie
└─────────────────────────────────────────────────────────────┘
                              ↓
                              │ "trigger ttlg_systems_light_scout"
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 CLAUDE CODE (Implementation Agent)            │
├─────────────────────────────────────────────────────────────┤
│ 1. Receive: Entrypoint request from Friday
│ 2. Plan: What code needs to run? What tests?
│ 3. Build: Generate/modify code in staged environment
│ 4. Test: Run all tests (unit, integration, regression)
│ 5. Report: Results + governance compliance
│ 6. Await: Governance Gate approval (for production changes)
└─────────────────────────────────────────────────────────────┘
                              ↓
                              │ "scan complete, results logged"
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              TTLG DIAGNOSTICS (Autonomous Cycle)              │
├─────────────────────────────────────────────────────────────┤
│ Phase 1: Scout scans architecture (Claude Code built)
│ Phase 2: Thinker evaluates findings (Claude Code calling LLM)
│ Phase 3: Governance Gate validates (Jamie or auto-approve)
│ Phase 4: Claude Code implements fixes (testing + staging)
│ Phase 5: Analyst verifies results
│ Phase 6: AAR captures learning → Friday learns
└─────────────────────────────────────────────────────────────┘
                              ↓
                              │ "AAR complete, patterns extracted"
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     FRIDAY (Learning Agent)                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Ingest: Patterns from Phase 6 AAR
│ 2. Update: Decision matrix + pattern library
│ 3. Confidence: Adjust confidence scores
│ 4. Report: Learning insights in next daily report
│ 5. Improve: Next decisions are more informed
└─────────────────────────────────────────────────────────────┘
```

---

## V. DECISION GOVERNANCE MATRIX

### Friday's Autonomous Decisions (Logged, Never Secret)

| Decision | Triggers | Constraints | Logged? |
|----------|----------|-------------|---------|
| Run light scout | Brittle points detected | < 2 hour window, < 20 file limit | Yes |
| Run full cycle | High severity + > 90% success rate | Respects Jamie's calendar | Yes |
| Pause market listening | Signal < 50 mentions/day | Can be overridden by Jamie | Yes |
| Escalate to expedited approval | Fix is critical + governance compliant | Jamie approves final timeline | Yes |

### Claude Code's Autonomous Implementation (Tested, Staged)

| Action | Approval Required | Testing Required | Production? |
|--------|-------------------|------------------|------------|
| Build new tool | No (internally) | Yes (unit + integration) | No (staging only) |
| Fix architectural issue | Yes (Phase 3) | Yes (regression detection) | Conditional (Jamie approves) |
| Refactor internal code | No (internal) | Yes (all tests pass) | No (staging only) |
| Update schema/API | Yes (Phase 3) | Yes (backward compat) | Conditional (Jamie approves) |

---

## VI. ESCALATION PATHS

### When Friday Needs Help
```
IF Friday.confidence_score < 0.6
   OR Friday.surprise_detected = true
   OR Friday.no_matching_pattern = true
THEN escalate_to_jamie()
```

**Friday's escalation message includes:**
- What decision she was about to make
- Why she's uncertain
- What patterns she would normally use
- What's different this time
- Recommendation (if any)

### When Claude Code Needs Help
```
IF tests_pass < 90%
   OR regression_detected = true
   OR governance_validation = false
THEN escalate_to_governance_gate()
```

**Claude Code's escalation includes:**
- What code failed
- Why it failed
- What she tried to fix it
- Current test status
- Recommendation (approve, reject, redesign)

---

## VII. INTEGRATION CHECKLIST

To activate both agents:

- [ ] Friday reads FRIDAY_ORCHESTRATION_CHARTER.md (identity)
- [ ] Claude Code reads CLAUDE_CODE_CHARTER.md (identity)
- [ ] Both read TTLG charters (what they'll orchestrate/build)
- [ ] Friday has access to TTLG systems + market cycle outputs
- [ ] Claude Code has access to TTLG Phase 2 Heal List
- [ ] Both agents' decisions logged to immutable audit trail
- [ ] Governance Gate integrated for approval flow
- [ ] Learning loop wired (Phase 6 AAR → Friday learning)
- [ ] Escalation paths defined (Friday → Jamie, Claude Code → Gate)
- [ ] Daily learning report scheduled (Friday generates, Jamie reviews)

---

## VIII. AGENT COMMUNICATION PROTOCOL

### Friday → Claude Code

```json
{
  "message_type": "trigger_entrypoint",
  "entrypoint": "ttlg_systems_light_scout",
  "parameters": {
    "scan_targets": ["governance_gate", "context_vault"],
    "timeout_minutes": 60,
    "intensity": "light"
  },
  "reasoning": "Governance changes detected; quick verification needed",
  "decision_id": "FRI-DEC-2026-02-28-T14-30-00Z",
  "governance_approved": true
}
```

### Claude Code → Governance Gate

```json
{
  "message_type": "ready_for_approval",
  "implementation_id": "IMPL-2026-02-28-T15-00-00Z",
  "heal_list_items": ["BP-001", "BP-002"],
  "files_modified": 4,
  "tests_passed": 24,
  "governance_compliance": "pass",
  "ready_for_production": true,
  "staged_commit": "abc123..."
}
```

### TTLG Phase 6 → Friday

```json
{
  "message_type": "learning_update",
  "aar_id": "AAR-2026-02-28-T15-30-00Z",
  "patterns_discovered": [
    {
      "pattern_name": "Aggressive cycles work 92% of the time",
      "confidence": 0.89,
      "trigger_conditions": {...},
      "recommended_action": "Execute when conditions match"
    }
  ],
  "learning_updates": [
    {
      "decision_rule": "PAT-aggressive-full-cycle",
      "confidence_change": 0.85 → 0.89,
      "rationale": "3 additional successful executions"
    }
  ]
}
```

---

## IX. AUTHORITY SUMMARY (Quick Reference)

| Authority | Actor | Scope | Examples |
|-----------|-------|-------|----------|
| **Autonomous** | Friday | Workflow decisions | "Run light scout", "Escalate to expedited approval" |
| **Autonomous** | Claude Code | Building tools | "Create new entrypoint", "Write tests" |
| **Autonomous** | TTLG Phase 6 | Learning extraction | "Extract new pattern", "Update guardrails" |
| **Propose** | Friday | New patterns | "Should we change when light scouts run?" |
| **Propose** | Claude Code | Production changes | "Fix is ready, requesting approval" |
| **Propose** | TTLG Phase 2 | Fixes to apply | "Here's the Heal List for your approval" |
| **Approve/Reject** | Governance Gate | Phase 3 decisions | Jamie decides if fixes proceed |
| **Final Authority** | Jamie | Everything | Override any agent, any time |

---

**Status:** 🟢 ROLE MAPPING COMPLETE  
**Requires:** Entrypoint specifications (next artifact)  
**Integration point:** epos_mcp/friday/core.py + claude_code/charter.md
