"""page_audit.py: the score arithmetic, every flaw and every pass, and the fetch layer against a local server."""

from __future__ import annotations

import functools
import gzip
import json
import socket
import sys

import pytest
from conftest import SCRIPTS, fake_response
from pages import BAD, BODY_TEXT, GOOD, GOOD_HEADERS


def lost(result) -> set[str]:
    return {p["label"] for c in result["checks"] for p in c["parts"] if not p["earned"]}


def audit(pa, html, **kw):
    return pa.analyze(fake_response(html, headers=kw.pop("headers", GOOD_HEADERS), **kw))


# ---- the rubric and the score arithmetic -------------------------------------------------------------------------


def test_rubric_adds_up_to_exactly_100(pa):
    total = sum(int(w) for spec in pa.RUBRIC.values() for _, w, _ in spec[3])
    assert total == 100


def test_every_check_has_a_category_why_fix_and_known_severities(pa):
    for cid, (cat, why, fix, spec) in pa.RUBRIC.items():
        assert cat in pa.CATS, cid
        assert why and fix, cid
        assert spec and all(sev in "chml" for _, _, sev in spec), cid


def test_perfect_page_scores_100_with_nothing_to_fix(pa):
    res = audit(pa, GOOD)
    assert (res["score"], res["max"]) == (100, 100)
    assert res["priority"] == [] and res["notes"] == []
    assert "Nothing to fix" in pa.render(res)


def test_every_point_is_accounted_for(pa):
    res = audit(pa, BAD, url="http://example.test/")
    assert res["score"] == sum(p["earned"] for c in res["checks"] for p in c["parts"])
    assert res["max"] == sum(p["points"] for c in res["checks"] for p in c["parts"]) == 100
    for c in res["checks"]:
        assert c["earned"] == sum(p["earned"] for p in c["parts"]) and c["max"] == sum(p["points"] for p in c["parts"])
    cats = res["categories"]
    assert sum(v["earned"] for v in cats.values()) == res["score"]
    assert sum(v["max"] for v in cats.values()) == 100
    assert cats["Crawl and index"]["max"] == 25 and cats["On-page SEO"]["max"] == 30
    assert cats["Structured data"]["max"] == 10 and cats["AI-search readiness"]["max"] == 15
    assert cats["Conversion"]["max"] == 20


def test_text_report_names_every_part_and_its_points(pa):
    text = pa.render(audit(pa, BAD, url="http://example.test/"))
    for label in ("200 status", "no noindex", "has a title", "exactly one H1", "has JSON-LD", "verb-led CTA"):
        assert label in text
    assert "GROWTH SCORE: " in text and "EVERY POINT" in text and "FIX FIRST" in text
    assert text.count("+") >= 1 and text.count("-") >= 10


def test_priority_orders_by_severity_then_points_lost(pa):
    res = audit(pa, BAD, url="http://example.test/")
    by = {c["id"]: c for c in res["checks"]}
    keys = [(pa.SEV.index(by[i]["severity"]), by[i]["earned"] - by[i]["max"]) for i in res["priority"]]
    assert keys == sorted(keys)
    assert by[res["priority"][0]]["severity"] == "critical"
    assert set(res["priority"]) == {c["id"] for c in res["checks"] if c["earned"] < c["max"]}


def test_severity_of_a_finding_is_its_worst_lost_point(pa):
    res = audit(pa, GOOD.replace(' name="description"', ' name="x"'), headers=GOOD_HEADERS)
    snippet = next(c for c in res["checks"] if c["id"] == "snippet")
    assert snippet["severity"] == "high"  # a missing description is "h" in the rubric
    assert [p["label"] for p in snippet["parts"] if not p["earned"]] == [
        "has a meta description",
        "description 70-160 characters",
    ]


# ---- every flaw, one at a time -----------------------------------------------------------------------------------

