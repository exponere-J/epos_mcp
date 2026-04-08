<!-- EPOS GOVERNANCE WATERMARK -->
# EPOS CONSUMER JOURNEY MAP v3.0
## The Autonomous Front Office — Complete Operational Blueprint
### Unified: Journey × Communication × Production × Intelligence × Governance

> "We are initializing the Autonomous Front Office. Digital communication is the circulatory system of EPOS. The only human bottleneck is reserved for 9th-Order Stewardship." — Growth Steward Directive

**Supersedes:** Journey Map v1, Journey Revisions, Gap Analysis, Procurement Plan
**Authority:** EPOS Constitution v3.1 + Completion Prospectus v2.0
**Storage:** `context_vault/doctrine/EPOS_CONSUMER_JOURNEY_MAP_v3.md`

---

# I. PLANNING DOCUMENTATION CHECKLIST

- [x] Core Identity: 9th-Order Growth Steward initialized
- [x] Foundry Setup: Content Lab (Radar, Architect, Producer, Marshall, Analyst) deployed
- [x] Campaign Launch: "Own the Farm" (Sovereignty) Batch 0 drafted
- [x] Gap Mapping: Intelligence, Presence, and Lead Buffer gaps identified and closed
- [x] Agent Registry: Machine-readable `agent_registry.json` created
- [x] Service Model: 4-Tier BPO (Conventional to Full AI System) defined
- [x] Diagnostic Ethos: TTLG (Through The Looking Glass) visualization formalized
- [x] Data Sovereignty: Airtable + Local Vault Sync protocol established
- [x] Communication Layers: Voice (ElevenLabs), Video (HeyGen), Meeting Intelligence (Whisper), GRAG engine
- [x] Video Production: Visual Mask system + 18+ derivative cascade pipeline
- [x] FOTW Integration: Three-phase intelligence (Passive → GRAG → Role Modeling) architecture
- [x] Upgrade Pipeline: 6-stage evolutionary loop (Detection → Recursive Learning) installed
- [x] Sovereign Procurement: Service stack mapped as pluggable utilities
- [x] Mission Control: 4-quadrant steward dashboard approved
- [x] Pre-Flight: Go/No-Go checklist finalized

---

# II. THE DUAL-AUDIT PROTOCOL

Before moving a prospect through the portal, measure their current "Information State."

## Auditing Conventional Businesses (Friction & Leakage)
- **The Shadow Audit**: RCH2 Audience Mapper + TTLG Diagnostic scan their digital presence, response times, and content quality
- **The Role Identification**: Identify "bottleneck roles" where humans perform repetitive tasks (manual follow-up, invoice generation)
- **The Visualization**: Map current state as a "Spaghetti Diagram" vs EPOS Node Blueprint

## Auditing Automation & AI Systems (Governance & Connectivity)
- **The Brittleness Test**: Check if existing "Zaps" break under slight data variations
- **Governance Audit**: EPOS Doctor scans AI outputs for Hallucination Risk and Brand Drift
- **The SaaS Cage Audit**: Measure data "sharecropping" on 3rd-party platforms vs sovereign Vault ownership

---

# III. THE 10-LAYER ACTION MATRIX

Applied at EVERY touchpoint. Each layer maps to specific roles, process nodes, and I.I.D.E.A.T.E. stages.

| Layer | Function | Primary Roles | Process Node | Communication Layer |
|-------|----------|---------------|--------------|-------------------|
| 1. Identity | Resolve who this is from email + domain + context | PS-EM, R1, VAULT | Lead Intake & Scoring | Email capture, form data |
| 2. Intent | Classify psychological state: Discovery / Education / Decision | TTLG, MA1 | TTLG Pre-Classifier | Behavioral signals, click patterns |
| 3. Data Capture | Normalize into Vault fields and tags | VAULT, META, BUS | Vault Adapter | All channels feed Vault |
| 4. Classification | Map to niche, revenue layer, node bundle | TTLG, S1, Research | Node Mapping Engine | TTLG diagnostic + Mirror Report |
| 5. Scoring | Assign Resonance Score (0-100) and Steward Threshold | AN1, MA1, BI | Echolocation Engine | Score drives channel escalation |
| 6. Routing | Choose next touchpoint, sequence, and communication channel | META, BUS, PS-EM | Journey Router | Email → Voice → Video → Meeting |
| 7. Delivery | Compose and send governed asset via appropriate channel | A1, V1, PS-EM, M1, HeyGen, ElevenLabs | Email/Content/Voice/Video Asset Engine | Multi-channel: text, avatar video, voice call |
| 8. Feedback | Log opens, clicks, reply semantics, call outcomes, video engagement | PS-EM, AN1, VAULT, Whisper | Feedback Collector | All channels report to Vault |
| 9. Learning | Update weights, templates, scripts, niche packs | AN1, MA1, Feature Proposer, EVL1 | BI / Tweak Node | I.I.D.E.A.T.E. Tweaking stage |
| 10. Steward Signal | Decide whether to escalate to Growth Steward | Growth Steward, TTLG, BI | Steward Gate | Voice Note Queue for score > 85 |

