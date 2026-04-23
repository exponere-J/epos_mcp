# Vocabulary Correction Dictionary — 50 Common Dictation Errors

*Apply this as a find-and-replace pass over transcripts before they
enter any LLM prompt. Ordered by frequency of occurrence.*

---

## Technical vocabulary

| Misheard | Intended |
|---|---|
| artifact | architect |
| prop receptor son | proprioception |
| Bridge Ah | bridge (architectural) |
| dock her | Docker |
| cheetah see | CCP |
| Fry Day | Friday |
| tee-tell-gee / TTT | TTLG |
| e-pose / epoch | EPOS |
| shop reven | sovereign |
| councel | council |
| node | node (accept "knowed" variant) |
| coded speaker | code speaker |
| prod aid | prototype |
| rest ful | RESTful |
| JSON yay | JSON |

## Business vocabulary

| Misheard | Intended |
|---|---|
| care ware | care wear (no) — should be "careware" (jargon) |
| foyer stream | four-stream |
| flywheel | flywheel (accept; verify capitalized) |
| shelving intelligence | swarm intelligence |
| cleans | clients |
| revenue stream | revenue stream (accept) |
| broad strat | broad strategy |
| Go to | go-to |
| mark kit | market |
| on boarding | onboarding |

## Names / proper nouns

| Misheard | Intended |
|---|---|
| Lulu | LuLu |
| Jamie pure dew | Jamie Purdue |
| exponent ray | EXPONERE |
| Gum road | Gumroad |
| Linked In | LinkedIn |
| Note book LM | NotebookLM |
| Open Router | OpenRouter |
| Lemon Squeeze Eee | Lemon Squeezy |
| Sky Pool / Skull | Skool |
| af fine / uff fine | AFFiNE |
| Hen tzner | Hetzner |
| Fire craw | Firecrawl |
| Browser use | BrowserUse |
| Computer use | ComputerUse |

## Action verbs

| Misheard | Intended |
|---|---|
| commit it | commit |
| push us | push |
| merge | merge (accept) |
| fit | fix |
| dip low | deploy |
| log it | log (accept; check context) |
| re factor | refactor |
| abs tracked | abstracted |
| or cast rate | orchestrate |

## Punctuation cues (speaker actually says)

| Spoken | Intended |
|---|---|
| period | . |
| comma | , |
| new paragraph | \n\n |
| new line | \n |
| colon | : |
| semicolon | ; |
| open paren | ( |
| close paren | ) |
| dash / em-dash | — |
| quote | " |
| close quote | " |

---

## How to apply

```bash
# One-liner Python:
python3 -c "
import json, re, sys
corrections = [...]  # load from JSON
text = sys.stdin.read()
for bad, good in corrections:
    text = re.sub(r'\b' + re.escape(bad) + r'\b', good, text, flags=re.IGNORECASE)
print(text)
" < transcript.txt > clean.txt
```

Or paste the dictionary into a spreadsheet + find/replace tool like
`sed` / a VS Code find-replace regex.
