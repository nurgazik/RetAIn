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


def connect():
    con = results.connect()
    con.executescript(SCHEMA)
    return con


def prompt_hash() -> str:
    return hashlib.sha1(practice.FILL_PROMPT.encode()).hexdigest()[:10]


def run(name: str, workers: int = 6) -> int:
    spec = results.spec(name)
    chk = results.primary_for(spec)
    env = load_env()
    words = dataset.load_words()

    def one(w):
        t0 = time.time()
        try:
            out = chk["call"](chk["model"], practice.FILL_PROMPT, f"Target word: {w['word']} — {w['definition']}",
                              env[chk["key"]], chk["params"])
            raw = out["text"]
            d = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
            sentence, answer = d["sentence"].strip(), d["answer"].strip()
            blank_ok = bool(answer.lower().startswith(practice.stem(w["word"])) and practice._blank(sentence, answer))
            p = typesafe.p_natural(w["word"], w["definition"], sentence)[0] if blank_ok else None
            cost = results.call_cost(spec, out["tokens_in"], out["tokens_out"], out.get("cost"))
            return (w["word"], 1, None, sentence, answer, int(blank_ok), p, cost, time.time() - t0)
        except Exception as exc:
            return (w["word"], 0, str(exc)[:300], None, None, 0, None, 0.0, time.time() - t0)
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, words))
    con = connect()
    rid = con.execute("INSERT INTO fill_runs (model_name, prompt, at) VALUES (?,?,?)",
                      (name, prompt_hash(), datetime.now(timezone.utc).isoformat())).lastrowid
    con.executemany("INSERT INTO fill_outputs VALUES (?,?,?,?,?,?,?,?,?,?)", [(rid, *r) for r in rows])
    con.commit()
    ok = [r for r in rows if r[1]]
    gate = [r for r in ok if r[5] and r[6] is not None and r[6] >= practice.NATURAL_AT]
    print(f"[fill] run {rid} {name}: {len(ok)}/{len(rows)} answered, {sum(r[5] for r in ok)} usable blanks, "
          f"{len(gate)} pass the Jev gate (≥ {practice.NATURAL_AT}); ${sum(r[7] for r in rows):.4f}")
    return rid


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
