"""Lookalikes for the fill-in hint (PRD D58; flow-fill-in-the-word.md).

A model (DeepSeek, eval 2026-10-06) writes five words that look like the lemma but mean something very
different; code keeps those that are real dictionary words of the same part of speech, spelled like the
target and not forms of it. They're stored once per lemma, shared by every user (no user data). When a
user taps Hint, Jev puts each in that user's sentence and drops any that read naturally there (they'd
be a defensible answer marked wrong). Shared by the service and the evals, so an eval tests what ships."""
import difflib
import json
import random
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import generate as G

from . import db, dictionary, practice, typesafe
from .config import ROOT

PROMPT = (ROOT / "prompts" / "exercises" / "lookalikes.md").read_text()
DICT_PATH = ROOT / "data" / "dictionary" / "wiktionary.db"
COUNT = 3            # lookalikes shown with the word
FITS_AT = 0.5        # Jev P(natural) in the user's blank at or above this → it fits: dropped (eval: catches 16/18)
MODEL = {"model": "deepseek/deepseek-v4.1-flash", "call": G.make_openai_compat("https://openrouter.ai/api/v1"),
         "key": "OPENROUTER_API_KEY", "params": {"reasoning": {"enabled": False}}}  # fallback: G.FALLBACK
POS = {"adjective": "adj", "adverb": "adv"}  # our labels → Wiktionary's
SIMILAR_AT = 0.4  # spelling similarity (difflib ratio, 0–1); the lookalike eval's best match to the grader was
                  # 0.45, relaxed a little by the founder (2026-10-06): keeps 365/375 similar, drops 5/19 not


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def user_message(word: str, pos: str, definition: str) -> str:
    return f"Target word: {word} ({pos}) — {definition}"


def dictionary_pos(word: str) -> set:
    """Parts of speech Wiktionary lists for this exact word (empty if it isn't there)."""
    if not DICT_PATH.exists():
        return set()
    con = sqlite3.connect(f"file:{DICT_PATH}?mode=ro", uri=True)
    try:
        return {json.loads(d)["pos"] for (d,) in con.execute("SELECT data FROM entries WHERE word=?", (word,))}
    finally:
        con.close()


def check(raw: str, word: str, pos: str, limit: int = COUNT) -> tuple:
    """Model output → (kept lookalikes, problems). A lookalike is dropped if it isn't a single word,
    repeats, starts with the target's stem (a form or relative: galvanic, squanderer), is spelled too
    unlike the target (benchmark → embankment), or isn't a dictionary word of the same part of speech. Reads the last JSON object (models sometimes add a
    second try after the first)."""
    objs = [m for m in re.findall(r"\{[^{}]*\}", raw) if '"lookalikes"' in m]
    d = json.loads(objs[-1])
    want = POS.get(pos, pos)
    kept, problems = [], []
    for x in d.get("lookalikes", []):
        x = str(x).strip().lower()
        if not re.fullmatch(r"[a-z][a-z-]*", x):
            problems.append(f"{x}: not one word")
        elif x in kept or x == word:
            problems.append(f"{x}: repeat")
        elif x.startswith(practice.stem(word)):
            problems.append(f"{x}: a form of the target")
        elif similarity(word, x) < SIMILAR_AT:
            problems.append(f"{x}: doesn't look like the target")
        elif want and want not in dictionary_pos(x):
            problems.append(f"{x}: not a dictionary {pos}")
        else:
            kept.append(x)
    return kept[:limit], problems


def stored(con, word: str) -> list:
    row = con.execute("SELECT candidates FROM lookalikes WHERE word=?", (word,)).fetchone()
    return json.loads(row[0]) if row else []


def ensure(con, word: str, pos: str, definition: str, env: dict) -> list:
    """Make sure the lemma has stored candidates (daily prep, or a Hint before prep wrote them);
    one retry when fewer than COUNT survive the code check. → call rows."""
    if stored(con, word):
        return []
    best, calls = [], []
    for _ in range(2):
        try:
            raw, model = G.call_model(PROMPT, user_message(word, pos or "", definition), env,
                                      purpose="lookalikes", primary=MODEL)
            calls.append(G.last_call())
            kept, problems = check(raw, word, pos or "", limit=5)
        except Exception as exc:
            print(f"[lookalikes] {word!r} failed ({exc})")
            continue
        best = kept if len(kept) > len(best) else best
        if len(best) >= COUNT:
            break
    if best:
        with db._lock:
            con.execute("INSERT OR IGNORE INTO lookalikes (word, candidates, model, created_at) VALUES (?,?,?,?)",
                        (word, json.dumps(best), model, db.now()))
            con.commit()
    return calls


def gloss(word: str, pos: str) -> str:
    senses = (dictionary.lookup(word) or {}).get("senses", [])
    want = POS.get(pos, pos)
    return next((s["gloss"] for s in senses if s["pos"] == want), senses[0]["gloss"] if senses else "")


def hint_options(word: str, pos: str, blanked: str, candidates: list) -> tuple:
    """Jev checks every candidate in this user's blank (in parallel); the first COUNT that don't fit
    join the word, shuffled. → (options, call rows)."""
    def score(x):
        try:
            p, row = typesafe.p_natural(x, gloss(x, pos), blanked.replace(practice.BLANK, x))
            return x, p, ("hint-check", *row[1:])
        except Exception as exc:
            print(f"[lookalikes] Jev on {x!r} failed ({exc})")
            return x, None, None
    with ThreadPoolExecutor(5) as pool:
        scored = list(pool.map(score, candidates))
    kept = [x for x, p, _ in scored if p is not None and p < FITS_AT][:COUNT]
    options = [word, *kept]
    random.shuffle(options)
    return options, [row for *_, row in scored if row]
