"""Word cards (D48): the capture flow in diagrams/word-capture-flow.md, on a tiny fixture
dictionary with the model stubbed."""
import json

import pytest

FIXTURE = [  # Wiktextract-shaped entries
    {"word": "linchpin", "lang_code": "en", "pos": "noun",
     "senses": [{"glosses": ["A pin through an axle."]},
                {"glosses": ["A person or thing critical to a system."], "tags": ["figuratively"]}],
     "sounds": [{"ipa": "/ˈlɪnt͡ʃˌpɪn/"}]},
    {"word": "run", "lang_code": "en", "pos": "verb", "senses": [{"glosses": ["To move quickly on foot."]}],
     "sounds": [{"ipa": "/ɹʌn/", "tags": ["US"]}]},
    {"word": "ran", "lang_code": "en", "pos": "verb",
     "senses": [{"glosses": ["simple past of run"], "tags": ["form-of", "past"], "form_of": [{"word": "run"}]}]},
    {"word": "ran", "lang_code": "en", "pos": "noun", "senses": [{"glosses": ["Yarns coiled on a winch."]}]},
    {"word": "Ran", "lang_code": "en", "pos": "name", "senses": [{"glosses": ["A surname."]}]},
    {"word": "protracted", "lang_code": "en", "pos": "verb",
     "senses": [{"glosses": ["past participle of protract"], "form_of": [{"word": "protract"}]}]},
    {"word": "protracted", "lang_code": "en", "pos": "adj", "senses": [{"glosses": ["Lasting a long time."]}]},
    {"word": "protract", "lang_code": "en", "pos": "verb", "senses": [{"glosses": ["To prolong."]}]},
    {"word": "fraught", "lang_code": "en", "pos": "adj",
     "senses": [{"glosses": ["Laden with cargo."], "tags": ["obsolete"]},
                {"glosses": ["Loaded with anxiety."], "tags": ["obsolete"]}]},
    {"word": "gaol", "lang_code": "fr", "pos": "noun", "senses": [{"glosses": ["not English"]}]},
]


@pytest.fixture()
def dictionary(client, tmp_path, monkeypatch):
    """Build the reference file from FIXTURE and stub the model; yields the list of model calls."""
    import service.dictionary as D
    dump = tmp_path / "fixture.jsonl"
    dump.write_text("\n".join(json.dumps(e) for e in FIXTURE))
    monkeypatch.setattr(D, "DICT_PATH", tmp_path / "wiktionary.db")
    D.build(dump)
    calls = []

    def fake_call_model(system, user, env, purpose="generate"):
        calls.append(user)
        D_G.CALL_LOG.append(("card", "gemma", 10, 10, 5))
        if system == D.EXAMPLES_SYSTEM:
            n = user.count("\n") - 1  # numbered meanings after "WORD:" and "MEANINGS:"
            return json.dumps({"examples": {str(i): [f"example {i}a", f"example {i}b"] for i in range(1, n + 1)}}), "gemma"
        if "WORD: rizz" in user:
            return json.dumps({"real": True, "pos": "noun", "definition": "Charm.", "examples": ["He has rizz."]}), "gemma"
        return json.dumps({"real": False}), "gemma"

    import generate as D_G
    monkeypatch.setattr(D_G, "call_model", fake_call_model)
    yield calls


def test_lookup_rules(dictionary):
    import service.dictionary as D
    assert [s["gloss"] for s in D.lookup("linchpin")["senses"]] == [
        "A pin through an axle.", "A person or thing critical to a system."]  # Wiktionary order
    assert D.lookup("ran")["headword"] == "run"  # inflection → the lemma's card
    assert D.lookup("protracted")["headword"] == "protracted"  # its own adjective wins
    assert len(D.lookup("fraught")["senses"]) == 2  # every sense obsolete-tagged: keep them all
    assert D.lookup("gaol") is None  # English entries only


def test_wiktionary_word_gets_card_with_examples(client, dictionary):
    w = client.post("/v1/words", json={"word": "Linchpin"}).json()
    card = w["card"]
    assert card["source"] == "wiktionary" and card["source_url"].endswith("/linchpin")
    assert card["senses"][1]["examples"] == ["example 2a", "example 2b"]
    assert w["definition"] == "A pin through an axle." and w["pos"] == "noun" and not w["unverified"]
    assert len(dictionary) == 1


def test_shared_card_is_reused_without_a_model_call(client, dictionary):
    client.post("/v1/words", json={"word": "ran"})
    assert client.post("/v1/words", json={"word": "run"}).json()["card"]["headword"] == "run"
    assert len(dictionary) == 1  # the second capture reused the shared card


def test_unknown_real_word_is_written_by_the_model(client, dictionary):
    w = client.post("/v1/words", json={"word": "rizz"}).json()
    assert w["card"]["source"] == "model" and w["definition"] == "Charm." and not w["unverified"]


def test_made_up_word_is_unverified_private_and_never_rewritten(client, dictionary):
    w = client.post("/v1/words", json={"word": "asdfgh"}).json()
    assert w["unverified"] and w["card"] is None and w["definition"] == ""
    assert any(x["word"] == "asdfgh" for x in client.get("/v1/words").json()["words"])  # in the user's list
    from service import db
    con = db.connect()
    uid = con.execute("SELECT user_id FROM words WHERE word='asdfgh'").fetchone()[0]
    assert "asdfgh" not in [x["word"] for x in db.learning_words(con, uid)]  # never offered to the engine
    assert con.execute("SELECT COUNT(*) FROM lexicon WHERE headword='asdfgh'").fetchone()[0] == 0  # not shared


def test_model_failure_still_saves_the_word(client, dictionary, monkeypatch):
    import generate as G

    def broken(*a, **k):
        raise RuntimeError("provider down")
    monkeypatch.setattr(G, "call_model", broken)
    w = client.post("/v1/words", json={"word": "linchpin"}).json()
    assert w["card"]["senses"][0]["examples"] == []  # filled by the next backfill
