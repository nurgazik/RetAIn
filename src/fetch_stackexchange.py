"""Stack Exchange fetcher: stocks the pantry with top-voted Q&A classics.

For each configured site, pulls the top-voted questions plus each question's
top-voted answer, and stores question + answer as one pantry item ready for
the advice-column wrapper (prompts/qa.md). Evergreen freshness class: repeat
runs are no-ops until pagination is added. Stdlib only.

API: https://api.stackexchange.com/2.3 — anonymous quota 300 req/day; this
script uses 2 requests per site.

Usage: python3 src/fetch_stackexchange.py
"""

import gzip
import json
import pathlib
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store

CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "sources.json"
API = "https://api.stackexchange.com/2.3"
USER_AGENT = "RetAIn-PoC/0.1 (personal vocabulary-retention research)"


def api_get(path: str, params: dict) -> dict:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{API}{path}?{query}",
                                 headers={"User-Agent": USER_AGENT,
                                          "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    payload = json.loads(data)
    if payload.get("backoff"):
        print(f"[warn] API asks for {payload['backoff']}s backoff "
              f"(quota left: {payload.get('quota_remaining')})")
    return payload


def top_answers(site: str, question_ids: list) -> dict:
    """Best answer per question, from one batched top-100-by-votes request.
    A question whose answers all fall outside the page is simply skipped."""
    ids = ";".join(str(q) for q in question_ids)
    payload = api_get(f"/questions/{ids}/answers",
                      {"order": "desc", "sort": "votes", "site": site,
                       "filter": "withbody", "pagesize": 100})
    best = {}
    for a in payload.get("items", []):
        qid = a["question_id"]
        if qid not in best or a["score"] > best[qid]["score"]:
            best[qid] = a
    return best


def run() -> None:
    config = json.loads(CONFIG_PATH.read_text())["stack_exchange"]
    if not config.get("enabled"):
        print("[skip] stack_exchange (disabled)")
        return

    con = store.connect()
    now = datetime.now(timezone.utc).isoformat()

    for site in config["sites"]:
        try:
            payload = api_get("/questions",
                              {"order": "desc", "sort": "votes", "site": site,
                               "filter": "withbody",
                               "pagesize": config.get("questions_per_site", 12)})
            questions = [q for q in payload.get("items", [])
                         if q.get("answer_count", 0) > 0 and q.get("body")]
            answers = top_answers(site, [q["question_id"] for q in questions])
        except Exception as exc:
            print(f"[error] {site}: {exc}")
            continue

        added = skipped = 0
        for q in questions:
            a = answers.get(q["question_id"])
            if not a:
                skipped += 1
                continue
            asker = q.get("owner", {}).get("display_name", "unknown")
            answerer = a.get("owner", {}).get("display_name", "unknown")
            inserted = store.upsert_item(con, {
                "id": q["link"].split("?")[0].rstrip("/"),
                "source": "stack_exchange",
                "section": site,
                "url": q["link"],
                "title": q["title"],
                "author": f"asked by {asker}; top answer by {answerer}",
                "published": datetime.fromtimestamp(
                    q["creation_date"], tz=timezone.utc).isoformat(),
                "fetched_at": now,
                "categories": q.get("tags", []),
                "license": config["license"],
                "content_html": (f"<h2>Question (score {q['score']})</h2>{q['body']}"
                                 f"<h2>Top answer (score {a['score']})</h2>{a['body']}"),
            })
            added += 1 if inserted else 0
        con.commit()
        print(f"[ok] {site}: {len(questions)} questions, {added} new"
              + (f" ({skipped} skipped, no answer in page)" if skipped else ""))
    con.close()


if __name__ == "__main__":
    run()
