"""site_probe.py: robots.txt parsing and matching, sitemaps, sampling and the safety rules."""

from __future__ import annotations

import gzip
import json
from types import SimpleNamespace

import pytest
from conftest import SCRIPTS
from pages import GOOD

OK_PAGE = "<html><head><title>t</title></head><body><h1>x</h1></body></html>"


def run(sp, capsys, *argv):
    code = sp.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def probe_json(sp, capsys, site, *extra):
    code, out, err = run(sp, capsys, site.url(), "--allow-private", "--delay", "0", "--json", *extra)
    return code, json.loads(out), err


def urlset(*urls, ns=True):
    inner = "".join(f"<url><loc>{u}</loc><lastmod>2025-01-01</lastmod></url>" for u in urls)
    return f'<?xml version="1.0"?><urlset{" xmlns=" + chr(34) + "http://www.sitemaps.org/schemas/sitemap/0.9" + chr(34) if ns else ""}>{inner}</urlset>'


def finding(res, area, text=""):
    return [f for f in res["findings"] if f["area"] == area and text in f["evidence"]]


# ---- robots parsing and matching (RFC 9309 behaviour) -------------------------------------------------------------


def test_robots_groups_merge_consecutive_user_agents_and_blank_lines_do_not_split(sp):
    groups, sitemaps = sp.parse_robots(
        "User-agent: a\n\nUser-agent: b\nDisallow: /x\n\nUser-agent: *\nAllow: /\nSitemap: https://e.test/s.xml\n"
    )
    assert groups[0][0] == ["a", "b"] and groups[0][1] == [("disallow", "/x")]
    assert sitemaps == ["https://e.test/s.xml"]


def test_robots_comments_case_bom_and_garbage_lines_are_ignored(sp):
    groups, _ = sp.parse_robots(
        "﻿USER-AGENT: Bot # a comment\nDISALLOW: /private # why\nnonsense line\n: \nDisallow /nocolon\n"
    )
    assert groups == [(["bot"], [("disallow", "/private")])]


def test_rules_before_any_user_agent_are_ignored(sp):
    groups, _ = sp.parse_robots("Disallow: /x\nUser-agent: *\nDisallow: /y\n")
    assert groups[0][1] == [("disallow", "/y")]


def test_longest_match_wins_and_allow_beats_disallow_on_a_tie(sp):
    g, _ = sp.parse_robots("User-agent: *\nDisallow: /shop\nAllow: /shop/sale\nDisallow: /a\nAllow: /a\n")
    assert sp.allowed(g, "Anybot", "/shop/x")[0] is False
    assert sp.allowed(g, "Anybot", "/shop/sale/1")[0] is True
    assert sp.allowed(g, "Anybot", "/a")[0] is True


def test_wildcards_and_end_anchor(sp):
    g, _ = sp.parse_robots("User-agent: *\nDisallow: /*.pdf$\nDisallow: /tmp*/\nAllow: /tmp-ok/\n")
    assert not sp.allowed(g, "x", "/files/a.pdf")[0]
    assert sp.allowed(g, "x", "/files/a.pdf?x=1")[0]
    assert not sp.allowed(g, "x", "/tmp1/")[0]
    assert sp.allowed(g, "x", "/tmp-ok/")[0]


def test_empty_disallow_allows_everything_and_no_rules_means_allowed(sp):
    g, _ = sp.parse_robots("User-agent: *\nDisallow:\n")
    assert sp.allowed(g, "x", "/anything")[0]
    assert sp.allowed([], "x", "/anything") == (True, "")


def test_a_specific_group_replaces_the_star_group_for_that_agent(sp):
    g, _ = sp.parse_robots("User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nAllow: /\n")
    assert sp.allowed(g, "Googlebot", "/p")[0] is True
    assert sp.allowed(g, "googlebot", "/p")[0] is True  # tokens are case-insensitive
    assert sp.allowed(g, "Bingbot", "/p")[0] is False


def test_norm_ignores_trailing_slash_and_fragment_but_not_scheme(sp):
    assert sp.norm("https://A.test/x/") == sp.norm("https://a.test/x#frag")
    assert sp.norm("http://a.test/x") != sp.norm("https://a.test/x")


# ---- the page scanner --------------------------------------------------------------------------------------------


