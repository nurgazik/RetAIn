import time

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


def test_daily_cap(client):
    for _ in range(3):
        assert client.post("/v1/transform", json={"text": TEXT}).status_code == 202
    assert client.post("/v1/transform", json={"text": TEXT}).status_code == 429


def test_diagnostics_stored(client):
    r = client.post("/v1/diagnostics", json={"kind": "unusable-share", "payload": {"types": ["public.url"]}})
    assert r.status_code == 201


def test_unknown_piece_404(client):
    assert client.get("/v1/pieces/p_nope").status_code == 404
