"""Model evals: cheap × fast × quality for the rewrite engine, on a frozen golden set.

  .venv/bin/python src/evals build                 add golden pieces (existing ones stay frozen)
  .venv/bin/python src/evals add <openrouter-slug> [name] ['{"params": ...}']
                                                   register a new OpenRouter model at its list price
  .venv/bin/python src/evals run <name> [--only id,id] [--resume RUN] [--no-checks | --checker NAME] [--no-defs]
                                                   full pipeline on every golden piece;
                                                   --resume re-runs a run's failed/missing pieces;
                                                   --no-checks: writer only; --checker: checks by NAME;
                                                   --no-defs: word-only prompts (no definitions)
  .venv/bin/python src/evals judge <name> [--gold grader|human]
                                                   score a model as the word checker against gold labels
  .venv/bin/python src/evals grade <run_id>        fixed API grader scores words + inventions
  .venv/bin/python src/evals grade --export R1 R2  blind packets for grading in Claude Code (no API cost)
  .venv/bin/python src/evals grade --import <dir> <grader-name>   load those verdicts
  .venv/bin/python src/evals label [N]             blind labelling page for the founder
  .venv/bin/python src/evals labels <labels.json>  import the founder's labels
  .venv/bin/python src/evals report                leaderboard (terminal + output/evals/leaderboard.html)

Sentence judge (TD-20, D53; golden set data/evals/golden/sentences.json):
  .venv/bin/python src/evals sentences page        founder page: write sentences + blind-label the rest
  .venv/bin/python src/evals sentences import <file> [rater]
                                                   load that page's export (rater defaults to founder)
  .venv/bin/python src/evals sentences export      founder-written sentences → blind packet for a second rater
  .venv/bin/python src/evals sentences judge <name>
                                                   run a registry model as the judge (scored in `report`)
  .venv/bin/python src/evals sentences feedback-export <run> [run ...]
                                                   blind packet of those runs' reasons + fixes (D55)
  .venv/bin/python src/evals sentences feedback-import <folder> <grader>
                                                   load grades.json written into that folder

Fill-in sentence writer (D55; prompts/exercises/fill-sentence.md):
  .venv/bin/python src/evals fill run <name>        one sentence per golden word + blank check + Jev gate score
  .venv/bin/python src/evals fill export <run> [run ...]   blind packet (natural / right sense / clear blank)
  .venv/bin/python src/evals fill import <folder> <grader>
  .venv/bin/python src/evals fill report

Lookalike writer for the fill-in hint (D58; prompts/exercises/lookalikes.md):
  .venv/bin/python src/evals look run <name>        three lookalikes per golden word + dictionary check
  .venv/bin/python src/evals look export <run> [run ...]   blind packet (similar / different / fits the blank)
  .venv/bin/python src/evals look import <folder> <grader>
  .venv/bin/python src/evals look report
  .venv/bin/python src/evals look jev <run> [run ...]      Jev score of each lookalike in the blank
  .venv/bin/python src/evals look jev-report               does Jev catch the ones that fit?

New model, end to end: add → run → grade → report.
"""
import json
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent
sys.path[0] = str(SRC)  # import siblings as evals.*, never shadow src/ modules

from evals import dataset, fillin, grade, judge, label, lookalike, report, results, run, sentences  # noqa: E402


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
        checker = args[args.index("--checker") + 1] if "--checker" in args else None
        checks, defs = "--no-checks" not in args, "--no-defs" not in args
        if resume:  # resume with the run's own settings
            row = results.connect().execute("SELECT spec FROM runs WHERE id=?", (resume,)).fetchone()
            rs = json.loads(row[0])
            name, checks, checker, defs = rs["name"], rs.get("checks", True), rs.get("checker"), rs.get("defs", True)
        else:
            name = args[0]
        print(f"run id {run.run(name, only, resume, checks, checker, defs)}")
    elif cmd == "judge":
        judge.judge(args[0], args[args.index("--gold") + 1] if "--gold" in args else "grader")
    elif cmd == "grade" and args[:1] == ["--export"]:
        grade.export_batch([int(a) for a in args[1:]])
    elif cmd == "grade" and args[:1] == ["--import"]:
        grade.import_batch(args[1], args[2])
    elif cmd == "grade":
        grade.grade_run(int(args[0]), redo="--redo" in args)
    elif cmd == "label":
        label.write_page(int(args[0]) if args else 150)
    elif cmd == "labels":
        label.import_labels(args[0])
    elif cmd == "report":
        report.report()
    elif cmd == "sentences" and args[:1] == ["page"]:
        sentences.write_page()
    elif cmd == "sentences" and args[:1] == ["import"]:
        sentences.import_input(args[1], args[2] if len(args) > 2 else "founder")
    elif cmd == "sentences" and args[:1] == ["export"]:
        sentences.export_packet()
    elif cmd == "sentences" and args[:1] == ["judge"]:
        sentences.judge(args[1])
    elif cmd == "sentences" and args[:1] == ["feedback-export"]:
        sentences.feedback_export([int(a) for a in args[1:]])
    elif cmd == "sentences" and args[:1] == ["feedback-import"]:
        sentences.feedback_import(args[1], args[2])
    elif cmd == "fill" and args[:1] == ["run"]:
        fillin.run(args[1])
    elif cmd == "fill" and args[:1] == ["export"]:
        fillin.export([int(a) for a in args[1:]])
    elif cmd == "fill" and args[:1] == ["import"]:
        fillin.import_grades(args[1], args[2])
    elif cmd == "fill" and args[:1] == ["report"]:
        print("\n".join(fillin.report()))
    elif cmd == "look" and args[:1] == ["run"]:
        lookalike.run(args[1])
    elif cmd == "look" and args[:1] == ["export"]:
        lookalike.export([int(a) for a in args[1:]])
    elif cmd == "look" and args[:1] == ["import"]:
        lookalike.import_grades(args[1], args[2])
    elif cmd == "look" and args[:1] == ["jev"]:
        lookalike.jev([int(a) for a in args[1:]])
    elif cmd == "look" and args[:1] == ["jev-report"]:
        print("\n".join(lookalike.jev_report()))
    elif cmd == "look" and args[:1] == ["report"]:
        print("\n".join(lookalike.report()))
    else:
        print(__doc__)


main(sys.argv[1:])
