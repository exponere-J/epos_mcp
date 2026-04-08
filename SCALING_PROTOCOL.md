# SCALING PROTOCOL
**Autonomous Growth Authorization & Resource Request Framework**

**Authority:** EPOS_CONSTITUTION_v3.1.md Article VI (Resource Governance), PLATFORM_STRATEGIST_NODES.md

---

## Preamble

The **Scaling Protocol** defines **when and how** the EPOS system can autonomously request additional resources (new Content Lab nodes, additional agents, expanded monitoring) without human intervention.

This is the bridge between **proven operational excellence** and **authorized growth**.

The core principle: **Scale only what is constitutionally sound.**

---

## PART 1: SCALING TRIGGERS

The system may request new resources **only when** specific conditions are met. These conditions are **checkable by Friday** in an automated workflow.

### Trigger Type 1: High-Confidence Pattern Maturity

**Condition:** A pattern in `friday_pattern_library.json` has been successfully applied 10+ times in the last 30 days with >95% success rate.

```
Metric:
  pattern.successful_applications >= 10 (in last 30 days)
  pattern.success_rate >= 0.95
  pattern.articles_enforced includes ["II", "III", "VII", "XIV"]

Example:
  Pattern: "Context Vault Directory Pre-Creation"
  Applications: 12 (in last 30 days)
  Success Rate: 11/12 = 0.92

  Evaluation: Does NOT trigger scaling (92% < 95% threshold)

  If Success Rate: 11/11 (100%), then TRIGGERS scaling
  → Friday may request a new Content Lab node for governance analysis

Action When Triggered:
  Friday publishes to scaling_requests.jsonl:
  {
    "request_id": "scale_req_20260311_001",
    "trigger_type": "pattern_maturity",
    "pattern_id": "EPOS_PATH_ENSURE_20260311",
    "pattern_success_rate": 0.98,
    "pattern_application_count": 12,
    "resource_requested": "ContentLab_Node",
    "proposed_domain": "governance_enforcement",
    "confidence": 0.96
  }
```

### Trigger Type 2: Bottleneck Detection (Scout Saturation)

**Condition:** Scout phase completes >50% slower than historical baseline, suggesting it needs parallelization or a second Scout instance.

```
Metric:
  scout_phase_duration > baseline_duration * 1.5 (for 5+ consecutive runs)

Calculation:
  Historical baseline (last 30 Scout runs): avg 900 seconds (15 min)
  Last 5 runs: avg 1450 seconds (24 min)
  Threshold: 900 * 1.5 = 1350 seconds
  Actual: 1450 > 1350 → TRIGGERS scaling

Action When Triggered:
  Friday publishes to scaling_requests.jsonl:
  {
    "request_id": "scale_req_20260311_002",
    "trigger_type": "scout_saturation",
    "metric_name": "scout_phase_duration",
    "historical_baseline_seconds": 900,
    "current_average_seconds": 1450,
    "threshold_exceeded_runs": 5,
    "resource_requested": "Scout_Instance",
    "proposed_domain": "market_intelligence",
    "confidence": 0.88
  }

Precedent:
  - If historical bottleneck was Scout, propose second Scout instance
  - If bottleneck was FOTW, propose FOTW capture expansion
  - If bottleneck was Content Lab, propose new Content Lab node
```

### Trigger Type 3: Escalation Frequency Spike (Governance Risk)

