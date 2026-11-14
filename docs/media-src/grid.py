#!/usr/bin/env python3
"""Write an HTML grid: one card per skill, with trigger phrases quoted from its real frontmatter.

Usage: python3 docs/media-src/grid.py OUT.html
Then:  node docs/media-src/shot.mjs OUT.html docs/skills-grid.png 1200 0 2

Needs PyYAML. Skill names, trigger phrases and one-line script descriptions are read from the repository: the
SKILL.md frontmatter, and `--help` of each script. The loop step and script of each skill come from the table in
agensi/growth-stack/README.md. Only the step colours are chosen here.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "agensi/growth-stack"
STEP_COLOURS = {"Audit": "#7dd3fc", "Fix": "#86efac", "Plan": "#fde68a", "Measure": "#f9a8d4"}
MAX_PHRASE_CHARS = 82  # whole phrases only, never cut in the middle


def frontmatter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


def pack_table() -> dict[str, tuple[str, str]]:
    """Map skill name to (loop step, script column) from the pack README table."""
    text = (PACK / "README.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\w+) \| \[`([a-z0-9-]+)`\]\([^)]*\) \| .*? \| (.+?) \|$", text, re.M)
    return {name: (step, scripts.replace("`", "")) for step, name, scripts in rows}


def trigger_phrases(description: str) -> list[str]:
    use_sentence = description.split("Do not use")[0]
    chosen: list[str] = []
    for phrase in re.findall(r'"([^"]+)"', use_sentence):
        if len(chosen) == 3 or sum(len(p) for p in [*chosen, phrase]) > MAX_PHRASE_CHARS:
            break
        chosen.append(phrase)
    return chosen


def script_summary(script: Path) -> str:
    out = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, text=True, check=True
    ).stdout
    return " ".join(out.split("\n\n")[1].split())


def card(name: str, step: str, scripts: str, phrases: list[str]) -> str:
    lines = "".join(f"<li>&ldquo;{html.escape(p)}&rdquo;</li>" for p in phrases)
    used = "no script" if scripts == "none" else scripts
    return (
        f'<div class="card" style="--c:{STEP_COLOURS[step]}"><div class="chip">{html.escape(step)}</div>'
        f'<div class="name">{html.escape(name)}</div><ul>{lines}</ul>'
        f'<div class="uses">{html.escape(used)}</div></div>'
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    table = pack_table()
    folders = sorted((PACK / "skills").iterdir())
    missing = {f.name for f in folders} - set(table)
    if missing:
        raise SystemExit(f"pack README table has no row for: {sorted(missing)}")
    order = list(STEP_COLOURS)
    rows = []
    for folder in folders:
        step, scripts = table[folder.name]
        meta = frontmatter(folder / "SKILL.md")
        rows.append((order.index(step), folder.name, step, scripts, trigger_phrases(meta["description"])))
    rows.sort()
    cards = [card(name, step, scripts, phrases) for _, name, step, scripts, phrases in rows]
    scripts_html = "".join(
        f'<div class="script"><div class="sname">{path.name}</div>'
        f'<div class="sdesc">{html.escape(script_summary(path))}</div></div>'
        for path in sorted((PACK / "shared/scripts").glob("*.py"))
    )
    template = (Path(__file__).parent / "grid.template.html").read_text(encoding="utf-8")
    page = (
        template.replace("{{COUNT}}", str(len(rows)))
        .replace("{{CARDS}}", "\n".join(cards))
        .replace("{{SCRIPTS}}", scripts_html)
    )
    Path(sys.argv[1]).write_text(page, encoding="utf-8")
    print(f"wrote {sys.argv[1]}: {len(rows)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
