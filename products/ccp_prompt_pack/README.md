# CCP Pack — Stop Sending Flat Prompts

**Version:** 1.0
**Platform:** Gumroad
**Price (test points):** $19 / $29 / $39 / $49
**Status:** v1.0 (pre-launch)

---

## What this is

A 4-ring methodology guide plus 20 battle-ready prompt templates. Stop
sending flat, generic prompts. Start engineering context the way the
model actually uses it.

## What's inside

1. **CCP Methodology Guide** (`CCP_METHODOLOGY_GUIDE.md`)
   The four rings (Document, Section, Statement, Token); how to decide
   which ring a concept lives in; side-by-side flat-prompt-vs-structured
   rewrites with before/after outputs; homograph disambiguation
   (e.g., `bank` as a financial institution vs. as a river edge).

2. **Prompt Template Library** (`templates/`, 20 templates, 5 categories)
   Drop-in templates for: strategic intent extraction, audience modeling,
   content production, post-mortem diagnostics, voice-to-structure.

3. **Quick-Start** (`QUICK_START.md`)
   Thirty minutes from zero to your first structured prompt, with a
   specific worked example.

## Who this is for

- Solo founders tired of prompts that produce generic output
- Consultants who need polish their clients can see
- Growth teams running prompt A/B tests at scale
- Anyone who's felt "the model could be so much better if I knew how"

## What makes this different

Most prompt packs sell incantations. This pack teaches a **parsing
discipline**: every prompt has 4 concentric rings, and the model reasons
better when you separate them. The templates are the output of applying
that discipline to the 20 highest-leverage use cases we've encountered
in two years of shipping.

## License

Personal / single-team use. Contact the author for reseller or agency
licensing.

## Build the PDFs

```bash
bash BUILD_PDF.sh
```

Requires one of: `pandoc`, `weasyprint`, or `wkhtmltopdf`. See
`BUILD_PDF.sh` for details.
