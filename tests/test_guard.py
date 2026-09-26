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
