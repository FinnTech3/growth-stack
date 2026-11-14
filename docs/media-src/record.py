#!/usr/bin/env python3
"""Run real commands and write a terminal cast (JSON) from their real output.

Usage: python3 record.py spec.json cast.json

spec.json keys:
  title, env, width, rows, wrap, fontSize, highlight, typingSeconds, endHoldSeconds, poster
  cwd       a folder to run in; leave it out to run in a fresh empty temporary folder
  setup     shell commands run in that folder first and not shown; $REPO_ROOT is this repository
  teardown  shell commands run in that folder at the end (for example stopping a server)
  steps: a list of
    {"note": "# a comment line"}
    {"cmd": "real command", "show": "what to display instead", "maxLines": 12, "expectExit": [0, 1]}
    {"run": "runs but is not shown, for example swapping the page a local server serves"}
    {"pause": 800}

"show" only shortens what is displayed (for example a long path). It never changes what runs.
Output longer than maxLines is cut and a "... (N more lines)" line says so.
A command whose exit code is not in expectExit (default [0]) makes this script fail.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def wrap_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for line in text.split("\n"):
        wrapped = textwrap.wrap(
            line, width, replace_whitespace=False, drop_whitespace=False, subsequent_indent="  "
        )
        lines.extend(wrapped or [""])
    return lines


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    cast = {
        "title": spec.get("title", "terminal"),
        "width": spec.get("width", 940),
        "rows": spec.get("rows", 22),
        "fontSize": spec.get("fontSize", 15),
        "typingSeconds": spec.get("typingSeconds", 3),
        "endHoldSeconds": spec.get("endHoldSeconds", 3),
        "poster": spec.get("poster", False),
        "highlight": spec.get("highlight", []),
        "steps": [],
    }
    wrap = spec.get("wrap", 98)
    env = dict(os.environ)
    env.update(spec.get("env", {}))
    env.setdefault("COLUMNS", str(wrap))
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("NO_COLOR", "1")
    env["REPO_ROOT"] = str(ROOT)
    cwd = spec.get("cwd") or tempfile.mkdtemp(prefix="record-")
    try:
        for command in spec.get("setup", []):
            subprocess.run(["bash", "-c", command], cwd=cwd, env=env, check=True)
        return run_steps(spec, cast, env, cwd, wrap)
    finally:
        for command in spec.get("teardown", []):
            subprocess.run(["bash", "-c", command], cwd=cwd, env=env, check=False)
        if not spec.get("cwd"):
            shutil.rmtree(cwd, ignore_errors=True)


def run_steps(spec: dict, cast: dict, env: dict[str, str], cwd: str, wrap: int) -> int:
    for step in spec["steps"]:
        if "note" in step:
            cast["steps"].append({"type": "note", "text": step["note"]})
        elif "pause" in step:
            cast["steps"].append({"type": "pause", "ms": step["pause"]})
        elif "run" in step:
            subprocess.run(["bash", "-c", step["run"]], cwd=cwd, env=env, check=True)
        elif "cmd" in step:
            done = subprocess.run(
                ["bash", "-c", step["cmd"]],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=step.get("timeout", 120),
                check=False,
            )
            if done.returncode not in step.get("expectExit", [0]):
                print(f"command failed ({done.returncode}): {step['cmd']}", file=sys.stderr)
                print(done.stdout + done.stderr, file=sys.stderr)
                return 1
            lines = wrap_lines((done.stdout + done.stderr).rstrip("\n"), wrap)
            limit = step.get("maxLines")
            if limit and len(lines) > limit:
                lines = [*lines[:limit], f"... ({len(lines) - limit} more lines)"]
            cast["steps"].append({"type": "cmd", "text": step.get("show", step["cmd"])})
            if lines != [""]:
                cast["steps"].append(
                    {"type": "out", "text": "\n".join(lines), "holdSeconds": step.get("hold", 1.4)}
                )
    Path(sys.argv[2]).write_text(json.dumps(cast, indent=1), encoding="utf-8")
    print(f"wrote {sys.argv[2]}: {len(cast['steps'])} steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
