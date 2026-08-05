# RetAIn — Product Requirements Document

**Owner:** Nurgazy Budaichiev
**Status:** Pre-PoC (feed validation phase)
**Last updated:** 2026-07-22

---

## 1. Problem statement

Advanced ESL speakers regularly encounter interesting new words while reading (books, articles, everyday life), look them up, appreciate them — and then lose them. Days later the word feels vaguely familiar but its meaning is gone. Existing tools fail this segment:

- **Duolingo and similar** target novice learners.
- **Flashcard apps (Anki-style)** are effective in theory but boring in practice, and they teach word–definition pairs stripped of collocations, register, and connotation — the things an advanced speaker actually needs.

The founding user is the owner: advanced English speaker (Russian mother tongue), living in Canada, wants his English eloquence to match his Russian. Captures ~10 new words/week from reading.

## 2. Core hypothesis

> Repeated exposure to a target word, in varied and genuinely interesting contexts, on a daily basis — with a light retrieval moment at each encounter — produces durable retention where flashcards fail.

Learning-science backing: incidental vocabulary acquisition through reading requires ~8–12 exposures in varied contexts (Nation, Krashen). Tap-to-reveal highlighting adds retrieval practice. The app is effectively **spaced repetition hidden inside content people want to read**.

Known limitation (accepted): passive exposure builds *receptive* knowledge (instant recognition). *Productive* use (deploying words in conversation) needs production practice — deferred to Future state.

## 3. Product shape

1. User captures a word (share sheet, manual entry).
2. RetAIn builds a word card (definition + register, collocations, nuance).
3. Each day, RetAIn serves a **finite daily digest** — X number of short content pieces (news, curiosity, narrative) with due words embedded and highlighted.
4. Highlighted word = retrieval moment: user tries to recall, taps to reveal definition + stats. A tap means "didn't remember" and feeds the scheduler.
5. Words graduate to "retained" when the user manually marks them as retained (MVP). Automatically "sensing" retention is a future-state idea.

