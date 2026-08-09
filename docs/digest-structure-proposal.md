# Digest structure proposal — from the 2026-08-08 coherence research

Status: **PROPOSAL, not decided.** Founder commissioned creative research on feed
coherence ("feels incredibly random — not useful to anyone this way") and new
sources. This doc synthesizes both research threads into a concrete structure for
founder rulings. Companion: docs/content-sources.md sweep-2 section (licenses).

## The diagnosis

Every daily-content product people describe with ritual language answers "why THIS
piece TODAY." Three working answers exist: the calendar chose it, the serial chose
it, or the named slot chose it. Source-driven feeds answer "because the pipeline
produced it" — that's the randomness RetAIn's founder feels. Supporting evidence:
the calendar pair is the only element the founder never complains about, and it's
the only element with date logic.

Key external evidence (full citations in the research transcript):
- **Dracula Daily**: PD novel serialized on its in-story dates; 1,600 → 200,000+
  subscribers (2022), ~75% self-reported open rates. The strongest known
  come-back-tomorrow device that isn't a guilt mechanic.
- **Economist Espresso / FT Edit**: rigid finishability (5/8 stories, fixed
  rubrics) as core product culture. Matches decided D22.
- **Poem-a-Day (315k), A.Word.A.Day (~300k, since 1994), Now I Know (100k+)**:
  one excellent flagship item daily beats five okay ones; the item is the brand.
- **Duolingo Stories**: recurring cast converts study into serial entertainment
  (retention numbers secondary-source; directional).
- **Dreaming Spanish**: progress denominated in content consumed, not points —
  its devoted community logs hours against a public roadmap.

## Proposed daily lineup (fixed order, named rubrics)

1. **The cold open** — 2-3 sentences in the house voice: why today's pieces are
   today's (the date's logic, the serial's cliffhanger position). One extra LLM
   call. Cheapest coherence device found.
2. **The Anniversary** — existing calendar pair, promoted from "two slots" to the
   edition's spine. Where natural, other slots hang off the date.
3. **The Serial** — daily 2-3 minute installment of one PD classic, rewritten in
   house voice, density-first, ending on the natural cliffhanger. Seasons ("Season
   1: Dracula, 90 days, Day 12 of 90"). Gutenberg source = existing pipeline.
4. **The Rotating Desk** — one culture rubric by weekday from sweep-2 sources,
   e.g.: Mon "Where Words Come From" (Wiktionary — biography of one of the
   reader's OWN words), Tue "The Cabinet" (Public Domain Review), Wed "Dispatch
   from the Deep" (NOAA), Thu "Somebody Patented That" (USPTO), Fri "Tonight's
   Plot" (Wikipedia film), weekend "Postcard from a Park" / "One Strange Story."
5. **The Conversation** — proprietary dialogue channel with recurring cast
   (2-4 characters, continuing situations, callbacks; hard cringe-quality gate).
   GATED on founder inputs: interest areas + cast approval.
6. **The Shelf** — the world/curiosity headline menu (GV/SE/NASA picks), demoted
   from main course to labeled dip-in shelf. "The more you read..." unchanged.
7. **The ending** — designed, not just a stop: content-denominated progress
   ("Day 12 of Dracula · 41 words in circulation · 6 retired"), tomorrow's serial
   teaser. No points, no streaks-guilt.

## Explicitly NOT proposed

- Heavy weekly theming of the word list (collides with D27/D32 scheduling).
- Point-based gamification (evidence favors content-denominated progress).
- Full per-user feed personalization (forecloses shared-edition value; MVP note:
  shared edition + personal word overlay — log as decision before personalizing).

## Decisions this implies (each needs a founder ruling)

1. Adopt rubric structure + cold open + designed ending? (Reorganization of
   existing pipeline output — smallest lift, testable within the PoC.)
2. Green-light The Serial? If yes: pick Season 1 book (Dracula is the evidence-
   backed default: epistolary, in-story dates align with real dates, public
   domain). Alternatives: shorter first season (a Sherlock Holmes story arc,
   Jekyll & Hyde) if 90 days feels long.
3. Which Rotating Desk rubrics make the first cut? (Founder taste call.)
4. The Conversation still gates on: interest areas + recurring-cast yes/no.
