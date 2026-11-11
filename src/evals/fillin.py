"""Fill-in sentence writer eval (D55; flow-fill-in-the-word, eval-fill-sentence diagram).
Each candidate writes one fill-in sentence per golden word with the production prompt; code checks
the blank works and records Jev's naturalness score (the production gate); a blind packet is graded
on natural / right sense / clear blank."""
import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from bakeoff import load_env
from service import practice, typesafe

from . import dataset, results
from .sentences import PACKETS

SCHEMA = """
CREATE TABLE IF NOT EXISTS fill_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT NOT NULL, prompt TEXT NOT NULL, at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fill_outputs (
    run_id INTEGER NOT NULL, word TEXT NOT NULL, ok INTEGER NOT NULL, error TEXT,
    sentence TEXT, answer TEXT, blank_ok INTEGER, p_natural REAL, cost_usd REAL, seconds REAL,
    PRIMARY KEY (run_id, word)
);
CREATE TABLE IF NOT EXISTS fill_variety (
    vrun TEXT NOT NULL, word TEXT NOT NULL, i INTEGER NOT NULL, topic TEXT, sentence TEXT, blank_ok INTEGER,
    p_natural REAL, PRIMARY KEY (vrun, word, i)
);
CREATE TABLE IF NOT EXISTS fill_grades (
    run_id INTEGER NOT NULL, word TEXT NOT NULL, grader TEXT NOT NULL,
    natural INTEGER, right_sense INTEGER, clear_blank INTEGER, at TEXT NOT NULL,
    PRIMARY KEY (run_id, word, grader)
);
"""
RUBRIC = """Each entry is a fill-in-the-blank exercise for an advanced English learner: a sentence with the
target word blanked, the hidden answer, and the word's meaning. For each entry answer:
  natural      true if the full sentence (answer filled in) is natural English a careful native writer would write.
  right_sense  true if the word is used in the meaning given.
  clear_blank  true if the context makes this word clearly the best fit, so a learner who knows it can recall
               it (not just one of several equally good synonyms).
Write {"<id>": {"natural": b, "right_sense": b, "clear_blank": b}, ...} to grades.json."""


PROMPT, TOPICS = practice.FILL_PROMPT, True  # production's writer: its prompt, settings rotating (D73)


def use(prompt: str | None = None, topics: bool | None = None) -> None:
    """Another writer prompt (a file), or settings off — e.g. production's previous writer for a baseline."""
    global PROMPT, TOPICS
    if prompt:
        PROMPT = open(prompt).read()
    if topics is not None:
        TOPICS = topics


def connect():
    con = results.connect()
    con.executescript(SCHEMA)
    for stmt in ("ALTER TABLE fill_runs ADD COLUMN topics INTEGER", "ALTER TABLE fill_outputs ADD COLUMN topic TEXT"):
        try:  # runs before D73 had no settings
            con.execute(stmt)
        except Exception:
            pass
    return con


def prompt_hash() -> str:
    return hashlib.sha1(PROMPT.encode()).hexdigest()[:10]


def write(chk: dict, env: dict, w: dict, topics: list | None) -> tuple:
    """One sentence as production writes it → (raw output, sentence, answer, blank_ok, p_natural)."""
    out = chk["call"](chk["model"], PROMPT, practice.fill_message(w["word"], w["definition"], topics),
                      env[chk["key"]], chk["params"])
    raw = out["text"]
    d = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    sentence, answer = d["sentence"].strip(), d["answer"].strip()
    blank_ok = bool(answer.lower().startswith(practice.stem(w["word"])) and practice._blank(sentence, answer))
    p = typesafe.p_natural(w["word"], w["definition"], sentence)[0] if blank_ok else None
    return out, sentence, answer, blank_ok, p


def run(name: str, workers: int = 6) -> int:
    spec = results.spec(name)
    chk = results.primary_for(spec)
    env = load_env()
    words = dataset.load_words()

    def one(w):
        t0 = time.time()
        topics = practice.topics_for(w["word"], 0) if TOPICS else None  # a word's first bank sentence
        topic = " | ".join(topics) if topics else None
        try:
            out, sentence, answer, blank_ok, p = write(chk, env, w, topics)
            cost = results.call_cost(spec, out["tokens_in"], out["tokens_out"], out.get("cost"))
            return (w["word"], 1, None, sentence, answer, int(blank_ok), p, cost, time.time() - t0, topic)
        except Exception as exc:
            return (w["word"], 0, str(exc)[:300], None, None, 0, None, 0.0, time.time() - t0, topic)
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, words))
    con = connect()
    rid = con.execute("INSERT INTO fill_runs (model_name, prompt, at, topics) VALUES (?,?,?,?)",
                      (name, prompt_hash(), datetime.now(timezone.utc).isoformat(), int(TOPICS))).lastrowid
    con.executemany("INSERT INTO fill_outputs (run_id, word, ok, error, sentence, answer, blank_ok, p_natural, "
                    "cost_usd, seconds, topic) VALUES (?,?,?,?,?,?,?,?,?,?,?)", [(rid, *r) for r in rows])
    con.commit()
    ok = [r for r in rows if r[1]]
    gate = [r for r in ok if r[5] and r[6] is not None and r[6] >= practice.NATURAL_AT]
    print(f"[fill] run {rid} {name}: {len(ok)}/{len(rows)} answered, {sum(r[5] for r in ok)} usable blanks, "
          f"{len(gate)} pass the Jev gate (≥ {practice.NATURAL_AT}); ${sum(r[7] for r in rows):.4f}")
    return rid


