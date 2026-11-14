---
name: local-seo
description: >
  Makes a business easy to find and trust for local searches: one source of truth for name, address and phone, consistency
  across the site, profile and directories, location and service-area pages, and a review routine. Use when the user says
  "improve my local SEO", "help me show up near me", "set up my Google Business Profile", "check my NAP consistency" or "write
  a service area page". Do not use for national or sitewide technical audits (use `technical-seo-audit`), writing the
  JSON-LD itself (use `structured-data`), generic on-page copy (use `on-page-seo`) or buying reviews, which this skill refuses.
---

# Local SEO

Requires: nothing to install. It works from the pages and listings the user names or pastes. If the user has run the
`growth-loop` audit, quote its `schema` and `trust` evidence; if not, ask the user to run that first or read the page by hand.

Local results lean on three things: relevance, distance and prominence. You cannot move distance. You can make the
business clear, consistent and well reviewed, and I would start with consistency because it is cheap and checkable.

## Inputs

- The exact trading name, address, phone number and opening hours, as the user wants them shown everywhere (the source of truth).
- Primary category and 2 or 3 services. Whether customers visit the premises or the business travels to them.
- Links or pasted text for: the site's contact page, the profile listing, and 3 to 5 directory listings.

## Steps

1. Write the source of truth as one block: name, address, phone, hours, categories, website, service areas.
2. Build a consistency table: one row per place the details appear (site header, contact page, schema, profile, each directory).
   Compare the three core fields character by character. Mark each as match, minor difference (abbreviation) or conflict.
3. Fix conflicts at the source first (the site), then the profile, then directories. Minor differences get one standard form.
4. Check the profile against [the checklist](references/profile-checklist.md): categories, services, hours, photos, description, links.
5. For a business that serves one place from a premises, write a location page: who and where, services, opening hours,
   directions and parking, local proof, a map, real local questions. For service areas, write one page per area only when
   each can say something true and different; otherwise one page that lists the areas.
6. Hand the structured data to `structured-data` with the source of truth as the input.
7. Plan reviews: ask recently served customers after the job, in the same message, with one direct link. Reply to every review,
   good or bad, in a calm and specific way. Never offer rewards for reviews, gate who is asked, or write your own.
8. Set the measure with `measurement-plan`: calls, direction requests and form fills from the profile and the page, each tagged.

## Output

The source-of-truth block; the consistency table with every mismatch and its fix; location or area page copy in the
business's own voice; the profile changes as a list; a review request message and reply templates; the measurement list.

## Exit criteria

- [ ] One source of truth is approved by the user and is the only version used.
- [ ] The consistency table has no conflict rows left, or each has an owner and a reason.
- [ ] Every location page contains something true that only that location can say.
- [ ] No fake address, virtual office or invented review appears anywhere.
- [ ] The measurement list names how calls and direction requests will be counted.

## Edge cases and errors

- Several locations: one page per location, one profile per location, and a different phone line only if the business really has one.
- Home-based or no-visitors business: hide the address on the profile if the guidelines require it, and use service areas honestly.
- Name changed or moved premises: list every old form so listings can be found and updated; keep the old address redirect note.
- Customer says a competitor has fake reviews: report it through the platform's own process; do not retaliate.
- Missing phone, hours or address on the page: ask. Never guess a detail.
- A listing the agent cannot open: record "not checked" in the table. Do not mark it a match.

## Rules

- Accuracy beats volume. Ten consistent listings beat fifty messy ones.
- No keyword stuffing in the business name; use the real name.
- No claims such as "number one" or "best" without evidence the user can show.
- Do not promise a map ranking.
