# Trigger tests: Growth Stack

Agensi's pre-publish rule: a skill triggers on its relevant prompts and not on unrelated ones. For a pack, the agent picks
one skill by name and description, so each prompt below must load the skill named beside it, and no other.

Status: **not yet run in an agent.** I wrote these prompts and checked them by reading each description against its
neighbours, which is not the same thing. Run each prompt in a fresh session with the pack installed and tick the box when the
right skill loads. Run them again after a model update.

## Should trigger (two prompts per skill)

| Skill | Prompt 1 | Prompt 2 |
|---|---|---|
| `growth-loop` | [ ] Audit https://example.com/pricing and tell me what to fix first | [ ] Re-audit my homepage now that I've changed the title and form |
| `technical-seo-audit` | [ ] Check my robots.txt and sitemap and tell me if anything blocks Google | [ ] Are AI crawlers blocked on my site? |
| `on-page-seo` | [ ] Rewrite my page title and meta description for "bike repair" | [ ] My headings are a mess, fix the outline of this page |
| `structured-data` | [ ] Add FAQ schema to this page | [ ] Generate JSON-LD for my product page and check it parses |
| `ai-search-readiness` | [ ] Make this page more likely to be quoted in AI answers | [ ] Can AI assistants read my site and what should I change on this page? |
| `local-seo` | [ ] Help me show up near me: check my name, address and phone are consistent | [ ] Write a service area page for my plumbing business |
| `keyword-clusters` | [ ] Cluster this keyword export into topics | [ ] Which of these keywords belong on the same page? |
| `content-brief` | [ ] Write a content brief for an article on e-bike batteries | [ ] Brief a writer on this topic and check their draft against it |
| `internal-linking` | [ ] Which pages should link to my pricing page? | [ ] Find orphan pages and fix my "click here" anchors |
| `positioning-messaging` | [ ] Define our positioning and who our ideal customer is | [ ] What makes us different? Build a messaging framework from these customer reviews |
| `landing-page-copy` | [ ] Why isn't this landing page converting? Rewrite the hero and button | [ ] Shorten my signup form and fix the call to action |
| `email-sequence` | [ ] Write a five-email welcome sequence for new subscribers | [ ] Improve my abandoned basket emails |
| `pricing-page-review` | [ ] Review my pricing page | [ ] Why do people skip the middle plan? |
| `launch-plan` | [ ] Plan the launch of our new feature with a timeline | [ ] Are we ready to launch? Give me a go or no-go checklist |
| `measurement-plan` | [ ] What should I track on this page and how do I set up UTMs? | [ ] How will I know if my changes worked? Define the conversion events |

## Near misses (must load the neighbour named, not the skill in the first column)

| Prompt | Should load | Not |
|---|---|---|
| Write the actual JSON-LD for my local shop | `structured-data` | `local-seo` |
| Group these 500 keywords by intent | `keyword-clusters` | `content-brief` |
| Rewrite my homepage headline and button | `landing-page-copy` | `positioning-messaging` |
| Why is Google not indexing my whole site? | `technical-seo-audit` | `growth-loop` |

## Should not trigger any skill

- [ ] Write a Python function that parses dates
- [ ] What is the capital of France?
- [ ] Translate this paragraph to Spanish
- [ ] Write a poem about the sea
- [ ] Explain what a closure is
- [ ] Help me pick a laptop
- [ ] Send a cold email to 500 people who never signed up
- [ ] Summarise this article
- [ ] Write a SQL query that joins orders to customers
- [ ] What is 17 times 23?
