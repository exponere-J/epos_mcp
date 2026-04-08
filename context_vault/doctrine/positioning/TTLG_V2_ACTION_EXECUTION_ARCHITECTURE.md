# TTLG v2: FROM DIAGNOSTIC TO AUTOMATED ACTION
## Architecture for "Do the Work, Not the Reading"

**Created:** 2026-04-04 (Morning Sprint)  
**Objective:** Evolve TTLG from report delivery → insight extraction → automated execution → outcome measurement  
**Execution Window:** Morning sprint (6–8 hours) to ship v2 before night launch  

---

## THE CORE INSIGHT

**The market doesn't want reports. The market wants outcomes.**

Current TTLG flow:
```
Diagnostic Scan → Report Generation → Client Reads & Processes → Client Acts → Outcome
```

This adds friction at "Client Reads & Processes" — if the insight requires interpretation, you lose value.

**TTLG v2 flow:**
```
Diagnostic Scan → Insight Extraction → Automated Action Execution → Outcome Measurement → Client Sees Results
```

**The shift:** The system doesn't hand the client a "here's what you need to do" report. The system **does what needs to be done**, shows the results, and offers the client two choices:
1. **"Keep it"** (continue this automated action, pay for ongoing)
2. **"Modify it"** (change variables, depth, frequency, channels)

---

## PART ONE: THE ACTION GATEWAY ARCHITECTURE

### Current State (TTLG v1)

```
DIAGNOSTIC ENGINE (Scout → Thinker → Gate → Surgeon → Analyst)
    ↓
REPORT TEMPLATE (Executive Summary, Findings, Recommendations)
    ↓
CLIENT EMAIL (Report sits in inbox, needs interpretation)
    ↓
??? (Client somehow acts on recommendations)
    ↓
OUTCOME (Hopefully)
```

**Problem:** The "???" step requires human interpretation. This is where 70% of diagnostics fail.

### Desired State (TTLG v2)

```
DIAGNOSTIC ENGINE (Scout → Thinker → Gate → Surgeon → Analyst)
    ↓
INSIGHT EXTRACTION (Parse report → Extract actionable findings)
    ↓
ACTION ROUTER (Map findings to executable operations)
    ↓
ACTION EXECUTOR (Run operations automatically)
    ↓
OUTCOME MEASUREMENT (Track results, feed back to Context Vault)
    ↓
CLIENT DASHBOARD (See results, approve continuation, modify)
    ↓
SALES COMPONENT (Present upgrade offer: "Want us to do more of this?")
```

---

## PART TWO: MISSING INTEGRATIONS & ACTION EXECUTORS

### What TTLG v1 Has

- ✅ Diagnostic framework (Scout → Analyst pipeline)
- ✅ Report generation (templates exist)
- ✅ PGP Orlando proving ground
- ✅ 90-day roadmap template
- ❌ **Insight extraction layer** (parse report → structured findings)
- ❌ **Action routing logic** (map findings → executable operations)
- ❌ **Action executors** (the systems that actually DO the work)
- ❌ **Outcome measurement** (track before/after)
- ❌ **Sales conversion component** (upsell automation)

### What We Need to Build This Morning

| Component | Purpose | Status | Build Time | Blocker? |
|---|---|---|---|---|
| **Insight Extractor** | Parse diagnostic report → JSON of actionable findings | 0% | 90 min | YES |
| **Action Router** | Map findings to EPOS nodes that execute them | 0% | 120 min | YES |
| **Action Executor Bridge** | Interface to Content Lab, FOTW, Event Bus | 0% | 45 min | YES |
| **Outcome Tracker** | Record before/after metrics, feed to dashboard | 20% | 60 min | YES |
| **Sales Component** | Auto-detect results, propose upsell | 10% | 45 min | MODERATE |
| **Client Dashboard** | Show results, approval buttons, modify interface | 0% | 90 min | NO (can ship MVP) |

**Critical path (longest dependencies first):**

