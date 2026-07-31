"""Calendar fetcher #2: 'News From 100 Years Ago' (bucket: calendar, D21).

Primary source: Internet Archive full-text newspapers dated exactly 100 years
ago (public domain, pre-1930). Chronicling America (loc.gov) was the original
plan but sits behind bot protection for datacenter IPs as of 2026-07 — retry
from production infra later; the IA path is equivalent for our use.

Usage: python3 src/fetch_century_news.py [YYYY-MM-DD of the historic date]
"""

import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store

USER_AGENT = "RetAIn-PoC/0.1 (personal vocabulary-retention research)"
OCR_CHAR_CAP = 16000


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def get_text(url: str, cap: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read(cap * 4).decode("utf-8", errors="replace")


def search_ia(historic: date) -> list:
    q = urllib.parse.urlencode({
        "q": f"mediatype:texts AND date:{historic.isoformat()} AND "
             f"(subject:newspapers OR collection:newspapers OR title:(newspaper))",
        "fl[]": "identifier", "rows": 30, "output": "json",
    })
    docs = get_json(f"https://archive.org/advancedsearch.php?{q}")
    return [d["identifier"] for d in docs.get("response", {}).get("docs", [])]


def looks_english(identifier: str, title: str) -> bool:
    return all(ord(c) < 128 for c in title) and all(ord(c) < 128 for c in identifier)


def is_english_text(text: str) -> bool:
    """ASCII titles can hide non-English papers (e.g. 'Diario Santa Fe') —
    check the OCR body for English function-word density."""
    words = re.findall(r"[a-z']+", text.lower())
    if len(words) < 200:
        return False
    hits = sum(1 for w in words if w in
               {"the", "and", "of", "to", "in", "that", "was", "for", "with", "his"})
    return hits / len(words) > 0.08


def run() -> None:
    today = date.today()
    historic = date(today.year - 100, today.month, today.day)
    if len(sys.argv) == 2:
        historic = date.fromisoformat(sys.argv[1])

    candidates = search_ia(historic)
    if not candidates:
        print(f"[error] no IA newspapers found for {historic}")
        return

    for identifier in candidates:
        meta = get_json(f"https://archive.org/metadata/{identifier}")
        title = str(meta.get("metadata", {}).get("title", identifier))
        if not looks_english(identifier, title):
            continue
        txt_files = [f["name"] for f in meta.get("files", [])
                     if f["name"].endswith("_djvu.txt")]
        if not txt_files:
            continue

        ocr = get_text(
            f"https://archive.org/download/{identifier}/{urllib.parse.quote(txt_files[0])}",
            OCR_CHAR_CAP)
        ocr = re.sub(r"\n{3,}", "\n\n", ocr)[:OCR_CHAR_CAP]
        if len(ocr) < 3000 or not is_english_text(ocr):
            continue

        item_id = f"ia-century-news-{historic.isoformat()}-{identifier}"
        con = store.connect()
        inserted = store.upsert_item(con, {
            "id": item_id,
            "source": "internet_archive_newspapers",
            "section": "calendar",
            "url": f"https://archive.org/details/{identifier}",
            "title": f"{title} — {historic.strftime('%B %d, %Y')}",
            "author": title,
            "published": historic.isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "content_html": f"<pre>{ocr}</pre>",
            "categories": ["calendar", "history", "newspaper"],
            "license": "Public domain (pre-1930 US)",
            "notes": f"IA identifier: {identifier}",
        })
        con.commit()
        print(f"[ok] {item_id}: '{title}', {len(ocr)} OCR chars, "
              f"{'new' if inserted else 'already present'}")
        return

    print("[error] no usable English-language OCR candidate found")


if __name__ == "__main__":
    run()