MUTATIONS = [
    (
        "no title",
        lambda h: h.replace("<title>Bike repair in Harbour Street, same-day service</title>", ""),
        "has a title",
    ),
    (
        "short title",
        lambda h: h.replace("Bike repair in Harbour Street, same-day service", "Bikes"),
        "title 30-60 characters",
    ),
    ("long title", lambda h: h.replace("same-day service", "same-day service " * 5), "title 30-60 characters"),
    ("no description", lambda h: h.replace('name="description"', 'name="other"'), "has a meta description"),
    (
        "short description",
        lambda h: h.replace(
            "Same-day bike repair and servicing in Harbour Street. Fixed prices, free quotes and a 90 day "
            "workshop guarantee on every job.",
            "Short.",
        ),
        "description 70-160 characters",
    ),
    ("noindex meta", lambda h: h.replace("<title>", '<meta name="robots" content="noindex"><title>'), "no noindex"),
    (
        "two canonicals",
        lambda h: h.replace(
            '<link rel="canonical" href="https://example.test/">',
            '<link rel="canonical" href="https://example.test/"><link rel="canonical" href="https://example.test/x">',
        ),
        "one canonical link",
    ),
    (
        "no canonical",
        lambda h: h.replace('<link rel="canonical" href="https://example.test/">', ""),
        "one canonical link",
    ),
    ("no lang", lambda h: h.replace(' lang="en-GB"', ""), "html lang"),
    (
        "no viewport",
        lambda h: h.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', ""),
        "viewport meta",
    ),
    ("no h1", lambda h: h.replace("<h1>Bike repair that gets you riding today</h1>", ""), "exactly one H1"),
    ("two h1", lambda h: h.replace("<h2>What we repair</h2>", "<h1>Second</h1>"), "exactly one H1"),
    (
        "skipped level",
        lambda h: h.replace("<h2>What we repair</h2>", "<h4>What we repair</h4>"),
        "no skipped heading level",
    ),
    ("thin page", lambda h: h.replace(BODY_TEXT, "Short."), "300+ words (rule of thumb)"),
    ("no alt", lambda h: h.replace(' alt="The workshop on Harbour Street"', ""), "images have alt"),
    ("generic anchor", lambda h: h.replace("tyre pressure guide", "click here"), "no empty or generic anchors"),
    ("empty anchor", lambda h: h.replace("</footer>", '<a href="/z"></a></footer>'), "no empty or generic anchors"),
    (
        "few internal links",
        lambda h: (
            h.replace('<a href="/services/">', "<span>")
            .replace('<a href="/about/">', "<span>")
            .replace('<a href="/book/">', "<span>")
            .replace('<a href="/privacy/">', "<span>")
        ),
        "3+ internal links",
    ),
    (
        "no og image",
        lambda h: h.replace('property="og:image"', 'property="og:x"'),
        "og:title, description, image and twitter:card",
    ),
    (
        "no twitter card",
        lambda h: h.replace('name="twitter:card"', 'name="x"'),
        "og:title, description, image and twitter:card",
    ),
    ("no json-ld", lambda h: h.replace("application/ld+json", "text/plain"), "has JSON-LD"),
    (
        "broken json-ld",
        lambda h: h.replace('"@context": "https://schema.org",', '"@context": "https://schema.org" ,,'),
        "all blocks parse",
    ),
    (
        "local business without phone",
        lambda h: h.replace('"telephone": "+44 1632 960123",', ""),
        "common type has required properties",
    ),
    (
        "no questions",
        lambda h: h.replace("How much does a service cost?", "Service cost").replace(
            "Do you collect bikes from home?", "Collection"
        ),
        "2+ question headings",
    ),
    (
        "answer too long",
        lambda h: h.replace(
            "A basic service costs 45 pounds and covers brakes, gears, tyres and a safety check, with parts "
            "charged at cost.",
            "word " * 80,
        ),
        "short direct answers (heuristic)",
    ),
    (
        "no author",
        lambda h: (
            h.replace('<meta name="author" content="Sam Okoro">', "")
            .replace("By Sam Okoro, ", "")
            .replace('"sameAs"', '"x"')
        ),
        "author",
    ),
    ("no date", lambda h: h.replace('<time datetime="2025-03-01">1 March 2025</time>', "1 March 2025"), "date"),
    (
        "no outside sources",
        lambda h: h.replace("https://example.org/guide", "/guide").replace("https://example.net/safety", "/safety"),
        "2+ outside sources (heuristic)",
    ),
    (
        "no cta",
        lambda h: h.replace('<a class="btn" href="/book/">Book a repair</a>', "").replace("Get my quote", ""),
        "verb-led CTA",
    ),
    ("generic cta label", lambda h: h.replace("Get my quote", "Submit"), "specific label"),
    (
        "long form",
        lambda h: h.replace(
            '<input name="email">',
            '<input name="email"><input name="a"><input name="b"><input name="c"><input name="d">',
        ),
        "largest form has 5 fields or fewer (rule of thumb)",
    ),
    (
        "no contact",
        lambda h: (
            h.replace('<a href="tel:+441632960123">01632 960123</a>', "us")
            .replace('"telephone": "+44 1632 960123"', '"x": 1')
            .replace('"postalCode": "AB1 2CD"', '"x": 1')
            .replace('"streetAddress": "4 Harbour Street",', "")
        ),
        "contact details",
    ),
    (
        "no policy links",
        lambda h: h.replace('<a href="/privacy/">Privacy policy</a> <a href="/terms/">Terms</a>', ""),
        "policy links",
    ),
    (
        "no proof",
        lambda h: h.replace(
            '<blockquote class="testimonial">Testimonial: they fixed my brakes in an hour.</blockquote>', ""
        ),
        "proof such as reviews (heuristic)",
    ),
]


