"""Checker test: how well does a model do the pipeline's word check (D19 idiom judge)?
Every graded piece's highlighted words go to the candidate with production's own prompt
(generate.QC_SYSTEM). Its pass/fail per word is compared with gold labels: the fixed
grader's verdicts, or the founder's blind labels. What matters:
  caught      share of gold-"wrong" words it rejects (misuse that would otherwise ship)
  false-reject share of gold-"idiomatic" words it rejects (good words lost)
"""
import json
import re
from datetime import datetime, timezone

import generate as G
from bakeoff import load_env

from . import dataset, results

SCHEMA = """
CREATE TABLE IF NOT EXISTS judge_evals (
    checker TEXT, gold TEXT, dataset TEXT, n_wrong INTEGER, caught INTEGER,
    n_idiomatic INTEGER, false_rejects INTEGER, n_acceptable INTEGER, acceptable_rejected INTEGER,
    failed_calls INTEGER, cost_usd REAL, seconds REAL, at TEXT
);
"""


def judge(name: str, gold: str = "grader") -> None:
    spec = results.spec(name)
    chk = results.primary_for(spec)
    env = load_env()
    defs_all = {w["word"]: w["definition"] for w in dataset.load_words()}
    con = results.connect()
    con.executescript(SCHEMA)
    col = "verdict" if gold == "grader" else "human"
    pieces = con.execute(f"SELECT DISTINCT m.run_id, m.piece_id, r.body FROM marks m JOIN results r "
                         f"ON r.run_id=m.run_id AND r.piece_id=m.piece_id WHERE m.{col} IS NOT NULL").fetchall()
    tally = {"wrong": [0, 0], "idiomatic": [0, 0], "acceptable": [0, 0]}  # [n, rejected]
    failed, cost, secs = 0, 0.0, 0.0
    for p in pieces:
        marks = con.execute(f"SELECT n, word, {col} AS gold FROM marks WHERE run_id=? AND piece_id=? "
                            f"AND {col} IS NOT NULL ORDER BY n", (p["run_id"], p["piece_id"])).fetchall()
        body = re.sub(r"<mark[^>]*>", "<mark>", p["body"])  # as qc_gate sees it (before tooltips)
        defs = {w: d for w, d in defs_all.items()
                if any(m["word"].lower().startswith(w[:6].lower()) for m in marks)}
        word_list = "\n".join(f"- {w}: {d}" for w, d in defs.items())
        t0 = __import__("time").time()
        try:
            out = chk["call"](chk["model"], G.QC_SYSTEM, f"WORD LIST:\n{word_list}\n\nTEXT:\n{body}",
                              env[chk["key"]], chk["params"])
            raw = re.sub(r"^```(json)?\s*|\s*```$", "", out["text"].strip(), flags=re.M).strip()
            verdicts = json.loads(raw)["verdicts"]
        except Exception as exc:
            failed += 1
            print(f"[judge] {p['piece_id']}: checker failed ({exc})")
            continue
        secs += __import__("time").time() - t0
        cost += results.call_cost(spec, out["tokens_in"], out["tokens_out"], out.get("cost"))
        # match verdicts to marks by word, in document order (a word can be marked twice)
        pool = [(v.get("word", "").strip().lower(), v.get("ok", True)) for v in verdicts]
        for m in marks:
            w = m["word"].lower()
            hit = next((i for i, (vw, _) in enumerate(pool) if vw[:6] == w[:6]), None)
            rejected = (not pool.pop(hit)[1]) if hit is not None else False
            if m["gold"] in tally:
                tally[m["gold"]][0] += 1
                tally[m["gold"]][1] += int(rejected)
    row = (name, gold, dataset.version(), *tally["wrong"], *tally["idiomatic"], *tally["acceptable"],
           failed, cost, secs, datetime.now(timezone.utc).isoformat())
    con.execute("INSERT INTO judge_evals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
    con.commit()
    pct = lambda k: f"{tally[k][1]}/{tally[k][0]}" + (f" ({tally[k][1] / tally[k][0]:.0%})" if tally[k][0] else "")
    print(f"[judge] {name} vs {gold} labels on {len(pieces)} pieces: caught wrong {pct('wrong')}, "
          f"rejected idiomatic {pct('idiomatic')}, rejected acceptable {pct('acceptable')}; "
          f"{failed} failed calls, ${cost:.4f}")
