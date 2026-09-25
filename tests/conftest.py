"""Service tests run against a temp SQLite file with the engine stubbed (no model calls)."""
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RETAIN_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("RETAIN_DEV_TOKEN", "dev-test")
    monkeypatch.setenv("RETAIN_SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("RETAIN_DAILY_CAP", "3")
    for m in [k for k in sys.modules if k == "service" or k.startswith("service.")]:
        del sys.modules[m]
    import service.engine as engine
    import service.app as app_mod

    def fake_generate_piece(con, item, wrapper, chosen, env, **kw):
        kw.get("progress", lambda p: None)("checking")
        engine.G.CALL_LOG.clear()
        engine.G.CALL_LOG.append(("generate", "gemini-3.1-flash-lite", 100, 50, 12))
        first = chosen[0] if chosen else "bolster"
        return {"title": item["title"] or "Untitled", "body": f"<p>We <mark>{first}</mark> it.</p>",
                "model": "gemini-3.1-flash-lite", "marks": 1, "words_used": [first], "word_count": 3,
                "qc_rejected": [], "invented_numbers": [], "attempts": 1, "invented_unmarked": []}

    monkeypatch.setattr(engine.G, "generate_piece", fake_generate_piece)
    from fastapi.testclient import TestClient
    with TestClient(app_mod.app) as c:
        c.headers["Authorization"] = "Bearer dev-test"
        yield c


TEXT = " ".join(["word"] * 40)
