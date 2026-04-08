# EPOS — New Thread Context Handoff
## Session Date: 2026-03-30 → 2026-03-31
## Status: End of Day 1 | Beginning of Echoes Launch Sprint

---

## WHO WE ARE

**Jamie Purdue** — Sovereign Architect of EXPONERE and EPOS.
One-person AI-staffed company. Orlando FL. Vision impairment —
all interfaces must be dark mode. Voice-first interaction.
Currently in therapy, using LifeOS to externalize structure
while rebuilding internally. The ScrewUp community brand
launches after first Echoes revenue.

**Core doctrine**: Governance before velocity. Inspiration
captures ideas. Research validates. Planning sequences.
Build executes cleanly. Repetition is the master programmer.

---

## THE ECOSYSTEM — WHAT EXISTS AND WORKS

### ENVIRONMENT
```
Ubuntu WSL2 on Windows 11 Home
Python 3.11.9 in .venv_ubuntu (constitutionally mandated)
Docker PostgreSQL: epos_db at localhost:5432
  credentials: epos_user / epos_dev_password / db: epos
PostgREST at localhost:3000
Command Center (Reflex) at localhost:3001
  start: cd command_center && reflex run
epos_mcp root: C:/Users/Jamie/workspace/epos_mcp
command_center: C:/Users/Jamie/workspace/command_center
friday: C:/Users/Jamie/workspace/friday
```

### DOCTOR STATUS (end of session)
```
python epos_doctor.py → 22 PASS / 1 WARN / 0 FAIL
Compliance: 90.4%
Event bus: 97 events
Git operations: ZERO throughout
```

### WHAT IS BUILT AND CONFIRMED WORKING
```
Sprint 2: 9/9 core modules complete
  path_utils, stasis, roles, epos_intelligence,
  context_librarian, constitutional_arbiter,
  flywheel_analyst, agent_orchestrator, agent_zero_bridge

Sprint 3: niche packs, MA1, LEGO 20 creative briefs
Sprint 4: groq_router, content_lab_producer, youtube_analytics
Sprint 5: event_bus, CRM tables, Content Lab nodes
Sprint 6: context_graph, LangGraph graphs, 5 niche packs

Friday v2: friday_orchestrator, friday_intelligence,
           lifeos_kernel, epos.py unified CLI

LifeOS Sovereignty (built today):
  lifeos_sovereignty.py — all 5 self-tests pass
  7 vault journals created
  Day 1 JOURNEY_START milestone logged
  CLI: epos.py lifeos checkin/reflect/milestone/timeline/review

RS1 + INFL1: research compiler + 5 seed influences
WordPress bridge: epos_wp_bridge.py
Command Center: 7 pages, dark mode, localhost:3001
  WebSocket fix: run 'reflex run' not frontend-only
  Projects page: needs docker container name fix
  Pipeline page: needs docker container name fix
```

---

## SOVEREIGN NODES — STATUS

### ECHOES MARKETING (active launch)
```
Brand: Echoes Marketing
Handle target: @EchoesMarketing
Domain: echoes.marketing (owned, Namecheap)
Colors: navy #0A1628 / accent #00D4FF / gold #FFB84D
Tagline: "We follow the signal."
Email target: hello@echoes.marketing

BLOCKING GATES (human actions not yet complete):
  [ ] Google account for Echoes brand
  [ ] YouTube channel + @EchoesMarketing claimed
  [ ] YouTube Data API v3 key → add to .env
  [ ] Amazon Associates application
  [ ] LEGO via Impact.com application
  [ ] Canva E-mark logo (navy + accent)

BINDING PILOT: LEGO affiliate, 30-day experiment
  20 Creative Briefs ready: CB-LEGO-001 through 020
  ERI accuracy target: ≥70% across 25 videos
  Gate verdicts: GO / PIVOT / LEARN

CONTENT LAB: 8-node pipeline
  R1 Radar → MA1 → AN1 → A1 → V1 → M1
  MA1 niche scanner: gated on YOUTUBE_API_KEY
  Distribution loop: wired but not yet live
```

