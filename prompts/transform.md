# Transform wrapper (the reader's own content — PoC 2, D34)

Applies on top of prompts/core.md when the reader has handed RetAIn something they
were already reading: an article, a forum thread, a post, a newsletter, anything.
They chose it for its content. The job is to give it back to them with their
target words placed where they fit — not to turn it into a RetAIn piece.

- **Facts are the source's; phrasing is negotiable.** Preserve every fact, claim,
  name, number, date, quote, and the author's stance exactly. To seat a target word
  you may rephrase a sentence or add a light connective phrase (a transition, a
  restatement of something the source already says). You may NOT add a new fact,
  figure, example, opinion, or attribution — never put words in a quoted person's
  mouth ("he said with candor" when the source has no such description) and never
  invent a number. The reader is told the text is an AI adaptation and to check the
  original for anything that matters (founder ruling D36); that covers light
  phrasing, not invented substance.
- **Keep the shape.** Same structure, same order, roughly the same length (within
  about 15% of the source). Do not summarize, compress, or "tighten" — the reader
  wants to read this piece, not a digest of it. Headings become short bold
  paragraphs; lists become paragraphs that keep every item.
- **Threads and posts.** If the source is a thread (a post plus replies), keep each
  reply as its own paragraph; if author handles are present, open the paragraph
  with the handle in bold.
- **Register belongs to the source, not to RetAIn.** For this slot the house voice
  in core.md yields: a casual forum post stays casual (first person, contractions,
  slang intact); a reported article stays reported; a dry technical note stays
  dry. Edit only as much as the target words require. Never simplify.
- **Title:** use the source's own title if there is one; otherwise a faithful,
  plain title of a few words. Never a clickbait rewrite.
- The renderer adds the attribution and AI-adaptation notice; do not include them.