1. **Insight Extractor** (90 min) — blocks everything downstream
2. **Action Router** (120 min) — waits on Extractor
3. **Action Executor Bridge** (45 min) — waits on Router
4. **Outcome Tracker** (60 min) — parallel with Bridge
5. **Sales Component** (45 min) — parallel
6. **Dashboard** (90 min) — parallel (can ship without full backend)

**Realistic morning completion:** Steps 1–4 complete by 13:00 (7 hours), steps 5–6 by 14:30 (8.5 hours)

---

## PART THREE: THE INSIGHT EXTRACTOR (BLOCKER #1)

### What It Does

Takes the diagnostic report (text blob) and extracts structured findings:

```json
{
  "client_id": "pgp_orlando_001",
  "diagnostic_run": "2026-04-04T08:00:00Z",
  "insights": [
    {
      "finding_id": "f_001",
      "category": "marketing",
      "severity": "high",
      "insight": "Email conversion rate is 1.2%, benchmark is 3.5%",
      "root_cause": "Subject lines lack urgency triggers",
      "executable_action": "ab_test_subject_lines",
      "action_type": "content_lab_task",
      "required_node": "email_strategist",
      "estimated_impact": {
        "metric": "email_ctr",
        "current": 1.2,
        "projected": 3.2,
        "confidence": 0.78,
        "timeframe_days": 14
      },
      "resource_allocation": {
        "hours": 4,
        "cost": 250,
        "frequency": "one_time"
      }
    },
    {
      "finding_id": "f_002",
      "category": "sales",
      "severity": "medium",
      "insight": "Sales calls lack structured discovery process",
      "root_cause": "No qualification script",
      "executable_action": "create_discovery_playbook",
      "action_type": "ttlg_service",
      "required_node": "ttlg_sales_track",
      "estimated_impact": {
        "metric": "deal_close_rate",
        "current": 0.35,
        "projected": 0.50,
        "confidence": 0.65,
        "timeframe_days": 30
      }
    }
  ],
  "recommended_actions": [
    "f_001",
    "f_002",
    "f_003"
  ],
  "total_estimated_hours": 12,
  "total_estimated_cost": 1200,
  "expected_roi": 3.2
}
```

### Build Template (90 minutes)

**Step 1: Prompt Engineering (15 min)**

Create a Claude prompt that extracts insights from raw diagnostic text:

```
You are the Insight Extraction Engine for TTLG diagnostics.

Input: A diagnostic report (text blob)

Output: A JSON with the structure below. Be precise:
- Each finding must have an executable action
- Severity must be high/medium/low
- Estimated impact must include confidence score
- Required node must match EPOS node registry

Rules:
- Only extract findings that are actionable
- Ignore observations that don't change behavior
- Include only findings where action is >$100 ROI
```

**Step 2: Context Extraction (15 min)**

Parse the diagnostic report to extract:
- Client industry/size
- Current metrics (baseline)
- Key blockers (top 3)
- Available budget
- Timeline constraints

**Step 3: Action Mapping (30 min)**

For each finding, map to an executor:
- `action_type: "content_lab_task"` → Route to Content Lab node
- `action_type: "sales_automation"` → Route to FOTW node
- `action_type: "ttlg_service"` → Route to TTLG sales track
- `action_type: "governance"` → Route to Governance Gate

**Step 4: Integration (30 min)**

Wire Insight Extractor to:
- Input: Diagnostic report (text/markdown)
- Output: JSON to Event Bus (event: `diagnostic.insights_extracted`)
- Logging: Context Vault (for learning + AAR)

### Code Scaffolding (Minimal)