@pytest.mark.parametrize(("name", "mutate", "label"), MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_each_flaw_costs_its_named_point_and_only_that_check(pa, name, mutate, label):
    base = lost(audit(pa, GOOD))
    mutated = mutate(GOOD)
    assert mutated != GOOD, f"mutation {name} changed nothing"
    now = lost(audit(pa, mutated))
    assert label in now - base, f"{name}: expected '{label}' lost, got {sorted(now - base)}"


def test_the_flaws_page_loses_most_points_and_the_perfect_page_loses_none(pa):
    bad = audit(pa, BAD, url="http://example.test/", headers={})
    assert bad["score"] < 25
    assert {"no noindex", "has a title", "exactly one H1", "verb-led CTA", "has JSON-LD"} <= lost(bad)
    assert lost(audit(pa, GOOD)) == set()


def test_x_robots_tag_header_noindex_is_caught(pa):
    res = audit(pa, GOOD, headers={**GOOD_HEADERS, "x-robots-tag": "noindex, nofollow"})
    assert "no noindex" in lost(res)


def test_non_200_status_and_redirect_chain_cost_points(pa):
    res = audit(pa, GOOD, status=404, chain=[("https://example.test/", 404)])
    assert {"200 status", "at most one redirect"} <= lost(res)  # a page that is not a 200 earns neither
    chain = [("https://example.test/a", 301), ("https://example.test/b", 301), ("https://example.test/", 200)]
    assert "at most one redirect" in lost(audit(pa, GOOD, chain=chain))


def test_slow_and_heavy_pages_lose_the_speed_points(pa):
    assert "fetched in under 2 s" in lost(audit(pa, GOOD, elapsed=3.5))
    assert "HTML under 500 KB" in lost(audit(pa, GOOD + "x" * 600_000))
    assert "HTML under 500 KB" in lost(audit(pa, GOOD, cut=True))


def test_missing_delivery_headers_are_named(pa):
    res = audit(pa, GOOD, headers={})
    assert {"gzip and a cache header", "3+ of 5 security headers"} <= lost(res)


def test_hreflang_is_reported_as_evidence(pa):
    html = GOOD.replace(
        "</head>",
        '<link rel="alternate" hreflang="en-gb" href="/"><link rel="alternate" hreflang="fr" href="/fr/"></head>',
    )
    ev = next(c for c in audit(pa, html)["checks"] if c["id"] == "indexable")["evidence"]
    assert ev["hreflang"] == ["en-gb", "fr"]


def test_nested_organization_without_url_is_not_a_failure(pa):
    html = GOOD.replace(
        '"@graph": [',
        '"@graph": [{"@type": "Article", "headline": "h", "datePublished": "2025-01-01", '
        '"author": {"@type": "Person", "name": "Sam"}, "publisher": {"@type": "Organization", "name": "N"}},',
    )
    assert "common type has required properties" not in lost(audit(pa, html))


def test_product_needs_an_offer_review_or_rating(pa):
    html = GOOD.replace('"@graph": [', '"@graph": [{"@type": "Product", "name": "Bike"},')
    ev = next(c for c in audit(pa, html)["checks"] if c["id"] == "schema")["evidence"]
    assert any("Product lacks" in m for m in ev["missing"])


def test_faq_article_breadcrumb_and_organization_requirements(pa):
    html = GOOD.replace(
        '"@graph": [',
        '"@graph": [{"@type": "FAQPage"}, {"@type": "Article", "headline": "x"}, '
        '{"@type": "BreadcrumbList"}, {"@type": "Organization"}, {"@type": "WebSite", "name": "n"},',
    )
    missing = " ".join(next(c for c in audit(pa, html)["checks"] if c["id"] == "schema")["evidence"]["missing"])
    for needle in (
        "FAQPage lacks mainEntity",
        "Article lacks author",
        "BreadcrumbList lacks itemListElement",
        "Organization lacks name",
        "WebSite lacks url",
    ):
        assert needle in missing


def test_hostile_json_ld_never_crashes(pa):
    deep = "[" * 3000 + "]" * 3000
    html = GOOD.replace(
        "</head>",
        f'<script type="application/ld+json">{deep}</script><script type="application/ld+json">{{"@type": 5}}</script></head>',
    )
    res = audit(pa, html)
    assert res["max"] == 100


def test_broken_html_is_tolerated(pa):
    junk = "<html><body><h1>Title<p>unclosed <a href='/x'>link <div><h2>two<table><td>cell<b>bold</i><<>>&&;<script>alert(1)"
    res = audit(pa, junk)
    assert 0 <= res["score"] <= 100 and res["max"] == 100


def test_empty_and_whitespace_bodies_score_without_crashing(pa):
    assert audit(pa, "")["score"] < 40
    assert audit(pa, "   \n\n")["max"] == 100


def test_script_style_and_noscript_text_is_not_counted_as_content(pa):
    plain = audit(pa, "<html><body><h1>One</h1><p>five words in this paragraph</p></body></html>")
    noisy = audit(
        pa,
        "<html><body><h1>One</h1><p>five words in this paragraph</p><script>var a = 'many many many';</script>"
        "<style>p {color: red}</style><noscript>hidden words here</noscript></body></html>",
    )
    ev = lambda r: next(c for c in r["checks"] if c["id"] == "content")["evidence"]["words"]
    assert ev(plain) == ev(noisy)


def test_search_form_is_not_counted_as_a_long_form(pa):
    html = GOOD.replace("</main>", '<form role="search"><input name="q"></form></main>')
    assert "largest form has 5 fields or fewer (rule of thumb)" not in lost(audit(pa, html))


def test_image_inside_a_link_gives_the_link_a_name(pa):
    html = GOOD.replace("</footer>", '<a href="/home"><img src="/l.png" alt="Home page"></a></footer>')
    assert "no empty or generic anchors" not in lost(audit(pa, html))


# ---- the fetch layer ---------------------------------------------------------------------------------------------


def run(pa, capsys, *argv):
    code = pa.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_user_agent_is_polite_and_fixed(pa, site, capsys):
    site.routes["/"] = {"body": GOOD}
    run(pa, capsys, site.url(), "--allow-private")
    assert site.log[0][1]["user-agent"] == "FinnTech-Growth-Audit/1.0"
    assert pa.UA == "FinnTech-Growth-Audit/1.0"


def test_full_run_over_http_loses_only_the_https_point_and_gzip_is_decoded(pa, site, capsys):
    site.routes["/"] = {
        "body": GOOD,
        "gzip": True,
        "headers": {k: v for k, v in GOOD_HEADERS.items() if k != "content-encoding"},
    }
    code, out, _ = run(pa, capsys, site.url(), "--allow-private", "--json")
    res = json.loads(out)
    assert code == 0 and res["score"] == 98
    assert [p["label"] for c in res["checks"] for p in c["parts"] if not p["earned"]] == ["served over https"]


def test_json_output_has_the_documented_keys(pa, site, capsys):
    site.routes["/"] = {"body": BAD}
    code, out, _ = run(pa, capsys, site.url(), "--allow-private", "--json")
    res = json.loads(out)
    assert code == 1
    for key in ("url", "final_url", "status", "score", "max", "categories", "checks", "priority", "notes", "redirects"):
        assert key in res
    assert set(res["checks"][0]) >= {"id", "category", "max", "earned", "severity", "evidence", "why", "fix", "parts"}


def test_exit_code_is_0_when_nothing_high_is_lost_and_1_otherwise(pa, site, capsys):
    site.routes["/good"] = {"body": GOOD}
    site.routes["/bad"] = {"body": BAD}
    assert run(pa, capsys, site.url("/good"), "--allow-private")[0] == 0
    assert run(pa, capsys, site.url("/bad"), "--allow-private")[0] == 1


def test_404_is_audited_and_flagged_critical(pa, site, capsys):
    site.routes["/gone"] = {"status": 404, "body": "<html><title>gone</title></html>"}
    code, out, _ = run(pa, capsys, site.url("/gone"), "--allow-private")
    assert code == 1 and "[CRITICAL] basics" in out


def test_redirect_is_followed_and_counted(pa, site, capsys):
    site.routes["/old"] = {"status": 301, "headers": {"Location": "/new"}}
    site.routes["/new"] = {"body": GOOD}
    _, out, _ = run(pa, capsys, site.url("/old"), "--allow-private", "--json")
    res = json.loads(out)
    assert res["final_url"].endswith("/new") and len(res["redirects"]) == 2
    assert next(c for c in res["checks"] if c["id"] == "basics")["evidence"]["redirects"] == 1


def test_two_redirects_lose_the_redirect_point(pa, site, capsys):
    site.routes["/a"] = {"status": 302, "headers": {"Location": "/b"}}
    site.routes["/b"] = {"status": 302, "headers": {"Location": "/c"}}
    site.routes["/c"] = {"body": GOOD}
    _, out, _ = run(pa, capsys, site.url("/a"), "--allow-private", "--json")
    assert "at most one redirect" in lost(json.loads(out))


def test_redirect_loop_stops_at_the_limit_with_exit_1(pa, site, capsys):
    site.routes["/a"] = {"status": 302, "headers": {"Location": "/b"}}
    site.routes["/b"] = {"status": 302, "headers": {"Location": "/a"}}
    code, _, err = run(pa, capsys, site.url("/a"), "--allow-private")
    assert code == 1 and "more than 5 redirects" in err
    assert len([1 for p, _ in site.log]) == 6


def test_redirect_to_a_non_http_scheme_is_refused(pa, site, capsys):
    site.routes["/a"] = {"status": 302, "headers": {"Location": "file:///etc/passwd"}}
    code, _, err = run(pa, capsys, site.url("/a"), "--allow-private")
    assert code == 1 and "only plain http(s)" in err


def test_loopback_and_private_addresses_are_blocked_by_default(pa, site, capsys):
    for url in (
        site.url(),
        site.url(host="localhost"),
        "http://169.254.169.254/latest/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://[::1]/",
        "http://0.0.0.0/",
        "http://2130706433/",
    ):
        code, out, err = run(pa, capsys, url)
        if url == "http://2130706433/" and sys.platform == "win32":
            assert code in (1, 2) and out == ""  # Windows does not resolve a bare decimal address at all: still no request
            continue
        assert code == 2 and "private or reserved" in err, url
        assert out == ""
    assert site.log == []  # nothing ever reached the local server


def test_a_redirect_into_a_private_address_is_refused_mid_chain(pa, site, capsys, monkeypatch):
    monkeypatch.setattr(pa, "public", lambda ip: ip == "127.0.0.1")  # pretend 127.0.0.1 is the one public address
    site.routes["/a"] = {"status": 302, "headers": {"Location": f"http://127.0.0.2:{site.port}/inside"}}
    site.routes["/inside"] = {"body": GOOD}
    code, _, err = run(pa, capsys, site.url("/a"))
    assert code == 1 and "private or reserved" in err
    assert [p for p, _ in site.log] == ["/a"]


def test_dns_rebinding_is_caught_after_connecting(pa, site, capsys, monkeypatch):
    real = socket.getaddrinfo
    calls = {"n": 0}

    def flip(host, port, *a, **kw):
        if host != "rebind.example":
            return real(host, port, *a, **kw)
        calls["n"] += 1
        ip = "93.184.216.34" if calls["n"] == 1 else "127.0.0.1"  # public when checked, loopback when connecting
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]

    monkeypatch.setattr(socket, "getaddrinfo", flip)
    code, _, err = run(pa, capsys, f"http://rebind.example:{site.port}/")
    assert code == 2 and "private or reserved" in err
    assert site.log == []  # the connection was made, but no request was ever sent


