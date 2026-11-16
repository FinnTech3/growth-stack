#!/usr/bin/env python3
"""site_probe.py URL [--json] [--sample N] [--allow-private]: check how a site presents itself to crawlers.

Reads robots.txt (rules for search and AI crawlers), finds and parses sitemaps, then samples URLs for status codes,
redirect chains, noindex, canonical mismatches and mixed content.
Exit 0: no high finding. 1: a high or critical finding, or the site could not be reached. 2: bad input. Standard library only.
"""
import argparse
import http.client
import ipaddress
import json
import re
import socket
import sys
import time
import xml.etree.ElementTree as ET
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


SEARCH = ("Googlebot", "Bingbot", "DuckDuckBot", "Applebot")
AI_DATA = ()  # no AI crawler names are built in; the owner names them with --agent
SEV = ["critical", "high", "medium", "low"]


def parse_robots(text):
  """Return (groups, sitemaps). A group is ([agent tokens], [(allow|disallow, pattern)])."""
  groups, sitemaps, cur, prev_agent = [], [], None, False
  for line in text.lstrip("\ufeff").splitlines():
    if ":" not in line.split("#", 1)[0]:
      continue
    k, _, v = line.split("#", 1)[0].partition(":")
    k, v = k.strip().lower(), v.strip()
    if k == "user-agent":
      if not prev_agent or cur is None:
        cur = ([], [])
        groups.append(cur)
      cur[0].append(v.lower())
    elif k in ("allow", "disallow") and cur is not None:
      cur[1].append((k, v))
    elif k == "sitemap" and v:
      sitemaps.append(v)
    prev_agent = k == "user-agent"
  return groups, sitemaps


def matches(pat, path):
  """robots.txt pattern: a prefix match where * is any run of characters and a final $ anchors the end. No regex, so no blow-up."""
  end = pat.endswith("$")
  parts = (pat[:-1] if end else pat).split("*")
  if not path.startswith(parts[0]):
    return False
  pos = len(parts[0])
  if len(parts) == 1:
    return not end or path == parts[0]
  for part in parts[1:-1]:
    i = path.find(part, pos)
    if i < 0:
      return False
    pos = i + len(part)
  last = parts[-1]
  return path.endswith(last) and len(path) - len(last) >= pos if end else path.find(last, pos) >= 0


def allowed(groups, token, path):
  """RFC 9309 matching: the group for the exact token (else *), longest matching pattern wins, allow wins a tie."""
  rules = [r for g in groups if token.lower() in g[0] for r in g[1]] or [r for g in groups if "*" in g[0] for r in g[1]]
  best = (-1, True, "")
  for kind, pat in rules:
    if not pat:
      continue
    if matches(pat, path) and (len(pat), kind == "allow") > best[:2]:
      best = (len(pat), kind == "allow", f"{kind}: {pat}")
  return best[1], best[2]


class Scan(HTMLParser):
  """Collects what a sampled page says about itself: robots meta, canonical, plain-http sub-resources."""

  def __init__(s):
    super().__init__()
    s.robots, s.canon, s.http = "", [], []

  def handle_starttag(s, tag, attrs):
    a = {k: v or "" for k, v in attrs}
    if tag == "meta" and a.get("name", "").lower() in ("robots", "googlebot"):
      s.robots += "," + a.get("content", "").lower()
    elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
      s.canon.append(a.get("href", ""))
    for key in ("src", "href") if tag == "link" and "stylesheet" in a.get("rel", "") else ("src",) if tag in ("img", "script", "iframe", "source", "video", "audio") else ():
      if a.get(key, "").lower().startswith("http://"):
        s.http.append(a[key])


def norm(u):
  x = urlsplit(u)
  return f"{x.scheme}://{(x.hostname or '').lower()}{x.path.rstrip('/') or '/'}" + (f"?{x.query}" if x.query else "")


