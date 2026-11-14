"""HTML fixtures. GOOD earns every point except the https one when served over plain http; BAD has every flaw."""

GOOD_HEADERS = {
    "cache-control": "max-age=300",
    "content-encoding": "gzip",
    "strict-transport-security": "max-age=31536000",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
}

BODY_TEXT = " ".join(
    "We service road bikes, mountain bikes and e-bikes from our workshop, and every job starts with a free check so "
    "you know the price before we pick up a spanner."
    for _ in range(9)
)

GOOD = f"""<!doctype html>
<html lang="en-GB"><head>
<meta charset="utf-8">
<title>Bike repair in Harbour Street, same-day service</title>
<meta name="description" content="Same-day bike repair and servicing in Harbour Street. Fixed prices, free quotes and a 90 day workshop guarantee on every job.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Sam Okoro">
<link rel="canonical" href="https://example.test/">
<meta property="og:title" content="Bike repair in Harbour Street">
<meta property="og:description" content="Same-day bike repair and servicing.">
<meta property="og:image" content="https://example.test/og.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context": "https://schema.org", "@graph": [
 {{"@type": "LocalBusiness", "name": "Harbour Street Bikes", "telephone": "+44 1632 960123",
   "address": {{"@type": "PostalAddress", "streetAddress": "4 Harbour Street", "postalCode": "AB1 2CD"}},
   "sameAs": ["https://example.org/harbour-street-bikes"]}},
 {{"@type": "Organization", "name": "Harbour Street Bikes", "url": "https://example.test/"}},
 {{"@type": "BreadcrumbList", "itemListElement": [{{"@type": "ListItem", "position": 1, "name": "Home"}}]}}
]}}
</script>
</head><body>
<header><nav><a href="/services/">Services and prices</a> <a href="/about/">About the workshop</a></nav></header>
<main>
<h1>Bike repair that gets you riding today</h1>
<p>By Sam Okoro, <time datetime="2025-03-01">1 March 2025</time>. Call <a href="tel:+441632960123">01632 960123</a>.</p>
<a class="btn" href="/book/">Book a repair</a>
<img src="/shop.jpg" alt="The workshop on Harbour Street">
<h2>How much does a service cost?</h2>
<p>A basic service costs 45 pounds and covers brakes, gears, tyres and a safety check, with parts charged at cost.</p>
<h2>Do you collect bikes from home?</h2>
<p>Yes. We collect and return within five miles of the shop for a flat 10 pounds, usually the same day.</p>
<h2>What we repair</h2>
<ul><li>Brakes and gears</li><li>Punctures and wheels</li><li>E-bike batteries</li></ul>
<p>{BODY_TEXT}</p>
<p>Read the <a href="https://example.org/guide">tyre pressure guide</a> and the <a href="https://example.net/safety">cycle safety rules</a>.</p>
<blockquote class="testimonial">Testimonial: they fixed my brakes in an hour.</blockquote>
<form action="/quote" method="post"><input name="name"><input name="email"><input type="hidden" name="t"><button type="submit">Get my quote</button></form>
</main>
<footer><a href="/privacy/">Privacy policy</a> <a href="/terms/">Terms</a></footer>
</body></html>
"""

BAD = """<html><head><meta name="robots" content="noindex,nofollow"></head><body>
<h3>Welcome</h3><h1>Home</h1><h1>Also home</h1>
<p>Lorem ipsum.</p>
<a href="/a">click here</a> <a href="/b">read more</a> <a href="/c"></a>
<img src="/x.jpg"><img src="/y.jpg">
<form><input name="a"><input name="b"><input name="c"><input name="d"><input name="e"><input name="f"><button>Submit</button></form>
</body></html>
"""
