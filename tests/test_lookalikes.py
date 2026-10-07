"""The lookalike code check (D58): what survives from a model's five candidates."""
import json

import service.lookalikes as L


def test_check_keeps_three_real_lookalikes_and_says_why_others_go(monkeypatch):
    monkeypatch.setattr(L, "dictionary_pos", lambda w: {"noun"} if w == "embankment" else {"verb"})
    raw = "thinking...\n" + json.dumps({"lookalikes": ["x"]}) + "\nbetter:\n" + json.dumps(
        {"lookalikes": ["bolster", "bolstered", "embankment", "bluster", "Holster", "bolter", "bolt 2"]})
    kept, problems = L.check(raw, "bolster", "verb")
    assert kept == ["bluster", "holster", "bolter"]
    assert problems == ["bolster: repeat", "bolstered: a form of the target",
                        "embankment: doesn't look like the target", "bolt 2: not one word"]


def test_check_drops_the_wrong_part_of_speech(monkeypatch):
    monkeypatch.setattr(L, "dictionary_pos", lambda w: {"noun"})
    kept, problems = L.check(json.dumps({"lookalikes": ["astride"]}), "astute", "adjective")
    assert kept == [] and problems == ["astride: not a dictionary adjective"]