def test_scan_finds_robots_canonical_and_plain_http_resources(sp):
    s = sp.Scan()
    s.feed(
        '<meta name="robots" content="NOINDEX"><link rel="canonical" href="/c"><img src="http://a.test/i.png">'
        '<script src="https://a.test/ok.js"></script><link rel="stylesheet" href="http://a.test/s.css">'
        '<a href="http://a.test/page">a plain link is not mixed content</a><iframe src="http://a.test/f"></iframe>'
    )
    assert "noindex" in s.robots and s.canon == ["/c"]
    assert sorted(s.http) == ["http://a.test/f", "http://a.test/i.png", "http://a.test/s.css"]


def test_mixed_content_only_counts_on_https_pages(sp, monkeypatch):
    html = '<img src="http://a.test/i.png">'
    for url, expected in (("https://e.test/", 1), ("http://e.test/", 0)):
        resp = SimpleNamespace(url=url, status=200, headers={}, body=html.encode(), chain=[(url, 200)])
        monkeypatch.setattr(sp, "get", lambda *a, _r=resp, **k: _r)
        assert sp.sample_url(url, True, 1)["mixed"] == expected


def test_canonical_mismatch_and_noindex_header_are_flagged_on_a_sampled_page(sp, site):
    site.routes["/p"] = {"body": '<link rel="canonical" href="/other">', "headers": {"X-Robots-Tag": "noindex"}}
    row = sp.sample_url(site.url("/p"), True, 2)
    assert row["canonical_mismatch"] and row["noindex"] and row["status"] == 200


# ---- end to end against a local site -----------------------------------------------------------------------------