---

# IV. THE 31+ TOUCHPOINT JOURNEY MAP

## Phase 1: Awareness (TP_01–TP_05)

### TP_01 — Email Capture

**Spec:** `TP_01_EMAIL_CAPTURE` via web form → initializes "The Portal Entry" sequence

**10-Layer Matrix:**
1. **Identity:** Email, IP, inferred company/role, device
2. **Intent:** Opt-in source (lead magnet vs homepage), time of day, UTM campaign
3. **Data Capture:** Email, IP, Source_Campaign, form variant, consent flags
4. **Classification:** Domain check (business vs free), Agency vs SaaS vs Local Service, size estimate
5. **Scoring:** +10 valid business domain, +X high-intent pages (pricing/diagnostic), decay if no action
6. **Routing:** Auto-add to "Portal Entry" email journey; send to LI_SC_LEAD_SCORER, LI_ROUTER
7. **Delivery:** Instant confirmation email + asset (PDF, diagnostic invite teaser). **NEW: HeyGen personalized video intro if enterprise domain detected.**
8. **Feedback:** Open/click tracking, device fingerprint, bounce handling
9. **Learning:** Update campaign performance in Vault, adjust source weighting and copy testing
10. **Steward Signal:** None — fully automated unless anomaly (VIP domain, massive list)

**Friction:** Manual lead review, bad data clogging nurture, no consistent classification
**Gap Fix (FP1 Fresh Presence):** Direct link to Content Lab prevents "stale profile" syndrome in first 48 hours

**Productized Solutions:**

| Node | Tier 1 (Conventional) | Tier 2 (Hybrid) | Tier 3 (AI-First) | Tier 4 (Fully Agentic) |
|------|----------------------|-----------------|-------------------|----------------------|
| Lead Intake | VA cleans weekly, basic CRM tags | VA + Airtable rules engine | LI_SC agent enriches and scores real-time | Autonomous intake bus → Vault → journey_map |
| Data Hygiene | Manual suppression lists | Automated bounce/unsub, monthly cleanup | Always-on quality filter (spam, role-based) | Self-tuning filters from campaign feedback |
| Classification | Spreadsheet columns by hand | Rules-based ("if domain contains agency") | Agent domain intel scan + vertical prediction | Classification → diagnostic → pricing wired |

**Event Bus:** `lead.captured`, `lead.scored`, `lead.routed`

---

### TP_02–TP_04 — Portal Entry Email Sequence

**Spec:** Automated 3-email nurture over 72 hours post-capture

**Communication Channels:**
- Email 1 (immediate): Welcome + lead magnet delivery
- Email 2 (24h): Value-add content from Content Lab (Echolocation-selected, highest-performing piece for their niche)
- Email 3 (72h): Diagnostic teaser + "Enter the Looking Glass" CTA
- **NEW: SMS/WhatsApp nudge (48h)** via CONV1 Conversation Strategist for Score 31-70 leads

**Event Bus:** `nurture.email.sent`, `nurture.email.opened`, `nurture.sms.delivered`

---

## Phase 2: Discovery (TP_05–TP_12)

### TP_05 — Diagnostic Invite

**Spec:** `TP_05_DIAGNOSTIC_INVITE` → "Mirror Report" + TTLG diagnostic invite (24h after TP_01)

