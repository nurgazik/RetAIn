"""Streaks and stats (D74). The phone reports what happened (taps, piece opens, words shown) into `events`;
the server logs what it decides (answers in practice_attempts, other word changes in word_log). Every stat is
worked out here when it's asked for; nothing is stored as a counter, so a counting rule can change later
without losing history. See docs/streaks-stats-research.md and diagrams/flow-streaks-and-shown.md."""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from statistics import median

from . import db
from .config import TZ

KINDS = {"tap", "open", "shown", "card", "listen", "hint"}  # card: its card opened; listen: pronunciation played;
                                                            # hint: a practice hint asked for (with what it showed)
HINTED = {"fill", "hangman"}                                # the exercises that have a hint
SURFACES = {"reader", "practice", "words"}          # where it happened (words = the Words tab or a widget link)
EXERCISES = {"fill", "write", "hangman"}
FUTURE = timedelta(minutes=10)   # phone clocks run a little fast
LATE = timedelta(days=3)         # an event queued offline longer than this is dropped


# ---------------------------------------------------------------- word history (server-decided changes)

def log_word(con, user: dict, word_id: int, kind: str, status_before: str | None, status_after: str,
             box_before: int | None = None, box_after: int | None = None) -> None:
    """One word_log row. The caller commits, so the change and its log row land together."""
    con.execute("INSERT INTO word_log (user_id, word_id, day, kind, status_before, status_after, box_before, "
                "box_after, at) VALUES (?,?,?,?,?,?,?,?,?)",
                (user["id"], word_id, user["day"], kind, status_before, status_after, box_before, box_after, db.now()))


# ---------------------------------------------------------------- events from the phone

def _parse_at(raw) -> datetime | None:
    try:
        at = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    return at if at.tzinfo else None  # a time without a zone can't be placed in the user's day


def _check(con, user: dict, e: dict, now: datetime, owned_pieces: dict, words: list) -> tuple:
    """One event → (row values, None) or (None, the reason it's rejected)."""
    kind, surface = e.get("kind"), e.get("surface") or "reader"
    if not isinstance(e.get("id"), str) or not 8 <= len(e["id"]) <= 64:
        return None, "id"
    if kind not in KINDS or surface not in SURFACES:
        return None, "kind"
    at = _parse_at(e.get("at"))
    if at is None:
        return None, "at"
    if at > now + FUTURE:
        return None, "future"
    if at < now - LATE:
        return None, "too old"
    word, word_id, piece_id, exercise = None, None, None, None
    detail = str(e["detail"])[:500] if kind == "hint" and e.get("detail") else None
    if kind in ("card", "listen"):  # looked the word up (not "shown", D74): any surface, by the word's id
        word_id = e.get("word_id")
        if not any(w[0] == word_id for w in words):
            return None, "word"
        word = next(w[1] for w in words if w[0] == word_id)
    elif surface == "reader":
        piece_id = e.get("piece_id")
        if piece_id not in owned_pieces:
            ok = piece_id and con.execute("SELECT 1 FROM pieces WHERE id=? AND user_id=?",
                                          (piece_id, user["id"])).fetchone() is not None
            owned_pieces[piece_id] = ok
        if not owned_pieces[piece_id]:
            return None, "piece"
        if kind != "open":
            word = (e.get("word") or "").strip().lower()[:60]
            if not word:
                return None, "word"
            word_id = db.match_word(word, words)
    elif surface == "practice":
        exercise, word_id = e.get("exercise"), e.get("word_id")
        if not (kind == "shown" and exercise in EXERCISES or kind == "hint" and exercise in HINTED):
            return None, "kind"
        if not any(w[0] == word_id for w in words):
            return None, "word"
        word = next(w[1] for w in words if w[0] == word_id)
    else:
        return None, "kind"
    day = db.day_of(at, db.zone(user["tz"]) or TZ)
    return (user["id"], e["id"], kind, surface, piece_id, exercise, word, word_id,
            at.astimezone(timezone.utc).isoformat(timespec="microseconds"), day, db.now(), detail), None


