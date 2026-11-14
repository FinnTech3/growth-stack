---
name: pricing-page-review
description: >
  Reviews how a pricing page presents plans and prices: plan count and names, the recommended plan, feature and limit
  wording, billing toggle honesty, tax clarity, risk reducers and objections, with severity-ranked findings and rewrites. Use when
  the user says "review my pricing page", "how should I structure my plans", "why do people skip the middle plan", "should I show
  prices or say contact us" or "is my pricing page clear". Do not use for choosing the price numbers from scratch, which needs the
  user's cost and customer value data, nor for general conversion copy (use `landing-page-copy`) or positioning (use `positioning-messaging`).
---

# Pricing page review

Requires: nothing to install. It works from the page the user names or pastes. If the user has run the `growth-loop`
audit, quote its `cta` (including `form_fields`) and `trust` evidence; otherwise read the page by hand.

I review the presentation of prices, not the prices. A price is a business decision that needs costs and what customers
will pay, and I will not invent either. What I can check is whether a buyer can tell what each plan is, what it costs
and what happens if they change their mind.

## Inputs

- The pricing page URL or its pasted text, and the plans, prices, billing periods and limits as the user states them.
- Who the plans are for, the refund, cancellation and trial terms exactly as they are, and whether prices include tax.
- What buyers ask before they buy (support questions, sales calls).

## Steps

1. Read the page as a buyer who is ready to choose. Note where you hesitate.
2. Count the plans. Rule of thumb: three or four is easy to compare; more needs a clear way to choose.
3. Check the names. A plan name should say who it is for, not rank (Solo, Studio, Team beats Bronze, Silver, Gold).
4. Check the recommended plan: one, visually distinct, with a stated reason ("most teams choose this" only if true and shown).
5. Check each plan: price, billing period, currency, what is included with the limits as numbers, and one button with the same label throughout.
6. Check the billing toggle: the default is honest, and any saving is shown as the actual amount, not a vague percentage you cannot verify.
7. Check tax and fees: is the price with or without VAT or sales tax, and are all fees visible before checkout?
8. Check risk reducers: trial length, cancel steps, refund window. Use the user's real terms, with the exact number of days.
9. Check objections with [the checklist](references/checklist.md): who is it not for, what happens at the limit, can I switch, who do I ask.
10. Rank findings: critical (hidden fees, misleading terms), high (unclear plan differences), medium, low. Write the fix for each.

## Output

A severity-ranked findings table (finding, where on the page, why it costs conversions, the rewrite); rewritten plan names
and feature bullets; the objections the page leaves unanswered; and a short experiment list with the measure for each.

## Exit criteria

- [ ] Each plan has a name, an audience, a price, a billing period and three to seven bullets with limits as numbers.
- [ ] One recommended plan is marked, with a reason that is true.
- [ ] Tax treatment, trial, cancellation and refund terms are stated exactly as the user supplied them.
- [ ] No dark pattern remains: no pre-ticked add-ons, no fees revealed late, no hidden cancellation.
- [ ] Every proposed change is tied to an event in `measurement-plan`, and no revenue effect is promised.

## Edge cases and errors

- Prices change by region or currency: show each region's real price and say which applies; do not convert by guesswork.
- "Contact us" pricing: fine for enterprise if a starting point or a clear route is shown; flag it when it hides small plans too.
- The user asks what to charge: say it needs cost and willingness-to-pay data, offer the questions to collect it, and do not name a number.
- Usage-based pricing: explain the unit, give one worked example, and show how the bill is capped if it is.
- A discount the user wants to show: only a real one with a real end date.
- Terms you cannot verify: ask. Do not write a refund promise the business has not made.

## Rules

- No invented prices, savings, discounts or testimonials.
- Plain words for limits: numbers, not "generous" or "unlimited" unless that is literally true.
- Do not promise higher sales. Say what becomes clearer.
- Dark patterns are findings, not options.
