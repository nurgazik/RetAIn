"""Daily practice (D56): set building, the fill-in check, the Jev-first judge and the schedule,
with every model stubbed (no calls leave the machine)."""
import json

import pytest


@pytest.fixture()
def stubs(client, monkeypatch):
    import service.practice as practice
    state = {"p": 0.95, "llm": 0, "verdict": "wrong", "look": 0, "fits": set()}

    def fake_model(system, user, env, purpose="generate", primary=None):
        def log(raw):  # as the real call logs it: this thread's row + the shared log
            practice.G._LAST.row = (purpose, "stub", 500, 100, 900, 0.00007, None, raw, "p1")
            practice.G.CALL_LOG.append(practice.G._LAST.row)
            return raw, "stub"

        word = user.split("Target word: ", 1)[1].split(" —", 1)[0]
        if purpose == "lookalikes":
            state["look"] += 1
            word = word.split(" (")[0]  # "Target word: bolster (verb) — …"
            return log(json.dumps({"lookalikes": [c + word[1:] for c in "qzkjv"]}))  # look alike, not forms
        if purpose == "fill-sentence":
            return log(json.dumps({"sentence": f"The new plan will {word} the team's confidence this year.",
                                   "answer": word}))
        state["llm"] += 1
        raw = json.dumps({"verdict": state["verdict"], "reason": "r", "fix": "f"})
        return log(raw)

    monkeypatch.setattr(practice.G, "call_model", fake_model)
    def fake_jev(w, d, s):
        p = (0.9 if w in state["fits"] else 0.01) if d == "g" else state["p"]  # "g": a lookalike's gloss
        return p, ("judge-jev", "jev-1.13.0", 300, 0, 200, 0.0000126, None, json.dumps({"natural": p}), "q1")
    monkeypatch.setattr(practice.typesafe, "p_natural", fake_jev)
    monkeypatch.setattr(practice.lookalikes, "dictionary_pos", lambda w: {"verb", "noun", "adj"})
    monkeypatch.setattr(practice.lookalikes, "gloss", lambda w, pos: "g")
    monkeypatch.setattr(practice.lookalikes.typesafe, "p_natural", fake_jev)
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


def test_fill_retries_until_right_without_revealing_the_word(client, stubs):
    item = today(client)["items"][0]
    wrong = client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": "Zzz"}).json()
    assert wrong == {"correct": False, "answer": "zzz", "meaning": "g"}  # its own meaning, not the word
    after = today(client)["items"][0]
    assert "answer" not in after["fill"] and "fill" not in after["attempts"]  # not done, not revealed
    assert after["fill"]["wrong"] == [{"answer": "zzz", "meaning": "g"}]
    ok = client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": item["word"].upper()}).json()
    assert ok["correct"] is True
    done = today(client)["items"][0]
    assert done["fill"]["answer"] and done["attempts"]["fill"]["correct"] == 0  # solved, but not first time


def test_fill_judged_on_the_first_try(client, stubs):
    from service.practice import add_days
    s = today(client)
    late, first = s["items"][0], s["items"][1]
    client.post("/v1/practice/fill", json={"word_id": late["word_id"], "answer": "nope"})
    client.post("/v1/practice/fill", json={"word_id": late["word_id"], "answer": late["word"]})
    client.post("/v1/practice/hint", json={"word_id": first["word_id"]})  # a hint isn't a try
    client.post("/v1/practice/fill", json={"word_id": first["word_id"], "answer": first["word"]})
    rows = boxes([late["word_id"], first["word_id"]])
    assert rows[late["word_id"]] == (0, add_days(s["day"], 1))
    assert rows[first["word_id"]] == (1, add_days(s["day"], 3))


def test_any_form_of_the_word_counts(client, stubs, monkeypatch):
    import service.practice as practice
    item = today(client)["items"][0]
    monkeypatch.setattr(practice.dictionary, "lemma", lambda w: item["word"] if w == item["word"] + "ed" else w)
    r = client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": item["word"] + "ed"}).json()
    assert r["correct"] is True and r["note"]


def test_confident_jev_gives_natural_without_an_llm_call(client, stubs):
    item = today(client)["items"][0]
    r = client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": f"They {item['word']} it well."})
    assert r.json() == {"verdict": "natural", "reason": None, "fix": None} and stubs["llm"] == 0


def test_unsure_jev_hands_the_sentence_to_the_llm(client, stubs):
    stubs["p"] = 0.4
    item = today(client)["items"][0]
    r = client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": f"They {item['word']} it badly."})
    assert r.json() == {"verdict": "wrong", "reason": "r", "fix": "f"} and stubs["llm"] == 1


