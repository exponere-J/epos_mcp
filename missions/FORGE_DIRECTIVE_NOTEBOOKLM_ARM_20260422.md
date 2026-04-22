# FORGE DIRECTIVE — NOTEBOOKLM CLI ARM (2026-04-22)

**Issued by:** The Architect
**Assigned to:** The Forge → Agent Zero
**Constitutional Authority:** Articles V, VII, X, XVI §3 (Audio Triage)
**Directive ID:** `FORGE_DIR_NOTEBOOKLM_ARM_20260422`
**Status:** Specified; build pending Sovereign prioritization

---

## Scope

Wrap `notebooklm-py` CLI as an execution-arm variant so every council
member can generate Audio Overviews, video overviews, study guides, and
source bulk-uploads without Jamie touching NotebookLM's web UI.

Satisfies Article XVI §3: "Audio Triage Node is not optional — it is
the primary interface."

## Files to create (~300 LOC)

1. **`nodes/execution_arm/notebooklm_arm.py`** — Python arm.
   - `upload(hub_name, sources: list[Path])` — bulk ingest into a notebook
   - `audio_overview(hub_name, prompt_style="briefing")` — generate Audio Overview
   - `video_overview(hub_name, ...)`
   - `study_guide(hub_name)`
   - `quiz(hub_name, depth="fundamentals")` — produces QLoRA training pairs
   - `health()` — checks `notebooklm-py` CLI presence + `storage_state.json` freshness
2. **`nodes/execution_arm/notebooklm_auth.py`** — storage_state.json rotation.
   - Detects expired auth; emits `notebooklm.auth.expired` event; Steward
     surfaces in briefing for Sovereign re-auth.
3. **`containers/agent-zero/Dockerfile`** — append: `pip install notebooklm-py`.

## Auth model

- `storage_state.json` lives at `context_vault/secrets/notebooklm_state.json`
  (gitignored; never enters the Bridge corpus).
- Sovereign re-authenticates via the notebooklm-py OAuth flow on their
  machine; the resulting state file is copied into the container volume
  read-only.
- Every arm call validates state freshness (< 30 days) and emits an event
  if expired.

## Hub-and-spoke wiring

Per the Chronicler Archetype: 1 hub + 7 satellites (one per archetype +
1 Sovereign queue). Hub names are fixed:
- `epos.hub.active_stage`
- `epos.satellite.architect`
- `epos.satellite.oracle`
- `epos.satellite.sentinel`
- `epos.satellite.forge`
- `epos.satellite.chronicler`
- `epos.satellite.steward`
- `epos.sovereign.queue`

## Deletion governance

The arm's `delete_source(hub, source_id)` and `delete_notebook(hub)`
paths route through `deletion_gate.enforce(target=f"notebooklm:{hub}:{source_id}")`.

## Verification

- `arm.health()` returns `operational` with state mtime.
- Upload 3 test sources to `epos.hub.active_stage` → retrieve via API.
- Generate Audio Overview → mp3 lands under
  `context_vault/attachments/audio/<hub>_<timestamp>.mp3`.
- Steward briefing picks up the Overview with correct metadata.

## Out of scope

- Third-party TTS models (Piper, ElevenLabs). The Chronicler is
  NotebookLM-exclusive per its Archetype §Distinction.
- Source-type converters (PDF→markdown, audio→transcript). Those land
  upstream in the Forge's ingest pipeline.
