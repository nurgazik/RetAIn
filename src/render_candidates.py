"""Render the candidate pool as a browsable HTML page (a window into the 'pantry').

Lists viable (taste-filtered) candidates with links to the originals, newest first,
plus a collapsed section showing what the taste filter excluded and why.

Usage: python3 src/render_candidates.py   -> output/candidates.html
"""

import html
import json
import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "candidates.html"

STYLE = """
  body { font-family: -apple-system, 'Helvetica Neue', sans-serif; background: #faf8f4;
         color: #26221c; margin: 0; padding: 2rem 1.25rem 4rem; line-height: 1.5; }
  .sheet { max-width: 780px; margin: 0 auto; }
  h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 2rem; }
  .item { padding: .65rem .8rem; border-bottom: 1px solid #e8e1d4; }
  .item a { color: #26221c; text-decoration: none; font-weight: 600; }
  .item a:hover { color: #8a6d3b; }
  .meta { font-size: .78rem; color: #6d675e; margin-top: .15rem; }
  .badge { display: inline-block; padding: .05rem .45rem; border-radius: 99px;
           font-size: .72rem; margin-right: .35rem; background: #eee5d4; color: #6d5426; }
  .badge.selected { background: #2f6b3a; color: #fff; }
  .badge.rejected { background: #b3543e; color: #fff; }
  details { margin-top: 1.5rem; } summary { cursor: pointer; font-weight: 600; }
"""


def render() -> None:
    skip = set(json.loads((ROOT / "config" / "sources.json").read_text())
               ["global_voices"]["skip_categories"])
    con = store.connect()
    rows = con.execute(
        "SELECT * FROM items WHERE source='global_voices' ORDER BY published DESC"
    ).fetchall()

    viable, filtered = [], []
    for r in rows:
        cats = set(json.loads(r["categories"]))
        if r["status"] == "rejected" or (cats & skip):
            filtered.append((r, sorted(cats & skip)))
        else:
            viable.append(r)

    def item_html(r, hit=None):
        cats = ", ".join(json.loads(r["categories"])[:6])
        badge = ""
        if r["status"] == "selected":
            badge = '<span class="badge selected">served/selected</span>'
        if hit:
            badge = f'<span class="badge rejected">filtered: {html.escape(", ".join(hit))}</span>'
        return (f'<div class="item">{badge}<a href="{html.escape(r["url"])}">'
                f'{html.escape(r["title"])}</a>'
                f'<div class="meta">{r["published"][:10]} · [{r["section"]}] · '
                f'{html.escape(r["author"] or "")} · {html.escape(cats)}</div></div>')

    body = "".join(item_html(r) for r in viable)
    filtered_body = "".join(item_html(r, hit) for r, hit in filtered)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetAIn · Candidate pool</title><style>{STYLE}</style></head>
<body><div class="sheet">
<h1>Candidate pool — {date.today().isoformat()}</h1>
<p>{len(viable)} viable candidates (links go to the originals on Global Voices).</p>
{body}
<details><summary>Taste-filtered out ({len(filtered)})</summary>{filtered_body}</details>
</div></body></html>""")
    print(f"wrote {OUT} ({len(viable)} viable, {len(filtered)} filtered)")


if __name__ == "__main__":
    render()
