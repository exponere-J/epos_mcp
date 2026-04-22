# TTLG ANTI-TRUNCATION CONTRACT v1

**Constitutional Authority:** EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XVI §1
**Charter:** `COUNCIL_CHARTER_v1.md`
**Ratified:** 2026-04-22 by Sovereign
**Scope:** all SCC-authored file writes at the governance gate
**Status:** Active

---

## Preamble — Why this contract exists

SCC can write files. TTLG can validate them. Without a formal alignment,
a subtle failure mode exists: SCC may write a partial file that still
passes a weak check (a plausible-looking SHA on a pre-computed hash, a
matching line count on a sparse file, a legal shebang on an empty body).
This contract eliminates that class of failure by requiring **six
independent integrity checks** per file. Any single miss = REJECT.

**No file enters the organism that is not byte-identical to what the
Architect committed.**

## Parties to the contract

| Party | Role |
|---|---|
| **The Architect** | Produces the session manifest with six-field integrity triples per file. |
| **The Forge (SCC)** | Writes each file to its WSL absolute path verbatim. Does not regenerate from specification. |
| **TTLG** | Independently re-computes all six fields and compares. Emits the verdict. |
| **ALPHA** (gate) | Constitutional arbiter of verdicts. REJECT is not appealable except by Sovereign. |

## The six integrity checks (per file)

For every `ADDED` or `MODIFIED` file in the session manifest:

| # | Check | What TTLG verifies | What it catches |
|---|---|---|---|
| 1 | **Full SHA256** | `sha256(file_bytes) == manifest.sha256` | Any byte change anywhere |
| 2 | **Byte count** | `len(file_bytes) == manifest.size_bytes` | Partial writes, silent truncation |
| 3 | **Line count** | `count(\n) + (1 if no-trailing-newline else 0) == manifest.lines` | Missing lines from middle or end |
| 4 | **First-line SHA** | `sha256(first_line) == manifest.first_line_sha256` | Head truncation (rare but possible) |
| 5 | **Last-nonempty-line SHA** | `sha256(last_nonempty_line) == manifest.last_nonempty_line_sha256` | Tail truncation (most common SCC failure) |
| 6 | **Trailing newline** | `file_ends_with_\n == manifest.trailing_newline` | Editor auto-strip, encoding drift |

**Verdict rule:** ALL SIX must pass. One miss = `REJECT_TRUNCATION`.

## Why six and not just SHA

| Scenario | SHA catches? | Why we still need 2–6 |
|---|---|---|
| SCC writes zero bytes but manifest says zero bytes | ❌ (hashes match on empty == empty) | #2 catches it when real size > 0 |
| SCC generates code from spec, loses last function | ✅ | #5 fails faster and names the failure type |
| Editor strips trailing newline | ✅ | #6 pinpoints the cause |
| File is written as UTF-8 BOM + content, manifest says no BOM | ✅ | #4 isolates the first-line mismatch |
| Silent CRLF → LF conversion | ✅ | #3 catches line-count drift before SHA comparison |

SHA is authoritative. The other five are **diagnostics** that make
rejections human-readable and telegraph the failure mode to the
Sovereign in plain terms.

## Contract terms (binding on all parties)

### The Architect (me) commits to:

1. Compute and publish all six integrity fields in the session manifest for every ADDED/MODIFIED entry.
2. Never ship a manifest with missing integrity fields.
3. Re-compute the integrity fields whenever the sandbox file changes before the push.
4. Emit a sentinel alert if sandbox file content drifts from the manifest before bridge crossing.

### The Forge (SCC) commits to:

1. Treat every file in the session manifest as **byte-sacred**. SCC copies; SCC does not reinterpret, re-format, re-serialize, or re-generate.
2. Before writing, verify the source bytes match the manifest SHA. If mismatch, refuse and escalate.
3. Write the file atomically: write to `<wsl_path>.partial`, fsync, rename to `<wsl_path>`. No half-written states visible to consumers.
4. Preserve line endings, encoding, trailing newlines, and leading BOMs exactly as the manifest describes.
5. Never run auto-format, linter, or "clean-up" passes against ingested files between SCC write and TTLG read.