def read_sitemap(url, allow_private, timeout, depth=0, seen=None):
  """Return (urls, problems). Handles sitemap indexes (2 levels, 5 files in all) and .gz files."""
  seen = seen if seen is not None else []
  urls, probs = [], []
  if url in seen or len(seen) >= 5:
    return urls, probs
  if seen and urlsplit(seen[0]).hostname != urlsplit(url).hostname:
    return urls, [("medium", "sitemap", f"{url}: on another host, not fetched")]
  seen.append(url)
  try:
    r = get(url, allow_private, timeout, 10_000_000)
  except FetchError as e:
    return urls, [("high", "sitemap", f"{url}: {e}")]
  body = r.body
  if body[:2] == b"\x1f\x8b":
    try:
      body = zlib.decompressobj(47).decompress(body, 50_000_000)
    except zlib.error:
      return urls, [("high", "sitemap", f"{url}: bad gzip")]
  if r.status != 200:
    return urls, [("high", "sitemap", f"{url}: HTTP {r.status}")]
  if re.search(rb"<!(DOCTYPE|ENTITY)", body, re.I):
    return urls, [("medium", "sitemap", f"{url}: has a DTD, not parsed (unsafe)")]
  try:
    root = ET.fromstring(body)
  except ET.ParseError as e:
    return urls, [("high", "sitemap", f"{url}: invalid XML ({e})")]
  locs = [(e.findtext("{*}loc") or "").strip() for e in root.iter() if e.tag.endswith("}url") or e.tag == "url"]
  if root.tag.endswith("sitemapindex"):
    for e in root.iter():
      if e.tag.endswith("sitemap"):
        loc = (e.findtext("{*}loc") or e.findtext("loc") or "").strip()
        if loc and depth < 1:
          sub, sp = read_sitemap(urljoin(url, loc), allow_private, timeout, depth + 1, seen)
          urls, probs = urls + sub, probs + sp
    return urls, probs
  urls = [u for u in locs if u] or [(e.text or "").strip() for e in root.iter() if e.tag.endswith("loc")]
  if len(urls) > 50_000:
    probs.append(("medium", "sitemap", f"{url}: {len(urls):,} URLs; the limit is 50,000 per file"))
  if not urls:
    probs.append(("medium", "sitemap", f"{url}: no URLs listed"))
  return urls, probs


def sample_url(url, allow_private, timeout):
  row = {"url": url}
  try:
    r = get(url, allow_private, timeout, 300_000)
  except FetchError as e:
    return {**row, "error": str(e)}
  s = Scan()
  try:
    s.feed(r.body.decode("utf-8", "replace"))
  except Exception:
    pass
  rob = s.robots + "," + r.headers.get("x-robots-tag", "").lower()
  row.update(status=r.status, final=r.url, hops=len(r.chain) - 1, chain=[c[1] for c in r.chain],
             noindex="noindex" in re.split(r"[,\s]+", rob), canonical=s.canon[:1],
             canonical_mismatch=bool(s.canon) and norm(urljoin(r.url, s.canon[0])) != norm(r.url),
             mixed=len(s.http) if r.url.startswith("https://") else 0)
  return row


