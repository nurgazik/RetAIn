"""Streaks and stats (D74): events from the phone (resends ignored, late events on their own day), the review
log on answers, word history, and the stats worked out from them."""
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from test_practice import stubs, today  # noqa: F401  (pytest fixture + helper)
from conftest import TEXT


def piece(client) -> str:
    pid = client.post("/v1/transform", json={"text": TEXT}).json()["piece_id"]
    for _ in range(40):
        if client.get(f"/v1/pieces/{pid}").json()["status"] == "done":
            return pid
        time.sleep(0.05)
    raise AssertionError("piece never finished")


def ev(kind, at=None, **kw):
    return {"id": uuid.uuid4().hex, "kind": kind, "at": (at or datetime.now(timezone.utc)).isoformat(), **kw}


def words(client) -> dict:
    return {w["word"]: w for w in client.get("/v1/words").json()["words"]}


# ---------------------------------------------------------------- the streak rule

def test_streak_counts_runs_and_resets_on_a_missed_day():
    from service.stats import streak
    days = ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-05", "2026-11-06"]
    assert streak(days, "2026-11-06") == {"current": 2, "best": 3, "today_counts": True, "total_days": 5}
    assert streak(days, "2026-11-07")["current"] == 2           # today isn't over: yesterday keeps it alive
    assert streak(days, "2026-11-07")["today_counts"] is False
    assert streak(days, "2026-11-08")["current"] == 0           # a missed day resets it (no protection, D74)
    assert streak(days, "2026-11-08")["total_days"] == 5        # the total never resets
    assert streak([], "2026-11-08") == {"current": 0, "best": 0, "today_counts": False, "total_days": 0}


# ---------------------------------------------------------------- events from the phone

def test_events_keep_resends_once_and_reject_bad_ones(client):
    pid = piece(client)
    tap = ev("tap", surface="reader", piece_id=pid, word="Bolstered")
    now = datetime.now(timezone.utc)
    r = client.post("/v1/events", json={"events": [
        tap, tap,                                                        # a resend
        ev("open", surface="reader", piece_id="p_not_mine"),
        ev("open", at=now + timedelta(hours=1), surface="reader", piece_id=pid),
        ev("open", at=now - timedelta(days=4), surface="reader", piece_id=pid),
        {"id": "short", "kind": "open"},
        ev("shown", surface="practice", exercise="fill", word_id=999999)]}).json()
    assert (r["kept"], r["duplicates"]) == (1, 1)
    assert [x["reason"] for x in r["rejected"]] == ["piece", "future", "too old", "id", "word"]
    again = client.post("/v1/events", json={"events": [tap]}).json()      # the queue retries later
    assert (again["kept"], again["duplicates"]) == (0, 1)
    import service.db as db
    con = db.connect()
    row = con.execute("SELECT word, word_id FROM events WHERE client_id=?", (tap["id"],)).fetchone()
    assert row["word"] == "bolstered" and row["word_id"] == words(client)["bolster"]["id"]  # printed form → word
    con.close()


def test_a_late_event_lands_on_the_day_it_happened(client):
    pid = piece(client)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    client.post("/v1/events", json={"events": [ev("open", at=yesterday, surface="reader", piece_id=pid)]})
    import service.db as db
    con = db.connect()
    day = con.execute("SELECT day FROM events WHERE kind='open'").fetchone()[0]
    con.close()
    assert day < client.get("/v1/me").json()["day"]
    s = client.get("/v1/stats").json()["streak"]
    assert s["current"] == 1 and s["today_counts"] is False      # yesterday's read keeps the streak alive


# ---------------------------------------------------------------- answers: the review log

def test_an_answer_records_the_box_before_and_after_and_its_time(client, stubs):
    item = today(client)["items"][0]
    client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": item["word"], "seconds": 7.5})
    import service.db as db
    con = db.connect()
    a = con.execute("SELECT * FROM practice_attempts").fetchone()
    w = con.execute("SELECT box, due_day FROM words WHERE id=?", (item["word_id"],)).fetchone()
    con.close()
    assert (a["box_before"], a["box_after"], a["due_after"]) == (0, 1, w["due_day"]) and w["box"] == 1
    assert a["seconds"] == 7.5 and a["sentence_id"] is not None   # which bank sentence was answered


def test_an_answer_and_its_schedule_change_save_together(client, stubs, monkeypatch):
    import service.practice as practice
    item = today(client)["items"][0]
    monkeypatch.setattr(practice, "reschedule", lambda *a: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        client.post("/v1/practice/fill", json={"word_id": item["word_id"], "answer": item["word"]})
    import service.db as db
    con = db.connect()
    assert con.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0] == 0   # no half-saved answer
    con.close()


# ---------------------------------------------------------------- word history and stats

