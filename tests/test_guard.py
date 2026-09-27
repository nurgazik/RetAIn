"""D40 tier tagging in sentence_guard: pure functions, no model calls."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
import generate as G  # noqa: E402

SRC = "The agency said the data confirm the trend. Launch is set for May.\n\nA second paragraph stays."


def test_one_word_swap_is_substitute():
    body = ("<p>The agency said the data <mark>corroborate</mark> the trend. Launch is set for May.</p>"
            "\n<p>A second paragraph stays.</p>")
    out, stats = G.sentence_guard(SRC, body)
    assert stats["edited"] == 1
    assert 'class="edited substitute"' in out and 'data-tier="substitute"' in out
    assert 'data-orig="The agency said the data confirm the trend."' in out
    assert "Launch is set for May.</p>" in out  # untouched sentence stays outside the span


def test_restructured_sentence_is_rephrase():
    body = ("<p>According to the agency, the figures <mark>corroborate</mark> what analysts had "
            "suspected about the trend. Launch is set for May.</p>\n<p>A second paragraph stays.</p>")
    out, _ = G.sentence_guard(SRC, body)
    assert 'data-tier="rephrase"' in out


def test_original_with_quotes_is_attribute_safe():
    src = 'He said "we confirm it" today. Nothing else.'
    body = '<p>He said "we confirm it" <mark>forthwith</mark>. Nothing else.</p>'
    out, _ = G.sentence_guard(src, body)
    assert 'data-orig="He said &quot;we confirm it&quot; today."' in out


def test_unmarked_edits_still_revert():
    body = "<p>The agency claimed the data confirm the trend. Launch is set for May.</p>\n<p>A second paragraph stays.</p>"
    out, stats = G.sentence_guard(SRC, body)
    assert stats["reverted"] == 1 and "edited" not in out


def test_rejected_word_reverts_its_sentence_to_source():
    # D41: a judge-rejected word's sentence goes back to the source; other edits stay
    body = ("<p>The agency said the data <mark>corroborate</mark> the trend. Launch is set for May.</p>"
            "\n<p>A second <mark>salient</mark> paragraph stays.</p>")
    out, stats = G.sentence_guard(SRC, G.unmark_sentences(body, ["corroborate"]))
    assert "corroborate" not in out
    assert "The agency said the data confirm the trend." in out
    assert "<mark>salient</mark>" in out and stats["edited"] == 1


# ---- D40 notes (SUPPLEMENT) and 120-word stretches

LONG = ("Tesla showed a new version of its Optimus robot folding laundry at its factory on "
        "Tuesday, a task the company called its hardest yet and one that took years of work "
        "by a large team of engineers.")
NOTE = ("<aside>Industrial robot arms are <mark>ubiquitous</mark> on factory floors, but they "
        "work behind cages on fixed tasks.</aside>")


def test_note_inside_paragraph_stays_inline_after_its_sentence():
    src = LONG + " It folded towels."
    out, stats = G.sentence_guard(src, f"<p>{LONG} {NOTE} It folded towels.</p>")
    assert stats["notes_kept"] == 1 and out.count("<p>") == 1
    assert out.index('class="note supplement"') < out.index("It folded towels.")
    assert G.coverage_stats(out)["tiers"]["supplement"] == 1


def test_note_between_paragraphs_attaches_to_previous_sentence():
    src = LONG + "\n\nShort one."
    out, stats = G.sentence_guard(src, f"<p>{LONG}</p>\n{NOTE}\n<p>Short one.</p>")
    assert stats["notes_kept"] == 1 and out.count("<p>") == 2
    assert out.index("note supplement") < out.index("Short one.")


def test_note_rules_drop_bad_notes():
    bad = {
        "number": "<aside>Robot arms date to <mark>1961</mark> in car plants.</aside>",
        "quote": '<aside>Engineers call it "the <mark>ubiquitous</mark> problem".</aside>',
        "new name": "<aside>Boston Dynamics made robots <mark>ubiquitous</mark> in videos.</aside>",
        "no mark": "<aside>Robot arms work behind cages on fixed tasks.</aside>",
    }
    for why, note in bad.items():
        _, stats = G.sentence_guard(LONG, f"<p>{LONG}</p>\n{note}")
        assert stats["notes_dropped"] == 1 and stats["notes_kept"] == 0, why


def test_note_kept_when_stretch_already_has_word():  # D43
    marked = LONG.replace("showed", "<mark>unveiled</mark>")
    out, stats = G.sentence_guard(LONG, f"<p>{marked}</p>\n{NOTE}")
    assert stats["notes_kept"] == 1 and stats["notes_dropped"] == 0
    assert "unveiled" in out and "note supplement" in out


def test_rejected_note_word_drops_the_note():
    body = G.unmark_sentences(f"<p>{LONG}</p>\n{NOTE}", ["ubiquitous"])
    out, stats = G.sentence_guard(LONG, body)
    assert stats["notes_dropped"] == 1 and "note" not in out


def test_fact_judge_never_sees_notes():
    assert "aside" not in G.strip_notes(f"<p>{LONG}</p>\n{NOTE}")
    assert G.invented_numbers({"content_html": LONG}, {"body": f"<p>{LONG}</p><aside>In 1961 x</aside>"}) == []


def test_stretches_cut_at_120_words_and_fold_short_tail():
    s = "Word " * 59 + "end."           # 60 words per sentence
    text = " ".join([s] * 5)            # 300 words -> 120 | 120 | 60 tail
    _, _, stretch_of = G.source_sentences(text)
    assert stretch_of == [0, 0, 1, 1, 2]
    _, _, stretch_of = G.source_sentences(" ".join([s] * 4) + " Short tail.")
    assert stretch_of == [0, 0, 1, 1, 1]  # a tail under 60 words joins the stretch before
    assert len(G.stretch_openings(text)) == 3


def test_one_long_paragraph_gets_one_note_per_stretch():
    s = "Word " * 59 + "end."
    src = " ".join([s] * 4)             # one 240-word paragraph = 2 stretches
    n = "<aside>Robot arms are <mark>ubiquitous</mark> in plants.</aside>"
    body = f"<p>{s} {n} {s} {n.replace('Robot', 'Crane')} {s} {s}</p>"
    out, stats = G.sentence_guard(src, body)
    assert stats["notes_kept"] == 1 and stats["notes_dropped"] == 1  # second note in the same stretch
    body = f"<p>{s} {n} {s} {s} {n.replace('Robot', 'Crane')} {s}</p>"
    out, stats = G.sentence_guard(src, body)
    assert stats["notes_kept"] == 2 and stats["stretches_covered"] == 2 and out.count("<p>") == 1


def test_split_paragraph_keeps_source_structure_and_note():
    src = LONG + " It folded towels. It folded shirts."
    body = (f"<p>{LONG}</p>\n<p>It folded towels. It folded shirts.</p>\n{NOTE}")
    out, stats = G.sentence_guard(src, body)
    assert out.count("<p>") == 1 and stats["notes_kept"] == 1


def test_merged_paragraphs_are_rebuilt():
    src = LONG + "\n\nSecond paragraph here. It stays apart."
    body = f"<p>{LONG} Second paragraph here. It stays apart.</p>"
    out, _ = G.sentence_guard(src, body)
    assert out.count("<p>") == 2
