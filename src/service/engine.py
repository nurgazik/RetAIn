"""Runs the PoC engine (generate.generate_piece) for one user's piece, on a worker thread,
updating pieces.status as phases pass so the events stream can relay them."""
import html as html_mod
import json
import re
import threading
import time

import generate as G  # src/generate.py (sys.path set in config)
from bakeoff import MODELS

from . import db
from .config import ENGINE_MODE

PRICES = {m["model"]: {"in": m["in"], "out": m["out"]} for m in MODELS}
_gen_lock = threading.Semaphore(2)  # at most two generations in flight (Gemini rate limits)


def text_to_html(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) == 1 and "\n" in text:
        paras = [p.strip() for p in text.split("\n") if p.strip()]
    return "\n".join(f"<p>{html_mod.escape(p)}</p>" for p in paras)


def enqueue(piece_id: str) -> None:
    threading.Thread(target=_run, args=(piece_id,), daemon=True).start()


def _set(con, piece_id: str, **fields) -> None:
    cols = ", ".join(f"{k}=?" for k in fields)
    con.execute(f"UPDATE pieces SET {cols} WHERE id=?", (*fields.values(), piece_id))
    con.commit()


def _run(piece_id: str) -> None:
    con = db.connect()
    t0 = time.time()
    try:
        piece = con.execute("SELECT * FROM pieces WHERE id=?", (piece_id,)).fetchone()
        words = db.learning_words(con, piece["user_id"])
        menu = [w["word"] for w in words]
        item = {"id": piece_id, "source": "user_text", "section": piece["source"],
                "url": piece["url"] or piece_id, "title": piece["title"] or "",
                "author": None, "published": None, "license": "user-supplied",
                "content_html": text_to_html(piece["source_text"])}
        env = {"GEMINI_API_KEY": __import__("os").environ.get("GEMINI_API_KEY", ""),
               "ANTHROPIC_API_KEY": __import__("os").environ.get("ANTHROPIC_API_KEY", "")}
        G.CALL_LOG.clear()
        with _gen_lock:
            _set(con, piece_id, status="generating")
            wrapper = "transform-sentence.md" if ENGINE_MODE == "sentence" else "transform.md"
            request = G.SENTENCE_REQUEST if ENGINE_MODE == "sentence" else None
            result = G.generate_piece(con, item, wrapper, menu, env, digest_date=None,
                                      words=words, record=False, request=request,
                                      density_floor=(ENGINE_MODE != "sentence"),
                                      progress=lambda phase: _set(con, piece_id, status=phase))
        cost = db.record_calls(con, piece["user_id"], piece_id, list(G.CALL_LOG), PRICES)
        _set(con, piece_id, status="done", title=result["title"], body_html=result["body"],
             attrib=G.attribution_for(item), offered_words=json.dumps(menu),
             words_used=json.dumps(result["words_used"]), model=result["model"],
             latency_ms=int((time.time() - t0) * 1000), cost_usd=round(cost, 6))
    except Exception as exc:
        print(f"[service] piece {piece_id} failed: {exc}")
        _set(con, piece_id, status="failed", error=str(exc)[:500],
             latency_ms=int((time.time() - t0) * 1000))
    finally:
        con.close()
