# FOTW CONSTITUTION
## The Law Governing the Fly on the Wall Node Family
### Sovereign Node Family — EXPONERE / EPOS Ecosystem
### Ratified: April 4, 2026
### Authority: Jamie Purdue, Sovereign Architect

---

## PREAMBLE: THE ORIGIN STORY

FOTW was born from a simple frustration: AI chat threads contain decisions, action items, strategic insights, and validated ideas — and they disappear when the tab closes.

Every working session with Claude, Gemini, Perplexity, ChatGPT, or NotebookLM produces intelligence. Strategies are debated. Architectures are designed. Pricing is modeled. Build paths are planned. And when the session ends, that intelligence lives only in the chat history — unstructured, unsearchable, and disconnected from the systems that should act on it.

The "Fly on the Wall" was the answer: what if the AI that participated in the conversation also captured, parsed, routed, and initiated the business processes that the conversation produced? Not as an afterthought. Not as manual note-taking. As an automatic, governed, constitutional pipeline that turns every conversation into structured action.

The name is literal. The AI is the fly on the wall of every working session. It hears everything. FOTW ensures nothing is lost and everything reaches the system that should act on it.

---

## ARTICLE I: MISSION

FOTW is a sovereign node family within the EPOS ecosystem. Its mission:

**Capture every expression of human intelligence — spoken, typed, browsed, or engaged with — and transform it into structured, routed, actionable data that initiates and furthers business processes.**

FOTW does not interpret prematurely. It does not act without governance. It captures first, parses second, routes third, validates fourth, and initiates fifth. Every layer has its own responsibility and its own constitutional boundary.

---

## ARTICLE II: THE FIVE-LAYER ARCHITECTURE

### Layer 1 — CAPTURE (Raw Data Acquisition)

**Purpose:** Acquire the raw conversational data from any source without modification, interpretation, or loss.

**Constitutional rule:** Layer 1 NEVER interprets. It stores the unmodified transcript with full attribution (who said what, when, in what context). Raw data is sacred. It is the evidence chain that everything downstream depends on.

**Storage:** `context_vault/fotw/raw/{source_type}/{session_id}.jsonl`

**Supported sources:**
- AI chat exports (Claude, ChatGPT, Gemini, Perplexity JSON exports)
- Messaging platforms (Slack threads, email chains, Discord, iMessage, WhatsApp)
- Meeting recordings (Zoom, Teams, phone calls — transcribed via ASR)
- Browser activity (open tabs, articles read, dashboards viewed)
- Content engagement (comments, replies, DMs across all platforms)
- Voice notes and dictation

**Output contract:**
```json
{
  "session_id": "unique identifier",
  "source_type": "chat_export | meeting | browser | engagement | voice",
  "captured_at": "ISO 8601 timestamp",
  "participants": ["speaker_1", "speaker_2"],
  "raw_messages": [
    {
      "index": 0,
      "speaker": "identified or anonymous",
      "timestamp": "if available",
      "content": "unmodified text",
      "metadata": {}
    }
  ],
  "capture_method": "api_export | browser_extension | audio_transcription | manual_upload",
  "fidelity_notes": "any known gaps in capture completeness"
}
```

### Layer 2 — PARSE (Context Resolution and Tagging)

**Purpose:** Apply CCP concentric ring analysis to the stored conversation. Identify every element type: decisions, action items, ideas, research questions, objections, financial signals, strategic insights.

**Constitutional rule:** Layer 2 NEVER modifies the raw data. It creates a parallel parsed structure that references the raw by index. If parsing confidence is below threshold, the element is flagged for human review rather than silently classified.

**Processing agent:** CCP Engine (concentric ring analysis) + Intent Classifier

**Element types identified:**
- `decision` — a choice was made, with who decided and what alternatives were discussed
- `action_item` — a task was assigned or implied, with owner if identifiable
- `idea` — a concept was proposed that could become a product, feature, or initiative
- `research_question` — an unknown was identified that needs investigation
- `objection` — a concern or pushback was raised
- `financial_signal` — pricing, budget, revenue, cost data was discussed
- `strategic_insight` — a pattern, positioning, or market observation was articulated
- `technical_decision` — an architecture, tool, or implementation choice was made
- `risk` — a failure mode, dependency, or blocker was identified
- `enthusiasm` — high-energy agreement or excitement was expressed (priority flag)

