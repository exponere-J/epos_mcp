# FOTW THREAD EXTRACTOR — BUILD SPECIFICATION
## The Original Product: Extract Intelligence from AI Chat Threads
### CODE DIRECTIVE — Bounded Build Missions
### Date: April 4, 2026
### Authority: Jamie Purdue, Sovereign Architect

---

## WHAT THIS IS

The Thread Extractor is the original FOTW expression — the product that started the entire FOTW vision. It captures AI chat thread exports (Claude, ChatGPT, Gemini, Perplexity), stores the raw data in the Context Vault, parses it through CCP for element identification, routes parsed elements to the correct EPOS business processes, and initiates validation and idea pipelines.

We already have CCP (the parser — Layer 2). What we need to complete the stack:

- **Layer 1:** Chat export ingestion and raw storage (the extraction leg)
- **Layer 3:** Deterministic routing from parsed elements to EPOS nodes (the routing leg)
- **Layer 5:** Business process initiation from validated elements (the publishing leg)

Layer 4 (validation via Idea Pipeline) already exists — ideas route to Friday triage and RS1 research briefs.

---

## THE THREE MISSIONS

### MISSION 1: THE EXTRACTION LEG (Layer 1)

**File:** `C:\Users\Jamie\workspace\fotw\thread_extractor.py`

**Purpose:** Ingest AI chat exports in any supported format, normalize them to the FOTW raw capture contract, and store in the Context Vault.

**Supported input formats:**

1. **Claude chat export** — JSON from claude.ai conversation export
   - Structure: array of messages with role (human/assistant), content, timestamp
   - Parser must handle: text content, tool use blocks, artifact references

2. **ChatGPT export** — JSON from OpenAI data export
   - Structure: conversations array with mapping of message nodes
   - Parser must handle: branching conversations, system prompts, plugin calls

3. **Gemini export** — JSON or markdown from Google AI Studio
   - Structure: varies by export method
   - Parser must handle: multi-turn, grounding citations

4. **Perplexity export** — markdown with citations
   - Structure: question/answer pairs with source citations
   - Parser must handle: inline citations, follow-up questions

5. **Plain text / markdown** — any unstructured conversation dump
   - Structure: speaker-prefixed lines or unmarked paragraphs
   - Parser must handle: heuristic speaker detection, approximate turn boundaries

6. **Slack thread export** — JSON from Slack API or export
   - Structure: messages array with user, text, timestamp, thread_ts
   - Parser must handle: threaded replies, reactions, file attachments (metadata only)

**Normalization contract (output of Layer 1):**

Every input format normalizes to this structure:
```json
{
  "session_id": "fotw-{timestamp}-{hash}",
  "source_type": "claude | chatgpt | gemini | perplexity | plaintext | slack",
  "source_file": "original filename",
  "captured_at": "ISO 8601",
  "participants": [
    {"id": "speaker_1", "role": "human | assistant | system", "name": "if known"}
  ],
  "messages": [
    {
      "index": 0,
      "speaker_id": "speaker_1",
      "role": "human",
      "timestamp": "if available, null otherwise",
      "content": "the message text",
      "content_type": "text | code | tool_use | artifact",
      "metadata": {}
    }
  ],
  "total_messages": 47,
  "total_words": 12500,
  "capture_fidelity": {
    "timestamps_available": true,
    "speakers_identified": true,
    "content_complete": true,
    "known_gaps": []
  }
}
```

**Storage locations:**
- Raw capture: `context_vault/fotw/raw/threads/{session_id}.json`
- Event published: `fotw.thread.captured` with session_id and statistics

**Verification:** Feed it a Claude chat export JSON. Confirm normalized output matches contract. Confirm stored in vault. Confirm event published.

---

### MISSION 2: THE ROUTING LEG (Layer 3)

**File:** `C:\Users\Jamie\workspace\fotw\element_router.py`

**Purpose:** Take the CCP-parsed elements from Layer 2 and route each one to the correct EPOS business process based on its type. Routing is deterministic — no LLM involved.

