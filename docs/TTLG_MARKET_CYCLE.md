# TTLG Market Cycle — Market Sentiment → Validation → Creation + Promotion
<!-- File: C:\Users\Jamie\workspace\epos\TTLG_MARKET_CYCLE.md -->

**Document authority:** EPOS Constitution v3.1 · TTLG Model & Routing Charter v1.0  
**Cycle designation:** Cycle B  
**Steward:** Jamie  
**Audience:** Claude Code, Friday (Gemini), human operators — written assuming zero AI engineering background

---

## What This Cycle Does

Cycle B listens to what the market is actually saying — in forums, social platforms, reviews, and communities — then turns that signal into validated product and service concepts. Nothing is invented. Every concept traces back to real pain. Every concept is tested against the real market before resources are committed to building it.

The cycle runs on the same constitutional infrastructure as Cycle A. The Governance Gate is shared. The Context Vault is shared. Friday (Gemini) reads both cycles simultaneously and surfaces connections between them.

---

## When Cycle B Runs

- Entering a new market domain or vertical
- Validating whether a planned EPOS service has real demand
- Weekly or monthly echolocation pulse for an active domain
- Friday detects a market signal pattern that aligns with a Cycle A system weakness
- Jamie wants to validate a product concept before building it

---

## How Cycle B Connects to Cycle A

Friday specifically watches for:
- A market pain in `Market_Map.json` that matches a known pattern in `vault/patterns/` from Cycle A history → surfaces the internal-external alignment to Jamie
- A validated concept in `Validation_Report.json` that aligns with a Cycle A Verification Report showing a fixed capability → "We built it internally; the market wants it externally"

This cross-cycle correlation is Friday's highest-value function and cannot be replicated by any single-cycle view.

---

## Cycle B — Phase-by-Phase Specification

### Phase 1: Market Scout — Listen

**What this phase IS:**  
Raw signal collection and clustering. Market Scout ingests the collected posts, comments, reviews, and forum threads you provide and organizes them into themes — what people talk about, what they complain about, and what they wish existed.

**What this phase IS NOT:**  
Market Scout does not interpret strategic fit. Market Scout does not suggest products or offers. It maps the raw signal. All interpretation belongs to Market Thinker.

**Model:** `TTLG_SCOUT_B` (default: `zhipu-ai/glm-4.5-air:free`)

**Before this phase runs — data collection is manual:**  
You or a collection agent must gather the raw signal before Scout runs. Sources may include:
- Reddit threads in relevant subreddits
- LinkedIn comments and posts in target communities
- X (Twitter) conversations and replies
- Discord or Slack community discussions
- Product reviews on G2, Capterra, or App Store
- Forum threads on Hacker News, Indie Hackers, or niche communities

Collected data is saved as plaintext or JSON to: `vault/runs/{run_id}/raw_market_data.txt`

**System prompt for Market Scout:**
```
You are a listener and categorizer. You have been given a collection of social posts, forum comments, and product reviews from a defined domain and persona set. Read everything. Group what you find into three categories: (1) Themes — what topics come up repeatedly, (2) Pains — specific complaints, frustrations, or failures people describe, (3) Wishes — explicit or implied desires for something that doesn't exist yet or isn't done well. For each item in every category, quote at least one real example from the input. Do not suggest solutions. Do not rank by opportunity. Output only what the data says.
```

**Output artifact:** `Market_Map.json`  
**Output location:** `vault/runs/{run_id}/Market_Map.json`

**Market_Map.json schema:**
```json
{
  "run_id": "string",
  "cycle": "B",
  "phase": 1,
  "domain": "string — e.g., 'agentic AI for agencies'",
  "personas_targeted": ["list of persona descriptions"],
  "sources_ingested": "integer — number of posts/threads read",
  "collected_at": "ISO 8601 timestamp",
  "themes": [
    {
      "theme_id": "string — THM-{sequence}",
      "name": "string",
      "frequency": "integer — how many times this theme appeared",
      "example_quote": "string — verbatim example from the data"
    }
  ],
  "pains": [
    {
      "pain_id": "string — PAIN-{sequence}",
      "description": "string — what people are complaining about",
      "frequency": "integer",
      "intensity": "High | Medium | Low — based on language and repetition",
      "example_quote": "string — verbatim example"
    }
  ],
  "wishes": [
    {
      "wish_id": "string — WISH-{sequence}",
      "description": "string — what people want that doesn't exist or isn't good enough",
      "frequency": "integer",
      "example_quote": "string — verbatim example"
    }
  ]
}
```