def ingest(con, user: dict, events: list) -> dict:
    """A batch from the phone's queue. Each event is kept, ignored as a resend (same id), or rejected with a
    reason; all three are final, so the phone drops them from its queue either way."""
    now = datetime.now(timezone.utc)
    words = con.execute("SELECT id, word FROM words WHERE user_id=?", (user["id"],)).fetchall()
    owned, kept, again, rejected = {}, 0, 0, []
    with db._lock:
        for e in events:
            e = e if isinstance(e, dict) else {}
            row, why = _check(con, user, e, now, owned, words)
            if why:
                rejected.append({"id": e.get("id"), "reason": why})
                continue
            cur = con.execute("INSERT OR IGNORE INTO events (user_id, client_id, kind, surface, piece_id, exercise, "
                              "word, word_id, at, day, received_at, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)
            kept, again = kept + cur.rowcount, again + (1 - cur.rowcount)
        con.commit()
    return {"kept": kept, "duplicates": again, "rejected": rejected}


# ---------------------------------------------------------------- streaks (D74)

def active_days(con, user_id: str) -> list:
    """Days that count (D74): the user answered a practice exercise or read a piece. Sorted, distinct.
    (Later: a day saved with points joins this list as its own fact.)"""
    return [r[0] for r in con.execute(
        "SELECT day FROM practice_attempts WHERE user_id=? UNION "
        "SELECT day FROM events WHERE user_id=? AND kind='open' ORDER BY 1", (user_id, user_id))]


def runs(days: list) -> list:
    """Consecutive days → [(first, last, length)], oldest first ("gaps and islands")."""
    out = []
    for d in days:
        if out and date.fromisoformat(d) - date.fromisoformat(out[-1][1]) == timedelta(days=1):
            out[-1] = (out[-1][0], d, out[-1][2] + 1)
        else:
            out.append((d, d, 1))
    return out


def streak(days: list, today: str) -> dict:
    """Current streak = the run ending today or yesterday (today isn't over yet); a missed day resets it (no
    protection until points exist, D74). Best = the longest run. Total = every day that counted."""
    rs = runs(days)
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    current = rs[-1][2] if rs and rs[-1][1] in (today, yesterday) else 0
    return {"current": current, "best": max((r[2] for r in rs), default=0),
            "today_counts": bool(days) and days[-1] == today, "total_days": len(days)}


# ---------------------------------------------------------------- what the app asks for

def user_stats(con, user: dict) -> dict:
    uid, day = user["id"], user["day"]
    one = lambda sql: con.execute(sql, (uid, day)).fetchone()[0]
    return {"day": day, "streak": streak(active_days(con, uid), day),
            "today": {"answers": one("SELECT COUNT(*) FROM practice_attempts WHERE user_id=? AND day=?"),
                      "words_practised": one("SELECT COUNT(DISTINCT word_id) FROM practice_attempts "
                                             "WHERE user_id=? AND day=?"),
                      "pieces_read": one("SELECT COUNT(DISTINCT piece_id) FROM events "
                                         "WHERE user_id=? AND day=? AND kind='open'"),
                      "words_shown": one("SELECT COUNT(DISTINCT word_id) FROM events "
                                         "WHERE user_id=? AND day=? AND kind='shown' AND word_id IS NOT NULL")}}


def _result(a) -> str:
    if a["kind"] == "write":
        return a["verdict"] or "unjudged"
    if a["kind"] == "hangman":
        return "won" if a["correct"] else "lost"
    return "right" if a["correct"] else "wrong"


def _first_tries(attempts) -> list:
    """The first try of each exercise on each day: what the schedule judges (D58)."""
    seen, out = set(), []
    for a in attempts:
        if (a["day"], a["kind"]) not in seen:
            seen.add((a["day"], a["kind"]))
            out.append(a)
    return out


def _clean(a) -> bool:
    return bool(a["correct"]) if a["kind"] != "write" else a["verdict"] == "natural"


def _days_between(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def word_stats(con, user: dict, word_id: int) -> dict | None:
    """One word's history. "Shown" counts once per piece per day in the reader and once per exercise per day
    in practice (D74; the rule is applied here, the raw events are all kept)."""
    w = con.execute("SELECT * FROM words WHERE id=? AND user_id=? AND status!='deleted'",
                    (word_id, user["id"])).fetchone()
    if w is None:
        return None
    one = lambda sql: con.execute(sql, (user["id"], word_id)).fetchone()[0]
    attempts = con.execute("SELECT * FROM practice_attempts WHERE user_id=? AND word_id=? ORDER BY id",
                           (user["id"], word_id)).fetchall()
    answers = {}
    for a in attempts:
        k = answers.setdefault(a["kind"], {"tries": 0})
        k["tries"] += 1
        k[_result(a)] = k.get(_result(a), 0) + 1
    changes = [dict(r) for r in con.execute(
        "SELECT day, kind, status_before, status_after FROM word_log WHERE user_id=? AND word_id=? ORDER BY id",
        (user["id"], word_id))]
    retained = [c["day"] for c in changes if c["kind"] == "retained"]
    firsts = _first_tries(attempts)
    fills = [a for a in attempts if a["kind"] == "fill"]
    fill_days = {a["day"] for a in fills}
    games = con.execute("SELECT wrong, hint, won, seconds FROM hangman_games WHERE user_id=? AND word_id=? "
                        "ORDER BY id", (user["id"], word_id)).fetchall()
    secs = {}
    for a in attempts:
        if a["seconds"] is not None and a["kind"] != "hangman":   # hangman's time lives on its game row (D69)
            secs.setdefault(a["kind"], []).append(a["seconds"])
    for g in games:
        if g["seconds"] is not None:
            secs.setdefault("hangman", []).append(g["seconds"])
    shown_reader = one("SELECT COUNT(*) FROM (SELECT DISTINCT day, piece_id FROM events WHERE user_id=? "
                       "AND word_id=? AND kind='shown' AND surface='reader')")
    taps_counted = one("SELECT COUNT(*) FROM (SELECT DISTINCT day, piece_id FROM events WHERE user_id=? "
                       "AND word_id=? AND kind='tap')")
    seen_days = [r[0] for r in con.execute(
        "SELECT day FROM events WHERE user_id=? AND word_id=? AND kind='shown' UNION "
        "SELECT day FROM practice_attempts WHERE user_id=? AND word_id=? ORDER BY 1 DESC LIMIT 1",
        (user["id"], word_id, user["id"], word_id))]
    hints, to_hint = {}, {}
    shown_at = {}   # (day, exercise) → when the exercise last appeared
    for r in con.execute("SELECT kind, exercise, day, at FROM events WHERE user_id=? AND word_id=? AND "
                         "surface='practice' AND kind IN ('shown', 'hint') ORDER BY at", (user["id"], word_id)):
        if r["kind"] == "shown":
            shown_at[(r["day"], r["exercise"])] = r["at"]
            continue
        hints[r["exercise"]] = hints.get(r["exercise"], 0) + 1
        start = shown_at.pop((r["day"], r["exercise"]), None)   # the first hint after it appeared
        if start:
            gap = (datetime.fromisoformat(r["at"]) - datetime.fromisoformat(start)).total_seconds()
            to_hint.setdefault(r["exercise"], []).append(gap)
    read_in = [dict(r) for r in con.execute(
        "SELECT p.id AS piece_id, p.title, MAX(e.day) AS day FROM events e JOIN pieces p ON p.id = e.piece_id "
        "WHERE e.user_id=? AND e.word_id=? AND e.kind='shown' AND e.surface='reader' "
        "GROUP BY p.id ORDER BY day DESC LIMIT 20", (user["id"], word_id))]
    return {
        "word_id": word_id, "word": w["word"], "status": w["status"], "added": w["day"], "box": w["box"],
        "shown": {"reader": one("SELECT COUNT(*) FROM (SELECT DISTINCT day, piece_id FROM events WHERE user_id=? "
                                "AND word_id=? AND kind='shown' AND surface='reader')"),
                  "practice": one("SELECT COUNT(*) FROM (SELECT DISTINCT day, exercise FROM events WHERE user_id=? "
                                  "AND word_id=? AND kind='shown' AND surface='practice')")},
        "taps": one("SELECT COUNT(*) FROM events WHERE user_id=? AND word_id=? AND kind='tap'"),
        "placed_in_reads": db.serving_counts(con, user["id"]).get(w["word"], 0),  # the engine used it (not seen)
        "answers": answers,
        "first_practised": attempts[0]["day"] if attempts else None,
        "last_practised": attempts[-1]["day"] if attempts else None,
        "history": [{"day": a["day"], "kind": a["kind"], "result": _result(a), "box_before": a["box_before"],
                     "box_after": a["box_after"]} for a in attempts],
        "changes": changes,
        "retained_on": retained[-1] if retained else None,
        "times_relearned": sum(c["status_before"] == "retained" and c["status_after"] == "learning" for c in changes),
        # how well it's remembered
        "tap_rate": round(taps_counted / shown_reader, 2) if shown_reader else None,   # taps ÷ times shown in reading
        "lapses": len({a["day"] for a in attempts                                      # forgotten after box 2+
                       if a["box_before"] is not None and a["box_before"] >= 2 and a["box_after"] == 0}),
        "first_try": {k: {"tries": sum(a["kind"] == k for a in firsts),
                          "clean": sum(a["kind"] == k and _clean(a) for a in firsts)}
                      for k in sorted({a["kind"] for a in firsts})},
        "confused_with": [{"answer": w, "times": n} for w, n in Counter(
            a["answer"].lower() for a in fills if not a["correct"]).most_common(5)],
        "hint_days": sum(any(a["hint"] for a in fills if a["day"] == d) for d in fill_days),
        "fill_days": len(fill_days),
        "median_seconds": {k: round(median(v), 1) for k, v in sorted(secs.items())},
        "hangman": {"games": len(games), "won": sum(g["won"] for g in games),
                    "avg_wrong": round(sum(g["wrong"] for g in games) / len(games), 1),
                    "hints": sum(g["hint"] for g in games)} if games else None,
        "hint_requests": dict(sorted(hints.items())),                    # asked for, answered or not
        "seconds_to_hint": {k: round(median(v), 1) for k, v in sorted(to_hint.items())},
        "sentences": [{"day": a["day"], "verdict": a["verdict"]} for a in attempts if a["kind"] == "write"],
        # where and when
        "read_in": read_in,
        "last_seen": seen_days[0] if seen_days else None,
        "days_since_seen": _days_between(seen_days[0], user["day"]) if seen_days else None,
        "days_to_retain": (_days_between(w["day"], retained[-1])  # since it was (last) saved
                           if retained and w["day"] and retained[-1] >= w["day"] else None),
        # looked it up (not "shown", D74)
        "card_opens": one("SELECT COUNT(*) FROM events WHERE user_id=? AND word_id=? AND kind='card'"),
        "listens": one("SELECT COUNT(*) FROM events WHERE user_id=? AND word_id=? AND kind='listen'"),
    }
