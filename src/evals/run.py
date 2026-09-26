"""Run one registry model through the full production pipeline (generate_piece: rewrite,
idiom judge, fact judge, repair) on every golden piece. The candidate model plays every
role, fallback off, so $/piece and seconds/piece are exactly "what if we switched"."""
import json
import time
from datetime import datetime, timezone

import generate as G
from bakeoff import load_env
from service import engine
from service.config import ENGINE_MODE

from . import dataset, results


def run(name: str, only: list = None, resume: int = None) -> int:
    spec = results.spec(name)
    pieces = dataset.load()
    if only:
        pieces = [p for p in pieces if any(o in p["id"] for o in only)]
    words = dataset.load_words()
    chosen = [w["word"] for w in words]
    wrapper, kwargs = engine.pipeline_args()
    env = load_env()
    con = results.connect()

    if resume:
        run_id = resume
        done = {r[0] for r in con.execute("SELECT piece_id FROM results WHERE run_id=?", (run_id,))}
    else:
        run_id = con.execute(
            "INSERT INTO runs (model_name, spec, dataset, engine_mode, engine, commit_id, started_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (name, json.dumps(spec), dataset.version(), ENGINE_MODE, results.engine_fingerprint(ENGINE_MODE),
             results.git_commit(), datetime.now(timezone.utc).isoformat())).lastrowid
        con.commit()
        done = set()

    G.PRIMARY, G.FALLBACK = results.primary_for(spec), None
    print(f"[evals] run {run_id}: {name} on {len(pieces)} pieces ({ENGINE_MODE} mode)")
    for i, p in enumerate(pieces, 1):
        if p["id"] in done:
            continue
        item = engine.user_item(f"eval:{p['id']}", p["source"], p["url"], p["title"], p["text"])
        G.CALL_LOG.clear()
        t0 = time.time()
        try:
            r = G.generate_piece(None, item, wrapper, chosen, env, words=words, record=False, **kwargs)
            err = None
        except Exception as exc:
            detail = exc.read().decode(errors="replace")[:300] if hasattr(exc, "read") else ""
            r, err = None, f"{type(exc).__name__}: {exc} {detail}".strip()[:500]
        seconds = time.time() - t0
        calls = list(G.CALL_LOG)
        cost = 0.0
        for purpose, model, tin, tout, ms, billed, reasoning in calls:
            c = results.call_cost(spec, tin, tout, billed)
            cost += c
            con.execute("INSERT INTO calls VALUES (?,?,?,?,?,?,?,?,?)",
                        (run_id, p["id"], purpose, model, tin, tout, reasoning, ms, c))
        cov = (r or {}).get("coverage") or {}
        coverage = cov.get("coverage")
        if coverage is None and cov.get("stretches"):  # D40 anchor trial: ~120-word stretches
            coverage = round(cov.get("covered", 0) / cov["stretches"], 2)
        con.execute(
            "INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, p["id"], int(r is not None), err, r and r["title"], r and r["body"],
             round(seconds, 2), cost, sum(c[2] for c in calls), sum(c[3] for c in calls),
             sum(c[6] for c in calls), len(calls), r and r["marks"], coverage,
             json.dumps({k: r[k] for k in ("attempts", "qc_rejected", "invented_numbers",
                                           "invented_unmarked", "word_count", "words_used")}
                        | {"coverage": cov, "source_words": p["words"]} if r else {})))
        con.commit()
        status = f"{r['marks']} marks, coverage {coverage}" if r else f"FAILED {err}"
        print(f"[evals] {i}/{len(pieces)} {p['id']}: {seconds:.1f}s ${cost:.5f} {status}")
    con.execute("UPDATE runs SET finished_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), run_id))
    con.commit()
    return run_id