### TTLG commits to:

1. Re-compute all six integrity fields from the on-disk file (never trust SCC's self-report).
2. Emit a `TRUNCATION_CHECK` verdict per file: `{pass, fail_reasons: []}`.
3. On any failure, write the rejection to `context_vault/bi/truncation_check.jsonl` with:
   - `file_path`, `directive_id`, `expected_<field>`, `actual_<field>`, `delta`, `timestamp`.
4. Block the `REGISTER` transition for any file that has ever failed check 1, 2, 3, 5, or 6. (Check 4 head-truncation is rare; on fail it may `REVISE` rather than block, per ALPHA ruling.)
5. Keep the TRUNCATION_CHECK log append-only; the Sovereign reviews it in the next morning briefing.

### ALPHA (arbiter) commits to:

1. Accept TTLG's TRUNCATION_CHECK verdict as authoritative.
2. Only the Sovereign may override a REJECT_TRUNCATION verdict.
3. A Sovereign override is logged with rationale to
   `context_vault/bi/sovereign_overrides.jsonl`; the overridden file
   is tagged `sovereign_override_truncation_accepted=true` in the
   registry for 90 days (Reward Bus scoring).

## Implementation receipt format

TTLG emits per-file to `context_vault/bi/governance_gate.jsonl`
(extending the existing gate receipt schema from the SCC Ingestion Directive):

```json
{
  "timestamp": "2026-04-22T14:30:01Z",
  "directive_id": "FORGE_DIR_SCC_INGEST_20260422",
  "file": "nodes/execution_arm/browser_use_arm.py",
  "wsl_path": "/mnt/c/Users/Jamie/workspace/epos_mcp/nodes/execution_arm/browser_use_arm.py",
  "verdict": "ACCEPTED",
  "truncation_check": {
    "passed": true,
    "full_sha256": "pass",
    "byte_count": "pass",
    "line_count": "pass",
    "first_line_sha256": "pass",
    "last_nonempty_line_sha256": "pass",
    "trailing_newline": "pass"
  },
  "governance_checks": {
    "path_discipline": "pass",
    "shebang": "pass",
    "watermark": "pass",
    "secret_scan": "pass"
  }
}
```

## Failure modes and responses

| Fail pattern | Verdict | TTLG response |
|---|---|---|
| Full SHA mismatch + byte count mismatch | `REJECT_TRUNCATION` | Halt batch; escalate to Sovereign. |
| Line count mismatch only | `REJECT_TRUNCATION` | Reject file; continue batch with warning. |
| Last-nonempty-line SHA mismatch | `REJECT_TAIL_TRUNCATION` | Most likely failure; reject; flag SCC behavior in next QLoRA cycle. |
| First-line SHA mismatch | `REVISE_HEAD_DRIFT` | Investigate encoding/BOM; may be salvageable. |
| Trailing newline only | `REVISE_WHITESPACE` | Auto-fix (append `\n`), re-check. |
| Everything passes | `ACCEPTED` | Proceed to governance checks. |

## Interaction with the SCC Ingestion Directive

This contract extends `FORGE_DIRECTIVE_SCC_INGEST_20260422.md` gate step 2
("Hash integrity") into a six-field check. The Directive is amended to
reference this contract as the authoritative gate specification.

## Amendment

This contract is amended only by Sovereign decision logged to the BI
surface with rationale. Version increments (`v1` → `v2`).

---

**See also:**
- `missions/FORGE_DIRECTIVE_SCC_INGEST_20260422.md` (the ingestion Directive this contract governs)
- `context_vault/state/session_manifest_20260422.json` (integrity fields live here)
- `context_vault/bi/truncation_check.jsonl` (rejection log)
- `COUNCIL_CHARTER_v1.md §VIII` (constitutional alignment)
