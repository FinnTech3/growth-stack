# Symptoms, causes and proof

| Finding | Usual cause | Fix | Proof |
|---|---|---|---|
| `User-agent: * is blocked from /` | A staging `robots.txt` shipped to production | Replace the file; keep a `Disallow` only for paths that must stay private | Probe shows `Googlebot` allowed |
| A search crawler is blocked from a path | A broad `Disallow` that also matches the page | Narrow the rule or add a longer `Allow` (the longest matching rule wins) | The rules table shows allowed for that path |
| `robots.txt` served as HTML | A catch-all route or a CMS 404 page | Serve plain text at `/robots.txt` | `robots_status` 200 and rules read |
| `robots.txt` HTTP 5xx | Origin error, rate limit | Fix the origin; crawlers may treat the site as off limits meanwhile | Status 200 or 404 |
| No sitemap found | Never published | Generate one, list it with a `Sitemap:` line | `sitemap_urls` greater than 0 |
| Sitemap invalid XML or has a DTD | Hand-edited file, plugin bug | Regenerate with plain `<urlset>` and `<url><loc>` | No sitemap finding |
| Sitemap lists a URL that redirects | Old URLs kept in the list | List the final URL only | The finding disappears |
| A sampled URL returns 404 or 5xx | Deleted page still linked or listed | Restore, redirect once (301) or remove from links and sitemap | Status 200 |
| Redirect chain of two or more hops | Layered rules (http to https, then www, then slash) | One rule from the first URL to the final one | `hops` is 0 or 1 |
| `noindex` on a listed URL | Template or header left on from staging | Remove the meta tag and `X-Robots-Tag`, or drop the URL from the sitemap | `noindex` false |
| Canonical points elsewhere | Copied template, parameter handling | Point the canonical at the page itself, or stop listing the page | `canonical_mismatch` false |
| http resources on an https page | Hard-coded old URLs in templates | Load every resource over https | `mixed` is 0 |

## Crawlers

The built-in list covers four search crawlers and a short list of data crawlers. Any other token goes in with
`--agent`. A named group that blocks the whole site shows in `blocked_everywhere` even when the script has never
heard of it. Whether that is right is the owner's call.
