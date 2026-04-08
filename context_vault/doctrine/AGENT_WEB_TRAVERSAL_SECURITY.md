<!-- EPOS GOVERNANCE WATERMARK -->
# AGENT_WEB_TRAVERSAL_SECURITY.md
# File: C:\Users\Jamie\workspace\epos_mcp\contextvault\doctrine\AGENT_WEB_TRAVERSAL_SECURITY.md

# AGENT WEB TRAVERSAL SECURITY PROTOCOL
## EPOS Constitutional Doctrine — External Network Access Governance

**Version:** 1.0.0  
**Status:** ACTIVE DOCTRINE — BINDING ON ALL AGENTS WITH EXTERNAL NETWORK ACCESS  
**Established:** 2026-02-21  
**Author:** Jamie Purdue, EPOS Architect  
**Ratified Under:** EPOS Constitution v3.1 — Articles II, IX, X; Zero-Trust Node Policy  
**Companion Documents:** MARKET_ORACLE_SPEC.md, NODE_SOVEREIGNTY_CONSTITUTION.md  
**Amendment Process:** Per EPOS Constitution v3.1, Article VIII

---

## PREAMBLE

Every agent that touches the external web becomes an attack surface. The Agentic Web is not a safer internet — it is the same internet with a new attack vector: agents that can read, decide, and act without a human reviewing each step. Prompt injection, credential exfiltration, poisoned market signals, and adversarial content designed to manipulate agent reasoning are not theoretical risks. They are the operating environment.

This doctrine applies to OpenClaw, the Market Awareness Node, any Research Engine capability, Content Lab tributaries, and any future agent granted external network access. The doctrine is written before a single web request is made, because security designed after the breach is not security — it is damage control.

An agent that cannot traverse the web safely is more dangerous than an agent that cannot traverse it at all.

---

## ARTICLE I: SCOPE AND APPLICABILITY

### Agents Governed by This Doctrine

Any EPOS component that initiates an outbound HTTP/HTTPS request, scrapes a URL, calls an external API, reads an RSS feed, or receives data from any source outside the `epos_mcp` perimeter is subject to this doctrine in full.

Current governed agents:

- **OpenClaw** — primary external sensory cortex, Fiverr/Upwork/LinkedIn/Reddit traversal
- **Market Awareness Node (Port 8015)** — receives and scores OpenClaw output
- **Content Lab Tributaries** — X (Twitter), TikTok, YouTube, LinkedIn capture schedulers
- **Research Engine** — any query dispatched to Exa, Brave Agentic API, or Firecrawl
- **FOTW (any external meeting/content ingestion)** — when consuming external links or uploads
- **WordPress/Haiku integration** — when reading or writing to external CMS endpoints

### Agents NOT Governed (Internal Only)

- Event Bus, Governance Gate, Context Server, Learning Server, Immune Monitor — internal container services with no external network requirements. If any of these components develops an external network dependency, this doctrine immediately applies.

---

## ARTICLE II: THE ZERO-TRUST WEB MODEL

### Core Principle

Every external URL, API response, data payload, and webpage is treated as potentially adversarial until it has been validated by the Sanitization Layer. Trust is never assumed based on source reputation, domain age, HTTPS status, or prior successful access. A trusted domain can be compromised. A trusted API can return poisoned data. A trusted marketplace can surface prompt injection in a gig listing.

### The Four Trust Axioms

**Axiom 1 — No Implicit Trust**
An agent never assumes a response is safe because the request was expected. Validation happens on every response, every time, with no exceptions for "known good" sources.

**Axiom 2 — Minimum Footprint**
Agents request only what they need. No speculative fetches, no "grab everything and filter later," no caching of raw external content in locations accessible to the reasoning layer without sanitization.

**Axiom 3 — Isolation Before Reasoning**
Raw external content never enters an agent's reasoning context directly. It passes through the Sanitization Layer first. An agent that reasons directly on unsanitized web content is constitutionally non-compliant.

**Axiom 4 — Explainable Provenance**
Every piece of data that influences an agent's decision can be traced to its source URL, retrieval timestamp, and validation status. If provenance cannot be established, the data is rejected and the rejection is logged.

---

## ARTICLE III: THE NEURAL RETRIEVAL HIERARCHY

### Why Standard Scraping Is Constitutionally Non-Preferred

