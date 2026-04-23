# Quick Start — Your First CCP Prompt in 30 Minutes

---

## Step 1: Pick something you're currently stuck on (5 min)

Not a toy example. A real thing. The prompt you've been fighting for
two days that produces mush.

Open the prompt you have. Paste it into a scratch file. We're going to
work on it.

## Step 2: Read the 4-ring explainer (5 min)

Open `CCP_METHODOLOGY_GUIDE.md`. Read sections 2 and 3 carefully.

Important: do not skip ring 3 (statement). It's where most flat prompts
rot.

## Step 3: Label your prompt (10 min)

Go through your prompt line by line. For each line, tag it with the
ring it belongs to:

- `[D]` — Document ring (what the artifact is)
- `[S]` — Section ring (what function it serves within the artifact)
- `[St]` — Statement ring (an assertion)
- `[T]` — Token ring (a word-choice or vocabulary preference)

Most flat prompts have 80% `[St]` lines mixed with 20% `[S]` lines and
no `[D]` at all. That's typical.

## Step 4: Rewrite with ring separation (7 min)

Add a `# DOCUMENT` heading and pull all `[D]` content under it (if you
didn't have any, write one). Then `# SECTION`, `# STATEMENT`, `# TOKEN`.

Each line gets its own bullet or its own line. No dense paragraphs.

## Step 5: Send both versions side by side (3 min)

Send the flat version first, note what the model produced.

Send the CCP version.

The CCP version should:
- Match your genre conventions better (tighter on-genre).
- Hit your specific constraints (not just the generic ones).
- Sound more like you, less like "generic AI writer."

If it doesn't — you probably have a ring imbalance. The most common
problem is too much statement, not enough section.

## Troubleshooting

| Symptom | Likely ring issue |
|---|---|
| Output is off-genre (too academic / too casual) | Missing or weak Document ring |
| On-topic but flat | Sections aren't labeled by function |
| Claims are right but tone is wrong | Token ring needs vocabulary preferences |
| Output confuses two meanings of a word | Homograph in Token ring — add disambiguator |

## Next

Pick a template from `templates/` that matches a recurring use case for
you. Adapt it. Run it three times with different inputs. You'll feel
the discipline start to click by run three.

---

*30 minutes to your first structured prompt. The next 30 days compound.*
