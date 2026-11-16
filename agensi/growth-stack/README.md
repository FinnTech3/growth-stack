# Growth Stack

Fifteen skills and three small scripts that run one loop on a page: audit it, find the biggest gaps, write the fix in the
page's own voice, set up measurement, then audit it again and show what moved.

## The straight answer

- `page_audit.py` fetches one page and gives it a Growth Score out of 100 with every point named, so you can see where the other points went.
- The skills turn each gap into the fix: title and description, schema, answers an AI assistant can quote, landing page copy, pricing, email, internal links, local, launch and measurement.
- Then you audit again. The score changes by exactly the points you recovered, and anything that got worse is listed.

It does not promise rankings, traffic or revenue. The score is a diagnostic. I say that in every report.

## Run it in 60 seconds

Ask your agent: "Audit https://your-site.example/page and tell me what to fix first." The agent loads `growth-loop`, writes
`page_audit.py` to a temporary file, runs it, deletes it, and reads you the result. The scripts use only the Python 3.10+
standard library. Nothing is installed.

```text
GROWTH SCORE: 23/100
  Crawl and index        13/25
  On-page SEO            10/30
  Structured data         0/10
  AI-search readiness     0/15
  Conversion              0/20

 1. [HIGH] cta -12: verb-led CTA (-6); specific label (-3); largest form has 5 fields or fewer (rule of thumb) (-3)
```

That is real output from the fixture page in [the worked example](examples/growth-loop-worked-example.md), which goes from 23 to 56 to 72 over two loops, with every command and every output shown.

## The loop

```text
   audit ──> biggest gaps ──> fix, in the page's voice ──> measurement ──> re-audit
     ^                                                                        |
     └────────────────────────────────────────────────────────────────────────┘
```

## The fifteen skills

| Step | Skill | Use it when | Script |
|---|---|---|---|
| Audit | [`growth-loop`](skills/growth-loop/SKILL.md) | You want a page scored, the gaps ranked and the change proved | `page_audit.py` |
| Audit | [`technical-seo-audit`](skills/technical-seo-audit/SKILL.md) | The whole site: robots rules, sitemaps, redirects, noindex | `site_probe.py` |
| Fix | [`on-page-seo`](skills/on-page-seo/SKILL.md) | Title, description, headings, share tags | `page_audit.py`, `text_stats.py` |
| Fix | [`structured-data`](skills/structured-data/SKILL.md) | JSON-LD that matches what the page shows | `page_audit.py` |
| Fix | [`ai-search-readiness`](skills/ai-search-readiness/SKILL.md) | Short answers, sources, entities, crawler access | `page_audit.py`, `site_probe.py` |
| Fix | [`local-seo`](skills/local-seo/SKILL.md) | Name, address, phone, location pages, reviews | none |
| Fix | [`internal-linking`](skills/internal-linking/SKILL.md) | Orphans, anchors, the sentence each link goes in | none |
| Plan | [`keyword-clusters`](skills/keyword-clusters/SKILL.md) | A keyword export turned into topics, intent and pages | `text_stats.py` |
| Plan | [`content-brief`](skills/content-brief/SKILL.md) | One piece, one reader, one outline, checked against the draft | `text_stats.py` |
| Fix | [`positioning-messaging`](skills/positioning-messaging/SKILL.md) | Who it is for, what is different, what proof exists | none |
| Fix | [`landing-page-copy`](skills/landing-page-copy/SKILL.md) | The button, the form, the hero, the proof | `page_audit.py`, `text_stats.py` |
| Fix | [`email-sequence`](skills/email-sequence/SKILL.md) | A sequence for people who opted in | `text_stats.py` |
| Fix | [`pricing-page-review`](skills/pricing-page-review/SKILL.md) | Plans, names, terms, honest pricing presentation | none |
| Plan | [`launch-plan`](skills/launch-plan/SKILL.md) | Dated tasks, go and no-go, a rollback, a review | none |
| Measure | [`measurement-plan`](skills/measurement-plan/SKILL.md) | Events, baseline, UTMs, consent, QA, re-audit dates | none |

Every skill has the same shape: inputs, steps, an output, exit criteria the agent can check, edge cases, and rules. Each one names its neighbours in its "Do not use" line so the right one loads.

## Why it's built this way

- **One file per script.** Agensi delivers text, and the agent writes each script to a temporary file. A script cannot import another, so each is a single standard-library file under 20 KB. The three scripts live once, in `shared/scripts/`, and every skill that runs one says how.
- **Two-space indents in the scripts.** That is the only way I could fit the full rubric and the safe fetching into 20 KB. The tests and everything else use four.
- **The score names every point.** 100 points, 11 checks, 37 parts. Each part says what earned or lost it. No black box, so you can argue with it.
- **Safe by default.** One page, a polite user agent, size and time caps, a redirect limit, and private, loopback and link-local addresses refused unless you pass `--allow-private`. The address is checked before connecting and again after, so a DNS trick cannot reach an internal host.
- **The measuring and the writing are separate.** The scripts measure. The skills write. The scripts never guess at copy and the skills never guess at numbers.

## What it won't do

- Promise rankings, traffic, citations or revenue.
- Invent a testimonial, a statistic, a client name or a price. If proof is missing it leaves a marked gap.
- Run JavaScript. The scripts read the HTML a crawler gets first, and the reports say so.
- Replace a crawler, analytics or a keyword tool. Bring an export and it works from that.
- Pick the AI crawler policy for you. `site_probe.py` tests the main search crawlers, shows every named agent a robots file blocks, and tests any other crawler tokens you name with `--agent`.

## Finn's take

Most SEO output is a long list with no order and no proof, and most marketing advice never looks at the page. I wanted one
loop that does both: measure the page, fix the three biggest things, measure again. The score is a diagnostic and it is wrong
sometimes, which is why the heuristic checks say so. If a skill tells you to change something, it should be able to say which
points that change recovers.

Built by FinnTech3.

## Licence

MIT, Copyright (c) 2026 FinnTech3.
