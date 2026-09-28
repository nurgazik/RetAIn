"""Word cards (D48, diagrams/word-capture-flow.md): Wiktionary for the facts, the model for
examples, a shared card per headword reused by every user.

Reference data: data/dictionary/wiktionary.db — a read-only SQLite file built once from
kaikki.org's Wiktextract English dump (CC BY-SA 4.0), one row per English entry, trimmed to
the fields a card needs. It is not app state: rebuilt wholesale when the dump is refreshed.

  python -m service.dictionary build [dump.jsonl]   build the reference file (~1 min)
  python -m service.dictionary backfill             cards for every word without one; fill
                                                    missing examples (idempotent)"""
import json
import pathlib
import re
import sqlite3
import sys

from . import db
from .config import ROOT

DICT_DIR = ROOT / "data" / "dictionary"
DICT_PATH = DICT_DIR / "wiktionary.db"
DROP = {"archaic", "obsolete", "rare", "dated"}  # senses a learner doesn't need (spike 2026-09-27)
MAX_EXAMPLE_SENSES = 5  # the model writes examples for the first five meanings; undercut has 17
US, UK = {"US", "General-American"}, {"UK", "Received-Pronunciation"}

EXAMPLES_SYSTEM = """You write example sentences for an advanced ESL learner's vocabulary card.
You get a word and its numbered meanings. For EACH meaning, write 2 or 3 natural, modern sentences
a skilled native writer would produce, using the word in exactly that meaning (inflected forms are
fine). Vary the settings; no dictionary-style or childish sentences.
Output STRICT JSON only: {"examples": {"1": ["...", "..."], "2": ["...", "..."]}}"""

UNKNOWN_SYSTEM = """You help an advanced ESL learner who saved a word that is not in our dictionary.
Decide whether it is a real English word or established expression (including slang, new words
and informal usage) that a native speaker would recognise. Typos, random strings and words from
other languages are not real. If it is real, define it and write 2 or 3 natural, modern example
sentences.
Output STRICT JSON only:
{"real": true, "pos": "<noun|verb|adjective|adverb|phrase>", "definition": "<one plain sentence>",
 "examples": ["...", "..."]}
or {"real": false}"""


# ---- reference file ------------------------------------------------------------------

def _trim(e: dict) -> dict:
    """Keep what a card needs; the raw entry carries translations, etymology, templates…"""
    return {
        "pos": e.get("pos"),
        "senses": [{k: v for k, v in {
            "glosses": s.get("glosses"), "tags": s.get("tags"),
            "form_of": [f["word"] for f in s.get("form_of", []) if f.get("word")],
            "alt_of": [f["word"] for f in s.get("alt_of", []) if f.get("word")],
        }.items() if v} for s in e.get("senses", [])],
        "sounds": [{"ipa": x["ipa"], "tags": x.get("tags", [])} for x in e.get("sounds", []) if x.get("ipa")],
    }


def build(dump: pathlib.Path) -> None:
    tmp = DICT_PATH.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript("CREATE TABLE entries (word TEXT NOT NULL, data TEXT NOT NULL);"
                      "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);")
    n = 0
    with dump.open(encoding="utf-8") as f:
        batch = []
        for line in f:
            e = json.loads(line)
            if e.get("lang_code") != "en" or not e.get("word"):
                continue
            batch.append((e["word"].lower(), json.dumps(_trim(e), separators=(",", ":"))))
            if len(batch) == 50_000:
                con.executemany("INSERT INTO entries VALUES (?,?)", batch)
                n += len(batch)
                batch = []
                print(f"  {n:,} entries", file=sys.stderr)
        con.executemany("INSERT INTO entries VALUES (?,?)", batch)
        n += len(batch)
    con.execute("CREATE INDEX idx_word ON entries (word)")
    con.execute("INSERT INTO meta VALUES ('dump', ?)", (dump.name,))
    con.commit()
    con.close()
    tmp.replace(DICT_PATH)
    print(f"built {DICT_PATH} ({n:,} entries, {DICT_PATH.stat().st_size / 1e6:.0f} MB)")


# ---- lookup --------------------------------------------------------------------------

def _entries(con, word: str) -> list:
    return [json.loads(r[0]) for r in con.execute("SELECT data FROM entries WHERE word=?", (word,))]


def _redirect(s: dict) -> list:
    return s.get("form_of", []) + s.get("alt_of", [])