HTML scraping of visual web pages produces unstructured content that must be interpreted by the reasoning layer, creating a broad attack surface for prompt injection and semantic manipulation. The Agentic Web fork has produced better primitives. EPOS agents SHALL use these primitives in the following priority order:

**Tier 1 — Agent-Native Structured APIs (Preferred)**
- Exa.ai neural retrieval — returns structured, semantically-indexed results designed for agent consumption
- Brave Agentic API — structured search results with agent-optimized response format
- Platform-native APIs (Fiverr API, Upwork API, LinkedIn API) — structured JSON, authenticated, auditable

**Tier 2 — Markdown-First Endpoints (Acceptable)**
- Cloudflare's `accept: text/markdown` header targets — returns Markdown instead of HTML
- Pages with `LLM.txt` sitemaps — structured agent guidance embedded in site architecture
- Any endpoint responding to `Accept: text/markdown` with valid Markdown content

**Tier 3 — Firecrawl-Mediated Extraction (Conditional)**
- Firecrawl converts HTML to structured Markdown before returning to the agent
- Acceptable only when Tier 1 and Tier 2 are unavailable for a specific target
- Every Tier 3 retrieval is logged with reason for downgrade from preferred tier

**Tier 4 — Raw HTML Scraping (Restricted)**
- Permitted only with explicit mission justification logged to the event bus
- Raw HTML NEVER enters the reasoning layer — Firecrawl or equivalent must mediate
- Rate-limited to 10 requests per hour per domain
- Requires Governance Gate approval before being added to any mission's permitted operations

**Tier 5 — Prohibited**
- Scraping behind authentication walls without explicit credential authorization
- Scraping `.onion` domains or anonymized routing networks
- Scraping any domain on the EPOS Deny List (see Article VII)
- Direct JavaScript-rendered page execution without sandboxed browser isolation

---

## ARTICLE IV: THE SANITIZATION LAYER

### Architecture

The Sanitization Layer is a mandatory processing stage between raw external content and any EPOS reasoning component. It is not optional. It is not skippable for "low-risk" content. Every byte from the external web passes through it.

```
External Web
    │
    ▼
[Retrieval Agent] — makes the HTTP request in isolated container
    │
    ▼
[Raw Response Buffer] — temporary, isolated, never accessed by reasoning layer
    │
    ▼
[Sanitization Layer]
    ├── Schema Validation — does response match expected structure?
    ├── Size Gate — reject if response exceeds 500KB without explicit authorization
    ├── Prompt Injection Scanner — detect instruction-like patterns in content
    ├── Credential Pattern Detector — detect API keys, tokens, passwords in returned data
    ├── Encoding Normalizer — strip Unicode tricks, zero-width characters, homoglyphs
    ├── URL Extractor — extract and log all URLs found in content (never auto-follow)
    └── Classification Tagger — tag content type, confidence, source tier
    │
    ▼
[Sanitized Payload] — safe for reasoning layer consumption
    │
    ▼
[EPOS Reasoning Component] — receives only sanitized, classified, sized content
```

### Prompt Injection Detection

Prompt injection is the primary attack vector against reasoning agents. An adversary embeds instruction-like text in web content, product listings, or API responses, hoping the agent will execute the embedded instruction rather than process the content as data.

**Detection Patterns (non-exhaustive, updated via Learning Server):**

```python
INJECTION_PATTERNS = [
    # Direct instruction injection
    r"ignore previous instructions",
    r"ignore all previous",
    r"disregard your",
    r"you are now",
    r"your new instructions",
    r"forget everything",
    r"system prompt",
    r"act as",
    r"pretend you are",
    
    # EPOS-specific targeting
    r"context vault",
    r"governance gate",
    r"constitutional",
    r"epos_doctor",
    r"agent zero",
    
    # Credential extraction attempts
    r"api[_\s]?key",
    r"send.*password",
    r"reveal.*token",
    r"what is your.*key",
    r"print.*credentials",
    
    # Exfiltration attempts
    r"http[s]?://(?!approved-domains)",  # URLs not on approved list
    r"curl\s",
    r"wget\s",
    r"fetch\s+http",
    
    # Encoding tricks
    r"\\u[0-9a-fA-F]{4}",  # Unicode escapes in unexpected positions
    r"\x[0-9a-fA-F]{2}",   # Hex escapes
]
```

