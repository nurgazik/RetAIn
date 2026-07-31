"""Calendar fetcher #1: Wikipedia 'On This Day' (bucket: calendar, D21).

Pulls today's curated events from the Wikimedia REST feed and stores one
pantry item per date. License: CC BY-SA (share-alike applies to the rewrite).

Usage: python3 src/fetch_onthisday.py [MM DD]
"""

import html
import json
import pathlib
import sys
import urllib.request
from datetime import date, datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store

USER_AGENT = "RetAIn-PoC/0.1 (personal vocabulary-retention research)"
MAX_EVENTS = 9


def fetch(mm: str, dd: str) -> dict:
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{mm}/{dd}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def build_content(events: list) -> str:
    events = sorted(events, key=lambda e: e.get("year", 0))
    # spread selections across the timeline rather than clustering modern ones
    step = max(1, len(events) // MAX_EVENTS)
    chunks = []
    for ev in events[::step][:MAX_EVENTS]:
        year = ev.get("year", "?")
        text = html.escape(ev.get("text", "").strip())
        extract = ""
        for page in ev.get("pages", [])[:1]:
            extract = html.escape(page.get("extract", "").strip())
        chunks.append(f"<h3>{year}</h3><p>{text}</p>"
                      + (f"<p><i>Context:</i> {extract}</p>" if extract else ""))
    return "\n".join(chunks)


def run() -> None:
    today = date.today()
    mm, dd = f"{today.month:02d}", f"{today.day:02d}"
    if len(sys.argv) == 3:
        mm, dd = sys.argv[1], sys.argv[2]

    data = fetch(mm, dd)
    events = data.get("selected", [])
    if not events:
        print(f"[error] no events returned for {mm}/{dd}")
        return

    item_id = f"wikipedia-onthisday-{mm}-{dd}-{today.year}"
    con = store.connect()
    inserted = store.upsert_item(con, {
        "id": item_id,
        "source": "wikipedia_onthisday",
        "section": "calendar",
        "url": f"https://en.wikipedia.org/wiki/Wikipedia:Selected_anniversaries/{today.strftime('%B')}_{int(dd)}",
        "title": f"On this day — {today.strftime('%B')} {int(dd)}",
        "author": "Wikipedia contributors",
        "published": datetime.now(timezone.utc).isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_html": build_content(events),
        "categories": ["calendar", "history"],
        "license": "CC BY-SA 4.0",
        "notes": None,
    })
    con.commit()
    print(f"[ok] {item_id}: {len(events)} events in feed, "
          f"{MAX_EVENTS} kept, {'new' if inserted else 'already present'}")


if __name__ == "__main__":
    run()
