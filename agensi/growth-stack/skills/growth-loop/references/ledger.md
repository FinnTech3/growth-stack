# Ledger and comparison

Keep one row per loop. The numbers come from the two audit files, not from memory.

| Date | URL | Score before | Gaps fixed | Score after | Parts recovered | Parts still lost, and why |
|---|---|---|---|---|---|---|
| (date of the after audit) | (final URL) | (before.json score) | (check ids) | (after.json score) | (labels) | (host-only, needs real proof, heuristic) |

## Compare two audits

Run this with the two JSON files, using the temporary-file routine from the skill (it uses the standard library only and
reads local files, never the network):

```python
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
print("score", a["score"], "->", b["score"])
pts = lambda r: {(c["id"], p["label"]): p["earned"] for c in r["checks"] for p in c["parts"]}
pa, pb = pts(a), pts(b)
for key in pa:
    if pa[key] != pb.get(key):
        print(("+" if pb.get(key, 0) > pa[key] else "-"), *key, pa[key], "->", pb.get(key, 0))
```

Any line that starts with `-` is a regression. Explain it or revert the change.

## What the score cannot say

It says nothing about traffic, rankings, revenue or whether the copy is true. Say that in every report.
