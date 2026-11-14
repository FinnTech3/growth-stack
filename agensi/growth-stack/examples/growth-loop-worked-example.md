# Worked example: the growth loop on a small shop page

Everything below is real output from the three scripts in this pack, run on the fixture site in
[`fixture-site/`](fixture-site/). The shop is fictional: "Harbour Street Bikes", a made-up address and a phone number from
the range reserved for drama use. The page has deliberate flaws. Nothing here is a customer result, and no number is
a claim about a real business.

**Request:** "Audit my homepage, fix the biggest gaps in my own voice, and show me the score before and after."

## Run it yourself

```sh
cd fixture-site
python3 -m http.server 8765 --bind 127.0.0.1 --directory before &       # serve the "before" page
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/page_audit.XXXXXX")"                  # paste shared/scripts/page_audit.py into it, unchanged
python3 "$SCRIPT" http://127.0.0.1:8765/ --allow-private --json > before.json
python3 "$SCRIPT" http://127.0.0.1:8765/ --allow-private
```

`--allow-private` is needed because the fixture runs on 127.0.0.1. Stop the server and serve `loop-1`, then `loop-2`, for
the later audits. The scripts exit 1 when they find a high or critical gap, and the fixture has them, so a non-zero exit is expected.

## Step 1: audit the page (baseline)

`page_audit.py` on the "before" page. This is the full output.

```text
Growth Audit: http://127.0.0.1:8765/
Fetched: HTTP 200, 1,385 bytes of HTML, 3 ms, 0 redirect(s)

GROWTH SCORE: 23/100
  Crawl and index        13/25
  On-page SEO            10/30
  Structured data         0/10
  AI-search readiness     0/15
  Conversion              0/20

FIX FIRST (severity of the worst lost point, then points lost)
 1. [HIGH] cta -12: verb-led CTA (-6); specific label (-3); largest form has 5 fields or fewer (rule of thumb) (-3)
      Evidence: cta=none, generic=['Submit'], form_fields=8
      Why: A clear next step is the conversion
      Fix: One verb-led button ('Get my quote'); short form
 2. [HIGH] snippet -11: title 30-60 characters (-2); has a meta description (-3); description 70-160 characters (-2); og:title, description, image and twitter:card (-4)
      Evidence: title=Home, title_chars=4, description_chars=0, tags=0
      Why: Title, description, tags are your listing
      Fix: Rewrite title and description; add og and twitter tags
 3. [HIGH] schema -10: has JSON-LD (-4); all blocks parse (-3); common type has required properties (-3)
      Evidence: blocks=0, bad=0, types=none, missing=none
      Why: Machines can check structured facts
      Fix: Add valid JSON-LD with its required properties
 4. [HIGH] basics -5: served over https (-2); viewport meta (-2); html lang (-1)
      Evidence: http=200, redirects=0, viewport=missing, lang=missing
      Why: A clean, mobile-ready 200 page is the base
      Fix: Serve 200 over https; add viewport meta, html lang
 5. [MEDIUM] answers -8: 2+ question headings (-4); short direct answers (heuristic) (-4)
      Evidence: questions=0, answered=0
      Why: Answer engines quote short answers
      Fix: Phrase H2s as questions; answer in 8-60 words
 6. [MEDIUM] trust -8: contact details (-3); policy links (-2); proof such as reviews (heuristic) (-3)
      Evidence: policy_links=0
      Why: Visitors look for proof you are real
      Fix: Show contact, link policies, add real proof
 7. [MEDIUM] links-images -5: no empty or generic anchors (-2); images have alt (-3)
      Evidence: internal=5, empty=0, generic=2, alt=0/2
      Why: Anchors and alt text say what things are
      Fix: Link related pages; describe anchors and images
 8. [MEDIUM] content -4: no skipped heading level (-2); 300+ words (rule of thumb) (-2)
      Evidence: h1=['Welcome to Harbour Street Bikes'], h2=2, skipped=['h3 after h1'], words=96
      Why: Topic, outline and substance
      Fix: One H1, 2+ H2s in order, full answer
 9. [MEDIUM] indexable -3: one canonical link (-3)
      Evidence: robots=none, canonical=none, hreflang=none
      Why: noindex removes the page from search
      Fix: Remove noindex; add one rel=canonical
10. [LOW] authority -7: author (-2); date (-2); 2+ outside sources (heuristic) (-3)
      Evidence: sources=0
      Why: Named, dated, sourced pages get cited
      Fix: Add a byline, a time element, source links
11. [LOW] delivery -4: gzip and a cache header (-2); 3+ of 5 security headers (-2)
      Evidence: encoding=none, cache=['last-modified'], security=0, bytes=1385, ms=3
      Why: Slow, bare pages lose trust
      Fix: Enable gzip, caching, security headers

EVERY POINT
  Crawl and index 13/25
    basics 5/10: +3 200 status; +2 at most one redirect; -2 served over https; -2 viewport meta; -1 html lang
    indexable 5/8: +5 no noindex; -3 one canonical link
    delivery 3/7: -2 gzip and a cache header; -2 3+ of 5 security headers; +2 HTML under 500 KB; +1 fetched in under 2 s
  On-page SEO 10/30
    snippet 3/14: +3 has a title; -2 title 30-60 characters; -3 has a meta description; -2 description 70-160 characters; -4 og:title, description, image and twitter:card
    content 5/9: +4 exactly one H1; +1 two or more H2s; -2 no skipped heading level; -2 300+ words (rule of thumb)
    links-images 2/7: +2 3+ internal links; -2 no empty or generic anchors; -3 images have alt
  Structured data 0/10
    schema 0/10: -4 has JSON-LD; -3 all blocks parse; -3 common type has required properties
  AI-search readiness 0/15
    answers 0/8: -4 2+ question headings; -4 short direct answers (heuristic)
    authority 0/7: -2 author; -2 date; -3 2+ outside sources (heuristic)
  Conversion 0/20
    cta 0/12: -6 verb-led CTA; -3 specific label; -3 largest form has 5 fields or fewer (rule of thumb)
    trust 0/8: -3 contact details; -2 policy links; -3 proof such as reviews (heuristic)

Heuristic and rule-of-thumb items are guides, not verdicts.
```

