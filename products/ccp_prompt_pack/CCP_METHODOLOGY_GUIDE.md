# The Concentric Context Protocol (CCP)

## Stop Sending Flat Prompts. Start Engineering Context.

---

## 1. The problem with flat prompts

A flat prompt is one that treats every word the model sees as equal
signal. Mostly it isn't. The model's attention allocates differently
depending on where in the prompt a concept appears and how it's framed.
A concept embedded in a section header pulls more weight than the same
concept buried in a bullet point. A token that appears once in isolation
is noisier than the same token appearing in a well-defined context.

Flat prompts ignore this. They pile everything in — backstory, audience,
constraint, task, examples — and hope the model sorts it out. Sometimes
it does. Usually what you get is output that's on-topic but generic,
misses your constraints, and doesn't sound like you.

**CCP is a discipline for separating the layers so the model reasons
better.**

## 2. The four rings

Every piece of context lives in one of four concentric rings. Inner
rings constrain outer rings. Rings are not nested prompts; they're
parsing layers that determine how the model weighs signals.

```
 ┌───────────────────────────────────────────┐
 │ 1. DOCUMENT                                │
 │   The whole: what kind of artifact this is │
 │    ┌────────────────────────────────────┐  │
 │    │ 2. SECTION                          │  │
 │    │   Subdivision: what function here  │  │
 │    │    ┌─────────────────────────────┐  │  │
 │    │    │ 3. STATEMENT                │  │  │
 │    │    │   Clause: one assertion     │  │  │
 │    │    │    ┌────────────────────┐   │  │  │
 │    │    │    │ 4. TOKEN           │   │  │  │
 │    │    │    │   Word or phrase   │   │  │  │
 │    │    │    └────────────────────┘   │  │  │
 │    │    └─────────────────────────────┘  │  │
 │    └────────────────────────────────────┘  │
 └───────────────────────────────────────────┘
```

### Ring 1 — Document

The document ring says **what the artifact is**. Is this a strategic
plan? A one-pager? A pitch? A post-mortem? The document type sets the
genre conventions the model imitates.

> A prompt that opens "Write a 500-word blog post" is a document-ring
> prompt. A prompt that opens "You are writing the 'how we won' section
> of a case study" is a section-ring prompt. These produce different
> tonal registers because the ring differs.

### Ring 2 — Section

The section ring says **what function the passage serves within the
document**. Intro? Thesis? Rebuttal? Methodology? Conclusion?

Sections carry local conventions. A thesis section is declarative; a
methodology section is procedural; a conclusion section reframes. The
model matches register to section.

### Ring 3 — Statement

The statement ring is **one assertion at a time**. A well-formed
statement has a subject, a claim, and (optionally) a qualifier. Flat
prompts bury statements inside bullet lists and paragraphs where the
model can't distinguish which is the primary claim.

CCP requires you to separate them. One statement per line. The primary
claim gets its own line. Qualifiers hang off it, also as separate
lines.

### Ring 4 — Token

The token ring is **the smallest signal**. Word choice, register,
vocabulary preferences. A single well-chosen token ("sovereign" vs
"user") shifts the model's entire frame.

Tokens are also where **homographs** live — words that carry multiple
meanings (bank, plane, novel). Homograph resolution is the token ring's
specialty.

## 3. Worked example — flat vs CCP

### Flat prompt (bad)

```
Write a LinkedIn post about how small businesses can use AI to grow.
Make it engaging and sound like a founder. Include a hook, a story,
and a call to action. Don't use jargon.
```

Result: a generic LinkedIn post that sounds like every other
AI-for-small-business post. Too on-topic to stand out.

### CCP-structured prompt (good)

```
# Document
# This is a LinkedIn post from a founder with a vision problem who built
# a business-ops platform because they couldn't read a screen for long.

# Section — Hook
# Opens with a concrete, embodied moment. First-person. Present tense.
# No mention of AI in the opening line.

# Section — Story
# 3–5 short paragraphs. Problem → constraint → what the constraint
# revealed. Must include a specific detail (time, place, tool) that
# outsiders wouldn't guess.

# Section — Thesis
# The system you built IS the lesson. Not "AI helped me" — "I built an
# organism, and the organism now runs the business I couldn't run
# manually." One sentence.

# Section — Call to action
# Not "DM me" or "link in bio." Invite someone who's felt the same
# constraint. Use the word "constraint," not "challenge."

# Tokens
# Prefer: organism, system, sovereign, discipline, constraint
# Avoid: leverage, actually, game-changer, powerful, unlock
```

Result: a LinkedIn post that sounds like one person, not a template.
The model's attention is directed by ring.

## 4. Homograph disambiguation (token ring)

Homographs are tokens that mean different things in different contexts.
The model can resolve them if you give it context — but only if you
signal which meaning you want.

Examples:

| Token | Meaning A | Meaning B | Disambiguator |
|---|---|---|---|
| bank | financial institution | river edge | "the river bank" / "the federal bank" |
| plane | aircraft | geometric surface | "an aircraft plane" / "a Cartesian plane" |
| novel | book | previously-unseen | "a novel by Hemingway" / "a novel approach" |
| sovereign | monarch | self-governing | "a sovereign king" / "a sovereign organism" |

CCP says: name the meaning explicitly in the surrounding statement when
the token is ambiguous. Don't rely on the model to guess.

## 5. When to use which ring

| Problem | Ring to edit |
|---|---|
| Output is off-genre (blog looks like an academic paper) | Document |
| Output is on-topic but flat/generic | Section (add function labels) |
| One claim out of many is wrong | Statement (isolate and re-phrase) |
| Tone / register is off | Token (swap vocabulary) |
| Model confuses two meanings of a word | Token (disambiguate) |

## 6. The CCP workflow (one pass)

1. **Write the prompt flat first.** Don't try to be structured on the
   first draft. Get the intent out.
2. **Label the rings.** Go through and tag every line: `[D]`, `[S]`,
   `[St]`, or `[T]`. Some lines are multi-ring.
3. **Separate by ring.** Move every `[T]` line to a TOKEN section,
   every `[St]` to STATEMENT, and so on. Use headers.
4. **Check homographs.** Any ambiguous token gets a disambiguator in
   its surrounding statement.
5. **Send it.** Compare output to the flat version. The structured
   version almost always wins on concreteness and voice.

## 7. What CCP doesn't fix

- A confused intent. If you don't know what you want, CCP won't find it.
- Insufficient subject-matter grounding. CCP organizes what you know;
  it doesn't invent what you don't.
- A bad model. CCP works with capable models. Underpowered models
  flatten the rings back into mush.

## 8. The templates

The 20 templates in `templates/` apply CCP to five recurring use cases:

1. **Strategic intent extraction** — you have a transcript, you need a
   strategic summary. 4 templates.
2. **Audience modeling** — you have a product, you need buyer avatars.
   4 templates.
3. **Content production** — you have a thesis, you need a piece. 4
   templates.
4. **Post-mortem diagnostics** — something broke, you need a clean AAR.
   4 templates.
5. **Voice → structure** — you dictated something, you need it
   organized. 4 templates.

Each template is annotated with which ring it's optimizing and why.

---

*Produced by EPOS. 1% daily. 37x annually.*
