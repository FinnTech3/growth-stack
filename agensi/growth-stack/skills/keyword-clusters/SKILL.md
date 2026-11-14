---
name: keyword-clusters
description: >
  Groups a keyword list into topic clusters with search intent, a primary keyword and a page for each, using the data the user
  supplies and measuring head terms with a script. Use when the user says "cluster these keywords", "group my keyword list
  into topics", "which keywords belong on the same page", "build a topic map for my site" or "I have a keyword export, what now".
  Do not use for finding search volumes (bring an export), writing the article brief (use `content-brief`), editing an existing
  page for one phrase (use `on-page-seo`) or planning links between pages (use `internal-linking`).
---

# Keyword clusters

Requires: Python 3.10+. `text_stats.py` is offline, makes no network calls and reads one text file or stdin.

I will not invent search volumes. The user brings an export from whatever keyword tool they use, and I group what is in it.
If the data has no volumes, the clusters have no priority score, and I say so.

## Inputs

- A keyword list, one per line, ideally a CSV export with volume and difficulty columns if the user has them.
- The pages that exist today (URLs and their main topic), so clusters can map to them.
- What the business sells, so intent can be judged against it.

## Running the script

Write `shared/scripts/text_stats.py` unchanged to a temporary file, run it on the keyword list, then delete it. With `--lines` each line counts
as one sentence, so the top words and phrases are the head terms.

```sh
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/text_stats.XXXXXX")"   # paste shared/scripts/text_stats.py into it, unchanged
python3 "$SCRIPT" keywords.txt --lines --top 30 --json   # head terms and repeated phrases
rm -f "$SCRIPT"
```

Exit 0 is success. Exit 2 means a missing file, empty or binary input or a bad option.

## Steps

1. Clean the list: lowercase, trim, remove exact duplicates, fold simple plurals. Keep the original beside the cleaned one. Write the cleaned list to `keywords.txt`, one keyword per line, with no volumes or other columns.
2. Run the script. The 15 to 30 head terms and phrases are the candidate cluster names.
3. Assign each keyword to the cluster whose head term it contains. A keyword with two head terms goes where the intent matches best.
4. Label intent with [the modifier table](references/intent.md): informational, commercial, transactional, navigational.
   Never mix two intents on one page.
5. Check overlap. Two keywords belong on one page only if the same pages answer both. You need live results or the user's
   tool for that. If you do not have them, say "grouped by wording and intent only; overlap not checked".
6. Pick one primary keyword per cluster: the best-fitting intent first, then the highest supplied volume. List the rest as supporting.
7. Map each cluster to an existing URL or mark it "new page". Check for cannibalisation: two live pages on one cluster.
8. Rank clusters by supplied volume times fit with the business. If there is no volume, rank by fit and say so.

## Output

A cluster table: cluster, primary keyword, supporting keywords, intent, page type, existing URL or new, priority and why.
Add an "unassigned" list with the reason for each, and a note on what was not verified (overlap, volumes).

## Exit criteria

- [ ] Every keyword is in exactly one cluster or in "unassigned" with a reason.
- [ ] Every cluster has one primary keyword and one intent; no two clusters share a primary.
- [ ] Every volume shown was copied from the user's data.
- [ ] Each cluster maps to one page, existing or new, and any cannibalisation is listed.
- [ ] The report states whether overlap was checked.

## Edge cases and errors

- A list of more than about 2,000 keywords: cluster the top terms by volume first and say what was left out.
- Brand terms and competitor names: put them in their own group; they are navigational and rarely belong on a content page.
- Keywords in two languages or regions: separate by market before clustering.
- The script exits 2: report the message, fix the file (text only, under 5 MB) and re-run.
- Very broad one-word terms: park them as head topics; do not try to rank one page for them.
- Questions as keywords: keep them as supporting terms under the answer's topic.

## Rules

- No invented volumes, difficulty scores or traffic estimates.
- One page, one intent, one primary keyword.
- Do not split a topic into many thin pages to catch more keywords.
- Say what you could not check.
