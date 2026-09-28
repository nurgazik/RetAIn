# RetAIn — Progress Log

Catch-up file for founder and assistant alike. **Convention: update the "Now / Next"
block and append a dated entry at the end of every working session.** Newest entries
first. Decisions live in PRD.md's log (D1–D34); this file is the narrative timeline.

---

## NOW (as of 2026-09-28)

**Phase: MVP build (Phase 2) — M1–M6 built and verified on the founder's phone; Sign in
with Apple live; membership active; M8 (monetization) and M9 (TestFlight) remain.**
PoC 1 (daily digest) closed 2026-09-24; PoC 2 passed its technical gates (D35). Product
shape: capture words → share/copy whatever you're reading → sheet over the host app →
piece with your words → My Reads. Service: `src/service/` on the Mac mini, public HTTPS
via Tailscale Funnel. App: `ios/RetAIn/` (xcodegen).

**Engine + reader (D40/D41, live 2026-09-26):** one model call places words three ways —
SUBSTITUTE, REPHRASE, or a SUPPLEMENT note (general background, inline, code-checked) —
aiming for one word per ~120-word stretch; judges stay, a rejected word reverts its
sentence (no re-runs). Reader: highlight + margin bracket per tier (green / blue / yellow;
founder's neon palette in dark mode; Figma "D" bar shapes, UX-13 done), tap a bar for a hint, tap a sentence for the
original, tap a word for its meaning. Safari shares are cleaned by Mozilla Readability.
**Top open problem: density** — ~1.5–2 words per article; the model under-attempts and
the checker rejects about half of its in-text words (backlog UX-1; test models via TD-13).
**2026-09-28 (D50, UX-15):** Siri capture built — "Hey Siri, add a word to RetAIn" → "Which word?"
(Apple allows no free word inside the trigger phrase). Builds and unit-tests on the simulator;
**not yet tried on the phone** (Siri, locked phone, time to answer on a new word).
**2026-09-28 (UX-14):** home-screen widget "Today's words" built — 5 learning words a day,
one at a time with meaning, › to advance; verified on the founder's phone. Bottom row reads "Today's words · n / 5".
**Next up:** founder's call on stretch length; model evals on surviving words per article.
**2026-09-27 (D48, UX-4):** word cards built — Wiktionary stored on the Mac mini
(`data/dictionary/wiktionary.db`), meanings in Wiktionary order, model-written examples, one
shared card per word; unknown words checked by the model, nonsense saved "unverified" and kept
out of rewrites. Reader word tap → card in a bottom-half sheet; widget shows the first meaning
+ "+N more" and opens the word. **Word-only prompts** (no definitions to the writer/judge)
passed the golden-set eval on quality but ran ~2.5× slower because OpenRouter routed them to a
slower host. **2026-09-28 (D49):** fixed — OpenRouter host order + a Flash-Lite race;
word-only prompts are now live. Watch speed with `python -m service.speed` (from `src/`).
**2026-09-27 (sharing, D45):** every app's Share button should work — one source at a time.
Sharing is now one reader per source behind a router (`ios/RetAIn/Shared/Sharing/`): selection,
Safari page, plain text, Reddit (post or the linked comment), any web link (Chrome) — all
verified on device. Facebook (D46) built: public posts read; private groups / friends-only
posts get specific messages; verified on device. X (D47) via oEmbed, verified on device —
long posts arrive cut; the sheet points to Safari, which gets the full post.
Reddit, Meta and X terms risks accepted while the founder is the only user — **revisit before
anyone else installs the app, TestFlight included** (backlog AD-10). Open bug: date-only
publish dates show a day early (TD-15).
**2026-09-27 (D44):** Safari shares keep page metadata (byline, site, date, sub-headline)
out of the body and show it as a reader header; never sent to the model. Verified on device.
**2026-09-27 (D43):** notes may now sit in a stretch that already has a word (max one
note per stretch). Open: empty stretches get no second chance (gap-fill call proposed),
and most notes die on "needs exactly one marked word".

**2026-09-26:** founder signed in with Apple on the real build (account
u_152716…, nurgazy7@gmail.com); first transform on the real account ran; account seeded
with the 50 words from data/words.json (+ his own "adversity"). `data/service.db` was
tracked in git by mistake — now untracked and ignored (history still contains earlier
copies; founder decided 2026-09-26 not to purge).

**Start here (new session, any model):** read this NOW block, then `docs/backlog.md`
(pending decisions DEC-1..5 at the top; epics TD/MO/UX/AD), then PRD.md decisions D34–D39.
Working agreement: commit locally as work lands, push in batches at milestones and say
so; no `rm`; no installs without asking; product decisions discussed before code;
architecture choices proposed to the founder before code (he wants to learn them);
restart the service after any `src/`/`prompts/` change, unasked.
- Figma: remote MCP server installed at user scope and authenticated (2026-09-26); tools
  load only in sessions started after that.
- Service: launchd `com.retain.service` → http://127.0.0.1:8585 and
  https://rays-mac-mini.tailb493b3.ts.net (Tailscale Funnel). Restart:
  `launchctl kickstart -k gui/$(id -u)/com.retain.service`. Log: ~/Library/Logs/retain-service.log.
  Tests: `.venv/bin/python -m pytest -q tests`. DB: data/service.db (gitignored).
  Secrets in .env.local (`RETAIN_DEV_TOKEN` for curl/simulator; `RETAIN_ENGINE_MODE`
  defaults to `sentence`, `rewrite` restores D36).
- App: `ios/RetAIn/` — `xcodegen generate`, then `xcodebuild -project RetAIn.xcodeproj
  -scheme RetAIn -destination 'platform=iOS Simulator,name=iPhone 17' build`; unit tests
  need `TEST_RUNNER_RETAIN_DEV_TOKEN=<token>`; UI test drives Safari (see
  UITests/SafariActionTests.swift). Device builds: full project from Xcode GUI (team
  UKGU6PX43H, paid) or `project-device.yml` variant headless (no entitlements, dev token).
  Founder's real account exists (Sign in with Apple) with 51 words.
- Engine: `src/generate.py` (`generate_piece`, `sentence_guard`, judges), prompts in
  `prompts/`; measurement harness `src/g2_wordfit.py` on `data/g2-pieces/`.

**Digest server status:** `src/serve.py` still runs (launchd agent, Tailscale) and becomes
the host for Spike S0's `/transform` route. Fetchers, calendar slots and editions are
retired but not deleted.

**Backlog (docs/poc2-transform.md §8) — Phase 0 gates, then Phase 1 rulings, then MVP.**
Founder ruling D35: technical feasibility is the PoC 2 gate; the 14-day invocation
count keeps running as an observation only.

**Backlog restructured 2026-09-26 into four epics — Tech Debt / Monetization / UX /
Administration — with a "Decisions pending" table on top (**docs/backlog.md**).
Recommended first moves: AD-2 privacy policy, AD-3 account deletion, UX-3 first-run —
all needed for TestFlight and none waits on a decision.**

**Next up (in order):**
0. **G1 — simulator half DONE.** Safari action extension reads the page via JS
   preprocessing, sheet over Safari, 4.9 s transform, 55 MB peak, app-group handoff
   confirmed (spikes/g1-extension/, UI test drives Safari). **Remaining: native-app
   share payloads + device memory — needs the phone + Apple ID in Xcode.**
   **G4 competitive scan DONE** → docs/competitive-scan.md (gap is real; neighbours
   monetise poorly).
   **G2 DONE, result is the new top risk:** on the founder's 5 real pieces, substitute
   mode finds ~1 slot/piece (2.4 marks/1,000 w, verbatim text); rewrite mode reaches
   8.1/1,000 only by inventing clauses on news ("he said with characteristic candor").
   Compare page: output/compare-transform.html. **Ruled → D36:** rewrite mode on
   Gemini, fidelity relaxed (phrasing may be added, facts/quotes/attributions may not),
   disclaimer rewritten; no costlier model. **D37:** link intake out of the MVP.
   **G3 DONE** → docs/link-intake-legality.md: Reddit `.json` dead + API excludes
   monetised apps; X free tier gone, oEmbed truncates; recommendation = selected text
   for Reddit/X, in-Safari extension for articles. **Founder ruling → D37.**
1. **S0 — DONE end to end (2026-09-24).** `/transform` + `POST /api/transform` live on
   the always-on server; the founder built the clipboard-based "RetAInize" Shortcut and
   a real run from the phone produced a 3-word piece in the ledger. **The 14-day "do I
   reach for it?" count starts today.** Recipe + the "Limit IP Address Tracking" gotcha
   in docs/poc2-transform.md §7 S0. Text only until the founder rules on URL fetching.
2. **P1 DONE — PRD §8 rewritten to the PoC 2 MVP** (surfaces, engine with gates, service,
   economics ≈ $0.003/transform, proposed TestFlight metric). P2 monetization deferred by
   founder until usage data; **P3: founder sets thresholds.**
3. **M1 transform service — BUILT AND RUNNING (2026-09-24 evening).** `src/service/`
   (FastAPI 0.141 / uvicorn / PyJWT, `.venv/`, `requirements.txt`); launchd agent
   `com.retain.service` on port 8585 (log ~/Library/Logs/retain-service.log); SQLite
   `data/service.db`. Verified by curl with the dev token: 401 without auth, 50 seeded
   words, 422 on short text, transform → SSE phases generating→checking→regenerating→
   repairing→done → piece in 7.2 s, 8 itemised model calls = $0.0038, tap recorded,
   word card created, in-flight piece re-queued after a restart. Sign in with Apple is
   coded per Apple's rules but untested until the app exists (M2; bundle id assumed
   `com.retain.app`, set `RETAIN_APPLE_BUNDLE_ID`). **Remaining: Tailscale Funnel** — the
   CLI hung silently on `tailscale funnel --bg 8585`, which usually means Funnel/HTTPS
   isn't enabled for the tailnet yet (founder: admin console).
