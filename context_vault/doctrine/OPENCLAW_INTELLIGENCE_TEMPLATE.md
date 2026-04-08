<!-- EPOS GOVERNANCE WATERMARK -->
# OPENCLAW PRE-INTEGRATION INTELLIGENCE TEMPLATE
## File: C:\Users\Jamie\workspace\epos_mcp\context_vault\doctrine\OPENCLAW_INTELLIGENCE_TEMPLATE.md
## Constitutional Authority: EPOS Constitution v3.1, Article X (Vendor Integration)

---

## Purpose

Before writing a single line of integration code, OpenClaw analyzes the target
landscape and delivers a structured intelligence brief. This replaces assumption-based
development with evidence-based architecture.

**The Principle:** We do not integrate blindly. We send intelligence ahead of execution.

---

## THE OPENCLAW RECON PROTOCOL

### Phase 1: DEFINE THE OBJECTIVE

Complete this block before activating OpenClaw.

```yaml
# ============================================================
# RECON REQUEST — Fill before every new integration
# ============================================================
recon_id: "RECON-XXX-YYYY"
date: "YYYY-MM-DD"
requested_by: "Growth Steward"

# What are we trying to accomplish?
objective: |
  [One sentence. What capability do we gain when this integration is complete?]

# What does success look like?
success_criteria:
  - "[Measurable outcome 1]"
  - "[Measurable outcome 2]"
  - "[Measurable outcome 3]"

# What EPOS nodes does this serve?
serving_nodes:
  - "[Node name — e.g., Content Lab, Sales Brain, Market Awareness]"

# What is the integration target?
target:
  name: "[Service/Platform/API name]"
  type: "[SaaS API | Self-hosted | Hardware | Protocol | Marketplace]"
  documentation_urls:
    - "[Primary docs URL]"
    - "[API reference URL]"
    - "[Pricing page URL]"

# Budget and constraints
constraints:
  max_monthly_cost: "$XX"
  data_sovereignty: "[Must self-host | Cloud acceptable | Hybrid]"
  latency_requirement: "[Real-time | Near-real-time | Batch acceptable]"
  constitutional_boundaries:
    - "Article X: Must be replaceable without losing core functionality"
    - "Article VII: No inline data > 8K tokens"
    - "[Additional constraints]"
```

---

### Phase 2: OPENCLAW RESEARCH DIRECTIVES

Feed these queries to OpenClaw sequentially. Each builds on the previous.

#### Directive 1: LANDSCAPE SCAN
```
Analyze [TARGET] as a potential integration for an autonomous business 
operating system. Report:

1. Architecture: How does their system work internally? What protocols,
   APIs, and data formats does it use?
2. Integration surface: What are ALL available connection points?
   (REST API, webhooks, SDKs, MCP servers, CLI tools, database access)
3. Rate limits and quotas: What are the hard ceilings per tier?
4. Data residency: Where is data stored? Can it be self-hosted?
5. Vendor lock-in risk: What happens if we need to migrate away?
   How portable is our data?
6. Competitive alternatives: Name 3 alternatives with the same 
   capability. How do they compare on sovereignty and cost?
```

#### Directive 2: COST MODELING
```
Based on the landscape scan of [TARGET], model the cost curve for
our usage profile:

- [Describe expected usage volume — e.g., 50+ content pieces/day,
  500 API calls/hour, 10GB data/month]
- Compare: their free tier, starter, pro, and enterprise pricing
  against our projected 30/60/90 day usage
- Calculate: cost per unit of value (cost per content piece published,
  cost per lead processed, cost per GB stored)
- Flag: any pricing cliffs where costs jump disproportionately
- Recommend: optimal tier for months 1, 3, 6, and 12
```

#### Directive 3: INTEGRATION ARCHITECTURE
```
Design the optimal integration between [TARGET] and our stack:
- EPOS runs: PostgreSQL + NocoDB + n8n + Ollama + Agent Zero
- All services communicate via Docker network
- n8n handles workflow automation with webhook triggers
- NocoDB provides the data interface
- Context Vault stores institutional knowledge

Propose:
1. Connection method (API polling vs webhooks vs direct DB vs MCP)
2. Data flow diagram (what goes where, in what format)
3. Authentication strategy (API keys, OAuth, JWT)
4. Error handling (what happens when [TARGET] is down?)
5. n8n workflow sketch (trigger → process → store → notify)
6. Constitutional compliance check against EPOS Article X
```

