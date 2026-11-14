---
name: ai-search-readiness
description: >
  Measures and improves how likely AI answer engines are to quote a page: clear short answers under question headings,
  named entities, dated and sourced claims, extractable structure and crawl access. Use when the user says "will AI assistants
  cite my page", "optimise this for AI search", "make my content quotable in AI answers", "how do I get quoted in AI answers" or "why
  isn't my page used in AI answers". Do not use for classic title and meta work (use `on-page-seo`), writing JSON-LD (use
  `structured-data`), site-wide crawl problems beyond crawler access (use `technical-seo-audit`) or promising citations, which nobody can.
---

# AI-search readiness

Requires: Python 3.10+ and network access to the live page and its site. No accounts, keys or installs.

I measure inputs, never outputs. Nobody can promise a citation. What I can check is whether the page gives an answer
engine something clean to quote and whether the crawlers are allowed in.

## Inputs

- The page URL and the three questions a buyer asks that this page should answer.
- The owner's policy on each AI or data crawler: allowed, blocked, undecided.

## Running the scripts

Write each script (`shared/scripts/page_audit.py`, `shared/scripts/site_probe.py`) unchanged to a temporary file, run it, then delete it. Both use the network only to read the site you
name (`page_audit.py` the one page; `site_probe.py` its `robots.txt`, sitemaps and a small sample of pages), and both read no
local files.

```sh
A="$(mktemp "${TMPDIR:-/tmp}/page_audit.XXXXXX")"; S="$(mktemp "${TMPDIR:-/tmp}/site_probe.XXXXXX")"
python3 "$A" https://example.com/page --json     # checks "answers", "authority" and "schema"
python3 "$S" https://example.com/page --sample 5 --json   # crawler rules for this path
rm -f "$A" "$S"
```

Exit 0, 1 and 2 mean no high gap, a high or critical gap (or an unreachable site), and bad input.

## Steps

1. Run both scripts. Read the `answers`, `authority` and `schema` checks and the `rules` table from the probe.
2. List each buyer question. Mark whether the page has it as a heading, and whether the next paragraph answers it in 8 to 60
   words (a heuristic: short answers are easier to quote). Use [the answer patterns](references/answers.md).
3. Rewrite weak answers: lead with the answer, then the reason, then the caveat. Keep numbers only if the user supplied them.
4. Define the entities in the first paragraph: who you are, what the thing is, where, for whom. Use the same names everywhere.
5. Attach every claim to a source: link the primary source, or remove the claim. Add a named author and a visible date.
6. Make facts extractable: a list for steps, a table for specs, plain text for answers. Do not hide answers in tabs, images or scripts.
7. Check access: for each crawler in `rules`, report allowed or blocked and the rule. Do not change policy without the owner.
8. Re-run both scripts and compare.

## Output

A table of buyer questions with heading present, answer length and verdict; the rewritten answers; the sources added; the
entity list; the crawler-access table with the owner's decision; the audit parts before and after; and what cannot be measured.

## Exit criteria

- [ ] At least two question headings each followed by a paragraph of 8 to 60 words, so both "answers" parts are earned.
- [ ] Every statistic or claim has a linked source or was removed.
- [ ] An author and a date are visible and in markup.
- [ ] Each AI or data crawler is recorded as allowed or blocked by the owner's decision.
- [ ] The page is indexable and its snippets are not blocked.
- [ ] The final report says it measures inputs and promises no citation.

## Edge cases and errors

- Content only appears after a click, a scroll or a script run: the audit cannot see it, and neither may a crawler. Say so.
- Answer needs a long explanation: give the short answer first, then link or place the detail below it.
- Opinion or comparison pages: label opinion as opinion; do not source-wash it.
- Page behind a login or PDF only: this skill does not apply until a public HTML version exists.
- A crawler the script does not list: pass its token with `--agent`, or read `blocked_everywhere`.
- Blocking some crawlers is legitimate. Report it neutrally.

## Rules

- Do not invent sources, quotes or numbers. If a claim has no source, cut it or ask.
- Do not name or imitate a specific product's behaviour; describe the input you changed.
- Do not stuff questions into a page for their own sake. Each must be one a buyer really asks.
- Never promise citations, traffic or revenue.