**10-Layer Matrix:**
1. **Identity:** Enriched profile (role, company size, tech stack signals)
2. **Intent:** Prior email engagement? Click history on audit-related content
3. **Data Capture:** Clicks on "Enter the Looking Glass" button, preference tags (Operational vs Creative pain)
4. **Classification:** Conventional biz vs already-automated; map to Shadow Audit vs Governance Audit flow
5. **Scoring:** +X per click on audit/TTLG content, +Y for repeated diagnostic page visits
6. **Routing:** TTLG_DIAGNOSTIC_NODE + EDU1 send Mirror Report and invite
7. **Delivery:** Personalized Mirror Report: Spaghetti Diagram vs EPOS Node Blueprint. **NEW: HeyGen avatar walkthrough video embedded in email showing their specific bottleneck map.**
8. **Feedback:** Track which sections expanded (Sales, Ops, Finance), time on report
9. **Learning:** Context Server stores interest fingerprint ("Finance Node curiosity high")
10. **Steward Signal:** Optional micro-signal if deep governance/sovereignty interest (Ascension candidate)

**Friction:** Manual tech stack interpretation, generic Mirror Report, gold leads stalling after diagnostic
**Gap Fix (EDU1 Educational Architect):** Niche-specific scripts (Agency, SaaS, Local Service) PRE-LOADED in Context Vault so Mirror Reports are never generic

**Productized Solutions:**

| Node | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|------|--------|--------|--------|--------|
| TTLG Diagnostic | Human consultant builds audit deck from form | Human + template engine (Canva/Notion) | diagnosticserver.run_diagnostic creates 3-option menu | Diagnostic + pricing + engagement auto-fire; always-on Doctor |
| Mirror Report | Static PDF | Light personalization (industry, logo) | Dynamic: pulls site speed, content cadence, reply times, SaaS brittleness | Interactive report with embedded simulations; updates from event log |
| Bottleneck Locator | Manual notes on time leaks | Spreadsheet matrix (tasks × time) | Agent simulates 7-day workflow from data | Continuous telemetry writing back into Vault |

**Event Bus:** `diagnostic.invited`, `diagnostic.started`, `diagnostic.mirror_report.sent`

---

### TP_06–TP_11 — Discovery Nurture + Voice Activation

**NEW Communication Layers in Discovery:**
- **TP_07 (Score 40+):** ElevenLabs voice agent calls with Lead Qualifier profile. 60-second qualification. Books diagnostic if interested.
- **TP_09 (Score 60+):** HeyGen personalized video: "Here's what I noticed about your [niche] operations" — avatar references Mirror Report findings
- **TP_11 (Score 75+):** Whisper-transcribed discovery call invitation via Zoom. GRAG engine active during call providing live suggestions.

**Between-Session Intelligence:** After each voice/video touchpoint, EPOS auto-generates: follow-up action items, briefing materials for next interaction, updated journey position.

**Event Bus:** `voice.call.completed`, `video.personalized.sent`, `discovery.call.scheduled`, `grag.suggestion.delivered`

---

## Phase 3: Consideration (TP_12–TP_20)

### TP_12 — Offer Visualization

**Spec:** `TP_12_OFFER_VISUALIZATION` → 4-Tier BPO recommendation. Steward signal if score > 85.

**10-Layer Matrix:**
1. **Identity:** High-fidelity profile (revenue band, headcount, tool stack, main bottleneck)
2. **Intent:** Completed diagnostic; engaged with Mirror Report and solution content
3. **Data Capture:** Selected nodes (Sales Ops, Finance Ops, Content Lab), risk tolerance, timeline
4. **Classification:** Mapped to 4-Tier BPO model per function
5. **Scoring:** +50 if Tier 4 viewed, weight for multiple nodes, governance interest; threshold 85 for Steward alert
6. **Routing:** Score > 85 → Growth Steward with voice note script + context. Else → next nurture path.
7. **Delivery:** Interactive visualization (PDF + Loom-style walkthrough) of before vs after EPOS. **NEW: HeyGen avatar presents the 4-tier breakdown personalized to their diagnostic results.**
8. **Feedback:** Time on offer page, tier toggles, clicks on "See financial breakdown"
9. **Learning:** Diagnostic + pricing events feed calculator and cross-sell engine
10. **Steward Signal:** High-resonance leads appear in "Voice Note Queue" with angle + tier recommendation