**Phase 1 complete when:**
- `Market_Map.json` exists and is valid JSON
- At least 3 pains and 2 wishes are present
- Every entry has an `example_quote` from the actual collected data

---

### Phase 2: Market Thinker — Gap Analysis

**What this phase IS:**  
Strategic interpretation of the Market Map. Market Thinker compares what people want against what currently exists and against EPOS's strategic constraints to identify genuine gaps where a sovereign, local-first, or autonomy-focused solution could win.

**What this phase IS NOT:**  
Market Thinker does not design products or write copy. It identifies and ranks gaps. Concept Surgeon designs the offers.

**Model:** `TTLG_THINKER_B` (fixed: `deepseek/deepseek-r1:free` — cannot be changed by PRIORITY_MODE)

**Inputs required before phase starts:**
- `Market_Map.json` (Phase 1 output)
- Strategic constraints document (EPOS brand position, sovereignty principles, local-first mandate)
- Prior `Market_Playbook_*.json` files from previous Cycle B runs (if any)

**System prompt for Market Thinker:**
```
You are a gap analyst. You have a map of what the market is saying — themes, pains, and wishes. Your job is to identify gaps: places where existing tools fail, where no good solution exists, or where the market has a pain that aligns with a sovereign, local-first approach. For each gap you find, confirm that it is supported by at least two examples from the Market Map. Rank gaps by: size of pain (how many people, how intense), alignment with sovereign/local-first positioning, and absence of strong existing competition. Output a ranked list of gaps with evidence. Do not propose products yet.
```

**Output artifact:** `Gap_Opportunity_Map.json`  
**Output location:** `vault/runs/{run_id}/Gap_Opportunity_Map.json`

**Gap_Opportunity_Map.json schema:**
```json
{
  "run_id": "string",
  "cycle": "B",
  "phase": 2,
  "created_at": "ISO 8601 timestamp",
  "gap_count": "integer",
  "gaps": [
    {
      "gap_id": "string — GAP-{run_id}-{sequence}",
      "title": "string — short descriptive name",
      "description": "string — what gap exists and why it matters",
      "pain_sources": ["list of pain_id values from Market_Map that support this gap"],
      "wish_sources": ["list of wish_id values from Market_Map that support this gap"],
      "current_solutions": "string — what exists today and why it falls short",
      "sovereign_fit": "string — why a local-first, sovereign approach wins here",
      "opportunity_size": "High | Medium | Low",
      "competition_density": "High | Medium | Low | None",
      "rank": "integer — 1 = highest priority"
    }
  ]
}
```

**Phase 2 complete when:**
- `Gap_Opportunity_Map.json` exists and is valid JSON
- Every gap has at least 2 supporting `pain_sources` or `wish_sources` from the Market_Map
- No gap appears that cannot be traced to the Market_Map data

---

### Phase 3: Governance Gate — Concept Greenlight

**What this phase IS:**  
Human sovereignty. Jamie reviews the Gap_Opportunity_Map and selects which gaps to pursue with product or service concepts. Gaps not selected are deferred or rejected — the Concept Surgeon only works on approved gaps.

**What this phase IS NOT:**  
This gate cannot be automated or bypassed. If Jamie approves zero gaps, the cycle halts cleanly. That is a valid outcome.

**Model:** None — human decision only. Same shared Governance Gate infrastructure as Cycle A.

**Output artifact:** `Approved_Gap_List.json`  
**Output location:** `vault/runs/{run_id}/Approved_Gap_List.json`

**Approved_Gap_List.json schema:**
```json
{
  "run_id": "string",
  "cycle": "B",
  "phase": 3,
  "reviewed_at": "ISO 8601 timestamp",
  "approved_by": "human_steward",
  "approved_count": "integer",
  "rejected_count": "integer",
  "deferred_count": "integer",
  "gaps": [
    {
      "gap_id": "string",
      "title": "string",
      "status": "approved | rejected | deferred",
      "steward_note": "string or null"
    }
  ]
}
```

**Clean halt condition:**  
If `approved_count` is 0, write `GOVERNANCE_SKIP_{run_id}.json` to `vault/failures/`. Phases 4, 5, and 6 do not run. Friday logs the event. Not a failure.

---

### Phase 4: Concept Surgeon — Offer Design

**What this phase IS:**  
Concept and message design for each approved gap. Concept Surgeon turns gaps into product/service concepts and drafts 3–5 message variants per concept for real channels — LinkedIn, X, email, and direct message.