**Condition:** Friday detects >5 novel/high-risk escalations in 24 hours (escalations that don't match known patterns).

```
Metric:
  escalations_in_24h >= 5
  AND escalations_unknown_pattern_count >= 3

Definition of "Novel Escalation":
  Escalation message_type == "ESCALATION"
  AND escalation does not match any pattern in friday_pattern_library.json
  AND escalation.severity in ["warning", "error", "critical"]

Example Timeline:
  2026-03-11 06:00 - Escalation A: Model routing failure (KNOWN pattern)
  2026-03-11 09:30 - Escalation B: Path resolution error (KNOWN pattern)
  2026-03-11 11:00 - Escalation C: State corruption (NOVEL pattern #1)
  2026-03-11 14:15 - Escalation D: Timeout during FOTW capture (NOVEL pattern #2)
  2026-03-11 16:45 - Escalation E: Gemini rate limit (NOVEL pattern #3)

  Count: 5 escalations, 3 novel → TRIGGERS scaling

Action When Triggered:
  Friday publishes to scaling_requests.jsonl:
  {
    "request_id": "scale_req_20260311_003",
    "trigger_type": "escalation_frequency_spike",
    "escalations_in_24h": 5,
    "novel_escalations": [
      {"escalation_id": "esc_c", "description": "State corruption"},
      {"escalation_id": "esc_d", "description": "Timeout during FOTW capture"},
      {"escalation_id": "esc_e", "description": "Gemini rate limit"}
    ],
    "resource_requested": "ContentLab_Node",
    "proposed_domain": "escalation_analysis",
    "urgency": "high",
    "confidence": 0.75,
    "recommendation": "New Content Lab node to analyze novel escalation patterns"
  }
```

### Trigger Type 4: Commercial Signal (Revenue-Linked)

**Condition:** EPOS diagnostic cycle produces findings with >8/10 business impact score, indicating the diagnostic is commercially valuable and should be scaled.

```
Metric:
  business_impact_score >= 8 (out of 10)
  Score calculated as:
    - Finding criticality (critical findings worth more)
    - Organizational drag (findings that reduce operational friction)
    - Revenue protection (findings that prevent loss or enable growth)

Example Calculation:
  Scout findings on EPOS_ROOT:
    - 1 critical governance violation → 3 points
    - 3 high-risk dependencies → 2 points
    - 5 medium efficiency losses → 1.5 points
  Total: 6.5/10 → Does NOT trigger

  Scout findings on external revenue system:
    - 1 critical revenue leak → 4 points
    - 2 high-risk customer friction points → 3 points
    - 3 medium operational drag → 1 point
  Total: 8/10 → TRIGGERS scaling

Action When Triggered:
  Friday publishes to scaling_requests.jsonl:
  {
    "request_id": "scale_req_20260311_004",
    "trigger_type": "commercial_signal",
    "business_impact_score": 8.5,
    "scan_target": "external_revenue_system",
    "findings_with_revenue_impact": 5,
    "resource_requested": "ContentLab_Node",
    "proposed_domain": "revenue_protection",
    "confidence": 0.92,
    "recommendation": "Scale diagnostic capability to this domain for revenue protection product"
  }
```

---

## PART 2: RESOURCE REQUEST WORKFLOW

When a scaling trigger fires, the system follows this workflow:

### Step 1: Request Generation (Friday)

Friday creates a scaling request and publishes to `friday_orchestrator/logs/scaling_requests.jsonl`:

```json
{
  "request_id": "scale_req_20260311_005",
  "timestamp": "2026-03-11T17:30:00Z",
  "trigger_type": "pattern_maturity",
  "pattern_id": "EPOS_GOVERNANCE_ANALYSIS",
  "resource_requested": "ContentLab_Node",
  "node_configuration": {
    "node_id": "governance_impact_analyzer_v2",
    "domain": "governance_enforcement",
    "input_schema": "scout_output.json + ambient_log.jsonl",
    "output_schema": "markdown_research_asset",
    "model_alias": "contentlab_governance_v1",
    "estimated_throughput": "50 scans/day"
  },
  "justification": {
    "metric_name": "pattern_maturity",
    "metric_value": 0.98,
    "threshold": 0.95,
    "business_case": "Governance analysis pattern has 98% success rate. New node will serve as primary analyzer for all regulatory compliance scans."
  },
  "confidence": 0.96,
  "approval_required": true,
  "approval_authority": "Jamie (Founder)",
  "request_status": "pending_approval"
}
```

### Step 2: Request Validation (Governance Gate)

The Governance Gate (or Friday) validates the request:

```
CHECK 1: Is the trigger legitimate?
  Pattern: EPOS_GOVERNANCE_ANALYSIS
  Success Rate: 0.98 ✅
  Applications: 15 ✅
  Articles Enforced: II, III, VII, XIV ✅

CHECK 2: Is the resource request well-scoped?
  New node domain: governance_enforcement (specific) ✅
  Input/output schema: clearly defined ✅
  Estimated throughput: reasonable ✅

CHECK 3: Are constitutional articles obeyed?
  Article VI (Resource Governance): New resource must prove operational readiness ✅
  Article III (Governance Gate): Node must pass gate audits ✅
  Article VIII (Unified Nervous System): Node must use standard event protocol ✅

VALIDATION: PASSED
Ready for human approval
```

### Step 3: Approval (Jamie/Human Authority)

Jamie reviews the request and approves or rejects:

```
REQUEST: governance_impact_analyzer_v2
DOMAIN: governance_enforcement
SUCCESS RATE: 98%
APPLICATIONS: 15 in last 30 days
CONFIDENCE: 0.96

DECISION OPTIONS:
  [1] APPROVE - Create the new Content Lab node immediately
  [2] CONDITIONAL APPROVE - Approve with additional monitoring requirements
  [3] DEFER - Schedule for next quarter (resource constraints)
  [4] REJECT - Do not scale this domain (strategic decision)

APPROVED (with conditions):
  - Node must pass Governance Gate audit on first 10 runs
  - Business impact scoring must be tracked for ROI analysis
  - Node can be scaled to 100% throughput after 30-day validation
  - If success rate drops below 0.90, revert to manual review

Approval recorded:
{
  "request_id": "scale_req_20260311_005",
  "approval_decision": "conditional_approve",
  "approved_by": "Jamie",
  "approval_timestamp": "2026-03-11T18:00:00Z",
  "conditions": [
    "First 10 runs must pass governance gate",
    "Track business impact for ROI analysis",
    "Revert if success rate < 0.90"
  ]
}
```

### Step 4: Resource Deployment

Once approved, the system provisions the new resource:

```bash
# Create new Content Lab node
mkdir -p context_vault/contentlab_nodes/governance_impact_analyzer_v2
cat > context_vault/contentlab_nodes/governance_impact_analyzer_v2/charter.md << 'EOF'
# Node: governance_impact_analyzer_v2

Domain: governance_enforcement
Model Alias: contentlab_governance_v1
Input Schema: scout_output.json + ambient_log.jsonl
Output: markdown_research_asset

Deployment Date: 2026-03-11
Approval: Jamie (conditional approval)
Success Threshold: 0.90
EOF

# Update .env with new node configuration
echo "CONTENTLAB_GOVERNANCE_V2_MODEL_ALIAS=contentlab_governance_v1" >> .env

# Update friday_orchestrator to include new node
echo "New node deployed: governance_impact_analyzer_v2" >> friday_orchestrator/logs/deployment.jsonl
```

### Step 5: Monitoring & Validation

Friday monitors the new resource for the first 30 days:

```json
{
  "node_id": "governance_impact_analyzer_v2",
  "deployment_date": "2026-03-11",
  "runs_completed": 10,
  "success_rate": 0.95,
  "avg_synthesis_quality": 0.92,
  "business_impact_score": 8.2,
  "status": "performing_well",
  "next_review": "2026-04-11"
}
```

If success rate drops below 0.90, Friday automatically:
1. Logs a degradation signal
2. Reverts the node to manual approval mode
3. Publishes an escalation for Jamie to review

---

## PART 3: SCALING CONSTRAINTS

The system **cannot** autonomously scale without obeying these constraints:

### Constraint 1: Constitutional Compliance

Every new resource (agent, node, tool) must:
- ✅ Start with an IPP submission
- ✅ Include explicit failure scenarios
- ✅ Be validated by the Governance Gate
- ✅ Obey all EPOS articles (II-XIV)

**No exceptions.** A resource that cannot pass the governance gate cannot be deployed.

### Constraint 2: Operational Readiness

Every new resource must:
- ✅ Have a clear input schema (what it consumes)
- ✅ Have a clear output schema (what it produces)
- ✅ Define success metrics (how we know it works)
- ✅ Include automatic rollback triggers (when to shut it down)

### Constraint 3: Resource Limits

Scaling is bounded by:

```
Maximum Content Lab Nodes: 12 (per EPOS_CONSTITUTION_v3.1.md)
Maximum Agent Instances: 4 per agent type (Scout, FOTW, Friday, Architect)
Maximum Daily Diagnostic Cycles: 1000 (infrastructure limit)
Maximum Scan Artifacts: 100,000 (storage limit, then archive)
```

If scaling would exceed these limits, Friday escalates to Jamie for approval of infrastructure expansion.

### Constraint 4: Financial Impact

Scaling is gated by cost:

```
Cost per new Content Lab node: ~$2,000/month (model API + infrastructure)
Cost per new Scout instance: ~$5,000/month
Cost per new FOTW aggregator: ~$1,500/month

If monthly scaling cost exceeds budget, Friday escalates to financial approval.
```

---

## PART 4: AUTONOMOUS ESCALATION MATRIX

When a scaling request cannot be automatically approved, Friday escalates to Jamie using this matrix:

| Trigger Type | Confidence | Approval Path | SLA |
|---|---|---|---|
| Pattern Maturity (>95% success) | >0.95 | Auto-approve if Articles II-XIV compliant | <1 hour |
| Bottleneck Detection | 0.80-0.95 | Jamie review + conditional approval | <4 hours |
| Escalation Frequency Spike | 0.70-0.80 | Jamie review + risk assessment | <8 hours |
| Commercial Signal | >0.90 | Jamie review (revenue decision) | <24 hours |
| Infrastructure Expansion (exceeds limits) | N/A | Jamie + CTO review | <1 week |
| Budget Approval (exceeds monthly cost) | N/A | Jamie + Finance review | <1 week |

---

## PART 5: ANTI-SCALING GUARDRAILS

The system is **designed to resist** reckless scaling:

### Guardrail 1: Success Rate Floor

A resource can only be scaled if it maintains >90% success rate. If success rate drops below 90%, the system:

1. Logs a degradation signal
2. Reverts to manual approval mode
3. Publishes escalation to Jamie

### Guardrail 2: Pattern Maturity Requirement

A new pattern cannot be auto-deployed until it has been:
- Successfully applied 10+ times
- >95% success rate
- >30 days of proven operation

**No fast-tracks.** Even high-confidence new discoveries must prove themselves over time.

### Guardrail 3: Human Approval for Novel Domains

New Content Lab nodes for **novel domains** (never before analyzed) require explicit Jamie approval, even if trigger thresholds are met.

Example:
- Domain: "governance_enforcement" (proven) → can auto-approve if metrics hit
- Domain: "customer_emotion_analysis" (novel) → requires Jamie approval

### Guardrail 4: Rollback Authorization

If a new resource (node, agent, tool) causes:
- >1 Article XIV violation in first 30 days
- >20% degradation in existing system performance
- Revenue impact >$10K (negative)

Friday **automatically reverts** the resource and publishes an escalation.

---

## PART 6: AUDIT & TRANSPARENCY

Every scaling decision is logged and auditable:

```json
[
  {
    "event_type": "scaling_trigger_fired",
    "trigger_type": "pattern_maturity",
    "timestamp": "2026-03-11T17:30:00Z",
    "pattern_id": "EPOS_GOVERNANCE_ANALYSIS",
    "confidence": 0.98
  },
  {
    "event_type": "scaling_request_created",
    "request_id": "scale_req_20260311_005",
    "resource_type": "ContentLab_Node",
    "timestamp": "2026-03-11T17:31:00Z"
  },
  {
    "event_type": "scaling_request_approved",
    "request_id": "scale_req_20260311_005",
    "approved_by": "Jamie",
    "approval_type": "conditional_approve",
    "timestamp": "2026-03-11T18:00:00Z"
  },
  {
    "event_type": "resource_deployed",
    "node_id": "governance_impact_analyzer_v2",
    "deployment_timestamp": "2026-03-11T18:15:00Z"
  },
  {
    "event_type": "resource_validation_check",
    "node_id": "governance_impact_analyzer_v2",
    "runs_completed": 10,
    "success_rate": 0.95,
    "status": "performing_well",
    "timestamp": "2026-03-12T00:00:00Z"
  }
]
```

This log lives in `friday_orchestrator/logs/scaling_audit.jsonl` and is **immutable**.

---

## PART 7: EXAMPLE: SCALING IN ACTION

**Day 0 (March 11):**
- Friday detects "Context Vault Directory Pre-Creation" pattern has been successfully used 15 times with 98% success rate
- Publishes scaling request: governance_impact_analyzer_v2

**Day 0 (Same day, 1 hour later):**
- Governance Gate validates request: ✅ PASSED
- Request forwarded to Jamie for approval

**Day 0 (Same day, 4 hours later):**
- Jamie reviews request and approves with conditions
- Conditions: Node must pass gate on first 10 runs, success rate must stay >90%

**Day 1 (March 12):**
- governance_impact_analyzer_v2 is deployed and begins processing scans
- Runs 1-10: Success rate 95% ✅

**Day 5 (March 15):**
- Node has completed 50 runs with 94% success rate
- Business impact score: 8.2/10 (revenue-linked)
- Friday publishes validation report

**Day 30 (April 10):**
- governance_impact_analyzer_v2 has processed 1,500+ scans
- Success rate stable at 92%
- Node approved for full production deployment

---

## References

- **EPOS_CONSTITUTION_v3.1.md** — Article VI (Resource Governance)
- **PLATFORM_STRATEGIST_NODES.md** — Content Lab node definitions
- **FRIDAY_LEARNING_FRAMEWORK.md** — Pattern library maturity tracking
- **GOVERNANCE_GATE_CHARTER.md** — What makes a resource deployable

---

**Last Updated:** 2026-03-11
**Constitutional Authority:** Article VI, EPOS Constitution v3.1
**Next Evolution:** Market-linked scaling based on revenue impact metrics