**Friction:** Manual proposal construction, inconsistent tier presentation, no follow-up path on silence
**Gap Fix (PS-EM + 0-100 Scoring):** Hard-coded scoring logic in email router prevents low-intent noise from reaching voice-note queue

**Productized Solutions:**

| Node | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|------|--------|--------|--------|--------|
| Pricing Calculator | Human spreadsheet | Template sheet with guardrails | contextserver.calculate_pricing enforces constitutional rules | Diagnostic → pricing → proposal auto-composed as contracts |
| Offer Visualization | Designer one-off decks | Deck template ops fills manually | ARCHITECT auto-builds 4-tier visualization from manifests | Composable interface: client toggles nodes/tiers, system recalculates live |
| Steward Voice Note | You riff every time | Checklist script reference | FIN_OPS_01 + ARCHITECT auto-generate script from diagnostic + pricing events | System tunes scripts from closed/won outcomes, optimizing per persona |

**Event Bus:** `offer.visualization.sent`, `offer.tier.selected`, `pricing.calculated`, `steward.alert.triggered`

---

### TP_13–TP_19 — Consideration Nurture + Closing Sequence

**NEW Communication Layers in Consideration:**
- **TP_14 (Score 70+):** ElevenLabs Diagnostic Guide voice call. Walks through TTLG findings. GRAG active.
- **TP_16 (Score 80+):** HeyGen "Your EPOS Blueprint" video: personalized 3-minute walkthrough of their recommended node constellation
- **TP_18 (Score 85+):** **Steward Voice Note**: Growth Steward (Jamie) records personal 90-second voice note using auto-generated script with diagnostic context, pricing angle, and persona framing
- **TP_19 (Score 85+, no response):** Value-Add Pivot via LI-QA Autoresponder: "We noticed you're looking at the Finance Node; here's a case study"

**Event Bus:** `consideration.voice.completed`, `consideration.video.sent`, `steward.voicenote.sent`, `nurture.pivot.triggered`

---

## Phase 4: Commitment (TP_20–TP_26)

### TP_20 — Contract & Onboarding Initiation

**Spec:** Prospect converts to client. Engagement Manifest Generator fires.

**10-Layer Matrix:**
1. **Identity:** Confirmed client. Full profile locked in Vault.
2. **Intent:** Committed. Now needs frictionless onboarding.
3. **Data Capture:** Contract terms, selected tier, node configuration, billing info
4. **Classification:** Tier 1-4 assignment determines onboarding depth and automation level
5. **Scoring:** Engagement Health Score initialized at 100. Decay model begins.
6. **Routing:** Onboarding Orchestrator: forms → tasks → agents. Tier-appropriate sequence fires.
7. **Delivery:** Welcome package. **NEW: HeyGen Onboarding Welcome video** (avatar, warm greeting, first-week roadmap). **ElevenLabs Onboarding Assistant** call scheduled.
8. **Feedback:** Form completion rate, first-login time, support ticket volume
9. **Learning:** Onboarding friction points logged to Vault for process improvement
10. **Steward Signal:** If onboarding stalls > 48hr, alert Growth Steward with context

**Friction:** Contract back-and-forth, questionnaire bottleneck, account setup dependent on founder
**Gap Fix:** Engagement Manifest Generator + Onboarding Orchestrator fully autonomous for Tier 1-3

**NEW — FOTW Activation for Tier 3-4:**
- Phase 1 (Passive Intelligence) begins immediately at TP_20 for Tier 3-4 clients
- Browser tab scraping, call transcription, chat ingestion begins building client-specific knowledge base
- All data stays on client hardware (data sovereignty)

**Event Bus:** `client.onboarded`, `engagement.manifest.generated`, `fotw.phase1.activated`

---

### TP_21–TP_25 — Onboarding Execution

- **TP_21:** Node deployment and configuration (autonomous for Tier 1-3, guided for Tier 4)
- **TP_22:** First-week check-in. ElevenLabs Support Agent call or HeyGen video update.
- **TP_23:** FOTW initial intelligence report (Tier 3-4): "Here's what we've learned about your operations in week 1"
- **TP_24:** First Echolocation results delivered (if Content Lab deployed)
- **TP_25:** GRAG activation for Tier 3-4 clients (Phase 2 begins)

**Event Bus:** `node.deployed`, `checkin.completed`, `fotw.report.generated`, `grag.activated`

