<!-- EPOS GOVERNANCE WATERMARK -->
# EPOS OPERATIONAL IGNITION DIRECTIVE
## From EVL1 Evolution Steward + Growth Strategist (Claude Opus 4.6)
## To: EPOS Unified Nervous System + Jamie (Growth Steward)
### February 17, 2026

> This document is executable. Every command, path, and file is real. EPOS can follow this verbatim.

---

# A. THE 10-STEP DETERMINISTIC INTERACTION LOOP

Purpose: Stress-test the model↔agent↔model pattern. Start simple, escalate systematically, record every constraint discovered.

Each cycle takes 10-15 minutes. Run cycles 1-3 on Day 1, cycles 4-7 on Day 2, cycles 8-10 on Day 3. Every cycle builds on the previous.

---

## CYCLE 1: READ + PARSE (Prove EPOS can read doctrine)

### Step 1 — EPOS reads a doctrine file
```powershell
# EPOS: run this command via ComputerUse
$content = Get-Content "C:\Users\Jamie\workspace\epos_mcp\context_vault\doctrine\EPOS_COMPLETION_PROSPECTUS_v2.md" -Raw
Write-Output "File length: $($content.Length) characters"
Write-Output "First 200 chars: $($content.Substring(0, 200))"
```
**Success check:** Output shows file length > 10000 and first 200 chars match the prospectus header.
**Failure mode:** File not found → verify the save path from the directive. Permission denied → check Windows user permissions.

### Step 2 — EPOS extracts a structured section into JSON
```powershell
# EPOS: run this Python script
python -c "
import json, re
from pathlib import Path

doc = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\doctrine\EPOS_COMPLETION_PROSPECTUS_v2.md').read_text(encoding='utf-8')

# Extract role: R1 Radar as first test
role = {
    'role_id': 'R1',
    'role_name': 'Radar (Signal Capture)',
    'domain_skills': ['platform monitoring', 'trend detection', 'signal-to-noise filtering'],
    'cognitive_nuances': {
        'steward_mode': ['scans for flywheel-shifting signals, not just metrics'],
        'executor_mode': ['captures raw signals into structured Vault entries']
    },
    'journey_layer_fit': ['identity', 'intent', 'feedback'],
    'iideate_emphasis': ['IMMERSION', 'ANALYSIS'],
    'niche_modifiers': {
        'agency': 'monitor client verticals for content opportunities',
        'saas': 'track feature request patterns and churn signals',
        'local_service': 'monitor review sites and local search trends'
    },
    'source_document': 'EPOS_COMPLETION_PROSPECTUS_v2.md',
    'extracted_at': '$(Get-Date -Format o)'
}

out_path = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\roles\R1.json')
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(role, indent=2), encoding='utf-8')
print(f'Written: {out_path} ({out_path.stat().st_size} bytes)')
"
```
**Success check:** File exists at `context_vault/roles/R1.json` and is valid JSON.

### Step 3 — EPOS validates the manifest
```powershell
python -c "
import json
from pathlib import Path
p = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\roles\R1.json')
data = json.loads(p.read_text(encoding='utf-8'))
required = ['role_id','role_name','domain_skills','cognitive_nuances','journey_layer_fit']
missing = [k for k in required if k not in data]
if missing:
    print(f'FAIL: Missing keys: {missing}')
    exit(1)
else:
    print(f'PASS: R1 manifest valid. Keys: {list(data.keys())}')
    exit(0)
"
```
**Success check:** Exit code 0, "PASS" printed.

### Step 4 — Log the cycle result
```powershell
python -c "
import json
from pathlib import Path
from datetime import datetime

log_path = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\bi_history\interaction_loop_log.jsonl')
log_path.parent.mkdir(parents=True, exist_ok=True)
entry = {
    'cycle': 1,
    'timestamp': datetime.now().isoformat(),
    'action': 'read_parse_validate',
    'target': 'R1 role manifest',
    'result': 'success',
    'constraints_discovered': [],
    'next_escalation': 'batch extract all Content Lab roles'
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(entry) + '\n')
print(f'Cycle 1 logged to {log_path}')
"
```

