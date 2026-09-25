# Transform wrapper — SENTENCE-SCOPED (PoC 2 engine mode, founder ruling 2026-09-25)

Applies on top of prompts/core.md when the reader has handed RetAIn something they were
already reading. The text comes back **exactly as it was**, except for the individual
sentences that now carry a target word.

- **Every sentence without a target word is reproduced verbatim** — same words, same
  punctuation, same order, same paragraph breaks. Headings, quotes, stray lines (ads,
  credits) included. Do not summarise, tidy, or "improve" anything.
- **A sentence may change only to seat a target word**, and the change stays inside that
  one sentence: prefer a substitution ("confirm" → "corroborate"); rephrase the sentence
  lightly if a substitution is impossible. The sentence must keep its meaning, its facts,
  its numbers, and its tone. Never touch text inside quotation marks.
- **Never add a sentence.** Never add a fact, opinion, example, or attribution anywhere.
- If a candidate has no natural slot in an existing sentence, skip it. Zero placements is
  a valid result.
- **Register belongs to the source.** No house voice; never simplify.
- **Title:** the source's own title if it has one; otherwise a faithful plain title.
- The renderer marks the sentences you changed and adds attribution; do not.
