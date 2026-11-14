"""text_stats.py: offline text measurement. No network, so no server here."""

from __future__ import annotations

import io
import json
import sys

import pytest
from conftest import SCRIPTS

SAMPLE = """# Bike repair in Harbour Street

We fix bikes. We fix brakes. We fix gears. Our team is trained by experts, and you might get a quote today.

## How much does a service cost?

A basic service costs from 45 pounds. The frame is checked by a mechanic. It is built to last.

```
We fix this code block, which must not be counted as prose.
```

- Fast, innovative and robust service
- Call us today

See the [price list](https://example.com/prices) and ![logo](logo.png).
"""


def run(ts, capsys, *argv, stdin=None, monkeypatch=None):
    if stdin is not None:
        monkeypatch.setattr(
            sys, "stdin", io.TextIOWrapper(io.BytesIO(stdin if isinstance(stdin, bytes) else stdin.encode()))
        )
    code = ts.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def stats(ts, text, **kw):
    return ts.analyse(text, kw.get("top", 10), kw.get("keywords", []), kw.get("flags", []), kw.get("wpm", 200))


def test_syllable_heuristic(ts):
    assert [ts.syllables(w) for w in ("cat", "table", "service", "make", "beautiful", "the", "rhythm")] == [
        1,
        2,
        2,
        1,
        3,
        1,
        1,
    ]


def test_readability_follows_the_stated_formulas(ts):
    r = stats(ts, "The cat sat on the mat. The dog ran to the park.")
    w, s, syl = r["words"], r["sentences"], r["syllables"]
    assert (w, s) == (12, 2)
    assert r["readability"]["flesch_reading_ease"] == round(206.835 - 1.015 * (w / s) - 84.6 * (syl / w), 1)
    assert r["readability"]["flesch_kincaid_grade"] == round(0.39 * (w / s) + 11.8 * (syl / w) - 15.59, 1)
    assert any("206.835" in f for f in r["readability"]["formulas"])


@pytest.mark.parametrize(
    ("text", "band"),
    [
        ("The cat sat. The dog ran. A man had a pen.", "very easy"),
        (
            "Notwithstanding unprecedented organisational interdependencies, multidisciplinary "
            "administrators systematically operationalise comprehensive infrastructure.",
            "very difficult",
        ),
    ],
)
def test_readability_bands(ts, text, band):
    assert stats(ts, text)["readability"]["band"] == band


def test_code_fences_links_images_and_headings_are_not_prose(ts):
    r = stats(ts, SAMPLE)
    assert "code block" not in " ".join(w for w, _ in r["top_words"])
    assert [h["heading"] for h in r["outline"]] == ["Bike repair in Harbour Street", "How much does a service cost?"]
    assert [h["level"] for h in r["outline"]] == [1, 2]
    plain = (
        "We fix bikes. We fix brakes. We fix gears. Our team is trained by experts, and you might get a quote today.\n\n"
        "A basic service costs from 45 pounds. The frame is checked by a mechanic. It is built to last.\n\n"
        "Fast, innovative and robust service\n\nCall us today\n\nSee the price list and logo."
    )
    twin = stats(ts, plain)
    assert (r["words"], r["paragraphs"]) == (twin["words"], twin["paragraphs"])  # markup changes nothing


def test_counts_paragraphs_sentences_and_long_sentences(ts):
    long = "word " * 30 + "end."
    r = stats(ts, f"One short sentence. Another one here.\n\n{long}")
    assert r["paragraphs"] == 2 and r["sentences"] == 3 and r["long_sentences_over_25_words"] == 1


def test_reading_time_uses_the_stated_speed(ts):
    text = ("word " * 400).strip() + "."
    assert stats(ts, text, wpm=200)["reading_time_seconds"] == 120
    assert stats(ts, text, wpm=400)["reading_time_seconds"] == 60