```python
# File: /engine/ttlg_insight_extractor.py

import json
from datetime import datetime
from anthropic import Anthropic

class TTLGInsightExtractor:
    def __init__(self, client_id: str, diagnostic_report: str):
        self.client_id = client_id
        self.report = diagnostic_report
        self.client = Anthropic()
    
    def extract_insights(self) -> dict:
        """Parse diagnostic report → structured insights"""
        prompt = self._build_extraction_prompt()
        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        insights_json = self._parse_response(response.content[0].text)
        return self._publish_to_event_bus(insights_json)
    
    def _build_extraction_prompt(self) -> str:
        return f"""
Extract actionable insights from this diagnostic report.

Report:
{self.report}

Output JSON with this schema:
{{
  "client_id": "{self.client_id}",
  "insights": [
    {{
      "finding_id": "f_001",
      "category": "marketing|sales|service|governance",
      "severity": "high|medium|low",
      "insight": "...",
      "executable_action": "...",
      "action_type": "content_lab_task|sales_automation|ttlg_service|governance",
      "required_node": "...",
      "estimated_impact": {{"metric": "...", "current": X, "projected": Y, "confidence": 0.XX}},
      "resource_allocation": {{"hours": X, "cost": Y}}
    }}
  ],
  "recommended_actions": ["f_001", "f_002"],
  "total_estimated_hours": X,
  "total_estimated_cost": Y,
  "expected_roi": X.X
}}

Rules:
1. Only actionable findings (can execute within 30 days)
2. ROI > $100 minimum
3. Confidence score based on benchmark research
4. Be specific about execution steps
"""
    
    def _parse_response(self, response_text: str) -> dict:
        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        return json.loads(json_str)
    
    def _publish_to_event_bus(self, insights: dict) -> dict:
        # Write to Context Vault / Event Bus
        event = {
            "event_type": "diagnostic.insights_extracted",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": self.client_id,
            "payload": insights
        }
        # Log to Event Bus (JSONL)
        # TODO: Wire to contextvault/events/systemevents.jsonl
        return insights
```

---

## PART FOUR: ACTION ROUTER (BLOCKER #2)

### What It Does

Takes extracted insights and routes each to the right executor:

```
Finding: "Email subject lines lack urgency"
  ↓ Action Router
  ↓
Routing Decision: "This is a Content Lab task → Email Strategist node"
  ↓
Route to: Content Lab (MA1 → AN1 → A1) with task payload
  ↓
Dispatch: "Create 10 subject line variants, test framework"
```

### Build Template (120 minutes)

**Step 1: Node Registry (30 min)**

Map every executable action to a node:

```python
ACTION_NODE_REGISTRY = {
    "ab_test_subject_lines": {
        "node": "content_lab_email_strategist",
        "input_schema": {
            "current_subject": "str",
            "target_metric": "ctr|open_rate",
            "variants_count": "int"
        },
        "output_event": "content.email_variants_generated"
    },
    "create_discovery_playbook": {
        "node": "ttlg_sales_track",
        "input_schema": {
            "industry": "str",
            "deal_size": "int",
            "sales_cycle_days": "int"
        },
        "output_event": "sales.discovery_script_created"
    },
    "audit_governance_gates": {
        "node": "governance_gate",
        "input_schema": {
            "systems": ["list"],
            "risk_tolerance": "low|medium|high"
        },
        "output_event": "governance.audit_complete"
    },
    # ... add 20+ more mappings
}
```

**Step 2: Route Decision Logic (45 min)**

Create routing logic:

```python
class ActionRouter:
    def __init__(self, insights: dict):
        self.insights = insights
        self.routes = []
    
    def route_all_insights(self):
        """For each insight, determine executor + dispatch"""
        for insight in self.insights["insights"]:
            route = self._determine_route(insight)
            self.routes.append(route)
            self._dispatch_to_executor(route)
        return self.routes
    
    def _determine_route(self, insight: dict) -> dict:
        """Map insight → executor node"""
        action_type = insight["executable_action"]
        
        if action_type not in ACTION_NODE_REGISTRY:
            return {
                "status": "no_route",
                "finding_id": insight["finding_id"],
                "reason": f"Unknown action type: {action_type}"
            }
        
        registry_entry = ACTION_NODE_REGISTRY[action_type]
        
        return {
            "status": "routed",
            "finding_id": insight["finding_id"],
            "target_node": registry_entry["node"],
            "input_payload": self._build_payload(insight, registry_entry),
            "output_event": registry_entry["output_event"],
            "estimated_hours": insight["resource_allocation"]["hours"],
            "estimated_cost": insight["resource_allocation"]["cost"]
        }
    
    def _build_payload(self, insight: dict, registry: dict) -> dict:
        """Extract required fields for executor"""
        payload = {
            "finding_id": insight["finding_id"],
            "insight": insight["insight"],
            "action": insight["executable_action"]
        }
        # Populate schema-required fields
        for field in registry["input_schema"]:
            # Extract from insight context
            payload[field] = insight.get(field, None)
        return payload
    
    def _dispatch_to_executor(self, route: dict):
        """Send routed action to executor"""
        if route["status"] != "routed":
            return
        
        event = {
            "event_type": "action.dispatched",
            "target_node": route["target_node"],
            "payload": route["input_payload"],
            "output_event": route["output_event"]
        }
        # Publish to Event Bus
        # TODO: Wire to Event Bus
```

**Step 3: Execution Dispatch (45 min)**

Wire router to emit events that trigger executors:

```python
def dispatch_to_event_bus(route: dict):
    """Emit event that Content Lab / FOTW / TTLG node will subscribe to"""
    event = {
        "event_type": f"{route['target_node']}.execute_task",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": f"{route['finding_id']}_exec_{datetime.utcnow().timestamp()}",
        "payload": route["input_payload"],
        "result_event": route["output_event"],
        "client_id": route.get("client_id")
    }
    # Write to Event Bus (systemevents.jsonl)
    # Each executor node listens for its event type
```

---

## PART FIVE: ACTION EXECUTOR BRIDGE (BLOCKER #3)

### What It Does

Connects the routed actions to actual EPOS nodes:

- **Content Lab**: Execute brief generation, A/B test design, asset production
- **FOTW**: Real-time monitoring of outcomes (email opens, sales calls, etc.)
- **TTLG Sales Track**: Generate sales scripts, discovery playbooks
- **Governance Gate**: Run compliance audits

### Minimal Integration (45 minutes)

For **morning launch**, we don't build full executors. We build **hooks** that:

1. Listen for dispatched events
2. Log intent to Context Vault
3. Queue for human confirmation (or auto-execute if low-risk)
4. Track execution status

```python
class ActionExecutorBridge:
    def __init__(self):
        self.subscribers = {}
        self.context_vault = ContextVault()
    
    def register_executor(self, event_type: str, handler_fn):
        """Register node executor for an event type"""
        self.subscribers[event_type] = handler_fn
    
    def execute_action(self, route: dict):
        """Execute routed action or queue for approval"""
        event_type = f"{route['target_node']}.execute_task"
        
        # Check if low-risk auto-execute
        if self._is_low_risk(route):
            return self._auto_execute(route)
        
        # Otherwise queue for human approval
        return self._queue_for_approval(route)
    
    def _is_low_risk(self, route: dict) -> bool:
        """Can we auto-execute this?"""
        # Rules: auto-execute if cost < $500 AND hours < 8
        cost = route["input_payload"].get("estimated_cost", 0)
        hours = route["input_payload"].get("estimated_hours", 0)
        return cost < 500 and hours < 8
    
    def _auto_execute(self, route: dict):
        """Call the executor directly"""
        handler = self.subscribers.get(route["target_node"])
        if not handler:
            return {"status": "no_handler", "target_node": route["target_node"]}
        
        try:
            result = handler(route["input_payload"])
            # Log to Context Vault
            self.context_vault.log_action_execution(route, result, "success")
            return {"status": "executed", "result": result}
        except Exception as e:
            self.context_vault.log_action_execution(route, str(e), "failed")
            return {"status": "error", "error": str(e)}
    
    def _queue_for_approval(self, route: dict):
        """Queue for client/human review"""
        approval_task = {
            "task_id": route["finding_id"],
            "action": route["input_payload"]["action"],
            "estimated_cost": route["input_payload"].get("estimated_cost"),
            "estimated_hours": route["input_payload"].get("estimated_hours"),
            "estimated_roi": route.get("estimated_roi"),
            "approve_url": f"/approve/{route['finding_id']}",
            "reject_url": f"/reject/{route['finding_id']}"
        }
        # Store in Context Vault + send approval request
        self.context_vault.log_approval_queue(approval_task)
        return {"status": "awaiting_approval", "task_id": approval_task["task_id"]}
```