The score is 23/100. Every point is named, so I can say exactly where the other 77 went.
Two of them, "served over https" and the delivery headers, belong to the host, not the page: this fixture is plain http
from Python's built-in server, so those points stay lost all the way through, and I will not pretend otherwise.

## Step 2: pick the three biggest gaps

The report sorts by the severity of the worst lost point, then by points lost. Loop 1 takes the top three:

```text
 1. [HIGH] cta -12: verb-led CTA (-6); specific label (-3); largest form has 5 fields or fewer (rule of thumb) (-3)
 2. [HIGH] snippet -11: title 30-60 characters (-2); has a meta description (-3); description 70-160 characters (-2); og:title, description, image and twitter:card (-4)
 3. [HIGH] schema -10: has JSON-LD (-4); all blocks parse (-3); common type has required properties (-3)
```

That is 33 recoverable points in three checks. I fix no more than three gaps per loop, so I can tell which change moved which points.
The routing table sends them to `landing-page-copy` (button and form), `on-page-seo` (title, description, share tags) and
`structured-data` (the business markup).

## Step 3: capture the page's own voice

Before writing anything I measure the existing copy with `text_stats.py`, so the new words sound like the shop.

```text
Words 75  Sentences 15  Paragraphs 7  Avg 5.0 words/sentence  Long (over 25 words) 0
Reading time about 0m 22s at 200 words/min (a rule of thumb)
Flesch Reading Ease 74.3 (fairly easy); Flesch-Kincaid grade 4.1
  Flesch Reading Ease = 206.835 - 1.015 x (words / sentences) - 84.6 x (syllables / words)
  Flesch-Kincaid grade = 0.39 x (words / sentences) + 11.8 x (syllables / words) - 15.59
  syllables are counted by a vowel-group heuristic, so treat scores as +/- a few points

Outline
  h1 Welcome to Harbour Street Bikes
      h3 Innovative, cutting-edge bike solutions
    h2 Our services
    h2 Get in touch

Top words: prices (2), e-bikes (2), family-run (1), workshop (1), provide (1), world-class (1), robust (1), bike (1), solutions (1), every (1)
Top phrases: none repeated
Keyword 'bike repair': 0x, 0.0 per 100 words, in a heading: no, in first 100 words: no

You versus we: 0 you-words, 11 we-words (customer-first copy leans to you)
Repeated openings (heuristic): none
Three sentences in a row starting the same way: We
Passive voice (heuristic): 1 (6.7 per 100 sentences)
    are trained
Hedge words (heuristic): might x1, probably x1, could x1
Hype or jargon words (heuristic): world-class x1, robust x1
```

