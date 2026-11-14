---
name: launch-plan
description: >
  Builds a launch plan for a product or feature: tier, goal, audiences, assets, owned then earned then paid channels, a dated
  timeline with owners, go and no-go criteria, a rollback, and a post-launch review. Use when the user says "plan my product
  launch", "launch checklist for this feature", "how should I announce this", "write a launch timeline" or "are we ready
  to launch". Do not use for the positioning itself (use `positioning-messaging`), the launch page's conversion copy (use
  `landing-page-copy`), the email copy (use `email-sequence`) or setting up the tracking (use `measurement-plan`).
---

# Launch plan

Requires: nothing to install. It works from the facts the user gives. If the launch page is live, run `growth-loop` on it first.

A launch is a dated list of owned tasks with a way to say "not yet". I would rather ship a smaller launch on time with
measurement ready than a large one nobody can learn from.

## Inputs

- What is launching, the date the user wants and the one goal number the user owns (sign-ups, orders, bookings).
- The audience segments, the channels the user already owns (list, site, profiles) and the budget, if any.
- Who is on the team and who owns each area.

## Steps

1. Pick the tier: small (a feature note), medium (a feature with an announcement) or large (a product launch). Size the plan to the tier.
2. Write the goal as one number, a date and where it is counted. Agree it with the owner.
3. List the audiences and what each needs to hear. Reuse the message hierarchy from `positioning-messaging` if one exists.
4. List the assets: the launch page, the announcement, emails (outline only; use `email-sequence`), social posts, help docs, a short demo.
5. Order channels owned first, then earned, then paid. Do not plan paid spend until the page converts.
6. Build the timeline with [the template](references/timeline.md): from about two weeks before to two weeks after, each task with an owner and a done-when.
7. Write go and no-go criteria that can be checked: the page returns 200 and passes the audit's critical items, the form works,
   tracking fires, support knows the answer to the top five questions.
8. Write the rollback: how to switch the launch off, who decides, and the message to send if it breaks.
9. Set the review: the same metrics at one week and two weeks, in the same place, compared with the baseline.

## Output

The tier and goal; the audience and asset list; the dated timeline table; the go and no-go checklist with the current status
of each item; the rollback; the review template. End with the three tasks that, if late, should move the date.

## Exit criteria

- [ ] The goal is one number with a date and a counting source.
- [ ] Every task has an owner and a done-when.
- [ ] Measurement is set up and tested before launch day, not after.
- [ ] Go and no-go criteria are checkable, and the launch page was audited with `growth-loop`.
- [ ] A rollback and a review date exist.
- [ ] No result is promised and no number in the plan is invented.

## Edge cases and errors

- No audience of their own: plan for earning attention slowly; do not assume a launch day spike.
- The date is fixed and the page is not ready: cut scope, not the checks.
- Several launches in one week: stagger them, or merge into one message.
- Nothing to measure yet: make the first launch a learning launch and say which question it answers.
- Press or partner dates the user cannot control: put them in the timeline as dependencies with a fallback.
- A rollback that is only "hope": it is not a rollback. Write the switch.

## Rules

- Owned channels before paid ones.
- No invented numbers, quotes, partners or press.
- Say "no-go" when a critical check fails.
- A launch plan promises effort and measurement, never outcomes.
