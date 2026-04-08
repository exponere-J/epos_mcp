# EPOS — Tomorrow Morning Build Plan
## 04:00 – 08:00 AM | March 31, 2026
**Sprint ID**: SPRINT-20260331-INFRASTRUCTURE-LAUNCH
**Operator**: Jamie Purdue — Sovereign Architect
**Mission**: From domain-only to operational digital infrastructure

---

## THE OPERATING PRINCIPLE FOR TOMORROW

Every block has one purpose.
Every task has one owner.
Every build starts with a read.
Every completion has a verification.

**Inspiration goes to the idea log. Research goes to NotebookLM.
Planning goes here. Build happens in CODE and Cowork.
Nothing bleeds across boundaries.**

---

## PRIORITIZED CHECKLIST — COMPLETE TASK INVENTORY

### TIER 1 — BLOCKING (must complete before anything else works)

```
[ ] 1.  Google account created for Echoes brand
        Why blocking: YouTube, Gmail, Drive, Analytics all depend on this
        Owner: Jamie (human action — 5 minutes)
        When: 04:00 AM — first thing, before opening anything else

[ ] 2.  Cloudflare account created, echoes.marketing DNS transferred
        Why blocking: email routing, website hosting, SSL all depend on this
        Owner: Cowork
        When: 04:05 AM

[ ] 3.  hello@echoes.marketing email routing verified (receive + send)
        Why blocking: affiliate applications require a business email
        Owner: Cowork + Jamie (Gmail app password setup)
        When: 04:20 AM

[ ] 4.  Supabase project created, core tables provisioned
        Why blocking: website lead capture form needs the database
        Owner: Cowork
        When: 04:35 AM
```

### TIER 2 — LAUNCH CRITICAL (needed before public presence)

```
[ ] 5.  echoes.marketing website live on Cloudflare Pages
        Why critical: Amazon Associates requires live website for approval
        Owner: Cowork
        When: 04:50 AM

[ ] 6.  YouTube channel created, @EchoesMarketing claimed
        Why critical: content pilot cannot start without the channel
        Owner: Jamie (human action — phone verification required)
        When: 05:15 AM

[ ] 7.  YouTube Data API v3 enabled, key added to .env
        Why critical: MA1 niche scanner is gated on this key
        Owner: Jamie → CODE adds to .env
        When: 05:25 AM
```

### TIER 3 — REVENUE ENABLING (affiliate and monetization)

```
[ ] 8.  Amazon Associates application submitted
        Why: LEGO affiliate links need this before content goes live
        Dependency: Task 5 (live website) must be complete
        Owner: Cowork
        When: 05:35 AM

[ ] 9.  LEGO affiliate via Impact.com application submitted
        Why: binding pilot revenue depends on this approval
        Dependency: Task 5 (live website) must be complete
        Owner: Cowork
        When: 05:50 AM
```

### TIER 4 — DATA INFRASTRUCTURE (sheets and CRM)

```
[ ] 10. Google Drive folder structure created
        EXPONERE/ECHOES/, EXPONERE/EPOS/, EXPONERE/PGP/,
        EXPONERE/TTLG/, EXPONERE/LIFEOS/, EXPONERE/SHARED WITH STACEY/
        Owner: Cowork
        When: 06:05 AM

[ ] 11. Echoes_CRM.gsheet created with all tabs and formatting
        Tabs: Contacts | Pipeline View | Touchpoint Log
        Owner: Cowork
        When: 06:15 AM

[ ] 12. EPOS_PM.gsheet created with all tabs and formatting
        Tabs: Projects | Tasks | My Work Today |
              Sprint Board | Blocked Log
        Owner: Cowork
        When: 06:35 AM

[ ] 13. PGP Orlando seeded into CRM as first contact
        Stage: Diagnostic | TTLG Score: 49 | Tier: L2
        Owner: Cowork
        When: 06:50 AM

[ ] 14. Existing 46 tasks seeded into EPOS_PM Tasks tab
        Source: epos.tasks PostgreSQL table
        Export via: docker exec epos_db psql query → CSV → Sheet
        Owner: CODE then Cowork
        When: 06:55 AM
```

### TIER 5 — SOCIAL HANDLES (claim before someone else does)

```
[ ] 15. LinkedIn company page: Echoes Marketing
        Owner: Cowork
        When: 07:10 AM

[ ] 16. Instagram business: @EchoesMarketing
        Owner: Cowork
        When: 07:20 AM

[ ] 17. X (Twitter): @EchoesMarketing
        Owner: Cowork
        When: 07:30 AM

[ ] 18. Facebook Business Page: Echoes Marketing
        Owner: Cowork
        When: 07:40 AM
```

### TIER 6 — IF TIME PERMITS BEFORE 8 AM

```
[ ] 19. Command Center: WebSocket fix verified
        Run: ./start_command_center.sh → confirm no WS error
        Owner: CODE

[ ] 20. Command Center: Projects page loads live DB data
        Verify: /projects shows 10+ projects

[ ] 21. Content Calendar seeded: CB-LEGO-001 through 020
        Copy from context_vault/missions/lego_affiliate/
        into Echoes_CRM content tab
```

