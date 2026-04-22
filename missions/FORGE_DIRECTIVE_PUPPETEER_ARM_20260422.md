# FORGE DIRECTIVE — PUPPETEER STEALTH ARM (2026-04-22)

**Issued by:** The Architect
**Assigned to:** The Forge (Desktop Code) → Agent Zero
**Constitutional Authority:** Articles V, VII, X, XIV, XVI §3
**Directive ID:** `FORGE_DIR_PUPPETEER_ARM_20260422`
**Status:** Specified; build pending Sovereign prioritization

---

## Scope

Add a **Puppeteer stealth arm** as a fifth variant in `nodes/execution_arm/`
that serves as automatic fallback when Playwright-based BrowserUse is
detected/blocked by anti-bot systems.

## Why Puppeteer (not just a Playwright stealth config)

Playwright's stealth ecosystem is immature relative to Puppeteer's.
`puppeteer-extra` + `puppeteer-extra-plugin-stealth` is the battle-tested
anti-fingerprinting layer. Rather than reimplement, wrap it and keep
BrowserUse's Playwright backend unchanged for the non-blocked majority
of tasks.

## Files to create (~350 LOC total)

1. **`nodes/execution_arm/puppeteer_arm.py`** — Python side. Node subprocess
   wrapper. Task goes in via JSON stdin; Puppeteer driver emits JSON stdout.
2. **`nodes/execution_arm/puppeteer_driver.js`** — Node side. Imports
   `puppeteer-extra` + stealth plugin; executes the task; returns result.
3. **`containers/agent-zero/Dockerfile`** — append: install Node.js 20,
   npm install `puppeteer puppeteer-extra puppeteer-extra-plugin-stealth`.
4. **`nodes/execution_arm/mode_selector.py`** — extend variant list:
   `browser_use.*` now has a `browser_use.puppeteer` variant; reasoner
   promotes to puppeteer on:
   - retry-after-blocked signal (prior browser_use run returned 403/anti-bot markers)
   - `context["stealth_required"] = True`
   - target domain in `STEALTH_DOMAINS` env var (comma-separated)

## Auto-fallback rule

When a BrowserUse (Playwright) run ends with an error matching
`/cloudflare|perimeterx|datadome|bot.?detect|challenge|captcha/i` or an HTTP
status in {403, 429, 503}, the callable transparently re-runs the same
task through the Puppeteer arm. The receipt records both attempts.

## Deletion governance

Puppeteer arm reuses the same `deletion_gate.enforce` before any
destructive web action (listing delete, record purge on a web app).
No special carve-out.

## Verification

- `docker compose build agent-zero && docker compose up -d agent-zero`
- `curl -X POST localhost:50080/api/execute -d
   '{"task":"Scrape a Cloudflare-protected page at <URL>", "mode_hint":"browser_use.puppeteer"}'`
  → receipt contains `arm: "browser_use.puppeteer"` and success.
- Intentional-block test: hit a known-hostile page via Playwright first
  (expect block), confirm auto-fallback fires and succeeds with Puppeteer.

## Out of scope

- Captcha-solving services (2Captcha, Anti-Captcha). Those are a future
  directive gated on Sovereign approval of paid third-party calls.
- Mobile emulation profiles (future directive).
