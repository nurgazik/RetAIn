"""Lookalike writer eval (D55, D58; flow-fill-in-the-word, eval-lookalikes diagram).
Each candidate writes three lookalikes per golden word with the production prompt; code keeps the
real dictionary words of the same part of speech (service/lookalikes.check). A blind packet puts
each lookalike next to that word's fill-in sentence (from the fill eval's Gemma run) and is graded
on: looks similar · very different meaning · could it fill the blank (the number that decides
whether production needs a per-sentence Jev check)."""
import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from bakeoff import load_env
from service import dictionary, lookalikes, practice, typesafe

from . import dataset, fillin, results
from .sentences import PACKETS

SENTENCE_RUN = 1  # fill_runs.id 1: gemma-4-26b, the production fill-in writer (2026-10-04)
SCHEMA = """
CREATE TABLE IF NOT EXISTS look_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT NOT NULL, prompt TEXT NOT NULL, at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS look_outputs (
    run_id INTEGER NOT NULL, word TEXT NOT NULL, ok INTEGER NOT NULL, error TEXT,
    raw TEXT, kept TEXT, problems TEXT, cost_usd REAL, seconds REAL,
    PRIMARY KEY (run_id, word)
);
CREATE TABLE IF NOT EXISTS look_jev (
    run_id INTEGER NOT NULL, word TEXT NOT NULL, lookalike TEXT NOT NULL, p_natural REAL, cost_usd REAL,
    PRIMARY KEY (run_id, word, lookalike)
);
CREATE TABLE IF NOT EXISTS look_grades (
    run_id INTEGER NOT NULL, word TEXT NOT NULL, lookalike TEXT NOT NULL, grader TEXT NOT NULL,
    looks_similar INTEGER, different_meaning INTEGER, fits_blank INTEGER, at TEXT NOT NULL,
    PRIMARY KEY (run_id, word, lookalike, grader)
);
"""
RUBRIC = """Each entry is a hint for a fill-in-the-blank exercise for an advanced English learner: the target word
(hidden answer) and its meaning, the sentence with the blank, and candidate wrong options ("lookalikes").
For each lookalike answer:
  looks_similar      true if it looks like the target (spelling, length, start or ending) so a learner could
                     plausibly mix them up.
  different_meaning  true if its meaning is very different from the target's (not a synonym, antonym or
                     same-topic word).
  fits_blank         true if the lookalike, in any grammatical form, could sensibly fill the blank, so a learner
                     who picks it would be marked wrong for a defensible answer. Judge the sentence as written.
Write {"<id>": {"<lookalike>": {"looks_similar": b, "different_meaning": b, "fits_blank": b}, ...}, ...}
to grades.json."""


def connect():
    con = results.connect()
    con.executescript(SCHEMA)
    return con


def prompt_hash() -> str:
    return hashlib.sha1(lookalikes.PROMPT.encode()).hexdigest()[:10]


def run(name: str, workers: int = 6) -> int:
    spec = results.spec(name)
    chk = results.primary_for(spec)
    env = load_env()
    words = dataset.load_words()

    def one(w):
        t0 = time.time()
        try:
            out = chk["call"](chk["model"], lookalikes.PROMPT, lookalikes.user_message(w["word"], w["pos"], w["definition"]),
                              env[chk["key"]], chk["params"])
            kept, problems = lookalikes.check(out["text"], w["word"], w["pos"])
            cost = results.call_cost(spec, out["tokens_in"], out["tokens_out"], out.get("cost"))
            return (w["word"], 1, None, out["text"], json.dumps(kept), json.dumps(problems), cost, time.time() - t0)
        except Exception as exc:
            return (w["word"], 0, str(exc)[:300], None, "[]", "[]", 0.0, time.time() - t0)
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, words))
    con = connect()
    rid = con.execute("INSERT INTO look_runs (model_name, prompt, at) VALUES (?,?,?)",
                      (name, prompt_hash(), datetime.now(timezone.utc).isoformat())).lastrowid
    con.executemany("INSERT INTO look_outputs VALUES (?,?,?,?,?,?,?,?,?)", [(rid, *r) for r in rows])
    con.commit()
    full = sum(len(json.loads(r[4])) == lookalikes.COUNT for r in rows)
    dropped = sum(len(json.loads(r[5])) for r in rows)
    print(f"[look] run {rid} {name}: {full}/{len(rows)} words with {lookalikes.COUNT} kept lookalikes, "
          f"{dropped} dropped by the code check; ${sum(r[6] for r in rows):.4f}")
    return rid


def sentences() -> dict:
    """word → the blanked fill-in sentence the fill eval's production run wrote for it."""
    con = fillin.connect()
    return {r["word"]: practice._blank(r["sentence"], r["answer"]) for r in con.execute(
        "SELECT word, sentence, answer FROM fill_outputs WHERE run_id=? AND blank_ok=1", (SENTENCE_RUN,))}


