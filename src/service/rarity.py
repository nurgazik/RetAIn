"""How common a word is (PRD D61): wordfreq's Zipf score of the word family, shown as five bands.

Zipf = log10 of how often a word appears per billion words of mixed English (books, subtitles, news,
web; wordfreq 3.1.1, data frozen around 2021, CC BY-SA 4.0). The family is the saved word plus the
inflections Wiktionary lists for it (exigency + exigencies), so a word isn't called rare just because
it's mostly met in another form. A property of the word, not the user: stored on the shared card.
Plain code and reference data, no model."""
import math

from wordfreq import word_frequency

from . import dictionary

# (lowest Zipf, band), most common first. On an ~90,000-word book: Zipf 4 ≈ once a book,
# 3 ≈ once in 10 books, 2 ≈ once in 100, 1 ≈ once in 1,000. Agreed with the founder 2026-10-29.
BANDS = [(4.0, "common"), (3.0, "advanced"), (2.0, "uncommon"), (1.0, "rare"), (float("-inf"), "very-rare")]


def zipf(word: str) -> float:
    """The word family's Zipf score; 0.0 when wordfreq has never seen it (agelast)."""
    total = sum(word_frequency(w, "en") for w in [word, *dictionary.inflections(word)])
    return round(math.log10(total * 1e9), 2) if total else 0.0


def band(z: float) -> str:
    return next(name for low, name in BANDS if z >= low)


def backfill(con) -> int:
    """Score every card that has no score yet (cards from before D61); idempotent."""
    rows = con.execute("SELECT id, headword FROM lexicon WHERE zipf IS NULL").fetchall()
    for r in rows:
        con.execute("UPDATE lexicon SET zipf=? WHERE id=?", (zipf(r["headword"]), r["id"]))
    con.commit()
    return len(rows)
