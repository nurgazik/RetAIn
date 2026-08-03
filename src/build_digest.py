"""Daily digest builder: one command -> today's edition as a single HTML page.

Assembles the PoC reading experience (PRD D21/D22, docs/architecture.md):
calendar pair + 2 picks, words scheduled by expanding intervals with D27
stage-based daily caps, finite edition with a "you're caught up" ending and a
browse-the-pantry menu for tomorrow (D17: founder picks beat the algorithm).

Idempotent per day: re-running reuses today's already-generated pieces and
rewrites the same file. A failed slot degrades to a smaller edition — the
digest itself can never fail (D15).

Usage: python3 src/build_digest.py [--force] [--date YYYY-MM-DD]
"""

import json
import pathlib
import re
import subprocess
import sys
from datetime import date, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store
from bakeoff import load_env
from generate import CSS, POP_JS, attribution_for, generate_piece

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "digest"

# days until a word is due again, indexed by digest servings so far (D27:
# dense early exposure, expanding later)
INTERVALS = [1, 1, 2, 4, 7, 12, 20]
MENU_SIZE = 12

WRAPPERS = {"wikipedia_onthisday": "onthisday.md",
            "internet_archive_newspapers": "century.md",
            "stack_exchange": "qa.md"}
SLOT_LABELS = {"wikipedia_onthisday": "On This Day",
               "internet_archive_newspapers": "News From 100 Years Ago",
               "global_voices": "From the World",
               "stack_exchange": "The Advice Column",
               "nasa": "Science Desk"}

FETCHERS = ["fetch_onthisday.py", "fetch_century_news.py",
            "fetch_rss.py", "fetch_stackexchange.py"]