**Dependencies:**
- Layer 1 output (normalized thread) stored in vault
- CCP Engine (Layer 2) has parsed the thread and produced element classifications

**The routing table (constitutional law):**

```python
ROUTING_TABLE = {
    "decision": {
        "primary": "context_vault/fotw/decisions/{session_id}.jsonl",
        "secondary": "pm_surface",  # if project-linked
        "event": "fotw.decision.logged",
        "action": "append to decision log with full context"
    },
    "action_item": {
        "primary": "pm_surface",  # creates a task
        "secondary": "friday_queue",  # if owner is Jamie
        "event": "fotw.action.created",
        "action": "create task with title, owner, source session, deadline if mentioned"
    },
    "idea": {
        "primary": "idea_pipeline",  # calls idea_log.capture()
        "secondary": "friday_triage",  # queued for 17:30 triage
        "event": "fotw.idea.captured",
        "action": "log idea with source attribution, queue for triage"
    },
    "research_question": {
        "primary": "rs1_queue",  # RS1 generates 7-vector brief
        "secondary": "ccp_vector_routing",  # CCP routes to correct vector
        "event": "fotw.research.queued",
        "action": "generate research brief, route to NotebookLM via Drive sync"
    },
    "objection": {
        "primary": "context_vault/fotw/objections/{session_id}.jsonl",
        "secondary": "sales_brain_patterns",
        "event": "fotw.objection.logged",
        "action": "store objection with context, add to Sales Brain pattern library"
    },
    "financial_signal": {
        "primary": "context_vault/fotw/financial/{session_id}.jsonl",
        "secondary": "fin_ops",
        "event": "fotw.financial.detected",
        "action": "store financial data point, flag for FIN_OPS review"
    },
    "strategic_insight": {
        "primary": "context_vault/doctrine/insights/{date}.jsonl",
        "secondary": "content_lab_seeds",
        "event": "fotw.insight.stored",
        "action": "store as institutional knowledge, seed Content Lab for potential content"
    },
    "technical_decision": {
        "primary": "context_vault/architecture/decisions/{date}.jsonl",
        "secondary": "doctor_validation",
        "event": "fotw.technical.decided",
        "action": "store architecture decision, flag Doctor for constitutional validation"
    },
    "risk": {
        "primary": "context_vault/fotw/risks/{session_id}.jsonl",
        "secondary": "pm_surface_blocker",
        "event": "fotw.risk.flagged",
        "action": "store risk, create blocker in PM if severity is high"
    },
    "enthusiasm": {
        "primary": "content_lab_priority",
        "secondary": "lead_scoring_signal",
        "event": "fotw.enthusiasm.detected",
        "action": "flag for Content Lab priority treatment, boost lead score if client-facing"
    }
}
```

**The router process:**
1. Read parsed elements from CCP output (Layer 2)
2. For each element, look up type in ROUTING_TABLE
3. Execute primary action (write to vault path or call EPOS module)
4. Execute secondary action if applicable
5. Publish event to both FOTW and EPOS event buses
6. Log the routing decision to `context_vault/fotw/routing_log.jsonl`

**Output contract:**
```json
{
  "session_id": "references source session",
  "routed_at": "ISO 8601",
  "elements_routed": 47,
  "by_destination": {
    "pm_surface": 12,
    "idea_pipeline": 8,
    "context_vault": 15,
    "rs1_queue": 5,
    "content_lab": 3,
    "sales_brain": 2,
    "fin_ops": 2
  },
  "events_published": 47,
  "routing_failures": 0
}
```

**Verification:** Parse a real thread through CCP, then run the router. Confirm elements appear in correct vault paths. Confirm events published. Confirm PM tasks created for action items. Confirm ideas logged in idea pipeline.

---

### MISSION 3: THE PUBLISHING LEG (Layer 5)

**File:** `C:\Users\Jamie\workspace\fotw\process_initiator.py`

**Purpose:** For elements that require active process initiation (not just storage), trigger the downstream EPOS workflows.

