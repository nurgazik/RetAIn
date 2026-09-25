# Transform wrapper — HYBRID (PoC 2 engine-mode candidate, G2)

Applies on top of prompts/core.md when the reader has handed RetAIn something they were
already reading. Substitution first; a light rewrite only where substitution cannot seat a
word.

- **Default: substitution.** Reproduce the source word for word and swap a plain word or
  short phrase for a candidate target word where the sense is the same and the result is
  idiomatic ("confirm" → "corroborate"). Adjust an article, preposition or inflection as
  grammar requires.
- **Permitted rewrite: at most ONE clause per paragraph** may be rephrased to seat a
  candidate word, keeping the meaning exactly. Never add information, opinions, examples
  or colour; never remove a fact; never touch text inside quotation marks; never change a
  number.
- Everything else stays: sentence order, paragraph breaks, headings, stray lines.
- If a candidate has no natural slot, skip it.
- **Register belongs to the source.** No house voice; never simplify.
- **Title:** the source's own title if it has one; otherwise a faithful plain title.
- The renderer adds attribution and the AI notice; do not include them.