Plain, short sentences, no jargon beyond a few puffed-up words, and 11 we-words against 0 you-words. I keep the plain
register. The hype and the we-heavy hero are a gap for a later loop, not this one.

## Step 4: write the fixes (loop 1)

The exact change to the page, as a diff the owner can paste. The facts in the markup (address, phone) come from the
fixture's own contact page. Nothing is invented. The button says what the visitor gets, and the form drops from eight
fields to three. The rest of the fields can be asked after the quote.

```diff
--- before/index.html
+++ loop-1/index.html
@@ -2,7 +2,20 @@
 <html>
 <head>
 <meta charset="utf-8">
-<title>Home</title>
+<title>Bike repair in Harbour Street, collected and back same day</title>
+<meta name="description" content="Family-run bike repair on Harbour Street. Fixed prices from 45 pounds, collection within five miles, most jobs back the same day.">
+<meta property="og:title" content="Bike repair on Harbour Street">
+<meta property="og:description" content="Family-run bike repair on Harbour Street. Fixed prices from 45 pounds, collection within five miles, most jobs back the same day.">
+<meta property="og:image" content="http://127.0.0.1:8765/img/shop.jpg">
+<meta name="twitter:card" content="summary_large_image">
+<script type="application/ld+json">
+{"@context": "https://schema.org", "@graph": [
+ {"@type": "LocalBusiness", "@id": "http://127.0.0.1:8765/#shop", "name": "Harbour Street Bikes", "url": "http://127.0.0.1:8765/",
+  "telephone": "+44 1632 960123",
+  "address": {"@type": "PostalAddress", "streetAddress": "4 Harbour Street", "addressLocality": "Exampletown", "postalCode": "AB1 2CD"}},
+ {"@type": "Organization", "name": "Harbour Street Bikes", "url": "http://127.0.0.1:8765/"}
+]}
+</script>
 </head>
 <body>
 <div><a href="/">Harbour Street Bikes</a> | <a href="/services">Services</a> | <a href="/contact/">Contact</a></div>
@@ -18,11 +31,10 @@
 <h2>Get in touch</h2>
 <p>Call us on <img src="/img/phone.png"></p>
 <form action="/send" method="post">
-<input name="name" placeholder="Name"><input name="email" placeholder="Email"><input name="phone" placeholder="Phone">
-<input name="address" placeholder="Address"><input name="make" placeholder="Bike make"><input name="model" placeholder="Bike model">
-<input name="problem" placeholder="What is wrong?"><input name="date" placeholder="Preferred date">
-<button>Submit</button>
+<input name="name" placeholder="Name"><input name="email" placeholder="Email"><input name="problem" placeholder="What is wrong with the bike?">
+<button>Get my quote</button>
 </form>
+
 <p>&copy; Harbour Street Bikes</p>
 </body>
 </html>
```

Before I let anyone ship this I run `measurement-plan`. For this page that is one primary event and two supporting ones:

| Event | Trigger | Properties | QA step | Status |
|---|---|---|---|---|
| `submit_quote_form` (primary) | Quote form submitted successfully | `page`, `source` | Submit a test form, see one event | pending |
| `click_quote_button` | The "Get my quote" button is pressed | `page` | Press it, see one event | pending |
| `click_phone_link` | The telephone link is pressed | `page` | Press it on a phone-sized window | pending |

Baseline recorded on 14 November 2026: Growth Score 23. The fixture has no analytics, so there is no baseline
conversion count to record, and I say so rather than make one up.

## Step 5: re-audit (loop 1)

Same command, same flags, the "loop-1" page. Summary:

