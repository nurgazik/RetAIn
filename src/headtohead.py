"""Head-to-head: claude-haiku-4-5 vs gemini-3.1-flash-lite (D5 challenge).

3 articles x 3 wrappers x 2 models, identical word menus per article.
Writes output/headtohead/h2h.html (all six pieces, labeled) + results.json.

Usage: python3 src/headtohead.py
"""

import html as html_mod
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store
from bakeoff import load_env, parse_output, call_anthropic, call_gemini

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "headtohead"

MODELS = [
    {"name": "claude-haiku-4-5", "call": call_anthropic, "key": "ANTHROPIC_API_KEY",
     "in": 1.00, "out": 5.00},
    {"name": "gemini-3.1-flash-lite", "call": call_gemini, "key": "GEMINI_API_KEY",
     "in": 0.25, "out": 1.50},
]

ROUNDS = [
    {"label": "A-news", "item_like": "%Dimash%", "wrapper": "news.md",
     "words": ["galvanize", "zeitgeist", "ubiquitous", "scathing", "affable",
               "gravitas", "eschew", "windfall", "coalesce", "adamant"]},
    {"label": "B-onthisday", "item_like": "%onthisday-07-25%", "wrapper": "onthisday.md",
     "words": ["quagmire", "impasse", "panacea", "disparage", "corroborate",
               "tenuous", "linchpin", "astute", "squander", "belabor"]},
    {"label": "C-century", "item_like": "%cric_005489%", "wrapper": "century.md",
     "words": ["shrewd", "placate", "flounder", "acumen", "convoluted",
               "assuage", "perfunctory", "candor", "conundrum", "deft"]},
]


def build_user_prompt(item, words_defs: dict) -> str:
    word_list = "\n".join(f"- {w}: {d}" for w, d in words_defs.items())
    text = re.sub(r"<[^>]+>", " ", item["content_html"])
    text = html_mod.unescape(re.sub(r"[ \t]+", " ", text)).strip()
    return (f"CANDIDATE TARGET WORDS (a menu — embed only the ones that fit naturally):\n"
            f"{word_list}\n\nSOURCE (title: {item['title']}):\n\n{text}")


def run() -> None:
    env = load_env()
    con = store.connect()
    all_words = {w["word"]: w["definition"]
                 for w in json.loads((ROOT / "data" / "words.json").read_text())["words"]}
    core = (ROOT / "prompts" / "core.md").read_text()

    results, sections = [], []
    for rnd in ROUNDS:
        item = con.execute("SELECT * FROM items WHERE id LIKE ? OR title LIKE ?",
                           (rnd["item_like"], rnd["item_like"])).fetchone()
        if not item:
            print(f"[error] no item for {rnd['label']}")
            continue
        system = core + "\n\n---\n\n" + (ROOT / "prompts" / rnd["wrapper"]).read_text()
        user = build_user_prompt(item, {w: all_words[w] for w in rnd["words"]})

        for spec in MODELS:
            t0 = time.monotonic()
            try:
                r = spec["call"](spec["name"], system, user, env[spec["key"]])
                elapsed = round(time.monotonic() - t0, 1)
                p = parse_output(r["text"])
                cost = round(r["tokens_in"] / 1e6 * spec["in"]
                             + r["tokens_out"] / 1e6 * spec["out"], 5)
                results.append({"round": rnd["label"], "model": spec["name"],
                                "seconds": elapsed, "cost_usd": cost,
                                "tokens_out": r["tokens_out"], "marks": p["marks"],
                                "word_count": p["word_count"],
                                "words_used": p["words_used"], "title": p["title"]})
                sections.append(
                    f'<section><div class="label">{rnd["label"]} · {spec["name"]} · '
                    f'{elapsed}s · ${cost}</div>'
                    f'<h2>{html_mod.escape(p["title"])}</h2>{p["body"]}</section>')
                print(f"{rnd['label']} / {spec['name']}: {p['marks']} marks, "
                      f"{elapsed}s, ${cost}")
            except Exception as exc:
                print(f"{rnd['label']} / {spec['name']}: FAILED — {exc}")
                results.append({"round": rnd["label"], "model": spec["name"],
                                "error": str(exc)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "h2h.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetAIn · Head-to-head</title><style>
  body {{ font-family: Georgia, serif; background: #faf8f4; color: #26221c;
         margin: 0; padding: 2rem 1.25rem 4rem; line-height: 1.65; }}
  .sheet {{ max-width: 640px; margin: 0 auto; }}
  section {{ border-top: 3px solid #8a6d3b; margin-top: 2.5rem; padding-top: .5rem; }}
  .label {{ font-family: -apple-system, sans-serif; font-size: .8rem; font-weight: 700;
            letter-spacing: .06em; color: #8a6d3b; }}
  h2 {{ font-size: 1.3rem; line-height: 1.3; }}
  p {{ margin: 0 0 1.1rem; font-size: 1.05rem; }}
  mark {{ background: linear-gradient(transparent 55%, #ffe08a 55%); padding: 0 .1em; }}
</style></head><body><div class="sheet">
<h1 style="font-family:-apple-system,sans-serif;font-size:1.3rem">
Head-to-head: Haiku 4.5 vs Gemini 3.1 Flash-Lite</h1>
{''.join(sections)}
</div></body></html>""")
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUT_DIR}/h2h.html and results.json")


if __name__ == "__main__":
    run()
