# FRIDAY LEARNING FRAMEWORK

**The Decision Intelligence System for Autonomous Orchestration**

---

## I. MISSION

Friday is no longer a passive scheduler. She is a **decision agent** that:
- Observes outcomes from both TTLG cycles (systems + market)
- Learns patterns about which workflows succeed and why
- Makes increasingly intelligent choices about *what to run*, *when*, and *how aggressively*
- Logs every decision for audit and learning (governance maintained)

---

## II. THE THREE DECISION LOOPS

### Loop 1: Systems Cycle Feedback
**Source:** TTLG Systems diagnostics (internal EPOS scanning)

Friday observes:
- `scan_completeness`: Did the scan capture 100% of architecture?
- `brittle_points_severity`: Are we finding critical vs. low-risk issues?
- `fix_success_rate`: When Phase 4 executes, do fixes pass verification?
- `learning_patterns_captured`: Is each scan producing 1+ new patterns?

**Learning:** "When brittle_points_severity is HIGH, run full diagnostic cycle. When LOW, light scout suffices."

### Loop 2: Market Cycle Feedback
**Source:** TTLG Market listening and echolocation validation

Friday observes:
- `signal_strength`: How much social chatter about this domain?
- `solution_validation_score`: Did the market respond to our messages?
- `concept_confidence`: How many personas confirmed this pain point?
- `sentiment_trend`: Is this pain rising, stable, or declining in market?

**Learning:** "When validation_score > 3.5, move concept to build phase. When < 2.0, archive and monitor."

### Loop 3: Execution Feedback
**Source:** Claude Code & Governance Gate outcomes

Friday observes:
- `approval_latency`: How long did Jamie take to approve fixes?
- `execution_time`: Did Claude Code deliver in estimated hours?
- `regression_rate`: Did fixes introduce new problems?
- `governance_compliance`: Were all constitutional rules respected?

**Learning:** "When regression_rate > 5%, slow down. When < 2%, accelerate approval."

---

## III. FRIDAY'S DECISION MATRIX

Before running any workflow, Friday consults her decision matrix:

```
IF systems_brittle_points_severity = CRITICAL
   AND fix_success_rate > 90%
   AND governance_compliance = 100%
THEN run FULL_TTLG_SYSTEMS_CYCLE
   WITH intensity = "aggressive"
   AND approval_timeout = "4 hours" (expedited)

IF systems_brittle_points_severity = MEDIUM
   AND last_scan_was_3_days_ago
THEN run LIGHT_SCOUT_ONLY
   WITH intensity = "quick"
   AND scope = "targeted"

IF market_signal_strength > 500_mentions
   AND solution_validation_score > 3.5
   AND competitor_sentiment_trend = "declining"
THEN run FULL_MARKET_CYCLE
   WITH cadence = "weekly"
   AND content_intensity = "high"

IF market_signal_strength < 100_mentions
   OR solution_validation_score < 1.5
THEN run MONITORING_ONLY
   WITH cadence = "monthly"
   AND action = "PAUSE_and_ARCHIVE"
```

---

## IV. FRIDAY'S MEMORY ARCHITECTURE

### What Friday Remembers (Persistent)

**Decision Journal** (logs every choice):
```json
{
  "decision_id": "DEC-2026-02-28-T14-30-00Z",
  "timestamp": "2026-02-28T14:30:00Z",
  "trigger": "systems_cycle_complete",
  "context": {
    "brittle_points_severity": "high",
    "fix_success_rate": 0.92,
    "governance_compliance": 1.0,
    "last_scan_age_days": 1,
    "approval_latency_hours": 2.5
  },
  "decision": "RUN_FULL_TTLG_SYSTEMS_CYCLE",
  "intensity": "aggressive",
  "rationale": "High severity + excellent track record warrants full cycle with expedited approval",
  "expected_outcome": "identify and fix 2-3 architectural issues within 4 hours",
  "actual_outcome": "identified 3 issues, 2 fixed in 3.5 hours, 1 deferred",
  "outcome_match": "EXCEEDED_EXPECTATIONS",
  "learning_updated": true
}
```

**Outcome Pattern Library**:
```json
{
  "pattern_id": "PAT-aggressive-full-cycle",
  "pattern_name": "Aggressive Full TTLG Cycle Success Pattern",
  "trigger_conditions": {
    "brittle_points_severity": "high",
    "fix_success_rate": ">85%",
    "governance_compliance": ">95%"
  },
  "historical_outcomes": [
    {"success_rate": 0.92, "time_hours": 3.5},
    {"success_rate": 0.88, "time_hours": 4.2},
    {"success_rate": 0.95, "time_hours": 3.1}
  ],
  "avg_success_rate": 0.917,
  "confidence": "high",
  "recommendation": "Execute this pattern when triggers align"
}
```