---

## PART SIX: OUTCOME MEASUREMENT (BLOCKER #4)

### What It Does

Tracks results before → after and feeds loop back to client + sales component.

```
Action Executed (e.g., "Create 10 email subject variants")
  ↓
Outcome Measurement: Track metric (email open rate)
  ↓
Baseline (was 1.2%) vs. New (now 3.2%?)
  ↓
Feed back to client: "Your email opens improved 165%"
  ↓
Sales component: "Want us to do this for SMS next?"
```

### Build Template (60 minutes)

**Step 1: Metric Definition (15 min)**

For each insight, define what to measure:

```python
OUTCOME_METRICS = {
    "ab_test_subject_lines": {
        "metric_name": "email_open_rate",
        "data_source": "email_provider_api|google_analytics|custom",
        "baseline_field": "current_open_rate",
        "measurement_window_days": 14,
        "success_threshold": 0.20  # 20% improvement = success
    },
    "create_discovery_playbook": {
        "metric_name": "deal_close_rate",
        "data_source": "crm_api",
        "baseline_field": "current_close_rate",
        "measurement_window_days": 30,
        "success_threshold": 0.15
    }
}
```

**Step 2: Measurement Integration (30 min)**

Connect to data sources (CRM, email provider, Google Analytics):

```python
class OutcomeMeasurement:
    def __init__(self, action_id: str, metric_config: dict):
        self.action_id = action_id
        self.config = metric_config
        self.baseline = None
        self.current = None
    
    def measure_outcome(self) -> dict:
        """Fetch current metric value"""
        data_source = self.config["data_source"]
        
        if data_source == "email_provider_api":
            self.current = self._fetch_from_email_api()
        elif data_source == "crm_api":
            self.current = self._fetch_from_crm()
        elif data_source == "google_analytics":
            self.current = self._fetch_from_ga()
        
        improvement = (self.current - self.baseline) / self.baseline
        success = improvement >= self.config["success_threshold"]
        
        return {
            "action_id": self.action_id,
            "metric": self.config["metric_name"],
            "baseline": self.baseline,
            "current": self.current,
            "improvement_pct": improvement,
            "success": success,
            "measured_at": datetime.utcnow().isoformat()
        }
```

**Step 3: Context Vault Logging (15 min)**

Log all outcomes for learning:

```python
def log_outcome_to_context_vault(action_id: str, outcome: dict):
    """Store outcome for AAR + pattern learning"""
    entry = {
        "event_type": "action.outcome_measured",
        "action_id": action_id,
        "outcome": outcome,
        "timestamp": datetime.utcnow().isoformat()
    }
    # Write to contextvault/outcomes/{client_id}/{action_id}.jsonl
```

---

## PART SEVEN: SALES COMPONENT (BLOCKER #5)

### What It Does

Automatically detects successful actions and proposes upsells.

**Logic:**
```
Action outcome: "Email opens improved 165%"
  ↓
Sales component detects: "Metric exceeded success threshold"
  ↓
Auto-generates offer: "Want us to apply this to SMS? (similar pattern, new channel)"
  ↓
Present to client: "Next optimization: SMS open rate audit ($497, 20% projected ROI)"
```

### Minimal Implementation (45 minutes)

