---
name: structured-data
description: >
  Writes, fixes and validates JSON-LD structured data for one page: Organization, WebSite, Article, Product, FAQPage,
  LocalBusiness and BreadcrumbList, with every required property filled from what the page really shows. Use when the user
  says "add schema markup", "fix my structured data", "add FAQ schema to this page", "generate JSON-LD for my product" or
  "why don't I get rich results". Do not use for titles and headings (use `on-page-seo`), content shaped for AI answers (use
  `ai-search-readiness`), Google Business Profile and citations (use `local-seo`) or crawl rules (use `technical-seo-audit`).
---

# Structured data

Requires: Python 3.10+ and network access to the live page. No accounts, keys or installs.

Structured data states facts a machine can check. I only mark up what a visitor can see on the page. Markup that
claims more than the page shows is worse than none.

## Inputs

- The page URL and its type (home, article, product, local business, FAQ).
- The real facts: legal or trading name, address, phone, prices, dates, author. Ask for any the page does not show.

## Running the script

`shared/scripts/page_audit.py` uses the network only to read the page you name and reads no local files. Write it unchanged to a
temporary file, run it, then delete it:

```sh
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/page_audit.XXXXXX")"   # paste shared/scripts/page_audit.py into it, unchanged
python3 "$SCRIPT" https://example.com/page --json       # read checks "schema", "authority" and the evidence under them
rm -f "$SCRIPT"
```

Exit 0 means no high gap, 1 means a high or critical gap or a failed fetch, 2 means bad input. A syntax error in a JSON-LD
block shows as `bad` greater than 0 in the `schema` evidence, and as a lost "all blocks parse" part.

## Steps

1. Run the audit. Read the `schema` evidence: how many blocks, how many failed to parse, which types, which properties are missing.
2. Choose the types the page has earned, using [the type guide](references/types.md). One main entity per page.
3. Build a single `@graph` block from [the templates](references/types.md). Give each entity an `@id` and link them (the
   `WebSite` publishes the `Organization`; the page belongs to the `WebSite`).
4. Fill every required property the audit names. Required, as the script checks them: Organization `name`; WebSite `name`
   and `url`; Article `headline`, `author` and `datePublished`; Product `name` plus one of `offers`, `review` or
   `aggregateRating`; FAQPage `mainEntity`; LocalBusiness `name`, `address` and `telephone`; BreadcrumbList `itemListElement`.
5. For each value, note where on the page it is visible. If it is not visible, either add it to the page or leave it out.
6. Dates in ISO 8601 (`2025-03-01`). Prices as numbers with `priceCurrency`. URLs absolute.
7. Validate twice: parse the block as JSON, then re-run the audit and confirm the parts recovered.
8. Tell the user to confirm the live page in the search engine's own rich results test. This skill cannot run it.

## Output

The complete `<script type="application/ld+json">` block ready to paste; a table of property, value and where it is
visible on the page; the audit parts before and after; and a list of anything left out because the page does not show it.

## Exit criteria

- [ ] The block parses as JSON and the audit's "all blocks parse" part is earned.
- [ ] Every type present has its required properties, so "common type has required properties" is earned.
- [ ] Every value in the block is visible on the page or in the user's supplied facts.
- [ ] No rating, review count, price or date was invented.
- [ ] The re-audit shows no regression elsewhere.

## Edge cases and errors

- Several blocks or a CMS plugin already emits some: merge into one graph or delete the duplicates; never output two competing `Organization`s.
- FAQPage on a page whose questions are not visible: do not add it. Eligibility for rich results changes, so promise nothing.
- Product without a price on the page: leave `offers` out and add the price to the page first.
- No `address` for a service-area business: use `areaServed`, and say the audit may still mark `LocalBusiness` incomplete.
- JSON that the audit cannot parse: report the exact line, fix the syntax, re-run. Do not paste a "fixed" block you did not parse.
- A subtype such as `Dentist`: the script knows a few; for others check the required properties by hand and say so.

## Rules

- Mark up the visible page only. No hidden claims, no reviews the business did not receive.
- One entity per fact. Reuse `@id` references instead of repeating objects.
- Do not promise rich results, rankings or clicks.
- Keep the user's real wording for names and descriptions.
