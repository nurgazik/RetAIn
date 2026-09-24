# PoC 2 — on-demand "RetAInization" of the reader's own content

*Written 2026-09-24. Owner: founder. This file is the PoC 2 source of truth: rationale,
hypothesis, UX, iOS feasibility, success criteria, technical spikes, and the user-story
backlog. Spike findings get appended to §7 as they land. Product decisions still go to the
PRD decisions log (D34 onward).*

---

## 1. Why PoC 2

### What PoC 1 showed

PoC 1 (the daily digest, PRD §7) ran 7 of its planned 14 days, 2026-08-02 → 08-08.
Pieces generated per day, from `generated_pieces`:

| Day | 08-02 | 08-03 | 08-04 | 08-05 | 08-06 | 08-07 | 08-08 |
|---|---|---|---|---|---|---|---|
| Pieces | 29 | 10 | 6 | 2 | 7 | 3 | 2 |

Success criterion 1 (read willingly ≥10 of 14 days) failed. Criteria 2 (retention
self-quiz) and 3 (rewrite quality bar) were never reached — engagement failed first, so
**the retention mechanism is untested, not disproven.**

### The diagnosis (founder, 2026-09-24)

A daily digest that people actually read is a **content business**: an editor's daily
commitment, a voice, taste as the moat, media economics. The products that sustain a
finite daily ritual without algorithmic personalization (Morning Brew, The Economist's
Espresso, Dracula Daily) all pay that cost. PoC 1 tried to get the benefit without the
commitment by letting a pipeline play editor; the 08-08 note ("feels incredibly random")
is what an editor-less publication feels like. The founder does not want to be in the
content business. That closes the digest, independent of any engineering fix.

Secondary finding, also from PoC 1: content that exists to carry words is structurally
second-rate. It is constrained by the word list, chosen by a pipeline, and competes for
reading time against things the reader already wanted to read.

### The pivot

RetAIn stops constructing a feed. Reading happens wherever the user already reads —
Safari, Reddit, X, Apple News, anywhere. Whenever they want, they run the piece in front
of them through RetAIn and read it back with their words sprinkled in. On demand only.
**No scheduler, no daily digest, no editions, no "due" words.** The iOS app is the MVP
surface; a browser plugin is a later ecosystem piece.

### What carries over from PoC 1, and what is dropped

