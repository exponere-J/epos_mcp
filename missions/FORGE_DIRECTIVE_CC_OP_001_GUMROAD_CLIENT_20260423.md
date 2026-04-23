# FORGE DIRECTIVE — CC-OP-001 — Gumroad & Lemon Squeezy Client

**Issued by:** The Architect
**Assigned to:** The Forge (SCC) → Agent Zero
**Directive ID:** `FORGE_DIR_CC_OP_001_20260423`
**Constitutional Authority:** Articles V, VII, X, XIV, XVI §3
**Status:** Specified; execution pending Stage-C start

---

## Scope

Build `epos/commerce/gumroad_client.py` + `epos/commerce/lemon_squeezy_client.py` implementing the **Deployer** row of the Unified Registry. Primary path: platform APIs. Fallback: Playwright via BrowserUse arm with the `execCommand("insertText")` ProseMirror bypass.

## Files to create

1. `epos/commerce/__init__.py`
2. `epos/commerce/gumroad_client.py`
3. `epos/commerce/lemon_squeezy_client.py`
4. `epos/commerce/rich_text_shim.py` (shared ProseMirror bypass)
5. `context_vault/products/catalog.json` (initial empty {products: []})
6. `nodes/execution_arm/shims/prosemirror_bypass.py` (arm-side shim)

## Contract (Gumroad client)

```python
class GumroadClient:
    def list_product(self, product: Product) -> ListingReceipt: ...
    def update_price(self, product_id: str, price_usd: float) -> dict: ...
    def fetch_sales(self, since: datetime) -> list[Sale]: ...
    def update_description(self, product_id: str, markdown: str) -> dict: ...

class ListingReceipt:
    product_id: str
    live_url: str
    created_at: str
    path_used: Literal["api", "playwright_fallback"]
    sha256_of_source: str   # idempotency key
```

## Execution order per list_product call

1. Try Gumroad v2 API: `POST /products` with title, price, files.
2. If 2xx → success; write to catalog.json; emit `product.shelf.implanted`.
3. If API fails OR the product needs rich-text description → fallback to Playwright:
   - Use the BrowserUse headed arm (operator-observable)
   - Navigate to creator dashboard
   - Fill form; on the description field, use `execCommand("insertText", false, markdown)` to bypass ProseMirror's normal paste restrictions
   - Save; capture the new product URL
   - Emit same receipt with `path_used="playwright_fallback"`
4. Either path writes to `context_vault/products/catalog.json`

## ProseMirror bypass snippet (the research key)

```javascript
// injected via playwright page.evaluate()
const desc = document.querySelector('[contenteditable="true"].ProseMirror');
desc.focus();
document.execCommand("insertText", false, MARKDOWN_TEXT);
// Alternative if execCommand is deprecated in the target browser:
// Dispatch a 'beforeinput' event with inputType='insertFromPaste'
// and data=MARKDOWN_TEXT, then a 'paste' event.
```

## Governance gates

- Deletion gate applies to `delete_product(product_id)` path. Never deletes without Sovereign approval.
- Atomic catalog.json writes via `.partial → fsync → rename`.
- Secret scan on responses (credentials must not leak into catalog).

## Environment

- `GUMROAD_API_KEY` (Gumroad v2 — Bearer token)
- `LEMON_SQUEEZY_API_KEY` (Lemon Squeezy v1)
- `GUMROAD_STORE_URL` (for Playwright fallback)

## Verification

1. `from epos.commerce.gumroad_client import GumroadClient; c = GumroadClient()`
2. `c.list_product(Product(title="Test", price_usd=9.99, file_path="..."))` returns a ListingReceipt.
3. Catalog.json contains a new row with matching product_id.
4. `product.shelf.implanted` event fires.

## Out of scope

- Etsy client (separate directive; OAuth 1.0a complexity).
- Stripe direct checkout (Tier 2 service marketplace, not Stage-1).

## Rollback

`delete epos/commerce/` + `git restore context_vault/products/catalog.json`.

## Dependencies / prerequisite Directives

- CC-OP-002 Session Keeper (for Playwright session state) — REQUIRED before fallback path works.
- BUILD 26 Execution Arm — DONE.
