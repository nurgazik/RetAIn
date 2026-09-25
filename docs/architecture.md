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

---

# PoC 2 → MVP: the transform service (M1) — PROPOSAL, pending founder yes (2026-09-24)

Everything above describes the digest pipeline (PoC 1). Under D34 the ingest → store →
select half is retired; generate → QC → render and the served ledger carry over. This
section proposes the hosted service the iOS app and its extensions will call (backlog M1,
PRD §8 "Service"). Nothing here is built.

## What it is

One small HTTP service that owns three things: **who the user is**, **their words**, and
**the transform**. The phone never holds an LLM key; the extension sends text, the service
sends back a piece. Same engine code as today (`generate.py`), wrapped in an API.

```
iOS app / share ext / Safari action
   │  Sign in with Apple → session token (stored in the app-group keychain, shared by app + extensions)
   ▼
POST /v1/transform {text, title?, url?, source}  → {piece_id}         (returns at once)
GET  /v1/transform/{piece_id}/events   (server-sent events: received → generating →
                                        checking → repairing → done + piece JSON)
GET  /v1/pieces, GET /v1/pieces/{id}          My Reads
POST /v1/pieces/{id}/taps {word}               tap = "didn't remember"
GET/POST/PATCH /v1/words                       list, capture (+ word-card enrichment), lifecycle
```

The "working the magic" moment is the events stream: the sheet shows each phase as it
happens, and the piece arrives only after QC, the fact judge and any repair finish (D29).

## Decisions proposed (what / why / standard practice?)

| Area | Proposal | Why | Standard? |
|---|---|---|---|
| Language + framework | **Python + FastAPI + uvicorn** | Reuses `generate.py` unchanged; FastAPI gives auth dependencies, request validation and SSE streaming in a few lines. Alternative: keep the stdlib `http.server` (zero deps, but auth/streaming/validation by hand). | Yes — the default Python API stack. **New dependency: needs your ok.** |
| Hosting, option A | **The Mac mini, exposed with Tailscale Funnel** — a public HTTPS URL on the ts.net domain, free, no other hosting bill. The Mac is already the always-on appliance; the launchd agent already restarts the server. | Free, available today, and HTTPS from the start (which also ends the "Limit IP Address Tracking" problem). Enough for the founder plus ~5 TestFlight readers. Risks: home network, one machine, no isolation. | Common for solo MVPs; not for a public launch. |
| Hosting, option B | **Fly.io, one shared-CPU machine with a persistent volume** (≈ $3–5/month). | Proper host with HTTPS, secrets, logs, restart on crash; same Docker image later scales. | Yes. **Costs money: needs your ok.** |
| Recommendation | **A now (M1–M9), B before anyone outside TestFlight.** The code is identical; only the deploy target changes. | | |
| Database | **SQLite on the single machine**, new tables: `users`, `words` (per user, status + servings), `pieces` (per user, body, offered/placed), `events` (impressions/taps), `calls` (every model call: purpose, tokens, USD). Nightly file backup (Litestream or a cron copy). Move to Postgres only when there is a second machine. | We already run SQLite; one writer, small data. | Yes for single-node MVPs. |
| Auth | **Sign in with Apple** → server verifies Apple's identity token once → issues its own session token (JWT, long-lived, revocable). App and extensions share it through the app-group keychain. | Required by App Store rules when any third-party sign-in exists; gives a stable user id with no passwords. | Yes. |
| Streaming | **Server-sent events** for phases; piece JSON at the end. | Simpler than WebSockets, works through any proxy, trivially consumed by `URLSession`. | Yes. |
| Cost control | Per-user daily transform cap in config (e.g. 30) + the `calls` table from day one. | Every transform costs ~$0.003; a cap protects against runaway cost before monetization (P2) exists. | Yes. |
| Secrets | Gemini/Anthropic keys in the host environment only (`.env.local` today; Fly secrets later). | Keys never ship in the app. | Yes. |
| Word ordering | Server-side sort: fewest lifetime servings first, per user (D32 minus intervals). | D34. | — |

## What changes in the repo

- `src/service/` (new): `app.py` (routes), `auth.py`, `db.py` (schema + migrations),
  `engine.py` (thin wrapper around `generate_piece` with a per-user word list), `sse.py`.
- `generate.py`: reads the word list from a parameter instead of `data/words.json`
  (today's file becomes the founder's seed list on first sign-in).
- `serve.py` keeps running as-is until the app exists, then retires.
- `requirements.txt` (new): fastapi, uvicorn, python-jose or pyjwt (Apple token
  verification), sse-starlette or hand-rolled SSE.

## Not in M1

Monetization (P2), word-card enrichment prompt tuning (M5), push notifications, Android,
multi-region, admin UI. Rate limits beyond the daily cap.

## Done when

`curl` can sign in with a test token, add words, post a transform, watch the events stream
end with a piece, list pieces, and record a tap — all on HTTPS from the phone via the
Funnel URL — and every model call has a row in `calls` with a dollar figure.
