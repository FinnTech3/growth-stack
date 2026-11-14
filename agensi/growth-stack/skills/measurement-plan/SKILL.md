---
name: measurement-plan
description: >
  Sets up measurement before a change ships: the decision it informs, one primary conversion event, supporting events with
  names and properties, a baseline, a UTM scheme, consent, a QA step for every event and a re-audit schedule. Use when the user
  says "set up analytics for this page", "what should I track", "define my conversion events", "set up UTM tracking" or "how will
  I know if the changes worked". Do not use for installing a specific analytics tool in code, reading an experiment's statistics,
  or building a dashboard; this skill defines what to measure and how to check it. For the page audit itself use `growth-loop`.
---

# Measurement plan

Requires: nothing to install. The plan is a document plus a QA checklist the user can run in their own analytics tool.

Measurement comes before the change, not after it. If nobody wrote down the baseline, nobody can say whether anything
moved. I start with the decision: what would you do differently if this number went up or down?

## Inputs

- The change being made and the page or journey it affects.
- The analytics tool in use and who owns it. If none, say so; the plan still stands.
- The one action that counts as success, and how people reach the page (campaigns, search, email).

## Steps

1. Write the decision each metric informs. Drop any metric that changes no decision.
2. Define one primary conversion event: its name, the exact trigger (what the visitor does), where it fires and what counts as a duplicate.
3. Add three to five supporting events along the path (see [naming](references/events.md)). Use `verb_noun` in snake case and a short list of properties.
4. Record the baseline before shipping: the number, the period (at least two full weeks so weekdays and weekends are both in, a rule of thumb),
   and the `growth-loop` Growth Score with its date. State that the score is a diagnostic, not a business result.
5. Define the UTM scheme: lowercase, no spaces, `source`, `medium`, `campaign`, and a record of every tagged link. Never tag internal links.
6. Decide consent and privacy: what is collected, the legal basis, how consent is asked and what happens when it is refused. State the rules
   to check for the user's region. This is not legal advice.
7. Write the QA step for each event: open the page, do the action, confirm the event in the tool's debug or real-time view, confirm the properties, confirm no duplicate.
8. Set the review: when to compare against the baseline, who looks and what decision follows each outcome.
9. Set the re-audit schedule: run `growth-loop` after every release that touches the page, and monthly otherwise.

## Output

The decision list; the event table (name, trigger, properties, owner, QA step, status); the UTM table; the baseline log
(metric, period, value, date, Growth Score); the consent note; the review and re-audit dates.

## Exit criteria

- [ ] There is exactly one primary conversion event with a definition and a trigger.
- [ ] Every event has a trigger, a property list, an owner and a QA step; each QA step was run or is marked pending.
- [ ] A baseline value, period and date are recorded before the change ships.
- [ ] The consent approach is stated, and the plan works for visitors who decline.
- [ ] A review date and a re-audit schedule are set.

## Edge cases and errors

- Low traffic: results will be noisy. Say so, widen the period and judge direction, not decimals.
- No analytics tool: record a manual count (form submissions, calls, bookings) with a date, and plan the tool.
- Conversions happen offline (phone, in person): add a way to ask "how did you hear about us" and log the answers.
- Campaign overlaps with the change: note it, because the effect cannot be separated.
- A visitor who declines consent: do not track them; report what the data excludes.
- Event fires twice or not at all in QA: fix before the change ships.

## Rules

- Measure to decide, not to collect.
- No metric without a definition, an owner and a check.
- Never read an effect from one week of data on a small number.
- Do not promise outcomes. State the question the data will answer.