---

## Phase 5: Stewardship & Expansion (TP_26+)

### TP_26+ — Ongoing Stewardship

**Spec:** Systematic quarterly business review, upsell, and expansion. Not memory-dependent.

**10-Layer Matrix (Ongoing):**
1. **Identity:** Client profile continuously enriched from FOTW observations
2. **Intent:** Usage patterns, support tickets, expansion signals
3. **Data Capture:** Node telemetry, engagement health scores, NPS
4. **Classification:** Risk tier (healthy / at-risk / expansion-ready)
5. **Scoring:** Engagement Health Score: usage frequency, ticket volume, feature adoption, NPS
6. **Routing:** Healthy → Cross-sell engine. At-risk → Retention sequence. Expansion → Steward alert.
7. **Delivery:** Quarterly Business Review (auto-generated). **NEW: HeyGen quarterly video summary.** FOTW Phase 3 role models for operational optimization.
8. **Feedback:** QBR engagement, expansion interest signals, referral likelihood
9. **Learning:** Client lifecycle patterns feed into niche intelligence packs for future prospects
10. **Steward Signal:** Expansion-ready clients surface with recommended upsell path

**Productized Expansion Paths:**
- Individual node add-ons (L1: $49-149/mo)
- Bundle upgrades (L2: $149-597/mo)
- Department packages (L3: $997-1,497/mo)
- FOTW Intelligence Suite (L4: $297-997/mo)
- Governed Autonomy upgrade (L5: $2,997+/mo)
- White-Label licensing (L6: $997+/mo per their client)

**Event Bus:** `engagement.health.updated`, `crosssell.recommended`, `qbr.generated`, `fotw.role_model.generated`

---

# V. ROLE-TO-PROCESS-TO-SYSTEM NODE STACK

## Role Atoms → Process Nodes

| Process Node | Primary Roles | 9th-Order Steward Cognition | Executor Precision |
|-------------|---------------|---------------------------|-------------------|
| Lead Intake & Scoring | PS-EM, R1, AN1, S1 | Sees "lead" as flywheel weight shift, not a contact | Classifies by L1-L8 revenue layer + psychological state |
| Diagnostic & Mirror (TTLG) | TTLG, MA1, FOTW, Context Server | Simulates 10-step consequence chains: do nothing vs adopt | Maps pain → node capabilities → 3-tier engagement menu |
| Offer & Pricing | A1, FIN_OPS_01, Context Server | Ensures offers advance the Evolutionary Arc, not one-off deals | Enforces constitutional pricing (1.3x floor, 20-30% bundle discount) |
| Content Lab | R1, A1, P1, V1, M1, AN1 | Tunes Echolocation by segment and flywheel layer | Turns sparks into governed, platform-native cascades |
| Communication Hub | Voice Agent, HeyGen, Whisper, GRAG | Voice = trust, video = authority. Allocates modality by readiness | Executes scripts, transcribes, suggests constitutionally |
| FOTW Intelligence | Capture, GRAG, Role Modeler, Transmuter | Institutional memory is the ultimate moat | Captures without disrupting, models without assuming |
| Governance & Health | DOC, GATE, VAULT, BUS, META | Watches for drift, not bugs | Blocks violations, emits receipts, logs to Vault |

## Process Nodes → System Nodes

| System Node | Composed Of | Client Value | Revenue Range |
|------------|-------------|-------------|---------------|
| TTLG Diagnostic System | Lead Intake + Diagnostic & Mirror + Offer & Pricing + Governance | 10-layer business audit → tiered engagement | $150-$497/diagnostic |
| Content Lab | Content Lab + Platform Strategists + Video Production | 200 pieces/month, 5+ platforms, brand governance | $97-$997/mo |
| Communication Suite | Communication Hub + FOTW Meeting Capture + Between-Session | Voice + video + meeting intelligence | $197-$497/mo |
| FOTW Intelligence Suite | All FOTW nodes + GRAG + Role Modeler | Passive → real-time → operational modeling | $297-$997/mo |
| Autonomous Front Office | ALL system nodes composed | Complete AI-operated business front-end | $2,997-$15,997/mo |

---

# VI. FULL-SPECTRUM GAP ANALYSIS (RESOLVED)

## Consumer-Facing Gaps

