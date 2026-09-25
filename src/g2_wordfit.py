"""G2 / S1 — engine-mode measurement on the founder's own reading.

Runs every file in data/g2-pieces/*.txt through three engine modes (rewrite /
substitute / hybrid) with the QC gate on and the density floor off, records
metrics to output/g2-results.json (resumable) and renders output/compare-transform.html.

Usage: python3 src/g2_wordfit.py [--only rewrite,substitute] [--redo]
"""

import html as html_mod
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store
from bakeoff import load_env
from build_digest import word_stats
from generate import CSS, POP_JS, generate_piece

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIECES = sorted((ROOT / "data" / "g2-pieces").glob("*.txt"))
RESULTS = ROOT / "output" / "g2-results.json"
PAGE = ROOT / "output" / "compare-transform.html"

VARIANTS = {
    "rewrite": ("transform.md", None),  # production posture incl. the D28 density request
    "substitute": ("transform-substitute.md",
                   "SUBSTITUTE ONLY: keep the source verbatim and swap an existing word or "
                   "short phrase for a candidate where the sense is identical and idiomatic; "
                   "skip every candidate without a natural slot"),
    "sentence": ("transform-sentence.md", None),  # request comes from generate.SENTENCE_REQUEST below
    "hybrid": ("transform-hybrid.md",
               "substitute where a plain word already carries the sense; rewrite at most "
               "one clause per paragraph to seat a word; never add information; skip every "
               "candidate without a natural slot"),
}


def menu(con) -> list:
    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    stats = word_stats(con)
    learning = [w["word"] for w in words if w.get("status", "learning") == "learning"]
    return sorted(learning, key=lambda w: stats.get(w, {"count": 0})["count"])


