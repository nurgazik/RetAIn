# RetAIn

iOS app concept (pre-code): helps advanced ESL speakers retain new vocabulary. The user
captures words they want to keep; whenever they are reading something — anywhere — they
run it through RetAIn on demand and read it back with their words placed where they fit
idiomatically, with tap-to-reveal highlights as the retrieval signal. Repetition inside
reading the user already chose.

Founder/PM: Nurgazy Budaichiev (also the PoC test subject).

## Current phase

**MVP build (Phase 2) after PoC 2 passed its technical gates (D35–D38, 2026-09-24).**
PoC 1 (a daily digest) is closed: habit never formed and a readable digest is a content
business the founder declines to run. PoC 2's gates (Safari/share-sheet feasibility,
engine word-fit, link legality, competitive scan) are answered in docs/poc2-transform.md.
Built so far: **M1** transform service (`src/service/`, FastAPI + SQLite, launchd agent
`com.retain.service` on the Mac mini, port 8585) and **M2** iOS app shell (`ios/RetAIn/`,
xcodegen project: app + share extension + Safari action). Engine: Gemini Flash-Lite
rewrite with idiomatic QC + fact judge (D36). Next: device validation, monetization (P2),
TestFlight (M9). The digest pipeline is retired but kept in the repo; the G1 spike lives
in `spikes/`.

## Key documents

- `docs/backlog.md` — **the living work list**: four epics (Tech Debt, Monetization, UX,
  Administration), the founder's pending decisions (DEC-n), done ledger. Update item
  status here as work lands; ids are stable.
- `docs/poc2-transform.md` — **PoC 2 record**: rationale, hypothesis v2, iOS entry-point
  feasibility, gates, spike findings, engine measurements. Extend it; don't fork it.
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
- `docs/architecture.md` — digest-era pipeline skeleton (retired half) **plus the M1
  transform service design (D38)** at the bottom: API contract, tables, auth, hosting.
- `ios/RetAIn/project.yml` — the iOS app; regenerate with `xcodegen generate`; never edit
  the .xcodeproj by hand. Run tests with the dev token: see PROGRESS.md M2 entry.
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
- Scope guards: link intake is out (D37); engine mode is rewrite with relaxed fidelity
  and the fact judge (D36); monetization undecided (P2) — decide before anyone but the
  founder uses the product; no Anthropic model runs unless the founder asks (cost).
- Service secrets live in `.env.local` (`RETAIN_SESSION_SECRET`, `RETAIN_DEV_TOKEN`,
  `RETAIN_APPLE_BUNDLE_ID`); the dev token is for curl/simulator only.
