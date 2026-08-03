# RetAIn — Progress Log

Catch-up file for founder and assistant alike. **Convention: update the "Now / Next"
block and append a dated entry at the end of every working session.** Newest entries
first. Decisions live in PRD.md's log (D1–D30); this file is the narrative timeline.

---

## NOW (as of 2026-08-01 session end)

**Phase:** PoC build — pipeline works end to end (fetch → pantry → generate → render),
model selection is settled, digest experience is fully designed, **code is on GitHub**
(github.com/nurgazik/RetAIn, private). Calendar-piece output format is hardened,
word density is fixed with a mechanical floor (D28), the QC gate is live (D19), and
the pantry now has **five sources**: Global Voices, the calendar pair, NASA, and
Stack Exchange (7 sites, advice-column wrapper). Validation also tripwires invented
numbers. QC rejections regenerate rather than un-highlight (D29); the house voice
is live in core.md (D30, ratified by founder 2026-08-02). Not yet started: the
14-day daily reading run.

**Next up (in order):**
1. **Proprietary piece generator** (PoC Source 4 — PRD §7): fully GENERATED content, no
   source article — dialogues, flash fiction, workplace vignettes built around due words.
   Needs its own wrapper prompt. Why it matters: it's the *register vehicle* (words shown
   in the professional register the founder wants to speak in), the digest's never-empty
   floor, and MVP's narrative slot. DO NOT FORGET — founder flagged this explicitly
   before the machine switch.
2. Digest assembly + word scheduler (expanding intervals, D27 frequency caps)
3. Start the 14-day PoC reading run (checklist in PRD §7)

**Machine setup note:** work laptop pushes via SSH alias `github.com-retain`
(dedicated personal key `~/.ssh/id_ed25519_retain` — revoke from GitHub settings when
vacation coding ends). Home Mac: clone normally with personal credentials; recreate
`.env.local` (4 API keys — gitignored, never on GitHub) and `data/retain.db` refills
itself via the fetchers.

*(QC gate re-shipped 2026-08-01 alongside the density push — see D19/D28. The 07-31
descoping lasted one day; density strain was the predicted trigger.)*

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
