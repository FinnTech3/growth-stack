# Which type, and a template for each

| Page | Main type | Add |
|---|---|---|
| Homepage | `WebSite` + `Organization` | `sameAs` profile URLs |
| Blog post or guide | `Article` | `author`, `datePublished`, `dateModified`, `BreadcrumbList` |
| Product page | `Product` | `offers` with price and currency, `aggregateRating` only if the rating is on the page |
| Shop, office or clinic | `LocalBusiness` | opening hours, `geo`, `sameAs` |
| Page with visible Q and A | `FAQPage` | only the questions shown |
| Any inner page | `BreadcrumbList` | matches the visible trail |

All names below are fictional placeholders.

```json
{"@context": "https://schema.org", "@graph": [
 {"@type": "Organization", "@id": "https://example.com/#org", "name": "Example Ltd", "url": "https://example.com/",
  "sameAs": ["https://example.org/example-ltd"]},
 {"@type": "WebSite", "@id": "https://example.com/#site", "name": "Example", "url": "https://example.com/",
  "publisher": {"@id": "https://example.com/#org"}}
]}
```

```json
{"@type": "Article", "headline": "How a bike service works", "datePublished": "2025-03-01", "dateModified": "2025-04-02",
 "author": {"@type": "Person", "name": "Sam Okoro"}, "publisher": {"@id": "https://example.com/#org"},
 "mainEntityOfPage": "https://example.com/blog/bike-service"}
```

```json
{"@type": "Product", "name": "Brake service", "description": "Front and rear brake service.",
 "offers": {"@type": "Offer", "price": "45.00", "priceCurrency": "GBP", "availability": "https://schema.org/InStock"}}
```

```json
{"@type": "LocalBusiness", "name": "Harbour Street Bikes", "telephone": "+44 1632 960123",
 "address": {"@type": "PostalAddress", "streetAddress": "4 Harbour Street", "addressLocality": "Exampletown", "postalCode": "AB1 2CD"},
 "openingHours": "Mo-Sa 09:00-17:30", "sameAs": ["https://example.org/harbour-street-bikes"]}
```

```json
{"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "How much does a service cost?",
 "acceptedAnswer": {"@type": "Answer", "text": "A basic service costs 45 pounds."}}]}
```

```json
{"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/"},
 {"@type": "ListItem", "position": 2, "name": "Services"}]}
```

Use `LocalBusiness` or one of its subtypes (for example `Dentist`) for a place people visit. Never put a fabricated
`aggregateRating` or `review` in any block.
