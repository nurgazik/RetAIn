# Calendar wrapper: "News From 100 Years Ago" (Chronicling America)

Applies on top of prompts/core.md. The source is raw, noisy OCR text of an
American newspaper front page from exactly 100 years ago today. Expect scanning
artifacts, broken words, and jumbled column order.

- Mentally reconstruct the page, then pick the **1-3 most interesting stories**
  a modern reader would enjoy — favor human drama, technology of the era, prices
  and daily life, curiosities. Skip stories too garbled to reconstruct reliably.
- **Report only what the page actually says.** Names, numbers, and claims must
  come from the OCR text; if a detail is illegible, omit it rather than guess.
  You may add one short orienting phrase of common historical context (e.g.,
  what a sum was roughly worth), clearly framed as such.
- Frame as a dispatch: "One hundred years ago today, readers of the
  <paper name> woke up to..." — affectionate time-capsule tone, never mocking
  the past. Where the paper's own wording is delightful, quote it briefly.
- Target **250-400 words**.
- **Density-first slot (D33):** the reader reads the highlighted sentences.
  Rewrite freely — restructure, compress, extend with adjacent context a
  well-read friend could add (clearly common knowledge, e.g. what a sum was
  worth; the page's own facts stay sacred per the rules above). Aim for **one
  candidate word per 2-3 sentences**; a paragraph without one should be
  restructured or cut. Awkward collocations remain the worst failure.
- **Body format: HTML paragraphs, exactly this shape** — one `<p>` per
  paragraph, nothing else:

  ```
  <p>One hundred years ago today, readers of the <em>Intelligencer</em> woke
  up to... (a few sentences).</p>
  <p>The next story... </p>
  ```

  Output HTML only (`<p>`, `<em>`, `<mark>`); plain-text paragraphs or any
  `**` in the body are a failure.
- The renderer adds attribution (paper name, date, public domain via the
  Library of Congress).
