# RetAIn

iOS app concept (pre-code): helps advanced ESL speakers retain new vocabulary. The user
captures words they want to keep; whenever they are reading something — anywhere — they
run it through RetAIn on demand and read it back with their words placed where they fit
idiomatically, with tap-to-reveal highlights as the retrieval signal. Repetition inside
reading the user already chose.

Founder/PM: Nurgazy Budaichiev (also the PoC test subject).

## Current phase

**PoC 2 — on-demand transform (D34, 2026-09-24).** PoC 1 (a daily digest of rewritten
content) is closed: 7 of 14 days read, habit never formed, and a readable digest is a
content business the founder declines to run. Now running technical spikes S0–S5
(docs/poc2-transform.md §7) before any iOS work: text-intake route on the PoC server + an
iOS Shortcut for a 14-day self-test, word-fit measurement on real reading, Safari action
extension and share-extension feasibility in Xcode. Success criteria in
docs/poc2-transform.md §6. The digest pipeline (fetchers, calendar slots, editions) is
retired but kept in the repo.

## Key documents

- `docs/poc2-transform.md` — **PoC 2 source of truth**: rationale, hypothesis v2, iOS
  entry-point feasibility, success criteria, technical spikes (findings appended as they
  land), user-story backlog. Extend it; don't fork it.
- `PROGRESS.md` — **read this first when starting a session**: current state, next-up
  queue, and the dated narrative log. Update its NOW block and append an entry at the
  end of every working session — the founder relies on it to catch up after days away.

- `PRD.md` — product source of truth: hypothesis, decisions log (D1–D34), risks, and the
  horizons (PoC 1 closed / PoC 2 / MVP / Future state). Update the decisions log when a new product
  decision is made; park good-but-deferred ideas in Horizon 3, never drop them.
- `docs/content-sources.md` — verified licensing research on rewritable content sources
  (what's usable, what's ruled out, per-source prompt wrappers). Don't re-research; extend it.
- `data/words.json` — the target word list (the founder edits this by hand; the pipeline
  reads it and later appends serving stats). Don't regenerate or reorder it.
- `docs/architecture.md` — digest-era pipeline skeleton (ingest → candidate store → select →
  generate → QC → render). Generate/QC/render and the served ledger carry into PoC 2; the
  ingest/select half is retired.
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
  claude-haiku-4-5 as fallback (PRD D5, docs/model-bakeoff.md). QC gate is ON (D19);
  check its revisit triggers before MVP work or model changes.
- PoC 2 scope guards: no URL fetching of third-party sites until the founder rules on the
  terms-of-service reading (spike S3); engine mode (substitute vs rewrite) is undecided
  until S1; monetization undecided. Don't build past a spike's "done when".
