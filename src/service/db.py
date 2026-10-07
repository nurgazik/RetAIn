"""SQLite schema for the service: users, words, pieces, events, calls. One writer, WAL mode."""
import json
import sqlite3
import threading
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import DAY_STARTS_HOUR, DB_PATH, TZ

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    apple_sub   TEXT UNIQUE,
    email       TEXT,
    created_at  TEXT NOT NULL,
    tz          TEXT,            -- IANA name the app last sent (D51)
    last_day    TEXT             -- the latest day key seen; the day never moves back
);
CREATE TABLE IF NOT EXISTS words (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES users(id),
    word        TEXT NOT NULL,
    pos         TEXT,
    definition  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'learning',   -- learning | retained | archived (D26)
    added       TEXT NOT NULL,
    day         TEXT NOT NULL DEFAULT '',   -- the user's day it was added (D51)
    UNIQUE (user_id, word)
);
-- Word cards (D48): shared by every user, no user data. One row per headword (the dictionary
-- form: "ran" is stored under "run"); its meanings in Wiktionary order in `senses`.
CREATE TABLE IF NOT EXISTS lexicon (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    headword    TEXT NOT NULL UNIQUE,
    source      TEXT NOT NULL,       -- wiktionary | model
    ipa         TEXT,                -- JSON [{"ipa", "tags"}], at most two
    source_url  TEXT,                -- the wiktionary.org entry (CC BY-SA attribution)
    dump        TEXT,                -- which Wiktionary download it came from
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS senses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lexicon_id  INTEGER NOT NULL REFERENCES lexicon(id),
    ord         INTEGER NOT NULL,    -- Wiktionary's order
    pos         TEXT,
    gloss       TEXT NOT NULL,
    tags        TEXT,                -- JSON ["formal", "figuratively", ...]
    examples    TEXT,                -- JSON ["...", ...] written by the model; NULL = not written yet
    UNIQUE (lexicon_id, ord)
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
    meta          TEXT,            -- JSON: client diagnostics (payload types, app build)
    byline        TEXT,             -- page metadata from the Safari extension, shown in the
    site_name     TEXT,             -- reader's header; never sent to the model
    published     TEXT,
    dek           TEXT,             -- summary / sub-headline lines, blank-line separated
    day           TEXT NOT NULL DEFAULT ''   -- the user's day (D51); the cap counts it
);
CREATE INDEX IF NOT EXISTS idx_pieces_user ON pieces (user_id, created_at);
CREATE TABLE IF NOT EXISTS events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   TEXT NOT NULL,
    piece_id  TEXT NOT NULL,
    word      TEXT,
    kind      TEXT NOT NULL,        -- tap | impression
    at        TEXT NOT NULL,
    day       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS diagnostics (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   TEXT,
    kind      TEXT NOT NULL,        -- unusable-share | ...
    payload   TEXT,                 -- JSON: types, char counts, flags — never content
    at        TEXT NOT NULL
);
-- Daily practice (D56): today's set per user (keyed by the user's day, D51), every answer, and
-- model-written fill-in sentences shared by all users (no user data, like word cards).
CREATE TABLE IF NOT EXISTS practice_sets (
    user_id     TEXT NOT NULL REFERENCES users(id),
    day         TEXT NOT NULL,
    items       TEXT NOT NULL,      -- JSON: word_id, word, definition, box, fill {text, answer, source}
    created_at  TEXT NOT NULL,
    PRIMARY KEY (user_id, day)
);
CREATE TABLE IF NOT EXISTS practice_attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES users(id),
    word_id     INTEGER NOT NULL REFERENCES words(id),
    day         TEXT NOT NULL,
    kind        TEXT NOT NULL,      -- fill | write
    answer      TEXT NOT NULL,      -- what the user typed
    correct     INTEGER,            -- fill: code's check
    verdict     TEXT,               -- write: natural | could-be-better | wrong
    reason      TEXT,
    fix         TEXT,
    p_natural   REAL,               -- write: Jev's P(natural); NULL if Jev failed
    judged_by   TEXT,               -- write: jev (✓ at the threshold) | llm
    hint        TEXT,               -- fill: the options the Hint showed (JSON); NULL = no hint
    created_at  TEXT NOT NULL
);
-- hint lookalikes per lemma, shared by all users (no user data, like practice_sentences; D58).
CREATE TABLE IF NOT EXISTS lookalikes (
    word        TEXT PRIMARY KEY,   -- the lemma
    candidates  TEXT NOT NULL,      -- JSON: up to 5 that passed the code check; Jev picks per sentence
    model       TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS practice_sentences (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    word        TEXT NOT NULL,
    sentence    TEXT NOT NULL,
    answer      TEXT NOT NULL,      -- the word as it appears in the sentence
    p_natural   REAL,               -- Jev's check when written
    created_at  TEXT NOT NULL
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
    ms         INTEGER,
    at         TEXT NOT NULL,
    response   TEXT,                -- the model's raw output, before any parsing or guard
    prompt_sha TEXT,                -- first 12 hex of sha1(system prompt): which prompt version
    host       TEXT,                -- who served it: an OpenRouter host (makora, venice…) or google
    day        TEXT NOT NULL DEFAULT '',  -- the user's day (the piece's, for engine calls)
    attempt_id INTEGER                -- the practice attempt this call judged (practice_attempts.id)
);
"""

_lock = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


# ---------------------------------------------------------------- the user's day (D51)
# Every row carries `day` — the user's local date, starting at 4 am — beside its UTC time.
# See docs/architecture.md "The user's day" and diagrams/infra-user-day.md.

def zone(name: str | None) -> ZoneInfo | None:
    """A timezone from its IANA name (America/Toronto); None for missing or unknown names."""
    if not name or len(name) > 64:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def day_of(at: datetime, tz: ZoneInfo) -> str:
    """The day key for a moment: local date, with days starting at DAY_STARTS_HOUR."""
    return (at.astimezone(tz) - timedelta(hours=DAY_STARTS_HOUR)).date().isoformat()


def next_day_at(day: str, tz: ZoneInfo) -> str:
    """When the day after `day` starts, in UTC."""
    start = datetime.combine(date.fromisoformat(day) + timedelta(days=1), time(DAY_STARTS_HOUR), tz)
    return start.astimezone(timezone.utc).isoformat(timespec="seconds")


def server_day() -> str:
    """The day for writes with no user (dictionary backfill): the fallback timezone."""
    return day_of(datetime.now(timezone.utc), TZ)


def resolve_day(con, user: dict, tz_name: str | None, at: datetime | None = None) -> dict:
    """The user row + tz, day and next_day_at. Saves a new valid timezone from the app, and
    the day as users.last_day; the day never moves back (a flight west can't replay one)."""
    sent = zone(tz_name)
    tz = sent or zone(user.get("tz")) or TZ
    day = day_of(at or datetime.now(timezone.utc), tz)
    last = user.get("last_day")
    if last and last > day:
        day = last
    changes = {k: v for k, v in (("tz", sent and sent.key), ("last_day", day)) if v and v != user.get(k)}
    if changes:
        with _lock:
            con.execute(f"UPDATE users SET {', '.join(f'{k}=?' for k in changes)} WHERE id=?",
                        (*changes.values(), user["id"]))
            con.commit()
    return user | changes | {"tz": tz.key, "day": day, "next_day_at": next_day_at(day, tz)}


def _backfill_days(con) -> None:
    """Rows written before D51 get their day from the UTC stamp in the fallback timezone."""
    for table, col in (("pieces", "created_at"), ("calls", "at"), ("events", "at"), ("words", "added")):
        rows = con.execute(f"SELECT rowid, {col} FROM {table} WHERE day = ''").fetchall()
        for rowid, stamp in rows:
            if len(stamp) == 10:  # a bare date (hand-written words.json): already a day
                day = stamp
            else:
                at = datetime.fromisoformat(stamp)
                day = day_of(at if at.tzinfo else at.replace(tzinfo=timezone.utc), TZ)
            con.execute(f"UPDATE {table} SET day=? WHERE rowid=?", (day, rowid))
        if rows:
            print(f"[db] {table}: day set on {len(rows)} older rows")


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
    for stmt in ("ALTER TABLE pieces ADD COLUMN meta TEXT", "ALTER TABLE calls ADD COLUMN ms INTEGER",
                 "ALTER TABLE calls ADD COLUMN response TEXT", "ALTER TABLE calls ADD COLUMN prompt_sha TEXT",
                 "ALTER TABLE pieces ADD COLUMN byline TEXT", "ALTER TABLE pieces ADD COLUMN site_name TEXT",
                 "ALTER TABLE pieces ADD COLUMN published TEXT", "ALTER TABLE pieces ADD COLUMN dek TEXT",
                 "ALTER TABLE words ADD COLUMN lexicon_id INTEGER REFERENCES lexicon(id)",
                 "ALTER TABLE calls ADD COLUMN host TEXT",
                 "ALTER TABLE users ADD COLUMN tz TEXT", "ALTER TABLE users ADD COLUMN last_day TEXT",
                 "ALTER TABLE words ADD COLUMN box INTEGER NOT NULL DEFAULT 0",  # practice schedule (D56)
                 "ALTER TABLE words ADD COLUMN due_day TEXT",                    # NULL = never practised
                 "ALTER TABLE practice_attempts ADD COLUMN p_natural REAL",      # full judging record
                 "ALTER TABLE practice_attempts ADD COLUMN judged_by TEXT",
                 "ALTER TABLE calls ADD COLUMN attempt_id INTEGER",
                 "ALTER TABLE practice_attempts ADD COLUMN hint TEXT",           # fill hint (D58)
                 *(f"ALTER TABLE {t} ADD COLUMN day TEXT NOT NULL DEFAULT ''" for t in ("pieces", "calls", "events", "words"))):
        try:  # migrations for DBs created before these columns
            con.execute(stmt)
        except sqlite3.OperationalError:
            pass
    for t in ("pieces", "calls", "events", "words"):  # after the migrations: old DBs lack `day` until then
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_day ON {t} (user_id, day)")
    _backfill_days(con)
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
    """Every learning word, fewest servings first (D32's sort, D34: no scheduler).
    Unverified words (no card, no definition — D48) never reach a rewrite."""
    counts = serving_counts(con, user_id)
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM words WHERE user_id=? AND status='learning' AND definition != '' ORDER BY id", (user_id,))]
    return sorted(rows, key=lambda w: counts.get(w["word"], 0))


def record_calls(con, user_id: str, piece_id: str | None, calls: list, prices: dict, *, day: str,
                 attempt_id: int | None = None) -> float:
    """calls: [(purpose, model, tokens_in, tokens_out[, ms[, billed_usd[, reasoning, response, prompt_sha[, host]]]])]
    → rows in `calls`; returns USD total."""
    total = 0.0
    with _lock:
        for c in calls:
            purpose, model, tin, tout = c[:4]
            ms = c[4] if len(c) > 4 else None
            p = prices.get(model, {"in": 0.0, "out": 0.0})
            billed = c[5] if len(c) > 5 else None  # OpenRouter reports the billed cost
            usd = billed if billed is not None else tin / 1e6 * p["in"] + tout / 1e6 * p["out"]
            total += usd
            response, prompt_sha = (c[7], c[8]) if len(c) > 8 else (None, None)
            host = c[9] if len(c) > 9 else None
            con.execute("INSERT INTO calls (user_id, piece_id, purpose, model, tokens_in, tokens_out, usd, ms, at, "
                        "response, prompt_sha, host, day, attempt_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (user_id, piece_id, purpose, model, tin, tout, usd, ms, now(), response, prompt_sha, host, day,
                         attempt_id))
        con.commit()
    return total
