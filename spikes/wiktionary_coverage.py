"""Wiktionary coverage spike (2026-09-27): can Wiktionary (kaikki.org's Wiktextract English
extraction, CC BY-SA 4.0) supply word cards for the founder's list? Measures, per word: found
directly / via its lemma (form_of) / not found; IPA (US/UK); audio; senses before and after
dropping archaic/obsolete/rare/dated ones; example vs. quotation counts; register tags.
Reads data/service.db read-only and data/dictionary/*.jsonl (gitignored; download date in the
filename). Caches matched entries to output/wiktionary_entries.json so reruns skip the 3 GB scan.
Writes output/wiktionary_coverage.json and output/wiktionary_cards.html (sample cards).
Run: python3 spikes/wiktionary_coverage.py [dump.jsonl]"""
import html
import json
import pathlib
import random
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
CACHE = OUT / "wiktionary_entries.json"
DROP = {"archaic", "obsolete", "rare", "dated"}
REGISTER = {"formal", "informal", "colloquial", "slang", "literary", "derogatory", "pejorative",
            "humorous", "euphemistic", "vulgar", "offensive", "figuratively", "idiomatic", "jargon"}
US, UK = {"US", "General-American"}, {"UK", "Received-Pronunciation"}


def db_words() -> list:
    con = sqlite3.connect(f"file:{ROOT / 'data' / 'service.db'}?mode=ro", uri=True)
    return sorted(r[0] for r in con.execute("SELECT DISTINCT word FROM words"))


def scan(dump: pathlib.Path, wanted: set) -> dict:
    """One pass over the dump: every English entry whose headword is in `wanted` (lowercased)."""
    found = {}
    with dump.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i % 200_000 == 0:
                print(f"  scanned {i:,} entries", file=sys.stderr)
            e = json.loads(line)
            key = e.get("word", "").lower()
            if key in wanted and e.get("lang_code", "en") == "en":
                found.setdefault(key, []).append(e)
    return found


def load_entries(dump: pathlib.Path, words: list) -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    entries = scan(dump, set(words))
    lemmas = {f["word"].lower() for es in entries.values() for e in es for s in e.get("senses", [])
              for f in pointers(s)} - set(entries)
    if lemmas:  # second pass only for lemmas the first pass didn't already pick up
        print(f"  second pass for {len(lemmas)} lemmas", file=sys.stderr)
        entries.update(scan(dump, lemmas))
    OUT.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(entries))
    return entries


def pointers(s: dict) -> list:
    """Where a sense redirects: inflection (form_of: ran → run) or alternative spelling (alt_of)."""
    return s.get("form_of", []) + s.get("alt_of", [])


def is_form_only(es: list) -> bool:
    return all(pointers(s) or "form-of" in s.get("tags", []) for e in es for s in e.get("senses", []))


def measure(word: str, entries: dict) -> dict:
    es, via = entries.get(word, []), None
    if es and is_form_only(es):  # "ran" → "run": the card belongs to the lemma
        lemma = next((f["word"].lower() for e in es for s in e["senses"] for f in pointers(s)), None)
        if lemma:
            es, via = entries.get(lemma, []), lemma
    if not es:
        return {"word": word, "status": "not found"}
    senses = [(e["pos"], s) for e in es for s in e.get("senses", []) if s.get("glosses")
              and not pointers(s) and "form-of" not in s.get("tags", [])]
    kept = [(p, s) for p, s in senses if not DROP & set(s.get("tags", []))]
    exs = [x for _, s in kept for x in s.get("examples", [])]
    quotes = [x for x in exs if x.get("type") == "quotation" or x.get("ref")]
    sounds = [x for e in es for x in e.get("sounds", [])]
    ipa = [x for x in sounds if x.get("ipa")]
    return {
        "word": word, "status": "via lemma" if via else "direct", "lemma": via or word,
        "pos": sorted({p for p, _ in kept}),
        "ipa_any": bool(ipa), "ipa_us": any(US & set(x.get("tags", [])) for x in ipa),
        "ipa_uk": any(UK & set(x.get("tags", [])) for x in ipa),
        "audio": any(x.get("ogg_url") or x.get("mp3_url") for x in sounds),
        "senses_all": len(senses), "senses_kept": len(kept),
        "senses_with_example": sum(1 for _, s in kept if s.get("examples")),
        "usage_examples": len(exs) - len(quotes), "quotations": len(quotes),
        "register": sorted({t for _, s in kept for t in s.get("tags", []) if t in REGISTER}),
        "card": {"ipa": [x["ipa"] for x in ipa][:2],
                 "senses": [{"pos": p, "gloss": s["glosses"][-1], "tags": s.get("tags", []),
                             "examples": [x["text"] for x in s.get("examples", [])
                                          if not (x.get("type") == "quotation" or x.get("ref"))][:2]}
                            for p, s in kept]},
    }


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "0/0"