def test_word_changes_are_logged_and_counted(client, stubs):
    wid = client.post("/v1/words", json={"word": "galvanize", "definition": "x"}).json()["id"]
    client.patch(f"/v1/words/{wid}", json={"status": "retained"})
    client.patch(f"/v1/words/{wid}", json={"status": "learning"})
    client.patch(f"/v1/words/{wid}", json={"note": "only a note"})          # not a status change: no row
    s = client.get(f"/v1/words/{wid}/stats").json()
    assert [c["kind"] for c in s["changes"]] == ["added", "retained", "learn-again"]
    assert s["retained_on"] == client.get("/v1/me").json()["day"] and s["times_relearned"] == 1
    client.delete(f"/v1/words/{wid}")
    client.post("/v1/words", json={"word": "galvanize", "definition": "x"})  # saved again after delete
    s = client.get(f"/v1/words/{wid}/stats").json()
    assert [c["kind"] for c in s["changes"]][-2:] == ["deleted", "saved-again"]


def test_shown_counts_once_per_piece_per_day_and_stats_add_up(client, stubs):
    pid = piece(client)
    item = today(client)["items"][0]
    wid, word = item["word_id"], item["word"]
    shown_reader = lambda: ev("shown", surface="reader", piece_id=pid, word=word)
    client.post("/v1/events", json={"events": [
        shown_reader(), shown_reader(),                                   # read twice today: shown once
        ev("tap", surface="reader", piece_id=pid, word=word),
        ev("shown", surface="practice", exercise="fill", word_id=wid),
        ev("open", surface="reader", piece_id=pid)]})
    client.post("/v1/practice/fill", json={"word_id": wid, "answer": "nope"})
    client.post("/v1/practice/fill", json={"word_id": wid, "answer": word})
    s = client.get(f"/v1/words/{wid}/stats").json()
    assert s["shown"] == {"reader": 1, "practice": 1} and s["taps"] == 1
    assert s["answers"] == {"fill": {"tries": 2, "wrong": 1, "right": 1}}
    assert [h["result"] for h in s["history"]] == ["wrong", "right"]
    u = client.get("/v1/stats").json()
    assert u["streak"] == {"current": 1, "best": 1, "today_counts": True, "total_days": 1}
    assert u["today"] == {"answers": 2, "words_practised": 1, "pieces_read": 1, "words_shown": 1}


# ---------------------------------------------------------------- migration

def test_an_older_events_table_is_rebuilt_with_its_taps(client):
    import service.db as db
    uid = client.get("/v1/me").json()["user_id"]
    con = db.connect()
    con.execute("DROP TABLE events")
    con.execute("CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, "
                "piece_id TEXT NOT NULL, word TEXT, kind TEXT NOT NULL, at TEXT NOT NULL, day TEXT NOT NULL DEFAULT '')")
    con.execute("INSERT INTO events (user_id, piece_id, word, kind, at, day) VALUES (?,?,?,?,?,?)",
                (uid, "p_x", "bolstering", "tap", "2026-10-01T10:00:00+00:00", "2026-10-01"))
    con.commit(); con.close()
    db.init()
    con = db.connect()
    r = con.execute("SELECT * FROM events").fetchone()
    assert (r["kind"], r["surface"], r["word"], r["day"]) == ("tap", "reader", "bolstering", "2026-10-01")
    assert r["word_id"] == words(client)["bolster"]["id"]
    assert con.execute("SELECT COUNT(*) FROM word_log WHERE kind='added'").fetchone()[0] > 0  # older words backfilled
    con.close()


def test_recall_stats_from_the_logs(client, stubs):
    """D74 word stats: tap rate, lapses, first tries, confusions, hints, time, where it was read, look-ups."""
    pid = piece(client)
    item = today(client)["items"][0]
    wid, word = item["word_id"], item["word"]
    import service.db as db
    con = db.connect()
    con.execute("UPDATE words SET box=3 WHERE id=?", (wid,))   # a word that seemed known…
    con.commit(); con.close()
    client.post("/v1/events", json={"events": [
        ev("shown", surface="reader", piece_id=pid, word=word),
        ev("tap", surface="reader", piece_id=pid, word=word),
        ev("tap", surface="reader", piece_id=pid, word=word),          # same piece, same day: one "didn't remember"
        ev("card", surface="words", word_id=wid), ev("listen", surface="reader", word_id=wid),
        ev("card", surface="words", word_id=999999)]})                  # not the user's word: rejected
    client.post("/v1/practice/hint", json={"word_id": wid})
    client.post("/v1/practice/fill", json={"word_id": wid, "answer": "Bolsterous", "seconds": 4})  # …forgotten
    client.post("/v1/practice/fill", json={"word_id": wid, "answer": word, "seconds": 10})
    s = client.get(f"/v1/words/{wid}/stats").json()
    assert s["tap_rate"] == 1.0 and s["lapses"] == 1
    assert s["first_try"] == {"fill": {"tries": 1, "clean": 0}}
    assert s["confused_with"] == [{"answer": "bolsterous", "times": 1}]
    assert (s["hint_days"], s["fill_days"]) == (1, 1) and s["median_seconds"] == {"fill": 7.0}
    assert [r["piece_id"] for r in s["read_in"]] == [pid]
    assert s["last_seen"] == client.get("/v1/me").json()["day"] and s["days_since_seen"] == 0
    assert (s["card_opens"], s["listens"]) == (1, 1)
    assert s["days_to_retain"] is None and s["sentences"] == []