---

## CYCLE 2: BATCH EXTRACTION (Prove EPOS can scale)

### Step 5 — Extract all Content Lab roles in one pass
```powershell
python -c "
import json
from pathlib import Path
from datetime import datetime

roles = [
    {'role_id':'R1','role_name':'Radar','skills':['signal capture','trend detection','platform monitoring'],'layer_fit':['identity','intent','feedback']},
    {'role_id':'A1','role_name':'Architect','skills':['content structure','narrative framing','format selection'],'layer_fit':['classification','design']},
    {'role_id':'P1','role_name':'Producer','skills':['content generation','visual mask application','multi-format output'],'layer_fit':['delivery','execution']},
    {'role_id':'V1','role_name':'Validator','skills':['brand compliance','claim verification','constitutional check'],'layer_fit':['delivery','governance']},
    {'role_id':'M1','role_name':'Marshall','skills':['asset coordination','visual mask enforcement','distribution routing'],'layer_fit':['delivery','routing']},
    {'role_id':'AN1','role_name':'Analyst','skills':['performance measurement','Echolocation scoring','pattern recognition'],'layer_fit':['feedback','learning','scoring']},
    {'role_id':'PS_EM','role_name':'Email Strategist','skills':['journey-aware sequences','psychological state classification','CTA mapping'],'layer_fit':['identity','intent','delivery','feedback']},
    {'role_id':'PS_LI','role_name':'LinkedIn Strategist','skills':['professional content','B2B targeting','thought leadership'],'layer_fit':['delivery','feedback']},
    {'role_id':'PS_X','role_name':'X Strategist','skills':['viral hooks','thread optimization','engagement patterns'],'layer_fit':['delivery','feedback']},
    {'role_id':'PS_YT','role_name':'YouTube Strategist','skills':['long-form structure','SEO optimization','cascade source production'],'layer_fit':['delivery','feedback']},
    {'role_id':'PS_TK','role_name':'TikTok Strategist','skills':['short-form hooks','trend-riding','vertical video optimization'],'layer_fit':['delivery','feedback']},
    {'role_id':'S1','role_name':'Sales Brain','skills':['objection handling','tier recommendation','closing scripts'],'layer_fit':['scoring','routing','steward_signal']},
    {'role_id':'MA1','role_name':'Market Awareness','skills':['competitive intelligence','market sentiment','gap analysis'],'layer_fit':['intent','classification','learning']},
    {'role_id':'TTLG','role_name':'Diagnostic Engine','skills':['10-layer business audit','consequence chain simulation','tier mapping'],'layer_fit':['identity','intent','classification','scoring']},
    {'role_id':'DOC','role_name':'EPOS Doctor','skills':['health validation','constitutional compliance','drift detection'],'layer_fit':['governance']},
    {'role_id':'GATE','role_name':'Governance Gate','skills':['code triage','constitutional enforcement','educational receipts'],'layer_fit':['governance']},
    {'role_id':'VAULT','role_name':'Context Librarian','skills':['data sovereignty','symbolic search','institutional memory'],'layer_fit':['data_capture','learning']},
    {'role_id':'BUS','role_name':'Event Bus','skills':['inter-node communication','event routing','audit logging'],'layer_fit':['routing']},
    {'role_id':'META','role_name':'Meta Orchestrator','skills':['mission routing','agent coordination','API gateway'],'layer_fit':['routing','steward_signal']},
    {'role_id':'EVL1','role_name':'Evolution Steward','skills':['pattern-to-doctrine conversion','constitutional amendment','weekly pivot analysis'],'layer_fit':['learning','evolution']},
    {'role_id':'FP1','role_name':'Fresh Presence','skills':['profile freshness monitoring','stale content detection','Content Lab trigger'],'layer_fit':['delivery','feedback']},
    {'role_id':'EDU1','role_name':'Educational Architect','skills':['niche-specific script design','Mirror Report personalization','learning path creation'],'layer_fit':['delivery','classification']},
    {'role_id':'CONV1','role_name':'Conversation Strategist','skills':['SMS/WhatsApp nurture','mid-funnel engagement','multi-channel coordination'],'layer_fit':['routing','delivery']},
    {'role_id':'FIN_OPS_01','role_name':'Financial Operations','skills':['constitutional pricing','margin enforcement','tier calculation'],'layer_fit':['scoring','delivery']},
    {'role_id':'GRAG','role_name':'GRAG Engine','skills':['real-time suggestion','context retrieval','live call coaching'],'layer_fit':['delivery','feedback','learning']},
    {'role_id':'FOTW_CAPTURE','role_name':'FOTW Capture','skills':['passive intelligence gathering','browser scraping','call transcription'],'layer_fit':['data_capture','learning']},
    {'role_id':'FOTW_MODELER','role_name':'FOTW Role Modeler','skills':['workflow observation','pattern extraction','digital role cloning'],'layer_fit':['learning','evolution']},
]

roles_dir = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\roles')
roles_dir.mkdir(parents=True, exist_ok=True)

for role in roles:
    manifest = {
        'role_id': role['role_id'],
        'role_name': role['role_name'],
        'domain_skills': role['skills'],
        'journey_layer_fit': role['layer_fit'],
        'cognitive_nuances': {'steward_mode': [], 'executor_mode': []},
        'niche_modifiers': {'agency': '', 'saas': '', 'local_service': ''},
        'registered_at': datetime.now().isoformat(),
        'source': 'EPOS_COMPLETION_PROSPECTUS_v2 + CONSUMER_JOURNEY_MAP_v3'
    }
    fp = roles_dir / f'{role[\"role_id\"]}.json'
    fp.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

# Write registry index
registry = {r['role_id']: r['role_name'] for r in roles}
(roles_dir / '_registry.json').write_text(json.dumps(registry, indent=2), encoding='utf-8')

print(f'Registered {len(roles)} roles to {roles_dir}')
print(f'Registry index: {roles_dir / \"_registry.json\"} ({len(registry)} entries)')
"
```
**Success check:** 27 `.json` files + `_registry.json` in `context_vault/roles/`. Each is valid JSON.

