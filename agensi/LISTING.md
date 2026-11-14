# Agensi listing copy

Paste these into the submit form at agensi.io/dashboard/submit. Upload `dist/growth-stack.zip` (build it with
`python3 tools/agensi_build.py agensi/growth-stack`, which also checks this file against Agensi's field limits). Agensi lists
it as a skill pack because the zip holds 15 `SKILL.md` files. The logo and three screenshots (the score loop, the skill grid, what moved) are in `agensi/media/`.

| Field | Value |
|---|---|
| Title | Growth Stack: SEO and Marketing Skills in One Pack |
| Categories | Marketing & SEO; Sales & Lead Gen; Writing & Content |
| Suggested price | $19 one-time |
| Tags | seo, marketing, site-audit, conversion, schema, ai-search, local-seo, email, pricing, launch |
| Compatibility note | Requires Python 3.10 or newer for the three scripts (standard library only, nothing to install). Works with any agent that supports SKILL.md and can run python3. |
| Permissions | Network access to the pages you ask it to audit: page_audit.py reads one page, site_probe.py reads that site's robots.txt, sitemaps and a small sample of its pages. No credentials, no accounts. text_stats.py makes no network calls and reads one text file you name. The agent writes each script to a temporary file and deletes it afterwards. |
| Docs link | https://github.com/FinnTech3/growth-stack |

## Summary

Audit a page, find the biggest gaps, write the fix in the page's own voice, set up measurement, re-audit. Fifteen skills and three scripts, with a Growth Score that names every point and a worked example that goes from 23 to 72.

## Description

Most SEO output is a long list with no order and no proof. Most marketing advice never looks at the page. Growth Stack does
both in one loop: it measures one page, ranks the gaps, routes each to the skill that fixes it, and measures again so you can see exactly which points moved.

**How it works.** You ask in your own words ("audit this page", "rewrite my title and description", "review my pricing page").
The agent picks the matching skill from its description. When a skill needs numbers it writes a small standard-library
Python script to a temporary file, runs it, and deletes it. `page_audit.py` gives a Growth Score out of 100 across crawl and
index, on-page SEO, structured data, AI-search readiness and conversion. Every one of the 100 points is named, and the lost
ones come with the evidence, why it matters and the fix. `site_probe.py` checks robots.txt rules for search and AI crawlers,
sitemaps and a sample of URLs. `text_stats.py` measures readability, keywords, passive voice and the you-versus-we balance of
your copy, offline.

**The fifteen skills.** Growth loop, technical SEO audit, on-page SEO, structured data, AI-search readiness, local SEO,
keyword clusters, content brief, internal linking, positioning and messaging, landing page copy, email sequence, pricing page review,
launch plan and measurement plan. Each has inputs, steps, an output, exit criteria the agent can check, edge cases and
rules, and each names its neighbours so the right one loads.

**What makes it different.** The score is transparent and the fixes are tied to it. A fix that does not recover named
points is not a fix. The scripts refuse private addresses, cap size, time and redirects, and check the address before and after connecting.

**Where it stops.** It reads the HTML a crawler gets first, so JavaScript-only content is not seen. It promises no rankings,
traffic, citations or revenue. It will not invent a testimonial, a statistic or a price; missing proof is a marked gap.
The AI crawler list is short on purpose and takes more tokens with `--agent`.

## See it in action

**Request:** "Audit my homepage, fix the biggest gaps in my own voice, and show me the score before and after." The page is a fictional bike shop fixture served locally (the pack's worked example has every command and every output).

**Result, step 1: the audit** (`page_audit.py`, real output)

```text
GROWTH SCORE: 23/100
  Crawl and index        13/25
  On-page SEO            10/30
  Structured data         0/10
  AI-search readiness     0/15
  Conversion              0/20

 1. [HIGH] cta -12: verb-led CTA (-6); specific label (-3); largest form has 5 fields or fewer (rule of thumb) (-3)
 2. [HIGH] snippet -11: title 30-60 characters (-2); has a meta description (-3); description 70-160 characters (-2); og:title, description, image and twitter:card (-4)
 3. [HIGH] schema -10: has JSON-LD (-4); all blocks parse (-3); common type has required properties (-3)
```

**Step 2: loop 1 fixes the top three gaps** (button and form, title, description and share tags, business markup). The re-audit and the comparison snippet:

```text
GROWTH SCORE: 56/100
score 23 -> 56
+ snippet title 30-60 characters 0 -> 2
+ snippet has a meta description 0 -> 3
+ snippet description 70-160 characters 0 -> 2
+ snippet og:title, description, image and twitter:card 0 -> 4
+ schema has JSON-LD 0 -> 4
+ schema all blocks parse 0 -> 3
+ schema common type has required properties 0 -> 3
+ cta verb-led CTA 0 -> 6
+ cta specific label 0 -> 3
+ cta largest form has 5 fields or fewer (rule of thumb) 0 -> 3
```

**Step 3: loop 2 fixes the next three** (mobile and language basics, question headings with short answers, contact and policy links):

```text
score 56 -> 72
+ basics viewport meta 0 -> 2
+ basics html lang 0 -> 1
+ answers 2+ question headings 0 -> 4
+ answers short direct answers (heuristic) 0 -> 4
+ trust contact details 0 -> 3
+ trust policy links 0 -> 2
```

**Step 4: the site probe** (`site_probe.py`) on the same site found a sitemap URL that redirects and no Sitemap line in robots.txt:

```text
  [MEDIUM] sitemap: http://127.0.0.1:8765/services: the sitemap lists a URL that redirects
      Fix: List the final URL.
  [LOW] robots.txt: no Sitemap line
      Fix: Add 'Sitemap: <absolute URL>' to robots.txt.
```

After loop 2 the score is 72/100, and the probe reports no findings. Still lost: 28 points. Six are hosting (https and server headers, because the fixture runs on plain Python), three are review proof, because I will not write a testimonial the owner does not have, and the worked example gives the reason for the other 19.

## Limitations

- It reads raw HTML. Pages that build their content in JavaScript will score on what a crawler gets first.
- Heuristic checks (answer length, proof, thin content, CTA wording) are rules of thumb and are labelled as such.
- It does not run Core Web Vitals, backlinks, rankings or analytics. Bring exports and it works from them.
- The skills need your facts. Without a real quote, price or address, they leave a marked gap.
- The AI crawler list is short by design. Add other tokens with `--agent`.

## FAQ

**Do I need to install anything?** No. The agent writes each script to a temporary file and deletes it. You need Python 3.10 or newer on the machine that runs the agent.

**Does it change my site?** No. It reads pages and hands you the copy, markup or config to paste. You decide what ships.

**Will the score go up my rankings?** I make no such promise. The score measures things that are cheap to fix and easy to get wrong. Rankings depend on far more.

**Can I audit a staging site?** Yes, with `--allow-private`, on sites you own. Expect the https and header points to stay lost.

**Can I use one skill without the rest?** Yes. Each skill stands alone, and the ones that need the audit say how to get it.

## Use cases

- Score a landing page, fix the top three gaps and prove what changed
- Check robots.txt, sitemaps and AI crawler access for a whole site
- Write a title, description and valid JSON-LD that match what the page shows
- Cluster a keyword export, brief the article and plan the internal links
- Review a pricing page and plan a launch with measurement ready first
