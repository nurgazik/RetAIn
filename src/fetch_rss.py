"""Generic RSS fetcher: stocks the candidate pool (the 'pantry', PRD §4).

Fetches every enabled source's feeds from config/sources.json and inserts new
items into the store. Makes no serving decisions. Stdlib only.

Usage: python3 src/fetch_rss.py
"""

import email.utils
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store

CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "sources.json"
USER_AGENT = "RetAIn-PoC/0.1 (personal vocabulary-retention research)"
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def canonical_id(url: str) -> str:
    return url.split("?")[0].split("#")[0].rstrip("/")


def parse_pubdate(raw: str) -> str:
    try:
        return email.utils.parsedate_to_datetime(raw).isoformat()
    except Exception:
        return raw or ""


def is_wire_content(author: str, patterns: list) -> bool:
    author_lower = (author or "").lower()
    return any(p.lower() in author_lower for p in patterns)


def extract_paragraphs(html: str) -> str:
    """Keep only substantial prose <p> blocks — drops WordPress nav/link cruft
    that some sources (NASA) ship inside content:encoded."""
    kept = []
    for p in re.findall(r"<p[^>]*>.*?</p>", html, flags=re.S):
        text = re.sub(r"<[^>]+>", "", p).strip()
        link_text = sum(len(re.sub(r"<[^>]+>", "", a)) for a in
                        re.findall(r"<a[^>]*>.*?</a>", p, flags=re.S))
        if len(text) >= 60 and link_text / max(len(text), 1) < 0.5:
            kept.append(p)
    return "\n".join(kept)


def parse_feed(xml_bytes: bytes) -> list:
    root = ET.fromstring(xml_bytes)
    parsed = []
    for it in root.findall(".//item"):
        link = (it.findtext("link") or "").strip()
        if not link:
            continue
        author = (
            it.findtext("dc:creator", "", NS) or it.findtext("author") or ""
        ).strip()
        parsed.append(
            {
                "url": link,
                "title": (it.findtext("title") or "").strip(),
                "author": author,
                "published": parse_pubdate(it.findtext("pubDate") or ""),
                "categories": [c.text.strip() for c in it.findall("category") if c.text],
                "content_html": it.findtext("content:encoded", "", NS)
                or it.findtext("description", ""),
            }
        )
    return parsed


def run() -> None:
    config = json.loads(CONFIG_PATH.read_text())
    con = store.connect()
    now = datetime.now(timezone.utc).isoformat()

    for source_name, source in config.items():
        if not source.get("enabled"):
            print(f"[skip] {source_name} (disabled)")
            continue
        if source.get("type", "rss") != "rss":
            print(f"[skip] {source_name} (type {source['type']} — has its own fetcher)")
            continue
        wire_patterns = source.get("exclude_author_patterns", [])
        for section, feed_url in source["feeds"].items():
            try:
                items = parse_feed(fetch_url(feed_url))
            except Exception as exc:
                print(f"[error] {source_name}/{section}: {exc}")
                continue
            added = rejected = 0
            for item in items:
                if source.get("content_filter") == "paragraphs_only":
                    item["content_html"] = extract_paragraphs(item["content_html"])
                wire = is_wire_content(item["author"], wire_patterns)
                inserted = store.upsert_item(
                    con,
                    {
                        **item,
                        "id": canonical_id(item["url"]),
                        "source": source_name,
                        "section": section,
                        "fetched_at": now,
                        "license": source.get("license"),
                        "status": "rejected" if wire else "fetched",
                        "notes": "wire content (excluded)" if wire else None,
                    },
                )
                if inserted:
                    added += 1
                    rejected += 1 if wire else 0
            con.commit()
            print(f"[ok] {source_name}/{section}: {len(items)} in feed, "
                  f"{added} new ({rejected} rejected as wire)")
    con.close()


if __name__ == "__main__":
    run()