def _kept(es: list) -> list:
    """A card's meanings: Wiktionary order, minus redirects, proper names (lowercasing merges
    "Ran" the surname into "ran") and archaic/obsolete/rare/dated senses."""
    senses = [{"pos": e["pos"], "gloss": s["glosses"][-1], "tags": s.get("tags", [])}
              for e in es if e["pos"] != "name" for s in e["senses"]
              if s.get("glosses") and not _redirect(s) and "form-of" not in s.get("tags", [])]
    # a heading note like "(obsolete except …)" can tag every sense (fraught): then keep them all
    return [s for s in senses if not DROP & set(s["tags"])] or senses


def lookup(word: str) -> dict | None:
    """Wiktionary card facts for `word`, or None. When Wiktionary's first sense is an inflection,
    spelling variant or misspelling (ran → run, belabor → belabour, ubiquitious → ubiquitous)
    and that entry exists, the card is the target's. Senses keep Wiktionary's order."""
    if not DICT_PATH.exists():
        return None
    con = sqlite3.connect(f"file:{DICT_PATH}?mode=ro", uri=True)
    try:
        dump = con.execute("SELECT value FROM meta WHERE key='dump'").fetchone()[0]
        headword, es = word, _entries(con, word)
        first = next((s for e in es if e["pos"] != "name" for s in e["senses"] if s.get("glosses")), {})
        target = next(iter(_redirect(first)), "").lower()
        own = _kept(es)  # a word with real meanings of its own stays itself (protracted, scathing)
        stays = len(own) >= 2 or any(s["pos"] in ("adj", "adv") for s in own)
        if target and target != word and not stays and _kept(_entries(con, target)):
            headword, es = target, _entries(con, target)
        kept = _kept(es)
        if not kept:
            return None
        sounds = [x for e in es for x in e["sounds"]]
        ipa = ([x for x in sounds if US & set(x["tags"])][:1] + [x for x in sounds if UK & set(x["tags"])][:1]
               or sounds[:1])
        return {"headword": headword, "senses": kept, "ipa": ipa, "dump": dump,
                "source_url": f"https://en.wiktionary.org/wiki/{headword.replace(' ', '_')}"}
    finally:
        con.close()


# ---- cards ---------------------------------------------------------------------------

def _ask(system: str, user: str, env: dict) -> tuple:
    """One model call on the production chain → (parsed JSON or None, the call log rows)."""
    import generate as G
    start = len(G.CALL_LOG)  # never clear: a transform on another thread shares this log
    try:
        raw, _ = G.call_model(system, user, env, purpose="card")
        parsed = json.loads(re.sub(r"^```(json)?\s*|\s*```$", "", raw.strip(), flags=re.M).strip())
    except Exception as exc:  # the capture still succeeds; backfill fills the gap later
        print(f"[card] model call failed ({exc})")
        parsed = None
    return parsed, G.CALL_LOG[start:]


def write_examples(con, lexicon_id: int, headword: str, env: dict) -> list:
    """Model examples for the first MAX_EXAMPLE_SENSES meanings still missing them. Returns call rows."""
    rows = con.execute("SELECT id, pos, gloss, examples FROM senses WHERE lexicon_id=? ORDER BY ord",
                       (lexicon_id,)).fetchall()[:MAX_EXAMPLE_SENSES]
    todo = [r for r in rows if r["examples"] is None]
    if not todo:
        return []
    meanings = "\n".join(f"{i}. ({r['pos']}) {r['gloss']}" for i, r in enumerate(todo, 1))
    parsed, calls = _ask(EXAMPLES_SYSTEM, f"WORD: {headword}\nMEANINGS:\n{meanings}", env)
    got = (parsed or {}).get("examples") or {}
    for i, r in enumerate(todo, 1):
        ex = got.get(str(i))
        if isinstance(ex, list) and ex:
            con.execute("UPDATE senses SET examples=? WHERE id=?", (json.dumps([str(x) for x in ex[:3]]), r["id"]))
    con.commit()
    return calls