#### Directive 4: FAILURE PRE-MORTEM
```
For the proposed [TARGET] integration, enumerate:

1. Five ways it breaks at runtime
   (auth expires, rate limit hit, schema change, downtime, data corruption)
2. For each failure: what does the user see? What does the system log?
3. Graceful degradation plan: how does EPOS continue operating
   without this integration?
4. Migration plan: if we must replace [TARGET] in 48 hours,
   what is the extraction and replacement sequence?
5. Constitutional violations this integration could introduce
   if not properly governed
```

#### Directive 5: OPTIMUM PATH RECOMMENDATION
```
Given all research above, recommend:

1. GO / NO-GO decision with reasoning
2. If GO: exact implementation sequence (numbered steps)
3. Estimated implementation time (hours, not days)
4. First milestone: what is the smallest testable integration
   we can deploy in under 1 hour?
5. Full integration: what does the complete wiring look like?
6. What should we monitor post-integration to verify health?
```

---

### Phase 3: INTELLIGENCE BRIEF OUTPUT

OpenClaw delivers a structured brief stored in the Context Vault:

```
context_vault/
  recon/
    RECON-001-HETZNER.md
    RECON-002-WORDPRESS.md
    RECON-003-ELEVENLABS.md
    RECON-004-STRIPE.md
    ...
```

Each brief follows this structure:

```markdown
# RECON BRIEF: [TARGET NAME]
## Recon ID: RECON-XXX
## Date: YYYY-MM-DD
## Status: [GO | NO-GO | CONDITIONAL]

### Executive Summary
[3 sentences max. Decision + rationale + key risk.]

### Landscape
[Architecture, APIs, integration points]

### Cost Model
[Projected costs at 30/60/90/365 days]

### Recommended Architecture
[Data flow, n8n workflow, connection method]

### Failure Modes
[Top 5 failure scenarios with mitigations]

### Implementation Sequence
[Numbered steps, estimated hours per step]

### Constitutional Compliance
[Article X check, sovereignty assessment, migration plan]

### First Milestone
[The smallest deployable test — under 1 hour]
```

---

### Phase 4: GOVERNANCE GATE

Before any code is written:

1. Recon brief reviewed by Growth Steward (you)
2. GO/NO-GO decision recorded in NocoDB missions table
3. If GO: mission JSON created referencing the recon brief
4. Agent Zero executes against the researched architecture
5. Post-integration: n8n monitors the health metrics identified in the brief

---

## THE INTROSPECTION PROTOCOL — OpenClaw as Architectural Mirror

The Recon Protocol looks outward. The Introspection Protocol looks inward.

OpenClaw has full read access to the Context Vault, the EPOS Constitution,
every architectural document, every node definition, and the PostgreSQL
schema. This makes it uniquely positioned to evaluate EPOS against the
frontier of what's possible.

### Introspection Mission Types

#### INTRO-A: Architecture Audit
```
You have read access to the complete EPOS architecture via the 
Context Vault and the PostgreSQL epos_core schema.

Scan the following:
- context_vault/doctrine/ (constitutional documents, templates)
- context_vault/recon/ (completed intelligence briefs)
- PostgreSQL epos_core schema (7 tables, triggers, indexes)
- docker-compose.yml (service topology)
- ENVIRONMENT_SPEC.md, COMPONENT_INTERACTION_MATRIX.md
- FAILURE_SCENARIOS.md, PATH_CLARITY_RULES.md

Produce an Architecture Health Report:
1. Component coupling analysis — which services are too tightly bound?
2. Single points of failure — what breaks the whole stack?
3. Scaling bottlenecks — what fails first under 10x load?
4. Constitutional drift — are any components violating their articles?
5. Data flow inefficiencies — are there unnecessary hops or duplication?
6. Security surface — what is exposed that shouldn't be?

Score each area 1-10. Flag anything below 7.
Write report to: context_vault/recon/INTRO-A-ARCHITECTURE-AUDIT.md
```

#### INTRO-B: Research Frontier Scan
```
Search for the most recent research papers, blog posts, and reference 
architectures published in the last 90 days on these topics:

1. Multi-agent orchestration architectures (Agent Zero, CrewAI, 
   AutoGen, LangGraph, OpenAI Swarm patterns)
2. Agentic memory systems (hippocampal architectures, FAISS 
   alternatives, persistent context strategies, MemGPT patterns)
3. Self-healing software architectures (chaos engineering for AI 
   systems, autonomous remediation, constitutional AI governance)
4. MCP server design patterns (emerging best practices, security 
   models, performance optimization)
5. Event-driven agentic systems (event bus patterns for AI, 
   pub/sub at agent scale, reactive agent architectures)
6. Solopreneur-scale autonomous business systems (one-person 
   company automation, AI-native business operations)

For each topic:
- Identify the 3 most relevant papers or implementations
- Extract the core architectural insight
- Map it to a specific EPOS component that could benefit
- Propose a concrete improvement with estimated effort

Write report to: context_vault/recon/INTRO-B-FRONTIER-SCAN-[DATE].md
```

