"""Candidate store + served ledger (docs/architecture.md).

One SQLite file. Items move through: fetched -> selected -> served, or -> rejected.
Rejected items stay in the store so fetchers never re-ingest and re-reject them.
"""

import json
import pathlib
import sqlite3

DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "retain.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id           TEXT PRIMARY KEY,   -- canonical article URL
    source       TEXT NOT NULL,      -- key in config/sources.json
    section      TEXT,               -- feed name the item first arrived from
    url          TEXT NOT NULL,
    title        TEXT,
    author       TEXT,
    published    TEXT,               -- ISO 8601
    fetched_at   TEXT NOT NULL,      -- ISO 8601
    status       TEXT NOT NULL DEFAULT 'fetched',
    content_html TEXT,
    categories   TEXT,               -- JSON array
    license      TEXT,
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS idx_items_status ON items (source, status, published);

CREATE TABLE IF NOT EXISTS generated_pieces (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id      TEXT NOT NULL REFERENCES items (id),
    created_at   TEXT NOT NULL,      -- ISO 8601
    model        TEXT NOT NULL,
    words_used   TEXT,               -- JSON array (the WordServing join, PoC-simple)
    title        TEXT,
    body_html    TEXT NOT NULL,
    digest_date  TEXT,               -- YYYY-MM-DD when served in a digest; NULL = test piece
    offered_words TEXT               -- JSON array: the menu offered (D32 skip-rate data)
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    for col in ("digest_date TEXT", "offered_words TEXT"):
        try:  # migrations for dbs created before these columns existed
            con.execute(f"ALTER TABLE generated_pieces ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    con.row_factory = sqlite3.Row
    return con


def upsert_item(con: sqlite3.Connection, item: dict) -> bool:
    """Insert if new. Returns True if inserted, False if already known."""
    cur = con.execute(
        """INSERT OR IGNORE INTO items
           (id, source, section, url, title, author, published, fetched_at,
            status, content_html, categories, license, notes)
           VALUES (:id, :source, :section, :url, :title, :author, :published,
                   :fetched_at, :status, :content_html, :categories, :license, :notes)""",
        {
            **item,
            "categories": json.dumps(item.get("categories", [])),
            "status": item.get("status", "fetched"),
            "notes": item.get("notes"),
        },
    )
    return cur.rowcount > 0


def set_status(con: sqlite3.Connection, item_id: str, status: str, notes: str = None):
    con.execute(
        "UPDATE items SET status = ?, notes = COALESCE(?, notes) WHERE id = ?",
        (status, notes, item_id),
    )
    con.commit()