**Market Sentiment Tracker**:
```json
{
  "domain": "agentic_web_browsing_security",
  "signal_history": [
    {"date": "2026-02-21", "mentions": 45, "sentiment": "negative"},
    {"date": "2026-02-23", "mentions": 67, "sentiment": "negative"},
    {"date": "2026-02-27", "mentions": 124, "sentiment": "strongly_negative"},
    {"date": "2026-02-28", "mentions": 156, "sentiment": "strongly_negative"}
  ],
  "trend": "RISING",
  "trend_confidence": "high",
  "recommendation": "Increase market listening cadence; concept validation imminent"
}
```

### What Friday Forgets (Ephemeral)

- Raw log entries older than 90 days (preserved in TTLG audit trail)
- Duplicate patterns (consolidated into single decision rule)
- Failed hypotheses (archived, not actively learned from)

---

## V. FRIDAY'S LEARNING MECHANISMS

### Mechanism 1: Outcome Clustering
When multiple decisions lead to similar outcomes, Friday groups them:

```
CLUSTER: "Quick Scout Followed by Light Integration"
├─ Decision 1: Light scout on governance.py → 2 issues, 1.5 hours
├─ Decision 2: Light scout on context_vault.py → 3 issues, 1.8 hours
├─ Decision 3: Light scout on event_bus.py → 2 issues, 1.4 hours
└─ PATTERN: Light scans take ~1.5 hours, find ~2.3 issues avg.
   CONFIDENCE: 0.89 (3 observations)
   RECOMMENDATION: Schedule light scans in 2-hour windows
```

### Mechanism 2: Counterfactual Analysis
When an outcome surprises Friday, she analyzes what *would* have happened if she'd made a different choice:

```
ACTUAL DECISION: Approved expedited fix without full verification
ACTUAL OUTCOME: Fix caused 2 regressions (governance_compliance = 0.92)
CONFIDENCE: Below threshold

COUNTERFACTUAL: "What if I'd requested Phase 5 verification?"
ANALYSIS: Would have caught regressions before deployment
IMPACT: Would have added 1 hour but prevented 6 hours of debugging
LEARNING: Future fixes require Phase 5 even when time-constrained
UPDATE: Decision rule modified to always include verification
```

### Mechanism 3: Confidence Decay
Friday's confidence in old patterns decays over time. Stale learnings get re-validated:

```
PATTERN: "Aggressive cycles work 92% of the time"
├─ Confidence (current): 0.89
├─ Last validated: 8 days ago
├─ Decay factor: 0.98 (per day)
└─ Current effective confidence: 0.89 × 0.98^8 = 0.75
    → Friday will seek re-validation before using pattern
```

### Mechanism 4: Surprise-Driven Learning
When outcomes deviate >15% from predictions, Friday flags for manual review:

```
PREDICTED: Light scout takes 1.5 hours
ACTUAL: Light scout took 4.2 hours
DEVIATION: +180% (SURPRISE!)

ACTION: Log high-priority learning event
QUESTION: "What changed? New codebase size? API latency? Network issues?"
OUTPUT: Decision journal + request for Jamie's context
```

---

## VI. FRIDAY'S DECISION GOVERNANCE

### Authority Boundaries

**Friday decides autonomously:**
- Which workflow to run (light scout vs. full cycle)
- When to run it (cadence, timing)
- How to present findings to Claude Code
- ✅ **Logged, auditable, learnable**

**Friday proposes; Jamie approves:**
- Whether to execute a fix (Phase 3 Governance Gate)
- Whether to update decision rules
- Whether to pause/restart cycles
- ✅ **Constitutional compliance maintained**

**Jamie decides (final authority):**
- Whether to ratify new learning patterns
- Whether to override Friday's recommendations
- Whether to change decision matrix
- ✅ **Human stewardship preserved**

### Governance Log Entry (Every Decision)

```json
{
  "decision_log_id": "GOVLOG-2026-02-28-T14-30-00Z",
  "decision_id": "DEC-2026-02-28-T14-30-00Z",
  "actor": "friday_orchestrator",
  "action": "RUN_FULL_TTLG_SYSTEMS_CYCLE",
  "authority_level": "autonomous",
  "constitutional_check": "PASSED",
  "rules_consulted": ["PAT-aggressive-full-cycle", "PAT-governance-compliance-threshold"],
  "decision_logged": true,
  "governance_compliant": true,
  "timestamp": "2026-02-28T14:30:00Z"
}
```

---

## VII. FRIDAY'S LEARNING DISPLAY (Dashboard)

Every morning, Friday generates a report:

```
═══════════════════════════════════════════════════════════════
FRIDAY LEARNING REPORT | 2026-02-28
═══════════════════════════════════════════════════════════════

📊 DECISION HISTORY (Last 7 days)
├─ Decisions made: 14
├─ Decisions logged: 14 (100% governance compliant)
├─ Success rate: 0.93 (13 of 14 exceeded expectations)
└─ Avg decision time: 2.3 minutes

🎯 TOP PATTERNS (High Confidence)
1. PAT-aggressive-full-cycle (confidence: 0.89, uses: 4)
2. PAT-light-scout-for-stability (confidence: 0.85, uses: 8)
3. PAT-market-signal-threshold (confidence: 0.91, uses: 6)

⚠️ SURPRISES (Require Attention)
1. SURPRISE-001: Light scout took 4.2 hrs (expected 1.5)
   → Investigating: New codebase complexity? API latency?
   → Status: FLAGGED_FOR_HUMAN_REVIEW

🚀 RECOMMENDED NEXT ACTIONS
1. Run Phase 1 Systems scan (brittle points at HIGH)
2. Accelerate market listening (signal trending UP)
3. Request Jamie's input on SURPRISE-001 before proceeding

📈 LEARNING VELOCITY
├─ New patterns discovered: 2 (last 7 days)
├─ Existing patterns validated: 6
├─ Confidence avg: 0.87 (↑ from 0.83 last week)
└─ Learning quality: IMPROVING

═══════════════════════════════════════════════════════════════
```

---

## VIII. INTEGRATION WITH TTLG CYCLES

### Systems Cycle → Friday Learning

```
TTLG Phase 6 AAR (learning artifacts)
    ↓
Friday ingests patterns
    ↓
Friday updates decision matrix
    ↓
Next systems scan decisions are more informed
    ↓
Virtuous cycle: EPOS gets healthier, Friday gets smarter
```

### Market Cycle → Friday Learning

```
TTLG Market validation (echolocation scores)
    ↓
Friday observes concept_validation_score
    ↓
Friday decides: Move to build? Archive? Continue testing?
    ↓
Outcome feeds back (customer response, market chatter)
    ↓
Friday refines product roadmap decisions
```

---

## IX. FAILURE MODE DETECTION

Friday automatically flags decisions that produce unexpected outcomes:

```
DECISION: "Run light scout (low intensity)"
EXPECTATION: 1-2 issues, 1.5 hours
ACTUAL: 8 issues, 3 hours, governance_compliance = 0.88
MATCH: MISMATCH (confidence drop from 0.85 → 0.62)

ACTION:
1. Log failure mode
2. Alert: "Light scout assumptions may be outdated"
3. Recommend: "Consult decision matrix before next light scout"
4. Trigger: Manual review by Jamie
```

---

## X. FRIDAY'S LEARNING ETHICS

**What Friday WILL learn:**
- ✅ Patterns from successful outcomes
- ✅ Why certain workflows work better than others
- ✅ Optimal timing and intensity for cycles
- ✅ How to predict governance approval latency

**What Friday WILL NOT learn:**
- ❌ How to bypass Governance Gate
- ❌ How to hide decisions from audit trail
- ❌ How to optimize for speed over correctness
- ❌ How to override Jamie's authority

**Enforcement:** Governance Gate validates every decision Friday makes. If a decision violates a rule, it's blocked and logged.

---

## XI. IMPLEMENTATION CHECKLIST

To activate Friday's learning framework:

- [ ] Create `friday_decision_journal.jsonl` (immutable log)
- [ ] Create `friday_pattern_library.json` (patterns + confidence)
- [ ] Create `friday_market_sentiment.json` (signal tracking)
- [ ] Implement `friday_learn_from_aar()` function (pattern extraction)
- [ ] Implement `friday_decision_matrix()` function (choose workflow)
- [ ] Implement `friday_generate_learning_report()` function (daily summary)
- [ ] Wire Friday to TTLG Phase 6 AARs (input: learnings)
- [ ] Wire Claude Code to Friday's decision matrix (input: which workflow to build)
- [ ] Create governance validation for all Friday decisions (no silent approvals)
- [ ] Set up daily learning report generation (email to Jamie)

---

## XII. NEXT STEPS

Once activated, Friday's learning loop becomes:

```
Day 1: Run initial TTLG scans → Generate AARs
Day 2: Friday ingests patterns → Updates decision matrix
Day 3: Friday makes decisions using learned patterns
Day 4: Claude Code builds based on Friday's choices
Day 5: Outcomes feed back → Friday learns
Day 6: Learning report generated → Jamie reviews
Week 2: Confidence in patterns increases → Decisions improve
Month 1: Friday becomes predictive (not just reactive)
```

---

**Status:** 🟢 FRAMEWORK READY  
**Requires:** Decision journal implementation + pattern extraction  
**Timeline:** Activate after first TTLG scan completes  
**Authority:** Jamie approves pattern ratification quarterly
