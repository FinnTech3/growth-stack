---
name: internal-linking
description: >
  Plans internal links so important pages are reachable and described properly: hubs and spokes, orphan pages, anchor text, and
  the exact sentence each new link goes into. Use when the user says "fix my internal links", "which pages should link to this
  one", "improve my anchor text", "find orphan pages" or "plan internal linking for my blog". Do not use for crawl errors or
  redirect chains (use `technical-seo-audit`), grouping keywords (use `keyword-clusters`), links from other sites, or
  changing titles and headings (use `on-page-seo`).
---

# Internal linking

Requires: nothing to install. It works from a list of URLs and the page text the user supplies or the agent can read. If
the user has run the `growth-loop` audit, quote its `links-images` evidence (internal count, empty and generic anchors).

Internal links tell people and crawlers which pages matter and what they are about. Most sites I look at have the right
pages and the wrong links between them. I fix the anchors first, then the gaps.

## Inputs

- A URL list (sitemap, export or the user's page list) with each page's topic and whether it earns money.
- The cluster map from `keyword-clusters`, if one exists. If not, group the pages by topic by hand.
- Page text for the pages to be edited, so each link can be placed in a real sentence.

## Steps

1. List the money pages (the ones that should convert) and the hubs (one broad page per topic).
2. Build the link map: for every page, the pages it links to and the pages that link to it. Use the crawl or sitemap
   data the user has; if you can only read some pages, mark the rest "not mapped".
3. Find orphans: pages in the sitemap that nothing links to. Find thin hubs: hubs with fewer than three outbound links to their spokes.
4. Apply [the patterns](references/patterns.md): spokes link up to their hub, hubs link down to every spoke, spokes link
   sideways to one or two siblings, and informational pages link to the money page that follows.
5. Write each new link as a sentence: the existing sentence, the rewritten sentence, the anchor text and the target URL.
6. Fix bad anchors: replace "click here" and "read more" with 2 to 5 words that name the target. Vary the anchors that point at one page.
7. Cap sitewide links: nav and footer stay short. Contextual links in the body do the work.
8. Re-audit the edited pages with `growth-loop` and confirm `links-images` improved and no link returns a 404.

## Output

A link plan table: from page, to page, anchor, the rewritten sentence, reason. Then the orphan list, the anchor fixes and
the pages not mapped. End with the expected audit change, stated as a check to re-run, not a ranking.

## Exit criteria

- [ ] Every page in the target set has at least one contextual inbound link, so there are no orphans.
- [ ] Every money page has three or more contextual inbound links from related pages (rule of thumb).
- [ ] No exact anchor is used for one target more than three times (rule of thumb); no generic anchors remain.
- [ ] Each proposed link has a rewritten sentence that reads naturally and a target that returns 200.
- [ ] The re-audit shows no empty anchors and a higher internal link count on the edited pages.

## Edge cases and errors

- A link target redirects or 404s: fix the target first (use `technical-seo-audit`), then link to the final URL.
- Pagination, filters and tag archives create thousands of near-duplicate links: leave them out of the plan and say so.
- A page cannot take a natural link: add a short "related" block with descriptive anchors rather than forcing a sentence.
- Pages the agent could not read: list them as "not mapped", never as "no links".
- Very large sites: plan the top 20 money pages first, and state the cut-off.
- The user wants hundreds of links added at once: batch them in groups of about 20 pages and re-audit between batches.

## Rules

- Anchors describe the target; never use the same phrase for different targets.
- Do not use `nofollow` on internal links to shape anything.
- No hidden links, no links in text the visitor cannot see.
- Do not promise rankings. Say which pages become reachable and clearer.
