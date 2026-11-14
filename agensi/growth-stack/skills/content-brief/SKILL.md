---
name: content-brief
description: >
  Writes a content brief for one piece: the query and intent, the reader, an outline where every heading answers a real
  question, sources, internal links, voice and a success measure, then checks a draft against it. Use when the user says "write
  a content brief for [topic]", "outline an article for [keyword]", "brief a writer on this", "what should this post cover" or
  "check this draft against the brief". Do not use for grouping keywords (use `keyword-clusters`), rewriting a live page's
  snippet (use `on-page-seo`), landing-page conversion copy (use `landing-page-copy`) or writing the article itself.
---

# Content brief

Requires: Python 3.10+. `text_stats.py` is offline, makes no network calls and reads one text file or stdin.

A brief is a decision list. It says what the piece is for, who reads it, what it must answer and how we will know it worked.
I keep it to one page because writers read one page.

## Inputs

- The primary keyword and its cluster (from `keyword-clusters` if there is one) and the intent.
- The reader and what they will do next. The one action the piece supports.
- 3 to 5 pages that already answer the question (the user names them or pastes them), and the user's own facts and sources.

## Running the script

Write `shared/scripts/text_stats.py` unchanged to a temporary file, run it on the outline or the draft, then delete it:

```sh
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/text_stats.XXXXXX")"   # paste shared/scripts/text_stats.py into it, unchanged
python3 "$SCRIPT" draft.md --keyword "primary phrase" --keyword "supporting phrase" --json
rm -f "$SCRIPT"
```

Exit 0 is success. Exit 2 means a missing file, empty or binary input or a bad option.

## Steps

1. State the job: one sentence, "After reading this, the reader can ___."
2. Name the intent (informational, commercial, transactional) and the reader's starting knowledge.
3. Read the reference pages. List what they all cover, what they miss and what they get wrong. The gap is the angle.
4. Build the outline with [the template](references/brief.md): an H1, then four or more H2s, each phrased as the question it
   answers, with a target length, the evidence it needs and its source.
5. List entities and terms the piece must define, and facts that need a source. Mark unsourced ones "needs source".
6. Set 3 or more internal link targets with the anchor text and where each fits.
7. Write voice rules from the user's existing writing. Include 3 phrases to use and 3 to avoid.
8. Set the single call to action, the word range for the whole piece and the measure (which event, which page, how long to wait), with `measurement-plan`.
9. When a draft exists, run `text_stats.py` and compare: required terms present, outline matches, reading ease within range.

## Output

The filled brief from the template, then, if a draft was supplied, a short check: coverage against the outline, keyword
placement, readability, and a list of claims still missing sources.

## Exit criteria

- [ ] The job is one sentence and the intent is named.
- [ ] The outline has an H1 and at least four H2s, each mapped to a question and a source or "needs source".
- [ ] At least three internal link targets have anchors.
- [ ] There is one call to action, a word range and a success measure.
- [ ] For a draft: every H2 in the outline appears, the primary phrase is in the title, an H2 and the first 100 words.

## Edge cases and errors

- The user has no reference pages: ask for them. Do not invent what competitors say.
- Two intents in one topic: split into two briefs.
- A thin topic that fits in 300 words: say so and brief a short piece, not a padded one.
- A topic that needs expert knowledge the user lacks: name the expert needed and what to ask them.
- `text_stats.py` exits 2: report the message, fix the file and re-run.
- A claim with no source: leave it in the brief marked "needs source"; never fill it with a made-up figure.

## Rules

- Every H2 answers a question a reader really asks.
- No invented statistics, quotes or sources.
- Do not tell the writer to hit a keyword density. Tell them where the phrase belongs.
- Brief the reader's need, not the search engine's.
