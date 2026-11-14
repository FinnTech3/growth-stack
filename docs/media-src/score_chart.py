#!/usr/bin/env python3
"""Write an HTML chart of three audits of the fixture site, drawn from real page_audit.py output.

Usage: python3 docs/media-src/score_chart.py OUT.html
Then:  node docs/media-src/shot.mjs OUT.html docs/score-loop.png 1200 0 2

Each fixture folder (before, loop-1, loop-2) is served on an ephemeral local port, audited with the real
agensi/growth-stack/shared/scripts/page_audit.py --json, and the scores are read from that JSON. The captions say
what each loop fixed, as the worked example describes it; every number comes from the audits.
"""

from __future__ import annotations

import functools
import html
import json
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "agensi/growth-stack/shared/scripts/page_audit.py"
SITE = ROOT / "agensi/growth-stack/examples/fixture-site"
LOOPS = [
    ("before", "As found", 'Title "Home", a "Submit" button, a form with eight fields, no JSON-LD'),
    ("loop-1", "After loop 1", "Fixed the top three: button and form, title and share tags, JSON-LD"),
    ("loop-2", "After loop 2", "Fixed the next three: mobile basics, question headings, contact and policy links"),
]
HOSTING = {"served over https", "gzip and a cache header", "3+ of 5 security headers"}
REVIEW_PROOF = {"proof such as reviews (heuristic)"}


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:
        pass


def audit(folder: str) -> dict:
    handler = functools.partial(Quiet, directory=str(SITE / folder))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        done = subprocess.run(
            [sys.executable, str(SCRIPT), url, "--allow-private", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    finally:
        server.shutdown()
    if done.returncode not in (0, 1):
        raise SystemExit(f"page_audit.py failed on {folder}: {done.stderr}")
    return json.loads(done.stdout)


def lost_points(result: dict, labels: set[str]) -> int:
    return sum(
        part["points"] - part["earned"]
        for check in result["checks"]
        for part in check["parts"]
        if part["label"] in labels
    )


def colour(score: int) -> str:
    return "#f87171" if score < 40 else "#fbbf24" if score < 65 else "#4ade80"


def panel(result: dict, title: str, caption: str, previous: int | None) -> str:
    score = result["score"]
    delta = "" if previous is None else f'<span class="delta">+{score - previous}</span>'
    bars = "".join(
        f'<div class="row"><span class="cat">{html.escape(name)}</span>'
        f'<span class="track"><i style="width:{100 * c["earned"] / c["max"]:.1f}%"></i></span>'
        f'<span class="val">{c["earned"]}/{c["max"]}</span></div>'
        for name, c in result["categories"].items()
    )
    return (
        f'<div class="panel"><div class="title">{html.escape(title)}</div>'
        f'<div class="score" style="color:{colour(score)}">{score}<small>/100</small>{delta}</div>'
        f'<div class="caption">{html.escape(caption)}</div>{bars}</div>'
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    results = [audit(folder) for folder, _, _ in LOOPS]
    panels, previous = [], None
    for result, (_, title, caption) in zip(results, LOOPS, strict=True):
        panels.append(panel(result, title, caption, previous))
        previous = result["score"]
    final = results[-1]
    lost = final["max"] - final["score"]
    hosting, proof = lost_points(final, HOSTING), lost_points(final, REVIEW_PROOF)
    note = (
        f"Still lost at {final['score']}: {lost} points. Hosting: {hosting} (https, caching, security headers), "
        f"which a plain local server cannot give. Review proof: {proof}, which it will not invent. "
        f"The other {lost - hosting - proof} are listed in the worked example, with the reason for each."
    )
    template = (Path(__file__).parent / "score_chart.template.html").read_text(encoding="utf-8")
    page = template.replace("{{PANELS}}", "\n".join(panels)).replace("{{NOTE}}", html.escape(note))
    page = page.replace("{{HEADLINE}}", " &rarr; ".join(str(r["score"]) for r in results))
    Path(sys.argv[1]).write_text(page, encoding="utf-8")
    print(f"wrote {sys.argv[1]}: scores {[r['score'] for r in results]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