def test_keyword_density_headings_and_first_100_words(ts):
    r = stats(ts, SAMPLE, keywords=["service", "bike repair", "Nothing Here"])
    by = {k["phrase"]: k for k in r["keywords"]}
    assert by["service"]["count"] == 2 and by["service"]["in_headings"] and by["service"]["in_first_100_words"]
    assert (
        by["bike repair"]["count"] == 0
        and by["bike repair"]["in_headings"]
        and not by["bike repair"]["in_first_100_words"]
    )
    assert by["Nothing Here"]["count"] == 0 and not by["Nothing Here"]["in_headings"]
    assert by["service"]["per_100_words"] == round(2 * 100 / r["words"], 2)


def test_keyword_matching_is_whole_word_and_case_insensitive(ts):
    r = stats(ts, "Servicing is not service. SERVICE matters.", keywords=["service"])
    assert r["keywords"][0]["count"] == 2


def test_top_words_drop_stopwords_and_top_phrases_need_repeats(ts):
    r = stats(ts, "Fast bike repair near you. Fast bike repair is what we do. The bike repair shop.")
    words = dict(r["top_words"])
    assert "the" not in words and words["bike"] == 3 and words["repair"] == 3
    phrases = dict(r["top_phrases"])
    assert phrases["bike repair"] == 3 and "fast bike repair" in phrases
    assert all(c >= 2 for c in phrases.values())


def test_top_flag_limits_the_lists(ts):
    text = (
        " ".join(f"alpha{c}" * 1 for c in "abcdefghijklmnop") + ". " + " ".join(f"alpha{c}" for c in "abcdefghijklmnop")
    )
    assert len(stats(ts, text, top=3)["top_words"]) == 3


def test_repeated_openings_and_same_start_runs(ts):
    r = stats(ts, "We fix bikes. We fix brakes. We fix gears. We fix wheels. Prices are fair.")
    assert r["repeated_openings"] == [("we fix", 4)]
    assert r["same_start_runs"] == ["We"]
    calm = stats(ts, "Bikes are fixed here. Brakes get adjusted. Gears run smooth. Wheels are trued.")
    assert calm["repeated_openings"] == [] and calm["same_start_runs"] == []


def test_passive_voice_is_counted_with_examples(ts):
    r = stats(ts, "The brakes were fixed by Sam. The shop is owned by Alex. We fix brakes. It was built quickly.")
    assert r["passive_heuristic"]["count"] == 3
    assert "were fixed" in r["passive_heuristic"]["examples"]
    assert stats(ts, "We fix brakes. Sam rides bikes.")["passive_heuristic"]["count"] == 0


def test_hedge_and_hype_words_are_counted_and_custom_flags_work(ts):
    r = stats(
        ts,
        "This might work. Perhaps it could help. It is a cutting-edge, robust tool. Our proprietary engine runs.",
        flags=["proprietary"],
    )
    assert r["hedges_heuristic"] == {"might": 1, "perhaps": 1, "could": 1}
    assert r["hype_heuristic"] == {"cutting-edge": 1, "robust": 1, "proprietary": 1}


def test_you_versus_we_balance(ts):
    r = stats(ts, "We make it. Our team and we love it. You get your bike back. You will see.")
    assert r["you_we"] == {"you": 3, "we": 3}


def test_json_output_is_valid_and_complete(ts, capsys, tmp_path):
    f = tmp_path / "a.md"
    f.write_text(SAMPLE)
    code, out, _ = run(ts, capsys, str(f), "--json", "--keyword", "service")
    data = json.loads(out)
    assert code == 0 and data["words"] > 30 and data["keywords"][0]["phrase"] == "service"
    for key in (
        "readability",
        "outline",
        "top_words",
        "top_phrases",
        "passive_heuristic",
        "hedges_heuristic",
        "you_we",
        "reading_time_seconds",
    ):
        assert key in data


def test_text_report_states_the_formulas_and_labels_heuristics(ts, capsys, tmp_path):
    f = tmp_path / "a.md"
    f.write_text(SAMPLE)
    _, out, _ = run(ts, capsys, str(f))
    assert "Flesch Reading Ease = 206.835" in out and "Flesch-Kincaid grade = 0.39" in out
    assert "Passive voice (heuristic)" in out and "Hedge words (heuristic)" in out and "rule of thumb" in out


