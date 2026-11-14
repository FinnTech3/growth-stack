---
name: on-page-seo
description: >
  Rewrites the on-page elements of one page in its own voice: title, meta description, H1 and heading outline, share tags,
  content depth and keyword placement, and measures the result. Use when the user says "rewrite my title and meta
  description", "fix my headings", "optimise this page for [keyword]", "why is my page title cut off" or "my page is thin,
  what do I add". Do not use for sitewide crawl problems (use `technical-seo-audit`), keyword grouping (use
  `keyword-clusters`), a new article (use `content-brief`), schema (use `structured-data`) or conversion copy (use `landing-page-copy`).
---

# On-page SEO

Requires: Python 3.10+. `page_audit.py` needs network access to the live page; `text_stats.py` is offline and reads one file.

Here is what I would change first: the title, then the description, then the H1. They are cheap, they are what people
read in the results, and they are easy to get wrong in ways a script can see.

## Inputs

- The page URL, and one primary query plus up to two secondary ones. If the user has none, take the top phrases from
  `text_stats.py`, propose one, and ask them to confirm it.
- The current copy, so the new copy keeps the page's own voice.

## Running the scripts

Write each script (`shared/scripts/page_audit.py`, `shared/scripts/text_stats.py`) unchanged to a temporary file, run it, then delete it. `page_audit.py` uses the network only to read the
page you name and reads no local files. `text_stats.py` makes no network calls; it reads one text file or stdin.

```sh
A="$(mktemp "${TMPDIR:-/tmp}/page_audit.XXXXXX")"   # paste shared/scripts/page_audit.py into it, unchanged
T="$(mktemp "${TMPDIR:-/tmp}/text_stats.XXXXXX")"   # paste shared/scripts/text_stats.py into it, unchanged
python3 "$A" https://example.com/page --json                # evidence: snippet, content, links-images, basics
python3 "$T" copy.md --keyword "primary phrase" --top 15    # voice, readability, keyword placement
rm -f "$A" "$T"
```

Exit 0 and 1 follow the audit (1 means a high or critical gap). Exit 2 means bad input. `text_stats.py` exits 2 on a missing
file, empty or binary input, or an out-of-range option.

## Steps

1. Run the audit. Quote the `snippet`, `content` and `basics` evidence: title and description lengths, H1 count, words.
2. Measure the existing copy with `text_stats.py`. Note reading ease, words per sentence and the you-versus-we counts. Match them.
3. Write the title: 30 to 60 characters, primary phrase near the front, a reason to click, brand last. Unique on the site.
4. Write the description: 70 to 160 characters, the answer or promise, one proof point, no quotation marks. See [patterns](references/snippets.md).
5. Write one H1 that states the topic in the visitor's words. Build the H2s as the questions the page answers, in order, never skipping a level.
6. Add or fix the share tags (`og:title`, `og:description`, `og:image`, `twitter:card`) and `lang` and viewport if lost.
7. Check placement with `--keyword`: the phrase should appear in the title, the H1 and the first 100 words, and read naturally.
8. Re-run both scripts. Compare lost parts before and after.

## Output

A before and after table for title, description, H1 and H2 outline with character counts; the exact head markup to paste;
any body edits as replacement sentences; the `text_stats.py` readings before and after; the audit parts recovered.

## Exit criteria

- [ ] Title 30 to 60 characters; description 70 to 160; exactly one H1; two or more H2s; no skipped heading level.
- [ ] `--keyword` reports the primary phrase in a heading and in the first 100 words.
- [ ] No phrase is repeated until it reads badly. Rule of thumb: over 3 uses per 100 words is stuffing.
- [ ] Reading ease did not get worse than the original unless the user asked for a different register.
- [ ] A re-audit shows the `snippet` and `content` parts recovered, with no regressions elsewhere.

## Edge cases and errors

- Page is a pricing, contact or login page: 300 words may not apply. Say the word-count part is a rule of thumb and leave it.
- Title already ranks and the user is nervous: change one element at a time and note the date.
- Two pages chase the same phrase: stop and use `keyword-clusters`. Do not rewrite both.
- Non-English page: the scripts' question and verb lists are English. Report those parts as not applicable.
- Search engines rewrite titles and snippets. Say the new ones are a proposal the engine may override.

## Rules

- Match the page's voice. If it says "you", you say "you".
- Do not invent facts, prices or proof for a description. Use only what is on the page or what the user supplied.
- Keyword counts catch stuffing; they are not a target. Never hit a density.
- Never promise a ranking. Say what you changed and what it should make clearer.
