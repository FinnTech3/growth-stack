#!/usr/bin/env python3
"""page_audit.py URL [--json] [--allow-private]: audit one page; print a Growth Score out of 100, every point named.

Exit 0: no high finding. 1: a high or critical finding, or the fetch failed. 2: bad input. Standard library only.
"""
import argparse
import http.client
import ipaddress
import json
import re
import socket
import sys
import time
import zlib
from html.parser import HTMLParser
from types import SimpleNamespace
from urllib.parse import quote, urljoin, urlsplit

UA, TIMEOUT, MAX_BYTES = "FinnTech-Growth-Audit/1.0", 10.0, 2_000_000


class FetchError(Exception):
  def __init__(self, msg, usage=False):
    super().__init__(msg)
    self.usage = usage


def public(ip):
  a = ipaddress.ip_address(ip.split("%")[0])
  a = getattr(a, "ipv4_mapped", None) or a
  return a.is_global and not a.is_multicast


def get(url, allow_private=False, timeout=TIMEOUT, max_bytes=MAX_BYTES):
  """GET, following up to 5 redirects. Every hop is checked before and after connecting."""
  t0, chain = time.monotonic(), []
  for hop in range(6):
    u, first = urlsplit(url), hop == 0
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
      raise FetchError(f"only plain http(s) URLs without credentials are supported: {url!r}", first)
    try:
      port = u.port or (443 if u.scheme == "https" else 80)
      ips = {i[4][0] for i in socket.getaddrinfo(u.hostname, port, type=socket.SOCK_STREAM)}
    except ValueError as e:
      raise FetchError(f"bad URL {url!r}: {e}", first) from e
    except (OSError, UnicodeError) as e:
      raise FetchError(f"cannot resolve {u.hostname}: {e}") from e
    blocked = FetchError(f"{u.hostname} is a private or reserved address (use --allow-private)", first)
    if not allow_private and not all(map(public, ips)):
      raise blocked
    conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(u.hostname, port, timeout=timeout)
    try:
      conn.connect()
      if not allow_private and not public(conn.sock.getpeername()[0]):
        raise blocked
      target = quote((u.path or "/") + (f"?{u.query}" if u.query else ""), safe="/%:@!$&'()*+,;=~-._?")
      conn.request("GET", target, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
      resp = conn.getresponse()
    except (OSError, http.client.HTTPException, FetchError) as e:
      conn.close()
      raise e if isinstance(e, FetchError) else FetchError(f"cannot fetch {url}: {e}") from e
    chain.append((url, resp.status))
    if resp.status in (301, 302, 303, 307, 308) and resp.getheader("Location"):
      conn.close()
      url = urljoin(url, resp.getheader("Location"))
      continue
    headers, body = {k.lower(): v for k, v in resp.getheaders()}, bytearray()
    try:
      while len(body) <= max_bytes:
        chunk = resp.read1(min(65536, max_bytes + 1 - len(body)))
        if not chunk:
          break
        body += chunk
        if time.monotonic() - t0 > timeout * 3:
          raise FetchError(f"{url} took longer than {timeout * 3:g}s to send its body")
    except (OSError, http.client.HTTPException) as e:
      raise FetchError(f"cannot read {url}: {e}") from e
    finally:
      conn.close()
    cut, data = len(body) > max_bytes, bytes(body[:max_bytes])
    if headers.get("content-encoding", "").lower() in ("gzip", "x-gzip"):
      try:
        data = zlib.decompressobj(47).decompress(data, max_bytes + 1)
      except zlib.error as e:
        raise FetchError(f"{url} sent a body that does not decompress") from e
      cut, data = cut or len(data) > max_bytes, data[:max_bytes]
    return SimpleNamespace(url=url, status=resp.status, headers=headers, body=data, chain=chain, cut=cut, elapsed=time.monotonic() - t0)
  raise FetchError(f"more than 5 redirects, ending at {url}")


def decode(r):
  m = re.search(r"charset=([\w-]+)", r.headers.get("content-type", ""), re.I)
  try:
    return r.body.decode(m.group(1) if m else "utf-8", "replace")
  except LookupError:
    return r.body.decode("utf-8", "replace")


SKIP, HEAD = {"script", "style", "template", "svg", "noscript"}, {f"h{i}" for i in range(1, 7)}
INLINE = {"a", "b", "i", "u", "s", "em", "strong", "span", "small", "sup", "sub", "code", "mark", "abbr", "cite", "q", "time"}


class P(HTMLParser):
  """One pass over the page. A new heading or link closes the open one, so broken HTML is tolerated."""

  def __init__(s):
    super().__init__(convert_charrefs=True)
    s.title, s.lang, s.meta, s.canon, s.alts, s.heads, s.imgs, s.anchors = None, "", [], [], [], [], [], []
    s.ld, s.forms, s.ctas, s.text, s.pbuf, s.skip, s.times = [], [], [], [], [], 0, 0
    s.in_title = s.in_ld = s.in_p = 0
    s.h = s.ans = s.a = None

  def end_a(s):
    if s.a is not None:
      s.anchors += [s.a] * (s.a["tag"] == "a")
      s.ctas += [" ".join(s.a["text"].split())] * s.a["cta"]
      s.a = None

  def handle_starttag(s, tag, attrs):
    a = {k: (v or "") for k, v in attrs}
    s.handle_data(" " * (tag not in INLINE))
    if tag in SKIP:
      s.skip += 1
      s.in_ld = tag == "script" and a.get("type", "").lower() == "application/ld+json"
      s.ld += [""] * s.in_ld
    elif s.skip:
      return
    elif tag in HEAD:
      s.h, s.ans = len(s.heads), None
      s.heads.append([int(tag[1]), "", None])
    elif tag == "html":
      s.lang = a.get("lang", "").strip()
    elif tag == "title":
      s.in_title, s.title = 1, s.title or ""
    elif tag == "meta":
      s.meta.append(a)
    elif tag == "link":
      rel = a.get("rel", "").lower().split()
      s.canon += [a.get("href", "")] * ("canonical" in rel)
      s.alts += [a.get("hreflang", "")] * ("alternate" in rel and bool(a.get("hreflang")))
    elif tag == "p":
      s.in_p, s.pbuf = 1, []
    elif tag == "time":
      s.times += 1
    elif tag == "img":
      s.imgs.append(a)
      if s.a is not None:
        s.a["text"] += " " + a.get("alt", "")
    elif tag in ("a", "button"):
      s.end_a()
      cta = (tag == "button" and a.get("type", "submit") != "reset") or bool(
        re.search(r"btn|button|cta", a.get("class", "") + a.get("role", ""), re.I))
      s.a = {"tag": tag, "href": a.get("href", "").strip(), "rel": a.get("rel", "").lower(), "text": a.get("aria-label", ""),
             "cta": cta}
    elif tag == "form":
      s.forms.append([0, a.get("role") == "search"])
    elif tag in ("input", "textarea", "select"):
      kind = a.get("type", "text").lower() if tag == "input" else tag
      s.ctas += [a.get("value", "").strip()] * (kind in ("submit", "button") and bool(a.get("value")))
      if s.forms and kind not in ("hidden", "submit", "button", "image", "reset"):
        s.forms[-1][0] += 1

  def handle_endtag(s, tag):
    s.handle_data(" " * (tag not in INLINE))
    if tag in SKIP:
      s.skip, s.in_ld = max(0, s.skip - 1), 0
    elif s.skip:
      return
    elif tag in HEAD:
      s.h, s.ans = None, (s.ans if s.h is None else s.h)
    elif tag == "title":
      s.in_title = 0
    elif tag in ("a", "button"):
      s.end_a()
    elif tag == "p" and s.in_p:
      s.in_p = 0
      if s.ans is not None and s.heads[s.ans][2] is None:
        s.heads[s.ans][2] = len("".join(s.pbuf).split())

  def handle_data(s, d):
    if s.skip:
      if s.in_ld:
        s.ld[-1] += d
    elif s.in_title:
      s.title += d
    else:
      if s.a is not None:
        s.a["text"] += d
      if s.h is not None:
        s.heads[s.h][1] += d
      if s.in_p:
        s.pbuf.append(d)
      s.text.append(d)


def walk(x, depth=0):
  """Yield every JSON-LD object."""
  for n in x if isinstance(x, list) else [x]:
    if isinstance(n, dict) and depth < 25:
      yield n
      for v in n.values():
        yield from walk(v, depth + 1) if isinstance(v, (dict, list)) else ()


# Rubric lines: id|category|why|fix|label:points:severity-if-lost;... The points sum to 100.
RUBRIC = {r[0]: [r[1], r[2], r[3], [p.rsplit(":", 2) for p in r[4].split(";")]] for r in (ln.split("|") for ln in """
basics|T|A clean, mobile-ready 200 page is the base|Serve 200 over https; add viewport meta, html lang|200 status:3:c;at most one redirect:2:l;served over https:2:m;viewport meta:2:h;html lang:1:l
indexable|T|noindex removes the page from search|Remove noindex; add one rel=canonical|no noindex:5:c;one canonical link:3:m
delivery|T|Slow, bare pages lose trust|Enable gzip, caching, security headers|gzip and a cache header:2:l;3+ of 5 security headers:2:l;HTML under 500 KB:2:m;fetched in under 2 s:1:m
snippet|P|Title, description, tags are your listing|Rewrite title and description; add og and twitter tags|has a title:3:c;title 30-60 characters:2:m;has a meta description:3:h;description 70-160 characters:2:l;og:title, description, image and twitter:card:4:l
content|P|Topic, outline and substance|One H1, 2+ H2s in order, full answer|exactly one H1:4:h;two or more H2s:1:l;no skipped heading level:2:l;300+ words (rule of thumb):2:m
links-images|P|Anchors and alt text say what things are|Link related pages; describe anchors and images|3+ internal links:2:m;no empty or generic anchors:2:l;images have alt:3:m
schema|S|Machines can check structured facts|Add valid JSON-LD with its required properties|has JSON-LD:4:m;all blocks parse:3:h;common type has required properties:3:m
answers|A|Answer engines quote short answers|Phrase H2s as questions; answer in 8-60 words|2+ question headings:4:m;short direct answers (heuristic):4:m
authority|A|Named, dated, sourced pages get cited|Add a byline, a time element, source links|author:2:l;date:2:l;2+ outside sources (heuristic):3:l
cta|C|A clear next step is the conversion|One verb-led button ('Get my quote'); short form|verb-led CTA:6:h;specific label:3:l;largest form has 5 fields or fewer (rule of thumb):3:m
trust|C|Visitors look for proof you are real|Show contact, link policies, add real proof|contact details:3:m;policy links:2:l;proof such as reviews (heuristic):3:m
""".strip().splitlines())}
CATS = {"T": "Crawl and index", "P": "On-page SEO", "S": "Structured data", "A": "AI-search readiness", "C": "Conversion"}
SEV = ["critical", "high", "medium", "low"]
REQ = {"Organization": "name", "WebSite": "name url", "Article": "headline author datePublished", "FAQPage": "mainEntity",
       "Product": "name offers|review|aggregateRating", "LocalBusiness": "name address telephone", "BreadcrumbList": "itemListElement"}
ALIAS = {"BlogPosting": "Article", "NewsArticle": "Article",
         **dict.fromkeys(["Restaurant", "Dentist", "Store", "AutoRepair", "BikeStore"], "LocalBusiness")}
CTA = re.compile(r"\b(start|get|buy|book|try|sign ?up|join|contact|request|download|subscribe|add to (cart|basket)|schedule|demo|"
                 r"quote|order|call|register|apply)\b", re.I)
GEN = {"click here", "here", "read more", "learn more", "more", "click", "details", "continue", "submit", "go", "send", "ok", ""}
QUESTION = re.compile(r"^(who|what|why|how|when|where|which|can|do|does|is|are|should)\b|\?\s*$", re.I)
PHONE = re.compile(r"\+\d[\d ()-]{8,}\d|\b0\d{2,4}[ -]?\d{3,4}[ -]?\d{3,4}\b|\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b")
ADDR = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b|\b\d{1,5}\s+[A-Z]\w+(\s+\w+)?\s+(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Way)\b")
PROOF = re.compile(r"testimonial|trusted by|(?<![\d,])\d[\d,]*\+? (customers|clients|reviews)|rated \d|★|5[ -]star", re.I)
SOCIAL = ("facebook.com", "twitter.com", "x.com", "linkedin.com", "instagram.com", "youtube.com")
SECURITY = ("strict-transport-security", "x-content-type-options", "x-frame-options", "content-security-policy", "referrer-policy")


def host_of(u):
  return (urlsplit(u).hostname or "").lower().removeprefix("www.")


def analyze(r):
  """Turn a fetched response into the score and every check. Pure: no network."""
  p, notes, C, h = P(), [], [], r.headers
  try:
    p.feed(decode(r))
    p.close()
  except Exception:
    notes.append("The HTML parser stopped early; results cover what it read.")
  p.end_a()
  meta = {}
  for m in p.meta:
    meta.setdefault((m.get("name") or m.get("property") or m.get("http-equiv") or "").lower(), m.get("content", ""))
  rob = ",".join([meta.get("robots", ""), h.get("x-robots-tag", "")]).lower()
  tok = set(re.split(r"[,\s]+", rob))
  text = " ".join("".join(p.text).split())
  title, desc = " ".join((p.title or "").split()), " ".join(meta.get("description", "").split())
  h1s = [" ".join(x[1].split()) for x in p.heads if x[0] == 1]
  bad_ld, types, lacks, nodes = 0, set(), [], []
  for raw in p.ld:
    try:
      found = list(walk(json.loads(raw)))
    except (ValueError, RecursionError):
      bad_ld += 1
      continue
    nodes += found
    for n in found:
      tt = n.get("@type")
      for t in [x for x in (tt if isinstance(tt, list) else [tt]) if isinstance(x, str)]:
        t = ALIAS.get(t, t)
        types.add(t)
        lacks += [f"{t} lacks {g}" for g in REQ.get(t, "").split()
                  if not any(n.get(k) not in (None, "", [], {}) for k in g.split("|"))]
  web = [(a, urljoin(r.url, a["href"])) for a in p.anchors if a["href"] and not a["href"].startswith(("#", "javascript:"))]
  me, labels = host_of(r.url), [" ".join(a["text"].split()) for a in p.anchors]
  internal = sum(host_of(u) == me for _, u in web if u.startswith("http"))
  cites = {host_of(u) for _, u in web if u.startswith("http") and host_of(u) != me and not host_of(u).endswith(SOCIAL)}
  empty, generic = labels.count(""), sum(x.lower() in GEN for x in labels)
  skipped = [f"h{b[0]} after h{a[0]}" for a, b in zip(p.heads, p.heads[1:]) if b[0] > a[0] + 1]
  h2, words, hops = sum(x[0] == 2 for x in p.heads), len(text.split()), len(r.chain) - 1
  qs = [x for x in p.heads if QUESTION.search(" ".join(x[1].split()))]
  good = [x for x in qs if x[2] and 8 <= x[2] <= 60]
  act, gen = [lab for lab in p.ctas if CTA.search(lab)], [lab for lab in p.ctas if lab.lower() in GEN]
  largest = max([f[0] for f in p.forms if not (f[1] and f[0] <= 1)] or [0])
  sec, caching = [k for k in SECURITY if k in h], [k for k in ("cache-control", "etag", "last-modified") if k in h]
  ce, vp = h.get("content-encoding", "").lower(), meta.get("viewport", "").replace(" ", "")
  contact = any(a["href"].startswith(("tel:", "mailto:")) for a in p.anchors) or PHONE.search(text) or ADDR.search(text)
  by = meta.get("author") or any("author" in a["rel"] for a in p.anchors) or any("author" in n for n in nodes) or re.search(
    r"\bBy [A-Z][a-z]+ [A-Z][a-z]+", text)
  dated = p.times or meta.get("article:published_time") or any(
    "datePublished" in n or "dateModified" in n for n in nodes)
  pol = sum(bool(re.search(r"privacy|terms|refund|returns|cookie|policy", a["href"] + a["text"], re.I)) for a in p.anchors)
  proof = PROOF.search(text) or {"Review", "AggregateRating"} & types or any(
    "aggregateRating" in n or "review" in n for n in nodes)
  alt = sum("alt" in i for i in p.imgs)
  og = [k for k in ("og:title", "og:description", "og:image", "twitter:card") if meta.get(k)]

  def chk(cid, *oks, **ev):
    cat, why, fix, spec = RUBRIC[cid]
    parts = [{"label": lb, "points": int(w), "earned": int(w) * bool(ok), "severity": SEV["chml".index(s)]} for (lb, w, s), ok in zip(spec, oks)]
    lost = [x["severity"] for x in parts if not x["earned"]]
    C.append({"id": cid, "category": cat, "max": sum(x["points"] for x in parts), "earned": sum(x["earned"] for x in parts),
              "severity": min(lost, key=SEV.index, default=None), "evidence": ev, "why": why, "fix": fix, "parts": parts})

  chk("basics", r.status == 200, r.status == 200 and hops <= 1, r.url.startswith("https://"), "width=device-width" in vp,
      bool(p.lang), http=r.status, redirects=hops, viewport=vp or "missing", lang=p.lang or "missing")
  chk("indexable", not {"noindex", "none"} & tok, len(p.canon) == 1, robots=rob.strip(", ") or "none",
      canonical=p.canon[:2] or "none", hreflang=p.alts or "none")
  chk("delivery", "gzip" in ce and bool(caching), len(sec) >= 3, len(r.body) <= 500_000 and not r.cut,
      r.elapsed <= 2.0, encoding=ce or "none", cache=caching, security=len(sec), bytes=len(r.body), ms=round(r.elapsed * 1000))
  chk("snippet", bool(title), 30 <= len(title) <= 60, bool(desc), 70 <= len(desc) <= 160, len(og) == 4, title=title[:70],
      title_chars=len(title), description_chars=len(desc), tags=len(og))
  chk("content", len(h1s) == 1 and bool(h1s[0]), h2 >= 2, not skipped, words >= 300, h1=h1s[:3], h2=h2,
      skipped=skipped or "none", words=words)
  chk("links-images", internal >= 3, not empty and generic <= 0.1 * max(1, len(labels)), alt >= 0.9 * len(p.imgs),
      internal=internal, empty=empty, generic=generic, alt=f"{alt}/{len(p.imgs)}")
  chk("schema", bool(p.ld), bool(p.ld) and not bad_ld, bool(types & set(REQ)) and not lacks, blocks=len(p.ld), bad=bad_ld,
      types=sorted(types) or "none", missing=lacks or "none")
  chk("answers", len(qs) >= 2, bool(qs) and len(good) * 2 >= len(qs), questions=len(qs), answered=len(good))
  chk("authority", bool(by), bool(dated), len(cites) >= 2, sources=len(cites))
  chk("cta", bool(act), bool(act) and not gen and len(act[0].split()) <= 6, largest <= 5, cta=act[:1] or "none",
      generic=gen or "none", form_fields=largest)
  chk("trust", bool(contact), pol > 0, bool(proof), policy_links=pol)
  if r.cut:
    notes.append(f"HTML was cut at {len(r.body):,} bytes; later content is not scored.")
  cats = {n: {f: sum(c[f] for c in C if c["category"] == k) for f in ("earned", "max")} for k, n in CATS.items()}
  prio = [c["id"] for c in sorted((c for c in C if c["severity"]), key=lambda c: (SEV.index(c["severity"]), c["earned"] - c["max"]))]
  return {"url": r.chain[0][0], "final_url": r.url, "status": r.status, "html_bytes": len(r.body), "fetch_ms": round(r.elapsed * 1000), "redirects": r.chain, "score": sum(c["earned"] for c in C),
          "max": sum(c["max"] for c in C), "categories": cats, "checks": C, "priority": prio, "notes": notes}


def render(res):
  ev = lambda c: ", ".join(f"{k}={v}" for k, v in c["evidence"].items())
  lost = lambda c: "; ".join(f"{x['label']} (-{x['points']})" for x in c["parts"] if not x["earned"])
  out = [f"Growth Audit: {res['final_url']}", f"Fetched: HTTP {res['status']}, {res['html_bytes']:,} bytes of HTML, {res['fetch_ms']} ms, "
         f"{len(res['redirects']) - 1} redirect(s)", "",
         f"GROWTH SCORE: {res['score']}/{res['max']}"]
  out += [f"  {k:<22}{v['earned']:>3}/{v['max']}" for k, v in res["categories"].items()]
  by = {c["id"]: c for c in res["checks"]}
  out += ["", "FIX FIRST (severity of the worst lost point, then points lost)"]
  for i, cid in enumerate(res["priority"], 1):
    c = by[cid]
    out += [f"{i:>2}. [{c['severity'].upper()}] {cid} {c['earned'] - c['max']}: {lost(c)}", f"      Evidence: {ev(c)}",
            f"      Why: {c['why']}", f"      Fix: {c['fix']}"]
  out += ["  Nothing to fix: every point earned."] * (not res["priority"]) + ["", "EVERY POINT"]
  for k, name in CATS.items():
    out.append(f"  {name} {res['categories'][name]['earned']}/{res['categories'][name]['max']}")
    out += [f"    {c['id']} {c['earned']}/{c['max']}: " + "; ".join(f"{'+' if x['earned'] else '-'}{x['points']} {x['label']}"
            for x in c["parts"]) for c in res["checks"] if c["category"] == k]
  out += (["", "NOTES"] + [f"  {n}" for n in res["notes"]]) * bool(res["notes"])
  return "\n".join(out + ["", "Heuristic and rule-of-thumb items are guides, not verdicts."])


def main(argv=None):
  ap = argparse.ArgumentParser(prog="page_audit.py", description="Audit one page and print a Growth Score out of 100.")
  ap.add_argument("url")
  ap.add_argument("--json", action="store_true", help="print the full result as JSON")
  ap.add_argument("--allow-private", action="store_true", help="allow private, loopback and link-local addresses")
  a = ap.parse_args(argv)
  url = a.url if "://" in a.url else "https://" + a.url
  try:
    r = get(url, a.allow_private)
    if "html" not in r.headers.get("content-type", "").lower():
      raise FetchError(f"not an HTML page (content-type: {r.headers.get('content-type', 'missing')})")
  except FetchError as e:
    print(f"error: {e}", file=sys.stderr)
    return 2 if e.usage else 1
  res = analyze(r)
  print(json.dumps(res, indent=1) if a.json else render(res))
  return 1 if any(c["severity"] in ("critical", "high") for c in res["checks"]) else 0


if __name__ == "__main__":
  sys.stdout.reconfigure(errors="replace")
  sys.exit(main())
