# AAR: Intelligence Layer Diagnostic + LiteLLM Proxy Fix
**Date:** 2026-04-10
**Directives:** PRINT_MODEL_REGISTRY + FIX_LITELLM_PROXY + INTELLIGENCE_LAYER_AUDIT
**Result:** COMPLETE — Proxy operational, model registry printed, intelligence layer mapped

---

## What Was Done

### M1 — EPOS Model Registry
Produced a full model registry across 6 tiers:
- **Tier 1**: Active backends (Groq Cloud LIVE, LiteLLM Proxy LIVE, Ollama running/empty)
- **Tier 2**: Wired model slots (llama-3.3-70b reasoning, llama-3.1-8b classification, LiteLLM proxy default, Ollama direct, Claude Code fallback)
- **Tier 3**: Claude model name aliases in LiteLLM (8 claude/* names → groq/llama-3.3-70b-versatile)
- **Tier 4**: Features with active model wiring (morning briefing, nightly upskill, research scanner, code executor, TTLG healing, Groq classification)
- **Tier 5**: Unwired slots (14 features identified — thread tracker synthesis, proactive intelligence explanation, anomaly context, TTLG question generator, pattern promotion classifier, avatar drift, SOP drift, FOTW sentiment, etc.)
- **Tier 6**: Groq task-type → model matrix with TPM limits

### M2 — LiteLLM Proxy Fix (`No connected db` Error)
**Symptom:** WSL2 CC test returned `400 {"error":{"message":"No connected db."}}`

**Root cause:** LiteLLM `main-latest` image enables spend logging by default. Spend logging requires a database (`DATABASE_URL`). No DB was configured in the EPOS stack for LiteLLM.

**Fix:** Added to `litellm_config.yaml`:
```yaml
general_settings:
  master_key: sk-epos-local-proxy
  disable_spend_logs: true
  disable_error_logs: true
```

**Verification:** `curl -X POST http://localhost:4000/v1/chat/completions` with `claude-sonnet-4-6` returned `{"content":"OK"}`. Proxy is clean.

### M3 — WSL2 Claude Code TPM Blocker (Confirmed Hard Limit)
Three background tasks confirmed the same result: Claude Code sends **~72,000 tokens** on initial context load. Groq free tier limit is **12,000 TPM** for `llama-3.3-70b-versatile`. This is a **6x gap** — not fixable by configuration.

**Error:** `429 RateLimitError: Limit 12000, Requested 72114`

**Options identified:**
| Path | TPM | Cost |
|---|---|---|
| Groq Dev Tier | 500k+ | ~$0.59/1M tokens |
| Ollama local | Unlimited | $0 (requires model pull) |
| Real Anthropic key (CC direct) | Per-token billing | ~$3/1M input |
| OpenRouter | Varies | Pay-per-use |

**Status:** Blocked until infrastructure decision. LiteLLM proxy is healthy — the blocker is upstream capacity.

### M4 — Intelligence Layer Diagnostic
Produced `INTELLIGENCE_LAYER_DIAGNOSTIC_20260410.md` — full audit of the Intelligence Layer across 5 domains:
- **14 specialization candidates** mapped (Constitutional Classifier, Impact Predictor, Pattern Signal Discriminator, and 11 secondary models)
- **16 deep research questions** formulated across 5 layers (Foundation, Orchestration, Diagnostic, Content, Recursive Learning)
- **5 executive questions** identified as prerequisites before model deployment
- **4-phase deployment path** defined (Research → Design → Validation → Gradual Deploy)
- **3 foundational models** identified as the priority tier (Constitutional Classifier, Impact Predictor, Pattern Signal Discriminator)

Key architectural insight documented: the three foundational models form a recursive feedback loop — each generates labeled training data that improves the next cycle. This is the mechanism by which small specialized models compound rather than just assist.

---

## Files Created / Modified

```
C:/Users/Jamie/workspace/epos_mcp/
  litellm_config.yaml              — MODIFIED: disable_spend_logs + disable_error_logs
  INTELLIGENCE_LAYER_DIAGNOSTIC_20260410.md  — NEW: full intelligence layer audit
  AAR_INTELLIGENCE_LAYER_PROXY_20260410.md   — NEW: this file

C:/Users/Jamie/Documents/EPOS/Attachments/
  INTELLIGENCE_LAYER_DIAGNOSTIC_20260410.md  — COPY: for Claude Project Files
  AAR_INTELLIGENCE_LAYER_PROXY_20260410.md   — COPY: for Claude Project Files
```

---

## Bugs Found & Fixed

| Bug | Fix |
|---|---|
| LiteLLM 400 `No connected db` on all proxy requests | Added `disable_spend_logs: true` + `disable_error_logs: true` to `general_settings` in `litellm_config.yaml`. Restarted litellm. |
| WSL2 `ANTHROPIC_BASE_URL` inheritance from parent CC session | Documented: WSL2 processes inherit Windows process env. Fix: open fresh Windows Terminal not spawned from active CC session. |

---

## Known Gaps (Not Blocking)

| Gap | Impact | Path to Fix |
|---|---|---|
| Groq free tier TPM (12k) insufficient for Claude Code (~72k) | Claude Code via LiteLLM proxy blocked | Groq Dev Tier upgrade OR Ollama local model OR real Anthropic key |
| Ollama container running but no models pulled | Ollama fallback path wired but inoperative | `docker exec epos-ollama ollama pull phi3:mini` + `ollama pull mistral:instruct` |
| 14 unwired model slots in intelligence layer | Rules-based / template-based decisions throughout | Phase 1-4 deployment path defined in diagnostic |
| Intelligence layer training data schema undefined | Constitutional Classifier has no labeled dataset yet | Define schema for linking gate decisions → constitutional articles (Phase 1, Week 1) |

---

## AAR Investigation: Missing AARs (April 8-10)

See separate investigation section in session output.

---

## State of EPOS Stack (End of Session)

```
LiteLLM Proxy:  LIVE — port 4000, claude-sonnet-4-6 → Groq verified
Groq Direct:    LIVE — mode=groq_direct, ok=True
Ollama:         RUNNING — no models pulled
Claude Code CLI: fallback_mode (container) / TPM-blocked (WSL2)
Docker:         epos-core (8001) + litellm (4000) + ollama (11434) + postgres (5432)
Model Registry: Printed — 6 tiers, 14 unwired slots identified
Intelligence Layer Diagnostic: Saved to project root + Attachments
```

---

## Next Directives When Ready

```bash
# Unblock Ollama fallback
docker exec epos-ollama ollama pull phi3:mini
docker exec epos-ollama ollama pull mistral:instruct

# Unblock Claude Code (option: direct Anthropic key)
wsl bash -c 'ANTHROPIC_API_KEY=sk-ant-YOUR_KEY claude'

# Intelligence Layer Phase 1
# → Answer 5 executive questions in INTELLIGENCE_LAYER_RESEARCH_ANSWERS.md
# → Define Constitutional Classifier training data schema
```