**On Detection:**
- Content is quarantined immediately
- Retrieval is logged as `SECURITY_ALERT: prompt_injection_detected`
- Source domain is flagged for review in the Deny List candidate queue
- No portion of the flagged content enters the reasoning layer
- Immune Monitor is notified via event bus: `security.injection.detected`

### Size and Rate Controls

```python
SANITIZATION_LIMITS = {
    "max_response_size_bytes": 512_000,        # 500KB hard limit
    "max_response_size_reasoning": 32_000,      # 32KB max into reasoning context
    "max_urls_extracted_per_response": 50,      # URL list ceiling
    "max_requests_per_domain_per_hour": {
        "tier_1_api": 1000,
        "tier_2_markdown": 200,
        "tier_3_firecrawl": 60,
        "tier_4_raw_html": 10,
    },
    "max_concurrent_external_requests": 5,      # Global concurrent cap
    "request_timeout_seconds": 30,             # No hanging connections
    "retry_max_attempts": 2,                   # Fail fast, log, move on
    "retry_backoff_seconds": 5,
}
```

---

## ARTICLE V: CONTAINER ISOLATION PROTOCOL

### The "Agent-as-Adversary" Model

Following the IronClaw security model identified in the Agentic Web analysis, EPOS treats every external-facing agent as a potential adversary — not because agents are malicious, but because any agent that touches the external web can be compromised through the content it retrieves. The container is the last line of defense.

### Isolation Requirements

Every agent with external network access MUST run in an isolated container with the following constraints:

**Network Policy:**
```yaml
# Docker network policy for external-facing agents
networks:
  openclaw_external:
    driver: bridge
    internal: false           # Can reach external internet
    attachable: false         # Cannot be attached ad-hoc
  epos_internal:
    driver: bridge
    internal: true            # Cannot reach external internet
    
# OpenClaw connects to BOTH networks
# All other EPOS services connect ONLY to epos_internal
# OpenClaw is the sole internet-facing component
```

**Volume Policy:**
```yaml
volumes:
  # OpenClaw can WRITE to:
  openclaw_staging:           # Raw retrieved content (pre-sanitization)
  market_intelligence_write:  # Post-sanitization, validated signals only
  
  # OpenClaw CANNOT access:
  context_vault_internal:     # Node operational state — read/write forbidden
  engine_modules:             # Core EPOS Python modules — forbidden
  credentials_vault:          # API keys, tokens — forbidden
  governance_gate:            # Constitutional enforcement — forbidden
```

**Process Policy:**
```yaml
# OpenClaw container security constraints
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE       # Only needed for outbound HTTP
read_only: true            # Root filesystem is read-only
tmpfs:
  - /tmp:size=64m,noexec   # Temporary work space, no execution
```

**Hetzner Migration Note:** When migrating to Hetzner, the above policies translate to Firewall Rules at the host level: OpenClaw's server has outbound access on 443/80; all other service servers have no outbound internet access and communicate only on the internal private network. This is the hardened equivalent of WebAssembly sandboxing at the infrastructure level.

### What a Compromised OpenClaw Can Do

A constitutionally-compliant OpenClaw, even if its reasoning is manipulated by injected content, is bounded by its container permissions. The worst-case compromised state is:

- Can retrieve and write poisoned content to `openclaw_staging` — caught by Market Awareness sanitization
- Can exhaust outbound rate limits — caught by container network policy rate limits
- Can fill staging disk — caught by volume size limits (see below)
- Cannot read Context Vault, cannot touch engine modules, cannot access credentials, cannot reach other EPOS containers directly

This is acceptable risk. The container is the firewall for the reasoning layer.

---

## ARTICLE VI: CREDENTIAL MANAGEMENT FOR EXTERNAL APIS

### The Credential Vault Protocol

All API credentials (Exa, Brave, Fiverr API, Upwork API, LinkedIn API, X API, etc.) are stored in the EPOS Credential Vault, not in environment variables, not in `.env` files accessible to external-facing containers, and not embedded in any code file.

**Storage Standard:**
```
credentials_vault/
  exa_api.enc          # AES-256-GCM encrypted
  brave_api.enc
  fiverr_api.enc
  upwork_api.enc
  linkedin_api.enc
  x_api.enc
```

Each `.enc` file is encrypted with a key derived from the machine fingerprint (hardware ID + OS installation ID). Keys are never stored in the `epos_mcp` directory. They are never logged. They are never included in snapshots.