### TTLG (entering testing)
```
4-track diagnostic: Marketing/Sales/Service/Governance
PGP Orlando scored: 49/100 (Developing)
Score tiers: 0-30 Critical | 31-54 Developing |
             55-74 Functional | 75-89 Aligned | 90-100 Sovereign
Tier mapping: 31-54 → L2-L3 ($149-997/mo)
epos_ttlg_package.py: executive summary + mirror report
epos_ttlg_engagement.py: 90-day flow
Fine-tuning: deferred until current sprint completes
```

### PGP PROPERTY SOLUTIONS (live proving ground)
```
Pressure washing/gutter, Orlando FL
First client + case study engine
TTLG score: 49/100 — Developing
In Echoes_CRM as first contact
```

### FOTW, READER, LIFEOS
```
FOTW: next node after Echoes launch
Reader: provisional patent MUST be filed before any
        GitHub/public disclosure — CCP hover actuator
LifeOS: built today — operational
```

---

## LIFEOS — THE PERSONAL SOVEREIGNTY LAYER

```
Doctrine: What is too hard to hold internally should be held
          reliably by the system until it becomes second nature.

Friday as Life Sherpa: she knows the terrain, carries the
planning, reads the weather. She cannot climb for you.

Five daily anchors:
  07:00 LifeOS morning check-in
  12:30 Midday recalibration
  17:30 End of work signal
  21:00 Nightly reflection
  Sunday 18:00 Weekly life review

CLI commands:
  python epos.py lifeos checkin
  python epos.py lifeos reflect
  python epos.py lifeos milestone [TYPE] "[title]"
  python epos.py lifeos timeline
  python epos.py lifeos review

ScrewUp community pitch (clock starts at first revenue):
  "Disorganization isn't a character flaw. It's a signal.
   LifeOS answers it."
```

---

## DIGITAL INFRASTRUCTURE — PLANNED, NOT YET BUILT

```
Website: Cloudflare Pages (free, unlimited bandwidth)
  echoes.marketing → deploy from GitHub repo
  Lead capture form → Supabase leads table

Database: Supabase (free forever, 500MB, no expiry)
  Project: echoes-marketing, region: US East
  Tables: leads, content_calendar, contacts, service_ledger
  Connects to: Cloudflare Pages frontend

Email: Cloudflare Email Routing + Gmail SMTP (free)
  hello@echoes.marketing → Jamie's Gmail
  signal@echoes.marketing → Jamie's Gmail
  clients@echoes.marketing → Jamie's Gmail
  Send-from via Gmail App Password

Google Sheets (immediate CRM and PM — no cost):
  EXPONERE/ECHOES/Echoes_CRM.gsheet
    Tabs: Contacts | Pipeline View | Touchpoint Log
  EXPONERE/EPOS/EPOS_PM.gsheet
    Tabs: Projects | Tasks | My Work Today |
          Sprint Board | Blocked Log
  EXPONERE/PGP/PGP_Jobs.gsheet
  EXPONERE/EPOS/EPOS_Revenue.gsheet
```

---

## TOMORROW MORNING — THE MISSION (04:00 – 08:00 AM)

### THE FOUR-HOUR BLOCK BREAKDOWN

```
04:00-04:05  HUMAN: Create Echoes Google account
04:05-04:50  COWORK: Cloudflare DNS + Email routing
04:50-05:15  COWORK: Supabase database + website live
05:15-05:35  HUMAN: YouTube channel + API key
05:35-06:05  COWORK: Affiliate applications
06:05-07:05  COWORK: Google Sheets CRM + PM build
07:05-07:45  COWORK: Social handles claimed
07:45-08:00  REVIEW: Gate check + milestone log
```

### PRIORITIZED CHECKLIST (18 tasks)