**What this phase IS NOT:**  
Concept Surgeon does not publish anything. It produces drafts. Every concept requires explicit Governance Gate approval and Jamie's review before any external publishing occurs. Concept Surgeon does not invent gaps — every concept must cite its source pain in the Gap Map.

**Model:** `TTLG_SURGEON_B` (default: `zhipu-ai/glm-4.5-air:free`)

**Inputs required before phase starts:**
- `Approved_Gap_List.json` (Phase 3 output) — `approved_count` must be > 0
- `Gap_Opportunity_Map.json` (for context on each approved gap)
- `Market_Map.json` (for verbatim pain language to use in messaging)

**System prompt for Concept Surgeon:**
```
You are an offer designer. For each approved gap, you will create: (1) a product or service concept — who it serves, what specific problem it solves, and what their life looks like after using it; (2) three to five message variants for LinkedIn, X, email, and direct message, each leading with a different angle on the same pain. Every concept must explicitly cite which pain or wish from the Market Map it addresses. Use the verbatim language from the market data — do not polish or sanitize it. Authenticity outperforms perfection. Do not publish. Draft only.
```

**Output artifact:** `Solution_Concepts.json`  
**Output location:** `vault/runs/{run_id}/Solution_Concepts.json`

**Solution_Concepts.json schema:**
```json
{
  "run_id": "string",
  "cycle": "B",
  "phase": 4,
  "created_at": "ISO 8601 timestamp",
  "concept_count": "integer",
  "concepts": [
    {
      "concept_id": "string — CON-{run_id}-{sequence}",
      "gap_id": "string — which approved gap this concept addresses",
      "name": "string — short product/service name",
      "who_it_serves": "string — persona description",
      "problem_solved": "string — specific pain addressed",
      "outcome": "string — what their situation looks like after",
      "pain_sources_cited": ["list of pain_id values from Market_Map"],
      "message_variants": [
        {
          "channel": "LinkedIn | X | Email | DM",
          "angle": "string — what aspect of the pain this message leads with",
          "subject_or_hook": "string — opening line or subject",
          "body": "string — full message text"
        }
      ]
    }
  ]
}
```

**Phase 4 complete when:**
- `Solution_Concepts.json` exists and is valid JSON
- Every approved gap has at least one concept
- Every concept has at least 3 message variants
- Every concept cites at least 2 `pain_sources_cited` from the Market_Map

---

### Phase 5: Echolocation Analyst — Market Validation

**What this phase IS:**  
Real-world validation. After message variants from Phase 4 are reviewed by Jamie and published to actual channels, Echolocation Analyst reads the engagement response and classifies which concepts and messages resonated with the market and which did not.

**What this phase IS NOT:**  
Analyst does not publish messages — Jamie does, after reviewing Phase 4 output. Analyst does not recommend what to build — that is Market Legacy's domain. Analyst classifies engagement evidence only.

**Model:** `TTLG_ANALYST_B` (default: `openrouter/free`)

**Publication step — manual, between Phase 4 and Phase 5:**  
Jamie reviews `Solution_Concepts.json`, selects message variants to publish, posts them to LinkedIn, X, email, or DM, and collects the engagement data. Engagement data is saved as plaintext to: `vault/runs/{run_id}/raw_engagement_data.txt`

Engagement data to collect:
- Likes, saves, reposts, and comments per post
- Direct messages received referencing the concept
- Email replies
- Any explicit "please build this" or "I need this" signals
- Any "not relevant" or no-reaction signals

**System prompt for Echolocation Analyst:**
```
You are a validation classifier. You have received engagement data from published market messages. For each concept and message variant, classify the response as: Resonated (saves, DMs, explicit interest, "please build this"), Tepid (passive likes only, no substantive engagement), or Silent (no measurable reaction). For every Resonated classification, cite the specific evidence. Do not mark anything as Resonated without specific supporting evidence. Do not recommend what to build.
```

**Output artifact:** `Validation_Report.json`  
**Output location:** `vault/runs/{run_id}/Validation_Report.json`

**Validation_Report.json schema:**
```json
{
  "run_id": "string",
  "cycle": "B",
  "phase": 5,
  "validated_at": "ISO 8601 timestamp",
  "resonated_count": "integer",
  "tepid_count": "integer",
  "silent_count": "integer",
  "results": [
    {
      "concept_id": "string",
      "message_variant_channel": "string",
      "classification": "Resonated | Tepid | Silent",
      "evidence": "string — specific engagement signals that support this classification",
      "notable_responses": ["list of verbatim responses or paraphrased DMs"]
    }
  ]
}
```

