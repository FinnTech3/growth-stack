---
name: email-sequence
description: >
  Designs and writes an email sequence for people who have opted in: a trigger, a goal, a map of emails with delays, a subject,
  preview text and body for each, an exit rule, and a readability check. Use when the user says "write a welcome email
  sequence", "draft onboarding emails", "write a follow-up sequence for my leads", "improve my abandoned basket emails" or "how many
  emails should my nurture sequence have". Do not use for cold outreach to people who have not opted in, one-off newsletters,
  text messages, landing page copy (use `landing-page-copy`) or deciding positioning (use `positioning-messaging`).
---

# Email sequence

Requires: Python 3.10+. `text_stats.py` is offline, makes no network calls and reads one text file or stdin.

One sequence, one goal. Most weak sequences have six emails because someone liked the number. I start from the moment the
person joined and ask what they need next.

## Inputs

- The trigger (signed up, bought, abandoned a basket, downloaded something) and the one conversion the sequence is for.
- What the sender knows about each person, and nothing more. Personalise only from fields that exist.
- The sender's existing emails or pages, for voice, and the facts and proof the user holds.
- Confirmation that the people on the list opted in. If not, stop and tell the user.

## Running the script

Write `shared/scripts/text_stats.py` unchanged to a temporary file, run it on each email body (one file per email), then delete it:

```sh
SCRIPT="$(mktemp "${TMPDIR:-/tmp}/text_stats.XXXXXX")"   # paste shared/scripts/text_stats.py into it, unchanged
python3 "$SCRIPT" email-1.md --json                      # length, readability, you versus we, hedges, hype words
rm -f "$SCRIPT"
```

Exit 0 is success. Exit 2 means a missing file, empty or binary input or a bad option.

## Steps

1. Write the goal as one measurable event and the exit rule: the sequence stops for anyone who has done it.
2. Map the sequence with [the template](references/sequence.md): email number, delay, purpose, one call to action.
   Start with the smallest number that covers the doubts a new person has. Add an email only for a new purpose.
3. Write each subject: aim for 50 characters or fewer (rule of thumb), plain, specific, no capital shouting. Give two options.
4. Write preview text that adds to the subject instead of repeating it.
5. Write the body in the sender's voice: short paragraphs, one idea, one link that matters, the sender's real name.
6. Run `text_stats.py` on each. Check length, reading ease and the you-versus-we count; cut hype and hedges.
7. Add the required footer: who is sending, why they got it, and a working unsubscribe. Check the user's local rules; this is not legal advice.
8. Tag each link with the UTM scheme from `measurement-plan` and list which events count.
9. Write a plain-text version and read it aloud for sense.

## Output

The sequence map; for each email the subject options, preview text, body and the `text_stats.py` readings; the exit
rule; the link and tracking list; and the questions the user must answer before sending.

## Exit criteria

- [ ] The list is opted in, and the footer carries sender identity and an unsubscribe.
- [ ] Every email has one purpose and one call to action.
- [ ] The sequence has an exit rule tied to the goal event.
- [ ] No claim, figure, testimonial or discount is invented; offers come from the user.
- [ ] Each email has been measured and is within the reading ease and length the user's earlier emails set.
- [ ] Links are tagged and the success event is defined.

## Edge cases and errors

- No opt-in record: do not draft. Explain that consent comes first and point the user to their local rules.
- The user wants urgency: only real deadlines. Never a countdown that resets.
- Abandoned basket: remind and help. Do not invent stock levels or discounts.
- Opens are not reliable because mail apps can load images automatically. Judge by clicks and the downstream event.
- A person replies: stop automation for them and let a human answer.
- The script exits 2: report the message, fix the file and re-run.

## Rules

- Write like the sender talks.
- One email, one ask.
- No fake scarcity, no fake personalisation, no hidden unsubscribe.
- Never promise open rates or revenue.