```
TIER 1 — BLOCKING (must complete first):
[ ] T1  Create Echoes Google account
[ ] T2  Cloudflare: transfer echoes.marketing DNS
[ ] T3  Email routing: hello/signal/clients@echoes.marketing
[ ] T4  Supabase: project + 4 tables provisioned

TIER 2 — LAUNCH CRITICAL:
[ ] T5  Cloudflare Pages: echoes.marketing website live
[ ] T6  YouTube: channel created, @EchoesMarketing claimed
[ ] T7  YouTube Data API v3 key → .env

TIER 3 — REVENUE ENABLING:
[ ] T8  Amazon Associates: application submitted
[ ] T9  LEGO Impact.com: application submitted

TIER 4 — DATA INFRASTRUCTURE:
[ ] T10 Google Drive: EXPONERE folder structure created
[ ] T11 Echoes_CRM.gsheet: 3 tabs, formatting, dropdowns
[ ] T12 EPOS_PM.gsheet: 5 tabs, formatting, dropdowns
[ ] T13 PGP Orlando seeded in CRM (TTLG: 49, Stage: Diagnostic)
[ ] T14 46 tasks exported from PostgreSQL → PM sheet

TIER 5 — SOCIAL HANDLES:
[ ] T15 LinkedIn: Echoes Marketing company page
[ ] T16 Instagram: @EchoesMarketing business account
[ ] T17 X: @EchoesMarketing
[ ] T18 Facebook: Echoes Marketing business page
```

### SUCCESS DEFINITION AT 8 AM
```
echoes.marketing: live and capturing leads
hello@echoes.marketing: sending and receiving
Supabase: database live, form submission working
YouTube: @EchoesMarketing claimed
Affiliates: 2 applications submitted
CRM: PGP Orlando as first contact
PM sheet: 46 tasks visible
Socials: 3-4 handles claimed
Doctor: 0 FAIL | Git: ZERO
```

---

## COWORK DIRECTIVES — READY TO PASTE

### DIRECTIVE 1: DNS AND EMAIL
```
"Create a Cloudflare account and add the domain echoes.marketing.
Transfer DNS from Namecheap by updating nameservers to Cloudflare
values. Enable Email Routing. Create three forwarding addresses:
hello@echoes.marketing, signal@echoes.marketing, and
clients@echoes.marketing — all forwarding to [Jamie's Gmail].
Verify the destination address when the confirmation email arrives.
Then configure Gmail to send from hello@echoes.marketing using
Gmail SMTP (smtp.gmail.com port 587) with an App Password.
Take a screenshot confirming email routing is enabled."
```

### DIRECTIVE 2: DATABASE AND WEBSITE
```
"Create a Supabase project named echoes-marketing in the US East
region on the free plan. In the SQL editor, create four tables:
leads (id uuid pk, name text, email text not null, source text,
segment text, lead_score int default 0, created_at timestamptz
default now()), content_calendar (id uuid pk, brief_id text,
title text not null, hook_type text, eri_predicted int,
eri_actual int, status text default 'draft', platform text,
publish_date date, url text, created_at timestamptz default now()),
contacts (id uuid pk, name text not null, email text, company text,
segment text, stage text default 'discovery', lead_score int
default 0, ttlg_score int, last_touchpoint date, notes text,
created_at timestamptz default now()), service_ledger (id uuid pk,
contact_id uuid references contacts(id), service_type text,
delivered_at timestamptz, outcome text, created_at timestamptz
default now()). Enable Row Level Security on all four tables.
Copy the project URL and anon key from Settings → API.

Then create a GitHub repo named echoes-marketing-site. Create a
single index.html file with a dark-mode landing page for Echoes
Marketing: background #0A1628, accent #00D4FF, gold #FFB84D.
Content: brand name Echoes Marketing, tagline We follow the signal,
three pillars Detect / Amplify / Distribute, email capture form
that submits to the Supabase leads table via fetch API, and
hello@echoes.marketing as contact. Mobile responsive. Load under
1 second. Include Open Graph meta tags.

Deploy to Cloudflare Pages connected to that GitHub repo.
Connect custom domain echoes.marketing.
Confirm the site loads at https://echoes.marketing.
Test the email capture form and confirm the lead appears
in the Supabase leads table."
```