def _insert_lexicon(con, headword: str, source: str, ipa: list, url: str | None, dump: str | None,
                    senses: list) -> int:
    """Create the shared card; if another request created it first, use theirs."""
    cur = con.execute("INSERT OR IGNORE INTO lexicon (headword, source, ipa, source_url, dump, created_at) "
                      "VALUES (?,?,?,?,?,?)", (headword, source, json.dumps(ipa), url, dump, db.now()))
    lid = con.execute("SELECT id FROM lexicon WHERE headword=?", (headword,)).fetchone()[0]
    if cur.rowcount:
        con.executemany("INSERT INTO senses (lexicon_id, ord, pos, gloss, tags, examples) VALUES (?,?,?,?,?,?)",
                        [(lid, i, s["pos"], s["gloss"], json.dumps(s.get("tags", [])),
                          json.dumps(s["examples"]) if s.get("examples") else None)
                         for i, s in enumerate(senses, 1)])
    con.commit()
    return lid


def build_card(con, word: str, env: dict) -> tuple:
    """The capture flow (diagram): shared list → Wiktionary (+ model examples) → model
    fallback → unverified. Returns (lexicon_id | None, first definition | "", call rows)."""
    found = lookup(word)
    headword = found["headword"] if found else word
    row = con.execute("SELECT id FROM lexicon WHERE headword=?", (headword,)).fetchone()
    if row:  # someone already added it: no model call
        return row["id"], first_gloss(con, row["id"]), []
    if found:
        lid = _insert_lexicon(con, headword, "wiktionary", found["ipa"], found["source_url"], found["dump"],
                              found["senses"])
        return lid, first_gloss(con, lid), write_examples(con, lid, headword, env)
    parsed, calls = _ask(UNKNOWN_SYSTEM, f"WORD: {word}", env)
    if not parsed or not parsed.get("real") or not parsed.get("definition"):
        return None, "", calls  # unverified: stays in the user's own list only
    lid = _insert_lexicon(con, word, "model", [], None, None,
                          [{"pos": parsed.get("pos"), "gloss": parsed["definition"],
                            "examples": [str(x) for x in parsed.get("examples", [])][:3]}])
    return lid, parsed["definition"], calls


def first_gloss(con, lexicon_id: int) -> str:
    r = con.execute("SELECT gloss FROM senses WHERE lexicon_id=? ORDER BY ord LIMIT 1", (lexicon_id,)).fetchone()
    return r[0] if r else ""


def cards(con, lexicon_ids: set) -> dict:
    """{lexicon_id: card} for the API, in two queries."""
    ids = [i for i in lexicon_ids if i]
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    out = {r["id"]: {"headword": r["headword"], "source": r["source"], "ipa": json.loads(r["ipa"] or "[]"),
                     "source_url": r["source_url"], "senses": []}
           for r in con.execute(f"SELECT * FROM lexicon WHERE id IN ({marks})", ids)}
    for s in con.execute(f"SELECT * FROM senses WHERE lexicon_id IN ({marks}) ORDER BY lexicon_id, ord", ids):
        out[s["lexicon_id"]]["senses"].append({"pos": s["pos"], "gloss": s["gloss"],
                                               "tags": json.loads(s["tags"] or "[]"),
                                               "examples": json.loads(s["examples"] or "[]")})
    return out


def backfill() -> None:
    """Cards for every word row without one (definitions become the card's first meaning,
    as for new words), then examples wherever the model hasn't written them yet."""
    from . import engine
    env = engine.model_env()
    con = db.connect()
    cost = 0.0
    words = sorted({r["word"] for r in con.execute("SELECT word FROM words WHERE lexicon_id IS NULL")})
    print(f"[backfill] {len(words)} words without a card")
    for i, w in enumerate(words, 1):
        lid, definition, calls = build_card(con, w, env)
        cost += db.record_calls(con, None, None, calls, engine.PRICES)
        if lid:
            con.execute("UPDATE words SET lexicon_id=?, definition=? WHERE word=? AND lexicon_id IS NULL",
                        (lid, definition, w))
            con.commit()
        print(f"[backfill] {i}/{len(words)} {w}: {'card ' + str(lid) if lid else 'not found (kept as is)'}")
    for r in con.execute("SELECT DISTINCT l.id, l.headword FROM lexicon l JOIN senses s ON s.lexicon_id = l.id "
                         "WHERE s.examples IS NULL AND l.source='wiktionary'").fetchall():
        cost += db.record_calls(con, None, None, write_examples(con, r["id"], r["headword"], env), engine.PRICES)
    print(f"[backfill] done, ${cost:.4f}")
    con.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build(pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else sorted(DICT_DIR.glob("*.jsonl"))[-1])
    elif cmd == "backfill":
        db.init()
        backfill()
    else:
        print(__doc__)
