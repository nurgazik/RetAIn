# Pipeline Architecture Notes

Technical counterpart to PRD §4 (Feed mechanics). Product concepts live there; this file
records the implementation patterns so the build follows the agreed skeleton. The PoC
exercises this exact skeleton at toy scale — nothing is thrown away at MVP graduation.

## Pipeline stages (classic ETL shape)

```
ingest (per-source fetchers, on schedule)
  → candidate store (pool per source)
    → select (digest assembly: one pass per slot, per user)
      → generate (LLM rewrite: shared core prompt + per-source wrapper)
        → QC (words present/marked? natural? facts preserved?) — regenerate on failure
          → render (HTML digest; MVP: app payload)
```

Each stage is independently runnable and testable. Fetchers know nothing about users;
assembly knows nothing about HTML.

## Candidate store + served ledger

- One small DB (PoC: **SQLite**, single file in `data/`).
- Every item has a **stable ID** (canonical URL or source-native ID) — the dedup key.
- Item lifecycle states: `fetched → selected → served` (+ `rejected` for QC/taste-filter
  discards, kept so we don't re-fetch and re-reject forever).
- The **served ledger is permanent** and per-user (PoC: single user). Assembly only ever
  picks unserved candidates.

## Idempotent daily builds

"Build digest for 2026-07-23" run twice yields the same digest, not a second one — the
build is keyed by (user, date) and re-runs read stored state instead of re-deciding.
This is the single biggest debugging-pain saver; keep it from the first script.

## Policy-driven slots

Slot definitions (source preference order + fallback ladder + count) live in config, not
code. News slot example: VOA today → VOA yesterday-unserved → Wikinews/Global Voices →
swap slot for evergreen/generated. Adding a source = one fetcher + one policy line.

## Data model vocabulary (agreed 2026-07-25)

Six entities. Content state is global; everything about a user's relationship to
content is per-user.

| Entity | Key fields / states |
|---|---|
| **ContentItem** (pantry, global) | `bucket`: fresh \| evergreen \| calendar; `status`: fetched \| rejected (taste filter only); full text captured at ingest |
| **Exposure** (per user↔item; the served ledger, upgraded) | `offered` (placed in an edition; zero signal if never scrolled to) → `seen` (viewport impression, counted) → `opened`; plus `bookmarked` (Saved shelf, cap 10). Seen-not-tapped applies a ranking penalty; retired for that user after 2–3 ignored impressions. Offered-never-seen: freely re-offerable |
| **GeneratedPiece** (per user, permanent — My Reads) | rewrite text, generated_at, model, source item ref. Distinct from ContentItem: one article can yield different rewrites for different users/words |
| **Word** | `status`: learning \| retained \| archived. learning↔retained reversible (reactivation re-enters scheduler with dense exposure); archived = soft delete (old pieces still reference it). Scheduler stats (times_served, times_revealed, last_served_at, interval) are fields, not statuses |
| **WordServing** (word↔piece join) | which words were embedded in which generated piece — powers highlighting (color by *current* word status, D24), exposure counts, scheduler |
| **Edition** | which items were offered to which user on which date + batch number — makes daily builds idempotent and auditable |

iOS impression tracking: standard viewport callbacks (~50% visible ≥1s). App-open and
scroll-depth telemetry from day one; usage decisions deferred (personalization parked).

## Dedup tiers

1. **Exact:** stable-ID check against store + ledger (PoC: this is enough for evergreen).
2. **Near-duplicate news (PoC):** cheap title-similarity check.
3. **Semantic (product scale):** embedding similarity between candidates and recent
   served items. Standard recommendation-system kit; explicitly deferred.

## PoC stack decisions

- Python scripts, no framework; SQLite; manual/cron daily run.
- LLM calls: Haiku-class for rewrites (PRD D5); QC pass as a second cheap call.
- Output: static HTML file with `<mark>` highlights + hover/tap definition reveal.

## MVP-scale notes (recorded, not built)

- Overnight batch generation bucketed **per user timezone** (PRD D13) — implies a
  per-user "digest date" concept, not one global daily run.
- Generate only for recently-active users (PRD D4).
- Batch API for 50% token cost reduction.