| Carries over | Dropped |
|---|---|
| Word capture (typed, share sheet) and `data/words.json` | Fetchers, pantry, candidate store, calendar slots |
| Rewrite engine: `src/generate.py`, `prompts/core.md` house voice (D30) | Scheduler, expanding intervals, "due" pool |
| QC gate (D19) and reject-means-absent (D29) | Editions, re-deal, "you're caught up" (D22) |
| Tap-to-reveal as the retrieval moment (D7 semantics, minus interval logic) | Digest layout, headline list, pre-generation (D17/D20) |
| Served ledger (`generated_pieces.words_used`, `offered_words`) | Density floor as a product rule (D28) — becomes a measurement |
| Word ordering: fewest-servings-first (D32's sort, no intervals) | Proprietary piece generator (parked, Horizon 3) |
| AI-rewrite disclaimer on every piece (D33) | On This Day / century wrappers |
| Word lifecycle learning / retained / archived (D26) | |

---

## 2. Hypothesis v2

> Repeated exposure to a target word, inside content the user chose to read anyway, with a
> tap-to-reveal retrieval moment at each encounter, produces durable retention. Exposure
> frequency is driven by how often the user invokes the transform, not by a schedule.

What changed from v1 (PRD §2): the "spaced" half is gone. Nation's 8–12 exposures in
varied contexts don't require a schedule, only enough encounters — but the encounter count
is now entirely a function of user behaviour. That makes **invocation frequency** the
thing PoC 2 must measure first.

Known limitations, accepted:
- Receptive knowledge only (as in v1); productive use stays Horizon 3.
- Exposure is opportunistic. A word gets served only when the user reads something with a
  natural slot for it. If the founder's 50 professional-register words rarely find slots
  in his real reading, the product narrows to "improves your work reading" — which may
  still be fine, but it should be known.

---

## 3. UX flow

1. **Capture** (unchanged): add a word by typing or via the iOS share sheet from any app.
   Word card = definition, register, collocations, nuance.
2. **Invoke** ("RetAInize this"): the user is looking at something and decides to run it
   through RetAIn. Entry points in §4.
3. **Transform**: the engine places the user's words where they fit idiomatically, streams
   the result with the visible "working the magic" moment (D17/D20 carry-over), QC runs
   behind the stream, rejected words never reach the screen (D29).
4. **Read** in RetAIn's reader view: highlighted words, tap to reveal meaning and times
   seen. A tap means "didn't remember". Source link + AI-rewrite disclaimer on every piece.
5. **Ledger**: every transform logs offered words, placed words, taps, source (app / URL /
   text), and length — the raw material for the success criteria and, later, for pricing.

The habit problem moves, it doesn't vanish: the user must remember, mid-reading, to invoke.
This is the Instapaper/Pocket pattern (send it somewhere, read it there), which works for
people who batch reading and has a known ceiling for everyone else. In RetAIn's favour: the
content is something the user already wanted, so the tool adds to an existing act instead
of asking for a new one.

---

## 4. iOS entry points — feasibility (unverified against Apple docs until Spike S2)

iOS gives third-party apps no way to alter what another app shows. Unlike Android, there
is no accessibility overlay and no "process selected text" hook (Android's
`ACTION_PROCESS_TEXT`). So the product cannot be "Reddit, but with your words"; it is
"hand the content to RetAIn, read it in RetAIn's view". The share sheet is the universal
entry point. The routes:

| Route | Mechanism | Works where | Notes |
|---|---|---|---|
| Share sheet, URL | App's share button hands RetAIn a link; RetAIn fetches + extracts text | Open web only | Fails for Facebook, most of X, paywalls. Reddit has a `.json` view but rate-limits/blocks and its API terms restrict commercial use — fragile. **Terms-of-service reading required before use (S3).** |
| Share sheet, selected text | User long-presses text, selects, shares | Any app with selectable text | Never breaks; misses whole threads; clunkier |
| Safari **action extension** with JS preprocessing | Extension runs a JS file in the page before its UI opens; reads the rendered DOM from the user's own session | Safari | Captures paywalled / logged-in pages as the user sees them, no scraping. Sheet over the page. **The strong case.** |
| Safari **web extension** | Runs continuously in Safari, can edit the page in place | Safari | The only true in-place route; fits substitution mode. Horizon 3. |
| Screenshot + OCR | Share a screenshot; Vision framework text recognition | Literally anywhere incl. Facebook, Kindle | Ugly but real fallback |
| Clipboard | Copy → open RetAIn → paste | Anywhere | Zero engineering; the baseline every route must beat |

Per-source quality (to be confirmed by S2/S3):

| Where the user is | Best handoff | Expected quality |
|---|---|---|
| Article in Safari | Action extension reads the page | Excellent |
| reddit.com / x.com in Safari | Same | Excellent |
| Reddit native app | Share URL → `.json` fetch first try; text selection fallback | Fair, fragile |
| X native app | Selected text or copy; public oEmbed for single posts (unverified) | Fair |
| Facebook native app | Selected text or screenshot | Poor |
| Apple News, Kindle, paywalled apps | Selected text or screenshot | Poor |

Two facts that shape the experience:
- **Latency.** A 1,000-word rewrite on gemini-3.1-flash-lite takes roughly 5–15 s
  un-streamed. The sheet must stream (first paragraph in ~1–2 s) or the user leaves.
- **Extensions are thin.** They run in a separate process with a small memory budget. Grab
  text, call the API, render; all state lives in the main app via an app group.

Honest summary: Safari is where this product is great; native social apps are where it is
merely possible. If most of the founder's reading is Reddit/X in native apps, **handoff
friction is the top product risk**, ahead of anything in the engine.

---

## 5. The engine question (open — decided by Spike S1 → D35)

Three modes, to be measured on content the founder actually read:

- **Rewrite** — current pipeline (`prompts/core.md` voice + a transform wrapper). Highest
  placement rate; highest risk of drifting facts and meaning. PoC 1 measured ~30% forced
  embeds under density pressure and 2 invented specifics on news content (D33).
- **Substitute** — swap a plain word for the target where the sense matches ("confirm" →
  "corroborate"); change nothing else. Preserves facts by construction, sentence-local,
  cheap, and works in place (web extension). Same mechanic Toucan uses for foreign-language
  vocabulary (from memory — verify in the competitive scan). Lower placement rate.
- **Hybrid** — substitute, plus at most one clause-level rewrite per paragraph.

Why this matters more than in PoC 1: the reader chose the sourdough thread to learn about
sourdough. Facts and meaning are sacred, and the reader knows the topic well enough to
notice distortion.

Word ordering survives as a **sort, not a scheduler**: with 50 words and one article the
model places maybe five; left alone it places the same easy-fit five every time (PoC 1 saw
the inverse). D32's fewest-servings-first order stays; intervals and due dates go.

---

## 6. Success criteria (proposed — founder to ratify N)

Measured over a 14-day self-test on the founder's real reading (Spike S0):

1. **Invocation habit:** founder runs the transform unprompted on ≥ N of 14 days. (N to be
   set by founder; PoC 1's bar was 10/14 for reading.)
2. **Word-fit:** ≥ X placed-and-QC-clean words per 1,000 words on real content (X from
   S1's measurement, not a guess), with zero surviving misuses on founder read-through.
3. **Handoff friction:** for each source the founder actually reads, a route he rates
   "would use again".
4. **Retention:** day-14 self-quiz on served words vs the "look it up once, lose it"
   baseline (PoC 1 criterion 2, unchanged).

Go/no-go: 1 fails → the on-demand model has the same habit problem as the digest; stop.
2 fails → engine work before any app. 3 fails on the founder's main sources → the product
is Safari-only; decide whether that is enough. 4 fails → rethink the mechanism.

---

## 7. Technical spikes (ordered)

Spikes are time-boxed investigations that end in a written finding here, not shipped
features. Findings are appended under each spike as they land.

### S0 — Handoff with zero Swift: does the founder reach for it?
- **Question:** given the lowest-friction handoff available today, does "run this through
  RetAIn" happen unprompted?
- **Method:** add a `/transform` route to `src/serve.py` (which already does
  headline-click → streamed rewrite via `generate_piece`) taking pasted text and rendering
  the same reader view. Add an iOS Shortcut that accepts share-sheet input from any app and
  opens the server URL (via Tailscale) with it — the share-sheet flow on Reddit/X/Safari
  with no Xcode. Every invocation logged (source, length, offered/placed words).
- **Scope guard:** text intake only until the founder rules on URL fetching (S3 terms
  reading). This is the only spike that touches product code, and it is the PoC server,
  not the app.
- **Done when:** route + shortcut work from the phone on three apps; the 14-day count is
  running.

**S0 status (2026-09-24): server side built and smoke-tested; Shortcut is the founder's
next step.**

- Built: `GET /transform` (paste box + "Your reads" list + today's word pills),
  `POST /api/transform` (JSON or form; form redirects to the read page), `user_text` items
  in the store with `section` = source app and `license` = user-supplied, a `transform.md`
  wrapper (fidelity first, keep shape and length, source register wins over house voice),
  `transform_menu` = all learning words sorted fewest-servings-first (D34: a sort, no caps).
  The existing `/read` + `/api/rewrite` streaming shell and QC path are reused unchanged.
- Smoke test (one 260-word forum-style post, gemini-3.1-flash-lite): 4 words placed
  (squander, bolster, candor, conundrum), 1 QC-rejected with a correct reason
  (*perfunctory* contradicted the poster's effort), regenerated clean; length 271 vs ~260
  source; every fact and the first-person register preserved. One borderline collocation
  survived ("that attempt to bolster our sessions") — an S1 data point, not a blocker.
- Known carry-over to watch in S1: `generate.py` still sends the D28 density instruction
  ("one word in every paragraph where one sits naturally") in the user message. On the
  reader's own content this is the density-first posture; S1 tests it against
  substitute-only.
- Always-on server restarted (launchd `com.retain.server`); `/transform` answers on
  `http://rays-mac-mini.tailb493b3.ts.net:8484/transform` from the phone via Tailscale.

**iOS Shortcut recipe ("RetAInize") — founder builds this on the phone, ~5 minutes.**
From memory of the Shortcuts app; verify each action name on the phone.

1. New shortcut, name **RetAInize**. In its settings turn on **Show in Share Sheet**;
   under Share Sheet Types accept **Text**, **URLs**, **Safari web pages**.
2. Action **Receive Text / URLs / Safari web pages input from Share Sheet**; set
   "If there's no input" to **Get Clipboard** (so copy → run also works).
3. Action **Get Details of Safari Web Page** → **Page Selection** (falls back to nothing
   when the input isn't a Safari page). *Unverified: whether Page Contents returns
   readable page text; if it does, that is a zero-Swift Safari full-page handoff and an
   early S2 signal.*
4. Action **Text**: the selection from step 3 if non-empty, otherwise the Shortcut Input
   as text. (An **If** block on "has any value" does this.)
5. Action **Get Contents of URL**: `http://rays-mac-mini.tailb493b3.ts.net:8484/api/transform`,
   Method **POST**, Request Body **JSON** with `text` = the Text from step 4,
   `source` = the app name if easy to type, otherwise `shortcut`.
6. Action **Get Dictionary Value** `read_url` from Contents of URL.
7. Action **Text**: `http://rays-mac-mini.tailb493b3.ts.net:8484` + Dictionary Value.
8. Action **Open URLs** on that text. Safari opens the read page with the "working the
   magic" moment; the piece streams in.

S0 text-only scope guard: sharing a *link* from Reddit/X/Safari sends a URL, not text —
the server rejects anything under 200 characters, so the Shortcut should be run on a
**text selection** (long-press → select → Share) until the founder rules on URL fetching
(S3). The invocation log line `[transform] <ip> source=<app> chars=<n> id=<id>` in
`~/Library/Logs/retain-server.log` plus the `user_text` rows are the 14-day count.

### S1 — Word-fit on real content: substitute, rewrite, or hybrid?
- **Question:** on ~10 pieces the founder actually read this week, how many of the 50
  words land naturally per 1,000 words, QC-clean, under rewrite / substitute / hybrid?
- **Method:** new wrapper `prompts/transform.md` (+ substitution variant); run through
  `generate_piece` with QC on (D19), density floor off. Measure marks/1,000w, QC reject
  rate, `invented_numbers` hits, and founder read-through rating. Compare page
  `output/compare-transform.html` (existing pattern).
- **Done when:** 3 variants × 10 pieces table + founder ruling on engine mode → D35.

### S2 — Safari action extension: can we read the rendered page and show our sheet?
- **Question:** does an iOS action extension with a JavaScript preprocessing file get the
  page DOM from the user's session (paywalled / logged-in included), and can it stream from
  our endpoint and render within the extension memory budget?
- **Method:** verify Apple docs first (no working from memory). Then a throwaway Xcode
  project: action extension + JS preprocessing returning article text; SwiftUI sheet that
  POSTs to `/transform` and streams. Test on 5 pages: open article, paywalled article the
  founder is logged into, reddit.com thread, x.com post, a very long page (memory).
- **Done when:** works/fails per page, Apple-docs citations, measured memory + latency.

### S3 — Share extension from native apps: what actually arrives?
- **Question:** sharing from Reddit, X, Facebook, Apple News, Kindle — what item types
  arrive (URL, text, both)? For URLs, is the content fetchable, and do the terms allow it?
- **Method:** share extension logging `NSItemProvider` types + payloads. Python script
  trying (i) Reddit `.json` view from residential IP and phone, (ii) X public oEmbed,
  (iii) a generic article extractor on 10 URLs. **Ask-first dependency:** extraction
  library (trafilatura vs readability-lxml) — docs checked, proposed before install.
- **Done when:** per-app table (arrives / fetchable / recommended route) + Reddit and X
  terms-of-service reading with links.

### S4 — Streaming into an extension + reader view port
- **Question:** does the "working the magic" streaming hold up inside an extension sheet,
  and what does the reader view (pills, tap-to-reveal, ledger) look like in SwiftUI?
- **Method:** extend the S2 project. First-token and full-piece latency on the phone for
  300 / 1,000 / 3,000-word inputs on gemini-3.1-flash-lite.
- **Done when:** latency table + a screen recording the founder reviews.

### S5 — Screenshot OCR fallback *(only if S3 shows Facebook/Kindle matter)*
- Vision text recognition on a shared screenshot → `/transform`. Time-boxed to one day.

---

## 8. User-story backlog

"As a reader, I want … so that …". Tags: **PoC** (needed for the 14-day self-test),
**MVP** (iOS app), **H3** (Horizon 3). Acceptance detail is added to a story when it is
picked up, not before.

### Epic A — Capture *(carried from PRD §8, unchanged)*
- **A1** (MVP) type a word into the app so it joins my list.
- **A2** (MVP) share a word from any app via the share sheet so capture never interrupts reading.
- **A3** (MVP) see a word card — definition, register, collocations, nuance — so the card beats a Kindle lookup.
- **A4** (MVP) mark a word retained, reactivate it, or archive it (D26), so my list reflects what I actually know.

### Epic B — Invoke ("RetAInize this")
- **B1** (PoC, S2) in Safari, tap the RetAIn action and read the page with my words in a sheet, without leaving the page.
- **B2** (PoC, S3) share a link from any app and read it transformed.
- **B3** (PoC, S3) share selected text from any app and read it transformed, so it works even where links can't be fetched.
- **B4** (PoC, S0) paste text or a link into the app and transform it — the baseline.
- **B5** (later, S5) share a screenshot and have RetAIn read it, for apps that lock text.
- **B6** (H3) in Safari, have my words substituted in place so the page itself changes.

### Epic C — Read
- **C1** (PoC, S4) see the piece stream in with a visible "working the magic" moment, so waiting feels like something happening for me.
- **C2** (PoC) see my words highlighted; tap one to reveal meaning and times seen.
- **C3** (MVP) a tap counts as "didn't remember", no tap counts as exposure (D7 semantics without interval scheduling), so the ledger is honest without a quiz.
- **C4** (PoC) see the source link and an "adapted with AI" disclaimer on every piece (D33).
- **C5** (MVP) find every piece I've transformed in My Reads, highlights recolored by current word status (D24).

### Epic D — Engine *(mode decided by S1 → D35)*
- **D1** (PoC) words appear only where idiomatic; QC-rejected words are absent, not un-highlighted (D9, D19, D29).
- **D2** (PoC) the facts and meaning of what I chose to read are preserved.
- **D3** (PoC) less-served words are preferred when fits are equal (D32 sort, no intervals), so the same easy five don't hog every piece.
- **D4** (open) choose how aggressive the transform is, from substitute-only to free rewrite.

### Epic E — Business *(deferred; listed so it is not lost)*
- **E1** monetization model — credits per transform / bring-your-own API key / subscription — **undecided**, revisit after S0–S4.
- **E2** (PoC) cost telemetry per transform from day one, so E1 is decided with numbers.

---

## 9. Open questions

- **Monetization** (E1): on-demand use changes the cost shape from "per digest per day" to
  "per transform, user-controlled". Credits, BYO key, subscription with fair-use cap — no
  decision until usage data from S0 exists.
- **Engine mode** (S1 → D35).
- **Browser plugin timing:** Safari web extension for in-place substitution (B6) — after
  the iOS app, unless S2 shows the action extension is weak and in-place is the only good
  Safari experience.
- **Android:** has the hooks iOS lacks (`ACTION_PROCESS_TEXT`, accessibility overlays) —
  in-place transform is possible there. Parked; not pursued.
- **Competitive scan** (PRD §6 open item): Toucan and Fluent (in-place foreign-language
  substitution in the browser) are the closest analogs — from memory, unverified. Do the
  scan before MVP investment.
- **Success-criteria thresholds** N and X (§6) — founder to set.