def export(run_ids: list) -> None:
    con = connect()
    words = {w["word"]: w for w in dataset.load_words()}
    blanks = sentences()
    entries, key = [], {}
    for rid in run_ids:
        for r in con.execute("SELECT * FROM look_outputs WHERE run_id=? AND ok=1", (rid,)):
            kept = json.loads(r["kept"])
            if not kept or r["word"] not in blanks:
                continue
            b = hashlib.sha1(f"look:{rid}:{r['word']}".encode()).hexdigest()[:8]
            key[b] = [rid, r["word"]]
            w = words[r["word"]]
            entries.append({"id": b, "word": w["word"], "pos": w["pos"], "definition": w["definition"],
                            "exercise": blanks[r["word"]], "lookalikes": kept})
    random.Random(7).shuffle(entries)
    out = PACKETS / f"look-{'-'.join(map(str, run_ids))}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "packet.json").write_text(json.dumps({"rubric": RUBRIC, "entries": entries}, indent=1, ensure_ascii=False))
    (out / "_key.json").write_text(json.dumps(key))
    print(f"[look] {len(entries)} entries in {out}/packet.json")


def import_grades(folder: str, grader: str) -> None:
    import pathlib
    folder = pathlib.Path(folder)
    key = json.loads((folder / "_key.json").read_text())
    grades = json.loads((folder / "grades.json").read_text())
    now = datetime.now(timezone.utc).isoformat()
    rows = [(*key[b], x, grader, int(v["looks_similar"]), int(v["different_meaning"]), int(v["fits_blank"]), now)
            for b, per in grades.items() if b in key for x, v in per.items()]
    con = connect()
    con.executemany("INSERT OR REPLACE INTO look_grades VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit()
    print(f"[look] {len(rows)} lookalike grades imported as '{grader}'")


def jev(run_ids: list, workers: int = 8) -> None:
    """Jev's P(natural) for each kept lookalike put in the word's blank (with the lookalike's own
    dictionary meaning): would a per-sentence Jev check catch the lookalikes that fit?"""
    con = connect()
    words = {w["word"]: w for w in dataset.load_words()}
    blanks = sentences()
    todo = [(r["run_id"], r["word"], x) for rid in run_ids
            for r in con.execute("SELECT run_id, word, kept FROM look_outputs WHERE run_id=? AND ok=1", (rid,))
            if r["word"] in blanks for x in json.loads(r["kept"])]

    def one(t):
        rid, word, x = t
        found = dictionary.lookup(x)
        want = lookalikes.POS.get(words[word]["pos"], words[word]["pos"])
        senses = (found or {}).get("senses", [])
        gloss = next((s["gloss"] for s in senses if s["pos"] == want), senses[0]["gloss"] if senses else "")
        try:
            p, row = typesafe.p_natural(x, gloss, blanks[word].replace(practice.BLANK, x))
            return (rid, word, x, p, row[5])
        except Exception as exc:
            print(f"[look] jev {x}: {exc}")
            return (rid, word, x, None, 0.0)
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, todo))
    con.executemany("INSERT OR REPLACE INTO look_jev VALUES (?,?,?,?,?)", rows)
    con.commit()
    print(f"[look] Jev scored {sum(r[3] is not None for r in rows)}/{len(rows)}; ${sum(r[4] for r in rows):.4f}")


def jev_report(grader: str = "claude-code") -> list:
    """How well Jev's score separates the lookalikes the grader says fit the blank, per cut-off."""
    rows = connect().execute("SELECT g.fits_blank, j.p_natural FROM look_grades g JOIN look_jev j USING (run_id, word, lookalike) "
                             "WHERE g.grader=? AND j.p_natural IS NOT NULL", (grader,)).fetchall()
    fits = [r["p_natural"] for r in rows if r["fits_blank"]]
    rest = [r["p_natural"] for r in rows if not r["fits_blank"]]
    lines = [f"{len(rows)} graded lookalikes with a Jev score: {len(fits)} fit the blank, {len(rest)} don't"]
    for cut in (0.05, 0.1, 0.2, 0.3, 0.5):
        lines.append(f"  drop when P(natural) ≥ {cut}: catches {sum(p >= cut for p in fits)}/{len(fits)} that fit · "
                     f"wrongly drops {sum(p >= cut for p in rest)}/{len(rest)} good ones")
    return lines


def report() -> list:
    """Per run: words that end with three good lookalikes (similar, different, not fitting the blank),
    and how many lookalikes fit the blank: the case a per-sentence Jev check would have to catch."""
    con = connect()
    lines = []
    for run in con.execute("SELECT * FROM look_runs ORDER BY id"):
        outs = con.execute("SELECT * FROM look_outputs WHERE run_id=?", (run["id"],)).fetchall()
        g = con.execute("SELECT * FROM look_grades WHERE run_id=?", (run["id"],)).fetchall()
        good = [x for x in g if x["looks_similar"] and x["different_meaning"] and not x["fits_blank"]]
        per_word = {}
        for x in good:
            per_word[x["word"]] = per_word.get(x["word"], 0) + 1
        n = len(outs)
        lines.append(f"{run['model_name']} (run {run['id']}): words with {lookalikes.COUNT} good lookalikes "
                     f"{sum(v == lookalikes.COUNT for v in per_word.values())}/{n} · graded {len(g)} · "
                     f"look similar {sum(x['looks_similar'] for x in g)} · very different {sum(x['different_meaning'] for x in g)} · "
                     f"FIT THE BLANK {sum(x['fits_blank'] for x in g)} · dropped by code "
                     f"{sum(len(json.loads(o['problems'])) for o in outs)} · ${sum(o['cost_usd'] for o in outs) / n:.5f}/word")
    return lines
