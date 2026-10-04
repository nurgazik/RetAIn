import time
from datetime import datetime, timezone

from conftest import TEXT


def test_auth_required(client):
    client.headers.pop("Authorization")
    assert client.get("/v1/me").status_code == 401


def test_dev_user_seeded_with_words(client):
    me = client.get("/v1/me").json()
    assert me["learning_words"] >= 50
    words = client.get("/v1/words").json()["words"]
    assert all("servings" in w for w in words)


def test_word_lifecycle(client):
    w = client.post("/v1/words", json={"word": "galvanize", "definition": "x"}).json()
    r = client.patch(f"/v1/words/{w['id']}", json={"status": "retained"})
    assert r.status_code == 200 and r.json()["status"] == "retained"
    assert client.patch(f"/v1/words/{w['id']}", json={"status": "bogus"}).status_code == 422


def test_transform_lifecycle_and_events(client):
    assert client.post("/v1/transform", json={"text": "too short"}).status_code == 422
    r = client.post("/v1/transform", json={"text": TEXT, "title": "T", "source": "test", "meta": {"types": ["x"]}})
    assert r.status_code == 202
    pid = r.json()["piece_id"]
    events = []
    with client.stream("GET", f"/v1/transform/{pid}/events") as s:
        for line in s.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
            if line.startswith("event: piece") or line.startswith("event: error"):
                break
    assert "phase" in events and events[-1] == "piece"
    piece = client.get(f"/v1/pieces/{pid}").json()
    assert piece["status"] == "done" and piece["words_used"] and "<mark" in piece["body_html"]
    assert piece["cost_usd"] > 0
    assert client.post(f"/v1/pieces/{pid}/taps", json={"word": "bolster"}).status_code == 201
    assert any(p["id"] == pid for p in client.get("/v1/pieces").json()["pieces"])
    me = client.get("/v1/me").json()
    assert me["spend_today_usd"] > 0


def test_page_metadata_stored_for_header(client):
    r = client.post("/v1/transform", json={"text": TEXT, "source": "test", "byline": "Arden McLeod",
                                           "site_name": "CBC", "published": "2026-09-26T12:00:00.000Z",
                                           "dek": "Summary line\n\nSub-headline"})
    piece = client.get(f"/v1/pieces/{r.json()['piece_id']}").json()
    assert (piece["byline"], piece["site_name"], piece["published"], piece["dek"]) == \
        ("Arden McLeod", "CBC", "2026-09-26T12:00:00.000Z", "Summary line\n\nSub-headline")
    bare = client.get(f"/v1/pieces/{client.post('/v1/transform', json={'text': TEXT}).json()['piece_id']}").json()
    assert bare["byline"] is None and bare["dek"] is None


def test_daily_cap(client):
    for _ in range(3):
        assert client.post("/v1/transform", json={"text": TEXT}).status_code == 202
    assert client.post("/v1/transform", json={"text": TEXT}).status_code == 429


PT = "America/Los_Angeles"


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


def test_day_starts_at_4am_local(client):
    """D51 (and TD-17): 8 pm and 1 am Pacific belong to the same day; 4 am starts the next."""
    import service.db as db
    tz = db.zone(PT)
    assert db.day_of(utc(2026, 9, 29, 3), tz) == "2026-09-28"   # 8 pm Sep 28 Pacific
    assert db.day_of(utc(2026, 9, 29, 8), tz) == "2026-09-28"   # 1 am Sep 29
    assert db.day_of(utc(2026, 9, 29, 11), tz) == "2026-09-29"  # 4 am Sep 29
    assert db.day_of(utc(2026, 9, 29, 3), db.zone("America/Toronto")) == "2026-09-28"  # 11 pm Toronto
    assert db.day_of(utc(2026, 9, 29, 8), db.zone("America/Toronto")) == "2026-09-29"  # 4 am Toronto
    assert db.next_day_at("2026-09-28", tz) == "2026-09-29T11:00:00+00:00"
    # DST ends 2026-11-01 at 2 am; the 4 am boundary is unaffected (UTC-8 from then on)
    assert db.next_day_at("2026-11-01", tz) == "2026-11-02T12:00:00+00:00"
    assert db.zone("Mars/Olympus") is None and db.zone("../etc/passwd") is None and db.zone("") is None


def test_timezone_header_sets_and_saves_the_users_day(client):
    me = client.get("/v1/me", headers={"X-Timezone": "Asia/Tokyo"}).json()
    assert me["tz"] == "Asia/Tokyo" and me["day"] and me["next_day_at"]
    assert client.get("/v1/me").json()["tz"] == "Asia/Tokyo"  # saved: no header, same zone
    bad = client.get("/v1/me", headers={"X-Timezone": "Nowhere/Invalid"})
    assert bad.status_code == 200 and bad.json()["tz"] == "Asia/Tokyo"  # an invalid name is ignored


def test_day_never_moves_back(client):
    """Flying Tokyo → Honolulu crosses back over the rollover: the day stays."""
    import service.db as db
    uid = client.get("/v1/me").json()["user_id"]
    con = db.connect()
    # /v1/me above saved the real today as last_day; clear it so the fixed `at` below is the
    # latest day seen (otherwise the test fails on any date after 2026-10-01)
    con.execute("UPDATE users SET last_day=NULL WHERE id=?", (uid,))
    user = dict(con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
    at = utc(2026, 9, 30, 20)  # 5 am Oct 1 in Tokyo, 10 am Sep 30 in Honolulu
    tokyo = db.resolve_day(con, user, "Asia/Tokyo", at=at)
    assert tokyo["day"] == "2026-10-01"
    user = dict(con.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone())
    honolulu = db.resolve_day(con, user, "Pacific/Honolulu", at=at)
    assert honolulu["day"] == "2026-10-01" and honolulu["tz"] == "Pacific/Honolulu"
    con.close()


def test_every_write_is_stamped_with_the_day(client):
    pid = client.post("/v1/transform", json={"text": TEXT}).json()["piece_id"]
    for _ in range(40):
        if client.get(f"/v1/pieces/{pid}").json()["status"] == "done":
            break
        time.sleep(0.05)
    client.post(f"/v1/pieces/{pid}/taps", json={"word": "bolster"})
    client.post("/v1/words", json={"word": "galvanize", "definition": "x"})
    import service.db as db
    con = db.connect()
    for t in ("pieces", "calls", "events", "words"):
        assert con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] > 0, t
        assert con.execute(f"SELECT COUNT(*) FROM {t} WHERE day=''").fetchone()[0] == 0, t
    con.close()


def test_older_rows_get_their_day_on_startup(client):
    import service.db as db
    uid = client.get("/v1/me").json()["user_id"]
    con = db.connect()
    con.execute("INSERT INTO events (user_id, piece_id, word, kind, at) VALUES (?,?,?,?,?)",
                (uid, "p_x", "w", "tap", "2026-09-29T08:30:00+00:00"))  # 1:30 am Pacific
    con.commit(); con.close()
    db.init()
    con = db.connect()
    assert con.execute("SELECT day FROM events WHERE piece_id='p_x'").fetchone()[0] == "2026-09-28"
    con.close()


def test_diagnostics_stored(client):
    r = client.post("/v1/diagnostics", json={"kind": "unusable-share", "payload": {"types": ["public.url"]}})
    assert r.status_code == 201


def test_unknown_piece_404(client):
    assert client.get("/v1/pieces/p_nope").status_code == 404