def refresh_pantry() -> None:
    for script in FETCHERS:
        try:
            subprocess.run([sys.executable, str(ROOT / "src" / script)],
                           timeout=240, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[fetch] {script} ok")
        except Exception as exc:
            print(f"[warn] {script}: {exc} (continuing — fetch never blocks the digest)")


def word_stats(con) -> dict:
    """Per-word digest serving stats from the ledger (test pieces excluded)."""
    stats = {}
    for r in con.execute("SELECT words_used, digest_date FROM generated_pieces "
                         "WHERE digest_date IS NOT NULL"):
        for w in json.loads(r["words_used"] or "[]"):
            s = stats.setdefault(w, {"count": 0, "last": None})
            s["count"] += 1
            if s["last"] is None or r["digest_date"] > s["last"]:
                s["last"] = r["digest_date"]
    return stats


def daily_cap(count: int) -> int:
    """D27 stage-based caps: new words bear dense repetition, mature ones don't."""
    return 3 if count < 3 else 1


def due_pool(con, today: str) -> list:
    """Learning words currently due, fewest-served first."""
    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    stats = word_stats(con)
    due = []
    for w in words:
        if w.get("status", "learning") != "learning":
            continue
        s = stats.get(w["word"], {"count": 0, "last": None})
        if s["last"] is None:
            due.append((0, w["word"]))
            continue
        if s["last"] >= today:  # already served today (rebuild) — cap logic handles it
            due.append((s["count"], w["word"]))
            continue
        interval = INTERVALS[min(s["count"], len(INTERVALS) - 1)]
        gap = (date.fromisoformat(today) - date.fromisoformat(s["last"])).days
        if gap >= interval:
            due.append((s["count"], w["word"]))
    return [(w, c) for c, w in sorted(due)]


def taste_ok(item, skip: list) -> bool:
    return not (set(json.loads(item["categories"] or "[]")) & set(skip))


def pick_items(con, today: str) -> list:
    """Today's slots: calendar pair + newest tasteful GV pick + SE/NASA rotation.
    Rebuilds keep the original lineup: items already generated for today win
    their slot, so a --force never swaps content or orphans ledger rows."""
    d = date.fromisoformat(today)
    mmdd = d.strftime("%m-%d")
    config = json.loads((ROOT / "config" / "sources.json").read_text())
    skip = config["global_voices"].get("skip_categories", [])
    served = {r["item_id"] for r in con.execute(
        "SELECT DISTINCT item_id FROM generated_pieces WHERE digest_date IS NOT NULL "
        "AND digest_date != ?", (today,))}
    existing = {}
    for r in con.execute("SELECT DISTINCT item_id FROM generated_pieces "
                         "WHERE digest_date=?", (today,)):
        it = con.execute("SELECT * FROM items WHERE id=?", (r["item_id"],)).fetchone()
        if it is not None and it["source"] not in existing:
            existing[it["source"]] = it

    otd = existing.get("wikipedia_onthisday") or con.execute(
        "SELECT * FROM items WHERE source='wikipedia_onthisday' AND id LIKE ?",
        (f"%{mmdd}-{d.year}%",)).fetchone()
    century = existing.get("internet_archive_newspapers") or con.execute(
        "SELECT * FROM items WHERE source='internet_archive_newspapers' AND id LIKE ?",
        (f"%{d.year - 100}-{mmdd}%",)).fetchone()
    gv = existing.get("global_voices") or next((r for r in con.execute(
        "SELECT * FROM items WHERE source='global_voices' AND status='fetched' "
        "ORDER BY published DESC")
        if r["id"] not in served and taste_ok(r, skip)), None)
    rotation = "stack_exchange" if d.day % 2 == 0 else "nasa"
    extra = (existing.get("stack_exchange") or existing.get("nasa")
             or next((r for r in con.execute(
                 "SELECT * FROM items WHERE source=? AND status='fetched' "
                 "ORDER BY RANDOM()", (rotation,)) if r["id"] not in served), None))

    slots = []
    for it in (otd, century, gv, extra):
        if it is None:
            continue
        slots.append(it)
    missing = 4 - len(slots)
    if missing:
        print(f"[warn] {missing} slot(s) empty today — edition degrades gracefully")
    return slots


def existing_piece(con, item_id: str, today: str):
    return con.execute(
        "SELECT * FROM generated_pieces WHERE item_id=? AND digest_date=? "
        "ORDER BY id DESC", (item_id, today)).fetchone()


def pantry_menu(con, today: str, exclude: set) -> list:
    """Six unserved headlines the founder can request for tomorrow (D17)."""
    config = json.loads((ROOT / "config" / "sources.json").read_text())
    skip = config["global_voices"].get("skip_categories", [])
    served = {r["item_id"] for r in con.execute(
        "SELECT DISTINCT item_id FROM generated_pieces WHERE digest_date IS NOT NULL")}
    out = []
    for source, n in [("global_voices", 3), ("stack_exchange", 2), ("nasa", 1)]:
        rows = con.execute(
            "SELECT * FROM items WHERE source=? AND status='fetched' ORDER BY RANDOM()",
            (source,))
        got = 0
        for r in rows:
            if r["id"] in served or r["id"] in exclude:
                continue
            if source == "global_voices" and not taste_ok(r, skip):
                continue
            out.append(r)
            got += 1
            if got == n:
                break
    return out


def word_pills(pieces: list) -> str:
    """All tracked words as pills; the ones served in this edition highlighted
    (and tappable for their definition)."""
    import html as html_mod
    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    served = {w for p in pieces for w in p["words_used"]}
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
    return (f'<div class="words"><div class="wcount">{len(served)} of '
            f'{len(pills)} words in today\'s edition — tap a highlighted pill '
            f'for its meaning</div>{"".join(pills)}</div>')


def assemble(today: str, edition_no: int, pieces: list, menu: list) -> str:
    d = date.fromisoformat(today)
    total_words = sum(len(re.sub(r"<[^>]+>", " ", p["body"]).split()) for p in pieces)
    minutes = max(1, round(total_words / 220))
    sections = []
    for p in pieces:
        label = SLOT_LABELS.get(p["item"]["source"], "Today's Pick")
        sections.append(f"""
  <div class="kicker">{label}</div>
  <h1>{p['title']}</h1>
  {p['body']}
  <div class="attrib">{attribution_for(p['item'])}</div>
  <hr class="sep">""")
    menu_html = "\n".join(
        f'    <li><!-- {m["id"]} --><span class="mtag">{SLOT_LABELS.get(m["source"], m["source"])}</span> '
        f'{m["title"]}</li>' for m in menu)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetAIn · Edition {edition_no} · {d.strftime('%B %d')}</title><style>{CSS}
  .masthead {{ text-align: center; margin-bottom: 2.5rem; }}
  .masthead .brand {{ font-family: -apple-system, sans-serif; font-weight: 700;
                     font-size: 1.05rem; letter-spacing: .18em; color: #8a6d3b; }}
  .masthead .edition {{ font-family: -apple-system, sans-serif; font-size: .8rem;
                       color: #6d675e; margin-top: .3rem; }}
  hr.sep {{ border: 0; border-top: 1px solid #ddd5c8; margin: 2.5rem 0; }}
  .fin {{ text-align: center; font-family: -apple-system, sans-serif;
         color: #6d675e; margin: 2.5rem 0; }}
  .fin .big {{ font-size: 1.1rem; color: #26221c; margin-bottom: .4rem; }}
  .menu {{ background: #fff; border: 1px solid #e5ddd0; border-radius: 8px;
          padding: 1rem 1.4rem; font-family: -apple-system, sans-serif; font-size: .9rem; }}
  .menu h2 {{ font-size: .8rem; letter-spacing: .1em; text-transform: uppercase;
             color: #8a6d3b; margin: 0 0 .6rem; }}
  .menu ol {{ margin: 0; padding-left: 1.2rem; }}
  .menu li {{ margin: .45rem 0; }}
  .mtag {{ color: #8a6d3b; font-size: .75rem; text-transform: uppercase;
          letter-spacing: .06em; margin-right: .3rem; }}
  .words {{ margin: 0 0 2.5rem; text-align: center; }}
  .wcount {{ font-family: -apple-system, sans-serif; font-size: .72rem;
            color: #6d675e; margin-bottom: .7rem; letter-spacing: .04em; }}
  .pill {{ display: inline-block; font-family: -apple-system, sans-serif;
          font-size: .78rem; color: #a49c8f; border: 1px solid #e5ddd0;
          border-radius: 999px; padding: .12em .65em; margin: .18em .12em; }}
  .pill.served {{ color: #26221c; border-color: #e8c96a; cursor: pointer;
                 background: linear-gradient(transparent 55%, #ffe08a 55%); }}
</style></head>
<body><div class="sheet">
  <div class="masthead">
    <div class="brand">RETAIN</div>
    <div class="edition">Edition {edition_no} · {d.strftime('%A, %B %d, %Y')} ·
      {len(pieces)} pieces · ~{minutes} min</div>
  </div>
  {word_pills(pieces)}
  {''.join(sections)}
  <div class="fin">
    <div class="big">That's today's edition — you're caught up.</div>
    <div>Come back tomorrow. The words will find you again.</div>
  </div>
  <div class="menu">
    <h2>Fancy something for tomorrow?</h2>
    <ol>
{menu_html}
    </ol>
    <p style="margin:.8rem 0 0; color:#6d675e;">Reply with a number and it jumps the queue.</p>
  </div>
</div><div id="pop"></div><script>{POP_JS}</script></body></html>"""


def run() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    today = (args[args.index("--date") + 1] if "--date" in args
             else date.today().isoformat())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{today}.html"
    if out_path.exists() and not force:
        print(f"[ok] {out_path} already built — use --force to rebuild")
        return

    refresh_pantry()
    con = store.connect()
    env = load_env()

    pool = due_pool(con, today)
    stats = word_stats(con)
    today_served = {}
    for r in con.execute("SELECT words_used FROM generated_pieces WHERE digest_date=?",
                         (today,)):
        for w in json.loads(r["words_used"] or "[]"):
            today_served[w] = today_served.get(w, 0) + 1
    print(f"[plan] {len(pool)} words due")

    pieces = []
    for item in pick_items(con, today):
        wrapper = WRAPPERS.get(item["source"], "news.md")
        reuse = existing_piece(con, item["id"], today)
        if reuse:
            print(f"[skip] {item['id']} already generated for {today}")
            pieces.append({"item": item, "title": reuse["title"],
                           "body": reuse["body_html"],
                           "words_used": json.loads(reuse["words_used"] or "[]")})
            continue
        menu = [w for w, c in pool
                if today_served.get(w, 0) < daily_cap(stats.get(w, {}).get("count", 0))
                ][:MENU_SIZE]
        if not menu:
            print("[warn] no due words under cap left; menu falls back to full pool")
            menu = [w for w, _ in pool][:MENU_SIZE]
        try:
            piece = generate_piece(con, item, wrapper, menu, env, digest_date=today)
        except Exception as exc:
            print(f"[warn] {item['id']} failed ({exc}); slot dropped")
            continue
        con.commit()
        for w in piece["words_used"]:
            today_served[w] = today_served.get(w, 0) + 1
        pieces.append(piece)

    if not pieces:
        print("[error] no pieces generated — no digest written")
        return

    keep = {p["item"]["id"] for p in pieces}
    cur = con.execute(
        "DELETE FROM generated_pieces WHERE digest_date=? AND item_id NOT IN "
        f"({','.join('?' * len(keep))})", (today, *keep))
    if cur.rowcount:
        print(f"[clean] removed {cur.rowcount} orphaned same-day piece(s) from ledger")
    con.commit()

    edition_no = 1 + con.execute(
        "SELECT COUNT(DISTINCT digest_date) FROM generated_pieces "
        "WHERE digest_date IS NOT NULL AND digest_date < ?", (today,)).fetchone()[0]
    menu = pantry_menu(con, today, exclude={p["item"]["id"] for p in pieces})
    out_path.write_text(assemble(today, edition_no, pieces, menu))
    (OUT_DIR / "latest.html").write_text(out_path.read_text())

    servings = sum(len(p["words_used"]) for p in pieces)
    distinct = sorted({w for p in pieces for w in p["words_used"]})
    print(f"[ok] Edition {edition_no}: {len(pieces)} pieces, {servings} word "
          f"servings ({len(distinct)} distinct: {', '.join(distinct)})")
    print(f"[ok] wrote {out_path} (+ latest.html)")


if __name__ == "__main__":
    run()
