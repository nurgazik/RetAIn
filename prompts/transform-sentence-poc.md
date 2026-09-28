# Transform wrapper — SENTENCE-SCOPED, DENSITY PoC variant (2026-09-28, not in production)

Identical to transform-sentence.md except the note rule is stricter (notes must carry a word).

Applies on top of prompts/core.md when the reader has handed RetAIn something they were
already reading. The text comes back **exactly as it was**, except for the individual
sentences that now carry a target word and a few short notes (D40, below).

- **Every sentence without a target word is reproduced verbatim** — same words, same
  punctuation, same order, same paragraph breaks. Headings, quotes, stray lines (ads,
  credits) included. Do not summarise, tidy, or "improve" anything.
- **A sentence may change only to seat a target word**, and the change stays inside that
  one sentence: prefer a substitution ("confirm" → "corroborate"); rephrase the sentence
  lightly if a substitution is impossible. The sentence must keep its meaning, its facts,
  its numbers, and its tone. Never touch text inside quotation marks.
- **Never add a sentence to the source's paragraphs.** Never add a fact, opinion, example,
  or attribution to them. The only text you may add is a note, below.
- **Goal: no stretch of reading (~120 words, listed in the request) without a target word
  (D40).** Work each listed stretch in this order: (1) substitute a word in one of its
  sentences; (2) if no substitution is natural, rephrase one of its sentences; (3) only if
  neither works, add a note. More than one word in a stretch is welcome whenever each fits
  naturally. Keep the source's paragraph breaks exactly: one `<p>` per source paragraph.
- **Notes — the third option.** Add ONE note right after any sentence of the stretch —
  inside the paragraph is fine — as `<aside>…</aside>` (no `<p>` inside).
  - **Every note carries exactly one `<mark>`ed word from the CANDIDATE TARGET WORDS
    list — that word is the only reason the note exists.** A note with no marked
    candidate word, or with a marked word that is not on the list, is deleted
    automatically, so never write one. Pick the candidate word first, then write the
    background sentence around it. One or two sentences.
  - General, lasting context that a well-read reader would find useful next to that
    sentence: what a thing is, how it works, the wider field it belongs to.
  - **No numbers, dates, quotations, or names that the source does not already use.**
    Nothing about recent events or trends ("increasingly", "these days"), no opinions
    attributed to anyone ("critics say", "experts argue"), and nothing that claims what
    the source's people did, said, or intend — the note is background, not news.
  - **Never define or explain the target word itself** — the reader recalls its meaning
    on their own; the note uses the word, it is not about the word.
  - At most one note per stretch. Notes are not only for empty stretches: a stretch that
    already carries a word may still take a note when it is genuinely relevant background
    (D43) — more words are welcome as long as each is used well. The note serves the
    sentence it follows — it must read as relevant background to it, not a digression. If
    every note you can think of would be strained, add none.
  - Example. Source paragraph: "Tesla showed a new version of its Optimus robot folding
    laundry at its Fremont factory on Tuesday, a task the company called its hardest yet."
    Note after that sentence: `<aside>Industrial robot arms are <mark>ubiquitous</mark> on factory floors,
    but they work behind cages on fixed tasks; a machine that shares space with people and
    handles soft, unpredictable objects is a different engineering problem.</aside>`
  - Wrong (deleted): `<aside>Mascots help brands build a recognizable identity.</aside>` —
    no marked candidate word. Right: `<aside>A mascot can become the <mark>linchpin</mark> of
    a brand's identity, recognised long before its logo.</aside>` (if "linchpin" is a
    candidate).
- If a candidate has neither a natural slot nor a natural note, skip it. Zero placements
  is a valid result.
- **Register belongs to the source.** No house voice; never simplify.
- **Title:** the source's own title if it has one; otherwise a faithful plain title.
- The renderer marks the sentences you changed, styles the notes, and adds attribution; do not.
