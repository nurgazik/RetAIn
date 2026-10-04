"""Daily practice (D56): set building, the fill-in check, the Jev-first judge and the schedule,
with every model stubbed (no calls leave the machine)."""
import json

import pytest


@pytest.fixture()
def stubs(client, monkeypatch):
    import service.practice as practice
    state = {"p": 0.95, "llm": 0, "verdict": "wrong"}

    def fake_model(system, user, env, purpose="generate"):
        word = user.split("Target word: ", 1)[1].split(" —", 1)[0]
        if purpose == "fill-sentence":
            return json.dumps({"sentence": f"The new plan will {word} the team's confidence this year.",
                               "answer": word}), "stub"
        state["llm"] += 1
        return json.dumps({"verdict": state["verdict"], "reason": "r", "fix": "f"}), "stub"

    monkeypatch.setattr(practice.G, "call_model", fake_model)
    monkeypatch.setattr(practice.typesafe, "p_natural",
                        lambda w, d, s: (state["p"], ("judge-jev", "jev-1.13.0", 300, 0, 200, 0.0000126)))
    return state


def today(client):
    r = client.get("/v1/practice/today")
    assert r.status_code == 200
    return r.json()


def test_set_is_built_once_per_day_with_answers_hidden(client, stubs):
    s = today(client)
    assert len(s["items"]) == 5
    assert all(i["fill"] and "_____" in i["fill"]["text"] and "answer" not in i["fill"] for i in s["items"])
    assert today(client)["items"] == s["items"]  # same set on the second open


def test_fill_check_accepts_the_blanked_form_and_the_base_word(client, stubs):
    item = today(client)["items"][0]
    wrong = client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": "zzz"}).json()
    assert wrong["correct"] is False and wrong["expected"].lower() == item["word"]
    item2 = today(client)["items"][1]
    ok = client.post("/v1/practice/fill", json={"word_id": item2["word_id"], "answer": item2["word"].upper()}).json()
    assert ok["correct"] is True
    after = today(client)["items"][0]
    assert after["fill"]["answer"] and after["attempts"]["fill"]["correct"] == 0  # revealed once tried


def test_confident_jev_gives_natural_without_an_llm_call(client, stubs):
    item = today(client)["items"][0]
    r = client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": f"They {item['word']} it well."})
    assert r.json() == {"verdict": "natural", "reason": None, "fix": None} and stubs["llm"] == 0


def test_unsure_jev_hands_the_sentence_to_the_llm(client, stubs):
    stubs["p"] = 0.4
    item = today(client)["items"][0]
    r = client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": f"They {item['word']} it badly."})
    assert r.json() == {"verdict": "wrong", "reason": "r", "fix": "f"} and stubs["llm"] == 1


def test_a_sentence_without_the_word_is_refused(client, stubs):
    item = today(client)["items"][0]
    r = client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": "Nothing relevant here."})
    assert r.status_code == 422


def test_schedule_up_a_box_on_clean_pass_back_to_tomorrow_on_a_miss(client, stubs):
    import service.db as db
    s = today(client)
    good, bad = s["items"][0], s["items"][1]
    client.post("/v1/practice/fill", json={"word_id": good["word_id"], "answer": good["word"]})
    client.post("/v1/practice/write", json={"word_id": good["word_id"], "sentence": f"We {good['word']} it."})
    client.post("/v1/practice/fill", json={"word_id": bad["word_id"], "answer": "nope"})
    con = db.connect()
    rows = {r["id"]: dict(r) for r in con.execute("SELECT id, box, due_day FROM words WHERE id IN (?,?)",
                                                  (good["word_id"], bad["word_id"]))}
    from service.practice import add_days
    assert rows[good["word_id"]]["box"] == 1 and rows[good["word_id"]]["due_day"] == add_days(s["day"], 3)
    assert rows[bad["word_id"]]["box"] == 0 and rows[bad["word_id"]]["due_day"] == add_days(s["day"], 1)
    con.close()


def test_own_reading_sentence_is_preferred(client, stubs):
    import service.db as db
    import service.practice as practice
    uid = client.get("/v1/me").json()["user_id"]
    con = db.connect()
    word = practice.pick_words(con, uid, client.get("/v1/me").json()["day"])[0]["word"]
    con.execute("INSERT INTO pieces (id, user_id, created_at, day, source, source_text, status, body_html) "
                "VALUES ('p1', ?, '2026-10-01', '2026-10-01', 'test', 'x', 'done', ?)",
                (uid, f"<p>Officials hoped the grant would <mark data-def='x'>{word}</mark> the local economy quickly.</p>"))
    con.commit()
    got = practice.from_reads(con, uid, word)
    con.close()
    assert got == {"text": "Officials hoped the grant would _____ the local economy quickly.", "answer": word,
                   "source": "read"}


def test_retained_words_leave_practice(client, stubs):
    import service.db as db
    import service.practice as practice
    me = client.get("/v1/me").json()
    con = db.connect()
    first = practice.pick_words(con, me["user_id"], me["day"])[0]
    client.patch(f"/v1/words/{first['id']}", json={"status": "retained"})
    assert first["id"] not in [w["id"] for w in practice.pick_words(con, me["user_id"], me["day"])]
    con.close()
