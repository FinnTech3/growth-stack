#!/usr/bin/env python3
"""text_stats.py [FILE|-] [--json] [--lines] [--top N] [--keyword PHRASE] [--flag WORD] [--wpm N]: measure a piece of writing.

Offline: reads one text or Markdown file (or stdin) and prints readability (formulas stated), word counts, the heading
outline, keyword and phrase frequency, repeated sentence openings, passive-voice and hedge-word counts (heuristics),
you-versus-we balance and reading time.
Exit 0: ok. 2: bad input. Standard library only.
"""
import argparse
import json
import re
import sys
from collections import Counter

STOP = set(["a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any", "are", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just", "me", "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "you", "your", "yours"])
HEDGES = ["might", "maybe", "perhaps", "possibly", "somewhat", "fairly", "quite", "rather", "probably", "arguably", "seems",
          "appears", "tends to", "sort of", "kind of", "a bit", "i think", "could"]
HYPE = ["cutting-edge", "world-class", "best-in-class", "state-of-the-art", "next-generation", "innovative", "robust", "synergy",
        "empower", "holistic", "turnkey", "industry-leading"]
PASSIVE = re.compile(r"\b(am|is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?(\w+ed|built|made|done|seen|given|shown|known|kept|sent|held|"
                     r"found|taken|written|chosen|driven|broken)\b", re.I)
WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")
YOU, WE = {"you", "your", "yours", "you're", "you'll", "you've"}, {"we", "our", "ours", "us", "we're", "we'll", "we've"}


def tokens(text):
  return [w.lower().replace("’", "'") for w in WORD.findall(text)]


def syllables(w):
  w = re.sub(r"[^a-z]", "", w.lower())
  n = len(re.findall(r"[aeiouy]+", w))
  if n > 1 and w.endswith("e") and not w.endswith("le"):
    n -= 1
  return max(1, n)