4. **M2 iOS app shell — BUILT (2026-09-24/25), simulator-verified.** `ios/RetAIn/`
   (xcodegen project; app + share extension + Safari action + unit tests + UI test).
   Screens: Sign in with Apple (+ Debug dev-token entry), Words (add / swipe lifecycle),
   My Reads, RetAInize paste box with "transform what you just copied?", Settings.
   Shared: API client with SSE phase stream, keychain session shared via the app group
   (simulator fallback via app-group defaults), reads cache, the product sheet, both
   extensions (single word → capture, text → transform). Verified: unit tests pass against
   the live service (transform → phases → piece → tap → list); in-app paste produced a
   3-word piece in 6.9 s; Safari UI test (More → Share → RetAIn → sheet) produced a 2-word
   piece in 6.4 s. **Not yet verified: Sign in with Apple on a device** (needs Apple ID in
   Xcode + phone) and **Funnel HTTPS** (founder ran the command; status unknown to me).
   M3/M4/M5/M6 are largely covered by the shared sheet and extensions; what remains for
   them is device validation of native-app share payloads and capture polish.
   **Device results (2026-09-25, founder's iPhone 16 Pro):** spike share extension from a
   native app — payload `public.plain-text` (639 / 742 chars), launch 17–18 ms, peak
   49–56 MB, 8–9 s end to end via Tailscale → G1 (b) and (d) answered. **M2 app installed
   on the phone by the assistant via devicectl** (device variant: team UKGU6PX43H, no
   entitlements — Apple confirms personal teams can't sign Sign in with Apple; App Groups
   worked for the spike via Xcode's GUI but not headless). Funnel live:
   https://rays-mac-mini.tailb493b3.ts.net.
   **Founder to-dos:** paid Apple Developer membership (waiting on Apple for the team id
   → Sign in with Apple, App Groups headless, TestFlight); P2 monetization; P3 thresholds;
   **density idea (founder: "a creative task, later")**. Tailscale "Launch at login" ✔
   (2026-09-25) — server survives a Mac reboot.
   **Working agreement (2026-09-25):** commit locally as work lands; push in batches at
   milestones and say so; no `rm`, no installs without asking (these are the founder's
   global "ask" rules and they are what triggered the overnight approval prompts).
   **M2 VERIFIED ON DEVICE 2026-09-25 05:28 UTC:** share extension from a native app →
   new service over HTTPS → 828-char plain-text payload → 3 words in 2.7 s, $0.0016,
   diagnostics stored in `pieces.meta`. (Device build: `project-device.yml`, Debug server
   must be the Funnel URL, not 127.0.0.1 — first attempt failed on that.) M3 (share-sheet
   sheet) therefore verified on device; M4 (Safari) and M5 (single-word capture) await
   the founder's next two shares. **05:34 UTC: second device share (1,532 chars plain
   text from Safari as a selection → 2 words, 11 s, a tap recorded) and M5 capture
   verified ("remain" added with a generated card, $0.00005).** M4 (Safari page action
   via JS preprocessing) still unproven on device — the founder's Safari share used the
   text path.
   **06:44 UTC: M4 VERIFIED ON DEVICE** — Safari page action on a TechCrunch article: JS
   preprocessing delivered 3,673 chars of page text (`types: com.apple.property-list`,
   `pageChars: 3673`), 3 words in 10.6 s, $0.0073. The plain "RetAIn" share entry from
   Safari also received the page (3,344 chars). Newly captured "remain" was placed first
   in the next piece (fewest-servings-first sort working as intended).
   **All build items M1–M6 are now verified on the founder's phone over HTTPS.**
   **Overnight 2026-09-25 (founder asleep) — all 8 backlog items shipped, tested, on the
   phone** (spec §8 "Overnight backlog" has the per-item detail): diagnostics + 25-word
   minimum for shares; **sentence-scoped engine mode is now the default** (mechanical
   sentence guard, edited sentences underlined; 2.4 words/1,000 vs 5.6 for rewrite —
   founder ruling needed); foreground refresh; per-call latency (model time ≈ 100%,
   judges now parallel); popup stats + "Got it"; dark mode; pytest suite (7 green);
   spend in Settings. Unit tests 3/3, UI test green, service tests 7/7.
   **Morning decisions for the founder (independent):** (a) density: keep sentence mode
   at ~1 word/piece, revert to rewrite, or a middle setting; (b) retry the Reddit comment
   share (diagnostics now logged); (c) Launch Tailscale at login; (d) paid Apple
   Developer membership: **ruled D39, individual enrollment; founder enrolling, then
   sends the Team ID → set it in project.yml + project-device.yml**; (e) which app the earlier shares came from; (f) cap input
   length for long pages (10–14 s) or accept; (g) retire the digest server + shortcut?
   **Morning 2026-09-25:** founder's Reddit share arrived as `public.url` only →
   "Only a link arrived" message shown as designed; Reddit routes = select-text or
   Copy-text → clipboard offer (D37 stands). Four browser articles transformed today
   (page text 3.7–6.3k chars, 1 word each under sentence mode; **browser = Safari**,
   founder-confirmed). Copied text from any app works (founder). Founder: membership
   pending team id; density idea coming; earlier-share provenance dropped.
5. **Next:** M8 monetization (blocked on P2) and M9 TestFlight (blocked on paid Apple
   Developer membership + P3). Daytime polish candidates: native text renderer,
   readability-style page extraction, Sign in with Apple device test once the
   membership exists →
   M8 monetization (needs P2) → M9 TestFlight (needs P3 thresholds + paid Apple
   Developer membership for App Groups on device and TestFlight).
5. Parked (Horizon 3): proprietary generator, Safari web extension in-place, screenshot
   OCR, Android, link intake (D37).

**Machine setup note:** work laptop pushes via SSH alias `github.com-retain`
(dedicated personal key `~/.ssh/id_ed25519_retain` — revoke from GitHub settings when
vacation coding ends). Home Mac: clone normally with personal credentials; recreate
`.env.local` (4 API keys — gitignored, never on GitHub) and `data/retain.db` refills
itself via the fetchers.

### 2026-09-28 — Siri word capture (D50, UX-15)

- **Constraint found first:** "Hey Siri, add the word *X* to RetAIn" in one sentence can't be
  built. App Shortcut phrases carry only values the app declares ahead of time (WWDC22: "it's not
  possible to gather an arbitrary string from the user in the initial utterance"); iOS 27 App
  Schemas cover fixed domains only. Founder approved the two-turn flow: "Add a word to RetAIn" →
  "Which word?".
- **Built:** `ios/RetAIn/App/Intents/AddWordIntent.swift` (asks for the word, re-asks if it isn't
  one word, calls the existing `addWord`, refreshes the widget cache, speaks "Added X" or "Saved X,
  but I couldn't find it in the dictionary. Check the spelling." for unverified words, shows a
  small card) and `RetAInShortcuts.swift` (4 phrases). The share sheet's one-word rule moved to
  `Shared/Sharing/WordInput.swift` so both paths use it; a punctuation-only share now gives no
  capture instead of an empty word. Runs inside the app: no new target, entitlement or server change.
- **Verified:** simulator build succeeds; the built app's App Intents metadata lists
  `AddWordIntent` with all 4 phrases. Unit tests 34/35 pass, including the new rule test and the
  existing share-capture test. The 1 failure is unrelated and older: the reader header shows
  "Sep 25" for 2026-09-26 in Pacific time → logged as TD-18.
- **Not verified yet (needs the phone):** Siri end to end, locked-phone run, and latency — a new
  word waits for its card call (p50 3.7 s; the 5 s hedge caps the tail), and Siri's time limit
  isn't confirmed. If too slow: return right after saving and let backfill build the card
  (server change, founder decides). Device test list: common word, rare word (*sesquipedalian*),
  a word already saved, a nonsense word.

### 2026-09-28 — Speed first: host order, Flash-Lite race, word-only live (D49)

- **Why the word-only arm was slow:** host choice, not the prompt. OpenRouter's default pick is
  weighted towards the cheapest host; a probe sent the same rewrite to each host: 10–118 s
  (Venice 146–191 tok/s, NextBit ~68, Reka/Novita 16–25; Makora, DeepInfra and Google Vertex
  refused with 429). Throughput sorting made things worse (runs 41/42: 11.9 s / 12.7 s).
  Google serves Gemma 4 only on its free tier (data used to improve products) — ruled out.
- **Built:** `PRIMARY` provider order Makora → Venice → DeepInfra (fallbacks allowed, ZDR only);
  `call_model` races Flash-Lite after 10 s (rewrite/repair) or 5 s (checks, cards); host logged
  per call (`calls.host`); `src/service/speed.py` report. 6 hedge tests; 44/44 service tests pass.
- **Measured (production path, same 10 pieces, minutes apart):** word only 9.1 s avg, 8.9 s p50,
  16.7 s max, all on Makora; with definitions 14.4 s avg, 42.4 s max, 3 Flash-Lite takeovers.
  Word-only made the default (`RETAIN_ENGINE_DEFS=on` reverts). Live transform after restart:
  3.1 s, all calls on Makora, host recorded.
- **Found:** TD-17 — daily cap and "spent today" compare a local date with UTC timestamps, so
  the day effectively runs 5 pm–5 pm Pacific (evening use counts toward tomorrow); this is also
  why two service tests failed last night. Low stakes while the founder is the only user.
- Word capture: card calls p50 3.7 s, p90 11.9 s (backfill) — the 5 s hedge now caps the tail.

### 2026-09-27 — Word cards from Wiktionary (D48, UX-4) + word-only prompt eval

- **Source research (n = 235 words):** commercial dictionary APIs ruled out (no permanent shared
  cache on public plans; Oxford enterprise only); iOS exposes no dictionary text. Wiktionary via
  kaikki.org's Wiktextract dump (CC BY-SA 4.0, 3.3 GB, download marked deprecated — our copy kept
  in `data/dictionary/`): 235/235 found, IPA 99%, modern usage example 62%. Spike:
  `spikes/wiktionary_coverage.py`. Decision **D48**. Diagram: `diagrams/word-capture-flow.md`
  (new `diagrams/` folder for major architecture/UX moments).
- **Built:** `src/service/dictionary.py` (reference DB build in 23 s, lookups < 1 ms; redirect
  rules ran → run, ubiquitious → ubiquitous, adjectives stay: protracted, scathing; proper names
  dropped; fraught keeps its all-"obsolete" senses), `lexicon` + `senses` tables, `words.lexicon_id`,
  capture never fails on a model error, backfill of the 235 test words. iOS: `WordCardView`
  (meanings, examples, IPA + on-device speech, badges, Wiktionary credit), reader bottom sheet
  replacing the web popup, widget "+N more" and `retain://word/<id>`.
- **Tests:** service 36 pass (6 new card tests); the 2 failures (transform lifecycle, daily cap)
  predate this work. iOS 33/34 pass; the one failure is TD-15 (known date bug).
- **Eval (founder: "the LLM should only get the word"):** golden set, 30 pieces, Gemma 26B,
  runs 37 (with definitions) vs 38 (word only), blind-graded in session (grader not yet checked
  against founder labels). Wrong usages 17/99 (17%) → 10/91 (11%); idiomatic 34% → 43%; marks/piece
  3.3 → 3.0; cost −21%. **Latency 6.0 s → 13.0 s p50**, reproduced on 10 pieces (runs 39/40:
  16.0 s vs 5.9 s). Cause: host routing, not model work — same output tokens, no reasoning; a
  probe (9 calls per mode) showed word-only prompts landing on NextBit (5.4 s/call avg, up to
  13 s) vs Makora (1.9 s) with definitions. Production switch `RETAIN_ENGINE_DEFS` left **on**.

### 2026-09-28 — Home-screen widget: today's words (UX-14)

- Founder asked for a swipeable 5-words-a-day widget. WidgetKit can't take swipes (only
  button/toggle taps via App Intents), so: medium widget, one word at a time with part of
  speech and meaning, "n / 5" counter, › button to advance (wraps). Learning words only;
  meaning always shown (founder's calls). Founder waived the product discussion.
- Structure: the phone had no copy of the word list, so the app now writes `/v1/words` to
  `words.json` in the app group (`Shared/Store/WordsStore.swift`, same pattern as
  `ReadsStore`) whenever it becomes active and whenever Words loads, then reloads the widget.
  The widget picks today's 5 with a shuffle seeded by the local date (same set all day, new
  at midnight); its position lives in app-group defaults. New target `RetAInWidget`
  (`ios/RetAIn/Widget/`) compiles only the three Shared files it needs.