def probe(url, sample, allow_private, timeout, delay, extra):
  u = urlsplit(url)
  origin = f"{u.scheme}://{u.netloc}"
  out, finds = {"origin": origin}, []

  def add(sev, area, msg, fix=""):
    finds.append({"severity": sev, "area": area, "evidence": msg, "fix": fix})

  rtxt = ""
  r = get(origin + "/robots.txt", allow_private, timeout, 500_000)
  out["robots_status"] = r.status
  if r.status == 200 and "html" in r.headers.get("content-type", "").lower():
    add("medium", "robots.txt", "served as HTML, so crawlers will ignore it", "Serve plain text from /robots.txt.")
  elif r.status == 200:
    rtxt = r.body.decode("utf-8", "replace")
  elif r.status >= 500:
    add("high", "robots.txt", f"HTTP {r.status}; crawlers may treat the whole site as off limits", "Fix the server error on /robots.txt.")
  elif r.status != 404:
    add("low", "robots.txt", f"HTTP {r.status}", "Serve 200 with rules, or 404 for none.")
  groups, sitemaps = parse_robots(rtxt)
  path = (u.path or "/") + (f"?{u.query}" if u.query else "")
  rules = []
  for token in [*SEARCH, *AI_DATA, *extra]:
    ok, why = allowed(groups, token, path)
    rules.append({"agent": token, "kind": "search" if token in SEARCH else "ai/data", "allowed": ok, "rule": why or "no matching rule"})
    if not ok and token in SEARCH:
      add("critical", "robots.txt", f"{token} is blocked from {path} ({why})", "Remove the Disallow that covers this URL.")
  everywhere = sorted({a for g in groups for a in g[0] if a != "*" and not allowed(groups, a, "/")[0]})
  out.update(rules=rules, blocked_everywhere=everywhere, robots_present=bool(rtxt))
  if groups and not allowed(groups, "*", "/")[0]:
    add("critical", "robots.txt", "User-agent: * is blocked from /", "Remove 'Disallow: /' unless the site is meant to be private.")
  if rtxt and not sitemaps:
    add("low", "robots.txt", "no Sitemap line", "Add 'Sitemap: <absolute URL>' to robots.txt.")
  found, urls, seen = [urljoin(origin + "/", s) for s in sitemaps] or [origin + "/sitemap.xml"], [], []
  for sm in found[:3]:
    if urlsplit(sm).hostname != u.hostname:
      add("medium", "sitemap", f"{sm}: on another host, not fetched", "Serve the sitemap from this host.")
      continue
    got, probs = read_sitemap(sm, allow_private, timeout, 0, seen)
    urls += got
    for sev, area, msg in probs:
      if sm == origin + "/sitemap.xml" and not sitemaps and "HTTP 404" in msg:
        add("medium", "sitemap", "no sitemap found in robots.txt or at /sitemap.xml", "Publish a sitemap and list it in robots.txt.")
      else:
        add(sev, area, msg, "Fix the sitemap so crawlers can read every URL.")
  urls = list(dict.fromkeys(urls))
  host = (u.hostname or "").lower()
  mine, other = [], []
  for x in urls:
    (mine if (urlsplit(x).hostname or "").lower() == host else other).append(x)
  if other:
    add("medium", "sitemap", f"{len(other)} URL(s) on another host, e.g. {other[0]}", "List only URLs on this host.")
  if origin.startswith("https") and any(x.startswith("http://") for x in urls):
    add("medium", "sitemap", "lists http:// URLs on an https site", "List the https URLs.")
  out["sitemap_urls"] = len(urls)
  k = max(0, min(sample - 1, len(mine)))
  picks = [origin + "/"] + [mine[i * len(mine) // k] for i in range(k)]
  rows = []
  for i, pick in enumerate(dict.fromkeys(picks)):
    if sample < 1:
      break
    time.sleep(delay * (i > 0))
    row = sample_url(pick, allow_private, timeout)
    rows.append(row)
    where = f"{pick}: "
    if "error" in row:
      add("high", "page", where + row["error"], "Make the URL reachable.")
      continue
    if row["status"] != 200:
      add("critical" if row["status"] >= 400 else "high", "page", where + f"HTTP {row['status']} after {row['hops']} redirect(s)", "Serve 200, or remove the URL from links and sitemap.")
    elif row["hops"] > 1:
      add("medium", "page", where + f"{row['hops']} redirects ({' > '.join(map(str, row['chain']))})", "Link straight to the final URL.")
    elif row["hops"] == 1 and pick in mine:
      add("medium", "sitemap", where + "the sitemap lists a URL that redirects", "List the final URL.")
    if row["noindex"]:
      add("high", "page", where + "noindex", "Remove noindex, or drop the URL from the sitemap.")
    if row["canonical_mismatch"]:
      add("medium", "page", where + f"canonical points to {row['canonical'][0]}", "Point the canonical at this URL, or stop listing it.")
    if row["mixed"]:
      add("high", "page", where + f"{row['mixed']} http:// resource(s) on an https page", "Load every resource over https.")
  out.update(sample=rows, sample_size=len(rows))
  finds.sort(key=lambda f: SEV.index(f["severity"]))
  out["findings"] = finds
  return out


def render(res):
  lines = [f"Site Probe: {res['origin']}", "", f"robots.txt: HTTP {res.get('robots_status', 'unreachable')}" + ("" if res["robots_present"] else " (no rules)"), "  CRAWL RULES for the audited path"]
  lines += [f"    {r['kind']:<8}{r['agent']:<22}{'allowed' if r['allowed'] else 'BLOCKED':<9}{r['rule']}" for r in res["rules"]]
  if res["blocked_everywhere"]:
    lines.append("  Named agents blocked from the whole site: " + ", ".join(res["blocked_everywhere"]))
  lines += ["", f"Sitemap URLs found: {res['sitemap_urls']}", f"Sampled {res['sample_size']} URL(s)"]
  lines += [f"    {r['status'] if 'status' in r else 'ERR'} {r['hops'] if 'hops' in r else '-'} redirect(s)  {r['url']}" for r in res["sample"]]
  lines += ["", "FINDINGS (worst first)"] + [f"  [{f['severity'].upper()}] {f['area']}: {f['evidence']}\n      Fix: {f['fix']}" for f in res["findings"]]
  lines += ["  None."] * (not res["findings"])
  return "\n".join(lines + ["", "Blocking an AI crawler is a choice, not a fault. Name any other crawler tokens with --agent."])


def main(argv=None):
  ap = argparse.ArgumentParser(prog="site_probe.py", description="Check robots.txt, sitemaps and a sample of URLs.")
  ap.add_argument("url")
  ap.add_argument("--json", action="store_true", help="print the full result as JSON")
  ap.add_argument("--sample", type=int, default=10, help="URLs to fetch (0 to 50, default 10)")
  ap.add_argument("--allow-private", action="store_true", help="allow private, loopback and link-local addresses")
  ap.add_argument("--agent", action="append", default=[], help="extra crawler token to test (repeatable)")
  ap.add_argument("--delay", type=float, default=0.25, help="seconds between sampled requests")
  a = ap.parse_args(argv)
  if not 0 <= a.sample <= 50 or not 0 <= a.delay <= 10:
    ap.error("--sample must be 0 to 50 and --delay 0 to 10")
  url = a.url if "://" in a.url else "https://" + a.url
  try:
    res = probe(url, a.sample, a.allow_private, TIMEOUT, a.delay, a.agent)
  except FetchError as e:
    print(f"error: {e}", file=sys.stderr)
    return 2 if e.usage else 1
  print(json.dumps(res, indent=1) if a.json else render(res))
  return 1 if any(f["severity"] in ("critical", "high") for f in res["findings"]) else 0


if __name__ == "__main__":
  sys.stdout.reconfigure(errors="replace")
  sys.exit(main())
