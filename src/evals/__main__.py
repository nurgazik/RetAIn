"""Model evals: cheap × fast × quality for the rewrite engine, on a frozen golden set.

  .venv/bin/python src/evals build                 add golden pieces (existing ones stay frozen)
  .venv/bin/python src/evals add <openrouter-slug> [name] ['{"params": ...}']
                                                   register a new OpenRouter model at its list price
  .venv/bin/python src/evals run <name> [--only id,id] [--resume RUN]
                                                   full pipeline on every golden piece;
                                                   --resume re-runs a run's failed/missing pieces
  .venv/bin/python src/evals grade <run_id>        fixed grader scores words + inventions
  .venv/bin/python src/evals label [N]             blind labelling page for the founder
  .venv/bin/python src/evals labels <labels.json>  import the founder's labels
  .venv/bin/python src/evals report                leaderboard (terminal + output/evals/leaderboard.html)

New model, end to end: add → run → grade → report.
"""
import json
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent
sys.path[0] = str(SRC)  # import siblings as evals.*, never shadow src/ modules

from evals import dataset, grade, label, report, results, run  # noqa: E402


def main(argv: list) -> None:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    if cmd == "build":
        dataset.build()
    elif cmd == "add":
        params = json.loads(args[2]) if len(args) > 2 else None
        print(results.add_openrouter(args[0], args[1] if len(args) > 1 else None, params))
    elif cmd == "run":
        only = args[args.index("--only") + 1].split(",") if "--only" in args else None
        resume = int(args[args.index("--resume") + 1]) if "--resume" in args else None
        name = resume and results.connect().execute("SELECT model_name FROM runs WHERE id=?", (resume,)).fetchone()[0]
        print(f"run id {run.run(name or args[0], only, resume)}")
    elif cmd == "grade":
        grade.grade_run(int(args[0]), redo="--redo" in args)
    elif cmd == "label":
        label.write_page(int(args[0]) if args else 150)
    elif cmd == "labels":
        label.import_labels(args[0])
    elif cmd == "report":
        report.report()
    else:
        print(__doc__)


main(sys.argv[1:])