**Output contract:**
```json
{
  "session_id": "references Layer 1 session",
  "parsed_at": "ISO 8601",
  "parser_version": "CCP v0.1.0",
  "elements": [
    {
      "element_id": "unique",
      "type": "decision | action_item | idea | research_question | ...",
      "source_index": [12, 13, 14],
      "speaker": "who originated this",
      "content_summary": "parsed interpretation",
      "confidence": 0.92,
      "ccp_decisive_ring": "section",
      "downstream_routes": ["pm_surface", "idea_pipeline"]
    }
  ],
  "statistics": {
    "total_elements": 47,
    "by_type": {"decision": 5, "action_item": 12, "idea": 8},
    "avg_confidence": 0.87
  }
}
```

### Layer 3 — ROUTE (Distribution to Business Processes)

**Purpose:** Send each parsed element to the EPOS node that should act on it. Routing is deterministic — element type maps to destination. No LLM involved in routing decisions.

**Constitutional rule:** Layer 3 routes based on type, not content. The routing table is constitutional law. Adding a new route requires an amendment, not a code change.

**Routing table:**

| Element Type | Primary Destination | Secondary Destination | Event Published |
|-------------|--------------------|-----------------------|-----------------|
| `decision` | Context Vault (decision log) | PM surface (if project-linked) | `fotw.decision.logged` |
| `action_item` | PM surface (new task) | Friday (if owner = Jamie) | `fotw.action.created` |
| `idea` | Idea Pipeline (capture) | Friday (triage queue) | `fotw.idea.captured` |
| `research_question` | RS1 (brief generation) | CCP (vector routing) | `fotw.research.queued` |
| `objection` | Sales Brain (pattern library) | Context Vault | `fotw.objection.logged` |
| `financial_signal` | FIN_OPS (modeling) | Context Vault | `fotw.financial.detected` |
| `strategic_insight` | Context Vault (doctrine) | Content Lab (seed) | `fotw.insight.stored` |
| `technical_decision` | Context Vault (architecture) | Doctor (validation) | `fotw.technical.decided` |
| `risk` | Failure Scenarios (pre-mortem) | PM surface (blocker) | `fotw.risk.flagged` |
| `enthusiasm` | Content Lab (priority seed) | Lead Scoring (signal) | `fotw.enthusiasm.detected` |

### Layer 4 — VALIDATE (Idea Pipeline and Quality Gates)

**Purpose:** Ideas and research questions that enter the Idea Pipeline undergo the 7-Vector validation protocol. GO/PIVOT/KILL verdicts are produced. Only validated items proceed to build.

**Constitutional rule:** No idea enters the build queue without passing through the 7-Vector Protocol. This layer exists to prevent the pattern that FOTW was built to solve — acting on unvalidated inspiration instead of researched certainty.

**Process:**
1. Idea enters Idea Pipeline via Layer 3 routing
2. Friday triages daily at 17:30 (scored, classified, prioritized)
3. RS1 generates 7-vector research brief
4. CCP auto-routes brief to NotebookLM vector notebooks via Drive sync
5. Research completes across 7 vectors
6. GO/PIVOT/KILL verdict produced
7. If GO → Sprint checklist pre-filled from V4, enters build queue

### Layer 5 — INITIATE (Business Process Activation)

**Purpose:** Validated ideas and routed action items trigger the downstream business processes that bring them to life.

**Constitutional rule:** Layer 5 only acts on items that have passed through Layers 1-4. It never initiates from raw data. It never skips validation. The governance chain is unbroken.

**Initiated processes:**
- Sprint checklist generation (from V4 Implementation research)
- CODE directive creation (from validated technical decisions)
- Content Lab brief generation (from validated strategic insights)
- TTLG dimension updates (from validated market observations)
- Engagement manifest creation (from validated client-facing decisions)
- SOP updates (from validated process improvements)

---

## ARTICLE III: THE SIX EXPRESSIONS

