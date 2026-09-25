# RetAIn — Progress Log

Catch-up file for founder and assistant alike. **Convention: update the "Now / Next"
block and append a dated entry at the end of every working session.** Newest entries
first. Decisions live in PRD.md's log (D1–D34); this file is the narrative timeline.

---

## NOW (as of 2026-09-24 session end)

**Phase:** **PoC 2 — on-demand transform (D34).** PoC 1 (the daily digest) is CLOSED:
it ran 7 of 14 days (08-02 → 08-08), usage decayed 29→2 pieces/day, criterion 1 failed.
Founder's diagnosis: a daily digest is a content business he doesn't want to be in.
New shape: the user captures words as before, reads wherever they already read, and on
demand runs the piece in front of them through RetAIn to read it with their words placed.
No scheduler, no digest. Spec + spikes + backlog: **docs/poc2-transform.md**.

**Digest server status:** `src/serve.py` still runs (launchd agent, Tailscale) and becomes
the host for Spike S0's `/transform` route. Fetchers, calendar slots and editions are
retired but not deleted.

**Backlog (docs/poc2-transform.md §8) — Phase 0 gates, then Phase 1 rulings, then MVP.**
Founder ruling D35: technical feasibility is the PoC 2 gate; the 14-day invocation
count keeps running as an observation only.

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
3. **M1 transform service — PROPOSAL WRITTEN, awaiting founder yes** (docs/architecture.md,
   bottom section): FastAPI on the Mac mini via Tailscale Funnel first (free, HTTPS), Fly.io
   later; SQLite with users/words/pieces/events/calls; Sign in with Apple; SSE phases;
   daily transform cap. Needs: ok on FastAPI dependency, hosting choice A/B.
4. **Phase 2 MVP build** M1 transform service → M2 app shell → M3 share-extension
   sheet → M4 Safari → M5 capture → M6 clipboard → M8 monetization → M9 TestFlight.
5. Parked (Horizon 3): proprietary generator, Safari web extension in-place, screenshot
   OCR, Android, link intake (D37).

**Machine setup note:** work laptop pushes via SSH alias `github.com-retain`
(dedicated personal key `~/.ssh/id_ed25519_retain` — revoke from GitHub settings when
vacation coding ends). Home Mac: clone normally with personal credentials; recreate
`.env.local` (4 API keys — gitignored, never on GitHub) and `data/retain.db` refills
itself via the fetchers.

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