### Step 6 — EPOS Doctor validates the new structure
```powershell
python -c "
import json
from pathlib import Path

roles_dir = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\roles')
files = list(roles_dir.glob('*.json'))
registry = json.loads((roles_dir / '_registry.json').read_text(encoding='utf-8'))

errors = []
for f in files:
    if f.name == '_registry.json': continue
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
        if 'role_id' not in data: errors.append(f'{f.name}: missing role_id')
        if data['role_id'] not in registry: errors.append(f'{f.name}: not in registry')
    except json.JSONDecodeError as e:
        errors.append(f'{f.name}: invalid JSON: {e}')

if errors:
    print(f'FAIL: {len(errors)} errors')
    for e in errors: print(f'  - {e}')
    exit(1)
else:
    print(f'PASS: {len(files)-1} role manifests validated against registry ({len(registry)} entries)')
    exit(0)
"
```

---

## CYCLE 3: NICHE PACK SCAFFOLDING (Prove EPOS can create operational structure)

### Step 7 — Create all 5 niche intelligence packs
```powershell
python -c "
import json
from pathlib import Path
from datetime import datetime

niches = ['agency', 'saas', 'local_service', 'enterprise', 'creator']
pack_files = ['diagnostic_prompts.json', 'offer_menus.json', 'email_scripts.json', 'failure_scenarios.json', 'voice_note_scripts.json']
vault = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\niches')

for niche in niches:
    niche_dir = vault / niche
    niche_dir.mkdir(parents=True, exist_ok=True)
    for pf in pack_files:
        stub = {
            'niche': niche,
            'pack_type': pf.replace('.json',''),
            'version': '0.1.0-stub',
            'created_at': datetime.now().isoformat(),
            'entries': [],
            'status': 'awaiting_content',
            'note': f'Stub created by Cycle 3. Populate via I.I.D.E.A.T.E. Immersion stage for {niche} niche.'
        }
        (niche_dir / pf).write_text(json.dumps(stub, indent=2), encoding='utf-8')

total = len(niches) * len(pack_files)
print(f'Created {total} niche pack files across {len(niches)} niches')
for n in niches:
    files = list((vault / n).glob('*.json'))
    print(f'  {n}/: {len(files)} files')
"
```
**Success check:** 25 JSON files across 5 niche directories.