### DIRECTIVE 3: GOOGLE SHEETS CRM
```
"In my Google Drive, create the folder structure:
EXPONERE/ECHOES/, EXPONERE/EPOS/, EXPONERE/PGP/,
EXPONERE/TTLG/, EXPONERE/LIFEOS/, EXPONERE/SHARED WITH STACEY/

Create a Google Sheet named Echoes_CRM in EXPONERE/ECHOES/.
Build three tabs:

Tab 1 named Contacts with columns:
A=ID (text, format ECH-001), B=Name, C=Email, D=Company,
E=Segment (dropdown: Creator/Local Business/Agency/SaaS/
Enterprise/Consumer), F=Stage (dropdown: Discovery/Engagement/
Nurture/Diagnostic/Offer/Delivery/Stewardship/Advocacy),
G=Lead Score (number), H=TTLG Score (number),
I=Source (dropdown: YouTube/Affiliate/Referral/Direct/PGP/Cold),
J=Last Touchpoint (date), K=Next Action (text),
L=Next Action Due (date), M=Tier (dropdown: L1/L2/L3/L4/L5/None),
N=Notes (text).
Freeze row 1 and column A. Header row background #00D4FF,
black bold text. Alternating rows #0A1628 and #0d1f3c.
Conditional formatting: Lead Score >= 85 = gold row background,
Lead Score 61-84 = light cyan, Next Action Due < today = red text.

Tab 2 named Pipeline View: sorted by Lead Score descending,
filtered to exclude Advocacy stage, frozen header.

Tab 3 named Touchpoint Log with columns:
A=Date, B=Contact ID, C=Contact Name, D=Type (dropdown:
Call/Email/Message/Meeting/Content), E=Notes, F=Outcome
(dropdown: Positive/Neutral/Negative/No Response),
G=Next Step, H=Logged By.

Add first contact row in Contacts tab:
ID=ECH-001, Name=PGP Property Solutions, Company=PGP Property
Solutions, Segment=Local Business, Stage=Diagnostic,
Lead Score=65, TTLG Score=49, Source=PGP, Tier=L2,
Notes=First TTLG diagnostic complete. 49/100 Developing.
Pressure washing and gutter services Orlando FL."
```

### DIRECTIVE 4: GOOGLE SHEETS PM
```
"Create a Google Sheet named EPOS_PM in EXPONERE/EPOS/ in
my Google Drive. Build five tabs:

Tab 1 named Projects with columns:
A=Project ID, B=Project Name, C=Node (dropdown: Echoes/TTLG/
PGP/FOTW/Reader/LifeOS/EPOS Core), D=Status (dropdown:
Backlog/Active/Blocked/Review/Closed/Archived),
E=Priority (dropdown: Critical/High/Medium/Low), F=Owner,
G=Start Date, H=Due Date, I=% Complete (number, data bar
green formatting), J=Blocked By, K=Notes.
Conditional formatting: Blocked = orange row, Critical = bold,
Closed = strikethrough gray.

Tab 2 named Tasks with columns:
A=Task ID, B=Project ID, C=Project Name (VLOOKUP from Projects),
D=Task Title, E=Status (dropdown: Backlog/Todo/In Progress/
Blocked/Review/Done/Cancelled), F=Priority (dropdown:
Critical/High/Medium/Low), G=Assignee, H=Due Date,
I=Completed Date, J=Sprint, K=Depends On, L=Notes.
Conditional formatting: Done = strikethrough gray,
Blocked = orange, Due Date < today and not Done = red.

Tab 3 named My Work Today:
Formula-filtered view of Tasks where Status is Todo or
In Progress or Blocked, and Due Date is within next 3 days.
Sorted by Priority then Due Date. Frozen header.
Label in A1: Last updated: [today's date]

Tab 4 named Sprint Board:
Groups tasks by Sprint column. Shows sprint name, total tasks,
done count, percentage complete with sparkline progress bars.

Tab 5 named Blocked Log:
All tasks where Status = Blocked. Columns: Task ID, Title,
Project, Blocked By, Blocked Since, Owner, Resolution Notes.

All tabs: header row #00D4FF black bold, alternating rows
#0A1628 and #0d1f3c, freeze row 1.

Share EXPONERE/SHARED WITH STACEY/ folder with editor access
for Stacey."
```

---

## THE BUILD CYCLE GOING FORWARD

```
INSPIRATION
  → Idea arrives (any time)
  → Voice memo OR one line in idea_log.txt
  → Do not act on it yet

RESEARCH (scheduled block)
  → NotebookLM hub-and-spoke research
  → 7 vectors: Product/Market/Technical/Implementation/
    Launch/Operations/Legal
  → GO / PIVOT / KILL gate before any build starts

PLANNING (this thread)
  → UI contracts and behavioral specs (not code)
  → Sprint checklist pre-filled through section A
  → Cowork directives written and ready
  → Definition of done stated before build starts

BUILD (CODE + Cowork — scheduled block)
  → Read existing files first
  → One task at a time
  → Verify before advancing
  → Fill checklist B1-B3 during execution

COMPOUND
  → AAR from filled checklist
  → Milestone logged to growth timeline
  → Next sprint inherits clean state
```