| Gap | Status | Resolution |
|-----|--------|-----------|
| FP1 Fresh Presence not linked to Content Lab | **CLOSED** | Direct event bus link: `content.published` triggers `presence.profile.updated` |
| EDU1 niche-specific scripts not pre-loaded | **CLOSED** | Niche packs in `context_vault/niches/{agency,saas,local_service}/` verified |
| PS-EM 0-100 scoring not hard-coded in email router | **CLOSED** | LI_SC_LEAD_SCORER threshold set to 85; low-intent filtered before voice queue |

## Internal Process Gaps

| Gap | Status | Resolution |
|-----|--------|-----------|
| EVL1 Evolution Steward not scheduled | **CLOSED** | Runs every Tuesday 09:00 EST. Converts Monday launch data into constitutional tweaks |
| Sovereignty Auditor for CRM sync | **CLOSED** | Sub-routine in `crm_sync_push.py` verifies Airtable mirror without losing local sovereignty |
| M1 Asset Marshall Visual Mask enforcement | **CLOSED** | Visual Mask validation added to Brand Validator (V1) pipeline before BUS distribution |
| FIN_OPS_01 Vault sync verification | **YELLOW → MONITORING** | Scheduled for verification during pre-flight. Alert if constitutional pricing data stale > 24h |

## Role-to-Process Verification Matrix

| Category | Node/Role | Mission | Status | Gap Fix |
|----------|-----------|---------|--------|---------|
| Consumer | TTLG | Run Diagnostic & Mirror Report | GREEN | Niche-packs loaded |
| Consumer | LI-SC Scorer | Score leads 0-100 | GREEN | Threshold 85 |
| Consumer | FP1 Fresh Presence | Prevent stale profile | GREEN | Content Lab linked |
| Consumer | EDU1 Educational Architect | Niche-specific scripts | GREEN | Vault pre-loaded |
| Internal | EPOS Doctor | Monitor SPR & Model Drift | GREEN | Reset trigger at 0.85 |
| Internal | FIN_OPS_01 | BPO Tier Pricing & Audits | YELLOW | Verify sync with Vault |
| Internal | EVL1 Evolution Steward | Tuesday Pivot/Evolution | GREEN | Scheduled T+24h post-launch |
| Internal | M1 Asset Marshall | Visual Mask enforcement | GREEN | V1 validation added |
| Internal | Sovereignty Auditor | CRM sync sovereignty | GREEN | Sub-routine deployed |

---

# VII. SOVEREIGN PROCUREMENT PLAN

Every 3rd-party SaaS is a "pluggable utility" — no SaaS Cage lock-in.

| Service | Category | EPOS Deployment Mode | Integration Point | Monthly Cost |
|---------|----------|---------------------|-------------------|-------------|
| ElevenLabs | Voice Synthesis | Agentic (Voice Agents) | API key in Vault; mapped to 4 Role Profiles | $22-$99 |
| HeyGen | Video/Avatar | Agentic (Asset Production) | 18+ derivative cascade; Visual Mask enforcement | $59-$299 |
| Whisper (local) | Transcription | Foundational (Intelligence) | Local ASR; zero cloud upload | $0 |
| Runway Gen-3 | Video Generation | Agentic (B-roll/Motion) | Supplemental visuals for cascade derivatives | $76-$144 |
| MidJourney/Flux | Image Generation | Agentic (Thumbnails/Visuals) | On-brand visual identity for all platforms | $30-$120 |
| Suno | Music/Audio | Agentic (Audio beds) | Original compositions for video content | $22-$44 |
| MailChimp | Email/Nurture | Automation (Distribution) | PS-EM role; synced with Airtable CRM spine | $20-$100 |
| Zoom | Delivery/Sales | Conventional → Hybrid | LI-ROUTER for Tier 4 calls; auto-transcribed via Whisper | $15-$25 |
| SMS/WhatsApp | Engagement | Agentic (Nurture) | CONV1 Conversation Strategist for Score 31-70 | $20-$50 |
| Airtable | CRM/Operations | Automation (Backbone) | Lead tracking, project status, client management | $50 |
| uuid.uuid4 | Identity Logic | Foundational | Immutable Lead IDs in agent_registry.json | $0 (stdlib) |

**Sovereignty Rule:** All API keys stored in Vault, never hard-coded. All data mirrored locally. Any service can be replaced without architectural change.