def test_reads_stdin_when_given_a_dash_or_nothing(ts, capsys, monkeypatch):
    code, out, _ = run(ts, capsys, "-", "--json", stdin="Hello there. Good bikes.", monkeypatch=monkeypatch)
    assert code == 0 and json.loads(out)["words"] == 4
    code, out, _ = run(ts, capsys, "--json", stdin="One two three.", monkeypatch=monkeypatch)
    assert json.loads(out)["words"] == 3


def test_missing_file_empty_input_and_binary_input_exit_2_cleanly(ts, capsys, monkeypatch, tmp_path):
    code, out, err = run(ts, capsys, str(tmp_path / "nope.md"))
    assert code == 2 and err.startswith("error: cannot read") and out == ""
    code, _, err = run(ts, capsys, "-", stdin="   \n\n", monkeypatch=monkeypatch)
    assert code == 2 and "no words" in err
    code, _, err = run(ts, capsys, "-", stdin=b"abc\x00\x01\x02" * 50, monkeypatch=monkeypatch)
    assert code == 2 and "not text" in err
    code, _, err = run(ts, capsys, str(tmp_path))  # a directory
    assert code == 2 and "Traceback" not in err


def test_oversized_input_is_refused(ts, capsys, monkeypatch):
    code, _, err = run(ts, capsys, "-", stdin=b"a " * 3_000_000, monkeypatch=monkeypatch)
    assert code == 2 and "over 5 MB" in err


@pytest.mark.parametrize("bad", [["--top", "0"], ["--top", "101"], ["--wpm", "0"], ["--top", "abc"]])
def test_bad_options_exit_2(ts, capsys, bad):
    with pytest.raises(SystemExit) as exc:
        ts.main(["-", *bad])
    assert exc.value.code == 2


def test_invalid_utf8_and_odd_characters_do_not_crash(ts):
    r = ts.analyse(
        b"caf\xe9 \xff\xfe bikes \xf0\x9f\x9a\xb2 are fine. Second one!".decode("utf-8", "replace"), 5, [], [], 200
    )
    assert r["words"] > 3


def test_single_word_and_no_sentence_ending_inputs(ts):
    assert stats(ts, "bikes")["sentences"] == 1
    assert stats(ts, "no full stop here")["words"] == 4


def test_script_makes_no_network_calls():
    text = SCRIPTS["text_stats"].read_text()
    for needle in ("urllib", "socket", "http.client", "requests", "ssl", "subprocess", "os.system", "eval(", "exec("):
        assert needle not in text


# ---- found by hostile review -------------------------------------------------------------------------------------


def test_a_huge_single_sentence_does_not_crash_the_readability_band(ts):
    res = stats(ts, "word " * 5000 + ".")
    assert res["readability"]["band"] == "very difficult"


def test_lines_mode_counts_every_line_as_a_sentence_and_phrases_do_not_cross_lines(ts):
    text = "red shoes\ncheap red\nshoes sale\n"
    res = ts.analyse(text, 10, [], [], 200, True)
    assert res["sentences"] == 3 and res["paragraphs"] == 3
    assert ts.analyse(text, 10, [], [], 200)["sentences"] == 1
    assert "red shoes" in dict(res["top_phrases"]) or res["top_phrases"] == []
    assert ("red cheap", 1) not in res["top_phrases"]


def test_phrases_are_not_built_across_paragraphs(ts):
    res = stats(ts, "alpha beta\n\nbeta gamma\n\nalpha beta\n\nbeta gamma\n")
    phrases = dict(res["top_phrases"])
    assert "alpha beta" in phrases and "beta beta" not in phrases


def test_a_byte_order_mark_does_not_hide_the_first_heading(ts, tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_bytes("﻿# Title here\n\nSome words follow.\n".encode())
    code, out, _ = run(ts, capsys, str(f), "--json")
    assert code == 0 and json.loads(out)["outline"][0]["heading"] == "Title here"


@pytest.mark.parametrize("text", ["*a " * 80_000, "[" * 200_000, "<" * 200_000, "`" * 200_000, " " * 4000 + "``"])
def test_markdown_noise_cannot_make_it_quadratic(ts, text):
    import time

    start = time.monotonic()
    ts.strip_md(text)
    assert time.monotonic() - start < 5
