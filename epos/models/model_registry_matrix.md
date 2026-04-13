# EPOS Model Registry Matrix — 30 Slots
## Authority: Jamie Purdue, Sovereign Architect | EXPONERE/EPOS
## Date: April 11, 2026 | Version: 1.0

> **Living document.** Programmatic source of truth is `context_vault/state/model_registry.json`.
> This markdown is the human-readable view. Updated by `ModelRegistry.seat_model()` events.

---

## STATUS KEY

| Status | Meaning |
|---|---|
| `seated` | Model is live and operational |
| `harness_ready` | Infrastructure built, awaiting API key or model pull |
| `wired_groq` | Currently wired via Groq; upgrade to Fireworks queued |
| `pending` | Selected but not yet deployed |
| `research_required` | Model selection TBD |
| `awaiting_training_data` | Custom fine-tune; needs 30+ days of operational data |

---

## TEXT / CODE MODELS (Slots A1–A18)

| Slot | Role | Selected Model | Provider | Context | Priority | Status |
|---|---|---|---|---|---|---|
| **A1** | Primary Script Generator / Sovereign Coding Agent | qwen3-coder-30b-a3b-instruct | Fireworks AI | 262K | **P0** | harness_ready |
| **A2** | TTLG Scout Reasoning | qwen3-32b | Fireworks AI | 131K | P0.5 | pending |
| **A3** | TTLG Thinker Constitutional Evaluation | qwen3-32b | Fireworks AI | 131K | P0.5 | pending |
| **A4** | TTLG Surgeon Refactor Proposals | qwen3-32b | Fireworks AI | 131K | P0.5 | pending |
| **A5** | TTLG Analyst Verification | qwen3-32b | Fireworks AI | 131K | P0.5 | pending |
| **A6** | General Reasoning — EPOS Core Services | qwen3-32b | Fireworks AI | 131K | P1 | pending |
| **A7** | Classification / Routing / Summarization | qwen3-8b | Fireworks AI | 32K | P1 | pending |
| **A8** | Content Generation — Avatar-Calibrated | qwen3-32b + avatar-lora | Fireworks AI | 131K | P1 | pending |
| **A9** | Morning Briefing Narrative Generator | qwen3-32b | Fireworks AI | 131K | P2 | pending |
| **A10** | Anomaly Root Cause Explanation | qwen3-32b | Fireworks AI | 131K | P2 | pending |
| **A11** | Research Scanner + Market Brief | qwen3-32b | Fireworks AI | 131K | P2 | wired_groq |
| **A12** | Thread Staleness Semantic Classifier | qwen3-8b | Fireworks AI | 32K | P2 | pending |
| **A13** | FOTW Engagement Intent Classifier | qwen3-8b | Fireworks AI | 32K | P3 | pending |
| **A14** | AAR Insight Abstractor | qwen3-32b | Fireworks AI | 131K | P3 | pending |
| **A15** | Long-Document RAG / Research Frontier | llama-4-scout-17b-16e | Fireworks AI | 10M | P3 | pending |
| **A16** | Scout Depth Router | qwen3-8b | Fireworks AI | 32K | P3 | pending |
| **A17** | SOP Semantic Drift Detector | qwen3-8b | Fireworks AI | 32K | P4 | pending |
| **A18** | Fallback Reasoning (Groq tier) | llama-3.3-70b-versatile | Groq (free) | 128K | P0 fallback | **seated** |

---

## IMAGE MODELS (Slots V1–V3)

| Slot | Role | Selected Model | Provider | Priority | Status |
|---|---|---|---|---|---|
| **V1** | Brand Image Generation | FLUX.1-schnell + brand-lora | Local | P3 | pending |
| **V2** | Content Image Generation | FLUX.1-schnell | Local | P3 | pending |
| **V3** | Video Thumbnail / Storyboard | FLUX.1-schnell | Local | P4 | pending |

---

## VIDEO MODELS (Slots W1–W2)

| Slot | Role | Selected Model | Provider | Priority | Status |
|---|---|---|---|---|---|
| **W1** | Hero Content Video | Wan-2.2 | Local (GPU) | P4 | pending |
| **W2** | Short-Form / Reels | Wan-2.2 | Local (GPU) | P4 | pending |

---

## AUDIO MODELS (Slot S1)

| Slot | Role | Selected Model | Provider | Priority | Status |
|---|---|---|---|---|---|
| **S1** | TTS Voiceover / Briefing Audio | TBD | TBD | P5 | research_required |