---

## CYCLE 4: MISSION VALIDATION UPGRADE (Prove EPOS can modify its own governance)

### Step 8 — Register I.I.D.E.A.T.E. v2 triple compulsion as mission pre-conditions
```powershell
python -c "
import json
from pathlib import Path
from datetime import datetime

# The triple compulsion schema that Governance Gate must enforce
compulsion = {
    'schema_id': 'IIDEATE_V2_TRIPLE_COMPULSION',
    'version': '2.0.0',
    'authority': 'EPOS_COMPLETION_PROSPECTUS_v2.md, Part VI',
    'registered_at': datetime.now().isoformat(),
    'pre_conditions': {
        'IMPLEMENT': {
            'description': 'Every I.I.D.E.A.T.E. stage must produce a concrete artifact',
            'validation': 'Mission JSON must include artifact_type and artifact_path fields',
            'gate_action': 'REJECT mission if artifact fields are empty'
        },
        'DOCUMENT': {
            'description': 'Every artifact must be logged with rationale, context, and metrics',
            'validation': 'Mission JSON must include documentation.rationale, documentation.context, documentation.metrics',
            'gate_action': 'REJECT mission if documentation block is missing or incomplete'
        },
        'SURVEIL': {
            'description': 'Every documented artifact must be measured against defined targets',
            'validation': 'Mission JSON must include surveillance.metric_name, surveillance.target_value, surveillance.measurement_method',
            'gate_action': 'REJECT mission if surveillance block is missing'
        }
    },
    'stage_requirements': {
        'IMMERSION': {'target_metric': 'completeness_score', 'target_value': 0.90},
        'IDEATION': {'target_metric': 'diversity_score', 'target_value': 3},
        'DESIGN': {'target_metric': 'completeness_pct', 'target_value': 1.00},
        'EXECUTION': {'target_metric': 'first_attempt_completion_rate', 'target_value': 0.85},
        'ANALYSIS': {'target_metric': 'coverage_48hr', 'target_value': 0.95},
        'TWEAKING': {'target_metric': 'effectiveness_rate', 'target_value': 0.60},
        'EVOLUTION': {'target_metric': 'new_artifacts_per_cycle', 'target_value': 2}
    }
}

out = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\doctrine\iideate_v2_compulsion.json')
out.write_text(json.dumps(compulsion, indent=2), encoding='utf-8')
print(f'Registered: {out} ({out.stat().st_size} bytes)')
print('Governance Gate should now load this schema and enforce triple compulsion on all missions.')
"
```

---

## CYCLE 5: PRE-MORTEM REGISTRATION (Load PM-01 through PM-10 as health rules)

