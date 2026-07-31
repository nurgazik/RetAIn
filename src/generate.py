"""Generate a digest piece from a pantry item via the production model (D5: Haiku).

Builds the prompt (core + wrapper + candidate words), calls claude-haiku-4-5,
records the result in generated_pieces, and renders reader HTML with
tap-to-reveal word highlights.

Usage:
  python3 src/generate.py <item_id_substring> <wrapper.md> <word1,word2,...> [out.html]
"""

import html as html_mod
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store
from bakeoff import load_env, parse_output, call_anthropic, call_gemini

ROOT = pathlib.Path(__file__).resolve().parent.parent

# D5 (2026-07-26): Flash-Lite primary, Haiku fallback on provider failure
PRIMARY = {"model": "gemini-3.1-flash-lite", "call": call_gemini, "key": "GEMINI_API_KEY"}
FALLBACK = {"model": "claude-haiku-4-5", "call": call_anthropic, "key": "ANTHROPIC_API_KEY"}

CSS = """
  body { font-family: Georgia, 'Times New Roman', serif; background: #faf8f4;
         color: #26221c; margin: 0; padding: 2rem 1.25rem 4rem; line-height: 1.65; }
  .sheet { max-width: 640px; margin: 0 auto; }
  .kicker { font-family: -apple-system, sans-serif; font-size: .75rem;
            letter-spacing: .12em; text-transform: uppercase; color: #8a6d3b;
            margin-bottom: .5rem; }
  h1 { font-size: 1.7rem; line-height: 1.25; margin: 0 0 1.25rem; }
  p { margin: 0 0 1.1rem; font-size: 1.06rem; }
  mark { background: linear-gradient(transparent 55%, #ffe08a 55%);
         padding: 0 .1em; cursor: pointer; border-radius: 2px; }
  #pop { position: absolute; display: none; z-index: 10; max-width: 280px;
         padding: .6rem .8rem; background: #26221c; color: #faf8f4;
         border-radius: 8px; font-family: -apple-system, sans-serif;
         font-size: .85rem; line-height: 1.45; }
  #pop b { color: #ffd76e; }
  .attrib { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd5c8;
            font-family: -apple-system, sans-serif; font-size: .8rem; color: #6d675e; }
  .attrib a { color: #8a6d3b; }
"""

POP_JS = """
  const pop = document.getElementById('pop');
  document.querySelectorAll('mark').forEach(m => {
    m.addEventListener('click', e => {
      e.stopPropagation();
      pop.innerHTML = '<b>' + m.textContent.trim() + '</b> — ' + m.dataset.def;
      pop.style.display = 'block';
      const r = m.getBoundingClientRect();
      pop.style.left = Math.min(r.left + window.scrollX, window.innerWidth - 300) + 'px';
      pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
    });
  });
  document.addEventListener('click', () => { pop.style.display = 'none'; });
"""


def call_model(system: str, user: str, env: dict) -> tuple:
    """Primary model with automatic fallback (D5). Returns (text, model_name)."""
    try:
        r = PRIMARY["call"](PRIMARY["model"], system, user, env[PRIMARY["key"]])
        return r["text"], PRIMARY["model"]
    except Exception as exc:
        print(f"[warn] {PRIMARY['model']} failed ({exc}); falling back to {FALLBACK['model']}")
        r = FALLBACK["call"](FALLBACK["model"], system, user, env[FALLBACK["key"]])
        return r["text"], FALLBACK["model"]


def annotate_marks(body: str, defs: dict) -> str:
    """Attach data-def tooltips to <mark>word</mark> tags."""
    def repl(m):
        word = m.group(1)
        stem = re.sub(r"<[^>]+>", "", word).lower()
        definition = next((d for w, d in defs.items() if stem.startswith(w[:6].lower())), "")
        return f'<mark data-def="{html_mod.escape(definition)}">{word}</mark>'
    return re.sub(r"<mark>(.*?)</mark>", repl, body, flags=re.S)


def render(kicker: str, title: str, body: str, attrib: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetAIn · {html_mod.escape(title)}</title><style>{CSS}</style></head>
<body><div class="sheet">
  <div class="kicker">{html_mod.escape(kicker)}</div>
  <h1>{html_mod.escape(title)}</h1>
  {body}
  <div class="attrib">{attrib}</div>
</div><div id="pop"></div><script>{POP_JS}</script></body></html>"""


def attribution_for(item) -> str:
    url = html_mod.escape(item["url"])
    if item["source"] == "wikipedia_onthisday":
        return (f'Adapted from <a href="{url}">Wikipedia\'s On This Day</a> '
                f"(CC BY-SA 4.0); this adaptation is likewise shared under CC BY-SA.")
    if item["source"] == "chronicling_america":
        return (f'Source: {html_mod.escape(item["author"])}, {item["published"]} — '
                f'public domain, via <a href="{url}">Chronicling America</a> '
                f"(Library of Congress).")
    return (f'Adapted from "<a href="{url}">{html_mod.escape(item["title"])}</a>" '
            f'by {html_mod.escape(item["author"] or "unknown")} ({item["license"]}).')


def run() -> None:
    item_like, wrapper_file, words_csv = sys.argv[1], sys.argv[2], sys.argv[3]
    out_path = ROOT / "output" / (sys.argv[4] if len(sys.argv) > 4
                                  else f"{item_like}.html")

    con = store.connect()
    item = con.execute("SELECT * FROM items WHERE id LIKE ?",
                       (f"%{item_like}%",)).fetchone()
    if not item:
        print(f"[error] no pantry item matching '{item_like}'")
        return

    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    chosen = [w.strip() for w in words_csv.split(",")]
    defs = {w["word"]: w["definition"] for w in words if w["word"] in chosen}
    word_list = "\n".join(f"- {w}: {d}" for w, d in defs.items())

    system = ((ROOT / "prompts" / "core.md").read_text() + "\n\n---\n\n"
              + (ROOT / "prompts" / wrapper_file).read_text())
    source_text = re.sub(r"<[^>]+>", " ", item["content_html"])
    source_text = html_mod.unescape(re.sub(r"[ \t]+", " ", source_text)).strip()
    user = (f"CANDIDATE TARGET WORDS (use 3-6, only where genuinely idiomatic):\n"
            f"{word_list}\n\nSOURCE (title: {item['title']}):\n\n{source_text}")

    env = load_env()
    print(f"[gen] {item['id']} via {PRIMARY['model']}...")
    raw, model_used = call_model(system, user, env)
    parsed = parse_output(raw)
    if parsed["marks"] == 0:  # one validation retry, mirroring pipeline QC
        print("[gen] no marks on attempt 1, retrying once...")
        raw, model_used = call_model(system, user, env)
        parsed = parse_output(raw)

    title = re.sub(r"[*#]+", "", parsed["title"]).strip()
    body = annotate_marks(parsed["body"], defs)

    con.execute(
        "INSERT INTO generated_pieces (item_id, created_at, model, words_used, title, body_html) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (item["id"], datetime.now(timezone.utc).isoformat(), model_used,
         json.dumps([w for w in re.split(r"[\s,•-]+", parsed["words_used"]) if w]),
         title, body))
    store.set_status(con, item["id"], "selected",
                     f"generated {datetime.now(timezone.utc).date()}")

    kicker = f"Daily Digest · {datetime.now(timezone.utc).strftime('%B %d')}"
    out_path.write_text(render(kicker, title, body, attribution_for(item)))
    print(f"[ok] {parsed['marks']} words embedded, {parsed['word_count']} words long")
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    run()
