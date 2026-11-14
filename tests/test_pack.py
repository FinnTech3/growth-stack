"""The pack as Agensi will see it: layout, frontmatter, scripts, copies, listing and house rules."""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml
from conftest import PACK, ROOT, SCRIPTS
from pages import GOOD

SKILLS = sorted(p.parent for p in (PACK / "skills").glob("*/SKILL.md"))
NAMES = [s.name for s in SKILLS]


def frontmatter(skill: Path) -> dict:
    text = (skill / "SKILL.md").read_text()
    return yaml.safe_load(text.split("---", 2)[1])


def test_there_are_fifteen_distinct_skills():
    assert len(SKILLS) == 15 and len(set(NAMES)) == 15


@pytest.mark.parametrize("skill", SKILLS, ids=NAMES)
def test_skill_file_shape(skill):
    path = skill / "SKILL.md"
    text = path.read_text()
    assert len(text.splitlines()) <= 120
    fm = frontmatter(skill)
    assert set(fm) == {"name", "description"}
    assert fm["name"] == skill.name and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"])
    desc = fm["description"]
    assert len(desc) < 1024
    use_when = desc.split("Use when", 1)[1].split("Do not use for", 1)[0]
    assert 3 <= len(re.findall(r'"[^"]{4,}"', use_when)) <= 5
    assert "Do not use for" in desc
    body = text.split("---", 2)[2]
    for heading in ("## Inputs", "## Steps", "## Output", "## Exit criteria", "## Edge cases and errors", "## Rules"):
        assert heading in body, heading
    assert re.search(r"^Requires: ", body, re.M)
    assert body.count("- [ ] ") >= 4  # exit criteria the agent can tick


@pytest.mark.parametrize("skill", SKILLS, ids=NAMES)
def test_do_not_use_lines_point_at_real_neighbours(skill):
    desc = frontmatter(skill)["description"]
    refs = re.findall(r"use `([a-z-]+)`", desc)
    assert refs, "every skill names at least one neighbour"
    assert all(r in NAMES and r != skill.name for r in refs)


@pytest.mark.parametrize("skill", SKILLS, ids=NAMES)
def test_scripts_are_run_from_a_temporary_file_never_by_path(skill):
    text = (skill / "SKILL.md").read_text()
    scripts = sorted(set(re.findall(r"shared/scripts/(\w+)\.py", text)))
    assert not re.search(r"(?m)^\s*(\$\s*)?python3?\s+(\./)?(shared/)?scripts/", text)
    if scripts:
        assert "## Running the script" in text and "unchanged" in text and "temporary file" in text
        assert 'python3 "$' in text and "rm -f" in text
        assert "network" in text.lower()
        for name in scripts:
            assert (PACK / "shared" / "scripts" / f"{name}.py").is_file(), name
    else:
        assert "## Running the script" not in text


@pytest.mark.parametrize("skill", SKILLS, ids=NAMES)
def test_every_reference_is_linked_and_every_link_resolves(skill):
    text = (skill / "SKILL.md").read_text()
    for link in re.findall(r"\]\((references/[^)#]+)\)", text):
        assert (skill / link).is_file()
    for ref in (skill / "references").glob("*.md") if (skill / "references").is_dir() else []:
        assert f"references/{ref.name}" in text, f"{ref} is not linked from SKILL.md"


def test_every_script_is_standard_library_only_and_under_20kb():
    stdlib = set(sys.stdlib_module_names)
    for path in (PACK / "shared" / "scripts").glob("*.py"):
        text = path.read_text()
        assert len(text.encode()) <= 20 * 1024, path
        for mod in re.findall(r"^(?:import|from)\s+([a-z_]+)", text, re.M):
            assert mod in stdlib, f"{path.name} imports {mod}"
        for bad in ("shell=True", "os.system", "eval(", "exec(", "base64", "subprocess", "os.environ", "pickle"):
            assert bad not in text, f"{path.name} contains {bad}"
        assert text.startswith("#!/usr/bin/env python3\n")


def test_network_scripts_read_no_local_files_and_text_stats_makes_no_network_calls():
    for name in ("page_audit", "site_probe"):
        text = SCRIPTS[name].read_text()
        assert not re.search(r"\bopen\s*\(|read_text|read_bytes|Path\(", text), name
    stats = SCRIPTS["text_stats"].read_text()
    assert not re.search(r"urllib|socket|http\.client|ssl", stats)


def test_each_script_exists_exactly_once_in_the_shared_folder():
    found = sorted(p.name for p in PACK.rglob("*.py"))
    assert found == ["page_audit.py", "site_probe.py", "text_stats.py"]
    assert all(p.parent == PACK / "shared" / "scripts" for p in PACK.rglob("*.py"))


def test_every_skill_that_names_a_script_names_its_shared_path():
    for skill in SKILLS:
        text = (skill / "SKILL.md").read_text()
        for name in re.findall(r"(?<![\w/])(?:shared/)?scripts/(page_audit|site_probe|text_stats)\.py", text):
            assert f"shared/scripts/{name}.py" in text, f"{skill.name} names {name}.py without the shared path"
        assert not re.search(
            r"(?<![\w/])scripts/(page_audit|site_probe|text_stats)", text.replace("shared/scripts/", "")
        ), skill.name


def test_every_script_runs_alone_from_an_empty_directory(tmp_path):
    for path in (PACK / "shared" / "scripts").glob("*.py"):
        lone = tmp_path / path.name
        lone.write_bytes(path.read_bytes())
        out = subprocess.run(
            [sys.executable, "-I", str(lone), "--help"], capture_output=True, text=True, cwd=tmp_path, check=False
        )
        assert out.returncode == 0 and "usage:" in out.stdout, path