---

# VIII. SYSTEM UPGRADE PRODUCTION PIPELINE

The immune system and R&D lab of the organism. Follows the Triple Compulsion (Implement, Document, Surveil).

## The 6-Stage Upgrade Loop

1. **Detection (Gap Brief):** AN1 identifies performance decay or manual bottleneck in Mission Control
2. **Simulation (Sandbox):** ARCHITECT creates a "Shadow Node" — new logic tested against historical Vault data
3. **Governance Gate (SPR Check):** EPOS Doctor audits Shadow Node for 9th-Order Drift or constitutional violations
4. **Procurement & Integration:** If upgrade needs new service hooks, Sovereign Procurement Plan updates
5. **Kinetic Deployment:** Producer pushes new `.json` manifest to MCP server
6. **Recursive Learning:** EVL1 monitors new version for 72 hours, logging resonance metrics to Vault

## Internal Upgrade Roles

| Role | Skill Set | Upgrade Responsibility |
|------|-----------|----------------------|
| DOC (EPOS Doctor) | Constitutional Audit | Verifying upgrades maintain 9th-order framing |
| META (Meta-Steward) | Architectural Integrity | Versioning agent_registry.json and node manifests |
| VAULT (Librarian) | Data Sovereignty | Ensuring upgrade logs are indexed for future GRAG |
| GATE (Gatekeeper) | Security & Permissions | API token rotations for HeyGen, ElevenLabs, Zoom |
| EVL1 (Evolution Steward) | Pattern Recognition | Converting launch data into constitutional tweaks (every Tuesday 09:00) |

---

# IX. MISSION CONTROL DOCTRINE

## The 4-Quadrant Steward Interface

| Quadrant | Name | Monitors | Alert Trigger |
|----------|------|----------|---------------|
| Q1 | Sovereignty Health (Governance) | SPR drift, constitutional compliance, data sovereignty audits | SPR < 0.85 or sovereignty violation |
| Q2 | Matriculation Funnel (Journey) | 31+ touchpoint heatmap, 4-tier BPO distribution, conversion rates | Phase stall > 48hr or conversion < target |
| Q3 | Production Foundry (Execution) | Video Pipeline, Content Lab output, niche intelligence pack freshness | Production < 50 pieces/week or niche pack > 90 days |
| Q4 | Steward Signal Queue (Action) | Leads with Score > 85, expansion-ready clients, at-risk accounts | Any score > 85 or engagement health < 60 |

---

# X. UNIVERSAL NODE SCHEMA (Context Vault + MCP)

Machine-readable manifest for every role, process node, and system node:

```json
{
  "node_id": "ttlg_diagnostic_system",
  "node_type": "system",
  "version": "1.0.0",
  "status": "sovereign_certified",
  "journey_layers": ["identity","intent","classification","scoring","routing","delivery","feedback","learning","steward_signal"],
  "business_niches": ["agency","saas","local_service","enterprise","creator"],
  "roles_involved": ["TTLG","MA1","FOTW","PS-EM","AN1","GrowthSteward"],
  "cognitive_profile": {
    "steward_bias": "pre-mortem_consequence_chain",
    "executor_bias": "atomic_offer_generation",
    "iideate_stage_emphasis": ["IMMERSION","DESIGN","ANALYSIS"]
  },
  "capabilities": {
    "inputs": ["client_needs","budget_range","digital_footprint"],
    "outputs": ["mirror_report","tiered_engagement_options","resonance_scores"],
    "events_published": ["diagnostic.started","diagnostic.engagement_created","diagnostic.pricing_calculated"]
  },
  "communication_channels": ["email","voice_agent","avatar_video","meeting_grag"],
  "monetization": {
    "standalone": "$150-497/diagnostic",
    "bundle": "Included in Autonomous Front Office",
    "white_label": "Available at L6"
  }
}
```

## Role Manifest Schema (Per-Niche Modifiers)

