"""RetAIn PoC reading server — the D17 hybrid experience, replicating the app.

GET /            today's edition: word pills, the calendar pair fully rewritten,
                 then a taste-filtered headline menu from every source.
GET /read?id=    shell page with the "working the magic" moment; fetches the
                 rewrite from /api/rewrite and swaps it in.
GET /api/rewrite generates the piece on demand (validation + QC + D29 regen),
                 records it in the served ledger (digest_date = today), returns
                 JSON. Only clicked pieces count as servings — words served ==
                 words actually read.

Stdlib only. Binds 0.0.0.0 so a phone on the same network can read too.

Usage: python3 src/serve.py [port]     (default 8484)
"""

import html as html_mod
import json
import pathlib
import re
import subprocess
import sys
import threading
import urllib.parse
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store
from bakeoff import load_env
from build_digest import (SLOT_LABELS, WRAPPERS, daily_cap, due_pool, taste_ok,
                          word_stats)
from generate import CSS, POP_JS, attribution_for, generate_piece

ROOT = pathlib.Path(__file__).resolve().parent.parent
MENU_SIZE = 12
HEADLINES = [("global_voices", 6), ("stack_exchange", 4), ("nasa", 2)]

_refresh_lock = threading.Lock()
_refreshing = False
_gen_lock = threading.Lock()  # one generation at a time keeps caps honest

EXTRA_CSS = """
  .masthead { text-align: center; margin-bottom: 2rem; }
  .masthead .brand { font-family: -apple-system, sans-serif; font-weight: 700;
                     font-size: 1.05rem; letter-spacing: .18em; color: #8a6d3b; }
  .masthead .edition { font-family: -apple-system, sans-serif; font-size: .8rem;
                       color: #6d675e; margin-top: .3rem; }
  hr.sep { border: 0; border-top: 1px solid #ddd5c8; margin: 2.2rem 0; }
  .words { margin: 0 0 2.2rem; text-align: center; }
  .wcount { font-family: -apple-system, sans-serif; font-size: .72rem;
            color: #6d675e; margin-bottom: .7rem; letter-spacing: .04em; }
  .pill { display: inline-block; font-family: -apple-system, sans-serif;
          font-size: .78rem; color: #a49c8f; border: 1px solid #e5ddd0;
          border-radius: 999px; padding: .12em .65em; margin: .18em .12em; }
  .pill.served { color: #26221c; border-color: #e8c96a; cursor: pointer;
                 background: linear-gradient(transparent 55%, #ffe08a 55%); }
  .menu-h { font-family: -apple-system, sans-serif; font-size: .8rem;
            letter-spacing: .1em; text-transform: uppercase; color: #8a6d3b;
            margin: 2rem 0 .8rem; }
  .hl { display: block; text-decoration: none; color: inherit; background: #fff;
        border: 1px solid #e5ddd0; border-radius: 8px; padding: .8rem 1rem;
        margin: .5rem 0; }
  .hl:active { background: #faf4e6; }
  .hl .tag { font-family: -apple-system, sans-serif; font-size: .7rem;
             text-transform: uppercase; letter-spacing: .06em; color: #8a6d3b; }
  .hl .t { font-size: 1rem; line-height: 1.4; }
  .hl .done { color: #6d675e; font-family: -apple-system, sans-serif;
              font-size: .75rem; }
  .foot { text-align: center; font-family: -apple-system, sans-serif;
          color: #6d675e; font-size: .85rem; margin: 2.5rem 0 1rem; }
  .magic { text-align: center; margin: 4rem 0; font-family: -apple-system, sans-serif;
           color: #6d675e; }
  .magic .spin { font-size: 2rem; animation: pulse 1.2s ease-in-out infinite; }
  @keyframes pulse { 0%,100% { opacity: .3 } 50% { opacity: 1 } }
  .back { font-family: -apple-system, sans-serif; font-size: .85rem; }
  .back a { color: #8a6d3b; text-decoration: none; }
"""

