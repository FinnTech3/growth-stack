# Routing the audit findings to a fixer

Each audit check has an id. Send the lost parts to the skill that fixes them. If a gap has no row here, say so and ask.

| Check id | Lost part (examples) | Fixer skill | First thing I would change |
|---|---|---|---|
| `basics` | not a 200, extra redirect, no https | `technical-seo-audit` | The final URL. Link and redirect straight to it. |
| `basics` | no viewport meta, no `lang` | `on-page-seo` | Two lines in `<head>` and `<html>`. |
| `indexable` | `noindex`, zero or two canonicals | `technical-seo-audit` | The `noindex`. It outranks everything else on the list. |
| `delivery` | no gzip, no cache header, few security headers, slow | `technical-seo-audit` | Compression. It is one server setting. |
| `snippet` | title or description missing or the wrong length, share tags missing | `on-page-seo` | The title, then the description. |
| `content` | no or many H1s, one H2, skipped levels, under 300 words | `on-page-seo` | One H1 that states the topic. |
| `links-images` | few internal links, generic anchors, no alt text | `internal-linking` | Anchors that say what the target is. |
| `schema` | no JSON-LD, invalid JSON, missing required properties | `structured-data` | One valid block for the real entity. |
| `schema` on a business with a shop or area | no `LocalBusiness` | `local-seo`, then `structured-data` | Name, address and phone, identical everywhere. |
| `answers` | no question headings, long answers | `ai-search-readiness` | Two question headings with 8 to 60 word answers. |
| `authority` | no author, no date, no sources | `ai-search-readiness` | Byline and a dated `<time>` element. |
| `cta` | no verb-led button, generic label, long form | `landing-page-copy` | The button label, then the form. |
| `trust` | no contact, no policies, no proof | `landing-page-copy` (`pricing-page-review` for plans) | The real contact details. Proof only if the user has it. |

## When the audit is not the problem

- The page says nothing distinctive: stop and use `positioning-messaging` before rewriting anything.
- There is no way to tell whether a change worked: use `measurement-plan` before shipping.
- The page is for a launch: use `launch-plan` for the timeline and keep this loop for the page.