**Access Pattern:**
1. Agent requests credential for specific API via the Credential Service (internal only)
2. Credential Service validates the requesting agent's identity (mission_id + agent_id)
3. Credential Service issues a time-limited token (expires in 1 hour or mission end, whichever is first)
4. Token is delivered to the agent in memory only — never written to disk, never logged
5. Token expiry is enforced by the Credential Service; expired tokens are rejected with `ERR-CRED-EXPIRED`

**Agents that can request credentials:**
- OpenClaw (for approved platform APIs only)
- Research Engine (for Exa, Brave only)
- Content Lab Tributaries (for platform-specific APIs only, scoped to their platform)

**Agents that CANNOT request credentials:**
- Any agent not on the pre-approved credential access manifest
- Any agent running in a container with external network access AND access to Context Vault internal state simultaneously (the two must never coexist)

---

## ARTICLE VII: THE DOMAIN ALLOW LIST AND DENY LIST

### Approved Domain Categories

OpenClaw and Research Engine agents may only initiate requests to domains in the following approved categories. Any domain not in an approved category requires explicit mission-level authorization logged to the event bus before the first request.

**Tier 1 — Agent-Native APIs (Pre-Approved):**
- `api.exa.ai`
- `api.search.brave.com`
- `api.fiverr.com`
- `api.upwork.com`
- `api.linkedin.com`
- `api.twitter.com` / `api.x.com`
- `api.reddit.com`
- `api.firecrawl.dev`

**Tier 2 — Marketplace Intelligence (Pre-Approved):**
- `www.fiverr.com` (read-only, Tier 3/4 retrieval)
- `www.upwork.com` (read-only, Tier 3/4 retrieval)
- `www.linkedin.com` (read-only, Tier 3/4 retrieval)
- `www.reddit.com` (read-only, Tier 2/3 retrieval)
- `twitter.com` / `x.com` (read-only)

**Tier 3 — Requires Mission Authorization (Not Pre-Approved):**
- Any domain not in Tier 1 or Tier 2
- Authorization logged as: `external.domain.auth.requested` event with mission_id, requesting_agent, target_domain, justification

**The Deny List (Permanent Prohibition):**
- Any domain flagged for prompt injection attempts (auto-added by Immune Monitor)
- Any domain returning content that triggered `security.injection.detected`
- Tor exit nodes and anonymization proxies
- Data broker aggregators (these should be sourced through Exa/Brave, not direct)
- Credential-phishing indicator domains (sourced from threat intelligence feeds, updated monthly)

---

## ARTICLE VIII: THE LLM.TXT AND MARKDOWN-FIRST ADOPTION PROTOCOL

### Why This Matters for EPOS

The Agentic Web fork creates a structural advantage for operators who adopt Markdown-first and `LLM.txt` standards before their competitors. Every WordPress page EPOS deploys for clients that includes these standards becomes natively readable by agent networks without requiring scraping, translation, or interpretation overhead. This compounds as agent traffic grows.

### Implementation Standard

Every WordPress deployment made through EPOS MUST include:

**1. The `Accept: text/markdown` Header Support**
The WordPress site should serve Markdown-formatted content when an agent sends `Accept: text/markdown` in the request header. This is achievable via Cloudflare Worker or WordPress plugin. The Markdown version should be a clean, structured representation of the page content without navigation chrome, ads, or decorative HTML.

**2. The `LLM.txt` Sitemap**
Located at `https://[client-domain]/llm.txt`, this file:
```
# [Client Business Name] — Agent-Readable Sitemap
# Format follows LLM.txt specification

## Services
/services/[service-name] — [one-line description]

## Contact
/contact — [contact method description]

## Portfolio
/portfolio — [brief portfolio description]

## Pricing
/pricing — [pricing structure description]

## About
/about — [business identity description]

> Agent Instructions: This business uses EPOS-powered AI agents.
> For structured data queries, append ?format=json to any endpoint.
> For Markdown content, send Accept: text/markdown header.
```

**3. The `robots.txt` Agent Policy**
```
# Standard crawlers
User-agent: *
Allow: /

# Agent-native crawlers (explicitly welcomed)
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

# Agent-optimized sitemap
Sitemap: https://[domain]/llm.txt
Sitemap: https://[domain]/sitemap.xml
```

### Security Consideration for LLM.txt