```python
class AutoUpsellEngine:
    def __init__(self, client_context: dict):
        self.client = client_context
        self.successful_actions = []
        self.upsell_offers = []
    
    def detect_successful_outcomes(self, outcomes: list):
        """Filter for outcomes that exceeded threshold"""
        for outcome in outcomes:
            if outcome["success"]:
                self.successful_actions.append(outcome)
    
    def generate_upsells(self):
        """For each success, propose adjacent opportunity"""
        upsell_map = {
            "ab_test_subject_lines": [
                "Apply same logic to SMS headlines",
                "Test email send time optimization",
                "Audit email copy for scarcity triggers"
            ],
            "create_discovery_playbook": [
                "Build objection-handling framework",
                "Create proposal template",
                "Design post-call follow-up sequence"
            ]
        }
        
        for action in self.successful_actions:
            action_type = action["action_type"]
            if action_type in upsell_map:
                for upsell_opportunity in upsell_map[action_type]:
                    offer = {
                        "trigger_action": action,
                        "upsell_opportunity": upsell_opportunity,
                        "estimated_cost": self._estimate_cost(upsell_opportunity),
                        "projected_roi": self._estimate_roi(action, upsell_opportunity)
                    }
                    self.upsell_offers.append(offer)
        
        return self.upsell_offers
    
    def _estimate_cost(self, opportunity: str) -> float:
        # Lookup base cost for opportunity type
        return 497  # Placeholder
    
    def _estimate_roi(self, parent_action: dict, opportunity: str) -> float:
        # If parent improved metric by 165%, similar action should achieve 60-80% of that
        parent_improvement = parent_action["improvement_pct"]
        return parent_improvement * 0.65
```

---

## PART EIGHT: EXECUTION CHECKLIST (Morning Sprint)

### 08:00–08:45 (45 min) — Setup

- [ ] Create branch: `ttlg-v2-action-execution`
- [ ] Set up file structure:
  - `/engine/ttlg_insight_extractor.py`
  - `/engine/ttlg_action_router.py`
  - `/engine/ttlg_action_executor.py`
  - `/engine/ttlg_outcome_measurement.py`
  - `/engine/ttlg_sales_component.py`
- [ ] Create test fixtures (sample diagnostic report)

### 08:45–10:15 (90 min) — Insight Extractor

- [ ] Build extraction prompt (15 min)
- [ ] Code Insight Extractor class (30 min)
- [ ] Wire to Event Bus (15 min)
- [ ] Test with PGP Orlando report (30 min)

### 10:15–12:15 (120 min) — Action Router

- [ ] Build ACTION_NODE_REGISTRY (20 min)
- [ ] Code ActionRouter class (40 min)
- [ ] Create route decision logic (30 min)
- [ ] Wire to Event Bus + test (30 min)

### 12:15–13:00 (45 min) — Action Executor Bridge

- [ ] Create executor registration system (20 min)
- [ ] Build auto-execute vs. approval logic (15 min)
- [ ] Wire to Content Lab hook (10 min)

### 13:00–14:00 (60 min) — Outcome Measurement

- [ ] Define OUTCOME_METRICS registry (15 min)
- [ ] Build measurement class (30 min)
- [ ] Wire to Context Vault (15 min)

### 14:00–14:45 (45 min) — Sales Component

- [ ] Build AutoUpsellEngine (30 min)
- [ ] Create upsell mapping logic (15 min)

### 14:45–15:00 (15 min) — Documentation + Testing

- [ ] Create README.md for v2 architecture
- [ ] Run end-to-end flow test (PGP Orlando diagnostic → insights → routes → outcomes)

### 15:00–15:30 (30 min) — MVP Dashboard

- [ ] Build client-facing dashboard mockup (Cloudflare Pages)
  - Show extracted insights
  - Approval buttons for queued actions
  - Results from executed actions
  - Upsell recommendations

---

## PART NINE: REMAINING BLOCKERS & SOLUTIONS