def test_a_judged_sentence_keeps_the_whole_record(client, stubs):
    import service.db as db
    stubs["p"] = 0.4
    item = today(client)["items"][0]
    sentence = f"They {item['word']} it badly."
    client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": sentence})
    con = db.connect()
    a = con.execute("SELECT * FROM practice_attempts WHERE kind='write' ORDER BY id DESC LIMIT 1").fetchone()
    calls = con.execute("SELECT purpose, response, prompt_sha FROM calls WHERE attempt_id=? ORDER BY id", (a["id"],)).fetchall()
    con.close()
    assert (a["answer"], a["verdict"], a["p_natural"], a["judged_by"]) == (sentence, "wrong", 0.4, "llm")
    assert [c["purpose"] for c in calls] == ["judge-jev", "feedback"]
    assert json.loads(calls[0]["response"]) == {"natural": 0.4} and calls[0]["prompt_sha"] == "q1"
    assert '"verdict": "wrong"' in calls[1]["response"]


def test_hint_shows_the_word_among_lookalikes_that_dont_fit(client, stubs):
    import service.db as db
    s = today(client)
    assert stubs["look"] == len(s["items"])  # written once per lemma during prep
    item = s["items"][0]
    w = item["word"]
    stubs["fits"] = {"q" + w[1:]}  # Jev says this one reads naturally in the blank: dropped
    opts = client.post("/v1/practice/hint", json={"word_id": item["word_id"]}).json()["options"]
    assert sorted(opts) == sorted([w, "z" + w[1:], "k" + w[1:], "j" + w[1:]])
    assert client.post("/v1/practice/hint", json={"word_id": item["word_id"]}).json()["options"] == opts  # same, free
    assert today(client)["items"][0]["fill"]["hint"] == opts
    r = client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": w}).json()
    assert r["correct"] is True  # a pill counts exactly like typing it
    con = db.connect()
    a = con.execute("SELECT hint FROM practice_attempts WHERE kind='fill' ORDER BY id DESC LIMIT 1").fetchone()
    con.close()
    assert json.loads(a["hint"]) == opts


def test_lookalikes_are_shared_across_days_and_users(client, stubs):
    import service.db as db
    from service import lookalikes
    s = today(client)
    con = db.connect()
    calls = lookalikes.ensure(con, s["items"][0]["word"], "verb", "d", {})
    con.close()
    assert calls == [] and stubs["look"] == len(s["items"])  # already stored: no new call


def test_parallel_prep_records_each_call_once(client, stubs):
    import service.db as db
    today(client)  # five words prepared on four threads
    con = db.connect()
    rows = con.execute("SELECT purpose, count(*) FROM calls GROUP BY purpose").fetchall()
    con.close()
    assert dict(rows)["lookalikes"] == stubs["look"]


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


def boxes(ids):
    import service.db as db
    con = db.connect()
    rows = {r["id"]: (r["box"], r["due_day"]) for r in con.execute(
        f"SELECT id, box, due_day FROM words WHERE id IN ({','.join('?' * len(ids))})", ids)}
    con.close()
    return rows


def test_either_exercise_alone_moves_a_word_and_both_count_once(client, stubs):
    from service.practice import add_days
    s = today(client)
    fill_only, write_only, both, slip = (i["word_id"] for i in s["items"][:4])
    words = {i["word_id"]: i["word"] for i in s["items"]}
    client.post("/v1/practice/fill", json={"word_id": fill_only, "answer": words[fill_only]})
    client.post("/v1/practice/write", json={"word_id": write_only, "sentence": f"We {words[write_only]} it."})
    client.post("/v1/practice/fill", json={"word_id": both, "answer": words[both]})
    client.post("/v1/practice/write", json={"word_id": both, "sentence": f"We {words[both]} it."})
    client.post("/v1/practice/write", json={"word_id": slip, "sentence": f"We {words[slip]} it."})
    client.post("/v1/practice/fill", json={"word_id": slip, "answer": "nope"})  # a miss after a clean pass
    rows = boxes([fill_only, write_only, both, slip])
    for w in (fill_only, write_only, both):
        assert rows[w] == (1, add_days(s["day"], 3))
    assert rows[slip] == (0, add_days(s["day"], 1))


def test_could_be_better_holds_the_gap(client, stubs):
    from service.practice import add_days
    stubs["p"], stubs["verdict"] = 0.4, "could-be-better"
    item = today(client)["items"][0]
    client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": item["word"]})
    client.post("/v1/practice/write", json={"word_id": item["word_id"], "sentence": f"We {item['word']} it."})
    assert boxes([item["word_id"]])[item["word_id"]] == (0, add_days(today(client)["day"], 1))


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