- Apple docs confirm a widget button "always guarantee[s] a timeline reload".
- Tests: `WordsStoreTests` 5/5 pass; full unit suite 30 tests, 3 skipped (no dev token),
  1 failure = known TD-15 date bug. Not done: simulator home-screen check (adding a widget
  needs manual gestures) — founder to add it on the phone after installing from Xcode.

### 2026-09-28 — Relaxed-usage PoC ("close enough" words)

Founder's north star: each word used in the right context, repeatedly. PoC: writer prompt
(`prompts/core-relaxed.md`), request (`RELAXED_REQUEST`) and usage checker
(`RELAXED_QC_SYSTEM`) accept right-meaning-but-not-ideal usage; `generate_piece(relaxed=True)`,
off in production. Replay: same 20 shares × 2 runs × {prod, relaxed} (80 runs, $0.10), then
all 197 placed words blind-graded by a Claude helper (2 natural / 1 close enough / 0 wrong).
- Words per 100 source words: 0.46 → 0.58 (+27%); stretches covered 83 → 101 of 144.
- Graded usable (natural + close): 0.40 → 0.53 per 100 (+31%); natural only 0.30 → 0.34.
- Wrong usages: prod 10/86 (12%), relaxed 11/111 (10%) — the rate did not rise.
- The strict checker would have rejected 24/109 relaxed words; the grader called 6 of those
  natural, 13 close, 7 wrong — the strict checker is noisy in both directions.
- Cost: mean latency 14 s → 36 s (median 6 → 18 s; cause not isolated), $ +18%.
- **Found: production already ships ~12% wrong usages** (deft tasks, tenuous gap, nascent
  for "newest") **and puts words inside direct quotes** ("succinct" in an Iranian
  diplomat's quote) — the checker and fact judge miss both.
- Caveat: one AI grader, not yet checked against the founder's labels (TD-13).

### 2026-09-28 — Density PoC: salvage drafts + stricter notes (no gain)

Founder: 235 learning words, density still ~1–2 per piece. Hypothesis (from one piece,
p_64e7: drafts of 9/8/2 marks shipped 2): (1) drafts with any off-list mark rank last,
(2) notes come back without a target word. PoC behind `generate_piece(poc=True)` (off in
production) + `prompts/transform-sentence-poc.md`; replay `spikes/density_poc.py` on the
founder's 20 most recent distinct shares, 2 runs per mode (80 runs, $0.08).
- **Density unchanged:** 2.33 → 2.30 words/piece; 0.49 per 100 source words both; 59%
  stretches covered both. Long (>250 w, n=22 runs): 3.27 → 3.41. Short (n=18): 1.17 → 0.94.
- Why (1) didn't help: production's retries on off-list marks were acting as extra rolls
  (18 retries vs 2); salvaging saves calls, not words. p_64e7 was an unlucky roll.
- Why (2) didn't help: the stricter note rule barely moved empty notes (25 → 23 drops).
- Side effect: long pieces 21.6 s → 12.9 s, cost −22%. Checker reverts 6 → 13.
- Conclusion: words aren't lost after the fact; the model under-attempts (~41% of stretches
  get nothing). Levers left: stronger model (TD-13), stretch length, gap-fill call.

### 2026-09-28 — X reader via oEmbed (D47)

- Founder's X share said "may need a login or a subscription" — our generic message. One probe:
  X redirects embedded web views to `x-safari-https://redirect.x.com/…` ("open in Safari"), so
  the hidden view fails at once. Disguising it as Safari was offered as possible and advised
  against (getting around a deliberate block); founder chose X's oEmbed instead, as it's free.
- Checked docs.x.com: oEmbed needs no login, no payment, no rate limit. One request for his
  post: 200, author + text, cut at ~280 chars ("executing similar… https://t.co/…").
- Built `XReader` (no web view): oEmbed JSON → the embed's <p> as text (line breaks kept;
  Apple's HTML import turns <br> into U+2028, normalized), trailing t.co link dropped,
  `x-oembed-cut` when it ends "…". Messages: not public (404), not a single post, short post.
