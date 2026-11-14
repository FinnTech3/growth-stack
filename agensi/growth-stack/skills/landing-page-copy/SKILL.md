---
name: landing-page-copy
description: >
  Reviews and rewrites a landing page for conversion in the page's own voice: hero, call to action, form, proof and objections,
  measured with an audit and a text analysis before and after. Use when the user says "rewrite my landing page", "why isn't
  this page converting", "review my homepage for conversion", "write a headline and call to action" or "shorten my signup
  form". Do not use for choosing the positioning (use `positioning-messaging`), pricing plans (use `pricing-page-review`),
  email copy (use `email-sequence`) or title and meta description work (use `on-page-seo`).
---

# Landing page copy and conversion review

Requires: Python 3.10+. `page_audit.py` needs network access to the live page and reads no local files. `text_stats.py` is
offline, makes no network calls and reads one text file or stdin.

A landing page has one visitor, one job and one action. Here is what I would change first: the button label, the form,
then the line above the button. Those three decide most pages, and the audit can see all of them.

## Inputs

- The page URL, the single action it exists for, and where the traffic comes from (the ad, email or search that promises something).
- The positioning, if it exists. If the page claims nothing distinctive, run `positioning-messaging` first.
- Real proof the user holds: a quote they may use, a number from their records, a client name.

## Running the scripts

Write each script (`shared/scripts/page_audit.py`, `shared/scripts/text_stats.py`) unchanged to a temporary file, run it, then delete it.

```sh
A="$(mktemp "${TMPDIR:-/tmp}/page_audit.XXXXXX")"; T="$(mktemp "${TMPDIR:-/tmp}/text_stats.XXXXXX")"
python3 "$A" https://example.com/landing --json   # checks "cta" and "trust": button, label, form fields, contact, policies, proof
python3 "$T" hero-and-body.md --json              # readability, you versus we, hedges, hype words
rm -f "$A" "$T"
```

Exit 0 and 1 follow the audit (1 means a high or critical gap). Exit 2 means bad input.

## Steps

1. Run the audit. Quote the `cta` and `trust` evidence: the first action label, any generic labels, the largest form, contact, policies and proof.
2. Measure the current copy with `text_stats.py`. Keep its sentence length and register.
3. Check message match: does the headline repeat the promise that brought the visitor? If not, that is gap one.
4. Rewrite the hero with [the structure](references/structure.md): a headline that states the outcome for the visitor, a
   line saying how and for whom, one verb-led button naming the outcome, and a proof line beside it.
5. Cut the form to what is needed for the next step. Rule of thumb: five fields or fewer. Move everything else to after the conversion.
6. Rewrite the sections below in order of the visitor's doubts: how it works, proof, objections, then the button again.
7. Replace hype and vague words with specifics the user can back. Run `text_stats.py` again.
8. Add the missing trust items the user really has: contact details, policy links, a real quote. Leave a marked gap where proof is needed.
9. Re-run the audit and compare. Hand the measure to `measurement-plan`.

## Output

Before and after for each section with the reason for each change; the new button and form spec; the open questions that
need real proof; the `text_stats.py` readings before and after; the audit parts recovered; the measure to watch.

## Exit criteria

- [ ] The audit shows a verb-led CTA with a specific label and a largest form of five fields or fewer.
- [ ] The headline repeats the promise from the traffic source, or the mismatch is listed for the user.
- [ ] `text_stats.py` shows the hype list empty and the you count above the we count, or says why not.
- [ ] No claim, number, quote or client name is invented; missing proof is a marked gap.
- [ ] A re-audit shows the `cta` and `trust` parts recovered and no regression.

## Edge cases and errors

- Single page with no form: the "largest form" part passes; tell the user what the button leads to.
- Several competing buttons: pick the primary action and demote the rest to text links.
- The user wants a test: a split test needs many conversions per variant for a clear result (rule of thumb); below that, ship and compare before and after, and say it is weak evidence.
- Regulated claims (health, finance): flag them for the user's own review; do not write them.
- Page is behind a form or script: ask the user to paste the rendered copy.
- `text_stats.py` or the audit exits non-zero: report the exact message first.

## Rules

- Write in the page's own voice. Do not replace it with yours.
- No invented proof. A gap is better than a lie.
- One page, one action.
- Never promise a conversion rate.