def opening(sentence: str) -> str:
    """The first four words: near-copies ("The young intern had the…") share them."""
    return " ".join(sentence.lower().split()[:4])


def variety(name: str, n_words: int = 10, k: int = 5, workers: int = 6) -> str:
    """k sentences for each of the first n_words golden words, as a word's 1st..k-th bank sentences would be
    written (settings rotating when on). Reports distinct openings per word and the Jev gate rate (D73)."""
    chk = results.primary_for(results.spec(name))
    env = load_env()
    jobs = [(w, i) for w in dataset.load_words()[:n_words] for i in range(k)]

    def one(job):
        w, i = job
        topics = practice.topics_for(w["word"], i) if TOPICS else None
        topic = " | ".join(topics) if topics else None
        try:
            _, sentence, _, blank_ok, p = write(chk, env, w, topics)
            return (w["word"], i, topic, sentence, int(blank_ok), p)
        except Exception as exc:
            return (w["word"], i, topic, f"ERROR {str(exc)[:200]}", 0, None)
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, jobs))
    vrun = f"{name} · prompt {prompt_hash()} · settings {'on' if TOPICS else 'off'} · " \
           f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}"
    con = connect()
    con.executemany("INSERT INTO fill_variety VALUES (?,?,?,?,?,?,?)", [(vrun, *r) for r in rows])
    con.commit()
    by_word = {}
    for r in rows:
        by_word.setdefault(r[0], []).append(r)
    distinct = [len({opening(r[3]) for r in rs}) for rs in by_word.values()]
    gate = sum(1 for r in rows if r[5] is not None and r[5] >= practice.NATURAL_AT)
    line = (f"{vrun}: {len(rows)} sentences, {len(by_word)} words · distinct openings per word "
            f"{sum(distinct) / len(distinct):.1f} of {k} (min {min(distinct)}) · usable blanks "
            f"{sum(r[4] for r in rows)}/{len(rows)} · pass Jev gate {gate}/{len(rows)}")
    print(line)
    return line


def export(run_ids: list) -> None:
    con = connect()
    defs = {w["word"]: w["definition"] for w in dataset.load_words()}
    entries, key = [], {}
    for rid in run_ids:
        for r in con.execute("SELECT * FROM fill_outputs WHERE run_id=? AND ok=1 AND blank_ok=1", (rid,)):
            b = hashlib.sha1(f"{rid}:{r['word']}".encode()).hexdigest()[:8]
            key[b] = [rid, r["word"]]
            entries.append({"id": b, "word": r["word"], "definition": defs[r["word"]],
                            "exercise": practice._blank(r["sentence"], r["answer"]), "answer": r["answer"]})
    random.Random(5).shuffle(entries)
    out = PACKETS / f"fill-{'-'.join(map(str, run_ids))}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "packet.json").write_text(json.dumps({"rubric": RUBRIC, "entries": entries}, indent=1, ensure_ascii=False))
    (out / "_key.json").write_text(json.dumps(key))
    print(f"[fill] {len(entries)} entries in {out}/packet.json")


def import_grades(folder: str, grader: str) -> None:
    import pathlib
    folder = pathlib.Path(folder)
    key = json.loads((folder / "_key.json").read_text())
    grades = json.loads((folder / "grades.json").read_text())
    con = connect()
    now = datetime.now(timezone.utc).isoformat()
    con.executemany("INSERT OR REPLACE INTO fill_grades VALUES (?,?,?,?,?,?,?)",
                    [(*key[b], grader, int(v["natural"]), int(v["right_sense"]), int(v["clear_blank"]), now)
                     for b, v in grades.items() if b in key])
    con.commit()
    print(f"[fill] {len(grades)} grades imported as '{grader}'")


def report() -> list:
    """Per run: of all 51 words, how many end as a good exercise — usable blank, all three grades
    true — and how many of those the Jev gate lets through (what would ship)."""
    con = connect()
    lines = []
    for run in con.execute("SELECT * FROM fill_runs ORDER BY id"):
        rows = con.execute("SELECT o.*, g.natural, g.right_sense, g.clear_blank FROM fill_outputs o LEFT JOIN fill_grades g "
                           "ON g.run_id=o.run_id AND g.word=o.word WHERE o.run_id=?", (run["id"],)).fetchall()
        good = [r for r in rows if r["natural"] and r["right_sense"] and r["clear_blank"]]
        gated = [r for r in rows if r["p_natural"] is not None and r["p_natural"] >= practice.NATURAL_AT]
        bad_through = [r for r in gated if r["natural"] is not None and not (r["natural"] and r["right_sense"])]
        n = len(rows)
        lines.append(f"{run['model_name']} (run {run['id']}): good exercises {len(good)}/{n} · usable blanks "
                     f"{sum(r['blank_ok'] for r in rows)}/{n} · pass Jev gate {len(gated)} · unnatural or wrong-sense "
                     f"that pass the gate {len(bad_through)} · ${sum(r['cost_usd'] for r in rows) / n:.5f}/sentence")
    return lines
