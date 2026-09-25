"""RetAIn transform service — routes. See docs/architecture.md (M1) and PRD D38."""
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import date

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from . import auth, db, engine
from .config import DAILY_CAP, MAX_CHARS, MIN_CHARS


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    # Recovery: a piece caught mid-generation by a restart is re-queued (generation is idempotent).
    con = db.connect()
    try:
        stuck = [r["id"] for r in con.execute(
            "SELECT id FROM pieces WHERE status IN ('queued','generating','checking','regenerating','repairing')")]
        for pid in stuck:
            con.execute("UPDATE pieces SET status='queued' WHERE id=?", (pid,))
        con.commit()
    finally:
        con.close()
    for pid in stuck:
        print(f"[service] re-queued {pid} after restart")
        engine.enqueue(pid)
    yield


app = FastAPI(title="RetAIn service", version="0.1", lifespan=lifespan)


# ---------------------------------------------------------------- auth

class AppleSignIn(BaseModel):
    identity_token: str
    nonce: str | None = None


@app.post("/v1/auth/apple")
def auth_apple(body: AppleSignIn):
    try:
        claims = auth.verify_apple_identity_token(body.identity_token, body.nonce)
    except jwt.PyJWTError as exc:
        raise HTTPException(401, f"apple token rejected: {exc}")
    con = db.connect()
    try:
        user, created = db.upsert_user(con, claims["sub"], claims.get("email"))
        return {"token": auth.issue_session(user["id"]), "user_id": user["id"], "new_user": created}
    finally:
        con.close()


@app.get("/v1/me")
def me(user=Depends(auth.current_user)):
    con = db.connect()
    try:
        n_words = con.execute("SELECT COUNT(*) FROM words WHERE user_id=? AND status='learning'", (user["id"],)).fetchone()[0]
        n_pieces = con.execute("SELECT COUNT(*) FROM pieces WHERE user_id=? AND status='done'", (user["id"],)).fetchone()[0]
        return {"user_id": user["id"], "email": user["email"], "learning_words": n_words, "pieces": n_pieces}
    finally:
        con.close()


# ---------------------------------------------------------------- words

class WordIn(BaseModel):
    word: str = Field(min_length=1, max_length=60)
    definition: str | None = None
    pos: str | None = None


class WordPatch(BaseModel):
    status: str = Field(pattern="^(learning|retained|archived)$")


@app.get("/v1/words")
def list_words(user=Depends(auth.current_user)):
    con = db.connect()
    try:
        counts = db.serving_counts(con, user["id"])
        rows = [dict(r) for r in con.execute("SELECT * FROM words WHERE user_id=? ORDER BY id", (user["id"],))]
        for r in rows:
            r["servings"] = counts.get(r["word"], 0)
        return {"words": rows}
    finally:
        con.close()


@app.post("/v1/words", status_code=201)
def add_word(body: WordIn, user=Depends(auth.current_user)):
    word = body.word.strip().lower()
    definition = (body.definition or "").strip()
    con = db.connect()
    try:
        existing = con.execute("SELECT * FROM words WHERE user_id=? AND word=?", (user["id"], word)).fetchone()
        if existing and not definition:
            definition, body.pos = existing["definition"], body.pos or existing["pos"]
        if not definition:  # word card, minimal for M1: one cheap call for a definition (M5 enriches)
            import generate as G
            G.CALL_LOG.clear()
            raw, _ = G.call_model(
                "You write one-line dictionary definitions for an advanced ESL learner. Output STRICT "
                "JSON only: {\"pos\": \"<verb|noun|adjective|adverb>\", \"definition\": \"<one plain sentence>\"}",
                f"WORD: {word}", {"GEMINI_API_KEY": __import__('os').environ.get('GEMINI_API_KEY', ''),
                                  "ANTHROPIC_API_KEY": __import__('os').environ.get('ANTHROPIC_API_KEY', '')},
                purpose="card")
            raw = raw.strip().strip("`").removeprefix("json").strip()
            card = json.loads(raw)
            definition, body.pos = card["definition"], body.pos or card.get("pos")
            db.record_calls(con, user["id"], None, list(G.CALL_LOG), engine.PRICES)
        con.execute("INSERT INTO words (user_id, word, pos, definition, status, added) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(user_id, word) DO UPDATE SET status='learning'",
                    (user["id"], word, body.pos, definition, "learning", db.now()))
        con.commit()
        return dict(con.execute("SELECT * FROM words WHERE user_id=? AND word=?", (user["id"], word)).fetchone())
    finally:
        con.close()


