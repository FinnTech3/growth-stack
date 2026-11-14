# Event naming and tables

## Naming

- `verb_noun`, lowercase, snake case: `submit_quote_form`, `click_book_button`, `view_pricing`.
- Past or present tense, one style throughout.
- One name per action. Put the variation in properties, not in the name.
- Properties: `page`, `plan`, `source`, `form_id`. Keep to what the decision needs.

## Event table

| Event | Trigger | Properties | Owner | QA step | Status |
|---|---|---|---|---|---|
| `submit_quote_form` (primary) | Form submitted successfully | `page`, `source` | | Submit a test form; see one event with both properties | pending |

## UTM scheme

| Parameter | Rule | Example (fictional) |
|---|---|---|
| `utm_source` | Where the link is placed, lowercase | `newsletter` |
| `utm_medium` | The type: `email`, `social`, `cpc`, `referral` | `email` |
| `utm_campaign` | The campaign, lowercase with hyphens | `spring-service-offer` |

Tag links in emails, posts and ads. Never tag links between pages on the same site: it breaks the session and the source.

## Baseline log

| Metric | Period | Value | Recorded on | Growth Score at the time |
|---|---|---|---|---|

## QA checklist

1. Open the page in a clean browser window with the tool's debug view on.
2. Do the action. 3. Confirm one event with the right name and properties. 4. Refuse consent and confirm nothing is sent.
5. Repeat on a phone-sized window.
