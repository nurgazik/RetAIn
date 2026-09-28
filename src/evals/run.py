"""Run one registry model through the full production pipeline (generate_piece: rewrite,
idiom judge, fact judge, repair) on every golden piece. By default the candidate model plays
every role, fallback off, so $/piece and seconds/piece are exactly "what if we switched".
Roles can be separated (no engine code changes; done by routing calls here):
  checks=False   writer only: the pipeline's idiom + fact checks are skipped, so the writer's
                 raw output is graded (apples-to-apples writer comparison)
  checker=NAME   the writer is `name`, every check/repair call goes to registry model NAME
  defs=False     word-only prompts: writer and QC judge see the bare words, no definitions"""
import json
import time
from datetime import datetime, timezone

import generate as G
from bakeoff import load_env
from service import engine
from service.config import ENGINE_MODE

from . import dataset, results


def run_label(name: str, checks: bool = True, checker: str = None, defs: bool = True) -> str:
    return (name + (" [writer only]" if not checks else f" + checker {checker}" if checker else "")
            + ("" if defs else " [word only]"))


def route_roles(spec: dict, checks: bool, checker: str) -> dict:
    """Point generate.py's check calls at the chosen checker, or skip the checks.
    Returns {api model id: registry spec} for costing each call."""
    specs = {spec["model"]: spec}
    if not checks:
        G.run_judges = lambda *a, **k: ([], ([], []))
    elif checker:
        cspec = results.spec(checker)
        specs[cspec["model"]] = cspec
        chk, writer_call = results.primary_for(cspec), G.call_model

        def routed(system, user, env, purpose="generate"):
            if purpose == "generate":
                return writer_call(system, user, env, purpose)
            t0 = time.time()
            r = chk["call"](chk["model"], system, user, env[chk["key"]], chk["params"])
            G.CALL_LOG.append((purpose, chk["model"], r.get("tokens_in", 0), r.get("tokens_out", 0),
                               int((time.time() - t0) * 1000), r.get("cost"), r.get("tokens_reasoning", 0)))
            return r["text"], chk["model"]
        G.call_model = routed  # qc_gate / fact_qc / repair look call_model up at call time
    return specs


def run(name: str, only: list = None, resume: int = None, checks: bool = True, checker: str = None,
        defs: bool = True) -> int:
    spec = results.spec(name)
    pieces = dataset.load()
    if only:
        pieces = [p for p in pieces if any(o in p["id"] for o in only)]
    words = dataset.load_words()
    chosen = [w["word"] for w in words]
    wrapper, kwargs = engine.pipeline_args()
    env = load_env()
    con = results.connect()

    label = run_label(name, checks, checker, defs)
    if resume:
        run_id = resume
        done = {r[0] for r in con.execute("SELECT piece_id FROM results WHERE run_id=? AND ok=1", (run_id,))}
        con.execute("DELETE FROM calls WHERE run_id=? AND piece_id NOT IN "
                    "(SELECT piece_id FROM results WHERE run_id=? AND ok=1)", (run_id, run_id))  # failed pieces re-run
        con.commit()  # never hold the write lock across model calls: parallel runs share this db
    else:
        run_id = con.execute(
            "INSERT INTO runs (model_name, spec, dataset, engine_mode, engine, commit_id, started_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (label, json.dumps({**spec, "checks": checks, "checker": checker, "defs": defs}), dataset.version(), ENGINE_MODE,
             results.engine_fingerprint(ENGINE_MODE),
             results.git_commit(), datetime.now(timezone.utc).isoformat())).lastrowid
        con.commit()
        done = set()

    G.PRIMARY, G.FALLBACK = results.primary_for(spec), None
    G.DEFS_IN_PROMPT = defs
    specs = route_roles(spec, checks, checker)
    print(f"[evals] run {run_id}: {label} on {len(pieces)} pieces ({ENGINE_MODE} mode)")
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
        for purpose, model, tin, tout, ms, billed, reasoning in (c[:7] for c in calls):
            c = results.call_cost(specs.get(model, spec), tin, tout, billed)
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
