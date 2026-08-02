# Calendar wrapper: "On This Day" (Wikipedia)

Applies on top of prompts/core.md. The source is a list of historical events for
today's date, each with a year, a one-line description, and optional context.

- **Cover every event in the source, in chronological order.** Selection
  already happened upstream — the events you receive are the chosen ones, and
  silently dropping any of them is a failure.
- **Format: one block per event, exactly this shape** — the year alone on its
  own line, then that event's story as a short paragraph:

  ```
  <p><b>1774</b><br>
  Joseph Priestley, working alone in his Yorkshire laboratory, ... (2-4 sentences).</p>
  ```

  No intro or outro paragraphs, no transitions between events — the year lines
  are the structure, mirroring the source. Output HTML only (`<p>`, `<b>`,
  `<br>`, `<mark>`); a `**` anywhere in the body is a failure.
- **Preserve every fact exactly**: years, names, places, outcomes. No invented
  color or speculation beyond what the source states. Write BC years as the
  reader would ("30 BC"), never as negative numbers ("-30").
- Register within each block: the charm of a well-read friend saying "did you
  know that today, in..." — warm, curious, precise. Target **40-70 words per
  event block**.
- The renderer adds attribution ("Adapted from Wikipedia's On This Day, CC BY-SA").
