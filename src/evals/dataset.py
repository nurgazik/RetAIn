"""Golden dataset: a frozen set of source texts + one frozen word list, so every model run
is measured on identical inputs. One JSON file per piece under data/evals/golden/:
  private/  the founder's own reads (service.db, G2 fixtures) — gitignored, never shared
  public/   licensed texts (pantry: Global Voices, NASA, Stack Exchange; Wikipedia)
`build` only adds pieces that aren't there yet; delete a file to retire a piece (this
changes the dataset version, so older runs stop being comparable).
"""
import hashlib
import html as html_mod
import json
import pathlib
import random
import re
import sqlite3
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GOLDEN = ROOT / "data" / "evals" / "golden"
WORDS = GOLDEN / "words.json"

READ_SOURCES = ("action-ext", "app-paste", "paste", "share-ext")  # real reads; test rows excluded
PANTRY_PICKS = {"global_voices": 4, "nasa": 3, "stack_exchange": 3}
WIKIPEDIA = [("Great Stink", "history"), ("Tardigrade", "science"), ("Bauhaus", "culture")]
MIN_WORDS, MAX_WORDS = 150, 2000


def words_in(text: str) -> int:
    return len(text.split())


def html_to_text(content_html: str) -> str:
    """Pantry HTML → plain paragraphs separated by blank lines."""
    blocks = re.findall(r"<(?:p|li|h\d|blockquote)[^>]*>(.*?)</(?:p|li|h\d|blockquote)>", content_html, re.S)
    if not blocks:
        blocks = [content_html]
    paras = [html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))).strip() for b in blocks]
    return "\n\n".join(p for p in paras if p)


def normalized(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()[:400]


def load() -> list:
    return [json.loads(p.read_text()) for p in sorted(GOLDEN.glob("*/*.json"))]


def load_words() -> list:
    return json.loads(WORDS.read_text())["words"]


def version(pieces: list = None) -> str:
    """Hash of every piece's id + text and the word list: runs compare only on equal versions."""
    h = hashlib.sha1()
    for p in sorted(pieces or load(), key=lambda p: p["id"]):
        h.update(p["id"].encode() + p["text"].encode())
    h.update(WORDS.read_bytes())
    return h.hexdigest()[:10]


def write(piece: dict, seen: set) -> bool:
    path = GOLDEN / piece["split"] / f"{piece['id']}.json"
    key = normalized(piece["text"])
    n = words_in(piece["text"])
    if path.exists() or key in seen or not MIN_WORDS <= n <= MAX_WORDS:
        return False
    seen.add(key)
    path.write_text(json.dumps({**piece, "words": n}, indent=1, ensure_ascii=False) + "\n")
    print(f"  + {piece['split']}/{piece['id']} ({n} words, {piece['genre']})")
    return True


def build() -> None:
    GOLDEN.joinpath("private").mkdir(parents=True, exist_ok=True)
    GOLDEN.joinpath("public").mkdir(parents=True, exist_ok=True)
    seen = {normalized(p["text"]) for p in load()}
    svc = sqlite3.connect(ROOT / "data" / "service.db")
    svc.row_factory = sqlite3.Row
    # both service accounts are the founder's: the Sign in with Apple account (real words)
    # and the dev-token account (device/curl tests). Reads come from both; words from the real one.
    founder = svc.execute("SELECT id FROM users WHERE apple_sub != 'dev' ORDER BY created_at").fetchone()[0]

    if not WORDS.exists():
        # frozen menu: the founder's learning words in the order the service offers them
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from service import db as svc_db
        rows = svc_db.learning_words(svc, founder)
        WORDS.write_text(json.dumps({"_readme": "Frozen eval word menu (founder's learning words, "
                                     "service order). Changing it changes the dataset version.",
                                     "words": [{"word": r["word"], "pos": r["pos"],
                                                "definition": r["definition"]} for r in rows]},
                                    indent=1, ensure_ascii=False) + "\n")
        print(f"  + words.json ({len(rows)} words)")

    print("private: founder's reads")
    for r in svc.execute(f"SELECT id, source, title, url, source_text FROM pieces "
                         f"WHERE source IN ({','.join('?' * len(READ_SOURCES))}) ORDER BY created_at",
                         READ_SOURCES):
        write({"id": f"read-{r['id'][-8:]}", "split": "private", "genre": "user-read",
               "source": r["source"], "license": "private (founder's read)", "url": r["url"] or "",
               "title": r["title"] or "", "text": r["source_text"].strip()}, seen)
    for f in sorted((ROOT / "data" / "g2-pieces").glob("*.txt")):
        write({"id": f"g2-{f.stem}", "split": "private", "genre": "user-read", "source": "g2-fixture",
               "license": "private (founder's read)", "url": "",
               "title": f.stem.split("-", 1)[1].replace("-", " ").title(), "text": f.read_text().strip()}, seen)

    print("public: pantry (licensed)")
    pantry = sqlite3.connect(ROOT / "data" / "retain.db")
    pantry.row_factory = sqlite3.Row
    rng = random.Random(26)
    for source, n in PANTRY_PICKS.items():
        rows = [r for r in pantry.execute("SELECT * FROM items WHERE source=? ORDER BY id", (source,))
                if MIN_WORDS <= words_in(html_to_text(r["content_html"])) <= MAX_WORDS]
        added = sum(p["source"] == source for p in load())  # quota counts pieces already frozen
        for r in rng.sample(rows, len(rows)):
            if added >= n:
                break
            slug = re.sub(r"\W+", "-", html_mod.unescape(r["title"]).lower()).strip("-")[:40]
            added += write({"id": f"{source.replace('_', '')}-{slug}", "split": "public",
                            "genre": {"global_voices": "news", "nasa": "science",
                                      "stack_exchange": "forum"}[source],
                            "source": source, "license": r["license"] or "", "url": r["url"] or r["id"],
                            "title": html_mod.unescape(r["title"]), "text": html_to_text(r["content_html"])}, seen)

    print("public: Wikipedia (CC BY-SA 4.0)")
    for title, genre in WIKIPEDIA:
        q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1,
                                    "format": "json", "titles": title, "redirects": 1})
        req = urllib.request.Request(f"https://en.wikipedia.org/w/api.php?{q}",
                                     headers={"User-Agent": "RetAIn-evals/0.1 (private eval set)"})
        page = next(iter(json.loads(urllib.request.urlopen(req, timeout=60).read())["query"]["pages"].values()))
        paras, total = [], 0
        for para in page["extract"].split("\n"):
            para = para.strip()
            if para.startswith("==") and total > 500:
                break  # intro + first sections, ~500-900 words
            if para and not para.startswith("=="):
                paras.append(para)
                total += words_in(para)
        slug = re.sub(r"\W+", "-", title.lower())
        write({"id": f"wikipedia-{slug}", "split": "public", "genre": genre,
               "source": "wikipedia", "license": "CC BY-SA 4.0",
               "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
               "title": title, "text": "\n\n".join(paras)}, seen)

    pieces = load()
    print(f"golden set: {len(pieces)} pieces "
          f"({sum(p['split'] == 'private' for p in pieces)} private, "
          f"{sum(p['split'] == 'public' for p in pieces)} public), "
          f"{sum(p['words'] for p in pieces)} words, version {version(pieces)}")