def test_site_with_no_robots_and_no_sitemap(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    code, res, _ = probe_json(sp, capsys, site)
    assert code == 0 and res["robots_status"] == 404 and not res["robots_present"]
    assert finding(res, "sitemap", "no sitemap found")
    assert all(r["allowed"] for r in res["rules"])


def test_blocked_search_crawler_is_critical_and_exit_1(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {
        "body": "User-agent: Googlebot\nDisallow: /\n",
        "headers": {"Content-Type": "text/plain"},
    }
    code, res, _ = probe_json(sp, capsys, site)
    assert code == 1
    assert finding(res, "robots.txt", "Googlebot is blocked")[0]["severity"] == "critical"
    assert next(r for r in res["rules"] if r["agent"] == "Bingbot")["allowed"]


def test_star_group_blocking_everything_is_critical(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {"body": "User-agent: *\nDisallow: /\n", "headers": {"Content-Type": "text/plain"}}
    _, res, _ = probe_json(sp, capsys, site)
    assert finding(res, "robots.txt", "User-agent: * is blocked")


def test_ai_crawlers_are_reported_but_blocking_one_is_not_a_finding(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {
        "body": "User-agent: CCBot\nDisallow: /\n\nUser-agent: ExampleAIBot\nDisallow: /\n",
        "headers": {"Content-Type": "text/plain"},
    }
    _, res, _ = probe_json(sp, capsys, site, "--agent", "ExampleAIBot", "--agent", "OtherBot")
    by = {r["agent"]: r for r in res["rules"]}
    assert by["CCBot"]["allowed"] is False and by["CCBot"]["kind"] == "ai/data"
    assert by["ExampleAIBot"]["allowed"] is False and by["OtherBot"]["allowed"] is True
    assert by["Googlebot"]["allowed"] is True
    assert not [f for f in res["findings"] if f["severity"] in ("critical", "high")]


def test_any_named_agent_blocked_from_the_whole_site_is_listed(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {
        "body": "User-agent: SomeNewBot\nUser-agent: AnotherBot\nDisallow: /\n\nUser-agent: *\nDisallow: /admin/\n",
        "headers": {"Content-Type": "text/plain"},
    }
    _, res, _ = probe_json(sp, capsys, site)
    assert res["blocked_everywhere"] == ["anotherbot", "somenewbot"]


def test_robots_rules_are_checked_against_the_given_path(sp, site, capsys):
    site.routes["/members/x"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {
        "body": "User-agent: *\nDisallow: /members/\n",
        "headers": {"Content-Type": "text/plain"},
    }
    code = sp.main([site.url("/members/x"), "--allow-private", "--delay", "0", "--json", "--sample", "0"])
    res = json.loads(capsys.readouterr().out)
    assert code == 1 and finding(res, "robots.txt", "Googlebot is blocked from /members/x")


def test_robots_server_error_is_a_high_finding(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {"status": 503, "body": "down"}
    code, res, _ = probe_json(sp, capsys, site)
    assert code == 1 and finding(res, "robots.txt", "HTTP 503")[0]["severity"] == "high"


def test_robots_served_as_html_is_ignored_and_flagged(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {"body": "<html>User-agent: *\nDisallow: /</html>"}
    _, res, _ = probe_json(sp, capsys, site)
    assert finding(res, "robots.txt", "served as HTML") and not res["robots_present"]
    assert all(r["allowed"] for r in res["rules"])


def test_robots_sitemap_line_is_used_and_missing_line_is_noted(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {"body": "User-agent: *\nDisallow: /x/\n", "headers": {"Content-Type": "text/plain"}}
    _, res, _ = probe_json(sp, capsys, site)
    assert finding(res, "robots.txt", "no Sitemap line")


def test_sitemap_is_parsed_sampled_and_every_url_checked(sp, site, capsys):
    pages = [f"/p{i}" for i in range(6)]
    for p in pages:
        site.routes[p] = {"body": OK_PAGE}
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {
        "body": urlset(*[site.url(p) for p in pages]),
        "headers": {"Content-Type": "application/xml"},
    }
    site.routes["/robots.txt"] = {
        "body": f"User-agent: *\nSitemap: {site.url('/sitemap.xml')}\n",
        "headers": {"Content-Type": "text/plain"},
    }
    code, res, _ = probe_json(sp, capsys, site, "--sample", "4")
    assert code == 0 and res["sitemap_urls"] == 6 and res["sample_size"] == 4
    assert res["sample"][0]["url"].endswith("/") and all(r["status"] == 200 for r in res["sample"])
    assert len({r["url"] for r in res["sample"]}) == 4


def test_sitemap_without_a_namespace_still_parses(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/a"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {"body": urlset(site.url("/a"), ns=False)}
    _, res, _ = probe_json(sp, capsys, site)
    assert res["sitemap_urls"] == 1


def test_sitemap_index_children_are_followed(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    for name, urls in (("one", ["/a", "/b"]), ("two", ["/c"])):
        site.routes[f"/{name}.xml"] = {"body": urlset(*[site.url(u) for u in urls])}
    for u in ("/a", "/b", "/c"):
        site.routes[u] = {"body": OK_PAGE}
    index = (
        '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<sitemap><loc>{site.url('/one.xml')}</loc></sitemap><sitemap><loc>{site.url('/two.xml')}</loc></sitemap></sitemapindex>"
    )
    site.routes["/sitemap.xml"] = {"body": index}
    _, res, _ = probe_json(sp, capsys, site, "--sample", "10")
    assert res["sitemap_urls"] == 3 and res["sample_size"] == 4  # three listed pages plus the home page
    assert not finding(res, "sitemap")


def test_a_sitemap_index_does_not_recurse_forever(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {
        "body": f'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>{site.url("/sitemap.xml")}</loc></sitemap></sitemapindex>'
    }
    code, res, _ = probe_json(sp, capsys, site)
    assert code == 0 and res["sitemap_urls"] == 0


def test_gzipped_sitemap_is_read(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/a"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml.gz"] = {
        "body": gzip.compress(urlset(site.url("/a")).encode()),
        "headers": {"Content-Type": "application/gzip"},
    }
    site.routes["/robots.txt"] = {
        "body": f"Sitemap: {site.url('/sitemap.xml.gz')}\n",
        "headers": {"Content-Type": "text/plain"},
    }
    _, res, _ = probe_json(sp, capsys, site)
    assert res["sitemap_urls"] == 1


def test_invalid_xml_sitemap_is_a_high_finding(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {"body": "<urlset><url><loc>x</url>"}
    code, res, _ = probe_json(sp, capsys, site)
    assert code == 1 and finding(res, "sitemap", "invalid XML")


def test_sitemap_with_a_dtd_is_refused_not_expanded(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><urlset><url><loc>&a;</loc></url></urlset>'
    site.routes["/sitemap.xml"] = {"body": bomb}
    _, res, _ = probe_json(sp, capsys, site)
    assert finding(res, "sitemap", "DTD") and res["sitemap_urls"] == 0


def test_sitemap_over_50000_urls_and_empty_sitemap_are_flagged(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {"body": urlset(*[f"https://e.test/{i}" for i in range(50_001)])}
    _, res, _ = probe_json(sp, capsys, site, "--sample", "0")
    assert finding(res, "sitemap", "50,000")
    site.routes["/sitemap.xml"] = {"body": urlset()}
    _, res, _ = probe_json(sp, capsys, site, "--sample", "0")
    assert finding(res, "sitemap", "no URLs listed")


def test_sitemap_urls_on_another_host_are_flagged_and_never_fetched(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {"body": urlset("http://elsewhere.invalid/a", site.url("/").rstrip("/") + "/a")}
    site.routes["/a"] = {"body": OK_PAGE}
    _, res, _ = probe_json(sp, capsys, site, "--sample", "5")
    assert finding(res, "sitemap", "another host")
    assert all("elsewhere" not in r["url"] for r in res["sample"])


def test_sitemap_listing_a_redirect_a_404_a_noindex_and_a_canonical_mismatch(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/redir"] = {"status": 301, "headers": {"Location": "/ok"}}
    site.routes["/ok"] = {"body": OK_PAGE}
    site.routes["/gone"] = {"status": 404, "body": "nope"}
    site.routes["/hidden"] = {"body": '<meta name="robots" content="noindex">'}
    site.routes["/dupe"] = {"body": '<link rel="canonical" href="/ok">'}
    site.routes["/sitemap.xml"] = {"body": urlset(*[site.url(p) for p in ("/redir", "/gone", "/hidden", "/dupe")])}
    code, res, _ = probe_json(sp, capsys, site, "--sample", "10")
    assert code == 1
    assert finding(res, "sitemap", "the sitemap lists a URL that redirects")
    assert finding(res, "page", "HTTP 404")[0]["severity"] == "critical"
    assert finding(res, "page", "noindex")[0]["severity"] == "high"
    assert finding(res, "page", "canonical points to /ok")
    severities = [f["severity"] for f in res["findings"]]
    assert severities == sorted(severities, key=sp.SEV.index)


def test_redirect_chain_of_two_hops_is_reported_with_its_statuses(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/a"] = {"status": 301, "headers": {"Location": "/b"}}
    site.routes["/b"] = {"status": 302, "headers": {"Location": "/c"}}
    site.routes["/c"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {"body": urlset(site.url("/a"))}
    _, res, _ = probe_json(sp, capsys, site)
    assert finding(res, "page", "2 redirects (301 > 302 > 200)")


def test_unreachable_sampled_url_is_reported_not_fatal(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/slow"] = {"body": OK_PAGE, "delay": 3}
    site.routes["/sitemap.xml"] = {"body": urlset(site.url("/slow"))}
    sp_get = sp.get
    sp.get = lambda url, ap, timeout, mb: sp_get(url, ap, 0.3, mb)
    try:
        code, res, _ = probe_json(sp, capsys, site)
    finally:
        sp.get = sp_get
    assert code == 1 and finding(res, "page", "cannot fetch")


def test_sample_zero_fetches_no_pages_and_sample_is_capped(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    _, res, _ = probe_json(sp, capsys, site, "--sample", "0")
    assert res["sample"] == [] and res["sample_size"] == 0
    for bad in (["--sample", "51"], ["--sample", "-1"], ["--delay", "-1"], ["--sample", "x"]):
        with pytest.raises(SystemExit) as exc:
            sp.main([site.url(), "--allow-private", *bad])
        assert exc.value.code == 2


def test_requests_are_polite(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    probe_json(sp, capsys, site, "--sample", "1")
    assert {h["user-agent"] for _, h in site.log} == {"FinnTech-Growth-Audit/1.0"}
    assert site.log[0][0] == "/robots.txt"


def test_private_addresses_are_blocked_before_any_request(sp, site, capsys):
    code, out, err = run(sp, capsys, site.url())
    assert code == 2 and "private or reserved" in err and out == "" and site.log == []
    assert run(sp, capsys, "http://169.254.169.254/")[0] == 2


@pytest.mark.parametrize("url", ["ftp://example.com/", "file:///etc/hosts", "http://u:p@example.com/"])
def test_bad_urls_exit_2(sp, capsys, url):
    code, _, err = run(sp, capsys, url, "--allow-private")
    assert code == 2 and err.startswith("error:") and "Traceback" not in err


def test_unreachable_origin_is_exit_1(sp, capsys):
    code, _, err = run(sp, capsys, "http://does-not-exist.invalid/", "--delay", "0")
    assert code == 1 and "cannot resolve" in err


def test_text_report_has_the_sections_and_the_ai_note(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    code, out, _ = run(sp, capsys, site.url(), "--allow-private", "--delay", "0")
    assert (
        code == 0
        and "CRAWL RULES" in out
        and "FINDINGS (worst first)" in out
        and "Blocking an AI crawler is a choice" in out
    )
    assert "ai/data" in out and "search" in out


def test_the_fetch_layer_is_identical_in_both_network_scripts():
    def layer(path, end):
        text = path.read_text()
        return text[text.index("UA, TIMEOUT") : text.index(end)].strip().strip()

    assert layer(SCRIPTS["page_audit"], "def decode(") == layer(SCRIPTS["site_probe"], "SEARCH = ")


def test_good_page_sampled_through_a_sitemap_has_no_findings(sp, site, capsys):
    site.routes["/"] = {"body": GOOD}
    site.routes["/robots.txt"] = {
        "body": f"User-agent: *\nSitemap: {site.url('/sitemap.xml')}\n",
        "headers": {"Content-Type": "text/plain"},
    }
    site.routes["/sitemap.xml"] = {"body": urlset(site.url("/"))}
    code, res, _ = probe_json(sp, capsys, site)
    # the fixture's canonical points at its https home, so that mismatch is the one finding
    assert code == 0 and [f["evidence"] for f in res["findings"] if "canonical" not in f["evidence"]] == []


# ---- found by hostile review -------------------------------------------------------------------------------------


def test_wildcard_heavy_robots_rule_cannot_hang_the_matcher(sp):
    import time

    groups, _ = sp.parse_robots("User-agent: *\nDisallow: /" + "*a" * 15 + "*b\n")
    start = time.monotonic()
    assert sp.allowed(groups, "Googlebot", "/" + "a" * 500)[0] is True
    assert time.monotonic() - start < 2


@pytest.mark.parametrize(
    ("pat", "path", "want"),
    [
        ("/a*c", "/abc", True), ("/a*c", "/abd", False), ("/a*c$", "/abcx", False), ("/a*c$", "/abcc", True),
        ("/a$", "/a", True), ("/a$", "/ab", False), ("/*.pdf$", "/x/y.pdf", True), ("/*.pdf$", "/x/y.pdf?z", False),
        ("/a*a$", "/a", False), ("/*", "/anything", True), ("*c", "c", True), ("/p", "/p/q", True),
    ],
)
def test_pattern_matcher_cases(sp, pat, path, want):
    assert sp.matches(pat, path) is want


def test_sitemap_with_a_dtd_after_4096_bytes_is_still_refused(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    pad = "<!--" + "x" * 5000 + "-->"
    site.routes["/sitemap.xml"] = {
        "body": f'<?xml version="1.0"?>{pad}<!DOCTYPE x [<!ENTITY a "aaaa">]><urlset><url><loc>&a;</loc></url></urlset>'
    }
    _, res, _ = probe_json(sp, capsys, site)
    assert finding(res, "sitemap", "DTD") and res["sitemap_urls"] == 0


def test_a_sitemap_on_another_host_is_reported_and_never_fetched(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/robots.txt"] = {
        "body": f"User-agent: *\nSitemap: {site.url('/sm.xml', host='localhost')}\n",
        "headers": {"Content-Type": "text/plain"},
    }
    site.routes["/sm.xml"] = {"body": urlset(site.url("/"))}
    _, res, _ = probe_json(sp, capsys, site, "--sample", "0")
    assert finding(res, "sitemap", "another host") and res["sitemap_urls"] == 0
    assert "/sm.xml" not in [p for p, _ in site.log]


@pytest.mark.parametrize("delay", ["nan", "inf", "-1", "11"])
def test_bad_delay_is_a_usage_error_not_a_traceback(sp, delay):
    with pytest.raises(SystemExit) as e:
        sp.main(["http://127.0.0.1/", "--delay", delay])
    assert e.value.code == 2


def test_sitemap_url_with_non_ascii_characters_is_sampled(sp, site, capsys):
    site.routes["/"] = {"body": OK_PAGE}
    site.routes["/caf%C3%A9"] = {"body": OK_PAGE}
    site.routes["/sitemap.xml"] = {"body": urlset(site.url("/café"))}
    _code, res, err = probe_json(sp, capsys, site)
    assert "Traceback" not in err and not [r for r in res["sample"] if "error" in r]
