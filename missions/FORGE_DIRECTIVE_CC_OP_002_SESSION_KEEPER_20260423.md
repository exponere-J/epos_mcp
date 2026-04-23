# FORGE DIRECTIVE — CC-OP-002 — Session Persistence Layer

**Directive ID:** `FORGE_DIR_CC_OP_002_20260423`
**Constitutional Authority:** Articles V, VII, X, XIV, XVI §3

---

## Scope

Build `epos/commerce/session_keeper.py` — a Playwright `storage_state` manager that persists authenticated sessions for Gumroad, LinkedIn, Etsy, and any future platform. Sessions are per-Sovereign artifacts; live at `context_vault/secrets/sessions/<platform>.json` (gitignored).

## Contract

```python
class SessionKeeper:
    def capture_session(self, platform: str, browser_context) -> Path:
        """Dump playwright browser_context.storage_state() → JSON file."""
    def restore_session(self, platform: str, browser_context) -> bool:
        """Apply stored state to a fresh context; return True on success."""
    def expires_in_days(self, platform: str) -> int:
        """Estimate remaining session lifetime (platform-specific heuristic)."""
    def re_auth_if_stale(self, platform: str) -> bool:
        """If expired, emit 'session.expired.<platform>' event for Sovereign re-auth."""
```

## Files

1. `epos/commerce/session_keeper.py`
2. `context_vault/secrets/sessions/.gitkeep` (directory marker)
3. `context_vault/secrets/sessions/_schema.md` (documents the JSON shape)

## Gitignore updates

```
context_vault/secrets/
!context_vault/secrets/.gitkeep
!context_vault/secrets/_schema.md
```

## Platform-specific expiry heuristics

- **Gumroad:** ~30 days (cookie lifetime)
- **LinkedIn:** ~14 days (tight)
- **Etsy:** ~7 days (very tight; re-auth often)

## Verification

1. `keeper = SessionKeeper()`
2. `keeper.capture_session("gumroad", ctx)` writes JSON to expected path.
3. `keeper.restore_session("gumroad", fresh_ctx)` returns True and the context has the cookies.
4. On expired session, `session.expired.gumroad` event fires.

## Governance

- Session files NEVER enter git (gitignored).
- Schema doc DOES enter git so new platforms inherit the same pattern.
- No deletion of session files without deletion_gate approval.

## Out of scope

Platform-specific login automation (that's future directives per platform).
