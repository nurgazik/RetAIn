"""Eval harness: scoring helpers and the runner, with the pipeline stubbed (no model calls)."""
import json

import pytest

import bakeoff
from evals import grade, label, results


WORDS = [{"word": "bolster", "definition": "to support"}, {"word": "candor", "definition": "honesty"}]


def test_merge_is_deep_and_overrides():
    body = {"a": 1, "cfg": {"x": 1, "y": 2}}
    assert bakeoff.merge(body, {"cfg": {"y": 3}, "b": 2}) == {"a": 1, "cfg": {"x": 1, "y": 3}, "b": 2}


def test_extract_marks_numbers_in_order_and_flags_notes():
    body = ('<p>Aid will <mark data-def="to support">bolster</mark> the plan. It works.</p>'
            '<aside class="supplement"><mark>Candor</mark> matters here.</aside>')
    text, marks = grade.extract_marks(body, WORDS)
    assert text == "Aid will [1]bolster[/1] the plan. It works.\n\nNOTE: [2]Candor[/2] matters here."
    assert [(m["n"], m["target"], m["in_note"]) for m in marks] == [(1, "bolster", False), (2, "candor", True)]
    assert marks[0]["sentence"] == "Aid will bolster the plan."


def test_kappa():
    assert label.kappa([("a", "a"), ("b", "b")]) == 1.0
    assert label.kappa([("a", "b"), ("b", "a")]) == -1.0
    assert label.kappa([]) is None


def test_call_cost_prefers_billed():
    spec = {"in": 1.0, "out": 10.0}
    assert results.call_cost(spec, 1_000_000, 0, None) == 1.0
    assert results.call_cost(spec, 1_000_000, 0, 0.002) == 0.002


def test_run_records_cost_time_and_failures(tmp_path, monkeypatch):
    from evals import dataset, run
    import generate as G
    monkeypatch.setattr(results, "DB_PATH", tmp_path / "e.db")
    pieces = [{"id": "p1", "source": "t", "url": "", "title": "T", "text": "x " * 200, "words": 200},
              {"id": "p2", "source": "t", "url": "", "title": "T", "text": "y " * 200, "words": 200}]
    monkeypatch.setattr(dataset, "load", lambda: pieces)
    monkeypatch.setattr(dataset, "load_words", lambda: WORDS)
    monkeypatch.setattr(dataset, "version", lambda p=None: "v1")
    spec = {"name": "m", "provider": "gemini", "model": "m", "in": 1.0, "out": 10.0, "params": {}}
    monkeypatch.setattr(results, "spec", lambda name: spec)

    def fake(con, item, wrapper, chosen, env, **kw):
        if item["id"] == "eval:p2":
            raise RuntimeError("boom")
        G.CALL_LOG.append(("generate", "m", 1000, 100, 5, None, 0))
        G.CALL_LOG.append(("qc", "m", 500, 10, 5, 0.0005, 0))
        return {"title": "T", "body": "<p>We <mark>bolster</mark> it.</p>", "marks": 1, "words_used": ["bolster"],
                "word_count": 3, "qc_rejected": [], "invented_numbers": [], "invented_unmarked": [],
                "attempts": 1, "coverage": {"coverage": 1.0, "tiers": {}, "eligible_paragraphs": 1}}
    monkeypatch.setattr(G, "generate_piece", fake)
    monkeypatch.setattr(G, "PRIMARY", G.PRIMARY)  # restored after the test: run() swaps both
    monkeypatch.setattr(G, "FALLBACK", G.FALLBACK)

    run_id = run.run("m")
    con = results.connect()
    rows = {r["piece_id"]: r for r in con.execute("SELECT * FROM results WHERE run_id=?", (run_id,))}
    assert rows["p1"]["ok"] == 1 and rows["p1"]["cost_usd"] == pytest.approx(0.001 + 0.001 + 0.0005)
    assert rows["p2"]["ok"] == 0 and "boom" in rows["p2"]["error"]
    assert json.loads(rows["p1"]["metrics"])["source_words"] == 200
    assert G.FALLBACK is None  # evals never fall back: a failing model must show as failing
