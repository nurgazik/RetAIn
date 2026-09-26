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

## 6. Success criteria — revised 2026-09-24 (founder ruling, D35)

**Founder's ruling after S0:** "as long as it can travel from app to app and easily get
invoked against any piece of text content, we are in good shape. The learning was purely
technical." PoC 2's gate is therefore **technical feasibility**, not habit formation.
The habit question stays open as an observation, not a gate.

| # | Gate | Answered by | Status |
|---|---|---|---|
| 1 | The transform can be invoked from any app against any text and read back in ~20 s | S0 | **Passed 2026-09-24** (clipboard Shortcut, phone → Mac via Tailscale) |
| 2 | On iOS, a sheet over the host app can read the shared text (and, in Safari, the page itself), stream the piece, and hand it to the main app | G1 (S2+S3+S4) | open |
| 3 | Word-fit on the founder's real reading is acceptable: placed-and-QC-clean words per 1,000 words ≥ X, zero surviving misuses on read-through; engine mode chosen | G2 (S1) | open — X set by founder after seeing the data |
| 4 | Facts, meaning and register of the source survive the transform on founder read-through | G2 (S1) | open (S0 sample: yes) |

**Observation, not a gate:** the 14-day invocation count from S0 (`[transform]` log lines,
`user_text` rows). Reported at MVP scoping (Phase 1) as evidence, with no threshold.
Rationale for keeping it: habit is what closed PoC 1; the count is free.

**Go/no-go:** gates 2–4 pass (or fail with a workable fallback) → Phase 1 decisions, then
MVP build. Gate 2 fails outright on Safari → the product is share-sheet-only; decide
whether that is enough. Gate 3 fails → engine work before any app code.

---

## 7. Technical spikes (ordered)

Spikes are time-boxed investigations that end in a written finding here, not shipped
features. Findings are appended under each spike as they land.

**Backlog mapping (2026-09-24):** S0 = done. S2, S3 and S4 share one throwaway Xcode
project and run as a single backlog item, **G1 "extension spike"**; S1 is **G2**; the
terms-of-service half of S3 is split out as **G3** because it is a legal reading, not
code. S5 stays conditional. See §8 for the ordered backlog.

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

**iOS Shortcut "RetAInize" — built and verified on the founder's phone 2026-09-24.**
Clipboard version (five actions, no Share Sheet yet):

1. **Get Clipboard**
2. **Get Contents of URL** — `http://rays-mac-mini.tailb493b3.ts.net:8484/api/transform`,
   Method POST, Request Body JSON, fields `text` = Clipboard, `source` = `shortcut`
3. **Get Dictionary Value** — key `read_url` in Contents of URL
4. **Text** — `http://rays-mac-mini.tailb493b3.ts.net:8484` immediately followed by the
   Dictionary Value variable (no line break)
5. **Open URLs** — the Text

Use: copy a passage in any app → open Shortcuts → tap RetAInize (or ▶ in the editor).
Safari opens the read page and the piece streams in. Because it reads the clipboard, it is
app-agnostic — Reddit, X, Safari, Kindle all work the same way. Share Sheet (ⓘ in the
editor → Show in Share Sheet, with a "Receive input" block) is an optional refinement.

**Gotcha found during the first run — iOS "Limit IP Address Tracking".** The shortcut's
POST arrived and the read page loaded, but the page's own `/api/rewrite` request never
left the phone and the page showed "Can't reach your Mac". Cause: Safari routes insecure
HTTP through Apple's relay when *Limit IP Address Tracking* is on (per Wi-Fi network and
per cellular setting; it applies even with iCloud Private Relay off), and it drops the
in-page fetch silently after showing a "This Connection Is Not Private" interstitial for
the navigation. Fix applied: Settings → Wi-Fi → ⓘ → Limit IP Address Tracking off (and
the same under Cellular → Cellular Data Options). Durable fix if this bites again: serve
over HTTPS via `tailscale serve` (needs HTTPS certificates enabled in the tailnet admin
console — currently off). Verified working run: 639 chars → 3 words placed, 188 words,
ledger row with `section = shortcut`.

S0 text-only scope guard: the server rejects anything under 200 characters, and the
Shortcut sends text, never a link — URL fetching waits on the S3 terms reading. The
invocation log line `[transform] <ip> source=<app> chars=<n> id=<id>` in
`~/Library/Logs/retain-server.log` plus the `user_text` rows are the 14-day count.

