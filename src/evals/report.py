"""Leaderboard: every run on the current dataset version, cheap × fast × quality.
Prints a table and writes output/evals/leaderboard.html."""
import html as html_mod
import json
import pathlib
import statistics

from . import dataset, label, results

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PAGE = ROOT / "output" / "evals" / "leaderboard.html"


def pct(xs: list, q: float):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def summarize(con, run) -> dict:
    rows = con.execute("SELECT * FROM results WHERE run_id=?", (run["id"],)).fetchall()
    ok = [r for r in rows if r["ok"]]
    marks = con.execute("SELECT verdict FROM marks WHERE run_id=? AND verdict IS NOT NULL", (run["id"],)).fetchall()
    grades = con.execute("SELECT inventions, note_problems FROM grades WHERE run_id=?", (run["id"],)).fetchall()
    graded_marks = len(marks)
    v = lambda k: sum(m["verdict"] == k for m in marks) / graded_marks if graded_marks else None
    return {
        "run": run["id"], "model": run["model_name"], "pieces": f"{len(ok)}/{len(rows)}",
        "usd": statistics.mean(r["cost_usd"] for r in ok) if ok else None,
        "p50": pct([r["seconds"] for r in ok], .5), "p90": pct([r["seconds"] for r in ok], .9),
        "marks": statistics.mean(r["marks"] for r in ok) if ok else None,
        "coverage": statistics.mean(r["coverage"] for r in ok if r["coverage"] is not None)
                    if any(r["coverage"] is not None for r in ok) else None,
        "reasoning": sum(r["tokens_reasoning"] or 0 for r in ok),
        "graded": f"{len(grades)}/{len(ok)}", "idiomatic": v("idiomatic"), "wrong": v("wrong"),
        "inventions": (sum(len(json.loads(g["inventions"])) for g in grades) / len(grades)) if grades else None,
        "note_problems": (sum(len(json.loads(g["note_problems"])) for g in grades) / len(grades)) if grades else None,
    }


def fmt(x, kind):
    if x is None:
        return "—"
    return {"usd": f"${x:.5f}", "s": f"{x:.1f}s", "pct": f"{x:.0%}", "n": f"{x:.1f}", "d": f"{x:+.0%}"}[kind]


def report() -> None:
    con = results.connect()
    version = dataset.version()
    runs = con.execute("SELECT * FROM runs WHERE dataset=? AND finished_at IS NOT NULL ORDER BY id",
                       (version,)).fetchall()
    size = len(dataset.load())
    runs = [r for r in runs  # partial runs (--only smoke tests) don't compare
            if con.execute("SELECT count(*) FROM results WHERE run_id=?", (r["id"],)).fetchone()[0] == size]
    rows = [summarize(con, r) for r in runs]
    base_name = results.registry().get("baseline")
    base = next((r for r in reversed(rows) if r["model"] == base_name and r["usd"]), None)
    for r in rows:
        r["vs"] = (r["usd"] / base["usd"] - 1) if base and r["usd"] else None
    cols = [("Model", "model", None), ("Run", "run", None), ("Pieces ok", "pieces", None),
            ("$/piece", "usd", "usd"), ("vs baseline", "vs", "d"), ("p50", "p50", "s"), ("p90", "p90", "s"),
            ("Marks/piece", "marks", "n"), ("Coverage", "coverage", "pct"), ("Graded", "graded", None),
            ("Idiomatic", "idiomatic", "pct"), ("Wrong", "wrong", "pct"),
            ("Inventions/piece", "inventions", "n"), ("Note problems/piece", "note_problems", "n")]
    cell = lambda r, k, kind: fmt(r[k], kind) if kind else str(r[k])
    print(f"dataset {version}: {len(dataset.load())} pieces · baseline {base_name}")
    print(" | ".join(c[0] for c in cols))
    for r in rows:
        print(" | ".join(cell(r, k, kind) for _, k, kind in cols))
    ag = label.agreement(con)
    ag_line = (f"Grader vs founder on {ag['n']} words: {ag['exact']:.0%} exact agreement, "
               f"kappa {ag['kappa']:.2f} (3 labels), {ag['kappa_wrong']:.2f} (wrong vs not)"
               if ag["n"] else "Grader not yet checked against founder labels (python src/evals label).")
    print(ag_line)

    head = "".join(f"<th>{html_mod.escape(c[0])}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f"<td>{html_mod.escape(cell(r, k, kind))}</td>" for _, k, kind in cols) + "</tr>"
                   for r in rows)
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Model leaderboard</title>
<style>
:root {{ --bg:#faf8f4; --fg:#26221c; --muted:#6d675e; --line:#ddd5c8; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1c1a17; --fg:#eee8dd; --muted:#a39c90; --line:#3a352e; }} }}
body {{ font-family: -apple-system, sans-serif; background: var(--bg); color: var(--fg); padding: 1.5rem 16px; }}
.scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; font-size: .85rem; white-space: nowrap; }}
th, td {{ border-bottom: 1px solid var(--line); padding: .45rem .6rem; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--muted); font-weight: 600; }}
p {{ color: var(--muted); font-size: .88rem; max-width: 760px; }}
</style></head><body>
<h1>Rewrite-engine leaderboard</h1>
<p>Dataset {version}: {len(dataset.load())} pieces, full production pipeline, candidate model in every role.
$/piece = all calls (billed cost where the provider reports it). p50/p90 = seconds per piece.
Coverage = share of 25+-word paragraphs carrying a word. Idiomatic / Wrong = share of highlighted
words, per the fixed grader. {html_mod.escape(ag_line)}</p>
<div class="scroll"><table><tr>{head}</tr>{body}</table></div></body></html>""")
    print(f"wrote {PAGE}")
