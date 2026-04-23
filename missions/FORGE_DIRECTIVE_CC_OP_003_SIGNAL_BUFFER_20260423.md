# FORGE DIRECTIVE — CC-OP-003 — SQLite Signal Buffer

**Directive ID:** `FORGE_DIR_CC_OP_003_20260423`
**Constitutional Authority:** Articles V, VII, X, XVI §2

---

## Scope

Build `epos/traffic/signal_buffer.py` — the **Gatekeeper** of the pipeline. Ingests raw FOTW + Oracle + Sentinel signals; deduplicates via nomic-embed; scores priority; gates which signals advance to Synthesis.

## Files

1. `epos/traffic/__init__.py`
2. `epos/traffic/signal_buffer.py`
3. `epos/traffic/schema.sql`
4. `context_vault/intelligence/PIPELINE_STAGE_MATRIX.md` (renders from buffer state)

## Contract

```python
class SignalBuffer:
    def ingest(self, signal: Signal) -> IngestReceipt:
        """Insert or merge (if dedup threshold met)."""
    def top_n(self, n: int = 10) -> list[Signal]:
        """Return highest-priority pending signals."""
    def mark_advanced(self, signal_id: str, to_phase: str) -> None:
        """Record that a signal advanced to Synthesis/Fortification/etc."""
    def render_matrix(self) -> str:
        """Regenerate PIPELINE_STAGE_MATRIX.md from current buffer."""
```

## Schema (schema.sql)

```sql
CREATE TABLE IF NOT EXISTS signals (
  signal_id TEXT PRIMARY KEY,
  verbatim TEXT NOT NULL,
  source_platform TEXT NOT NULL,
  source_url TEXT,
  source_author TEXT,
  signal_type TEXT,
  confidence REAL NOT NULL,
  frequency INTEGER NOT NULL DEFAULT 1,
  priority_score REAL NOT NULL,
  pain_magnitude REAL NOT NULL,
  source_diversity INTEGER NOT NULL DEFAULT 1,
  current_phase TEXT NOT NULL DEFAULT 'sensing',
  embedding BLOB,
  created_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);
CREATE INDEX idx_signals_priority ON signals(priority_score DESC);
CREATE INDEX idx_signals_phase ON signals(current_phase);
```

## Dedup algorithm

1. Embed verbatim via nomic-embed-text (768-d)
2. Cosine-sim against last 30 days of embeddings
3. If max > 0.92 → merge: increment frequency, widen source_diversity, recompute priority
4. Else insert

## Priority formula

```
priority = (pain_magnitude × 0.4)
         + (log2(frequency + 1) × 0.3)
         + (confidence × 0.2)
         + (min(source_diversity, 5) / 5 × 0.1)
```

Range 0–1. Multiply by 10 for the matrix display.

## Verification

1. Insert 3 near-duplicate signals → only 1 row, frequency=3, source_diversity=3.
2. Insert a distinct signal → 2 rows total.
3. `top_n(1)` returns the highest-priority row.
4. `render_matrix()` produces a markdown table with columns: phase, count, avg_priority, top_signal.

## Dependencies

- nomic-embed-text (existing in the EPOS embedding pipeline)
- sqlite3 (stdlib)
