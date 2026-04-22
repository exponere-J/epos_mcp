# EPOS INSTITUTIONAL MEMORY

> **APPEND-ONLY.** Never delete entries. Update after every session.
> New Directives append to the DIRECTIVES table. New AARs append to the AARs table. SESSION CONTINUITY is the only block that is overwritten — but every prior session's state should have been captured in the tables before overwrite.

## Directive & AAR Registry

### DIRECTIVES (Format: YYYYMMDD-NN)
| ID | Title | Status | Key Output |
|----|-------|--------|------------|
| 20260413-01 | Path & Secret Sanitation | COMPLETE | sanitation_verifier.py |
| 20260413-02 | Repository Sovereignty | COMPLETE | .git/hooks, GitHub push |
| 20260413-03A | Voice System | COMPLETE | 14 voice pipeline files |
| 20260413-04 | Institutional Memory | COMPLETE | evolution_archive.json |
| 20260413-05 | SCC Shadow Protocol | COMPLETE | shadow_protocol.py |
| 20260414-01 | CCP + PM Surface | COMPLETE | extractor.py, store.py |
| 20260414-02 | Reward Bus Backwire | COMPLETE | reward_aggregator.py |
| 20260414-03 | Integration Wiring | IN PROGRESS | voice→CCP→PM→Friday |
| 20260414-04A | FOTW Bridge | COMPLETE | epos/fotw/ package |
| 20260421-A1 | Metabolic Governor | BUILT | metabolic_governor.py |
| 20260421-A2 | Audio Triage | BUILT | audio_triage.py |
| 20260421-A3 | Nebula Watcher | TIMEOUT | retry queued |
| 20260421-E1 | Pre-Mortem Gate | SPEC ONLY | in Enhanced Engineering doc |
| 20260421-S1 | Council Instantiation | COMPLETE | 11 council files |
| 20260421-S2 | Stop-hook silenced + Architect Tool Registry | COMPLETE | .claude/settings.local.json, ARCHITECT_TOOL_REGISTRY_v1.md |
| 20260421-S3 | Institutional Memory Seeded | COMPLETE | MEMORY.md |
| 20260421-S4 | AAR Corpus Relocated to Attachments | COMPLETE | 48 AARs moved; 4 doctrine refs re-pathed |
| 20260421-AZ | AZ Execution Arms (4 variants) | COMPLETE | nodes/execution_arm/ (7 files), AZ Dockerfile, az_bridge.py, 2 Friday executors |
| 20260422-T1 | TTLG Post-Completion (full organism) | COMPLETE | organism_state.json (73 modules: 8 REGISTER, 65 LEGACY_AUDIT), TTLG_RESUBMISSION_LOOP_v1.md |
| 20260422-B1 | Bridge Protocol (sandbox↔WSL via GitHub MCP) | PROPOSED | Awaiting Sovereign ratification + first MCP push |
| 20260422-MF | MiroFish Simulator | NOT BUILT | Directive not yet drafted; growth-path Tier 3 Week 2 |

### AARs (Format: YYYYMMDD-session)
| ID | Focus | Key Learning |
|----|-------|-------------|
| 20260407-AM | Execution Layer | BrowserUse operational, 22 nodes |
| 20260407-PM | 8-Scan Diagnostic | Score 64/100, workflow 1 breaks at step 3 |
| 20260408 | Dockerization | 14-service compose, bidirectional bus |
| 20260409 | Thread Summary | Intelligence layer path mapped |
| 20260414-04A | FOTW Bridge | 8 CCP elements in 6.9s, path bug caught |
| 20260421 | EXHAUSTIVE | Council named, products packaged, Docker launched |
| 20260422-TTLG | Post-Completion Full Organism | 73 modules validated: 8 REGISTER, 65 LEGACY_AUDIT, 0 REVISE, 0 REJECT |

### SESSION CONTINUITY
Last session: 2026-04-22
Docker status: 5 healthy, 5 restarting, 1 port conflict (unchanged — AZ container rebuild pending)
Products ready: CCP Pack, Pre-Mortem Kit (PDFs pending)
Active client: LuLu (TP6, discovery pending; price-sensitive protocol active)
Council: 6 named, 3 growth path
Process Registry: 73 entries at context_vault/state/organism_state.json
Execution Arm: 4 variants built (browser_use + computer_use × headless + headed); deletion-gated; universal call surface; pending AZ container rebuild
Bridge Protocol: proposed, not yet ratified; ALL of today's artifacts remain sandbox-only until first MCP push
Next priorities:
  1. Sovereign ratification of Bridge Protocol + first MCP push to claude/general-session-zLIkW
  2. Rebuild AZ container with new Dockerfile (arms deps)
  3. Live TTLG 8scan to upgrade 65 LEGACY_AUDIT entries
  4. MiroFish Stage-1 Directive (growth-path activation)
  5. Package products, fix Docker services, first LinkedIn post
