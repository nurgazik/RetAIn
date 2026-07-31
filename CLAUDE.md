# RetAIn

iOS app concept (pre-code): helps advanced ESL speakers retain new vocabulary by embedding
their to-retain words into a finite, personalized **daily digest** of genuinely interesting
rewritten content (news, Q&A, retold classics, original LLM pieces) — spaced repetition
hidden inside reading, with tap-to-reveal highlights as the retrieval signal.

Founder/PM: Nurgazy Budaichiev (also the PoC test subject).

## Current phase

**PoC — feed validation.** No app yet. Building a script pipeline that produces a daily
HTML digest for the founder to read for 14 days, item by item with quality review per
source. Go/no-go criteria in PRD.md §7.

## Key documents

- `PROGRESS.md` — **read this first when starting a session**: current state, next-up
  queue, and the dated narrative log. Update its NOW block and append an entry at the
  end of every working session — the founder relies on it to catch up after days away.

- `PRD.md` — product source of truth: hypothesis, decisions log (D1–D10), risks, and the
  three horizons (PoC / MVP / Future state). Update the decisions log when a new product
  decision is made; park good-but-deferred ideas in Horizon 3, never drop them.
- `docs/content-sources.md` — verified licensing research on rewritable content sources
  (what's usable, what's ruled out, per-source prompt wrappers). Don't re-research; extend it.
- `data/words.json` — the target word list (the founder edits this by hand; the pipeline
  reads it and later appends serving stats). Don't regenerate or reorder it.
- `docs/architecture.md` — pipeline skeleton (ingest → candidate store → select → generate
  → QC → render), served ledger, idempotent daily builds, slot policies. Build to this.
- `docs/model-bakeoff.md` — rewrite-model evaluation record (6 models, 7 configs, the
  deliberation/word-discipline dose-response finding). Extend it when testing new models;
  harness is `src/bakeoff.py` (`python3 src/bakeoff.py <model-filter>`).

## Working conventions

- **Fundamentals demand research + joint decisions.** For anything foundational
  (content sources, digest model, core UX, model choice), the founder wants meticulous
  investigation with tangible evidence of existing patterns — never a quick unilateral
  call by the assistant. (Lesson learned: prematurely accepting a single news source;
  a founder-pushed research sweep proved 6 sources existed.) Quick pragmatic calls are
  fine for implementation details. Log agreed decisions in the PRD decisions log.
- Product decisions get discussed before implementation; the founder thinks in
  PoC → MVP → Future-state horizons — scope suggestions accordingly.
- Rewrite quality bar: words only where genuinely idiomatic (awkward collocations teach
  wrong usage — worse than nothing); advanced reading level, never simplified.
- Cost posture: rewrite model is gemini-3.1-flash-lite (~$0.0017/piece) with
  claude-haiku-4-5 as fallback (PRD D5, docs/model-bakeoff.md). QC gate is descoped
  for PoC but has revisit triggers in D19 — check them before MVP work or model changes.
