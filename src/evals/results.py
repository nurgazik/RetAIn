"""Eval results store (data/evals.db, gitignored: it holds outputs of private reads)
and the model registry (data/evals/models.json)."""
import json
import pathlib
import sqlite3
import urllib.request

import bakeoff

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "evals.db"
REGISTRY = ROOT / "data" / "evals" / "models.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name  TEXT NOT NULL,      -- registry name (model + settings), e.g. gpt-6-luna@none
    spec        TEXT NOT NULL,      -- registry entry as run (prices, params)
    dataset     TEXT NOT NULL,      -- golden-set version hash: only same-version runs compare
    engine_mode TEXT NOT NULL,
    engine      TEXT,               -- fingerprint of pipeline code + prompts: only same-engine runs compare
    commit_id   TEXT,               -- git HEAD at run time (+ "-dirty"), for reading history
    started_at  TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS results (
    run_id      INTEGER NOT NULL REFERENCES runs(id),
    piece_id    TEXT NOT NULL,
    ok          INTEGER NOT NULL,
    error       TEXT,
    title       TEXT,
    body        TEXT,
    seconds     REAL,               -- wall clock for the whole piece (what the reader waits)
    cost_usd    REAL,               -- all calls; billed cost when the provider reports it
    tokens_in   INTEGER,
    tokens_out  INTEGER,            -- includes reasoning tokens
    tokens_reasoning INTEGER,
    n_calls     INTEGER,
    marks       INTEGER,
    coverage    REAL,               -- D40: share of 25+-word paragraphs carrying a word
    metrics     TEXT,               -- JSON: attempts, qc_rejected, invented_numbers, tiers, word counts
    PRIMARY KEY (run_id, piece_id)
);
CREATE TABLE IF NOT EXISTS calls (
    run_id INTEGER, piece_id TEXT, purpose TEXT, model TEXT,
    tokens_in INTEGER, tokens_out INTEGER, tokens_reasoning INTEGER, ms INTEGER, cost_usd REAL
);
CREATE TABLE IF NOT EXISTS grades (
    run_id      INTEGER NOT NULL,
    piece_id    TEXT NOT NULL,
    grader      TEXT NOT NULL,
    inventions  TEXT,               -- JSON list: claims absent from the source
    note_problems TEXT,             -- JSON list: false or misleading D40 notes
    raw         TEXT,
    cost_usd    REAL,
    at          TEXT NOT NULL,
    PRIMARY KEY (run_id, piece_id, grader)
);
CREATE TABLE IF NOT EXISTS marks (
    run_id   INTEGER NOT NULL,
    piece_id TEXT NOT NULL,
    n        INTEGER NOT NULL,      -- position of the <mark> in the body
    word     TEXT,
    sentence TEXT,
    grader   TEXT,
    verdict  TEXT,                  -- idiomatic | acceptable | wrong (grader)
    reason   TEXT,
    human    TEXT,                  -- idiomatic | acceptable | wrong (founder, blind)
    PRIMARY KEY (run_id, piece_id, n)
);
"""


ENGINE_FILES = ["src/generate.py", "src/service/engine.py", "src/bakeoff.py", "prompts/*.md"]


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    for col in ("engine TEXT", "commit_id TEXT"):
        try:  # migration for dbs created before these columns existed
            con.execute(f"ALTER TABLE runs ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    return con


def engine_fingerprint(mode: str) -> str:
    """Hash of everything that shapes a piece besides the model: pipeline code, prompts, mode.
    The engine is under active development; a run on a different engine isn't comparable."""
    import hashlib
    h = hashlib.sha1(mode.encode())
    for pattern in ENGINE_FILES:
        for f in sorted(ROOT.glob(pattern)):
            h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()[:10]


def git_commit() -> str:
    import subprocess
    run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = run("status", "--porcelain", "--", "src", "prompts")
    return run("rev-parse", "--short", "HEAD") + ("-dirty" if dirty else "")


# --- model registry -------------------------------------------------------------------

PROVIDERS = {  # provider → (caller factory, API key name, default params)
    "gemini": (lambda s: bakeoff.call_gemini, "GEMINI_API_KEY", {}),
    "openai": (lambda s: bakeoff.call_openai, "OPENAI_API_KEY", {}),
    "anthropic": (lambda s: bakeoff.call_anthropic, "ANTHROPIC_API_KEY", {}),
    # zdr: route only to hosts with a zero-data-retention policy (golden set holds private reads)
    "openrouter": (lambda s: bakeoff.make_openai_compat("https://openrouter.ai/api/v1"),
                   "OPENROUTER_API_KEY", {"provider": {"zdr": True}}),
    "openai_compat": (lambda s: bakeoff.make_openai_compat(s["base_url"]), None, {}),
}


def registry() -> dict:
    return json.loads(REGISTRY.read_text())


def spec(name: str) -> dict:
    for m in registry()["models"]:
        if m["name"] == name:
            return m
    raise SystemExit(f"'{name}' is not in {REGISTRY.relative_to(ROOT)} — add it first "
                     f"(python src/evals add <openrouter-slug>)")


def primary_for(s: dict) -> dict:
    """Registry entry → generate.PRIMARY shape."""
    factory, key, defaults = PROVIDERS[s["provider"]]
    return {"model": s["model"], "call": factory(s), "key": key or s["key_env"],
            "params": bakeoff.merge(json.loads(json.dumps(defaults)), s.get("params"))}


def call_cost(s: dict, tokens_in: int, tokens_out: int, billed) -> float:
    """Billed cost when the provider reports it (OpenRouter), else list price × tokens."""
    if billed is not None:
        return billed
    return tokens_in / 1e6 * s["in"] + tokens_out / 1e6 * s["out"]


def add_openrouter(slug: str, name: str = None, params: dict = None) -> dict:
    """Add an OpenRouter model to the registry with its current list price (public API)."""
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60) as r:
        models = {m["id"]: m for m in json.loads(r.read())["data"]}
    if slug not in models:
        close = [k for k in models if slug.split("/")[-1][:6] in k][:10]
        raise SystemExit(f"'{slug}' not on OpenRouter. Close matches: {close}")
    m = models[slug]
    entry = {"name": name or slug.split("/")[-1], "provider": "openrouter", "model": slug,
             "in": round(float(m["pricing"]["prompt"]) * 1e6, 4),
             "out": round(float(m["pricing"]["completion"]) * 1e6, 4),
             "params": params or {}, "price_source": "openrouter /api/v1/models (list price)",
             "added": __import__("datetime").date.today().isoformat()}
    reg = registry()
    reg["models"] = [x for x in reg["models"] if x["name"] != entry["name"]] + [entry]
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")
    return entry
