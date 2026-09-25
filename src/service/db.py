"""SQLite schema for the service: users, words, pieces, events, calls. One writer, WAL mode."""
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    apple_sub   TEXT UNIQUE,
    email       TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS words (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES users(id),
    word        TEXT NOT NULL,
    pos         TEXT,
    definition  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'learning',   -- learning | retained | archived (D26)
    added       TEXT NOT NULL,
    UNIQUE (user_id, word)
);
CREATE TABLE IF NOT EXISTS pieces (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id),
    created_at    TEXT NOT NULL,
    source        TEXT,             -- share-ext | action-ext | app-paste | shortcut | ...
    title         TEXT,
    url           TEXT,
    source_text   TEXT NOT NULL,
    body_html     TEXT,
    attrib        TEXT,
    offered_words TEXT,             -- JSON
    words_used    TEXT,             -- JSON
    model         TEXT,
    status        TEXT NOT NULL,    -- queued | generating | checking | regenerating | repairing | done | failed
    error         TEXT,
    latency_ms    INTEGER,
    cost_usd      REAL,
    meta          TEXT             -- JSON: client diagnostics (payload types, app build)
);
CREATE INDEX IF NOT EXISTS idx_pieces_user ON pieces (user_id, created_at);
CREATE TABLE IF NOT EXISTS events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   TEXT NOT NULL,
    piece_id  TEXT NOT NULL,
    word      TEXT,
    kind      TEXT NOT NULL,        -- tap | impression
    at        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS diagnostics (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   TEXT,
    kind      TEXT NOT NULL,        -- unusable-share | ...
    payload   TEXT,                 -- JSON: types, char counts, flags — never content
    at        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS calls (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT,
    piece_id   TEXT,
    purpose    TEXT NOT NULL,       -- generate | qc | fact | repair | card
    model      TEXT NOT NULL,
    tokens_in  INTEGER,
    tokens_out INTEGER,
    usd        REAL,
    at         TEXT NOT NULL
);
"""

_lock = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=5000")
    return con


def init() -> None:
    con = connect()
    con.executescript(SCHEMA)
    try:  # migration for DBs created before `meta`
        con.execute("ALTER TABLE pieces ADD COLUMN meta TEXT")
    except sqlite3.OperationalError:
        pass
    con.commit()
    con.close()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def upsert_user(con, apple_sub: str, email: str | None) -> tuple:
    """Returns (user_row, created)."""
    row = con.execute("SELECT * FROM users WHERE apple_sub=?", (apple_sub,)).fetchone()
    if row:
        return row, False
    uid = new_id("u")
    with _lock:
        con.execute("INSERT INTO users (id, apple_sub, email, created_at) VALUES (?,?,?,?)",
                    (uid, apple_sub, email, now()))
        con.commit()
    return con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone(), True


def serving_counts(con, user_id: str) -> dict:
    counts = {}
    for r in con.execute("SELECT words_used FROM pieces WHERE user_id=? AND status='done'", (user_id,)):
        for w in json.loads(r["words_used"] or "[]"):
            counts[w] = counts.get(w, 0) + 1
    return counts


def learning_words(con, user_id: str) -> list:
    """Every learning word, fewest servings first (D32's sort, D34: no scheduler)."""
    counts = serving_counts(con, user_id)
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM words WHERE user_id=? AND status='learning' ORDER BY id", (user_id,))]
    return sorted(rows, key=lambda w: counts.get(w["word"], 0))


def record_calls(con, user_id: str, piece_id: str | None, calls: list, prices: dict) -> float:
    """calls: [(purpose, model, tokens_in, tokens_out)] → rows in `calls`; returns USD total."""
    total = 0.0
    with _lock:
        for purpose, model, tin, tout in calls:
            p = prices.get(model, {"in": 0.0, "out": 0.0})
            usd = tin / 1e6 * p["in"] + tout / 1e6 * p["out"]
            total += usd
            con.execute("INSERT INTO calls (user_id, piece_id, purpose, model, tokens_in, tokens_out, usd, at) "
                        "VALUES (?,?,?,?,?,?,?,?)", (user_id, piece_id, purpose, model, tin, tout, usd, now()))
        con.commit()
    return total
