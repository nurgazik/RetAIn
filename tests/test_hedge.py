"""call_model's hedge (2026-09-28): errors switch to the fallback at once; a slow primary races
the fallback and the first answer wins; the serving host is logged."""
import time

import pytest

import generate as G


def fake(delay: float, text: str, fail: bool = False, host: str = None):
    def call(model, system, user, key, params=None):
        time.sleep(delay)
        if fail:
            raise RuntimeError("provider down")
        return {"text": text, "tokens_in": 1, "tokens_out": 1, **({"host": host} if host else {})}
    return call


@pytest.fixture()
def models(monkeypatch):
    def set_models(primary, fallback):
        monkeypatch.setattr(G, "PRIMARY", {"model": "gemma", "call": primary, "key": "K"})
        monkeypatch.setattr(G, "FALLBACK", fallback and {"model": "gemini-flash-lite", "call": fallback, "key": "K"})
    monkeypatch.setattr(G, "HEDGE_AFTER", {})
    monkeypatch.setattr(G, "HEDGE_AFTER_DEFAULT", 0.1)
    G.CALL_LOG.clear()
    return set_models


def test_fast_primary_wins_and_host_is_logged(models):
    models(fake(0, "gemma says", host="makora"), fake(0, "flash says"))
    assert G.call_model("s", "u", {"K": ""}) == ("gemma says", "gemma")
    assert G.CALL_LOG[-1][9] == "makora"


def test_primary_error_goes_straight_to_fallback(models):
    models(fake(0, "", fail=True), fake(0, "flash says"))
    assert G.call_model("s", "u", {"K": ""})[1] == "gemini-flash-lite"


def test_slow_primary_loses_the_race(models):
    models(fake(1.0, "gemma says"), fake(0.05, "flash says"))
    t = time.time()
    assert G.call_model("s", "u", {"K": ""})[1] == "gemini-flash-lite"
    assert time.time() - t < 0.5  # didn't wait for the slow primary


def test_slow_primary_still_wins_if_it_finishes_first(models):
    models(fake(0.2, "gemma says"), fake(1.0, "flash says"))
    assert G.call_model("s", "u", {"K": ""})[1] == "gemma"


def test_slow_primary_that_then_fails_uses_the_fallback(models):
    models(fake(0.2, "", fail=True), fake(0.4, "flash says"))
    assert G.call_model("s", "u", {"K": ""})[1] == "gemini-flash-lite"


def test_no_fallback_raises(models):
    models(fake(0, "", fail=True), None)
    with pytest.raises(RuntimeError):
        G.call_model("s", "u", {"K": ""})