@app.patch("/v1/words/{word_id}")
def patch_word(word_id: int, body: WordPatch, user=Depends(auth.current_user)):
    con = db.connect()
    try:
        cur = con.execute("UPDATE words SET status=? WHERE id=? AND user_id=?", (body.status, word_id, user["id"]))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "no such word")
        return dict(con.execute("SELECT * FROM words WHERE id=?", (word_id,)).fetchone())
    finally:
        con.close()


# ---------------------------------------------------------------- transform

class TransformIn(BaseModel):
    text: str
    title: str | None = None
    url: str | None = None
    source: str = "app"
    meta: dict | None = None   # client diagnostics, stored verbatim


def _piece_out(r) -> dict:
    d = dict(r)
    d.pop("source_text", None)
    for k in ("offered_words", "words_used"):
        d[k] = json.loads(d[k]) if d.get(k) else []
    return d


@app.post("/v1/transform", status_code=202)
def transform(body: TransformIn, user=Depends(auth.current_user)):
    text = body.text.strip()
    if len(text) < MIN_CHARS:
        raise HTTPException(422, f"need at least {MIN_CHARS} characters of text")
    text = text[:MAX_CHARS]
    con = db.connect()
    try:
        today = date.today().isoformat()
        n_today = con.execute("SELECT COUNT(*) FROM pieces WHERE user_id=? AND created_at LIKE ?",
                              (user["id"], f"{today}%")).fetchone()[0]
        if n_today >= DAILY_CAP:
            raise HTTPException(429, f"daily cap of {DAILY_CAP} transforms reached")
        pid = db.new_id("p")
        con.execute("INSERT INTO pieces (id, user_id, created_at, source, title, url, source_text, status, meta) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (pid, user["id"], db.now(), body.source, (body.title or "").strip() or None,
                     (body.url or "").strip() or None, text, "queued",
                     json.dumps(body.meta) if body.meta else None))
        con.commit()
    finally:
        con.close()
    engine.enqueue(pid)
    return {"piece_id": pid, "events_url": f"/v1/transform/{pid}/events"}


@app.get("/v1/transform/{piece_id}/events", response_class=EventSourceResponse)
async def transform_events(piece_id: str, user=Depends(auth.current_user)):
    """Phases as they happen (queued → generating → checking → regenerating → repairing →
    done|failed), then the piece. Polls the row; the writer is the engine thread."""
    last = None
    for _ in range(600):  # 5 minutes at 0.5 s
        con = db.connect()
        try:
            r = con.execute("SELECT * FROM pieces WHERE id=? AND user_id=?", (piece_id, user["id"])).fetchone()
        finally:
            con.close()
        if r is None:
            yield ServerSentEvent(event="error", raw_data="no such piece")
            return
        if r["status"] != last:
            last = r["status"]
            yield ServerSentEvent(event="phase", raw_data=last)
        if last == "done":
            yield ServerSentEvent(event="piece", data=_piece_out(r))
            return
        if last == "failed":
            yield ServerSentEvent(event="error", raw_data=r["error"] or "failed")
            return
        await asyncio.sleep(0.5)
    yield ServerSentEvent(event="error", raw_data="timed out")


# ---------------------------------------------------------------- pieces & events

@app.get("/v1/pieces")
def list_pieces(limit: int = 50, user=Depends(auth.current_user)):
    con = db.connect()
    try:
        rows = con.execute("SELECT id, created_at, source, title, url, words_used, status, latency_ms, cost_usd "
                           "FROM pieces WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user["id"], limit))
        out = []
        for r in rows:
            d = dict(r)
            d["words_used"] = json.loads(d["words_used"] or "[]")
            out.append(d)
        return {"pieces": out}
    finally:
        con.close()


@app.get("/v1/pieces/{piece_id}")
def get_piece(piece_id: str, user=Depends(auth.current_user)):
    con = db.connect()
    try:
        r = con.execute("SELECT * FROM pieces WHERE id=? AND user_id=?", (piece_id, user["id"])).fetchone()
        if r is None:
            raise HTTPException(404, "no such piece")
        return _piece_out(r)
    finally:
        con.close()


class TapIn(BaseModel):
    word: str


@app.post("/v1/pieces/{piece_id}/taps", status_code=201)
def tap(piece_id: str, body: TapIn, user=Depends(auth.current_user)):
    con = db.connect()
    try:
        if con.execute("SELECT 1 FROM pieces WHERE id=? AND user_id=?", (piece_id, user["id"])).fetchone() is None:
            raise HTTPException(404, "no such piece")
        con.execute("INSERT INTO events (user_id, piece_id, word, kind, at) VALUES (?,?,?,?,?)",
                    (user["id"], piece_id, body.word.strip().lower(), "tap", db.now()))
        con.commit()
        return {"ok": True}
    finally:
        con.close()


@app.get("/healthz")
def healthz():
    return {"ok": True}