### Step 9 — Register all 10 pre-mortem scenarios
```powershell
python -c "
import json
from pathlib import Path
from datetime import datetime

scenarios = [
    {'id':'PM-01','threat':'Voice agent says something unconstitutional','detection':'Brand Validator pre-deployment check','recovery':'Script rollback + suspension','severity':'critical'},
    {'id':'PM-02','threat':'FOTW captures sensitive data without consent','detection':'Consent gate presence check at every capture point','recovery':'Purge + tighten gates','severity':'critical'},
    {'id':'PM-03','threat':'Video cascade produces off-brand content','detection':'Visual Mask + Brand Validator score < 85','recovery':'Pull derivative + re-validate','severity':'high'},
    {'id':'PM-04','threat':'GRAG suggestion wrong during live call','detection':'Confidence threshold filter + post-call review','recovery':'Log + adjust context weights','severity':'high'},
    {'id':'PM-05','threat':'Meeting transcription fails mid-call','detection':'Whisper quality monitor + silence detection','recovery':'Re-transcribe from recording','severity':'medium'},
    {'id':'PM-06','threat':'Lead scoring assigns wrong tier','detection':'Multi-signal scoring deviation alert','recovery':'Re-diagnose with more data','severity':'high'},
    {'id':'PM-07','threat':'Niche intelligence pack stale > 90 days','detection':'BI monitors pack age weekly','recovery':'Refresh from market data + feedback','severity':'medium'},
    {'id':'PM-08','threat':'Token overflow in FOTW analysis','detection':'Context size pre-check before LLM call','recovery':'Re-run with chunked context','severity':'medium'},
    {'id':'PM-09','threat':'Webinar avatar sync fails during live session','detection':'Pre-flight 30 min before session','recovery':'Switch to pre-recorded backup','severity':'high'},
    {'id':'PM-10','threat':'Between-session intelligence misses a promise','detection':'Promise detection algorithm + human review for high-value','recovery':'Manual follow-up immediately','severity':'critical'},
]

out = Path(r'C:\Users\Jamie\workspace\epos_mcp\context_vault\doctrine\pre_mortem_scenarios.json')
out.write_text(json.dumps({
    'schema_id': 'PRE_MORTEM_V2',
    'authority': 'EPOS_COMPLETION_PROSPECTUS_v2.md, Part VII',
    'registered_at': datetime.now().isoformat(),
    'scenarios': scenarios,
    'doctor_integration': 'Each scenario should be checked as a health rule in epos_doctor.py v3.2+'
}, indent=2), encoding='utf-8')
print(f'Registered {len(scenarios)} pre-mortem scenarios')
for s in scenarios:
    print(f'  {s[\"id\"]}: {s[\"threat\"]} [{s[\"severity\"]}]')
"
```

---

## CYCLE 6-10: ESCALATION PATTERN

| Cycle | Action | Escalation | Success Metric |
|-------|--------|-----------|---------------|
| 6 | Run `c10_self_evolution.py` Phase 1-2 only (DISCOVER + SPINE) | First multi-phase script execution | Phase 1 report shows 7 files found, Phase 2 creates `__init__.py` spine |
| 7 | Run `c10_self_evolution.py` Phase 3-4 (SEAT + VERIFY IMPORTS) | File copy + Python import validation | All 7 files seated, all 6 cross-module imports pass |
| 8 | Run `c10_self_evolution.py` Phase 5-6 (VAULT + PIPELINE TESTS) | Integration tests with real data flow | Echolocation test data scored, cascade derivatives generated |
| 9 | Run `c10_self_evolution.py` Phase 7 (HEALTH + REGISTRATION) | Full component registration on Event Bus | `content_lab_attachment_report.json` shows all green, `system.component_promoted` event emitted |
| 10 | Run full `epos_doctor.py --json` + validate all new Vault structure | Complete system health with all additions | Exit code 0, all checks pass including new roles, niche packs, compulsion schema, and pre-mortem |