```text
Growth Audit: http://127.0.0.1:8765/
Fetched: HTTP 200, 2,264 bytes of HTML, 4 ms, 0 redirect(s)

GROWTH SCORE: 56/100
  Crawl and index        13/25
  On-page SEO            21/30
  Structured data        10/10
  AI-search readiness     0/15
```

Every changed part, from the comparison snippet in `skills/growth-loop/references/ledger.md`:

```text
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

33 points recovered, which is exactly the 33 I expected from the three gaps, and no line starts with "-", so nothing regressed.

## Step 6: loop 2, the next three gaps

The re-audit's priority list now reads:

```text
 1. [HIGH] basics -5: served over https (-2); viewport meta (-2); html lang (-1)
 2. [MEDIUM] answers -8: 2+ question headings (-4); short direct answers (heuristic) (-4)
 3. [MEDIUM] trust -8: contact details (-3); policy links (-2); proof such as reviews (heuristic) (-3)
 4. [MEDIUM] links-images -5: no empty or generic anchors (-2); images have alt (-3)
 5. [MEDIUM] content -4: no skipped heading level (-2); 300+ words (rule of thumb) (-2)
 6. [MEDIUM] indexable -3: one canonical link (-3)
 7. [LOW] authority -7: author (-2); date (-2); 2+ outside sources (heuristic) (-3)
 8. [LOW] delivery -4: gzip and a cache header (-2); 3+ of 5 security headers (-2)
```

Loop 2 takes the first three. "served over https" cannot be fixed on this fixture, so `basics` is worth 3 recoverable points,
not 5. I also fix the sitemap and robots findings from `site_probe.py`, because they are a different instrument and touch no page score.

`site_probe.py` on the "before" site:

```text
Site Probe: http://127.0.0.1:8765

robots.txt: HTTP 200
  CRAWL RULES for the audited path
    search  Googlebot             allowed  no matching rule
    search  Bingbot               allowed  no matching rule
    search  DuckDuckBot           allowed  no matching rule
    search  Applebot              allowed  no matching rule
    ai/data Google-Extended       allowed  no matching rule
    ai/data Applebot-Extended     allowed  no matching rule
    ai/data CCBot                 allowed  no matching rule
    ai/data Bytespider            allowed  no matching rule
    ai/data Amazonbot             allowed  no matching rule
    ai/data Meta-ExternalAgent    allowed  no matching rule
    ai/data Diffbot               allowed  no matching rule

Sitemap URLs found: 3
Sampled 3 URL(s)
    200 0 redirect(s)  http://127.0.0.1:8765/
    200 1 redirect(s)  http://127.0.0.1:8765/services
    200 0 redirect(s)  http://127.0.0.1:8765/contact/

FINDINGS (worst first)
  [MEDIUM] sitemap: http://127.0.0.1:8765/services: the sitemap lists a URL that redirects
      Fix: List the final URL.
  [LOW] robots.txt: no Sitemap line
      Fix: Add 'Sitemap: <absolute URL>' to robots.txt.

Blocking an AI crawler is a choice, not a fault. The list is short on purpose: add other tokens with --agent.
```

The loop-2 changes to the page:

```diff
--- loop-1/index.html
+++ loop-2/index.html
@@ -1,7 +1,8 @@
 <!DOCTYPE html>
-<html>
+<html lang="en-GB">
 <head>
 <meta charset="utf-8">
+<meta name="viewport" content="width=device-width, initial-scale=1">
 <title>Bike repair in Harbour Street, collected and back same day</title>
 <meta name="description" content="Family-run bike repair on Harbour Street. Fixed prices from 45 pounds, collection within five miles, most jobs back the same day.">
 <meta property="og:title" content="Bike repair on Harbour Street">
@@ -26,15 +27,18 @@
 excellence. We think our prices might be fair, and we could probably fix most things. Our experts are trained by the best.</p>
 <p>We do brakes, gears, wheels and tyres. We do e-bikes too. We also offer collection. For prices, <a href="/services">click here</a>.
 To find out more, <a href="/contact/">read more</a>.</p>
-<h2>Our services</h2>
-<ul><li>Servicing</li><li>Repairs</li><li>E-bikes</li></ul>
+<h2>How much does a bike service cost?</h2>
+<p>A basic service costs 45 pounds and a full service costs 85 pounds. Parts are charged at cost. We quote before we start,
+so the price you are given is the price you pay.</p>
+<h2>Do you collect bikes from home?</h2>
+<p>Yes. We collect and return within five miles of the shop for a flat 10 pounds, and most bikes are back with you the same day.</p>
 <h2>Get in touch</h2>