def test_allow_private_flag_permits_loopback(pa, site, capsys):
    site.routes["/"] = {"body": GOOD}
    assert run(pa, capsys, site.url(), "--allow-private")[0] == 0


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/",
        "file:///etc/passwd",
        "gopher://x/",
        "http://user:pw@example.com/",
        "https://example.com:notaport/",
        "http:///nohost",
    ],
)
def test_bad_urls_exit_2_without_a_traceback(pa, capsys, url):
    code, out, err = run(pa, capsys, url, "--allow-private")
    assert code == 2 and err.startswith("error:") and "Traceback" not in err and out == ""


def test_unresolvable_host_is_a_fetch_failure_not_bad_input(pa, capsys):
    code, _, err = run(pa, capsys, "http://does-not-exist.invalid/")
    assert code == 1 and "cannot resolve" in err


def test_connection_refused_is_exit_1(pa, capsys):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    code, _, err = run(pa, capsys, f"http://127.0.0.1:{port}/", "--allow-private")
    assert code == 1 and "cannot fetch" in err


def test_a_server_that_never_answers_times_out(pa, site):
    site.routes["/slow"] = {"body": GOOD, "delay": 3}
    with pytest.raises(pa.FetchError, match="cannot fetch"):
        pa.get(site.url("/slow"), True, timeout=0.4)