**Digest, not feed.** Deliberately finite and refreshed daily — a 5–10 minute ritual (like Wordle/a morning newsletter), not an infinite scroll competing with Reddit. This also enables overnight batch pre-generation (cheaper, zero latency, QC'd before serving).

## 4. Feed mechanics (how the digest gets built)

### Sources sit on a freshness spectrum

| Type | Examples | Relationship with time | Can it have an "empty day"? |
|------|----------|------------------------|------------------------------|
| **Perishable** | VOA, Wikinews, Global Voices | New items daily; value decays in days. Digest promise is **"recent," not "breaking"** — yesterday's good story is fine this morning | Yes — the only type that can |
| **Evergreen pool** | Stack Exchange, Gutenberg classics, most of Wikipedia | Value never decays; what matters is **"new to you,"** not new to the world | Never (pool is bottomless for one reader) |
| **Calendar** | "On this day", Today in History | Self-refreshing by date | Never |
| **Generated** | Proprietary dialogues/fiction | Infinite by construction — the digest's safety net | Never |

Only one of the four slot types depends on the world producing new content daily. That resilience is a feature of the portfolio design, not luck.

### Pantry and chef: fetching is not choosing

- **Fetchers = procurement.** Each source's fetcher keeps a **candidate pool** stocked (pulls feeds on a schedule, adds anything new). It does *not* decide what gets served.
- **Digest assembly = the chef.** A separate step fills each slot: "best unserved candidate in this pool for this user." Selection criteria: never served before, interest match, **rewrite affordance** (piece needs narrative/analytic texture for advanced words to land naturally — a dry casualty count gives *affable* nowhere to live), and the taste guardrail below.
- **Taste guardrail (product decision):** never embed vocabulary practice into tragedy. News slot leans science/tech/culture/economy/human-interest; explicit "skip grim hard news" filter in selection.

### Duplicates

- **Never re-offer an *opened* item; decay, don't ban, the merely-seen:** the exposure ledger tracks offered → seen → opened per user. Opened items never reappear in editions (they live in My Reads). Seen-but-not-tapped items take a ranking penalty and retire after 2–3 ignored impressions (the bookmark gives users an explicit "interested, later," licensing us to read repeated silence as disinterest). Offered-but-never-seen items carry zero signal and remain fully eligible.
- **Same story, different wrapper (news):** title-similarity check in PoC; semantic (embedding) dedup at product scale.
- **Follow-ups on developing stories are not duplicates** — story continuity is a potential future feature (Horizon 3 flavor), to be done deliberately, not prevented accidentally.

### Empty days: fallback ladder per slot

Each slot has a policy, not a prayer. News slot example: today's best unserved Global Voices piece → yesterday's unserved → swap the slot for an extra evergreen/generated piece. **The digest can never fail to exist** — its floor is generated content that needs no external world. Per D9, the mix flexing day to day is fine.

### The digest experience (agreed 2026-07-25; supersedes the layout sketch below where they differ)

Foundational statement: **nobody needs to "keep up with" this feed — missing a day has
zero cost to the learning mechanism.** The scheduler simply waits. Any design that
manufactures a backlog manufactures pure guilt (see the inbox-model evidence in the
2026-07-25 UX research). Everything below follows from that.

- **Today's edition:** the calendar pair (D21: On This Day + News From 100 Years Ago)
  + ~13 curated picks from the pantry. Finite, ends with "you're caught up."
  All pieces generate on tap (D20) with streamed rendering.
- **One bounded re-deal:** "show me another batch" deals ~10 more, then a true stop —
  the kitchen closes. Never infinite. Batch-two taps are high-value interest signal
  (personalization question, still parked).
- **Silent rollover:** unpicked/unread headlines return to the pool — no unread counts,
  no "yesterday (12)," no decay UI. Reappearance in a future edition is familiarity,
  not backlog. Nothing is discarded at pick time: picking is a read operation; unpicked
  items stay in the pantry, compete in future editions, and (at scale) serve other
  users. Fresh items age out of fresh-slot *eligibility* (~1 week), not out of storage.
- **Saved shelf (bookmarks): capped at 10, no time expiry.** A bookmark flags a pantry
  item we already fully own (full text captured at ingest — no dependence on the source
  still being up). Saved items resurface into editions; a full shelf forces a one-tap
  trade to save more. The cap, not a clock, prevents the Pocket graveyard.
- **My Reads: every generated piece is permanent.** It was written for this user with
  their words — it's a personal artifact. Highlights render from the word's *current*
  status (learning = yellow, retained = green), so old pieces recolor retroactively as
  words graduate: the bookshelf doubles as a visible progress record.

### Digest layout: hybrid (D17)

- **Top: 1–2 pre-generated pieces** — the proprietary and calendar/anchor slots. Instantly readable on open, generated overnight (timezone-aware, D13), can get free QC. This is where the chef still picks.
- **Below: the headline list** — real titles from the taste-filtered candidate pool, essentially free to show. The user is the chef here: tap a headline → the rewrite **streams in live** with a "working the magic" moment. First paragraph in ~1–2 seconds; generation outruns reading speed.
- **Every generated piece carries the currently most-due words (D18).** Reading volume is the user's choice; word priority is the scheduler's job. No quotas.
- **Taps are logged from day one.** Whether/how they drive personalization of list ordering is deliberately undecided (open question) — but the data costs nothing to keep.

## 5. Key decisions log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Validate the feed **before** building any app | Feed quality is the riskiest assumption; everything else is known-buildable |
| D2 | Rewrite **real content** from legally-safe sources (public domain / CC BY), plus proprietary LLM-original pieces | Authenticity + freshness; title-only "seeded generation" rejected (clickbait titles ≠ article content). See docs/content-sources.md |
| D3 | The Conversation is **out** (CC BY-ND — no derivatives); Guardian API unverified, treat as out | Licensing research 2026-07-22 |
| D4 | ~~Pre-generate the whole digest overnight, not rewrite-on-click~~ **Superseded by D17** (2026-07-24) | Original latency objection assumed non-streamed generation; founder's review of the real candidate pool showed selection (not generation cost) is the binding constraint |
| D5 | Rewrite model (**updated 2026-07-26**): **gemini-3.1-flash-lite primary, claude-haiku-4-5 as named fallback rung**. 7 models/9 configurations tested (blind bake-off 07-24; Kimi + o3-mini effort sweep; 3-article head-to-head 07-26) | Head-to-head across all three wrappers: Flash-Lite 10/11 clean usages vs Haiku ~9/16 with ~5 misuses; 3.0s vs 10.5s; $0.0017 vs $0.0083/piece (5×). Its native menu discipline (skips words that don't fit — used the stress-word *candor* perfectly once, skipped it twice) is the behavior prompting never reliably got from Haiku. QC gate (D19) still required — 91% clean ≠ 100%. Fallback exists for provider outage/deprecation/regression; pipeline is provider-agnostic. Cross-model insight retained: word discipline scales with deliberation; the gate remains the cheap place to buy it. Full record: docs/model-bakeoff.md |
| D6 | Prompt architecture: **shared core + per-source wrapper** | News needs fact preservation; Q&A needs advice-column transformation; classics need compression + register modernization |
| D7 | Tap-to-reveal is the **implicit scheduling signal** for exposure intervals | No manual "did you know it?" friction; tap = reset interval, no-tap streak = advance. Graduation itself stays manual (see D12) |
| D8 | MVP capture is **word-only** (share sheet or typed) | Sentence-context capture deferred (scope creep) |
| D9 | Word count per digest is **flexible** (~8–15) | LLM uses only words that fit naturally — the main defense against awkward collocations |
| D10 | Freemium: free tier gets a reduced digest, paid gets full experience | Covers generation costs; monetization path |
| D11 | Digest size (pieces/day, read time) is **an open assumption the PoC must answer** — not fixed at 3–5 | Stated-as-fact numbers were a guess; PoC varies piece count across days and logs read time / appetite |
| D12 | Graduation to "retained" is **manual (user-driven) in MVP** | Keep the user in control; automatic retention-sensing (e.g., from no-tap streaks) is Horizon 3 |
| D13 | Overnight generation is **timezone-aware from MVP day one** | "Overnight" means the user's local night — digest ready by their local morning. Batch jobs bucketed per timezone; NA launch first, EU/other English-speaking regions acceptable if it adds no real scope |
| D14 | ~~Taste guardrail: no vocabulary embedding in tragedy/grim hard news~~ **Embedding guardrail REMOVED 2026-08-05 (founder): words may sit in any passage, including deaths/tragedy — QC judges idiomatic fit only.** Selection still requires **rewrite affordance**, and the GV feed's grim-category skip list (which *articles* get picked) stays | Original rationale (highlighted words in a disaster story would be ghoulish) was overruled by lived PoC experience: the placement rule chained with D29/D31 to strip words and hide blocks on death-heavy days (08-05: 9 events generated → 3 rendered), and the founder judged the ghoulishness concern overweighted — a highlight in a passage about Marilyn Monroe's death is a reading aid, not an offense |
| D15 | **Pantry/chef architecture:** fetchers stock candidate pools; a separate assembly step selects per slot against a permanent served ledger, with per-slot fallback ladders; daily builds are idempotent | Decouples "world produced content" from "digest exists"; digest can never fail (generated floor). See §4 + docs/architecture.md |
| D16 | News anchor is **Global Voices**, not VOA | Verified 2026-07-24 while building the fetcher: VOA dormant since 2025-03 (USAGM shutdown; survives as frozen public-domain archive) and Wikinews closed by Wikimedia in 2026. GV is alive, daily, CC BY, full text in feed, category tags support the D14 taste filter (which it needs — its main feed skews grim) |
| D17 | **Hybrid digest layout:** 1–2 pre-generated pieces on top (proprietary + calendar/anchor slots; instantly readable on open) + a taste-filtered **headline list** below; tapping a headline **streams** its rewrite on demand, with a visible "working the magic — rewriting this just for you" moment | Founder browsing the real pool out-picked the algorithmic chef instantly: selection is the hard problem, and user choice solves it without ML. Streaming kills the latency objection (first paragraph in ~1–2s, generates faster than reading). Supersedes D4 |
| D18 | **Exposure philosophy: "the more you read, the more words we serve."** No daily word quota, no exact science. The scheduler's only job is ensuring every generated piece (pre-gen or tapped) carries the currently most-due words | User controls reading volume; app controls word priority. Quota thinking leads to homework-shaped design — the Duolingo energy we're avoiding. Extends D9 |
| D19 | **Re-amended 2026-08-01 (founder): QC gate ON — shipped in `generate.py`** alongside the density push (D28). Per-word native-writer check via the production model chain (~$0.0005/piece), judging both idiomatic fit and D14 placement; **demote-don't-delete** (failed words are silently un-highlighted, text intact); judge errors fail open. Judge validated against planted failures: caught 2/2 real ones (a word embedded in the 1946 pogrom block; "impasse of opinion"), and correctly passed transitive *coalesce* (Merriam-Webster attests the transitive sense — the assistant's close-read flag was over-strict, not a judge miss) | History: original posture was no-QC; 2026-07-26 evidence (Haiku-era: 1–3 misuses/piece, learner can't self-QC, prompt tightening insufficient) flipped it to gate-on; 2026-07-31 descoped because the evidence was model-specific (Flash-Lite ran 14/16 clean at low density); 2026-08-01 the density push revived the quality-strain risk the dose-response insight predicted — borderline collocations appeared in denser close-reads, and the gate is the cheap place to buy discipline, exactly as D5 anticipated |
| D20 | **MVP is fully on-click rewrite** — no pre-generated pieces; amends D17's hybrid | Bake-off measured 10.8s full-piece latency on Haiku un-streamed; with streaming, first paragraph lands in ~1–2s, which the founder judges acceptable everywhere. Simplifies MVP (no batch orchestration, D13 timezone batching deferred with it). The "working the magic" moment becomes universal |
| D21 | **Calendar pair anchors the day:** "On This Day" (Wikipedia) + "News From 100 Years Ago" (Chronicling America) are the two date-bound daily slots | Both are self-refreshing by calendar (never an empty day), public-domain/CC, and give the digest its daily identity without depending on the news cycle |
| D22 | **Edition model:** finite Today (calendar pair + ~13 picks), one bounded re-deal, "you're caught up" ending; silent rollover with no unread counts | UX research 2026-07-25: finite editions (Espresso) and daily rituals (Wordle) sustain engagement; inbox/unread models create "phantom obligation" guilt. See §4 digest experience |
| D23 | **Saved shelf capped at 10, no time expiry**; bookmarks flag pantry items we fully own (text captured at ingest) and resurface into editions | Cap prevents the read-later graveyard (Pocket evidence) while honoring "save now, read weeks later"; ingest-time capture means zero dependence on source availability at read time |
| D24 | **My Reads is permanent**, with word highlights colored by current word status (learning/retained), recoloring retroactively | Generated pieces are paid-for personal artifacts; status-driven rendering turns the reading history into a visible progress record for free |
| D25 | **Exposure semantics:** offered → seen (viewport impression) → opened; seen-not-tapped decays via ranking penalty, retiring after 2–3 ignored impressions; offered-never-seen = zero signal | One impression is weak evidence; repeated silence is real evidence — especially now that bookmarks exist as the explicit "interested, later" channel. Impression log doubles as future personalization raw material |
| D26 | **Word lifecycle: learning \| retained \| archived — all transitions reversible** (retained→learning reactivation re-enters the scheduler with dense exposure; archived is a soft delete so My Reads keeps rendering) | "I thought I had it, I didn't" is a core honest moment of the product; hard deletes would orphan history. Scheduler stats are fields on the word, never statuses |
| D27 | **Word density via due-pool menus + stage-based frequency caps.** Every generation receives the full currently-eligible due pool (often 10+ words) as a menu with no target count; the model embeds only natural fits; the QC gate (D19) verifies. **Same-day recurrence of a word across pieces is desirable, not forbidden** — per-word daily caps decay with maturity (new ≈ 2–3/day, consolidating ≈ 1/day, mature = expanding multi-day intervals). Retention throughput is measured as **word-servings/day**, a first-class PoC metric alongside D11 | Founder's correction 2026-07-26: the scheduler must not partition words across pieces — a young word appearing in two different contexts the same day is exactly the dense early exposure the product promises. Density and quality stop trading off once the gate exists |
| D28 | **Density floor shipped (2026-08-01): the density lever is the generation *user message*, not the wrapper prompt.** The request now demands one candidate word in every event block / paragraph where one sits naturally (D14 passages explicitly excluded), replacing the hardcoded "use 3-6" cap; mechanical validation adds a density floor (≥1 mark per ~100 words) to the single retry, which now keeps the better of the two attempts | Founder: readers come to retain words, not just read — word-free blocks defeat the point. Evidence (08-01, 3 trials/variant on the same item): density rule in the wrapper alone → no gain plus one D14 violation; the same rule in the user message → 5–7 of 7 eligible blocks filled, zero D14 violations across 6 trials. The "use 3-6" line had been anchoring output at ~5 marks regardless of wrapper text. Residual variance is why the mechanical floor + retry exists; QC (D19) guards the quality edge |
| D29 | **A QC-rejected word must not appear in the piece at all (2026-08-02).** On QC failure the pipeline regenerates with the failed word removed from the menu and explicitly forbidden; un-highlighting survives only as the last-resort floor (regeneration also failed validation, or the word snuck back). MVP corollary: QC + any regeneration complete behind the streaming "working the magic" moment — nothing QC-touched ever reaches the screen | Founder caught the flaw in demote-don't-delete: the reader *knows their words* — a rejected word left in text unhighlighted is out of context AND confusingly untappable, and unhighlighted misuse still teaches wrong usage. Absence is the menu model's normal, unremarkable state (most due words don't appear in any given piece). Organic unmarked occurrences of a user's word in other texts remain fine |
| D30 | **House voice (2026-08-02): one publication, not a costume change.** Defined once in prompts/core.md — a sharp, warmly curious, well-read colleague; precise and concrete; lightly witty, never corporate/academic/breathless. **ESL support constraint:** never simplify ideas or register, but keep prose frictionless — moderate sentence architecture, no decorative rare vocabulary competing with the target words ("the target words are the stretch; the surrounding prose is the support"). Wrapper register notes are inflections of this voice, never replacements. Voice text v1 **ratified by founder 2026-08-02** after side-by-side review (output/compare-voice.html) | Founder: pure chameleon rewriting (matching each source's style) undermines the product — RetAIn is the register vehicle, and readers should marinate in the register they want to speak; but hard-to-read prose serves no one either. A/B on 3 slots (same items, same word menus) shows the coherence gain with each slot's charm retained |

| D31 | **On This Day renders only event blocks that carry at least one surviving highlight (2026-08-03, founder).** Implemented as a render-time filter AFTER generation, validation, and QC — the model still covers every source event (keeping full coverage removes any incentive to force words into events it wants to keep), then wordless blocks are dropped from the rendered piece | Founder: every rendered block should earn its place in a vocabulary product. Typical effect: ~9 generated → 6-7 rendered, each with exactly one word. ~~Accepted consequence: combined with D14, tragedy events never appear in this slot~~ (obsolete since D14's embedding guardrail was removed 2026-08-05 — tragedy blocks can now carry words and render) |

## 6. Risks & open questions

- **Engagement risk (top risk):** will the user open it daily after the novelty fades? PoC measures this directly on the founder.
- **Rewrite naturalness:** forced/awkward word usage teaches *wrong* usage — worse than nothing for advanced learners. Mitigated by D6/D9 in-prompt rules; per D19 occasional imperfection on on-click pieces is an accepted risk (watch it during PoC reviews).
- **Personalization: deliberately undecided.** The headline list reduces the need (user choice ≈ personalization); tap logging starts day one so no data is lost while the founder noodles on it. Revisit before MVP build.
- **Receptive vs productive gap:** digest alone may not produce conversational use. Production features are the future-state answer.
- **Licensing at scale:** Stack Exchange is CC BY-SA (derivatives must be share-alike — acceptable wrinkle, but remember it); VOA pages mix in copyrighted AFP/AP/Reuters wire content that must be filtered out.
- **Single-anchor fragility — RESOLVED 2026-07-25:** external research sweep + our verification took the live fresh-source pool from 1 to ~6: Global Voices, NASA (daily, PD), SciDev.Net (CC BY 2.0 verified, ~2–4/wk), Our World in Data (CC BY), GOV.UK (OGL, selective), World Bank (CC BY IGO). Evergreen pool also expanded (OpenStax, Wikisource, Rijksmuseum, Europeana, Chronicling America). Full inventory: docs/content-sources.md.
- **Competitive scan not yet done** (Anki, Vocabulary.com, WordUp, Membean, LLM-era entrants). Do before investing past PoC.

---

## 7. Horizon 1 — PoC (now)

**Goal:** prove (a) the digest is genuinely enjoyable to read daily, (b) digest words are retained better than captured-but-not-served words, and (c) determine the right digest size — pieces per day and minutes to read (D11). No app — a script producing a daily HTML digest, read for two weeks.

**Approach:** build the feed **item by item** — one source at a time, founder reviews content choice + rewrite quality, prompts tuned per source before adding the next.

### Scope

- Word list in `data/words.json` — seeded 2026-07-22 with 30 generated words (10 verbs / 10 nouns / 10 adjectives); founder curates and replaces with his real captured words over time. Plus informal interest topics.
- No control group in the PoC (descoped 2026-07-22) — retention is assessed by day-14 self-quiz on served words against the founder's own "look it up once, lose it" baseline. A proper control-group experiment can return post-PoC if rigor is needed.
- Fetchers (in build order):
  1. **VOA** — daily news anchor (public domain; filter to VOA-original pieces, exclude wire content)
  2. **Stack Exchange** (Workplace, History, etc.) — Q&A rewritten as advice-column/curiosity pieces
  3. **Project Gutenberg** — classic short story retold in modern register (~500 words)
  4. **Proprietary LLM piece** — dialogue / flash fiction / workplace vignette (no source needed)
- Rewrite pipeline: shared core prompt (due words + "only where idiomatic" + `<mark>` markup + advanced reading level) + per-source wrapper + QC pass (words present? natural? facts preserved?) with regeneration on failure.
- Simple expanding-interval scheduler picking due words per day (dense early exposure for new words).
- Output: daily HTML digest with highlighted words + hover/tap definitions. Delivery: local file or email — whatever is easiest to read with morning coffee.

### Success criteria (day 14)

1. Founder read the digest willingly ≥10 of 14 days.
2. Self-quiz: strong recall of served words (founder's judgment vs his usual "look it up once, lose it" baseline).
3. Rewrites consistently pass the founder's "would I read this on Reddit?" bar; no awkward word usage surviving QC.

**Go/no-go:** all three → proceed to MVP. Feed quality fails → iterate sources/prompts. Retention fails → rethink mechanism (more retrieval? production prompts?) before building anything.

### PoC checklist

- [x] Seed word list created (`data/words.json`, 30 words, 2026-07-22); founder curates it ongoing
- [ ] Founder provides 3–4 interest topics
- [ ] Word store + scheduler (expanding intervals, dense-new-word logic)
- [ ] Core rewrite prompt + QC pass
- [ ] Source 1: VOA fetcher + news wrapper → review → iterate
- [ ] Source 2: Stack Exchange fetcher + Q&A wrapper → review → iterate
- [ ] Source 3: Gutenberg retold classic → review → iterate
- [ ] Source 4: proprietary piece generator → review → iterate
- [ ] Daily digest assembly + HTML render (highlight + tap/hover reveal)
- [ ] Run 14 days; vary piece count across days (e.g., 2/3/4/5); log daily "did I read it / did I enjoy it / how long did it take / did it feel too short or too long"
- [ ] Day-14 self-quiz on served words → go/no-go decision

---

## 8. Horizon 2 — MVP (iOS app)

Built only if PoC passes. Scope:

**Capture**
- In-app manual word entry
- iOS Share Sheet extension (select word anywhere → share → RetAIn)
- Word card built at capture time: dictionary API (Free Dictionary / Merriam-Webster free tier) for canonical definition + one cheap LLM call for enrichment (register notes, collocations, near-synonym nuance, 2–3 examples) — the "better than Kindle lookup" card

**Digest**
- **Hybrid layout (D17):** 1–2 pre-generated top pieces (proprietary + calendar/anchor; overnight batch for recently-active users, **timezone-aware** per D13) + taste-filtered headline list; tap → streamed on-demand rewrite with the "working the magic" moment
- Top-piece count and overall sizing informed by PoC findings (D11)
- Every generated piece embeds the currently most-due words (D18); tap events logged from day one
- Generated titles for heavily-transformed pieces, with "adapted from X" attribution per license
- Interest profile: lightweight onboarding topic picker for day-one list ordering (may shrink or die if tap history proves sufficient — personalization decision parked)

**Learning loop**
- Word highlighting + tap-to-reveal (definition, times shown, date added)
- Expanding-interval scheduling driven by tap/no-tap signals; graduation to "retained" is **manual only** in MVP (D12)
- Streaks / daily goal — light gamification of the ritual

**Business**
- Freemium: free = reduced digest (fewer items/words); paid = full experience
- Unit economics (measured, head-to-head 2026-07-26): ~$0.0017/piece on gemini-3.1-flash-lite (+$0.001 QC gate) → worst-case daily user (5 pieces × 30 days) ≈ **$0.40/month**, typical engaged user ≈ $0.15/month; generation is >90% of marginal cost. Even on the Haiku fallback (~$0.008/piece) the worst case stays ≈ $1.40/month → 90%+ gross margin at $5–8 subscription either way

---

## 9. Horizon 3 — Future state (backlog — do not lose these)

- **Auto-graduation ("sensing" retention):** suggest or apply "retained" status automatically from sustained no-tap exposure streaks (and later, quiz/cloze performance) instead of relying on the user to remember to mark words.
- **Cloze mode:** highlighted blank instead of the word; user types it or picks from a multi-choice of their own words. Strongest form of retrieval practice; natural difficulty ramp after tap-to-reveal.
- **Micro-production prompts:** one per digest — "reply to this post in one sentence using *perfunctory*." The bridge from recognition to conversational use.
- **AI conversation partner:** practice using retained words in dialogue; the full answer to the productive-use gap.
- **Sentence-context capture:** share a whole sentence; LLM extracts the target word and stores the original context (shown later on the word card — encoding-specificity boost).
- **Kindle integration:** Vocabulary Builder import or highlight sync.
- **Siri / App Intents:** "Hey Siri, add *X* to RetAIn" for physical-book and conversation captures.
- **In-digest lookup & capture:** tap any unknown word in a digest piece to look it up and add it to the list (Kindle-style reading loop inside the app).
- **"Read more" long tail:** optional extra content beyond the daily digest, lazily generated on demand (this is where rewrite-on-click belongs).
- **Personalized fiction serials:** multi-day proprietary stories in the user's interest areas — retention hook + word vehicle.
- **Story continuity:** deliberate follow-ups on developing news stories the user already read ("here's what happened next") — engagement hook; distinct from accidental duplication (see §4).