def strip_md(text, lines=False):
  """Return (headings, units): headings as (level, text); units are the prose sentences' source paragraphs."""
  text = re.sub(r"```.*?```|~~~.*?~~~", " ", text, flags=re.S)
  heads, paras, buf = [], [], []

  def flush():
    if buf:
      paras.append(" ".join(buf))
      buf.clear()

  for line in text.splitlines():
    m = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
    if m:
      flush()
      heads.append((len(m.group(1)), clean(m.group(2))))
    elif not line.strip() or re.fullmatch(r"([-*_]\s*){3,}|\|?[-:| ]+\|?", line.strip()):
      flush()
    elif re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
      flush()
      buf.append(clean(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", line)))
      flush()
    else:
      buf.append(clean(line.lstrip("> ")))
      if lines:
        flush()
  flush()
  return heads, [p for p in paras if p.strip()]


def clean(s):
  s = re.sub(r"!\[([^\]]{0,300})\]\([^)]{0,500}\)", r"\1", s)
  s = re.sub(r"\[([^\]]{1,300})\]\([^)]{0,500}\)", r"\1", s)
  s = re.sub(r"<[^>]{1,500}>|`", "", s)
  return re.sub(r"[*_]{1,3}(\S.{0,300}?\S|\S)[*_]{1,3}", r"\1", s).strip()


def analyse(text, top, keywords, flags, wpm, lines=False):
  heads, paras = strip_md(text, lines)
  sents = [s.strip() for p in paras for s in re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])", p) if s.strip()]
  joined = " ".join(paras)
  low = tokens(joined)
  nw, ns = len(low), max(1, len(sents))
  syl = sum(map(syllables, low))
  per_sentence, per_word = nw / ns, syl / max(1, nw)
  fre = 206.835 - 1.015 * per_sentence - 84.6 * per_word
  fk = 0.39 * per_sentence + 11.8 * per_word - 15.59
  band = next((b for lim, b in ((90, "very easy"), (80, "easy"), (70, "fairly easy"), (60, "plain English"), (50, "fairly difficult"),
                                (30, "difficult")) if fre >= lim), "very difficult")
  uni = Counter(w for w in low if w not in STOP and len(w) > 2 and not w.isdigit())
  grams = Counter()
  for p in paras:
    pw = tokens(p)
    for n in (2, 3):
      for i in range(len(pw) - n + 1):
        g = pw[i:i + n]
        if g[0] not in STOP and g[-1] not in STOP:
          grams[" ".join(g)] += 1
  openings = Counter(" ".join(s.lower().split()[:2]) for s in sents if len(s.split()) > 2)
  runs, run = [], 1
  for a, b in zip(sents, sents[1:]):
    run = run + 1 if a.split()[0].lower() == b.split()[0].lower() else 1
    if run == 3:
      runs.append(b.split()[0])
  body = joined.lower()
  head_text = " ".join(h[1].lower() for h in heads)
  first100 = " ".join(low[:100])
  kw = []
  for k in keywords:
    rx = r"\b" + re.escape(k.lower()) + r"\b"
    c = len(re.findall(rx, body))
    kw.append({"phrase": k, "count": c, "per_100_words": round(c * len(k.split()) * 100 / max(1, nw), 2),
               "in_headings": bool(re.search(rx, head_text)), "in_first_100_words": bool(re.search(rx, first100))})
  passive = [m.group(0) for m in PASSIVE.finditer(joined)]
  count = lambda lst: {w: n for w in lst if (n := len(re.findall(r"\b" + re.escape(w) + r"\b", body)))}
  return {
    "words": nw, "sentences": len(sents), "paragraphs": len(paras), "syllables": syl,
    "avg_words_per_sentence": round(per_sentence, 1), "long_sentences_over_25_words": sum(len(s.split()) > 25 for s in sents),
    "reading_time_seconds": round(nw / wpm * 60), "wpm_assumed": wpm,
    "readability": {"flesch_reading_ease": round(fre, 1), "band": band, "flesch_kincaid_grade": round(fk, 1),
                    "formulas": ["Flesch Reading Ease = 206.835 - 1.015 x (words / sentences) - 84.6 x (syllables / words)",
                                 "Flesch-Kincaid grade = 0.39 x (words / sentences) + 11.8 x (syllables / words) - 15.59"],
                    "note": "syllables are counted by a vowel-group heuristic, so treat scores as +/- a few points"},
    "outline": [{"level": h[0], "heading": h[1]} for h in heads], "top_words": uni.most_common(top), "top_phrases": [(g, c) for g, c in grams.most_common(top * 3) if c >= 2][:top],
    "keywords": kw, "repeated_openings": [(o, c) for o, c in openings.most_common(5) if c >= 3], "same_start_runs": runs[:5],
    "passive_heuristic": {"count": len(passive), "per_100_sentences": round(len(passive) * 100 / ns, 1), "examples": passive[:5]},
    "hedges_heuristic": count(HEDGES), "hype_heuristic": count(HYPE + flags),
    "you_we": {"you": sum(w in YOU for w in low), "we": sum(w in WE for w in low)},
  }


def render(r):
  rd = r["readability"]
  out = [f"Words {r['words']:,}  Sentences {r['sentences']}  Paragraphs {r['paragraphs']}  Avg {r['avg_words_per_sentence']} words/sentence"
         f"  Long (over 25 words) {r['long_sentences_over_25_words']}",
         f"Reading time about {r['reading_time_seconds'] // 60}m {r['reading_time_seconds'] % 60:02d}s at {r['wpm_assumed']} words/min (a rule of thumb)",
         f"Flesch Reading Ease {rd['flesch_reading_ease']} ({rd['band']}); Flesch-Kincaid grade {rd['flesch_kincaid_grade']}",
         *(f"  {f}" for f in rd["formulas"]), f"  {rd['note']}", ""]
  if r["outline"]:
    out += ["Outline"] + [f"  {'  ' * (h['level'] - 1)}h{h['level']} {h['heading']}" for h in r["outline"]] + [""]
  out += ["Top words: " + ", ".join(f"{w} ({c})" for w, c in r["top_words"]),
          "Top phrases: " + (", ".join(f"{w} ({c})" for w, c in r["top_phrases"]) or "none repeated")]
  for k in r["keywords"]:
    out.append(f"Keyword '{k['phrase']}': {k['count']}x, {k['per_100_words']} per 100 words, "
               f"in a heading: {'yes' if k['in_headings'] else 'no'}, in first 100 words: {'yes' if k['in_first_100_words'] else 'no'}")
  yw = r["you_we"]
  out += ["", f"You versus we: {yw['you']} you-words, {yw['we']} we-words (customer-first copy leans to you)",
          "Repeated openings (heuristic): " + (", ".join(f"'{o}' x{c}" for o, c in r["repeated_openings"]) or "none"),
          "Three sentences in a row starting the same way: " + (", ".join(r["same_start_runs"]) or "none"),
          f"Passive voice (heuristic): {r['passive_heuristic']['count']} ({r['passive_heuristic']['per_100_sentences']} per 100 sentences)"
          + "".join(f"\n    {e}" for e in r["passive_heuristic"]["examples"]),
          "Hedge words (heuristic): " + (", ".join(f"{w} x{n}" for w, n in r["hedges_heuristic"].items()) or "none"),
          "Hype or jargon words (heuristic): " + (", ".join(f"{w} x{n}" for w, n in r["hype_heuristic"].items()) or "none")]
  return "\n".join(out)


def main(argv=None):
  ap = argparse.ArgumentParser(prog="text_stats.py", description="Measure a text or Markdown file. Reads stdin when FILE is - or absent.")
  ap.add_argument("file", nargs="?", default="-")
  ap.add_argument("--json", action="store_true", help="print the full result as JSON")
  ap.add_argument("--top", type=int, default=10, help="how many top words and phrases to list (default 10)")
  ap.add_argument("--keyword", action="append", default=[], help="phrase to count (repeatable)")
  ap.add_argument("--flag", action="append", default=[], help="extra word to flag as hype or jargon (repeatable)")
  ap.add_argument("--lines", action="store_true", help="treat every line as its own sentence (for keyword lists)")
  ap.add_argument("--wpm", type=int, default=200, help="reading speed for the time estimate (default 200)")
  a = ap.parse_args(argv)
  if not 1 <= a.top <= 100 or a.wpm < 1:
    ap.error("--top must be 1 to 100 and --wpm must be positive")
  try:
    if a.file == "-":
      raw = sys.stdin.buffer.read(5_000_001)
    else:
      with open(a.file, "rb") as fh:
        raw = fh.read(5_000_001)
  except OSError as e:
    print(f"error: cannot read {a.file}: {e.strerror or e}", file=sys.stderr)
    return 2
  if len(raw) > 5_000_000 or b"\x00" in raw[:8192]:
    print("error: input is over 5 MB or is not text", file=sys.stderr)
    return 2
  text = raw.decode("utf-8-sig", "replace")
  if not re.search(r"[A-Za-z0-9]", text):
    print("error: no words found in the input", file=sys.stderr)
    return 2
  res = analyse(text, a.top, a.keyword, [f.lower() for f in a.flag], a.wpm, a.lines)
  print(json.dumps(res, indent=1) if a.json else render(res))
  return 0


if __name__ == "__main__":
  sys.stdout.reconfigure(errors="replace")
  sys.exit(main())
