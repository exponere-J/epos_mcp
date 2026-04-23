# EXPONERE / EPOS Website — 5-Page Scaffold

**BUILD 59** — Cloudflare Pages-ready static site. 5 pages, minimal JS,
dark-first, optimized for the Sovereign's actual voice (no fluff).

## Pages

1. `index.html` — Home
2. `services.html` — Services (Tiers 1–3)
3. `about.html` — Founder / Origin / Story
4. `case_study.html` — PGP case study (template)
5. `contact.html` — Contact + Cal.com embed

## Deploy

```bash
# Cloudflare Pages
npx wrangler pages deploy .

# Or push to GitHub → Cloudflare Pages auto-deploys from the branch.
```

## Design notes

- Dark canvas default (`#0A1628` background, `#F5B642` accent)
- Typography: system font stack (no web-font bloat)
- Images: use WebP; hosts Sovereign assets under `./assets/`
- All copy reflects Brand DNA profile (see `products/brand_dna_kit/examples/epos_brand_dna.md`)

## Cal.com embed (contact.html)

Set `CAL_USERNAME` in `config.js` before deploy.

## Analytics

Uses self-hosted Plausible (no Google Analytics). Set
`PLAUSIBLE_DOMAIN` in `config.js`.
