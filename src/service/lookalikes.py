"""Lookalikes for the fill-in hint (PRD D58; flow-fill-in-the-word.md).

A model writes five words that look like the lemma but mean something very different; code keeps the
first three that are real dictionary words of the same part of speech and not forms of the target. Shared by
the service and the evals, so an eval tests the check that ships."""
import json
import re
import sqlite3

from . import practice

from .config import ROOT

PROMPT = (ROOT / "prompts" / "exercises" / "lookalikes.md").read_text()
DICT_PATH = ROOT / "data" / "dictionary" / "wiktionary.db"
COUNT = 3
POS = {"adjective": "adj", "adverb": "adv"}  # our labels → Wiktionary's


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


def check(raw: str, word: str, pos: str) -> tuple:
    """Model output → (kept lookalikes, problems). A lookalike is dropped if it isn't a single word,
    repeats, starts with the target's stem (a form or relative: galvanic, squanderer), or isn't a
    dictionary word of the same part of speech. Reads the last JSON object (models sometimes add a
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
        elif want and want not in dictionary_pos(x):
            problems.append(f"{x}: not a dictionary {pos}")
        else:
            kept.append(x)
    return kept[:COUNT], problems