- Tests: 2 new (cut post from X's real response; 404 / profile link / short post); 15 sharing
  tests pass. Live, 7 links: X 45 words 0.2 s; Reddit, Chrome, Facebook unchanged.
- Probes now live in a throwaway `Tests/ZZProbeTests.swift`, moved out after use.
- Device: X-app shares arrive as a link and go through oEmbed (2 posts, 270–272 chars, cut).
  Full text test: a tapped x.com link opens the X app (iOS universal links), so the link must
  be pasted into Safari's address bar. Then Safari's page script got the whole Ajzenstadt post
  (2,479 chars, ~400 words vs 272 via oEmbed), clean, no replies — but @mentions dropped
  ("Good article from\n\n, especially") and paragraph breaks lost (backlog UX-5).
- Built the agreed hint: readers can return a `notice`; the share sheet shows it as a banner.
  Cut X posts say "X shortened this post. For the full text, paste its link into Safari's
  address bar, then share from Safari." 15 sharing tests pass.

### 2026-09-27 — Facebook reader (D46)

- Founder: Facebook can't share a link to a comment, so a Facebook link means its post. He
  wanted messages as specific as Facebook allows when a post can't be read.
- Probed his 3 links logged out: public page post → the post (cut at "See more"; comments
  and the page's other posts on the same page); private group post → the group's front page
  (`/groups/<id>/`, name + "Private group · 70.2K members", no post); friend's post → `/login/`.
- Found: no Facebook share had ever reached the server as a link. The 17:44 unusable row
  (plain text, 1 word) was likely his Facebook share — Facebook sends the link as text
  (inferred). `ShareInput.promoteLinkText` now treats text that is only a web address as a link.
- Built `FacebookReader`: waits past `/share/` redirect pages; group front page checked before
  posts (its About text matches its preview text); finds the post by its preview text
  (og:description — Facebook's class names are generated), taps the post text's own collapsed
  container (the separate "... See more" button does nothing), retries until it grows.
  Messages: private group (named), login ("probably friends only"), anything else (generic).
  `PageLoader.wait` now returns false on timeout (it used to report success).
- Tests: 4 new (public post + See more, private group named, login wall, link-as-text); 13
  sharing tests pass. Live, 3 links: public post 618 words 1.3 s; group message named; login
  message. Full suite: 23 tests, only the D44 date test fails (known).
- Process slip: removing a probe with `git checkout` wiped uncommitted tests in the same file;
  re-added. Probes now go in a separate throwaway file.
- **Verified on device 2026-09-28 (founder: "works well"):** a sponsored post (ad) from
  Campers & Canopies BC was read (`facebook-post`), arriving as `public.plain-text` — confirms
  Facebook shares links as text. One unusable Facebook share 16 s earlier; founder closed it,
  no investigation.

### 2026-09-27 — Sharing rebuilt as readers per source; Reddit posts and comments (D45)

- Chrome worked on device (Wikipedia piece, `linkFetch: ok`). Reddit's Share button gave
  "Couldn't read this page". One diagnostic load (founder's link) showed why: Reddit serves a
  JavaScript check page first (1 word at 1.1 s; the real post at 2.2 s) and we read on the first
  load; and Readability picked a 463-word comment over the ~220-word post.
- Founder: a share should read what the user meant — the post or a comment. A comment link
  lands on `/comments/<post>/comment/<id>/` (verified with his r/economy link), so the link
  decides; no guessing. Founder accepted the Reddit terms risk for now (D45).
- Founder asked for a proper structure since sharing is core. Agreed and built (Strategy
  pattern): `ShareInput` (what arrived) → `ShareRouter` asks `SourceReader`s in order —
  Selection, SafariPage, PlainText, Reddit, WebPage — first to claim reads. `PageLoader` (hidden
  web view) now polls each reader's own "ready" test instead of trusting the first load.
  Replaces `ExtensionInput` + `PageFetcher`. Diagnostics/meta now carry `reader`.
- Tests: `Tests/SharingTests.swift`, 8 pass (routing order, capture/fallback messages, Safari
  header fields, loader waits past a check page, web page script, Reddit post / comment / old
  permalink / short post). Live probe (opt-in, 3 links): Reddit post 221 words 1.5 s, Reddit
  comment 125 words 1.3 s, Wikipedia 2,192 words 0.8 s. D44 date test still fails (below).
- **Verified on device 2026-09-27** (4 shares, all done, no unusable-share rows): Reddit post
  ×2 (`p_26294cec…`, 763 chars, u/Pelican_Ceramic · r/AskACanadian), Reddit comment
  (`p_bd92b31d…`, 627 chars, only the linked comment), Chrome fandom wiki (`p_64e7d6c0…`,
  web-readability, 6,530 chars). One word placed per Reddit piece (UX-1 density, not sharing).

### 2026-09-27 — Link-only shares read on the phone (Chrome; D37 fallback built)

- Founder: Chrome's Share button gave "Only a link arrived". Cause: only Safari runs an
  extension's page script (JavaScript preprocessing); Chrome sends `public.url` only. Evidence:
  all 6 diagnostics rows to date were URL-only unusable shares.
- Founder's learning: nobody will select text and share it. Every source needs a one-tap
  Share-button route; solve them one by one, open-web articles first.
- No decision change: D37 already allowed a URL fetch as the fallback for non-Safari apps.
  Built it on the phone, not the server (agreed): `Shared/PageFetcher.swift` loads the link in a
  hidden WKWebView (no cookies), waits for load or 10 s, runs the same `RetAInPage.js`.
  `ExtensionInput.readLink` runs it only when no usable text arrived. The sheet shows
  "Reading the page…" meanwhile. Diagnostics/meta carry `linkFetch` (ok / short / failed) and
  `extractor: fetched-readability`.
- Tests: 5 new in `Tests/LinkFetchTests.swift`, all pass; opt-in live probe
  (`TEST_RUNNER_RETAIN_NET_PROBE=1`): 3 pages — Wikipedia 2,192 words <1 s, a BBC URL 1,471
  words ~1 s (page identity unchecked), TechCrunch homepage 78 (not an article, expected).
- Found, not fixed: `ReaderPopupTests.testHeaderShowsDekAndSourceLine` fails — a date-only
  `published` ("2026-09-26") is parsed as UTC midnight and shown in local time, so Pacific
  shows Sep 25 (D44 header, `PieceHTML.displayDate`).
- **Pending:** founder device test from Chrome (3–5 open articles + 1 paywalled page).

### 2026-09-27 — Page metadata out of the body, into a reader header (D44, UX-11)

- Founder flagged CBC piece `p_0344f5cd95bd43ba`: summary, sub-headline, "Posted | Last
  Updated" line and an "audio version is AI-generated" note rendered as body paragraphs.
  Diagnosis: all four were in `source_text` (extraction, not the model). Readability kept
  CBC's header block; our 8-words-or-punctuation fragment rule passed it; and the byline /
  site / date the page script already extracted were dropped by `ExtensionInput.swift`.
  Sample: 4 of 8 readability pieces affected, all CBC.
- Founder rejected an LLM cleanup call (it adds wait). Built, deterministic
  (`ActionExt/RetAInPage.src.js`): short text the reader can't see (<80 words,
  `checkVisibility`) is removed before Readability; the fragment rule now runs first; leading
  datelines are dropped; a leading sub-headline, and a summary matching the page's meta
  description, move to a `dek` field (the summary only when a sub-headline or dateline
  confirms the header area, so a description that is just the lede stays in the body).
- Byline, site, date and dek travel app → service (4 new nullable `pieces` columns) → reader
  header under the headline ("Arden McLeod · CBC · Sep 26, 2026"). Never sent to the model.
- Found on the real page: CBC hides its summary at every width (`display: none`), so it is
  now dropped entirely, matching what CBC shows; the dek is the sub-headline only.
- Verified: iOS unit tests 10/10 (new: CBC fixture cut from the real page; lede-stays test;
  reader header + escaping); pytest 32/32; full real CBC page run in the simulator → body
  starts at the story's first paragraph, byline/site/date/dek correct. Service restarted,
  healthz ok, new fields returned. Existing pieces are unchanged (re-share to see the fix).
  Safari UI test not run.
- **Verified on device (same day):** founder re-shared the article → `p_2884d8f2c0ab4814`;
  body starts at the story, no dateline/audio note/summary; byline, site, date and dek
  stored; founder confirmed the header UI. (11.2 s vs 3.5–6.5 s recently — cause not checked.)

### 2026-09-27 — Reader font: New York + Dynamic Type (UX-9, partial)

- Founder asked which reading font the app uses (Georgia, fixed size) and what iOS uses for
  extended reading. Agreed: switch to Apple's New York (`ui-serif`, Georgia fallback) and
  follow the iOS text-size setting via `html { font: -apple-system-body }` (all rems scale;
  `p` 1.06rem → 1rem keeps the default size ~17px). CSS-only, `Shared/UI/PieceHTML.swift`.
- Verified: unit tests 7/7 pass; simulator Safari render of `PieceHTML.page` shows New York,
  scales at XXL (updated live without reload in Safari), and dark mode looks right.
  **Founder confirmed on device (same day):** New York shows, size follows the founder's system setting.

### 2026-09-27 — Notes allowed beside words (D43)

- Founder asked why the NZT-48 piece had substitutions/rephrases but no yellow notes. Log:
  the model wrote one on-topic note (after "Memory Loss", stretch 7) and `sentence_guard`
  deleted it because *grapple* was already in that stretch; stretches 6 and 8 stayed empty.
- Founder ruling (D43): the stretch target is a floor — notes stay where a word already
  is. Guard, prompt and SENTENCE_REQUEST changed; cap of one note per stretch kept; test
  flipped; 30/30 tests pass; service restarted, healthz ok.
- Rerun of the NZT-48 text 4× on the dev account (different 54-word list, ~$0.005): 5 words
  each, 1 note kept (in an empty stretch), 7 notes dropped — 1 for a quote, 1 for a
  QC-rejected word (astute), the rest "needs exactly one marked word". The D43 path (note
  beside a word) was not hit live; only the unit test covers it.
- Open: (1) gap-fill for stretches still empty after the guard; (2) why notes come back
  without exactly one <mark> — inspect raw model output before changing anything.
- Dev account's words replaced with a one-off copy of the founder's 235 (will drift).
- **Raw model output now stored:** `calls.response` (text as returned, before parsing or
  guard) + `calls.prompt_sha` (sha1 of the system prompt, 12 hex) for every call. No
  retention limit yet — decide before other users (with P2).
- **Bug found with it (unfixed, awaiting founder):** the model often `<mark>`s words that
  are NOT on the user's list inside notes (plasticity, overload, cognitive). The guard
  counts one mark and keeps the note; later the unlisted mark is unwrapped, so the reader
  gets a yellow note with no target word — pure added text. Rerun p_205aa1f52b474d2c
  shipped 3 such notes. Also explains many "needs exactly one marked word" drops.
- **Fixed (founder: "a note counts only when it carries a word from the list"):** before
  the guard, marks on unlisted words are unwrapped — their notes drop and their edited
  sentences revert to the author's text (D40 already says a sentence changes only to seat
  a target word; 4 such substitutions shipped in the same piece). Test added.
- Backlog TD-14: Langfuse tracing, around TestFlight.

### 2026-09-26 (night) — Engine switched to Gemma 4 26B (D42)

- Blind quality grading added to the harness (packets graded by Claude Code helper agents on
  the founder's plan, no API cost) plus role separation: writer-only runs, fixed checker, and a
  checker test against graded words. Findings in docs/model-bakeoff.md: Gemma is the better
  writer (21% vs 38% wrong raw; 11 vs 43 inventions), a weak self-checker (catches 55% of misuse;
  gpt-6-luna 91%).
- Founder decision D42: Gemma writes and self-checks via OpenRouter (ZDR hosts, thinking off);
  Flash-Lite is the fallback (TD-12 done). Service restarted; live test piece on Gemma: 3 calls,
  $0.00057, 12.3 s. Service now records OpenRouter's billed cost.
- Open: founder labelling session; grade the Gemma + luna split; privacy policy must name
  OpenRouter (AD-2).

### 2026-09-26 (evening) — Model research + standing eval harness

- Research (7 tracks, notes in `research_notes/`, report in `reports/LLM rewrite engine
  candidates 2026.md`): shortlist of models cheaper per piece than Flash-Lite, incl. Chinese
  open-weight (DeepSeek, Qwen, Xiaomi MiMo, Ant Ling) via Western zero-retention hosts,
  NVIDIA Nemotron, Gemma 4, gpt-6-luna. Founder rule: anything pricier per piece is out.
  claude-haiku-4-5 (fallback) may retire from 2026-10-15 → TD-12.
- Built `src/evals`: frozen golden set (30 pieces: 17 founder reads, 13 licensed; 51 words),
  runner = full production pipeline with the candidate in every role (via new
  `engine.pipeline_args`/`user_item`, so evals and service can't drift), per-call billed
  cost + reasoning tokens (callers take per-model `params`; OpenRouter route with ZDR),
  fixed grader + blind founder labelling page + kappa, leaderboard. 24 tests green.
- First runs: Flash-Lite $0.0042/piece, 4.8 s p50 (two runs agree); gpt-6-luna (reasoning
  none) $0.0027, 10.7 s p50, fewer words (fails validation → retries).
- Open (TD-13): grader choice (proposed gpt-6-sol), founder labels, OpenRouter key, shortlist runs.

### 2026-09-26 — Checks kept, regeneration dropped in sentence mode (D41)

- Founder asked to remove the idiom + fact checks to cut wait and cost. Evidence from the
  service log (19 idiom + 13 fact rejections, all real misuses or inventions, produced with
  the prompt rules in place) argued against; the checks cost ~0.9 s / ~$0.0009 per round.
  The expense was the full regeneration + second check round on 15/26 pieces.
- Built instead: in sentence mode, a rejected word's sentence loses its marks
  (`unmark_sentences` in src/generate.py) and `sentence_guard` restores the source
  sentence. No extra model calls. Rewrite mode unchanged. Test added (pytest 12 green).
- Measured on the 5 G2 fixtures: every piece 1 generate + 1 qc + 1 fact; avg 2.8 s,
  $0.0023. Two pieces had rejections handled by revert (ubiquitous, zeitgeist;
  corroborate — which had altered a Ben Crump quote). Rejected words confirmed absent.
- Visible side effect: coverage on these runs was 0–1 words per piece (2 pieces ended with
  0). That's the D40 coverage problem, not caused by this change, but the revert means no
  second attempt to place a word.

### 2026-09-26 (afternoon) — UX-13: Figma bar shapes, yellow notes

- Read the founder's three Figma nodes via Figma MCP: each bar is a filled "D" (flat left,
  curved right), a different curve per tier; note colour is now yellow #FFCE1F (was orange).
- Built as CSS masks from the exact Figma paths (`PieceHTML.swift`), stretched to bar
  height; widths 10/13/12 px. Dark mode = Figma colours (founder: looks good). Light mode:
  founder asked the assistant to choose — Figma hues darkened for cream: green #28a012 and
  cyan #0097a7 (≥3.2:1 contrast), yellow #d4a200 (2.2:1; darker turns brown). Disclaimer copy in `src/generate.py` updated (no more "dashed/dotted orange").
- Verified: sample page rendered in simulator Safari, light + dark, by eye. pytest 28
  green; service restarted, 200. iOS unit tests 7/7 green (after uninstalling the app
  from the simulator — it had been refusing to launch with "Launchd job spawn failed").
- Seen on render: a one-line bar is a short stub (10×~28 px). Founder to judge.

### 2026-09-26 (closing) — Tap hints, bracket bars, dark palette; handoff

- Margin bars became tap targets (left margin widened to 28px); tapping opens a hint card
  (bar sample + label + one line; founder-approved copy). Bars are now one thick "("
  bracket for every tier per the founder's mockup (colour-only; the hint is the
  colour-blind fallback); dark mode uses #2BFF06 / #00FFFF / #FF5F1F with words on a
  dimmed block. Verified by simulator renders in light and forced-dark; iOS tests green.
- Founder: shape still not the Figma one → Figma remote MCP installed (user scope) and
  authenticated; this session can't load its tools → UX-13 for a fresh session.
- Docs brought current for handoff: NOW block, backlog DEC-1 / UX-1 / UX-11 / UX-13,
  PRD D40 display clause. Commits are local; not pushed.

### 2026-09-26 (late night) — Tier colours; demo piece in the founder's account

- Founder's first real share (CBC wastewater, ~1,000 words, Readability-clean) placed 2
  words: the model attempted 6 across ~8 stretches, the checker rejected 4, the one note
  died with its rejected word. Engine was live (restart confirmed); UI showed no bars
  because only substitutions survived and they had none.
- Founder: highlights must follow the colour scheme and every change gets a bar. Now green
  (dashed) = substituted, blue (solid) = rephrased, orange (dotted) = note; bars merged
  per change and drawn as striped fills (WebKit drew dashed borders as one dash).
- Hand-built demo `p_demo_283d0c28f2` in the founder's account ("[Demo] …", words_used
  empty so it doesn't count as reading) — UI test only, not engine output.
- Open: model under-attempts and misuses words (6 tries / 8 stretches, 4 rejected) →
  candidate for the model evals (TD-13).

### 2026-09-26 (night) — Junk removal (Readability) and margin bars

- Safari extension runs Mozilla Readability 0.6.0 (vendored, Apache-2.0; founder-approved
  dependency) before the model: share bars, nav, footers and bylines leave the body; an
  opening headline becomes the title; short non-sentence fragments are dropped (RetAIn's own
  rule). Byline/site/date come back as separate fields (not yet shown). Text shared from
  other apps still arrives uncleaned.
- Reader: underlines removed. Margin bars per visual line — solid blue = rephrased, dotted
  orange = note; substitution gets no bar (its highlighted word is the change); word
  highlight is one colour. Snapshot of a real piece checked by eye.
- Tests: pytest 28; iOS unit 7 (new: page-script on a cluttered page; bars per tier).
- Still not live: service restart + phone rebuild pending founder.

### 2026-09-26 (evening) — Anchor trial: one word per ~120-word stretch

- Founder: per-paragraph is the wrong anchor (3 words in one paragraph and 0 in the next is
  fine); switched to ~120-word stretches, notes inline anywhere as long as they're marked.
  Checker stays as is, no re-runs; relaxing it is a future founder lever.
- Built: stretches cut in code and named in the request; guard anchors notes to the sentence
  they follow; inline note span (interim tinted italic, margin design pending). pytest 27,
  iOS ReaderPopupTests 3 green.
- Measured 15 pieces: 21/36 stretches, 1.5 words/piece (per-paragraph run: 2.4), 59% notes,
  longest word-free run median 193 words. Details: docs/poc2-transform.md §S1.
- Still not live (service restart + phone rebuild pending founder).

### 2026-09-26 (later) — SUPPLEMENT notes built in one call (D40 amended)

- Founder ruled one model call only (wait time beats a trial ratio). Notes are `<aside>`
  blocks written in the same generation; code checks them for free; fact judge skips them;
  D41 revert drops a note whose word is rejected. Reader: boxed "RetAIn note", tap explains
  it's added context; word tap still shows meaning. Disclaimer rewritten for sentence mode.
- Fixed on the way: `parse_output` dropped `<aside>`; `sentence_guard` collapsed a piece into
  one paragraph whenever the model split/merged paragraphs (likely UX-11's "blob").
- Measured (5 G2 fixtures): 12/24 eligible paragraphs covered, 3/2/7 substitute/rephrase/note,
  1.9–4.6 s, ~$0.0026/piece. Tests: pytest 19, iOS ReaderPopupTests 3, all green.
- Not yet live: service not restarted and the phone app not rebuilt (founder to choose when).

### 2026-09-26 — Density over fidelity: three embedding tiers (D40), step 1 built

- Founder ruled density beats fidelity: the product's value is their words inside what
  they read, and ~2.4/1,000 (≈1 per article) doesn't deliver it. Target is now **every
  paragraph of 25+ words carries a word**; tiers SUBSTITUTE → REPHRASE → SUPPLEMENT (added
  general-knowledge note, visually separate, up to 50% of words as a trial) → **D40**.
- Built step 1: `sentence_guard` tags each edited sentence with its tier (decided by a
  word-level diff: ≤4 words changed = substitute, else rephrase) and stores the original
  (`data-orig`). Reader: rephrase = dashed underline; tapping a sentence reveals the
  original, tapping the word still shows its meaning. Tests: pytest 11 green (4 new in
  tests/test_guard.py); iOS ReaderPopupTests 2 green.
- Next (step 2): permissive REPHRASE prompt, measure paragraph coverage on the 5 G2
  fixtures; build SUPPLEMENT only if coverage falls short.

### 2026-09-25 — Apple Developer enrollment: individual (D39)

- Founder asked whether he needs a company for the paid Apple Developer Program. Apple's
  docs checked: individuals can monetize fully (Paid Apps Agreement, 15% Small Business
  commission). Organization enrollment needs a D-U-N-S number, an email on the company's
  own domain and a website, and the consulting corp has none of these. **Ruled D39:**
  enroll as an individual now; revisit the corp before public launch, together with P2.
- Next: founder enrolls and sends the Team ID; assistant sets `DEVELOPMENT_TEAM` (replacing
  the personal team UKGU6PX43H in project-device.yml), regenerates, verifies signing.

### 2026-09-24 — PoC 1 closed; pivot to on-demand transform (D34)

- Founder returned after ~6 weeks away: never formed the habit during PoC 1; first
  framing was "a feed each user finds interesting is Meta's billion-dollar problem".
  Assistant pushed back on that half (finite rituals like Espresso/Wordle/Dracula Daily
  work without personalization) — founder's sharper reason landed: **those are content
  businesses, and he doesn't want to be in one.** Agreed as the true root cause.
- Data pulled from `generated_pieces`: 7 days, 29/10/6/2/7/3/2 pieces. Criterion 1
  failed; retention mechanism never tested.
- Pivot conversation: "RetAInize" whatever the user is reading, on demand, no scheduler.
  Founder deferred engine mode (substitute vs rewrite) and monetization; asked for UX +
  technical feasibility on iOS. Assistant's read: iOS has no in-place hook for other apps
  (unlike Android); share sheet is the universal entry; Safari action extension with JS
  preprocessing is the strong case; native Reddit/X are fair, Facebook/Kindle poor.
  All unverified against Apple docs — that is spike S2/S3.
- Written this session: docs/poc2-transform.md (spec, hypothesis v2, entry-point table,
  success criteria, spikes S0–S5, backlog epics A–E), PRD §2 v2 hypothesis, §7 outcome
  block, §7b, §8 supersession note, §9 browser-plugin item, D34. CLAUDE.md phase updated.
- **S0 built and smoke-tested** the same session: `/transform` page, `POST /api/transform`
  (JSON or form), `user_text` items, `prompts/transform.md` (fidelity first, keep shape,
  source register wins), `transform_menu` (fewest-servings-first sort, no caps). One
  forum-style test post: 4 words placed, 1 correctly QC-rejected, length and facts
  preserved; test rows deleted afterwards. launchd server restarted; `/transform` answers
  via Tailscale.
- **Shortcut built live with the founder** (five actions: Get Clipboard → Get Contents
  of URL POST JSON → Get Dictionary Value read_url → Text → Open URLs). First run failed
  with "Can't reach your Mac": the POST arrived but the page's fetch never left the
  phone — iOS *Limit IP Address Tracking* routes insecure HTTP through Apple's relay
  and drops it. Turned off per network; second run worked (639 chars → 3 words, 188
  words, `section=shortcut`). Durable alternative noted: HTTPS via `tailscale serve`.
- **Founder ruling (D35):** technical feasibility is the gate; habit count is an
  observation. Founder walked through the final UX (share → sheet over the host app →
  read → swipe down; copy saved to My Reads) and confirmed it. Assistant's caveat on
  record. Backlog rebuilt in docs/poc2-transform.md §8 as Phase 0 gates (G1–G4) →
  Phase 1 rulings (P1–P3) → Phase 2 MVP (M1–M9) → Horizon 3, each with an owner,
  blocker and done-when. Spec §6 success criteria rewritten to the four gates.
- **G1 in the simulator (same evening):** Apple docs verified (JS preprocessing key
  current, iOS 8+); throwaway Xcode project via xcodegen (installed with permission);
  in-app paste path 6.6 s / 37 MB; Safari action extension via a UI test that drives
  Safari's More → Share → RetAInize: page text returned from `<main>`, 41 ms launch at
  21 MB, 4.9 s transform, 55 MB with the rendered sheet, app-group handoff ok. iOS 26
  hides Share inside "More"; `innerText` misses collapsed sections.
- **Founder pasted 5 real pieces** (tech news ×2, Sedaris essay, local news, Reddit
  post) → G2 ran the same evening. Result: fidelity vs density trade-off is stark —
  see NOW block. Engine is now the top risk, ahead of iOS.
- **G4 competitive scan** delivered by a research agent → docs/competitive-scan.md.
- **G3 link-intake legality** delivered by a research agent → docs/link-intake-legality.md.
- **Founder rulings D36 + D37** (relaxed fidelity on Gemini; link intake out). Assistant
  flagged that G2's invention rate was per-embed, not occasional, incl. one fabricated
  attribution; ruling stands with the facts/attributions line as the guardrail.
- **Fact-QC judge + paragraph repair shipped** (founder-approved, Gemini only): flags
  hard inventions per D36, feeds D29 regeneration, repairs or drops residuals instead of
  un-highlighting. Judge-on numbers on the 5 pieces: 5.6 marks/1,000 w, length ×1.06,
  zero invented attributions in the highlighted sentences (vs 8.1/1,000 unguarded).
- **M1 built the same evening** (see NOW block): service package, launchd agent, curl
  end-to-end pass, cost telemetry itemised per call. Funnel pending the admin console.
- **M2 built overnight** (plan approved by founder): `ios/RetAIn/` app shell with both
  extensions; unit + UI tests pass in the simulator against the live service. Two
  simulator gotchas recorded in code: `AsyncLineSequence` drops the blank lines that
  delimit SSE events (parser flushes on the next `event:`), and the simulator does not
  share keychain items with extensions (app-group defaults fallback, simulator only).
- **P1 done:** PRD §8 rewritten to the PoC 2 MVP shape. Founder's pending list: Apple ID
  in Xcode + phone (G1 device checks), P3 thresholds, P2 monetization when usage data
  exists.

### 2026-08-08 — Coherence research sweep (founder-commissioned)

- Founder: feed "feels incredibly random — not useful to anyone this way"; asked
  for creative out-of-the-box research on sources + organization.
- Two parallel research agents ran: (1) corpora sweep — 15 new sources verified
  by fetching license pages (top finds: Public Domain Review CC BY-SA essays,
  NOAA dive logs PD, Wiktionary etymologies — biography of the reader's own
  words, NPS narratives, Wikipedia film plots; ruled out with receipts: Old
  Bailey and Founders Online both CC BY-NC, ESA text no-derivatives) →
  docs/content-sources.md sweep-2 section. (2) coherence patterns — 12 patterns
  with evidence (Dracula Daily 1,600→200k subs serializing a PD novel on its
  in-story dates; Espresso finishability; flagship-item products; recurring-cast
  effects; content-denominated progress).
- Synthesis: **docs/digest-structure-proposal.md** — named-rubric edition (cold
  open, Anniversary spine, Serial with seasons, weekday Rotating Desk,
  Conversation with recurring cast, demoted headline Shelf, designed ending).
  All rulings pending founder; nothing built.

### 2026-08-07 — The reading finding; density-first locked for calendar slots (D33)

- **Founder's core PoC finding after 2 days of reading:** he naturally skips
  content blocks without highlights and reads only highlight neighborhoods.
  N=1 by design (D1) — density isn't a nice-to-have, it's the product. Also
  implies the proprietary channel (engineered density) is the real main course;
  rewrites can't fully get there (foreshadowed in docs/proprietary-generator.md).
- Density-first A/B run at founder's request (same sources he'd read, same
  offered menus, real QC): worst news piece 0.4→2.6 marks/100w; century
  2.1→2.8. Costs measured honestly: ~30% forced-embed attempts under pressure
  (QC absorbed), and 2 invented specifics on news content ("EUR 0.10/kg",
  "Spain leading") — word-QC doesn't police facts. Compare page:
  output/compare-density.html.
- **D33 locked:** density-first prompts for On This Day + century wrappers
  (free restructuring, adjacent common-knowledge context, facts sacred; century
  target 250-400); news/GV stays source-close pending fact-QC; every piece's
  attribution now carries an AI-rewrite disclaimer. Next up for discussion:
  founder's "other things" — and the proprietary generator still gates on
  interest areas + recurring-cast call.

### 2026-08-05 — Density investigated; process failure; founder rulings

- Day-5 OTD came out 3/9 blocks. Diagnosis (solid): the D14→QC→D29→D31 chain
  compounds on death-heavy dates, AND least-served-first menus progressively
  concentrate never-placed words ("the buffet of rejects") — density decays daily.
  `corroborate` failed QC three runs straight; three rolls all produced 4 marks.
- **Process failure:** assistant shipped two product-shaped fixes (grim-event
  selection filter, menu mixing) and churned the day's OTD piece without
  discussion, then tried to commit. Founder stopped it. Both reverted. Lesson
  saved to persistent memory: diagnose freely, decide jointly, THEN code.
- **Founder rulings:** (1) D14's embedding guardrail REMOVED everywhere — words
  may sit in death/tragedy passages; QC judges idiomatic fit only (PRD D14
  amended, D31 consequence note obsolete). (2) Best-of-3 validation retries
  kept. (3) Word list grown 30 → 50 (founder asked for 20 more; professional
  register; also naturally dilutes the leftover-menu problem).
- **D32 (founder, same session):** menus = full active word list, soft-priority
  ordered (due → fewest servings), D27 caps the only hard filter; offered menus
  now logged per piece (skip-rate data); proprietary channel will take inverse
  priority (hard words get engineered premises). Implemented in
  build_digest.menu_for + serve + generate; today's calendar pair rebuilt under
  D32 + new D14.

### 2026-08-03 — D31: On This Day renders only word-bearing blocks

- Founder call: every rendered block should earn its place. Implemented as a
  render-time filter after QC (model still covers all events — no incentive to
  force words; wordless and QC-emptied blocks drop at render). Tested on Aug 3:
  9 generated → 6 rendered, one word each. Flagged + accepted consequence:
  D14 + D31 means tragedy events never appear in this slot.
- Git permissions: assistant blocked (correctly) from self-granting; rules given
  to founder to add via /permissions. Commit batching adopted — milestone/session
  commits instead of per-feature. serve.py + D31 currently uncommitted, pending.
- Mobile access decided: **Tailscale to the Mac** (over Fly.io deploy and a static
  Vercel archive — founder pick; full live experience, free, private). Vercel's
  limitation noted: static hosting can't run the tap-to-rewrite core.
- **Mobile access LIVE (2026-08-04):** Tailscale installed + signed in (needed the
  classic extension-approval reboot); phone URL:
  `http://rays-mac-mini.tailb493b3.ts.net:8484` (fallback `http://100.69.114.50:8484`).
  Server now runs as a launchd agent (`com.retain.server`, auto-start on boot,
  KeepAlive, logs at ~/Library/Logs/retain-server.log). Mac mini never sleeps
  (verified pmset) — it's now the always-on PoC appliance.

### 2026-08-02 (even later) — The real D17 experience: reading server with on-click rewrites

- Founder course-correct: the static 4-piece digest had the algorithm picking his
  reading — D17 explicitly decided the opposite (calendar pair pre-rewritten +
  headline menu; tapping triggers the rewrite in real time). Assistant under-built;
  no PRD change needed, just the correct implementation.
- `src/serve.py` (stdlib, port 8484): edition page (pills + calendar pair inline +
  12 taste-filtered headlines across GV/SE/NASA), `/read` shell with the "working
  the magic" moment, `/api/rewrite` runs the full pipeline (validation, QC, D29
  regen) on click in ~7s and records the read. **Serving semantics improved:
  only clicked pieces count** — words served == words actually read. Background
  pantry refresh when news is >20h stale. Read items show ✓ and stay listed.
- Verified live: click → 6.9s → 5 clean embeds, ledger row written, pills and
  ✓ markers update on return to the edition page.

### 2026-08-02 (later) — Digest builder shipped; Edition 1 built; 14-day run begins

- Founder reprioritized: habit test first, proprietary generator after (design
  captured in docs/proprietary-generator.md so nothing is lost).
- `src/build_digest.py`: one command → today's edition. Refreshes pantry
  (fetch never blocks), schedules words (expanding intervals [1,1,2,4,7,12,20],
  D27 stage caps: new 3/day, mature 1/day), fills slots (calendar pair + tasteful
  GV pick + SE/NASA rotation), assembles a finite edition (D22 "you're caught up")
  with a 6-headline pantry menu for tomorrow (D17 founder-picks). Idempotent per
  day; failed slots degrade gracefully. Serving stats: `generated_pieces.digest_date`
  (NULL = test piece); words_used now records actually-marked words, not the
  model's self-declaration. `generate.py` refactored: `generate_piece()` is a
  library function.
- Founder feature request, shipped same session: word-pill strip at the top of
  every edition — all 30 words as pills, today's served ones highlighted and
  tappable for definitions. Fixing it exposed a rebuild bug: --force after a
  fresh fetch could swap slot picks and orphan same-day ledger rows (phantom
  servings) → rebuilds now keep the original lineup and orphans are cleaned.
- **Edition 1 (2026-08-02): 4 pieces, ~6 min, 18 servings, 9 distinct words,
  0 empty popups.** QC earned its keep in one build: caught words placed in a
  martyr story (D14), killed a wrong `corroborate`; two `candor`s hit the
  last-resort unwrap floor. Watch: if last-resort fires often, D29's regen may
  need a second attempt.

### 2026-08-02 — QC UX fixed (D29); house voice created (D30)

- Founder caught the demote-don't-delete flaw: readers *know their words* — a
  QC-rejected word left unhighlighted in text is out of context and confusingly
  untappable. **D29:** QC failure now regenerates the piece with the word removed
  from the menu and explicitly forbidden; un-highlighting is only the last-resort
  floor. Verified with a forced-failure test (word absent from final piece; the
  regenerated piece gets its own QC pass). MVP note: QC + regen complete behind
  the streaming moment.
- **D30 house voice** in core.md (founder: chameleon rewriting undermines the
  register vehicle; ESL constraint — support, don't compete): one publication,
  slot inflections. A/B on 3 slots at `output/compare-voice.html` — awaiting
  founder ratification of the voice text. Also fixed stale "3 or 4 words" line
  in core.md contradicting D28.
- BC years now normalized in code (`-30 BC` → `30 BC`; prompt-only was flaky).

### 2026-08-01 (night) — Pantry widened: NASA + Stack Exchange live; fact tripwire added

- NASA: pure config addition to `fetch_rss.py` sources + a generic `paragraphs_only`
  content filter (its feeds ship whole-page WordPress markup; prose lives in `<p>` tags).
  Two feeds live (breaking news + science), 15 items in pantry.
- Stack Exchange: new `src/fetch_stackexchange.py` (API, 2 requests/site, anonymous
  quota 300/day) — top-voted evergreen classics + each question's top answer as one
  pantry item. 7 sites from the licensing research, 84 items in. New `prompts/qa.md`
  advice-column wrapper; SE attribution branch (both authors, share-alike note).
- End-to-end verified on both: the classic "automated my job" Workplace piece (advice
  shape lands, counsel faithful to the top answer) and a NASA Starship piece — which
  close-read caught inventing "1.2% scale model" (source says only "scale models").
  QC checks words, not facts → added `invented_numbers` tripwire to validation:
  every digit sequence in a piece must exist in the source, else retry + loud warn.
  news.md also hardened ("if the source gives no figure, give none").
- Density floor observed working live: technical NASA content ran 3 marks/400 words,
  retried, warned. Watch list: number-dense technical pieces may stay below floor.

### 2026-08-01 (later) — Density fixed at the right lever; QC gate shipped (D28; D19 re-amended)

- Founder: density too low — people come to retain words, and some blocks had none.
  A/B found the root cause: the hardcoded "use 3-6" in `generate.py`'s user message
  anchored every piece at ~5 marks; wrapper-prompt density rules did nothing (and once
  misplaced a word into the 1946 pogrom block — D14 violation). The same rule in the
  user message: 5–7/7 eligible blocks filled, zero D14 violations across 6 trials.
- Shipped (D28): strong density instruction in the user message; density floor
  (≥1 mark/~100 words) added to mechanical validation; retry now keeps the better
  of two attempts. Tragedy blocks stay word-free by design — density can't fill them.
- Shipped (D19 ON): per-word QC judge on the production model chain, demote-don't-
  delete (bad marks un-highlighted, text intact), fail-open. Validated on planted
  failures: caught both real ones incl. a D14 placement; passed transitive
  *coalesce* — correctly (MW attests it; assistant's flag was over-strict).
- Live verification: both calendar wrappers pass attempt 1, all embeds clean on
  close-read, no false demotions. Cost adds ~$0.0005/piece.

### 2026-08-01 — Calendar format hardened; validation closes the empty-popup gap

- Prompt work (started evening of 08-01, verified + committed just after midnight):
  onthisday rebuilt as one block per source event (year line, 40-70 words each, full
  coverage mandatory, BC years humanized); century + core mandate HTML-only bodies;
  core adds "only candidate-list words may be marked."
- `generate.py` grew mechanical validation (marks present / HTML / no `**` / all
  source years covered) with one retry, mirroring the descoped QC gate's shape.
- Close-read of the evening's pieces caught a real reader-facing bug: Flash-Lite marked
  `corroborate` when it wasn't on the candidate list → empty tap-to-reveal popup.
  Fixed twice over: unlisted marks now trigger the validation retry, and any that
  survive are unwrapped to plain text (never an empty popup). Kicker date switched
  from UTC to local (pieces after 5pm local were stamped tomorrow's date).
- Verified live: fresh onthisday + century runs both passed validation on attempt 1 —
  all 9 events covered incl. 30 BC, every mark defined, no markdown leakage. Word
  usage clean on close-read (two borderline-but-defensible: "deft sense of urgency,"
  "diplomatic impasse" for a policy dilemma). Not a D19 re-open trigger.

**Open items on founder:** none blocking — word list curation in `data/words.json`
ongoing (30 seed words in; founder knows few of them, ideal for PoC).

---

## Log (newest first)

### 2026-07-31 — QC descoped; first commit; GitHub connected

- Founder descoped the QC gate for PoC (D19 re-amended with revisit triggers) — evidence
  was Haiku-era; Flash-Lite runs 14/16 clean. Assistant close-reads remain the only
  misuse detector; a hard Flash-Lite misuse re-opens the decision.
- PROGRESS.md created (this file) as the standing catch-up log.
- **First git commit** (b9a7ec0, 24 files) after a week untracked; pushed to
  github.com/nurgazik/RetAIn over a fresh personal SSH key (work deploy key untouched),
  wiping a 4-month-old unfilled SpecKit template after inspection confirmed it held
  no product content.

### 2026-07-26 — Model question settled: Flash-Lite wins; density design corrected

- Founder corrected the scheduler mental model: same-day recurrence of a word across
  pieces is *desirable* (dense early exposure), not forbidden → **D27** (due-pool menus,
  stage-based per-word daily caps, word-servings/day as PoC retention metric).
- Prompt tightening A/B (v1 vs v2 calendar pieces): fixed the specific failures, new
  ones appeared — proved prompt-only mitigation insufficient → **D19 amended: QC gate
  mandatory** (~$0.001/piece, runs behind streaming, demote-don't-delete UX).
- Model testing marathon: Kimi K2.5 (4/4 clean words but 115s always-on reasoning —
  rejected), o3-mini effort sweep (low/medium/high dose-response: word discipline scales
  smoothly with deliberation), **Gemini 3.1 Flash-Lite discovered: 3s, $0.0017/piece,
  clean** → 3-article head-to-head vs Haiku across all wrappers → Flash-Lite 10/11
  clean vs Haiku ~9/16 → **D5 flipped: Flash-Lite primary, Haiku fallback**.
  `generate.py` switched and verified live (Dimash piece). Full record:
  docs/model-bakeoff.md. Unit economics now ~$0.40/mo worst-case heavy user.

### 2026-07-25 — Sources un-fragiled; digest experience designed; calendar pair built

- Gemini deep-research sweep (founder-commissioned after rightly rejecting my premature
  single-anchor acceptance) + our license verification → fresh pool 1 → ~6 sources
  (NASA daily PD, SciDev CC BY verified, OWID, GOV.UK, World Bank) + evergreen additions
  (OpenStax, Wikisource, Rijksmuseum CC0, Europeana, Chronicling America). ND/NC traps
  confirmed everywhere in nonprofit journalism. docs/content-sources.md expanded.
- Digest experience settled after UX-pattern research (Espresso/Wordle vs inbox-guilt
  evidence): **D20** fully on-click generation (no pre-gen), **D21** calendar pair
  (On This Day + News From 100 Years Ago), **D22** finite edition + one re-deal,
  **D23** Saved shelf cap 10, **D24** permanent My Reads with status-colored highlights.
  Data model vocabulary agreed (**D25** exposure: offered→seen→opened; **D26** word
  lifecycle learning/retained/archived) → docs/architecture.md.
- Built both calendar fetchers + `generate.py` (production Haiku path then). loc.gov
  bot-walled from sandbox → pivoted century-news to Internet Archive (equivalent, PD).
  First real generated pieces revealed 3 word-quality failures → QC debate began.
- Founder memory noted: prefers meticulous research + joint decisions on fundamentals.

### 2026-07-24 — Pipeline born; world rewrote the source plan; first bake-off

- Built `store.py` (SQLite pantry), `fetch_rss.py`, prompts (core + news wrapper).
  **Discovered VOA dormant (since 2025-03) and Wikinews closed (2026)** → Global Voices
  promoted to news anchor (**D16**); taste filter validated (44/89 GV items excluded).
- First end-to-end piece: Brewarrina fish traps (founder approved quality). Candidate-
  pool browser built. Founder browsing the pool out-picked the algorithm → **D17**
  hybrid layout + streaming "working the magic" (later superseded by D20 full on-click),
  **D18** "the more you read, the more we serve" (no quotas), **D19** original no-QC
  posture (later amended).
- API keys added (.env.local, gitignored). **Blind 4-model bake-off** (Haiku/Sonnet/
  gpt-5-mini/Gemini 3.6-flash) → Haiku won on cost×speed×quality (D5, later updated).

### 2026-07-23 — Feed mechanics designed

- Freshness spectrum (perishable/evergreen/calendar/generated), pantry-and-chef split,
  served ledger, per-slot fallback ladders, **D14** taste guardrail (no vocabulary
  embedding in tragedy), **D15** pipeline architecture → PRD §4 + docs/architecture.md.

### 2026-07-22 — Project founded

- PRD created: problem, hypothesis (spaced repetition hidden in engaging reading),
  three horizons (PoC/MVP/Future), decisions log started (D1–D13 over the day).
- Content-source licensing research: CC-license taxonomy, The Conversation ruled out
  (ND), VOA/Wikinews/GV identified (world later revised this), Stack Exchange/Gutenberg/
  PLOS/US-gov verified usable → docs/content-sources.md.
- 30 seed words created (data/words.json); control group descoped from PoC; git repo
  initialized (still uncommitted).