-<p>Call us on <img src="/img/phone.png"></p>
+<p>Call us on <a href="tel:+441632960123">01632 960123</a>.</p>
 <form action="/send" method="post">
 <input name="name" placeholder="Name"><input name="email" placeholder="Email"><input name="problem" placeholder="What is wrong with the bike?">
 <button>Get my quote</button>
 </form>
 
-<p>&copy; Harbour Street Bikes</p>
+<p>&copy; Harbour Street Bikes. <a href="/privacy/">Privacy policy</a></p>
 </body>
 </html>
```

The two sitemap and robots fixes are two lines: list `/services/` (the final URL) in `sitemap.xml`, and add
`Sitemap: http://127.0.0.1:8765/sitemap.xml` to `robots.txt`. A placeholder privacy page was added so the footer link has a
target. The owner has to supply the real policy text, and I did not write one.

## Step 7: re-audit (loop 2) and the final table

```text
Growth Audit: http://127.0.0.1:8765/
Fetched: HTTP 200, 2,718 bytes of HTML, 2 ms, 0 redirect(s)

GROWTH SCORE: 72/100
  Crawl and index        16/25
  On-page SEO            21/30
  Structured data        10/10
  AI-search readiness     8/15
```

```text
score 56 -> 72
+ basics viewport meta 0 -> 2
+ basics html lang 0 -> 1
+ answers 2+ question headings 0 -> 4
+ answers short direct answers (heuristic) 0 -> 4
+ trust contact details 0 -> 3
+ trust policy links 0 -> 2
```

And the probe on the "loop-2" site (the tail of its output):

```text
Sitemap URLs found: 3
Sampled 3 URL(s)
    200 0 redirect(s)  http://127.0.0.1:8765/
    200 0 redirect(s)  http://127.0.0.1:8765/services/
    200 0 redirect(s)  http://127.0.0.1:8765/contact/

FINDINGS (worst first)
  None.

Blocking an AI crawler is a choice, not a fault. The list is short on purpose: add other tokens with --agent.
```

| | Before | After loop 1 | After loop 2 |
|---|---:|---:|---:|
| Growth Score | 23 | 56 | 72 |
| Crawl and index | 13/25 | 13/25 | 16/25 |
| On-page SEO | 10/30 | 21/30 | 21/30 |
| Structured data | 0/10 | 10/10 | 10/10 |
| AI-search readiness | 0/15 | 0/15 | 8/15 |
| Conversion | 0/20 | 12/20 | 17/20 |

## What is still lost, and why

```text
 1. [MEDIUM] links-images -5: no empty or generic anchors (-2); images have alt (-3)
 2. [MEDIUM] content -4: no skipped heading level (-2); 300+ words (rule of thumb) (-2)
 3. [MEDIUM] indexable -3: one canonical link (-3)
 4. [MEDIUM] trust -3: proof such as reviews (heuristic) (-3)
 5. [MEDIUM] basics -2: served over https (-2)
 6. [LOW] authority -7: author (-2); date (-2); 2+ outside sources (heuristic) (-3)
 7. [LOW] delivery -4: gzip and a cache header (-2); 3+ of 5 security headers (-2)
```

- `trust`, proof such as reviews (-3): I did not write a testimonial and I will not. The owner has to supply a real quote.
- `basics`, https (-2) and `delivery` (-4): hosting. A plain Python server cannot give them.
- `links-images`, `content`, `indexable`: queued for loop 3. The hero copy still reads "world-class" and "robust" (see the `text_stats.py` output above), and that belongs to `landing-page-copy`.
- `authority` (-7): an author line and outside source links do not fit a shop's homepage, so I leave those. A dated "prices last checked" line would earn the 2 date points; that goes in loop 3.

## What the score does not say

It says nothing about visitors, rankings or sales. The fixture has no traffic. On a real page the next step is the
measurement plan: compare the primary event against the baseline after at least two full weeks, and re-audit after every release.

Built by FinnTech3.