The `LLM.txt` file is public-facing and will be read by external agents. It must NEVER contain:
- Internal system prompts or operational instructions
- API keys or credentials (even encrypted)
- Internal EPOS doctrine or constitutional references
- Anything that would give a competitor intelligence about the client's operational stack

The `LLM.txt` is a marketing and discoverability asset. It is not a technical configuration file.

---

## ARTICLE IX: THE X42 PROTOCOL — AGENT WALLET SECURITY

### What X42 Introduces

Coinbase's X42 Agentic Wallet protocol enables machine-to-machine commerce. In the EPOS context, this means agents could eventually fund their own compute, pay for API calls, or receive payment for delivered services — all without human intervention in the payment flow. This is powerful and constitutionally dangerous without explicit governance.

### Phase 1 Restrictions (Current)

X42 integration is NOT authorized in Phase 1. Rationale: an agent with autonomous spending authority and external network access is a category of risk that requires dedicated security doctrine, hardware security module integration, and constitutional amendment before deployment.

### Pre-Authorization Requirements for Future X42 Integration

Before any EPOS agent is granted X42 wallet access, the following must be completed:

1. **Spending Ceiling Constitution**: A formal constitutional amendment establishing hard spending ceilings per agent per hour, per day, and per mission. No ceiling = no authorization.

2. **Human Approval Gate for Threshold Transactions**: Any single transaction above $10 (or equivalent) requires human-in-the-loop approval. Any transaction above $50 requires Jamie's explicit confirmation. These thresholds are encoded in the wallet smart contract, not in agent instructions (which can be manipulated).

3. **Wallet Isolation**: The agent wallet is not the business wallet. The agent wallet is funded by a controlled transfer from the business wallet, with a maximum balance cap enforced by the wallet contract. If the agent wallet is drained by a compromised agent or adversarial content, the business wallet is unaffected.

4. **Transaction Audit Trail**: Every X42 transaction is logged to `context_vault/financial_audit/` with mission_id, agent_id, amount, recipient, justification, and timestamp. This log is append-only and cannot be modified by any agent.

5. **No Self-Authorization**: An agent cannot authorize its own wallet to receive more funds. Only a human-approved process can top up an agent wallet.

---

## ARTICLE X: INCIDENT RESPONSE PROTOCOL

### Detection Sources

The Immune Monitor is the primary detection mechanism for web traversal security incidents. It monitors:

- Anomalous outbound request volumes (>2x baseline for any agent in any 15-minute window)
- Prompt injection detection events from the Sanitization Layer
- Failed credential validation attempts
- Unauthorized domain access attempts (domains not on Allow List)
- Agent memory/context size anomalies (potential data exfiltration staging)

### Incident Classification

| Severity | Definition | Response |
|---|---|---|
| **P1 — Critical** | Confirmed prompt injection executed; credential exposure; unauthorized write to Context Vault | Immediate container halt, Stasis Mode, human notification |
| **P2 — High** | Prompt injection detected and blocked; unauthorized domain attempt; credential expiry failure | Agent suspended, incident logged, domain added to Deny List candidate queue |
| **P3 — Medium** | Rate limit exceeded; sanitization failure on non-injection content; timeout pattern | Logged, rate limiter adjusted, mission continues with reduced velocity |
| **P4 — Low** | Schema validation failure on external API response; single retry needed | Logged, automated retry, no human action required |

### P1 Response Sequence

1. Immune Monitor publishes `security.incident.p1` event to event bus
2. Governance Gate enters lockdown: no new external requests authorized
3. Affected container is halted (not restarted)
4. Snapshot of affected container's staging buffer is written to `context_vault/security_incidents/` for forensic analysis
5. All time-limited credentials issued to affected agent are revoked via Credential Service
6. Human notification via configured alert channel (email/SMS/Slack)
7. No restart authorized until human reviews forensic snapshot and authorizes recovery

### Post-Incident Learning

Every P1 and P2 incident produces an Incident Report written to `context_vault/security_incidents/YYYY-MM-DD_incident.json`. The Learning Server ingests these reports and updates:
- Injection pattern library (new patterns detected)
- Domain risk scores (sources that triggered incidents)
- Agent behavior baselines (recalibrate anomaly detection thresholds)

Security incidents are the Learning Server's most valuable training data. They are never deleted. They are never summarized into less detail than their original form.

---

## ARTICLE XI: EPOS DOCTOR SECURITY VALIDATION ADDITIONS

The following checks SHALL be added to `epos_doctor.py` web traversal security module:

```python
security_traversal_checks = [
    # Container isolation
    ("openclaw_network_isolation", "OpenClaw cannot reach epos_internal network directly"),
    ("no_agent_direct_vault_write", "No external-facing agent has write access to context_vault/internal/"),
    ("credential_vault_encrypted", "credentials_vault/*.env files absent; .enc files present"),
    ("container_read_only_root", "External-facing containers have read-only root filesystem"),
    
    # Sanitization layer
    ("sanitization_layer_running", "Sanitization service health check passes"),
    ("injection_patterns_current", "Injection pattern library updated within 30 days"),
    ("size_gate_enforced", "No response > 512KB in last 24hr traversal logs"),
    
    # Allow/Deny lists
    ("allow_list_present", "domain_allow_list.json exists and is non-empty"),
    ("deny_list_present", "domain_deny_list.json exists"),
    ("deny_list_updated", "Deny list modified within 7 days or confirmed current"),
    
    # Credential management
    ("no_plaintext_api_keys", "No API key patterns found in any .env, .py, .json files in epos_mcp/"),
    ("credential_service_running", "Credential Service health check passes"),
    ("token_expiry_enforced", "No tokens with TTL > 3600 seconds in credential service"),
    
    # Incident response
    ("immune_monitor_connected", "Immune Monitor subscribed to security.* events"),
    ("incident_log_writable", "context_vault/security_incidents/ directory exists and is writable"),
    ("p1_response_documented", "P1 response contact/alert configured"),
]
```

Exit Code 2 (Constitutional Violation — halt) triggers on:
- `no_agent_direct_vault_write` failure
- `no_plaintext_api_keys` failure
- `container_read_only_root` failure (on Hetzner migration)

---

## ARTICLE XII: INTEGRATION POINT MAP — OPENCLAW TO EPOS

### The Precise Wiring

This is the integration point map for OpenClaw's connection to the existing `epos_mcp` codebase, based on the inventory of `api/epos_api.py`, `engine/epos_intelligence.py`, and `containers/market-awareness/`:

```
OpenClaw Process
    │
    │  [Tier 1: Exa/Brave API calls via approved domains only]
    │  [Tier 3: Firecrawl for non-API targets]
    │  [All requests through Sanitization Layer before any EPOS contact]
    │
    ▼
containers/market-awareness/server.py (Port 8015)
    │
    ├── POST /ingest/openclaw         ← OpenClaw pushes sanitized payload here
    │        │
    │        ├── Schema validation against external.market.delta pre-validation schema
    │        ├── Confidence scoring (reject if < 0.70)
    │        ├── Opportunity classification
    │        └── Node relevance tagging
    │
    ├── Writes validated signal to:
    │        context_vault/market_intelligence/YYYY-MM/EVT-*.json
    │
    └── Publishes to Event Bus:
             containers/event-bus/server.py
                  │
                  └── event_type: "external.market.delta"
                           │
                           ├── engine/epos_intelligence.py
                           │        └── oracle_scan() method
                           │
                           └── api/epos_api.py
                                    └── /oracle/report endpoint
                                         └── Consumed by Advisory Dashboard
```

### Files to Extend (Not Replace)

- `containers/market-awareness/server.py` — add `/ingest/openclaw` endpoint and scoring logic
- `engine/epos_intelligence.py` — add `oracle_scan()` method subscribing to `external.market.delta`
- `api/epos_api.py` — add `/oracle/report` endpoint returning current Oracle advisory state
- `epos_doctor.py` — add security traversal checks from Article XI above
- `docker-compose.yml` — add network isolation policy separating `openclaw_external` from `epos_internal`

---

## RATIFICATION

This doctrine is established as binding constitutional law for all EPOS agents that touch the external web. It applies immediately to OpenClaw, retroactively to any existing external-facing components, and proactively to any future agent granted external network access.

The Agentic Web is an opportunity. It is also an attack surface. This doctrine is how EPOS hunts without being hunted in return.

Security is not a feature added after the system works. Security is the condition under which the system is allowed to operate at all.

**Signed:** Jamie Purdue, EPOS Architect  
**Date:** 2026-02-21  
**Constitutional Basis:** EPOS Constitution v3.1, Zero-Trust Node Policy, Node Sovereignty Constitution  
**Next Review:** 2026-05-21  
**Amendment Path:** Per EPOS Constitution v3.1, Article VIII