def report(rows: list) -> None:
    n, hit = len(rows), [r for r in rows if r["status"] != "not found"]
    k = sorted(r["senses_kept"] for r in hit)
    print(f"\nn = {n} distinct words (data/service.db)\n")
    print(f"found directly      {pct(sum(r['status'] == 'direct' for r in rows), n)}")
    print(f"found via lemma     {pct(sum(r['status'] == 'via lemma' for r in rows), n)}")
    print(f"not found           {pct(n - len(hit), n)}")
    h = len(hit)
    print(f"\nof the {h} found:")
    for label, key in (("IPA (any)", "ipa_any"), ("IPA US", "ipa_us"), ("IPA UK", "ipa_uk"), ("audio", "audio")):
        print(f"  {label:<18}{pct(sum(r[key] for r in hit), h)}")
    print(f"  senses, all       median {sorted(r['senses_all'] for r in hit)[h // 2]}, "
          f"max {max(r['senses_all'] for r in hit)}")
    print(f"  senses, kept      median {k[h // 2]}, max {k[-1]}, words with >5: {sum(x > 5 for x in k)}")
    print(f"  ≥1 usage example  {pct(sum(r['usage_examples'] > 0 for r in hit), h)}")
    print(f"  only quotations   {pct(sum(r['usage_examples'] == 0 and r['quotations'] > 0 for r in hit), h)}")
    print(f"  no examples       {pct(sum(r['usage_examples'] + r['quotations'] == 0 for r in hit), h)}")
    print(f"  register tag      {pct(sum(bool(r['register']) for r in hit), h)}")
    miss = [r["word"] for r in rows if r["status"] == "not found"]
    print(f"\nnot found: {', '.join(miss) or '—'}")
    lem = [f"{r['word']}→{r['lemma']}" for r in rows if r["status"] == "via lemma"]
    print(f"via lemma: {', '.join(lem) or '—'}")


CSS = """:root{--bg:#fafaf8;--card:#fff;--ink:#1d1d1f;--mute:#6e6e73;--line:#e5e5ea;--acc:#b4541a}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--card:#212121;--ink:#f2f2f2;--mute:#a1a1a6;--line:#333;--acc:#f0a064}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,system-ui,sans-serif}
main{max-width:680px;margin:0 auto;padding:24px 16px}.card{background:var(--card);border:1px solid var(--line);
border-radius:12px;padding:16px 20px;margin:16px 0}h2{margin:0}.ipa{color:var(--mute);font-size:15px}
ol{padding-left:20px}li{margin:8px 0}.pos{color:var(--acc);font-size:13px;text-transform:uppercase}
.tag{color:var(--mute);font-size:13px}.ex{color:var(--mute);font-style:italic;margin:2px 0 0}
.src{color:var(--mute);font-size:13px}"""


def cards_html(rows: list) -> str:
    hit = [r for r in rows if r["status"] != "not found"]
    by = sorted(hit, key=lambda r: r["senses_kept"])  # fewest, most, and three in between
    pick = [by[0], by[-1]] + random.Random(7).sample(by[1:-1], 3)
    out = []
    for r in pick:
        items = "".join(
            f'<li><span class="pos">{html.escape(s["pos"])}</span> '
            f'{"<span class=tag>(" + html.escape(", ".join(s["tags"])) + ")</span> " if s["tags"] else ""}'
            f'{html.escape(s["gloss"])}'
            + "".join(f'<p class="ex">“{html.escape(x)}”</p>' for x in s["examples"]) + "</li>"
            for s in r["card"]["senses"])
        via = f' <span class="tag">(from “{r["word"]}”)</span>' if r["status"] == "via lemma" else ""
        out.append(f'<div class="card"><h2>{html.escape(r["lemma"])}{via}</h2>'
                   f'<div class="ipa">{html.escape("  ".join(r["card"]["ipa"])) or "no IPA"} · '
                   f'{r["senses_kept"]} of {r["senses_all"]} senses kept</div><ol>{items}</ol></div>')
    return (f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            f'<title>Wiktionary Sample Cards</title><style>{CSS}</style><main><h1>Wiktionary sample cards</h1>'
            f'<p class="src">Raw Wiktionary data, archaic/obsolete/rare/dated senses removed, quotations hidden. '
            f'Source: <a href="https://en.wiktionary.org">Wiktionary</a>, CC BY-SA 4.0.</p>{"".join(out)}</main>')


def main(dump: pathlib.Path) -> None:
    words = db_words()
    entries = load_entries(dump, words)
    rows = [measure(w, entries) for w in words]
    report(rows)
    (OUT / "wiktionary_coverage.json").write_text(json.dumps(rows, indent=1))
    (OUT / "wiktionary_cards.html").write_text(cards_html(rows))
    print(f"\nwrote {OUT / 'wiktionary_coverage.json'} and {OUT / 'wiktionary_cards.html'}")


if __name__ == "__main__":
    default = sorted((ROOT / "data" / "dictionary").glob("*.jsonl"))[-1:]
    main(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default[0])
