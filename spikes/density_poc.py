"""Density PoC replay (2026-09-28): the founder's recent shares through the production
pipeline twice — as it runs today, and with poc=True (salvage drafts with off-list marks;
stricter-notes prompt). Same user word list and settings as the service. Reads
data/service.db read-only; writes output/density_poc.json.
Run: .venv/bin/python spikes/density_poc.py [n_pieces=20] [runs=2]"""
import json
import pathlib
import sqlite3
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from service import db, engine  # noqa: E402  (service.config loads .env.local)
import generate as G  # noqa: E402

USER = "u_152716439f0d463e"  # the founder's Apple account


def main(n: int, runs: int) -> None:
    con = sqlite3.connect(f"file:{ROOT / 'data' / 'service.db'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    words = db.learning_words(con, USER)
    menu = [w["word"] for w in words]
    seen, pieces = set(), []
    for p in con.execute("SELECT * FROM pieces WHERE user_id=? AND status='done' "
                         "ORDER BY created_at DESC", (USER,)):
        if p["source_text"] not in seen:
            seen.add(p["source_text"]); pieces.append(p)
        if len(pieces) == n:
            break
    wrapper, kwargs = engine.pipeline_args()
    env = engine.model_env()
    out = []
    for i, p in enumerate(pieces, 1):
        item = engine.user_item(p["id"], p["source"], p["url"], p["title"], p["source_text"])
        src_words = len(p["source_text"].split())
        for mode in ("prod", "poc"):
            for r in range(runs):
                G.CALL_LOG.clear()
                t0 = time.time()
                try:
                    res = G.generate_piece(None, item, wrapper, menu, env, words=words, record=False,
                                           poc=(mode == "poc"), **kwargs)
                    err = None
                except Exception as exc:
                    res, err = None, str(exc)[:300]
                calls = list(G.CALL_LOG)
                cost = sum(c[5] if c[5] is not None else
                           c[2] / 1e6 * engine.PRICES.get(c[1], {"in": 0})["in"]
                           + c[3] / 1e6 * engine.PRICES.get(c[1], {"out": 0})["out"] for c in calls)
                cov = (res or {}).get("coverage") or {}
                row = {"piece": p["id"], "title": p["title"], "source_words": src_words, "mode": mode,
                       "run": r, "error": err, "seconds": round(time.time() - t0, 1),
                       "calls": len(calls), "usd": round(cost, 5),
                       "words": res and res["words_used"], "n_words": res and len(res["words_used"]),
                       "stretches": cov.get("stretches"), "covered": cov.get("covered"),
                       "notes_dropped": cov.get("notes_dropped"),
                       "notes_kept": res and res["body"].count("<aside"),
                       "body": res and res["body"]}
                out.append(row)
                print(f"[poc] {i}/{len(pieces)} {p['id']} {src_words}w {mode}#{r}: "
                      f"{row['n_words']} words, notes kept {row['notes_kept']} dropped "
                      f"{row['notes_dropped']}, {row['calls']} calls, {row['seconds']}s ${row['usd']}"
                      + (f" ERROR {err}" if err else ""), flush=True)
                (ROOT / "output" / "density_poc.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20, int(sys.argv[2]) if len(sys.argv) > 2 else 2)