### S1 — Word-fit on real content: substitute, rewrite, or hybrid?
- **Question:** on ~10 pieces the founder actually read this week, how many of the 50
  words land naturally per 1,000 words, QC-clean, under rewrite / substitute / hybrid?
- **Method:** new wrapper `prompts/transform.md` (+ substitution variant); run through
  `generate_piece` with QC on (D19), density floor off. Measure marks/1,000w, QC reject
  rate, `invented_numbers` hits, and founder read-through rating. Compare page
  `output/compare-transform.html` (existing pattern).
- **Done when:** 3 variants × 10 pieces table + founder ruling on engine mode → D35.

**G2 results (2026-09-24) — 5 pieces the founder read, 3 modes, QC on, density floor off,
gemini-3.1-flash-lite.** Harness `src/g2_wordfit.py`; fixtures `data/g2-pieces/`; compare
page `output/compare-transform.html` (founder rating pending).

| Mode | Marks (all 5) | Marks / 1,000 w | Length vs source | QC rejected | Fidelity on read-through |
|---|---|---|---|---|---|
| rewrite (production posture) | 15 | 8.1 | ×1.11 (two pieces +23–24%) | 2 (+1 un-highlighted last resort) | **Fails.** Density was bought with invented clauses: "a figure that continues to *bolster* its position as a major player", "all of whom seem to rely on the platform as a *linchpin*", "he said with characteristic *candor*", "a *windfall* that has quickly turned heads". Editorialising on news; fabricated attribution. |
| substitute | 4 | 2.4 | ×1.00 (verbatim) | 2, plus one marked source word | **Holds.** But ≈1 slot per piece; one piece got zero. |
| hybrid | 6 | 3.6 | ×0.97 (one piece −18%: dropped paragraphs) | 1 | **Mixed.** Also invented ("To *underscore* the scale of this growth, he noted that…" — a statement he did not make) and truncated one piece. |

Per piece (marks / words):
01 tech news — rewrite 5/295, substitute 1/241, hybrid 1/194 · 02 tech-culture — 5/637,
1/584, 1/581 · 03 literary essay — 1/296, 1/293, 1/291 · 04 local news — 3/427, 1/424,
2/427 · 05 Reddit post — 1/191, 0/155, 1/156.

**Reading of the result.** On real, reader-chosen content with the current 50-word list,
natural slots are rare — about one per 350 words — and every mode that reaches higher
density does it by fabricating text. The rewrite prompt forbids adding information and
Flash-Lite added it anyway, sentence after sentence. The QC gate judges idiomatic fit, not
added propositions, so fabricated clauses pass. The engine, not iOS, is now the main
product risk.

Caveat on the measurement: the 50 words are a seeded list (generated 2026-07-22 plus
founder additions), not words captured from the founder's own reading. In the real
product the list comes from what the reader reads, so slot frequency should be higher
than this measures — by how much is unknown.

