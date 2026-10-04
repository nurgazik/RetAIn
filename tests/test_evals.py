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


def test_extract_marks_flags_inline_notes():
    body = ('<p>The plan held. <span class="note supplement" data-tier="supplement">Such aid can '
            '<mark data-def="x">bolster</mark> morale.</span></p>')
    text, marks = grade.extract_marks(body, WORDS)
    assert "(NOTE: Such aid can [1]bolster[/1] morale.)" in text
    assert marks[0]["in_note"] is True


def test_route_roles_sends_checks_to_checker(monkeypatch):
    import generate as G
    from evals import run
    monkeypatch.setattr(G, "call_model", G.call_model)
    monkeypatch.setattr(G, "run_judges", G.run_judges)
    specs = {"w": {"name": "w", "provider": "gemini", "model": "w-model", "in": 1, "out": 1, "params": {}},
             "c": {"name": "c", "provider": "gemini", "model": "c-model", "in": 2, "out": 2, "params": {}}}
    monkeypatch.setattr(results, "spec", lambda n: specs[n])
    seen = []
    monkeypatch.setattr(results, "primary_for", lambda s: {
        "model": s["model"], "key": "K", "params": {},
        "call": lambda model, system, user, key, params: seen.append(model) or {"text": "ok", "tokens_in": 1, "tokens_out": 1}})
    writer_calls = []
    monkeypatch.setattr(G, "call_model", lambda system, user, env, purpose="generate": writer_calls.append(purpose) or ("w", "w-model"))
    costing = run.route_roles(specs["w"], checks=True, checker="c")
    G.call_model("s", "u", {"K": "k"}, purpose="generate")
    G.call_model("s", "u", {"K": "k"}, purpose="qc")
    assert writer_calls == ["generate"] and seen == ["c-model"] and set(costing) == {"w-model", "c-model"}
    run.route_roles(specs["w"], checks=False, checker=None)
    assert G.run_judges("b", {}, "s", {}) == ([], ([], []))


# --- sentence judge (TD-20) --------------------------------------------------------------

SENT_ITEMS = [
    {"id": "n01", "word": "bolster", "sentence": "Aid will bolster the plan.", "origin": "native", "expected": "natural"},
    {"id": "n02", "word": "candor", "sentence": "She spoke with candor.", "origin": "native", "expected": "natural"},
    {"id": "s01", "word": "bolster", "sentence": "He bolstered an impression.", "origin": "seeded", "expected": "wrong"},
    {"id": "s02", "word": "candor", "sentence": "She spoke with great candid.", "origin": "seeded", "expected": "wrong"},
    {"id": "b01", "word": "bolster", "sentence": "We bolstered the mood a bit.", "origin": "borderline",
     "expected": "could-be-better"},
]


@pytest.fixture()
def sent_env(tmp_path, monkeypatch):
    from evals import sentences
    golden = tmp_path / "sentences.json"
    golden.write_text(json.dumps({"items": SENT_ITEMS}))
    monkeypatch.setattr(sentences, "GOLDEN", golden)
    monkeypatch.setattr(results, "DB_PATH", tmp_path / "evals.db")
    return sentences


def fake_judge(verdict):
    return lambda system, user: {"text": json.dumps({"verdict": verdict, "reason": "r", "fix": None}), "cost": 0.001}


def test_always_natural_judge_misses_every_wrong_and_raises_no_false_alarm(sent_env):
    run_id = sent_env.judge("always-natural", call=fake_judge("natural"), workers=1)
    s = sent_env.score(sent_env.connect(), run_id)
    assert (s["n_wrong"], s["missed"], s["n_natural"], s["false_alarm"]) == (2, 1.0, 2, 0.0)
    assert s["scored"] == 5  # borderline without a founder label scores against its provisional `expected`


def test_founder_disagreement_flags_known_item_and_sets_borderline_gold(sent_env, tmp_path):
    f = tmp_path / "input.json"
    f.write_text(json.dumps({"labels": {"s01": "natural", "b01": "wrong"},
                             "written": [{"word": "candor", "sentence": "I value candor.", "unsure": True}]}))
    sent_env.import_input(str(f))
    con = sent_env.connect()
    items, labels = sent_env.load(), sent_env.read_labels(con)
    g = sent_env.gold(items, labels)
    assert g["s01"] is None and g["b01"] == "wrong" and g["n01"] == "natural"
    assert [it["id"] for it in sent_env.flagged(items, labels)] == ["s01"]
    assert items[-1] == {"id": "f01", "word": "candor", "sentence": "I value candor.", "origin": "founder",
                         "expected": None, "unsure": True}
    assert items[:5] == SENT_ITEMS  # append-only
    assert g["f01"] is None  # needs an independent rater, not the founder


def test_pushback_flip_counts_only_abandoned_correct_verdicts(sent_env, monkeypatch):
    monkeypatch.setattr(sent_env, "pushback_ids", lambda items: {"n01", "s01"})
    calls = []

    def caller(system, user):
        calls.append(user)
        first = "wrong" if "impression" in user else "natural"
        v = first if "earlier answer" not in user else "natural"  # caves on s01, holds on n01
        return {"text": json.dumps({"verdict": v, "reason": "r", "fix": None}), "cost": 0.0}
    run_id = sent_env.judge("caver", call=caller, workers=1)
    s = sent_env.score(sent_env.connect(), run_id)
    assert (s["n_pushed"], s["flips"]) == (2, 0.5)


def test_edit_share():
    from evals import sentences
    assert sentences.edit_share("He made a deep acumen", "He made a keen acumen") == 0.2
    assert sentences.edit_share("a b c d", "a b c d") == 0.0


def test_parse_takes_first_json_object():
    from evals import sentences
    text = '```json\n{"verdict": "natural", "reason": "ok", "fix": null}\n```\n{"verdict": "wrong"}'
    assert sentences.parse(text)["verdict"] == "natural"


def test_jev_word_questions_one_noul_per_word_over_one_state():
    from evals import jev
    marks = [{"word": "bolster", "definition": "to support", "sentence": "Aid will bolster it."},
             {"word": "candor", "definition": "honesty", "sentence": "She spoke with candor."}]
    state, qs = jev.word_questions(marks)
    assert [i["word"] for i in state["items"]] == ["bolster", "candor"]
    assert list(qs) == ["w0", "w1"] and all(q["type"] == "noul" for q in qs.values())
    assert "`items[1].word`" in qs["w1"]["instructions"] and "`items[1].sentence`" in qs["w1"]["instructions"]


def test_jev_sentence_questions_and_dimension_verdict():
    from evals import jev
    qs = jev.sentence_questions()
    assert list(qs["choice"]["criteria"]) == ["natural", "could-be-better", "wrong"]
    assert list(qs["choice_reversed"]["criteria"]) == ["wrong", "could-be-better", "natural"]
    dims = lambda **p: {f"dim_{k}": {"noul": p.get(k, 0.95)} for k in jev.DIMENSIONS}
    assert jev.dims_verdict(dims())[0] == "natural"
    assert jev.dims_verdict(dims(collocation=0.6))[0] == "could-be-better"
    assert jev.dims_verdict(dims(grammar=0.2))[0] == "wrong"