```json
{
  "role_id": "PS-EM",
  "role_name": "Email Strategist",
  "domain_skills": ["journey-aware sequence design","psychological state classification","CTA token mapping"],
  "cognitive_nuances": {
    "steward_mode": ["anticipates 3 downstream touchpoints per email","scans for flywheel impact and revenue layer"],
    "executor_mode": ["formats copy to EPOS voice rules","ensures every email earns the next open"]
  },
  "business_niche_modifiers": {
    "agency": "emphasize white-label leverage and client margin",
    "saas": "emphasize pipeline acceleration and feature adoption",
    "local_service": "emphasize call volume and booked jobs",
    "enterprise": "emphasize governance, compliance, and sovereignty",
    "creator": "emphasize content velocity and audience growth"
  },
  "journey_layer_fit": ["identity","intent","delivery","feedback"]
}
```

---

# XI. NICHE INTELLIGENCE PACKS

Per niche, stored in Context Vault and queued in node-dedicated MCP server:

| Niche | Vault Path | Diagnostic Emphasis | Mirror Report Focus | Offer Angle |
|-------|-----------|-------------------|--------------------|-----------:|
| Agency | `context_vault/niches/agency/` | Client delivery bottlenecks, content scaling limits | Spaghetti Diagram of client workflows | White-label leverage + 80% margin |
| SaaS | `context_vault/niches/saas/` | Pipeline velocity, feature adoption, churn signals | Tech stack brittleness + data sovereignty audit | Integration depth + predictive intelligence |
| Local Service | `context_vault/niches/local_service/` | Scheduling, follow-up, review management | Response time map + missed opportunity calculator | Call volume + booked jobs ROI |
| Enterprise | `context_vault/niches/enterprise/` | Cross-department coordination, governance gaps | Governance audit + SaaS Cage assessment | Sovereignty + compliance + accumulated intelligence |
| Creator | `context_vault/niches/creator/` | Content velocity limits, platform dependency | Content output vs potential with EPOS | 10x content velocity + brand consistency |

Each pack contains: `diagnostic_prompts.json`, `offer_menus.json`, `email_scripts.json`, `failure_scenarios.json`, `voice_note_scripts.json`

---

# XII. PRE-FLIGHT GO/NO-GO CHECKLIST

## 1. Environment & Services
- [ ] Python 3.11.x confirmed, EPOS root path valid
- [ ] Agent Zero path valid, Ollama model up
- [ ] Ports 8001 (EPOS API) and 11434 (Ollama) in expected state
- [ ] API keys active: ElevenLabs, HeyGen, MailChimp, Zoom, Airtable
- [ ] API keys stored in Vault (not hard-coded), rate limits configured

## 2. Vault & Mission Control Integrity
- [ ] Context Vault structure complete (mission_data, bi_history, market_sentiment, agent_logs)
- [ ] `journey_map.json`, `agent_registry.json`, `mission_control.json` readable by MCP servers
- [ ] Niche packs (Agency, SaaS, Local Service) present with non-empty diagnostic_prompts.json
- [ ] EPOS Completion Prospectus v2 stored in `context_vault/doctrine/`

## 3. Governance & Drift Controls
- [ ] `epos_doctor.py --json` returns exit code 0 (all 15 checks pass)
- [ ] SPR drift-correction threshold set to 0.85 with actions encoded
- [ ] EVL1 Evolution Steward scheduled for Tuesday 09:00 EST
- [ ] `upgrade_pipeline.json` present for post-launch evolution

## 4. Content & Communication Readiness
- [ ] Content Lab health: all 6 components report "healthy"
- [ ] "Portal Entry" email sequence (TP_01-TP_05) queued in MailChimp
- [ ] HeyGen avatar templates configured (Founder Glow, Schematic, Glitch)
- [ ] ElevenLabs voice agent scripts pass Brand Validator
- [ ] Visual Mask enforcement active in V1 pipeline

## 5. Permissions & Access
- [ ] BrowserUse has read/write to all Context Vault paths
- [ ] `crm_sync_push.py` verified to update Airtable on score changes
- [ ] Mission Control interface open and ready for Steward Signal Queue
- [ ] Sovereignty Auditor sub-routine active

**ALL CHECKS PASS → GO**

BrowserUse initializes:
1. Initial Market Echolocation scan (first target batch)
2. Mission Control quadrant activation
3. Resonance Queue monitoring begins
4. I.I.D.E.A.T.E. Cycle 1 Immersion

---

> "The roadmap is rendered inevitable. The design is sovereign. The organism is ready to breathe. Let lil Essa walk." — Jamie Purdue, February 2026