**The initiation table:**

| Routed Element | Process Initiated | EPOS Module Called | Output |
|---------------|-------------------|-------------------|--------|
| `action_item` → PM | Task creation | `epos.py pm task create` | New task in PM surface with session link |
| `idea` → Pipeline | Idea capture + triage queue | `idea_log.capture()` + Friday triage | Idea logged, queued for scoring |
| `research_question` → RS1 | 7-vector brief generation | `rs1_research_brief.generate()` | Brief produced, pushed to Drive/NotebookLM |
| `risk` (high severity) → PM | Blocker task creation | `epos.py pm task create --blocked` | Blocker visible in PM, assigned to owner |
| `enthusiasm` → Content Lab | Priority content seed | `content_signal_loop.process_signal()` | Content brief queued with priority flag |

**The initiation process:**
1. Read routing log from Layer 3
2. Filter for elements that require active initiation (not just vault storage)
3. Call the appropriate EPOS module for each
4. Verify the process was initiated (check for created artifacts)
5. Publish confirmation event: `fotw.process.initiated`
6. Generate session summary: total elements captured, routed, and initiated

**The session summary (the final output of the full pipeline):**
```
FOTW Thread Extraction Complete
================================
Session:    fotw-20260404-abc123
Source:     claude_chat_export.json (47 messages, 12,500 words)
Captured:   47 messages stored in vault
Parsed:     35 actionable elements identified
  - 5 decisions logged
  - 12 action items → 12 PM tasks created
  - 8 ideas → 8 queued for Friday triage
  - 5 research questions → 5 RS1 briefs generating
  - 2 objections → Sales Brain pattern library
  - 2 financial signals → FIN_OPS review
  - 3 strategic insights → Content Lab seeds
  - 1 technical decision → Architecture log
  - 2 risks → 1 PM blocker created (high severity)
  - 1 enthusiasm signal → Content priority flag

Events:     47 published to EPOS bus
Next:       Friday triage at 17:30 | RS1 briefs in ~10 min
```

---

## CLI INTEGRATION

Add to `epos.py`:

```
python epos.py fotw extract <chat_export_file> [session_name]
  → Runs full pipeline: capture → parse → route → initiate
  → Prints session summary

python epos.py fotw parse <session_id>
  → Re-run CCP parse on an existing captured session

python epos.py fotw route <session_id>
  → Re-run routing on an existing parsed session

python epos.py fotw status
  → Show FOTW node health: sessions captured, elements routed, processes initiated

python epos.py fotw sessions
  → List all captured sessions with date, source, element counts

python epos.py fotw session <session_id>
  → Show full detail of a specific session: elements, routing, initiated processes
```

---

## SOVEREIGNTY REQUIREMENTS

- FOTW Thread Extractor lives at `C:\Users\Jamie\workspace\fotw\`
- Zero EPOS imports in core modules (write to vault paths directly)
- Own event log at `fotw/context_vault/events/fotw_events.jsonl`
- Publishes to EPOS bus via direct JSONL append (same pattern as CCP)
- Passes all 7 sovereignty tests
- Target certification score: 85+ (MARKETPLACE_READY)

---

## BUILD SEQUENCE FOR CODE

**Mission 1:** Thread Extractor (Layer 1) — capture and normalize
**Mission 2:** Element Router (Layer 3) — deterministic routing
**Mission 3:** Process Initiator (Layer 5) — downstream activation
**Mission 4:** CLI integration + sovereignty certification

Each mission is self-contained. Each produces an AAR. Each must pass Doctor before the next begins.

**The first test:** Export this chat thread. Run it through the pipeline. See how many decisions, action items, ideas, and insights today's session produced. That's FOTW eating its own cooking.

---

## SIGNATURES

**Sovereign Architect:** Jamie Purdue
**Date:** April 4, 2026

> *"The conversation that built FOTW should be the first conversation FOTW processes."*

---
*FOTW Thread Extractor Build Specification — EXPONERE / EPOS Autonomous Operating System*