def test_a_server_that_dribbles_its_body_hits_the_total_deadline(pa, site):
    site.routes["/drip"] = {"body": "x" * 4000, "dribble": 0.2}
    with pytest.raises(pa.FetchError, match=r"took longer|cannot read"):
        pa.get(site.url("/drip"), True, timeout=0.5)


def test_oversized_body_is_cut_at_the_cap_and_noted(pa, site):
    site.routes["/big"] = {"body": "<html><title>t</title>" + "a" * 50_000}
    r = pa.get(site.url("/big"), True, max_bytes=2048)
    assert r.cut and len(r.body) == 2048
    res = pa.analyze(r)
    assert any("cut at 2,048 bytes" in n for n in res["notes"])
    assert "HTML under 500 KB" in lost(res)


def test_gzip_bomb_is_capped(pa, site):
    site.routes["/bomb"] = lambda h: (
        h.send_response(200),
        h.send_header("Content-Type", "text/html"),
        h.send_header("Content-Encoding", "gzip"),
        h.send_header("Content-Length", str(len(gz := gzip.compress(b"a" * 5_000_000)))),
        h.end_headers(),
        h.wfile.write(gz),
    )
    r = pa.get(site.url("/bomb"), True, max_bytes=100_000)
    assert r.cut and len(r.body) == 100_000


