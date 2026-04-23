# FORGE DIRECTIVE — CC-OP-005 — Echolocation Measurement Agent

**Directive ID:** `FORGE_DIR_CC_OP_005_20260423`
**Constitutional Authority:** Articles V, X, XVI §2

---

## Scope

Build `epos/commerce/echolocation_agent.py` — scrapes platform metrics at T+24h (and T+48h, T+7d, T+30d optionally) via accessibility-tree navigation. Feeds the Reward Bus so MiroFish's Cycle 1 score can be compared to real market outcome.

## Files

1. `epos/commerce/echolocation_agent.py`
2. `context_vault/echolocation/runs/` (per-product measurement history)
3. `context_vault/echolocation/comparison/` (MiroFish-predicted vs observed deltas)

## Contract

```python
class EcholocationAgent:
    async def measure(self, product_id: str, platform: str,
                       window_hours: int = 24) -> Measurement:
        """Scrape current metrics; compare to T+0 baseline."""
    def compare_to_prediction(self, product_id: str) -> PredictionDelta:
        """Look up MiroFish prediction for product; compute delta."""
    def schedule_follow_ups(self, product_id: str) -> None:
        """Queue T+48h, T+7d, T+30d measurements."""

class Measurement:
    product_id: str
    platform: str
    window_hours: int
    metrics: dict   # views, sales, revenue, average_rating, review_count
    observed_at: str
    accessibility_tree_hash: str   # audit: what did we see
```

## Why accessibility tree, not DOM

Platform UIs change frequently; DOM selectors break. The accessibility tree is more stable and describes user-visible structure. Playwright's `page.accessibility.snapshot()` returns a structured tree we can query by role + name.

## Example — Gumroad metrics extraction

```python
snap = await page.accessibility.snapshot()
# Find the stats section by role="region" name="Product stats"
# Then traverse for "Sales" / "Views" / "Revenue" entries
```

## Reward Bus integration

```python
from epos.rewards.reward_aggregator import emit_signal
emit_signal({
    "type": "product.conversion.delta",
    "product_id": product_id,
    "window": window_hours,
    "observed": observed_metrics,
    "predicted": mirofish_prediction,
    "delta": delta,
})
```

At T+90d, Reward Bus uses the accumulated deltas to score whether MiroFish's Cycle 1 prediction was calibrated.

## Verification

1. Mock a product listing; run `measure("test_id", "gumroad", 24)`.
2. Verify an accessibility-tree snapshot is stored.
3. Verify a `product.conversion.delta` event fires with non-zero delta vs. MiroFish prediction.

## Dependencies

- CC-OP-002 Session Keeper
- BUILD 26 Execution arm (BrowserUse)
- MiroFish run registry (for prediction lookup)
