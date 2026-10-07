"""Daily practice (PRD D53, D56; flows: diagrams/flow-fill-in-the-word.md, flow-write-a-sentence.md).

Code owns the schedule and the fill-in check; models only write fill-in sentences (daily prep, cached)
and judge written sentences (Jev first, an LLM writes feedback only when needed).

Scheduling (Leitner-style expanding gaps): a word's `box` 0..4 maps to the gap before it's due
again. A miss (wrong fill-in, or a sentence judged wrong) sends it back to box 0, due tomorrow;
a clean pass moves it up a box; "could be better" keeps its box. New words come in oldest first.
"""
import json
import random
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import generate as G

from . import db, dictionary, lookalikes, typesafe
from .config import ROOT

SET_SIZE = 5
GAPS = [1, 3, 7, 14, 30]           # days until due again, by box
NATURAL_AT = 0.9                    # Jev ✓ only when this sure (TD-21: 0/35 wrong passed on the eval set)
SENTENCES_PER_WORD = 3              # model-written fill-in sentences kept per word before reusing
FILL_PROMPT = (ROOT / "prompts" / "exercises" / "fill-sentence.md").read_text()
JUDGE_PROMPT = (ROOT / "prompts" / "exercises" / "sentence-judge.md").read_text()
BLANK = "_____"