def test_corrupt_gzip_is_a_clean_error(pa, site):
    site.routes["/bad"] = {"body": b"not gzip at all", "headers": {"Content-Encoding": "gzip"}}
    with pytest.raises(pa.FetchError, match="does not decompress"):
        pa.get(site.url("/bad"), True)


def test_non_html_content_type_exits_1(pa, site, capsys):
    site.routes["/api"] = {"body": '{"a": 1}', "headers": {"Content-Type": "application/json"}}
    code, out, err = run(pa, capsys, site.url("/api"), "--allow-private")
    assert code == 1 and "not an HTML page" in err and out == ""


def test_charset_from_the_header_is_honoured(pa, site):
    site.routes["/"] = {
        "body": "<title>Caf\xe9 \xa3 bikes</title>".encode("latin-1"),
        "headers": {"Content-Type": "text/html; charset=iso-8859-1"},
    }
    res = pa.analyze(pa.get(site.url(), True))
    assert next(c for c in res["checks"] if c["id"] == "snippet")["evidence"]["title"] == "Café £ bikes"


def test_unknown_charset_falls_back_to_utf8(pa, site):
    site.routes["/"] = {"body": "<title>ok</title>", "headers": {"Content-Type": "text/html; charset=nonsense-9"}}
    assert pa.decode(pa.get(site.url(), True)) == "<title>ok</title>"


