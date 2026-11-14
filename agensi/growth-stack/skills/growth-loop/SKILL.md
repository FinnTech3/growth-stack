---
name: growth-loop
description: >
  Audits one live page with a transparent Growth Score out of 100 (crawl and index, on-page, structured data, AI-search
  readiness, conversion), ranks the biggest gaps, routes each to the right fixer skill, and re-audits to prove what changed.
  Use when the user says "audit this page", "what should I fix first on this page", "score my landing page", "run the growth
  loop on my homepage" or "re-audit after my changes". Do not use for sitewide crawl rules or sitemaps (use
  `technical-seo-audit`), for writing the fix itself (use the fixer named in the routing table), or for a page that is not live yet.
---

# Growth loop

Requires: Python 3.10+ and network access to the page you want audited. No accounts, keys or installs.

I run one loop and nothing else: audit the page, find the biggest gaps, write the fix in the page's own voice, set up
measurement, re-audit. The score is a diagnostic. It is not the goal, and it cannot promise rankings or revenue.

## Inputs

- The page URL, and the one action a visitor should take there (the conversion). Ask if the user has not said.
- Permission to fetch the page. The script sends one request per hop with the user agent `FinnTech-Growth-Audit/1.0`.

## Running the script

`shared/scripts/page_audit.py` fetches one page and scores it. It uses the network only to read the URL you give it, and it reads
no local files. `shared/scripts/text_stats.py` (step 4) is offline and reads one text file. Write each script unchanged to its own
temporary file, run it, then delete the files:

```sh
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/page_audit.XXXXXX")"   # paste shared/scripts/page_audit.py into it, unchanged
python3 "$SCRIPT" https://example.com/page --json > before.json   # full result, the baseline
python3 "$SCRIPT" https://example.com/page               # the readable report
rm -f "$SCRIPT"
T="$(mktemp "${TMPDIR:-/tmp}/text_stats.XXXXXX")"        # paste shared/scripts/text_stats.py into it, unchanged
python3 "$T" voice.md                                    # voice.md: the 5 to 10 copied sentences (step 4)
rm -f "$T"
```

After the user ships, run the first command again writing `after.json`. Compare the two with the snippet in the ledger reference.

Exit 0 means no high-severity gap. Exit 1 means a high or critical gap, or the fetch failed. Exit 2 means bad input, such
as a private address (add `--allow-private` only for the user's own staging or local site).

## Steps

1. Run the audit with `--json`, saving the output as `before.json`. Note the date, the final URL and the score.
2. Read `priority`. Take the three gaps that lose the most points; if a critical gap exists, it goes first whatever its size.
3. Route each gap with [the routing table](references/routing.md). One loop fixes at most three gaps, so you can tell
   which change moved which points.
4. Capture the page's own voice before writing anything: copy 5 to 10 sentences from the hero and body into a file and
   measure them with `text_stats.py` (see Running the script) (sentence length, you versus we, hype words). Keep that voice.
5. Hand each gap to its fixer skill. Do not edit the live page yourself unless the user asked. Deliver the exact new copy,
   markup or config as a diff the user can paste.
6. Before it ships, run `measurement-plan` so the baseline and the success measure are written down first.
7. After the user ships, run the same command on the same URL and save the result as `after.json`.
8. Compare the two with [the ledger snippet](references/ledger.md). Report every check that changed, points before and
   after, and any part that earned points before and does not now.

## Output

Return, in this order: the score table before and after; the three gaps with their lost parts quoted from the audit;
the fix handed to each fixer; the measurement baseline; the ledger row. Use the ledger layout in `references/ledger.md`.

## Exit criteria

- [ ] `before.json` exists with a score and a date, and `after.json` was run on the same URL with the same flags.
- [ ] Every gap fixed this loop names its fixer skill and the audit parts it should recover.
- [ ] The comparison lists no part that earned points before and lost them now.
- [ ] Points that only hosting can change (https, compression, headers) are listed for the host owner, not claimed.
- [ ] The answer says what the score cannot show: real conversion rate needs real traffic over time.

## Edge cases and errors

- Fetch failed (exit 1, `error:` line): report the exact message. Do not guess a score.
- Page needs JavaScript to show its content: the script reads raw HTML, so say the score covers what a crawler gets first.
- Page behind a login or a firewall that blocks the user agent: ask the user to allow it, or to paste the HTML.
- A redirect to another host: audit the final URL and say so.
- Score went down after a fix: show which parts, and revert that change before anything else.
- Staging or local site: use `--allow-private`, and expect the https and header points to stay lost.

## Rules

- Never promise rankings, traffic or revenue. Say what was measured and what it can and cannot show.
- Do not invent proof. If the page needs a review, a number or a client name, ask for the real one.
- Heuristic checks are marked in the report. Treat them as guides and say when one is wrong for this page.
- Change three things at most per loop. Re-audit every time.
