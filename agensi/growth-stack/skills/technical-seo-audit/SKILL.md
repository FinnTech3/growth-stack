---
name: technical-seo-audit
description: >
  Checks how a whole site presents itself to crawlers: robots.txt rules for search and AI crawlers, sitemaps, and a sample of
  URLs for status codes, redirect chains, noindex, canonical mismatches and mixed content, then ranks the findings.
  Use when the user says "audit my site's technical SEO", "why isn't Google indexing my pages", "check my robots.txt and
  sitemap", "are AI crawlers blocked on my site" or "find redirect chains". Do not use for scoring or rewriting one page
  (use `growth-loop` or `on-page-seo`), writing schema (use `structured-data`), making one page quotable by AI assistants (use `ai-search-readiness`), or Core Web Vitals field data, which needs real-user data.
---

# Technical SEO audit

Requires: Python 3.10+ and network access to the site you want checked. No accounts, keys or installs.

I would rather say "I could not check that" than guess. This skill reports what a crawler gets from the raw HTML and
the robots and sitemap files, and says clearly what it cannot see.

## Inputs

- A representative URL on the site (the homepage is fine) and whether the site is meant to be public.
- Which crawlers the owner wants allowed. Blocking an AI crawler is a choice, so ask; do not call it a fault.

## Running the script

`shared/scripts/site_probe.py` uses the network only to fetch the site's `/robots.txt`, its sitemaps and a small sample of its own
pages, one request at a time with a short delay, using the user agent `FinnTech-Growth-Audit/1.0`. It reads no local files.
Write it unchanged to a temporary file, run it, then delete it:

```sh
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/site_probe.XXXXXX")"   # paste shared/scripts/site_probe.py into it, unchanged
python3 "$SCRIPT" https://example.com/ --sample 20 --json
python3 "$SCRIPT" https://example.com/ --sample 20 --agent SomeOtherBot   # add any crawler token the user names
rm -f "$SCRIPT"
```

Exit 0 means no high-severity finding. Exit 1 means a high or critical finding, or the site could not be reached. Exit 2
means bad input, such as a private address (`--allow-private` is for the user's own staging or local site only).

## Steps

1. Run the probe with `--sample 20`. Read `rules`, `blocked_everywhere`, `findings` and `sample`.
2. Triage in the order the script gives: critical, high, medium, low. Do not reorder by how easy a fix is.
3. For every finding write: what it is, the likely cause, the fix, and the command that proves the fix (re-run the probe).
   [The symptom table](references/symptoms.md) lists the usual causes.
4. For crawler rules, list every crawler as allowed or blocked and ask the owner to confirm each AI or data crawler.
   `blocked_everywhere` shows any named agent the file blocks from the whole site, including ones you did not name.
5. Check the sitemap against the sample: every listed URL should return 200, be indexable and be its own canonical.
6. Hand page-level gaps (titles, copy, schema) to `growth-loop`. This skill stops at crawl and index health.

## Output

Return: a one-line verdict; a table of crawlers (allowed or blocked, with the rule that decides it); the sitemap summary
(files read, URLs listed); the sampled URLs with status and hops; the findings in severity order with cause, fix and proof
command; the decisions the owner must make; and what this audit could not see.

## Exit criteria

- [ ] The probe ran on the live site and its `findings` list is quoted, not paraphrased.
- [ ] No critical or high finding remains, or each remaining one has an owner and a reason.
- [ ] Every sampled sitemap URL returned 200, or the exception is listed with its fix.
- [ ] Each AI or data crawler is marked allowed or blocked by the owner's decision, not by default.
- [ ] A re-run after the fixes shows the finding gone.

## Edge cases and errors

- `error: ... private or reserved address` (exit 2): the URL points inside a network. Use `--allow-private` only on the user's own site.
- Server returns 403 to the probe: a firewall is blocking the user agent. Ask the owner to allow it, then re-run.
- Single-page apps that build links in JavaScript: the probe reads raw HTML only, so say that content and links may be missed.
- Sitemap index files: the probe reads up to 5 sitemap files in all, two levels deep. A bigger site needs a crawler.
- `robots.txt` that is 404 is fine: there are no rules. A 5xx is a high finding because crawlers may stop crawling.
- Sitemap or page on another host, or an http URL on an https site: reported as findings, never fetched across hosts.
- Compressed sitemaps (`.gz`) are read. A sitemap with a DTD is refused, not parsed.

## Rules

- Report evidence: the URL, the status, the rule. No finding without one.
- Never recommend blocking or allowing a crawler without the owner's say. State the trade-off in one sentence.
- Do not claim a fix will lift rankings. Say it removes a barrier.
- Sample, do not hammer: keep `--sample` at 50 or fewer and leave the default delay on.