**Founder ruling 2026-09-24 → D36: rewrite mode on Gemini Flash-Lite, fidelity relaxed
("AI can invent stuff for the purposes of word embedding once in a while; refer to the
source of truth if important"); no costlier model.** Implemented as: added phrasing OK,
added facts/figures/quotes/attributions not OK (`prompts/transform.md`), and the
disclaimer on every piece rewritten to say so. The candidate list below is kept as the
record of what was considered.

**Sanity rerun under the D36 prompt (rewrite mode, same 5 pieces, same evening):** 15 marks /
1,860 words = 8.1 per 1,000 (unchanged), length ×1.10, QC rejected 3 (salient, extrapolate,
conundrum — all correct calls). The facts/attributions line is **not** reliably obeyed by
Flash-Lite: "He remained *adamant* that the focus on the end-user product is what separates
them…" (a stance the source never states), "Investigators hope these digital findings will
*corroborate* the timeline…" and "He approached the sensitive subject with a somber
*gravitas*" (both invented, on a story about a death). Two QC-rejected words also survived
un-highlighted after the regeneration failed ("a *windfall* of growth", "*astute* handling")
— the D29 last-resort floor, which teaches the misuse it was meant to hide. Accepted risk
under D36; cheapest mitigation that stays on Gemini: a second judge pass (same model,
~$0.0005) that rejects sentences carrying a claim, attribution or characterisation absent
from the source. **Founder approved; built the same evening (`generate.py`: `fact_qc`,
`repair_paragraphs`, `drop_invented`).** The judge is calibrated to D36: evaluative colour
and connective phrasing pass; hard inventions fail — new facts/figures/names, words,
motives or manner attributed to a named person or organisation, changes inside quotes,
claims about what an investigation shows. A flagged word joins the D29 regeneration;
residuals get a paragraph rewrite without the word (two tries), then the invented sentence
is dropped if it carries no other highlight, and only then the old un-highlight floor.

Rerun with the judge on (rewrite mode, same 5 pieces): **10 marks / 1,796 words = 5.6 per
1,000, length ×1.06** (vs 8.1 and ×1.10 unguarded). All ten highlighted sentences read as
colour, none attributes words or motives to a named person. Cost: ~2 extra cheap calls
per piece (judge, sometimes repair). The ~30% density cost is the price of the rule.
1. **Substitute-only, accept ~1 word per piece** — zero-fabrication; value = an honest
   encounter now and then; encounters scale with reading volume.
2. **Rewrite with a stronger model + a fact-QC** — rerun rewrite mode on claude-haiku-4-5
   (D5 fallback, ~5× cost, still cents) and add a second judge that rejects any sentence
   whose propositions are not in the source. Tests whether fidelity can be bought.
3. **Highlight organic occurrences** — when a target word already appears in the source,
   mark it (ReadSmart-style; zero risk); stacks with 1 or 2.
4. **Reader-set aggressiveness** (D4) — ship substitute as default, rewrite as an opt-in
   "more words, looser text" mode with the disclaimer made prominent.

### S2 — Safari action extension: can we read the rendered page and show our sheet?
- **Question:** does an iOS action extension with a JavaScript preprocessing file get the
  page DOM from the user's session (paywalled / logged-in included), and can it stream from
  our endpoint and render within the extension memory budget?
- **Method:** verify Apple docs first (no working from memory). Then a throwaway Xcode
  project: action extension + JS preprocessing returning article text; SwiftUI sheet that
  POSTs to `/transform` and streams. Test on 5 pages: open article, paywalled article the
  founder is logged into, reddit.com thread, x.com post, a very long page (memory).
- **Done when:** works/fails per page, Apple-docs citations, measured memory + latency.

**G1 step 1 — Apple docs verified (2026-09-24), before any code:**

| Question | Answer | Source |
|---|---|---|
| Can an iOS action/share extension read the Safari page? | **Yes.** `NSExtensionJavaScriptPreprocessingFile` names a JS file; Safari runs its global `ExtensionPreprocessingJS.run(arguments)` and passes whatever `arguments.completionFunction({...})` returns to the extension as a property-list item under `NSExtensionJavaScriptPreprocessingResultsKey`. Requires `NSExtensionActivationSupportsWebPageWithMaxCount` ≥ 1 in the activation rule. iOS-only `finalize()` can even write back into the page. | Extensibility PG "Accessing a Webpage"; current key reference: **iOS 8.0+, not deprecated**, "supplied by a Share or Action extension" |
| Can it show full custom UI? | Yes — action extensions "always appear in an action sheet or full-screen modal view"; `NSExtensionActionWantsFullScreenPresentation` for full screen. | Extensibility PG "Action" |
| Memory / lifetime | "Memory limits … significantly lower than … a foreground app"; "the system may aggressively terminate extensions"; launch "well under one second" or it is killed; no `UIBackgroundModes` (App Store rejects). Exact MB figure is **not** documented — measure on device (sub-question d). | Extensibility PG "Creating an App Extension" |
| Networking inside the sheet | Ordinary `URLSession` data tasks work while the extension is alive (our streaming case); for work that must outlive the sheet, a background session with `sharedContainerIdentifier` = the app group, and the containing app finishes it. | Extensibility PG "Performing Uploads and Downloads" |
| Handoff to the main app | App groups: shared container + `UserDefaults(suiteName:)`; "use Core Data, SQLite, or POSIX locks" to coordinate. Current Xcode article confirms app groups are for "an app extension … and its host app". | Extensibility PG "Sharing Data"; Xcode "Configuring app groups" |

Reading: the mechanism the product depends on is documented, current, and old enough
to be stable (iOS 8). The unknowns that remain are empirical: the real memory ceiling,
streaming behaviour inside the sheet, and what each native app hands over — exactly
sub-questions (b)–(d). **Simulator covers (a), (c), (e) with Safari; (b) and (d) need the
founder's phone.**

**G1 step 2 — simulator results (2026-09-24, iPhone 17 simulator, iOS 26, Xcode 26.4).**
Throwaway project in `spikes/g1-extension/` (regenerate with `xcodegen generate`; UI test
`UITests/SafariExtensionTests.swift` drives Safari → More → Share → RetAInize).

| Sub-question | Result | Evidence |
|---|---|---|
| (a) Safari action extension reads the page | **Yes.** `RetAInPage.js` ran inside en.wikipedia.org, chose `<main>`, returned title, URL and 1,475 chars of visible text; extension received it under `com.apple.property-list` → `NSExtensionJavaScriptPreprocessingResultsKey`. | spike.log: `types: com.apple.property-list \| js-preprocessing: root=MAIN text=1475` |
| (c) Request survives inside the sheet | **Yes.** 4.9 s round-trip (POST + generate + QC) with the sheet open; piece rendered with highlight and tap-to-reveal. In-app paste path: 6.6 s. | `done … latency=4872ms`; screenshot `sheet-result.png` |
| (d) Memory | Extension launched in **41 ms at 21 MB**; **45 MB peak** during generation; **55 MB** with the piece rendered in a WKWebView. Apple publishes no figure; the commonly reported extension ceiling is ~120 MB (unverified) — measure on device. A native text renderer instead of WKWebView would cut ~15–20 MB. | footer readout |
| (e) App-group handoff | **Yes.** Extension wrote the piece to `group.com.retain.spike/reads.json`; the main app's stub My Reads lists it. | `group ok`; app list |
| (b) Native-app share payloads | **Device-confirmed 2026-09-25 (founder's iPhone 16 Pro, iOS 26):** text selections shared from native apps arrive as `public.plain-text` (639, 742, 828, 1,532 chars) and transform fine. **Reddit's own Share button on a post/comment sends `public.url` only** (diagnostics 16:36) — no text — so under D37 the Reddit routes are select-text → Share, or "Copy text" → open RetAIn → clipboard offer. Browser articles (BBC, TechCrunch, **Safari** — founder-confirmed) arrive as page text of 3.7–6.3k chars via the JS pre-step. **Copied text from any app** (Reddit "Copy text" → share/paste) works as the universal route; a 90-word physics post got an honest zero (both judges rejected the only candidate, guard restored the sentence). X, Kindle, Apple News, Chrome still unlogged. | Spike log on the phone: `types: public.plain-text`, `text: 639 chars` / `742 chars` |
| (d) Memory on device | Share extension launched in **17–18 ms** at **4–19 MB**; **peak 49–56 MB** with the piece rendered in WKWebView. Comfortably inside any plausible extension ceiling. End-to-end 8.0–9.0 s via Tailscale to the PoC server. | Spike log: `launch=17ms mem=4MB … memPeak=49MB`, `launch=18ms mem=19MB … memPeak=56MB` |

Findings worth carrying into the MVP:
- `innerText` returns only *visible* text: on mobile Wikipedia the collapsed sections were
  excluded (1,475 chars of a long article). MVP extractor should use a readability-style
  pass over `textContent`, not `innerText`.
- iOS 26 Safari has no direct Share button in the compact bar; Share sits inside the
  "More" menu, and first-run tips cover the toolbar. The UI test handles both.
- One placement in the Wikipedia lead read slightly off ("proven to **bolster** the rate
  of learning") — a G2 data point.
- With `CODE_SIGNING_ALLOWED` default and no team, simulator builds sign ad hoc and the
  app-group entitlement works; device builds need the founder's Apple ID in Xcode.

Tooling status on the Mac mini: Xcode 26.4 present; no code-signing identity and no
Apple ID team in Xcode yet (device runs need the founder to sign in once); no project
generator installed — proposal: `xcodegen` via Homebrew (dev tool only, not a product
dependency) so the throwaway project is a readable YAML file in the repo.

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

## 8. Backlog

Moved to **docs/backlog.md** (2026-09-26) — four epics, pending decisions, done ledger.
This file stays the PoC 2 record: rationale, gates, spike findings, engine measurements.

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