> **Accessibility priority.** Voice-native output for Friday morning briefings. Serves Jamie's vision accommodations. Research: Kokoro, StyleTTS2, Coqui XTTS.

---

## EMBEDDING MODELS (Slots E1–E3)

| Slot | Role | Selected Model | Provider | Priority | Status |
|---|---|---|---|---|---|
| **E1** | Context Vault Semantic Search | nomic-embed-text | Ollama (local) | P2 | pending |
| **E2** | AAR + SOP Corpus Search | bge-m3 | Ollama (local) | P2 | pending |
| **E3** | Avatar Drift Embedding Tracker | nomic-embed-text | Ollama (local) | P3 | pending |

> **To activate E1/E2:** `docker exec epos-ollama ollama pull nomic-embed-text && ollama pull bge-m3`

---

## SPECIALIZED / CUSTOM FINE-TUNED (Slots C1, I1, P1)

| Slot | Role | Base Model | Training Data | Priority | Status |
|---|---|---|---|---|---|
| **C1** | Constitutional Classifier | qwen3-8b + constitutional-lora | Gate decisions + AARs (30 days) | P6 | awaiting_training_data |
| **I1** | Impact Predictor | qwen3-8b + impact-lora | AAR before/after metrics (30 missions) | P6 | awaiting_training_data |
| **P1** | Pattern Signal Discriminator | qwen3-8b + pattern-lora | Constitution changelog + mission outcomes | P6 | awaiting_training_data |

> These are the **three foundational models** from the Intelligence Layer Diagnostic (Apr 10, 2026).
> They cannot be trained until the organism has accumulated sufficient operational data.
> Start training clock: today. Target training date: ~May 11, 2026.

---

## REGISTRY SUMMARY

| Metric | Count |
|---|---|
| **Total slots** | 30 |
| **Seated (live)** | 1 (A18 — Groq fallback) |
| **Harness ready** | 1 (A1 — Qwen3-Coder, awaiting Fireworks key) |
| **Wired via Groq** | 1 (A11 — Research Scanner) |
| **Selected, pending deployment** | 23 |
| **Research required** | 1 (S1 — Audio/TTS) |
| **Awaiting training data** | 3 (C1, I1, P1) |

---

## SEATING SEQUENCE (Priority Order)

```
TODAY (P0):
  └── A1: Qwen3-Coder-30B → sovereign_coding_agent.py harness
       Action: Get Fireworks API key → add to litellm_config.yaml → test

WEEK 1 (P0.5):
  └── A2-A5: Qwen3-32B → replace Llama in TTLG Scout/Thinker/Surgeon/Analyst
       Action: Fireworks API key → update groq_router.TASK_MODEL_MAP

WEEK 2 (P1):
  └── A6, A7, A8: Qwen3-32B/8B → EPOS Core, Classification, Content Lab

WEEK 3-4 (P2):
  └── A9-A12, E1, E2: Briefing narrative, anomaly context, research, embeddings

MONTH 2 (P3-P5):
  └── A13-A17, V1-V3, W1-W2, E3, S1: Intent, RAG, visual, audio

MONTH 2+ (P6):
  └── C1, I1, P1: Custom fine-tuned specialized models (30 days data minimum)
```

---

## LITELLM CONFIG ADDITIONS NEEDED

When Fireworks API key is obtained, add to `litellm_config.yaml`:

```yaml
- model_name: qwen3-coder-30b
  litellm_params:
    model: fireworks_ai/accounts/fireworks/models/qwen3-coder-30b-a3b-instruct
    api_key: os.environ/FIREWORKS_API_KEY

- model_name: qwen3-32b
  litellm_params:
    model: fireworks_ai/accounts/fireworks/models/qwen3-32b
    api_key: os.environ/FIREWORKS_API_KEY

- model_name: qwen3-8b
  litellm_params:
    model: fireworks_ai/accounts/fireworks/models/qwen3-8b
    api_key: os.environ/FIREWORKS_API_KEY

- model_name: llama-4-scout
  litellm_params:
    model: fireworks_ai/accounts/fireworks/models/llama-4-scout-17b-16e-instruct
    api_key: os.environ/FIREWORKS_API_KEY
```

---

*EPOS Model Registry Matrix — April 11, 2026*
*EXPONERE / EPOS Autonomous Operating System*
*1% daily. 37x annually.*