---

## ARCHITECTURAL CONSTANTS (never change without amendment)

```
All modules: function-based (complex integration layers
             like lifeos_sovereignty use classes — correct)
get_context_vault() not get_vault_path()
ConstitutionalViolation(rule, detail, component) — 3 args
Agent IDs: lowercase strings "ttlg" "bridge" "orchestrator"
LangGraph = canonical state machine for multi-step workflows
SOVEREIGN can_modify_constitution = human-in-the-loop interrupt
Python 3.11.9 — constitutionally mandated
All paths: WSL-native /mnt/c/Users/Jamie/...
No git add/commit/push during active sessions
Never hardcode credentials — always load via load_dotenv()
Dark mode everywhere: #0A1628 minimum
```

---

## KEY FILE PATHS

```
epos_mcp:          C:/Users/Jamie/workspace/epos_mcp
command_center:    C:/Users/Jamie/workspace/command_center
friday:            C:/Users/Jamie/workspace/friday

context_vault/lifeos/
  daily_log.jsonl, growth_timeline.jsonl,
  relationship_os.jsonl, kaizen_log.jsonl,
  service_ledger.jsonl, hard_things.jsonl,
  accountability_mirror.jsonl, reflections/

context_vault/steward_signals/queue.jsonl
context_vault/skills/index.json
context_vault/doctrine/FRIDAY_CONSTITUTIONAL_MANDATE_v2.md
context_vault/idea_log.txt  ← new, create if not exists
```

---

## PENDING HUMAN ACTIONS (gate items)

```
BLOCKING TOMORROW:
[ ] Create Echoes Google account (04:00 AM)
[ ] YouTube channel + @EchoesMarketing (05:15 AM)
[ ] YouTube Data API v3 key (05:25 AM)
[ ] Phone verifications for social accounts (07:05 AM)

DEFERRED (not tomorrow):
[ ] Canva E-mark logo (navy #0A1628, accent #00D4FF)
[ ] Rotate exposed API key from agent_router.py (December)
[ ] File provisional patent for CCP before Reader build
[ ] Windows 11 Pro upgrade ($99 — unlocks Cowork computer use)
[ ] Google Calendar events creation (Cowork reconnect)
```

---

## THE VISION IN ONE PARAGRAPH

EPOS is Stark Enterprises. Friday is chief of staff, executive
assistant, operations director, and Life Sherpa simultaneously.
The Command Center is the cockpit. LifeOS is the personal
sovereignty layer. Every node — Echoes, TTLG, FOTW, the Reader
— is independently viable and composable into the larger platform.
The organism breathes, learns from every outcome, and compounds.
The Steward sets direction, governs constitutional decisions,
and lives. Friday handles everything else.

Service is the core offering in life and business.
Credibility and sincerity can only be proven through
dedicated and authentic service.

---

## HOW TO START THE NEW THREAD

1. Paste this entire document as your first message
2. Add this statement:

"This is the complete context handoff for EPOS as of
2026-03-30. Tomorrow morning's 4-hour deep work block
(04:00-08:00 AM) is the Echoes Digital Infrastructure Sprint.
The prioritized checklist has 18 tasks across 5 tiers.
Four Cowork directives are written and ready to paste.
Four human gates require Jamie's direct action.

The operating principle going forward:
Inspiration → Idea Log → Research → Planning → Build → Compound.
No code in the planning thread. No new ideas during build blocks.
Every task verified before advancing.

Start by confirming doctor status and then walk through
the 04:00 AM human gate: creating the Echoes Google account.
After that, Cowork runs the infrastructure autonomously
while Jamie handles human-gate items as they arise."

---

*Context handoff created: 2026-03-30 end of session*
*Day 1 of the journey complete.*
*The system holds what you cannot hold alone.*
*Tomorrow the infrastructure goes live.*