def test_url_without_a_scheme_defaults_to_https(pa, capsys):
    code, _, err = run(pa, capsys, "localhost:9/x")
    assert code == 2 and "private or reserved" in err


def test_public_address_classifier(pa):
    for ip in ("8.8.8.8", "93.184.216.34", "2606:4700:4700::1111"):
        assert pa.public(ip), ip
    for ip in (
        "127.0.0.1",
        "10.1.2.3",
        "172.16.0.1",
        "192.168.0.1",
        "169.254.1.1",
        "100.64.0.1",
        "0.0.0.0",
        "::1",
        "fe80::1%eth0",
        "::ffff:127.0.0.1",
        "fc00::1",
        "224.0.0.1",
    ):
        assert not pa.public(ip), ip


def test_headers_with_the_same_name_do_not_crash_and_multi_value_is_kept(pa, site):
    site.routes["/"] = lambda h: (
        h.send_response(200),
        h.send_header("Content-Type", "text/html"),
        h.send_header("X-A", "1"),
        h.send_header("X-A", "2"),
        h.send_header("Content-Length", "0"),
        h.end_headers(),
    )
    assert pa.get(site.url(), True).headers["x-a"] in {"1", "2", "1, 2"}


def test_timeout_flag_less_main_uses_the_module_default(pa):
    assert pa.TIMEOUT == 10.0 and pa.MAX_BYTES == 2_000_000


def test_main_with_partial_timeout_patch(pa, site, capsys, monkeypatch):
    monkeypatch.setattr(pa, "get", functools.partial(pa.get, timeout=0.3))
    site.routes["/"] = {"body": GOOD, "delay": 2}
    code, _, err = run(pa, capsys, site.url(), "--allow-private")
    assert code == 1 and "cannot fetch" in err


# ---- found by hostile review -------------------------------------------------------------------------------------


def test_inline_style_and_script_before_json_ld_do_not_stop_the_parser(pa):
    html = (
        "<html lang=en><head><title>t</title><style>body{}</style></head><body><h1>Hi</h1>"
        "<script>var a=1</script><h2>Two?</h2></body></html>"
    )
    res = audit(pa, html)
    assert res["notes"] == []
    content = next(c for c in res["checks"] if c["id"] == "content")["evidence"]
    assert content["h1"] == ["Hi"] and content["h2"] == 1


def test_minified_html_does_not_glue_words_together(pa):
    res = audit(pa, "<html><body><h1>Hi</h1><p>one two</p><p>three<br>four</p></body></html>")
    assert next(c for c in res["checks"] if c["id"] == "content")["evidence"]["words"] == 5


def test_a_long_digit_run_does_not_hang_the_proof_check(pa):
    import time

    start = time.monotonic()
    audit(pa, "<html><body><p>" + "1" * 40_000 + "</p></body></html>")
    assert time.monotonic() - start < 5


def test_a_non_ascii_path_is_fetched_not_a_traceback(pa, site):
    site.routes["/caf%C3%A9"] = {"body": GOOD}
    res = pa.get(site.url("/café?q=é"), True)
    assert res.status == 200 and site.log[-1][0] == "/caf%C3%A9?q=%C3%A9"


def test_a_console_that_cannot_show_the_page_text_does_not_crash(site):
    """Windows consoles often use cp1252. A star or a CJK character in a title must not end the run with a traceback."""
    import os
    import subprocess
    import sys


    site.routes["/"] = {"body": "<!doctype html><html lang=en><title>Bob’s bikes ★ 日本</title><h1>Bob ★</h1>"}
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    r = subprocess.run(
        [sys.executable, str(SCRIPTS["page_audit"]), site.url(), "--allow-private"],
        capture_output=True, env=env, timeout=60,
    )
    assert r.returncode in (0, 1), r.stderr.decode(errors="replace")
    assert b"Traceback" not in r.stderr
    assert b"GROWTH SCORE" in r.stdout