---

## THE SCHEDULE — BLOCK BY BLOCK

```
04:00 – 04:05  HUMAN GATE
               Jamie creates Google account for Echoes
               Username suggestion: echoes.mktg@gmail.com
               Save credentials immediately to password manager

04:05 – 04:50  COWORK SESSION 1 — DNS AND EMAIL
               Hand Cowork the Phase 1 directive
               Walk away — it runs autonomously
               Jamie touchpoint: Gmail app password setup
               GATE: test email sent and received

04:50 – 05:15  COWORK SESSION 2 — DATABASE AND WEBSITE
               Hand Cowork the Phase 2+3 directive
               Walk away — it runs autonomously
               Jamie touchpoint: none
               GATE: echoes.marketing loads in browser
                     test form submission appears in Supabase

05:15 – 05:35  HUMAN GATE
               Jamie creates YouTube channel
               Claims @EchoesMarketing
               Enables YouTube Data API v3 in Google Console
               Copies API key

05:35 – 06:05  COWORK SESSION 3 — AFFILIATE APPLICATIONS
               Amazon Associates + LEGO Impact.com
               Jamie touchpoint: tax info if required
               GATE: confirmation emails received

06:05 – 07:05  COWORK SESSION 4 — SHEETS INFRASTRUCTURE
               Drive folders + CRM + PM sheets
               Export tasks from PostgreSQL via CODE first
               Cowork builds sheets, seeds data
               GATE: both sheets open, data visible, formatting applied

07:05 – 07:45  COWORK SESSION 5 — SOCIAL HANDLES
               LinkedIn + Instagram + X + Facebook
               Jamie touchpoint: phone verification per platform
               GATE: screenshot of each claimed handle

07:45 – 08:00  MORNING REVIEW
               Review all gates — mark checklist
               Note anything that needs follow-up
               Log milestone: JOURNEY_START for Echoes infrastructure
               python epos.py lifeos milestone JOURNEY_START \
                 "Echoes Marketing digital infrastructure live"

08:00          DEEP WORK BLOCK CLOSES
               Hand off any incomplete items to next sprint
               Start EPOS Build Sprint at 09:00
```

---

## THE RULES FOR TOMORROW MORNING

```
1. No new ideas during the build block.
   If an idea comes: voice memo or quick note to idea_log.txt
   It gets evaluated in the next planning session, not now.

2. No scope creep.
   If Cowork surfaces something interesting but unplanned:
   log it as DEFERRED, do not pursue it during this block.

3. Human gates are the only interruptions.
   When Cowork is running: close the laptop, do something else,
   or run the next CODE task in parallel. Do not hover.

4. Every gate must pass before the next phase starts.
   If a gate fails: diagnose, fix, re-verify. Do not skip ahead.

5. 08:00 is a hard stop.
   Incomplete items become the first tasks in the 09:00 sprint.
   The calendar block boundary is the discipline.
```

---

## WHAT SUCCESS LOOKS LIKE AT 8 AM

```
echoes.marketing: LIVE with email capture
hello@echoes.marketing: SENDING and RECEIVING
Supabase: DATABASE provisioned, leads table working
YouTube: @EchoesMarketing CLAIMED
Amazon Associates: APPLICATION submitted
LEGO Impact.com: APPLICATION submitted
Echoes_CRM.gsheet: LIVE in Google Drive
EPOS_PM.gsheet: LIVE with 46 tasks seeded
Social handles: 3-4 of 4 CLAIMED

Doctor: 0 FAIL
Git: ZERO operations
```

If all 18 tasks complete before 8 AM — you have built the
complete operational foundation for Echoes Marketing in one
4-hour deep work block. That is the compounding in action.

---

## WHAT CONTINUES AT 9 AM (EPOS BUILD SPRINT)

```
[ ] Command Center: WebSocket fix + Projects live data
[ ] Command Center: Pipeline CRM data
[ ] Wire Supabase to Echoes website lead form
[ ] YouTube API key → unlock MA1 competitor scan
[ ] Content Calendar Sheet → seed CB-LEGO-001 through 020
[ ] Content production loop: verify R1→AN1→A1→M1 chain
```

---

## IDEA LOG PROTOCOL

When inspiration strikes during a build block:

```
# Quick capture — do not stop what you are doing
echo "[IDEA] $(date): [your idea in one sentence]" >> \
  /mnt/c/Users/Jamie/workspace/epos_mcp/context_vault/idea_log.txt

# Review idea_log.txt every Sunday during weekly life review
# Good ideas become research briefs
# Research briefs become sprint items
# Sprint items become builds
```

This is the cycle:
INSPIRATION → IDEA LOG → RESEARCH → PLANNING → BUILD → COMPOUND

---

*Build plan created: 2026-03-30 end of session*
*Sprint starts: 2026-03-31 04:00 AM*
*All directives ready — see context handoff document*
