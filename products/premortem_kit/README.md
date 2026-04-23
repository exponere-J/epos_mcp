# Pre-Mortem Kit — Five Documents + Doctor

**Version:** 1.0
**Platform:** Gumroad
**Price (test points):** $29 / $49 / $79 / $99
**Status:** v1.0 (pre-launch)

---

## What this is

The Pre-Mortem Kit is the governance foundation we use to prevent
deployment failures before they happen. Five constitutional documents,
one unified framework guide, and a reference to `epos_doctor.py` — the
script that enforces the rules automatically.

This is not theory. These documents are load-bearing infrastructure for
a live sovereign-intelligence platform (EPOS). They've been stress-
tested against real production failures and iterated for two years.

## What's inside

1. **PRE_MORTEM_FRAMEWORK.md** — a unified 15-minute read that
   explains how the five documents work together. Read this first.

2. **`constitutional/`** — the five documents themselves:
   - `01_EPOS_Constitution.md` — the root rules for an autonomous system
   - `02_Failure_Scenarios.md` — a catalog of failure patterns and their
     recovery procedures
   - `03_Path_Clarity_Rules.md` — the discipline that eliminates the
     single most common class of deployment failure (path mixing)
   - `04_Pre_Flight_Checklist.md` — the go/no-go list for any
     deployment or significant operation
   - `05_Environment_Spec.md` — the contract between your code and the
     environments it runs in

3. **`EPOS_DOCTOR_REFERENCE.md`** — explains `epos_doctor.py`: what it
   checks, how to run it, how to extend it with your own checks.

## Who this is for

- Founders who've lost a week to a deploy-gone-wrong
- Technical leads who want a governance layer they can point their team at
- Consultants who need a credibility artifact to bring to clients
- Anyone who's felt the pain of "we didn't catch that in review"

## What makes this different

Most post-mortem templates are reactive. This kit is **pre-emptive**.
The five documents encode the constraints that prevent failure modes
from landing in the first place. The Doctor is the enforcement layer.

Together, they turn tribal knowledge ("remember last time we shipped
on a Friday?") into constitutional rules ("deploys require a pre-flight
checklist run; the Doctor refuses to proceed without one").

## License

Personal / single-team use. Reseller and agency licensing: contact the
author.

## Build the PDFs

```bash
bash BUILD_PDF.sh
```

Requires `pandoc` (+ optionally `weasyprint` for nicer styling).