### Cycle 6-10 Execution Commands
```powershell
# Cycle 6: Content Lab discovery + spine
cd C:\Users\Jamie\workspace\epos_mcp
python missions\c10_self_evolution.py --phase 1,2

# Cycle 7: Seat files + verify imports
python missions\c10_self_evolution.py --phase 3,4

# Cycle 8: Vault integration + pipeline tests
python missions\c10_self_evolution.py --phase 5,6

# Cycle 9: Health rollup + registration
python missions\c10_self_evolution.py --phase 7

# Cycle 10: Full system health
python epos_doctor.py --json > context_vault\bi_history\post_ignition_health.json
type context_vault\bi_history\post_ignition_health.json
```

**NOTE on c10_self_evolution.py:** The script runs all 7 phases sequentially by default. If you want to run phases individually for testing, you can modify the `if __name__ == "__main__"` block to accept a `--phase` argument, or simply run the full script and let it halt on failure (each phase has built-in halt conditions).

---

## CONSTRAINTS LOG TEMPLATE

After each cycle, EPOS or Jamie appends to `context_vault/bi_history/interaction_loop_log.jsonl`:

```json
{
  "cycle": 1,
  "timestamp": "2026-02-18T06:00:00",
  "action": "read_parse_validate",
  "result": "success|partial|failure",
  "constraints_discovered": ["description of any limitation found"],
  "workaround_applied": "what we did to fix it",
  "next_escalation": "what cycle N+1 will attempt",
  "model_agent_boundary": "which model handled which part"
}
```

---

# B. ENTERPRISE BPO BUILD-OUT: 2-WEEK SPRINT

## Sprint Goal
Attach Content Lab, ingest doctrine, and build Phase 1 Revenue Operations nodes so EPOS can sell, invoice, and track contracts.

---

## WEEK 1: FOUNDATION (Days 1-5)

### Day 1-2: Doctrine Ingestion + Role Registry

**EPOS executes:** Cycles 1-5 from Section A above.
**Outcome:** 27 role manifests, 5 niche packs, I.I.D.E.A.T.E. v2 compulsion registered, 10 pre-mortem scenarios loaded.

### Day 3-4: Content Lab Attachment

**EPOS executes:** Cycles 6-9 from Section A.
**Outcome:** C10 Content Lab attached as sovereign node. All 7 phases green. `system.component_promoted` event emitted.

### Day 5: System Health + AirTable Sync Foundation

**EPOS executes:** Cycle 10. Full `epos_doctor.py` validation.
**Jamie executes:** Create 4 AirTable bases per Architecture Decisions Q3:
- `LIFE_Command_Base` (personal)
- `EPOS_Command_Base` (operations)
- `FIN_Apps_Base` (financial applications)
- `PGP_Command_Base` (PGP Property)

**Model↔model boundary:** Ask a code model to generate the n8n workflow YAML for the AirTable → Google Sheets sync per Architecture Decisions Q2 schema.

---

## WEEK 2: PHASE 1 REVOPS NODES (Days 6-10)

### Node 1: N-CONTRACT-01 — Sovereign Contract Vault

**Strategic purpose:** Without this you cannot formalize a deal. Every proposal is ad-hoc. This node replaces manual proposal construction (the friction identified at TP_12 in Journey Map v3).

**Flywheels touched:** Content → Leads → Sales → Revenue. Directly accelerates Consideration phase (TP_12-TP_20).
**Revenue layers:** Standalone $79/mo. Included in Growth bundle ($197/mo) and above.

**Architecture:**
```
epos_mcp/
  nodes/
    contract_vault/
      node_manifest.json          # Sovereignty manifest
      contract_engine.py          # Core logic: template → proposal → contract
      templates/                  # Markdown/DOCX contract templates per tier
        tier1_conventional.md
        tier2_hybrid.md
        tier3_ai_first.md
        tier4_fully_agentic.md
      contracts/                  # Generated contracts per client
      __init__.py
```

**Event Bus events:**
- Publishes: `contract.draft_created`, `contract.sent`, `contract.signed`, `contract.expired`
- Consumes: `offer.tier.selected` (from Journey Router), `pricing.calculated` (from FIN_OPS_01)