def text_to_html(text: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "\n".join(f"<p>{html_mod.escape(p)}</p>" for p in paras)


def ensure_item(con, path: pathlib.Path) -> dict:
    text = path.read_text().strip()
    item_id = f"g2:{path.stem}"
    store.upsert_item(con, {
        "id": item_id, "source": "user_text", "section": "g2-fixture", "url": item_id,
        "title": path.stem.split("-", 1)[1].replace("-", " ").title(),
        "author": None, "published": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_html": text_to_html(text), "categories": [], "license": "user-supplied",
        "notes": "G2 fixture"})
    con.commit()
    return con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()


def run(only: set, redo: bool) -> dict:
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() and not redo else {}
    con = store.connect()
    env = load_env()
    m = menu(con)
    for path in PIECES:
        item = ensure_item(con, path)
        src_words = len(re.sub(r"<[^>]+>", " ", item["content_html"]).split())
        for name, (wrapper, request) in VARIANTS.items():
            if only and name not in only:
                continue
            key = f"{path.stem}|{name}"
            if key in results:
                continue
            print(f"\n=== {path.stem} / {name} ===")
            try:
                from generate import SENTENCE_REQUEST
                p = generate_piece(con, item, wrapper, m, env, digest_date=None,
                                   density_floor=False,
                                   request=SENTENCE_REQUEST if name == "sentence" else request)
                con.commit()
            except Exception as exc:
                print(f"[error] {key}: {exc}")
                results[key] = {"piece": path.stem, "variant": name, "error": str(exc)}
                RESULTS.write_text(json.dumps(results, indent=1))
                continue
            results[key] = {
                "piece": path.stem, "variant": name, "title": p["title"], "body": p["body"],
                "marks": p["marks"], "words": p["word_count"], "source_words": src_words,
                "per_1000": round(1000 * p["marks"] / max(p["word_count"], 1), 1),
                "length_ratio": round(p["word_count"] / max(src_words, 1), 2),
                "words_used": p["words_used"], "qc_rejected": p["qc_rejected"],
                "invented_numbers": p["invented_numbers"], "attempts": p["attempts"],
                "model": p["model"],
            }
            RESULTS.write_text(json.dumps(results, indent=1))
    con.close()
    return results


def render(results: dict) -> None:
    con = store.connect()
    rows = []
    for name in VARIANTS:
        rs = [r for r in results.values() if r.get("variant") == name and "error" not in r]
        if not rs:
            continue
        rows.append(f"<tr><td><b>{name}</b></td><td>{len(rs)}</td>"
                    f"<td>{sum(r['marks'] for r in rs)}</td>"
                    f"<td>{round(1000 * sum(r['marks'] for r in rs) / max(sum(r['words'] for r in rs), 1), 1)}</td>"
                    f"<td>{sum(len(r['qc_rejected']) for r in rs)}</td>"
                    f"<td>{sum(len(r['invented_numbers']) for r in rs)}</td>"
                    f"<td>{round(sum(r['length_ratio'] for r in rs) / len(rs), 2)}</td></tr>")
    summary = ("<table class='m'><tr><th>variant</th><th>pieces</th><th>marks</th>"
               "<th>marks / 1,000 w</th><th>QC rejected</th><th>invented numbers</th>"
               "<th>length ratio</th></tr>" + "".join(rows) + "</table>")
    sections = []
    for path in PIECES:
        item = con.execute("SELECT * FROM items WHERE id=?", (f"g2:{path.stem}",)).fetchone()
        cols = [f"<div class='col'><div class='kicker'>source</div>{item['content_html']}</div>"]
        for name in VARIANTS:
            r = results.get(f"{path.stem}|{name}")
            if not r:
                continue
            if "error" in r:
                cols.append(f"<div class='col'><div class='kicker'>{name}</div><p>error: {html_mod.escape(r['error'])}</p></div>")
                continue
            meta = (f"{r['marks']} marks · {r['words']} w ({r['per_1000']}/1,000) · "
                    f"length ×{r['length_ratio']} · QC rejected: {', '.join(r['qc_rejected']) or 'none'} · "
                    f"invented numbers: {', '.join(map(str, r['invented_numbers'])) or 'none'} · "
                    f"attempts {r['attempts']}")
            cols.append(f"<div class='col'><div class='kicker'>{name}</div>"
                        f"<div class='meta'>{meta}</div>{r['body']}</div>")
        sections.append(f"<h2>{html_mod.escape(item['title'])}</h2><div class='row'>{''.join(cols)}</div>")
    con.close()
    extra = """
      body { padding: 1.5rem; } .sheet { max-width: none; }
      .row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.2rem; align-items: start; }
      .col { background: #fff; border: 1px solid #e5ddd0; border-radius: 8px; padding: 1rem; font-size: .95rem; }
      .col p { font-size: .95rem; }
      .edited { text-decoration: underline; text-decoration-color: #e8c96a; text-underline-offset: 3px; }
      .meta { font-family: -apple-system, sans-serif; font-size: .72rem; color: #6d675e; margin-bottom: .8rem; }
      table.m { border-collapse: collapse; font-family: -apple-system, sans-serif; font-size: .9rem; margin-bottom: 2rem; }
      table.m th, table.m td { border: 1px solid #ddd5c8; padding: .4rem .8rem; text-align: left; }
      h2 { margin-top: 2.5rem; }
    """
    PAGE.write_text(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>G2 — engine modes on the founder's own reading</title><style>{CSS}{extra}</style></head>
<body><div class="sheet"><h1>G2 — rewrite vs substitute vs hybrid</h1>
<p class="meta">{len(PIECES)} pieces the founder read · QC gate on · density floor off · gemini-3.1-flash-lite.
Tap a highlight for its definition. Rate each column: would you accept this as "your text with your words"?</p>
{summary}{''.join(sections)}</div><div id="pop"></div><script>{POP_JS}</script></body></html>""")
    print(f"[ok] {PAGE}")


if __name__ == "__main__":
    args = sys.argv[1:]
    only = set()
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    res = run(only, "--redo" in args)
    render(res)