def add_days(day: str, n: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()


def stem(word: str) -> str:
    """Enough of the word to recognise its forms (bolster → bolst…, galvanize → galvaniz…)."""
    return word.lower() if len(word) <= 5 else word.lower()[:-2]


# ---------------------------------------------------------------- fill-in sentences

def _blank(sentence: str, answer: str) -> str | None:
    """The sentence with the answer blanked once, or None if it isn't there exactly once."""
    hits = list(re.finditer(rf"\b{re.escape(answer)}\b", sentence, flags=re.I))
    if len(hits) != 1:
        return None
    h = hits[0]
    return sentence[:h.start()] + BLANK + sentence[h.end():]


def from_reads(con, user_id: str, word: str) -> dict | None:
    """A sentence from the user's own pieces where this word was placed (newest first)."""
    st = stem(word)
    for (body,) in con.execute("SELECT body_html FROM pieces WHERE user_id=? AND status='done' AND body_html LIKE ? "
                               "ORDER BY created_at DESC LIMIT 20", (user_id, f"%>{st}%")):
        text = re.sub(r"<mark[^>]*>(.*?)</mark>", r"⟦\1⟧", body or "", flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        for s in G.split_sentences(re.sub(r"\s+", " ", text)):
            hit = next((x for x in re.findall(r"⟦([^⟧]+)⟧", s) if x.lower().startswith(st)), None)
            if not hit:
                continue
            plain = re.sub(r"⟦([^⟧]+)⟧", r"\1", s).strip()
            blanked = _blank(plain, hit)
            if blanked and 6 <= len(plain.split()) <= 45:
                return {"text": blanked, "answer": hit, "source": "read"}
    return None


def write_sentence(word: str, definition: str, env: dict) -> tuple:
    """Model writes one fill-in sentence; Jev checks it's natural. → (dict | None, call rows)."""
    calls = []
    try:
        raw, _ = G.call_model(FILL_PROMPT, f"Target word: {word} — {definition}", env, purpose="fill-sentence")
        calls = [G.last_call()]
        d = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        sentence, answer = d["sentence"].strip(), d["answer"].strip()
        if not answer.lower().startswith(stem(word)) or not _blank(sentence, answer):
            return None, calls
        p, row = typesafe.p_natural(word, definition, sentence)
        calls.append(row)
        return ({"sentence": sentence, "answer": answer, "p_natural": p} if p >= NATURAL_AT else None), calls
    except Exception as exc:
        print(f"[practice] fill sentence for {word!r} failed ({exc})")
        return None, calls


def model_sentence(con, word: str, definition: str, env: dict) -> tuple:
    """A cached model-written sentence; writes a new one while the word has fewer than
    SENTENCES_PER_WORD (one retry). Shared by all users: no user data. → (dict | None, call rows)."""
    rows = con.execute("SELECT sentence, answer FROM practice_sentences WHERE word=?", (word,)).fetchall()
    calls = []
    if len(rows) < SENTENCES_PER_WORD:
        for _ in range(2):
            got, c = write_sentence(word, definition, env)
            calls += c
            if got:
                with db._lock:
                    con.execute("INSERT INTO practice_sentences (word, sentence, answer, p_natural, created_at) "
                                "VALUES (?,?,?,?,?)", (word, got["sentence"], got["answer"], got["p_natural"], db.now()))
                    con.commit()
                rows = [*rows, got]
                break
    if not rows:
        return None, calls
    pick = random.choice(rows)
    return {"text": _blank(pick["sentence"], pick["answer"]), "answer": pick["answer"], "source": "model"}, calls


# ---------------------------------------------------------------- today's set

def pick_words(con, user_id: str, day: str, n: int = SET_SIZE) -> list:
    """Due words (most overdue first), then new words (oldest first); retained/unverified never."""
    base = "SELECT * FROM words WHERE user_id=? AND status='learning' AND definition != ''"
    due = con.execute(base + " AND due_day IS NOT NULL AND due_day <= ? ORDER BY due_day, id", (user_id, day)).fetchall()
    new = con.execute(base + " AND due_day IS NULL ORDER BY id", (user_id,)).fetchall()
    return [dict(r) for r in [*due, *new][:n]]


def build_set(con, user: dict, env: dict) -> dict:
    """Today's words with a fill-in sentence each (own reading first, else model-written)."""
    words = pick_words(con, user["id"], user["day"])
    calls = []

    def fill_for(w):  # its own connection: SQLite connections can't be shared across threads
        c = db.connect()
        try:
            own = from_reads(c, user["id"], w["word"])
            fill, calls = (own, []) if own else model_sentence(c, w["word"], w["definition"], env)
            if fill:  # the Hint's lookalikes, written once per lemma (D58)
                calls = calls + lookalikes.ensure(c, w["word"], w.get("pos"), w["definition"], env)
            return fill, calls
        finally:
            c.close()
    with ThreadPoolExecutor(4) as pool:
        fills = list(pool.map(fill_for, words))
    items = []
    for w, (fill, c) in zip(words, fills):
        calls += c
        items.append({"word_id": w["id"], "word": w["word"], "definition": w["definition"], "pos": w.get("pos"),
                      "box": w["box"], "fill": fill})
    with db._lock:
        con.execute("INSERT OR IGNORE INTO practice_sets (user_id, day, items, created_at) VALUES (?,?,?,?)",
                    (user["id"], user["day"], json.dumps(items), db.now()))
        con.commit()
    db.record_calls(con, user["id"], None, calls, prices(), day=user["day"])
    return get_set(con, user["id"], user["day"])


def get_set(con, user_id: str, day: str) -> dict | None:
    row = con.execute("SELECT items FROM practice_sets WHERE user_id=? AND day=?", (user_id, day)).fetchone()
    if not row:
        return None
    items = json.loads(row["items"])
    done, fills = {}, {}
    for a in con.execute("SELECT word_id, kind, correct, verdict, reason, fix, answer FROM practice_attempts "
                         "WHERE user_id=? AND day=? ORDER BY id", (user_id, day)):
        if a["kind"] == "fill":
            fills.setdefault(a["word_id"], []).append(dict(a))
        else:
            done.setdefault(a["word_id"], {})[a["kind"]] = dict(a)
    for wid, tries in fills.items():  # D58: retries until right; done once right, ✓ only if right first time
        solved = next((t for t in tries if t["correct"]), None)
        if solved:
            done.setdefault(wid, {})["fill"] = {**solved, "correct": tries[0]["correct"]}
    statuses = {r["id"]: r["status"] for r in con.execute(
        f"SELECT id, status FROM words WHERE id IN ({','.join('?' * len(items)) or 'NULL'})",
        [i["word_id"] for i in items])}
    for i in items:
        i["attempts"] = done.get(i["word_id"], {})
        i["status"] = statuses.get(i["word_id"], "learning")
        if i["fill"]:  # the client never needs the answer before it's solved
            wrong = [t["answer"].lower() for t in fills.get(i["word_id"], []) if not t["correct"]]
            i["fill"] = {"text": i["fill"]["text"], "source": i["fill"]["source"],
                         **({"hint": i["fill"]["hint"]} if i["fill"].get("hint") else {}),
                         "wrong": [{"answer": w, "meaning": meaning(w, i.get("pos"))} for w in dict.fromkeys(wrong)],
                         **({"answer": i["fill"]["answer"]} if "fill" in i["attempts"] else {})}
    return {"day": day, "items": items}


def item_of(con, user: dict, word_id: int) -> dict:
    row = con.execute("SELECT items FROM practice_sets WHERE user_id=? AND day=?", (user["id"], user["day"])).fetchone()
    for i in json.loads(row["items"]) if row else []:
        if i["word_id"] == word_id:
            return i
    raise KeyError(word_id)


def hint(con, user: dict, word_id: int, env: dict) -> tuple:
    """The fill-in Hint (D58): the word among up to three lookalikes that don't fit this sentence.
    Kept on today's set, so asking again shows the same options at no cost. → (options, call rows)."""
    item = item_of(con, user, word_id)
    if not item["fill"]:
        raise KeyError(word_id)
    if item["fill"].get("hint"):
        return item["fill"]["hint"], []
    calls = lookalikes.ensure(con, item["word"], item.get("pos"), item["definition"], env)
    options, c = lookalikes.hint_options(item["word"], item.get("pos") or "", item["fill"]["text"],
                                         lookalikes.stored(con, item["word"]))
    with db._lock:
        row = con.execute("SELECT items FROM practice_sets WHERE user_id=? AND day=?", (user["id"], user["day"])).fetchone()
        items = json.loads(row["items"])
        for i in items:
            if i["word_id"] == word_id:
                i["fill"]["hint"] = options
        con.execute("UPDATE practice_sets SET items=? WHERE user_id=? AND day=?", (json.dumps(items), user["id"], user["day"]))
        con.commit()
    return options, calls + c


# ---------------------------------------------------------------- answers

def meaning(word: str, pos: str | None) -> str | None:
    """A wrong answer's dictionary meaning, for tap-to-see (local lookup, no model)."""
    return lookalikes.gloss(word, pos or "") or None


def check_fill(item: dict, answer: str) -> dict:
    """Code only: the blanked form is right; so is any form of the word (D58: its lemma, or an inflection
    that folds into it), with the form shown. A wrong answer doesn't reveal the word (try again, D58):
    it comes back with its own meaning when the dictionary has it."""
    given, expected = answer.strip().lower(), item["fill"]["answer"].lower()
    if given == expected:
        return {"correct": True, "expected": item["fill"]["answer"], "note": None}
    if given == item["word"].lower() or dictionary.lemma(given) == item["word"].lower():
        return {"correct": True, "expected": item["fill"]["answer"], "note": f"Right word — here it's “{item['fill']['answer']}”."}
    return {"correct": False, "answer": given, "meaning": meaning(given, item.get("pos"))}


def judge_sentence(word: str, definition: str, sentence: str, env: dict) -> tuple:
    """Jev first: ✓ when P(natural) ≥ NATURAL_AT. Otherwise the LLM gives verdict, reason, fix.
    Jev failing falls through to the LLM. → (result dict, call rows)."""
    calls = []
    try:
        p, row = typesafe.p_natural(word, definition, sentence)
        calls.append(row)
        if p >= NATURAL_AT:
            return {"verdict": "natural", "reason": None, "fix": None, "by": "jev", "p_natural": p}, calls
    except Exception as exc:
        print(f"[practice] Jev failed, LLM judges ({exc})")
        p = None
    raw, _ = G.call_model(JUDGE_PROMPT, f"Target word: {word} — {definition}\nSentence: {sentence}", env,
                          purpose="feedback")
    calls.append(G.last_call())
    d, _ = json.JSONDecoder().raw_decode(raw[raw.index("{"):])
    verdict = d.get("verdict") if d.get("verdict") in ("natural", "could-be-better", "wrong") else "could-be-better"
    return {"verdict": verdict, "reason": d.get("reason"), "fix": d.get("fix") if verdict != "natural" else None,
            "by": "llm", "p_natural": p}, calls


def uses_word(sentence: str, word: str) -> bool:
    return any(t.startswith(stem(word)) for t in re.findall(r"[a-z]+", sentence.lower()))


def record(con, user: dict, item: dict, kind: str, answer: str, result: dict) -> int:
    """Store the attempt (with Jev's score and who judged, for sentences) → its id."""
    with db._lock:
        hinted = kind == "fill" and item["fill"].get("hint")
        cur = con.execute("INSERT INTO practice_attempts (user_id, word_id, day, kind, answer, correct, verdict, reason, "
                          "fix, p_natural, judged_by, hint, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (user["id"], item["word_id"], user["day"], kind, answer, result.get("correct"),
                           result.get("verdict"), result.get("reason"), result.get("fix"), result.get("p_natural"),
                           result.get("by"), json.dumps(hinted) if hinted else None, db.now()))
        con.commit()
    reschedule(con, user, item)
    return cur.lastrowid


def reschedule(con, user: dict, item: dict) -> None:
    """After every attempt, from all of today's attempts on the word (D57: either exercise counts on
    its own): a miss → box 0, due tomorrow; a "could be better" → same box; otherwise up one box.
    The base is the box when today's set was built, so two clean exercises are still one step.
    A fill-in is judged on its first try (D58): wrong first, right later is still a miss."""
    tries = {}
    for a in con.execute("SELECT kind, correct, verdict FROM practice_attempts WHERE user_id=? AND word_id=? AND day=? "
                         "ORDER BY id", (user["id"], item["word_id"], user["day"])):
        tries.setdefault(a["kind"], a)
    fill, write = tries.get("fill"), tries.get("write")
    box = item["box"]
    if (fill and not fill["correct"]) or (write and write["verdict"] == "wrong"):
        box = 0
    elif not (write and write["verdict"] == "could-be-better"):
        box = min(box + 1, len(GAPS) - 1)
    due = add_days(user["day"], GAPS[box])
    with db._lock:
        con.execute("UPDATE words SET box=?, due_day=? WHERE id=?", (box, due, item["word_id"]))
        con.commit()


def prices() -> dict:
    from .engine import PRICES
    return PRICES | {typesafe.MODEL: {"in": typesafe.PRICE_IN, "out": 0.0}}