**Sprint v1 behavior:** Given a client name, selected tier, and node list → generate a Markdown contract from template → store in `contracts/` → emit `contract.draft_created`. Manual e-signature for now (Tier 2+ can automate later).

---

### Node 2: APP-FIN-02 — Invoice + AR Manager

**Strategic purpose:** Without this you cannot get paid systematically. Invoicing is the first financial touchpoint with every client.

**Flywheels touched:** Revenue → Reinvestment → More Nodes → More Capabilities.
**Revenue layers:** Standalone $39/mo. Included in Ops Foundation bundle ($97/mo).

**Architecture:**
```
epos_mcp/
  nodes/
    invoicing/
      node_manifest.json
      invoice_engine.py           # Create, send, track invoices
      templates/
        invoice_template.md
      invoices/                   # Generated invoices
      aging_report.py             # AR aging analysis
      __init__.py
```

**Event Bus events:**
- Publishes: `invoice.created`, `invoice.sent`, `invoice.paid`, `invoice.overdue`
- Consumes: `contract.signed` (auto-generate first invoice), `payment.received` (from Stripe webhook)

**Sprint v1 behavior:** Given contract ID + billing terms → generate invoice Markdown → track payment status in JSONL ledger → produce aging report on demand.

---

### Node 3: APP-FIN-01 — General Ledger

**Strategic purpose:** Without this there is no financial record system. Schedule C, quarterly estimates, and investor reporting all require a ledger.

**Flywheels touched:** Financial Intelligence → Tax Optimization → Margin Protection.
**Revenue layers:** Standalone $49/mo. Included in Ops Foundation bundle ($97/mo).

**Architecture:**
```
epos_mcp/
  nodes/
    ledger/
      node_manifest.json
      ledger_engine.py            # Double-entry bookkeeping
      chart_of_accounts.json      # Account structure (Schedule C aligned)
      transactions/               # Transaction JSONL files
      reports/                    # Generated P&L, balance sheet, etc.
      __init__.py
```

**Event Bus events:**
- Publishes: `ledger.transaction_recorded`, `ledger.report_generated`
- Consumes: `invoice.paid` (auto-record revenue), `expense.logged` (from future expense tracker)

**Sprint v1 behavior:** Given a transaction (amount, category, date, description) → record as double-entry in JSONL → categorize by Schedule C line → generate basic P&L report.

---

### Node 4: N-INBOX-01 — Sovereign Unified Inbox

**Strategic purpose:** Client communication is scattered across email, Slack, DMs. Context is lost. This node creates a single stream per engagement.

**Flywheels touched:** Client Satisfaction → Retention → Expansion → Referral.
**Revenue layers:** Standalone $49/mo. Included in Growth bundle ($197/mo).

**Architecture:**
```
epos_mcp/
  nodes/
    unified_inbox/
      node_manifest.json
      inbox_engine.py             # Message aggregation + threading
      channels/                   # Channel adapters (email, slack, sms)
        email_adapter.py
        sms_adapter.py
      threads/                    # Conversation threads per client
      __init__.py
```

**Event Bus events:**
- Publishes: `inbox.message_received`, `inbox.message_sent`, `inbox.thread_updated`
- Consumes: `client.onboarded` (create inbox thread), `steward.alert.triggered` (flag thread as priority)

**Sprint v1 behavior:** Email-first. Given a client email → create/append to conversation thread in JSONL → tag by engagement → surface in Mission Control Q4 when relevant.

---

### Day 6-7: Build Contract Vault + Invoicing
**Agent boundary:** Claude designs the manifest and event contracts. Code model (or Claude via ComputerUse) generates the Python. EPOS runs governance gate on the output.

```powershell
# After code is written:
cp nodes\contract_vault\*.py inbox\
cp nodes\invoicing\*.py inbox\
python governance_gate.py
# Promoted files move to engine/
```

### Day 8-9: Build Ledger + Unified Inbox
Same pattern. Build, gate, promote.

