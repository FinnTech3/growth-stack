#!/usr/bin/env bash
# Regenerate every image in docs/ and agensi/media/screenshot-*.png from this repository's real output.
# Needs on PATH: python3 with PyYAML and Pillow, node with playwright (NODE_PATH can point at it), ffmpeg.
# Nothing is typed by hand: the clip and the stills run the real scripts on the bundled fixture site, the
# chart reads their --json output, and the grid is read from the real SKILL.md files and `--help` text.
set -euo pipefail
cd "$(dirname "$0")/../.."
src=docs/media-src
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# 1. The audit, fix, re-audit clip (gif and mp4).
python3 $src/record.py $src/loop.spec.json "$tmp/loop.cast.json"
node $src/termcast.mjs "$tmp/loop.cast.json" docs/demo.gif docs/demo.mp4

# 2. What moved between the first audit and the second loop (a 2x still of the real compare output).
python3 $src/record.py $src/moved.spec.json "$tmp/moved.cast.json"
node $src/termcast.mjs "$tmp/moved.cast.json" "$tmp/moved.png" --still
python3 $src/squash.py "$tmp/moved.png" docs/what-moved.png 64

# 3. The score chart, drawn from page_audit.py --json on the three fixture folders.
python3 $src/score_chart.py "$tmp/chart.html"
node $src/shot.mjs "$tmp/chart.html" "$tmp/chart.png" 1200 0 2
python3 $src/squash.py "$tmp/chart.png" docs/score-loop.png 128

# 4. The skill grid.
python3 $src/grid.py "$tmp/grid.html"
node $src/shot.mjs "$tmp/grid.html" "$tmp/grid.png" 1200 0 2
python3 $src/squash.py "$tmp/grid.png" docs/skills-grid.png 128

# 5. The GitHub social preview (upload it by hand in the repository settings).
node $src/shot.mjs $src/social.html "$tmp/social.png" 1280 640 1
python3 $src/squash.py "$tmp/social.png" docs/social-preview.png 200

# 6. The marketplace screenshots (logo.png is kept as it is).
cp docs/score-loop.png agensi/media/screenshot-1.png
cp docs/skills-grid.png agensi/media/screenshot-2.png
cp docs/what-moved.png agensi/media/screenshot-3.png