def test_a_script_run_as_a_subprocess_gives_the_documented_exit_codes(tmp_path):
    lone = tmp_path / "page_audit.py"
    lone.write_bytes(SCRIPTS["page_audit"].read_bytes())
    private = subprocess.run(
        [sys.executable, "-I", str(lone), "http://127.0.0.1:9/"], capture_output=True, text=True, check=False
    )
    assert private.returncode == 2 and "private or reserved" in private.stderr
    usage = subprocess.run([sys.executable, "-I", str(lone)], capture_output=True, text=True, check=False)
    assert usage.returncode == 2


def test_the_worked_example_reproduces_on_the_fixture_site(pa, site):
    fx = PACK / "examples" / "fixture-site"
    expected = {"before": 23, "loop-1": 56, "loop-2": 72}
    for stage, score in expected.items():
        site.routes.clear()
        for f in (fx / stage).rglob("*"):
            if f.is_file():
                rel = "/" + f.relative_to(fx / stage).as_posix()
                body = f.read_bytes()
                ctype = "text/html" if f.suffix == ".html" else "text/plain"
                site.routes[rel.removesuffix("index.html") if rel.endswith("index.html") else rel] = {
                    "body": body,
                    "headers": {"Content-Type": ctype},
                }
        res = pa.analyze(pa.get(site.url("/"), True))
        assert res["score"] == score, stage
    text = (PACK / "examples" / "growth-loop-worked-example.md").read_text()
    for score in ("23/100", "56/100", "72/100"):
        assert score in text


def test_the_lost_points_quoted_in_the_readme_are_true_for_loop_2(pa, site):
    stage = PACK / "examples" / "fixture-site" / "loop-2"
    for f in stage.rglob("*"):
        if f.is_file():
            rel = "/" + f.relative_to(stage).as_posix()
            ctype = "text/html" if f.suffix == ".html" else "text/plain"
            site.routes[rel.removesuffix("index.html") if rel.endswith("index.html") else rel] = {
                "body": f.read_bytes(),
                "headers": {"Content-Type": ctype},
            }
    res = pa.analyze(pa.get(site.url("/"), True))
    parts = [(p["label"], p["points"] - p["earned"]) for c in res["checks"] for p in c["parts"]]
    lost = {label: points for label, points in parts if points}
    hosting = ("served over https", "gzip and a cache header", "3+ of 5 security headers")
    assert res["max"] - res["score"] == 28 == sum(lost.values())
    assert sum(lost.get(label, 0) for label in hosting) == 6
    assert lost["proof such as reviews (heuristic)"] == 3
    readme = " ".join((ROOT / "README.md").read_text().split())
    assert "still loses 28 points: 6 are hosting" in readme and "3 are review proof" in readme


def test_root_readme_images_exist_and_have_alt_text():
    text = (ROOT / "README.md").read_text()
    tags = re.findall(r"<img [^>]*>", text)
    assert tags
    for tag in tags:
        assert re.search(r'alt="[^"]+"', tag), f"image without alt text: {tag}"
        src = re.search(r'src="([^"]+)"', tag).group(1)
        if not src.startswith("http"):
            assert (ROOT / src).is_file(), src
    for link in re.findall(r"\]\(((?:docs|agensi)/[^)#]+)\)", text):
        assert (ROOT / link).exists(), link


def test_pack_readme_starts_with_the_pack_name_and_lists_every_skill():
    readme = (PACK / "README.md").read_text()
    assert readme.startswith("# Growth Stack\n")
    for name in NAMES:
        assert f"`{name}`" in readme


def test_listing_matches_the_pack():
    listing = (ROOT / "agensi" / "LISTING.md").read_text()
    title = re.search(r"\| Title \| (.+?) \|", listing).group(1)
    assert title == "Growth Stack: SEO and Marketing Skills in One Pack" and len(title) <= 60
    assert "Marketing & SEO; Sales & Lead Gen; Writing & Content" in listing
    assert "15 `SKILL.md` files" in listing


def test_trigger_tests_cover_every_skill_and_say_they_have_not_been_run():
    text = (ROOT / "agensi" / "TRIGGER_TESTS.md").read_text()
    assert "not yet run in an agent" in text
    for name in NAMES:
        assert f"`{name}`" in text


def test_credit_and_licence_are_finntech3_only():
    assert "MIT" in (ROOT / "LICENSE").read_text().splitlines()[0]
    assert "Copyright (c) 2026 FinnTech3" in (ROOT / "LICENSE").read_text()


def test_the_pack_zip_extracts_cleanly(tmp_path):
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "agensi_build.py"), str(PACK), "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert out.returncode == 0 and "0 failed, 0 warning(s)" in out.stdout, out.stdout
    with zipfile.ZipFile(tmp_path / "growth-stack.zip") as zf:
        names = zf.namelist()
        assert sum(n.endswith("SKILL.md") for n in names) == 15
        assert all(n.startswith("growth-stack/") for n in names)
        assert not [n for n in names if "__pycache__" in n or n.endswith(".png")]


def test_example_fixture_has_the_flaws_it_claims():
    before = (PACK / "examples" / "fixture-site" / "before" / "index.html").read_text()
    assert "<title>Home</title>" in before and 'name="description"' not in before and "Submit" in before
    assert GOOD  # the shared test fixture is importable