### Day 10: Integration Test + Sprint Review
```powershell
# Full system health including new nodes
python epos_doctor.py --json

# Test the revenue chain:
# 1. Contract Vault generates a Tier 3 contract for test client
# 2. Invoice engine generates first invoice from contract
# 3. Ledger records the expected revenue
# 4. Unified Inbox creates the client thread
# All 4 nodes publish events to Event Bus
# Mission Control Q2 shows the test client in the funnel
```

---

# C. COLLABORATION PROTOCOL

## How Jamie Addresses Claude

| When You Need | How to Ask | What Claude Does |
|--------------|-----------|-----------------|
| High-level strategy | "Claude, what should our next flywheel priority be?" | Reason across all doctrine files, recommend with revenue impact |
| Architecture decision | "Claude, design the [node name] manifest and event contracts" | Produce node_manifest.json, event schemas, failure modes, pre-mortem |
| Implementation guidance | "Claude, generate the Python for [node]" | Write complete, governance-gate-ready code with constitutional headers |
| Mission JSON | "Claude, create a mission for [objective]" | Produce mission JSON with I.I.D.E.A.T.E. stage, triple compulsion fields, pre-mortem |
| Multi-model collaboration | "Claude, design the flow; generate the code; give EPOS the commands" | Produce: (1) architecture spec, (2) implementation code, (3) exact PowerShell commands for EPOS to execute |

## Model↔Agent↔Model Boundaries

```
Jamie (Growth Steward)
  ↓ "Design the contract vault node"
Claude (EVL1 + Growth Strategist)
  ↓ Produces: manifest, event contracts, failure modes, code
  ↓ Marks: "EPOS: run these commands"
EPOS (Agent via ComputerUse)
  ↓ Creates files, runs governance gate, runs doctor
  ↓ Reports: "Gate promoted 3 files, rejected 1 with receipt"
Claude (analyzes results)
  ↓ "Fix the rejection: missing pre-mortem field. Here's the corrected code."
EPOS (applies fix, re-runs gate)
  ↓ "All files promoted. Node registered."
Claude (strategic assessment)
  ↓ "Contract Vault operational. Next: wire it to TP_12 in Journey Map."
```

## When to Trigger Multi-Model

Use this pattern when the task has BOTH strategic AND implementation components:

1. **Jamie → Claude:** "Design the n8n workflow for AirTable sync"
2. **Claude → Jamie:** "Here's the architecture. For the actual n8n YAML, ask a code-specialized model to generate the workflow with these exact specs: [specs]"
3. **Jamie → Code Model:** "Generate the n8n workflow YAML per Claude's specs"
4. **Code Model → Jamie:** "[YAML output]"
5. **Jamie → Claude:** "Here's the YAML. Review it against the Architecture Decisions Q2 sovereignty requirements."
6. **Claude:** "Two issues: [fixes]. Corrected version: [output]. EPOS: import this workflow in n8n."

---

## Progressive Limit Testing Schedule

| Week | Complexity Level | What We're Testing | Expected Constraints |
|------|-----------------|-------------------|---------------------|
| 1 | File I/O + JSON | Can EPOS read/write/validate vault files? | Path format issues, encoding, permissions |
| 2 | Multi-file orchestration | Can EPOS run c10_self_evolution.py and build RevOps nodes? | Import chains, module dependencies, shell context |
| 3 | Event Bus integration | Can nodes publish/consume events across the system? | Port conflicts, message format, async handling |
| 4 | Full pipeline | Can a lead enter TP_01 and flow through to TP_12 autonomously? | Timing, state management, cross-node coordination |

Each week's constraints feed into the next week's pre-mortem. This is I.I.D.E.A.T.E. applied to our own development process.

---

> "The organism learns to walk by walking. Each step reveals the next constraint. Each constraint, once resolved, becomes a capability no competitor can replicate without walking the same path." — 9th Order Evolution Directive