**Phase 5 complete when:**
- `Validation_Report.json` exists and is valid JSON
- Every concept and message variant from Phase 4 has a corresponding result
- No `Resonated` classification exists without a populated `evidence` field

---

### Phase 6: Market Legacy — Playbooks and Decisions

**What this phase IS:**  
The decision and memory phase. Market Legacy synthesizes the entire cycle — what was found, what was tested, what resonated — into two outputs: an explicit productization decision for each concept (build now / refine / shelve) and a reusable playbook entry capturing what play worked for which persona in which channel.

**What this phase IS NOT:**  
Market Legacy does not design products or write new messages. It captures what happened and extracts the transferable learning.

**Model:** `TTLG_LEGACY_B` (fixed: `deepseek/deepseek-r1:free` — cannot be changed by PRIORITY_MODE)

**Inputs required before phase starts:**
- `Market_Map.json`
- `Gap_Opportunity_Map.json`
- `Approved_Gap_List.json`
- `Solution_Concepts.json`
- `Validation_Report.json`

**System prompt for Market Legacy:**
```
You are a decision maker and playbook writer. You have a complete record of a market intelligence cycle: what the market said, which gaps were approved for exploration, what concepts and messages were created, and how the market responded. For each concept, make an explicit decision: Build Now (strong resonance, clear demand), Refine and Retest (mixed signals, concept needs repositioning), or Shelve (no resonance, low-priority gap). Then extract at least one playbook entry: a specific, reusable description of what play worked for which persona in which channel and why. The playbook entry must be specific enough to replicate in a future cycle or with a different client.
```

**Output artifacts:**
- `Productization_Decision.json` → `vault/runs/{run_id}/Productization_Decision.json`
- `Market_Playbook_{run_id}.json` → `vault/patterns/Market_Playbook_{run_id}.json`

**Productization_Decision.json schema:**
```json
{
  "run_id": "string",
  "cycle": "B",
  "phase": 6,
  "created_at": "ISO 8601 timestamp",
  "decisions": [
    {
      "concept_id": "string",
      "name": "string",
      "decision": "Build Now | Refine and Retest | Shelve",
      "rationale": "string — specific evidence from Validation_Report supporting this decision",
      "next_action": "string — what happens next for this concept"
    }
  ]
}
```

**Market_Playbook_{run_id}.json schema:**
```json
{
  "playbook_id": "string — PLAY-{YYYYMMDD}-{sequence}",
  "created_from_run": "string — run_id",
  "domain": "string",
  "persona": "string — who this play works for",
  "channel": "string — where this play was deployed",
  "angle": "string — what pain angle led the message",
  "play_description": "string — what was done and how",
  "result": "string — what resonance was observed",
  "replication_instructions": "string — how to run this same play in a new context",
  "avoid": "string — what did not work and should be skipped next time"
}
```

**Phase 6 complete when:**
- `Productization_Decision.json` exists with a decision for every concept from Phase 4
- `Market_Playbook_{run_id}.json` exists in `vault/patterns/` with at least one entry
- Every `Build Now` decision has specific resonance evidence cited

---

## Cycle B Completion — What "Done" Means

A Cycle B run is complete when all of the following exist in `vault/runs/{run_id}/`:

```
raw_market_data.txt          ✅ Pre-Phase 1 (manual collection)
Market_Map.json              ✅ Phase 1
Gap_Opportunity_Map.json     ✅ Phase 2
Approved_Gap_List.json       ✅ Phase 3
Solution_Concepts.json       ✅ Phase 4
raw_engagement_data.txt      ✅ Pre-Phase 5 (manual publishing + collection)
Validation_Report.json       ✅ Phase 5
Productization_Decision.json ✅ Phase 6
vault/patterns/Market_Playbook_{run_id}.json ✅ Phase 6
run.log                      ✅ Full structured log
```

---

## Iteration — How Each Cycle B Run Improves the Next

After every completed Cycle B run:
1. `Market_Playbook_{run_id}.json` is added to `vault/patterns/`
2. On the next Cycle B run, Market Thinker receives all accumulated playbooks
3. Market Thinker uses playbooks to identify gaps faster and rank them with higher confidence
4. Concept Surgeon uses prior playbooks to lead with proven angles instead of starting from zero
5. Friday reads accumulated playbooks across domains and surfaces cross-domain pattern opportunities

---

*Last updated: 2026-03-01 · Authority: TTLG Model & Routing Charter v1.0*