def page(title: str, inner: str, extra_js: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_mod.escape(title)}</title><style>{CSS}{EXTRA_CSS}</style></head>
<body><div class="sheet">{inner}</div><div id="pop"></div>
<script>{POP_JS}{extra_js}</script></body></html>"""


def pills_html(con, today: str) -> str:
    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    served = set()
    for r in con.execute("SELECT words_used FROM generated_pieces WHERE digest_date=?",
                         (today,)):
        served |= set(json.loads(r["words_used"] or "[]"))
    pills = []
    for w in words:
        if w.get("status", "learning") == "archived":
            continue
        if w["word"] in served:
            pills.append(f'<span class="pill served" '
                         f'data-def="{html_mod.escape(w["definition"])}">'
                         f'{w["word"]}</span>')
        else:
            pills.append(f'<span class="pill">{w["word"]}</span>')
    return (f'<div class="words"><div class="wcount">{len(served)} of {len(pills)}'
            f' words served today — tap a highlighted pill for its meaning</div>'
            f'{"".join(pills)}</div>')


def ensure_calendar(con, env, today: str) -> list:
    """The calendar pair arrives pre-rewritten (D17). Fetch + generate if missing."""
    d = date.fromisoformat(today)
    mmdd = d.strftime("%m-%d")
    wanted = [("wikipedia_onthisday", f"%{mmdd}-{d.year}%", "fetch_onthisday.py"),
              ("internet_archive_newspapers", f"%{d.year - 100}-{mmdd}%",
               "fetch_century_news.py")]
    out = []
    for source, pattern, fetcher in wanted:
        item = con.execute("SELECT * FROM items WHERE source=? AND id LIKE ?",
                           (source, pattern)).fetchone()
        if item is None:
            try:
                subprocess.run([sys.executable, str(ROOT / "src" / fetcher)],
                               timeout=240, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as exc:
                print(f"[warn] {fetcher}: {exc}")
            item = con.execute("SELECT * FROM items WHERE source=? AND id LIKE ?",
                               (source, pattern)).fetchone()
        if item is None:
            print(f"[warn] no {source} item for {today}; slot skipped")
            continue
        piece = con.execute(
            "SELECT * FROM generated_pieces WHERE item_id=? AND digest_date=? "
            "ORDER BY id DESC", (item["id"], today)).fetchone()
        if piece is None:
            piece_d = generate_and_record(con, item, env, today)
            if piece_d is None:
                continue
            out.append((item, piece_d["title"], piece_d["body"]))
        else:
            out.append((item, piece["title"], piece["body_html"]))
    return out


def generate_and_record(con, item, env, today: str):
    """Menu from the due pool under D27 caps, then the full piece pipeline."""
    with _gen_lock:
        existing = con.execute(
            "SELECT * FROM generated_pieces WHERE item_id=? AND digest_date=? "
            "ORDER BY id DESC", (item["id"], today)).fetchone()
        if existing:
            return {"title": existing["title"], "body": existing["body_html"],
                    "words_used": json.loads(existing["words_used"] or "[]")}
        stats = word_stats(con)
        today_served = {}
        for r in con.execute(
                "SELECT words_used FROM generated_pieces WHERE digest_date=?",
                (today,)):
            for w in json.loads(r["words_used"] or "[]"):
                today_served[w] = today_served.get(w, 0) + 1
        pool = due_pool(con, today)
        menu = [w for w, c in pool
                if today_served.get(w, 0) < daily_cap(stats.get(w, {}).get("count", 0))
                ][:MENU_SIZE]
        if not menu:
            menu = [w for w, _ in pool][:MENU_SIZE]
        try:
            piece = generate_piece(con, item, WRAPPERS.get(item["source"], "news.md"),
                                   menu, env, digest_date=today)
            con.commit()
            return piece
        except Exception as exc:
            print(f"[error] generation failed for {item['id']}: {exc}")
            return None


def headline_menu(con, today: str) -> str:
    config = json.loads((ROOT / "config" / "sources.json").read_text())
    skip = config["global_voices"].get("skip_categories", [])
    read_today = {r["item_id"] for r in con.execute(
        "SELECT DISTINCT item_id FROM generated_pieces WHERE digest_date=?", (today,))}
    served_before = {r["item_id"] for r in con.execute(
        "SELECT DISTINCT item_id FROM generated_pieces WHERE digest_date IS NOT NULL "
        "AND digest_date != ?", (today,))}
    cards = []
    for source, n in HEADLINES:
        order = "published DESC" if source == "global_voices" else "RANDOM()"
        got = 0
        for r in con.execute(f"SELECT * FROM items WHERE source=? AND "
                             f"status IN ('fetched','selected') ORDER BY {order}",
                             (source,)):
            if r["id"] in served_before:
                continue
            if source == "global_voices" and not taste_ok(r, skip):
                continue
            qid = urllib.parse.quote(r["id"], safe="")
            tag = SLOT_LABELS.get(source, source)
            if source == "stack_exchange":
                tag += f" · {r['section']}"
            done = ' <span class="done">✓ read</span>' if r["id"] in read_today else ""
            cards.append(f'<a class="hl" href="/read?id={qid}">'
                         f'<div class="tag">{tag}</div>'
                         f'<div class="t">{html_mod.escape(r["title"] or "")}{done}'
                         f'</div></a>')
            got += 1
            if got == n:
                break
    return "\n".join(cards)


def edition_page() -> str:
    today = date.today().isoformat()
    con = store.connect()
    env = load_env()
    maybe_refresh_pantry(con)
    calendar = ensure_calendar(con, env, today)
    edition_no = con.execute(
        "SELECT COUNT(DISTINCT digest_date) FROM generated_pieces "
        "WHERE digest_date IS NOT NULL AND digest_date <= ?", (today,)).fetchone()[0] or 1
    d = date.fromisoformat(today)
    sections = []
    for item, title, body in calendar:
        sections.append(f"""
  <div class="kicker">{SLOT_LABELS.get(item['source'], 'Today')}</div>
  <h1>{html_mod.escape(title)}</h1>
  {body}
  <div class="attrib">{attribution_for(item)}</div>
  <hr class="sep">""")
    inner = f"""
  <div class="masthead">
    <div class="brand">RETAIN</div>
    <div class="edition">Edition {edition_no} · {d.strftime('%A, %B %d, %Y')}</div>
  </div>
  {pills_html(con, today)}
  {''.join(sections)}
  <div class="menu-h">Today's menu — tap a headline and we'll rewrite it for you</div>
  {headline_menu(con, today)}
  <div class="foot">The more you read, the more words we serve.</div>"""
    con.close()
    return page(f"RetAIn · Edition {edition_no}", inner)


def read_shell(item_id: str) -> str:
    qid = urllib.parse.quote(item_id, safe="")
    inner = f"""
  <div class="back"><a href="/">&larr; Back to today's edition</a></div>
  <div class="magic" id="magic">
    <div class="spin">✦</div>
    <p>Working the magic — rewriting this just for you...</p>
  </div>
  <div id="piece"></div>"""
    js = f"""
  fetch('/api/rewrite?id={qid}').then(r => r.json()).then(p => {{
    document.getElementById('magic').style.display = 'none';
    if (p.error) {{
      document.getElementById('piece').innerHTML = '<p>' + p.error + '</p>';
      return;
    }}
    document.getElementById('piece').innerHTML =
      '<div class="kicker">' + p.label + '</div><h1>' + p.title + '</h1>' +
      p.body + '<div class="attrib">' + p.attrib + '</div>' +
      '<div class="foot"><a style="color:#8a6d3b" href="/">&larr; Back for more</a></div>';
    document.querySelectorAll('#piece mark').forEach(m => {{
      m.addEventListener('click', e => {{
        e.stopPropagation();
        const pop = document.getElementById('pop');
        pop.innerHTML = '<b>' + m.textContent.trim() + '</b> — ' + m.dataset.def;
        pop.style.display = 'block';
        const r = m.getBoundingClientRect();
        pop.style.left = Math.min(r.left + window.scrollX, window.innerWidth - 300) + 'px';
        pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
      }});
    }});
  }});"""
    return page("RetAIn · rewriting...", inner, js)


def api_rewrite(item_id: str) -> dict:
    today = date.today().isoformat()
    con = store.connect()
    item = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        con.close()
        return {"error": "That piece seems to have wandered off. Go back and pick another."}
    piece = generate_and_record(con, item, load_env(), today)
    con.close()
    if piece is None:
        return {"error": "The rewrite hit a snag. Go back and try again — or pick another."}
    return {"title": piece["title"], "body": piece["body"],
            "label": SLOT_LABELS.get(item["source"], "Today's Pick"),
            "attrib": attribution_for(item)}


def maybe_refresh_pantry(con) -> None:
    """Background refresh when the newest news item is stale (>20h)."""
    global _refreshing
    newest = con.execute("SELECT MAX(fetched_at) FROM items "
                         "WHERE source='global_voices'").fetchone()[0]
    if newest and (datetime.now(timezone.utc)
                   - datetime.fromisoformat(newest)).total_seconds() < 20 * 3600:
        return
    with _refresh_lock:
        if _refreshing:
            return
        _refreshing = True

    def work():
        global _refreshing
        for script in ["fetch_rss.py", "fetch_stackexchange.py"]:
            try:
                subprocess.run([sys.executable, str(ROOT / "src" / script)],
                               timeout=240, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        _refreshing = False
        print("[fetch] background pantry refresh done")

    threading.Thread(target=work, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[http] {args[0] if args else ''}")

    def send_page(self, body: str, content_type: str = "text/html") -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(url.query)
        try:
            if url.path == "/":
                self.send_page(edition_page())
            elif url.path == "/read" and params.get("id"):
                self.send_page(read_shell(params["id"][0]))
            elif url.path == "/api/rewrite" and params.get("id"):
                self.send_page(json.dumps(api_rewrite(params["id"][0])),
                               "application/json")
            else:
                self.send_response(404)
                self.end_headers()
        except BrokenPipeError:
            pass
        except Exception as exc:
            print(f"[error] {url.path}: {exc}")
            try:
                self.send_response(500)
                self.end_headers()
            except Exception:
                pass


def run() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8484
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"[ok] RetAIn reading server: http://localhost:{port}")
    print(f"[ok] phone on same wifi: http://<this-mac's-LAN-IP>:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
