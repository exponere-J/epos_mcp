# Voice-First Prompting — The Discipline

## 1. Why voice-first prompts are different

Typed prompts compress. You write "draft a 600-word essay with 3
supporting points and a CTA." Nine words. Precise. Typing rewards
compression.

Voice-first prompts don't compress, they **sequence**. You say, while
walking: "I want to write about something I've been thinking about for
a week. It's the idea that proprioception — like the physical sense —
matters more than reasoning for autonomous systems. Give me three
examples. Then an objection. Then a close."

The voice version is longer. But it's actually **more** information:
tone, rhythm, the order the ideas surface in, and — crucially — the
speaker's natural phrasing.

A model that flattens a voice prompt back into a typed prompt loses
most of that. A voice-optimized prompt pipeline preserves it.

## 2. The three principles

### Principle 1 — Preserve the rhythm

Don't strip filler words without checking. "You know" and "kind of" and
"I mean" can be filler, OR they can be the speaker's actual register.
If you strip them, the output stops sounding like the speaker.

Rule: only strip a filler word if it appears ≥ 3 times per minute AND
in positions where it's doing no work (mid-clause interruptions). Keep
all sentence-opening and sentence-closing fillers; they're part of the
speaker's voice.

### Principle 2 — Preserve the order

Voice thinkers arrive at the thesis by a specific route — often an
anecdote → realization → generalization sequence. Don't reorder for
logical elegance. Keep the discovery path the speaker took.

### Principle 3 — Preserve the vocabulary

Voice thinkers have a personal word-list they favor (and one they
dislike). If the speaker said "organism," don't swap "system." The
vocabulary is the voice.

## 3. The vocabulary-correction problem

Voice dictation systems mis-hear words in predictable ways. "Architect"
becomes "artifact." "Proprioception" becomes "prop receptor son." Your
transcripts end up with garbage tokens that pollute downstream prompts.

`VOCABULARY_CORRECTIONS.md` is a dictionary of the 50 most common
dictation errors + their correct spellings, ready to plug into a
find-and-replace pass over your transcripts.

Apply it before the transcript goes into any prompt. Otherwise the
model starts reasoning over garbage inputs.

## 4. How to use this pack

1. Record yourself speaking one of the 30 prompts. Don't read it; say
   it in your own words.
2. Transcribe (phone, Whisper, whatever).
3. Run the transcript through the vocabulary corrections.
4. Paste into your LLM of choice.
5. The output preserves your voice to a noticeably higher degree than a
   flat typed prompt.

The first time you do this, it'll feel awkward. By the fifth time, it's
fast. Many users report they stop typing prompts entirely within a
month.

## 5. What this pack does NOT do

- It doesn't replace your need for a transcription tool. Bring your own.
- It doesn't train a voice-specific model for you. The prompts work
  with any capable general model.
- It doesn't give you a voice-first UI. That's the Exponere Reader
  (different product, Chrome extension, patent-pending).
