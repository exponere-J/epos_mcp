# Parts Bin Inventory

**Auto-generated** by daily cron reading `organism_state.process_matrix.capability_index`
and cross-referencing `products_registry`.

Every reusable component × which products it's currently deployed in.
Synthesizer queries this when assembling a new product candidate.

## Component → Products

(Populated at next daily cron run. Schema below is authoritative.)

| Component ID | Path | Capability tags | Current deployments | Version |
|---|---|---|---|---|
| (auto-rendered) | — | — | — | — |

## Deployments → Components

| Product | Components used | Last rebuild |
|---|---|---|
| P-0001 CCP Pack | E-0024 (ccp/), E-0094 (voice/pipeline) | 2026-04-22 |
| P-0002 Pre-Mortem Kit | E-0049 (epos_doctor) | 2026-04-22 |
| brand_dna_kit | content_lab/validation/brand_validator | 2026-04-23 |
| journey_map | EPOS_CONSUMER_JOURNEY_MAP_v3.md | 2026-04-23 |
| voice_pack | E-0094 (voice/pipeline) + vocabulary docs | 2026-04-23 |
| signal_framework | E-0153 (fotw_listener) | 2026-04-23 |

## Unused components (opportunity queue)

Components in the registry that aren't deployed in any product.
These are the Synthesizer's first-look candidates when a new signal arrives.

**See:** `context_vault/state/organism_state.json` for source data.