#### INTRO-C: Evolution Recommendation
```
Based on the Architecture Audit (INTRO-A) and the Frontier Scan 
(INTRO-B), produce an Evolution Recommendation:

1. IMMEDIATE (this week): Fixes or improvements that require 
   < 2 hours each and address critical gaps
2. SHORT-TERM (this month): Architectural upgrades that align 
   EPOS with proven patterns from the research frontier
3. STRATEGIC (next quarter): Fundamental capability additions 
   that would create competitive moat or unlock new revenue

For each recommendation:
- Reference the specific research that supports it
- Map to affected EPOS nodes and constitutional articles
- Estimate implementation effort (hours)
- Project impact on: throughput, reliability, intelligence, revenue
- Identify risks if NOT implemented (technical debt accumulation)

Rank all recommendations by: (impact × urgency) / effort

Write report to: context_vault/recon/INTRO-C-EVOLUTION-[DATE].md
```

#### INTRO-D: Competitive Architecture Comparison
```
Identify 5 comparable systems to EPOS in the market:
- Other solopreneur operating systems
- AI-native business automation platforms
- Multi-agent orchestration frameworks being used commercially
- Personal AI assistant architectures (OpenClaw itself, etc.)

For each:
- What is their architecture?
- What do they do better than EPOS currently?
- What does EPOS do better than them?
- What can we adopt without violating sovereignty principles?

Produce a competitive architecture matrix and write to:
context_vault/recon/INTRO-D-COMPETITIVE-[DATE].md
```

### Introspection Schedule

| Cycle | Mission | Frequency | Trigger |
|-------|---------|-----------|---------|
| Weekly | INTRO-B: Frontier Scan | Every Monday | Cron via n8n |
| Bi-weekly | INTRO-A: Architecture Audit | Every 2 weeks | Post-sprint |
| Monthly | INTRO-C: Evolution Recommendation | Monthly | After Audit + Scan |
| Quarterly | INTRO-D: Competitive Comparison | Every 90 days | Strategic planning |

### Automation via n8n

```
n8n Cron Trigger (Monday 06:00 EST)
    → HTTP Request to OpenClaw /hooks/agent
    → Message: "Execute INTRO-B Frontier Scan per Introspection Protocol"
    → OpenClaw researches, writes brief to Context Vault
    → n8n file watcher detects new brief in /recon/
    → NocoDB: Create mission record with brief reference
    → Steward Alert: "New frontier scan ready for review"
```

The organism doesn't just grow — it studies how organisms grow,
then applies the best patterns to itself.

---

## ACTIVE RECON QUEUE

| Recon ID | Target | Objective | Status |
|----------|--------|-----------|--------|
| RECON-001 | Hetzner Cloud | Optimize server provisioning for EPOS stack | QUEUED |
| RECON-002 | WordPress REST API | Content pipeline publishing endpoint | QUEUED |
| RECON-003 | ElevenLabs | Voice agent deployment for 4 channel profiles | PENDING |
| RECON-004 | Stripe | Payment processing for Sovereignty Suite | PENDING |
| RECON-005 | HeyGen | Video avatar production pipeline | PENDING |
| RECON-006 | Playwright | Browser automation for BrowserUse missions | PENDING |
| INTRO-A | EPOS Architecture | Internal health audit and coupling analysis | QUEUED |
| INTRO-B | Research Frontier | Latest multi-agent and agentic memory research | QUEUED |

---

## WHY THIS MATTERS

Traditional development: Guess → Code → Debug → Patch → Repeat

EPOS with OpenClaw: Research → Model → Design → Validate → Execute Once

The recon protocol transforms OpenClaw from a search tool into a 
strategic intelligence agency. Every integration arrives pre-analyzed,
cost-modeled, failure-projected, and constitutionally cleared.

This is the difference between building a business and engineering 
an organism that builds itself.

---

**Constitutional Note:** This template is itself subject to evolution.
After every 5 recon briefs, the Evolution Steward reviews the template
for pattern improvements and appends learnings to this document.
```