FOTW is not one product. It is a family of sensors, each capturing from a different source but all feeding the same five-layer pipeline.

| Expression | Captures From | Primary Use Case | Standalone Price |
|-----------|--------------|-----------------|-----------------|
| **Thread Extractor** | AI chat exports (Claude, ChatGPT, Gemini, Perplexity) | Extract decisions, ideas, and action items from working sessions | $39-97/mo |
| **Conversation Recorder** | Live calls, meetings, discovery sessions | Real-time transcription + post-call AAR + CRM updates | $97-297/mo |
| **Chat Transmuter** | Slack, email, Discord, messaging platforms | Turn async conversations into structured deliverables | $39-97/mo |
| **Content Comment Listener** | LinkedIn, X, YouTube, IG, blog comments | Engagement intelligence for Echolocation + community formation | $49-149/mo |
| **Browser Watcher** | Open tabs, articles, dashboards, research | Passive knowledge base from daily browsing (becomes Reader) | Free-$9.99/mo |
| **Real-Time Sales Guide (GRAG)** | Live interaction in progress (voice + screen + chat) | In-call coaching, objection handling, sentiment alerts | +$149/mo add-on |

Each expression passes the Node Sovereignty tests independently. Each can be sold standalone. Each produces more value when combined with others — because the Context Vault accumulates intelligence from all sources, making every subsequent interaction smarter.

---

## ARTICLE IV: SOVEREIGNTY CONTRACT

**Standalone Operation:** Each FOTW expression can operate without EPOS. The Thread Extractor, for example, exports chat threads and produces parsed elements without requiring TTLG, Friday, or any other node.

**Universal Contract:** All expressions share the same five-layer pipeline. Raw data in, parsed elements out. The pipeline is the protocol; the expressions are the sensors.

**Independent Monetization:** Each expression has its own pricing tier, its own value proposition, and its own target market. They are sovereign businesses that happen to share infrastructure.

**Data Sovereignty:** All captured data stays on the client's hardware. Nothing is uploaded to external servers. The client controls what is captured and can exclude sensitive topics at any time through approval gates.

**Event Bus Integration:** Every FOTW action publishes to the EPOS Event Bus. External consumers (TTLG, Content Lab, Lead Scoring, etc.) subscribe to FOTW events without coupling to FOTW internals.

---

## ARTICLE V: CONSTITUTIONAL BOUNDARIES

1. **FOTW never acts without capture.** No business process is initiated from inference or assumption. Every action traces back to a specific captured conversation element.

2. **FOTW never modifies raw data.** Layer 1 output is immutable. Parsed data in Layer 2 references the raw by index but never changes it.

3. **FOTW never skips validation for ideas.** Ideas route to the Idea Pipeline. The 7-Vector Protocol determines their fate. FOTW does not have authority to approve builds.

4. **FOTW never captures without consent.** Call recording, browser monitoring, and any always-on mode requires explicit opt-in. The default state is off.

5. **FOTW never routes without constitutional authority.** The routing table in Layer 3 is law. New routes require formal amendment.

---

## ARTICLE VI: INTEGRATION WITH EPOS

FOTW is the sensory organ of the EPOS nervous system. It provides the raw intelligence that every other node processes:

- **CCP** receives conversation data for context disambiguation
- **TTLG** receives diagnostic calibration data from real client interactions
- **Content Lab** receives engagement signals and content seeds
- **Lead Scoring** receives behavioral signals from engagement patterns
- **Sales Brain** receives objection patterns and successful closing techniques
- **Context Vault** receives institutional memory from every captured session
- **Friday** receives triaged ideas and action items for orchestration
- **RS1** receives research questions for 7-vector brief generation
- **Event Bus** receives every FOTW action as a published event

Without FOTW, these nodes operate on manually entered data. With FOTW, they operate on automatically captured, parsed, and routed intelligence from every conversation the business has.

---

## SIGNATURES

**Sovereign Architect:** Jamie Purdue
**Date:** April 4, 2026
**Status:** Constitutional — ratified

> *"The AI is in the room. FOTW makes sure nothing it heard is ever lost."*

---
*FOTW Constitution v1.0 — EXPONERE / EPOS Autonomous Operating System*