| Blocker | Status | Solution | Owner | Time |
|---|---|---|---|---|
| **Insight Extractor** (extract report → JSON) | CRITICAL | Claude Opus API for parsing | Claude Code | 90 min |
| **Action Router** (map findings → nodes) | CRITICAL | Build NODE_REGISTRY + decision logic | Claude Code | 120 min |
| **Action Executor Bridge** (connect to nodes) | CRITICAL | Event-driven dispatch to Content Lab/FOTW | Claude Code | 45 min |
| **Outcome Measurement** (track before/after) | CRITICAL | API integrations to CRM/email providers | Claude Code + manual for initial | 60 min |
| **Email provider API access** | BLOCKER | Do we have Gmail API key ready? | Jamie | 5 min |
| **CRM API access** (for outcome tracking) | BLOCKER | Airtable API key for PGP Orlando data | Jamie | 5 min |
| **Sales Component** | MODERATE | AutoUpsellEngine (can ship MVP) | Claude Code | 45 min |
| **Client Dashboard** | LOW | Can ship static mockup first, iterate | Claude Code | 90 min (deferred to week 2) |

**Critical dependencies:**
- Email/CRM API keys must be in `.env` BEFORE outcome measurement can work
- ACTION_NODE_REGISTRY must be locked before routing can route
- Insight Extractor must output clean JSON before router can parse it

---

## PART TEN: THE INTEGRATED FLOW (Sequence Diagram)

```
CLIENT → TTLG DIAGNOSTIC (Scan)
  ↓
[Diagnostic Complete: "Issues found in Marketing, Sales, Governance"]
  ↓
INSIGHT EXTRACTOR
  (Parse report → 5 structured insights)
  ↓
ACTION ROUTER
  Finding 1: "Email subject lines" → Content Lab Email Strategist
  Finding 2: "Sales discovery missing" → TTLG Sales Track
  Finding 3: "No governance gates" → Governance Gate
  ↓
ACTION EXECUTOR BRIDGE
  Finding 1 (low-risk): AUTO-EXECUTE
    → Content Lab generates 10 subject variants
  Finding 2 (medium-risk): QUEUE FOR APPROVAL
    → Client approves TTLG sales engagement
  Finding 3 (high-risk): QUEUE FOR APPROVAL
    → Client approves governance audit
  ↓
OUTCOME MEASUREMENT (14-30 days)
  Finding 1 result: "Email open rate: 1.2% → 3.2% (165% improvement)"
  Finding 2 result: "Sales close rate: 35% → 48% (35% improvement)"
  Finding 3 result: "Governance compliance: 60% → 100%"
  ↓
AUTO-UPSELL ENGINE
  Detection: "Finding 1 succeeded, similar pattern exists in SMS"
  Offer: "Apply email optimization to SMS? (Cost: $497, Projected ROI: 65%)"
  ↓
CLIENT DASHBOARD
  Show: Results + next opportunities
  Action: Client approves SMS optimization OR modifies scope
  ↓
CONVERSION
  Client approves upsell → New engagement created → Recurring revenue
```

---

## THE SHIFT IN VALUE DELIVERY

**TTLG v1 (Report-based):**
- Diagnostic report delivered → Client must interpret → Client must execute → Result unknown
- Success dependent on client capability
- No feedback loop to TTLG

**TTLG v2 (Action-based):**
- Diagnostic delivered → Insights auto-extracted → Actions auto-routed → Some auto-execute → Results tracked → Upsells auto-generated
- Success dependent on TTLG/EPOS node capability (we control)
- Tight feedback loop: action → outcome → next action
- Client only approves or modifies, doesn't interpret

**The market insight:** If you show a client "we already did the work, here are the results, want us to continue?" you've moved from consulting (advisory) to automation (utility). Utility scales.

---

## FINAL SPRINT PUSH

This morning:
1. Build Insight Extractor (90 min)
2. Build Action Router (120 min)
3. Build Executor Bridge (45 min)
4. Build Outcome Measurement (60 min)
5. Build Sales Component (45 min)
6. Quick MVP dashboard mockup (30 min)

**By 15:00:** TTLG v2 core is shipped. Evening launch can promote it as **"Diagnostic → Automated Action → Results"** instead of **"Diagnostic → Report."**

**The positioning shift:** From "We'll tell you what to do" to "We'll do it and show you the results."