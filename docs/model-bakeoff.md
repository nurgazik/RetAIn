# Model evals (standing harness, since 2026-09-26)

One-off bake-offs are replaced by `src/evals` (see its `__main__.py` for commands). Every
model runs the **full production pipeline** (sentence mode: rewrite + idiom judge + fact judge,
candidate model in every role, no fallback) on a **frozen golden set**
(`data/evals/golden/`: 17 of the founder's reads — private, gitignored — plus 13 licensed
texts; the founder's 51 words). Results land in `data/evals.db`; `src/evals report` prints
the leaderboard. Research behind the candidate list: `reports/LLM rewrite engine candidates 2026.md`.

New model: `src/evals add <openrouter-slug>` (or a line in `data/evals/models.json`) →
`run <name>` → `grade <run>` → `report`.

**Runs of 2026-09-26, dataset 3ad00d7222, engine 99d1911f2c (D40 anchor trial, sentence mode)** —
cost/speed/density only; grading pending. (Earlier runs 6–20 are void: the engine changed
between the baseline and the challengers, which is why runs now carry an engine fingerprint.)
All 11 ran in parallel; OpenRouter latency includes routing and rate-limit retries.

| Model | $/piece | vs today | p50 / p90 s | Marks/1k words | Coverage | Note |
|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite (today) | $0.00444 | — | 4.8 / 11.5 | 3.5 | 50% | |
| gemma-4-26b-a4b-it | $0.00095 | −79% | 4.6 / 8.4 | 3.9 | 56% | only challenger matching today on speed and density |
| deepseek-v4.1-flash | $0.00124 | −72% | 17.7 / 42.8 | 2.7 | 45% | slow |
| glm-5.3-flash (thinking on) | $0.00404 | −9% | 103 / 192 | 4.4 | 59% | densest, far too slow |
| mimo-v2.6-flash | $0.00155 | −65% | 51.6 / 114.7 | 2.3 | 33% | slow |
| nemotron-3.5-lightning | $0.00141 | −68% | 14.3 / 36.0 | 2.2 | 18% | runaway outputs |
| gpt-5.4-nano | $0.00405 | −9% | 20.9 / 44.4 | 2.1 | 23% | |
| ling-3.0-flash | $0.00025 | −94% | 5.1 / 16.8 | 1.2 | 26% | cheapest |
| gpt-6-luna (none) | $0.00237 | −47% | 10.1 / 31.9 | 1.3 | 22% | fails validation, retries |
| solar-mini4 | $0.00111 | −75% | 30.6 / 70.0 | 1.1 | 19% | runaway outputs |
| mercury-2.5 | $0.00089 | −80% | 8.9 / 39.8 | 0.8 | 17% | rate-limited upstream |

Qwen 3.7/3.8 not run: only Alibaba serves them on OpenRouter, not zero-retention (founder to decide).

**Quality, 2026-09-26 — blind grading by Claude Code (Opus 5.5) on the founder's plan; 6 helper
agents, one rubric, models hidden. Not yet checked against founder labels.**

Full pipeline, each model self-checking (engine 99d1911f2c):

| | Words graded | Idiomatic | Acceptable | Wrong | Inventions | Note problems |
|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 69 | 36% | 48% | 16% | 20 (9/30 pieces) | 7 |
| gemma-4-26b | 77 | 35% | 38% | 27% | 4 (4/30) | 11 |

Writer only, checks off (engine cce7c6f829) — the apples-to-apples writer comparison:

| | Words graded | Idiomatic | Wrong | Inventions | $/piece |
|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 123 | 25% | 38% | 43 (18/30) | $0.00236 |
| gemma-4-26b | 98 | 34% | 21% | 11 (7/30) | $0.00060 |

Checker test (`src/evals judge`, production QC prompt, gold = the 367 graded words):

| Checker | Catches wrong | Rejects idiomatic | Rejects acceptable |
|---|---|---|---|
| gpt-6-luna (none) | 91% | 15% | 56% |
| deepseek-v4.1-flash | 86% | 15% | 47% |
| gemini-3.1-flash-lite | 69% | 2% | 19% |
| gemma-4-26b | 55% | 2% | 17% |
| gpt-5.4-nano | 17% | 3% | 5% |

Split roles, full pipeline (not yet graded): Gemma + luna checker $0.00107/piece, 4.6/16.0 s,
coverage 45%; Gemma + deepseek checker $0.00122, 6.7/15.0 s, 46%; Flash-Lite alone $0.00395,
4.9/11.1 s, 43%.

**Decision (founder, D42):** Gemma 4 26B replaces Flash-Lite in production, self-checking as
before; Flash-Lite becomes the fallback. Split writer/checker is the ready next step if
misuse shows up.
gemini-2.5-flash-lite is closed to new API users (404, 2026-09-26).

---

# Rewrite-Model Bake-off (2026-07-24)

Four models, identical prompt (core + news wrapper), identical source article
("The gap in the archives", Global Voices), identical 10 candidate words.
Founder skim-judged quality "equal-ish"; close read below found real differences.
Harness: `src/bakeoff.py`; blind outputs in `output/bakeoff/`.

## Results

| Model | Blind letter | Time (no stream) | Cost/piece | Words embedded | Misuses | Notes |
|---|---|---|---|---|---|---|
| **claude-haiku-4-5** | B | **10.8s (fastest)** | $0.0071 | 7 — all natural | 0 | Densest natural embedding; minor `**` artifact leaked into TITLE |
| claude-sonnet-4-6 | A | 25.5s | $0.0254 | 6 — all natural | 0 | Most polished prose; longest piece; 3.6× Haiku cost |
| gpt-5-mini | D | 13.9s | **$0.0026 (cheapest)** | 4 | **1** | "risks a cultural **squander** of embodied techniques" — squander used as a noun (nonstandard); also loosest output-structure adherence (section ordering varies run to run) |
| gemini-3.6-flash | C | 19.9s | **$0.0323 (most expensive)** | 5 — all natural | 0 | Sticker price mid, but burned ~3K hidden thinking tokens per piece despite `thinkingBudget: 0` — actual cost 4.5× Haiku; also the thinnest piece (389 words) |

## Decision: Haiku 4.5 confirmed as the rewrite model (PRD D5)

- **Quality:** zero word misuses across 7 embeddings — the naturalness bar (D14/D19)
  is the one non-negotiable, and the only model to fail it was the cheapest one.
- **Speed:** fastest raw latency; best fit for the tap-to-stream moment (D17).
- **Cost:** $0.007/piece ≈ $1/user/month at 5 pieces/day — within the D10 freemium envelope.
- Sonnet 4.6 is the quality ceiling reference: noticeably more polished prose at 3.6×
  cost — useful as an occasional QC benchmark or premium-tier idea, not the default.

## Addendum 2026-07-26: Kimi K2.5 (founder-requested)

Same article + candidate words, run with the *tightened* core prompt (post word-pressure
fix — a mild advantage over the July 24 runs). Results (`output/bakeoff/bakeoff-kimi.html`):

- **Usage quality: 4/4 clean** (perfunctory, deft, eschew, ubiquitous — all textbook), and
  the best menu discipline of any model tested: used only 4 of 10 candidates.
- **Disqualifying economics/latency for the on-tap slot:** K2.5 is an always-reasoning
  model — it spent ~5.5K hidden thinking tokens (23K chars of internal reasoning) per
  piece. 115s wall-clock (10× Haiku), ~$0.020/piece (~3× Haiku). Worse for D20 UX:
  reasoning happens *before* output, so streamed time-to-first-paragraph would be
  60-100s, vs ~1-2s on Haiku. First harness run also truncated it (4K cap consumed by
  reasoning) — reasoning models need ~12K max_tokens headroom.
- **Verdict: quality competitive, product-fit poor.** Revisit only if Moonshot exposes a
  no-thinking mode; D5 (Haiku) stands.

## Addendum 2026-07-26 (2): o3-mini (founder-requested)

Run at `reasoning_effort: low`, 12K token headroom. Results
(`output/bakeoff/bakeoff-o3-mini.html`):

- **Speed/cost: excellent** — 5.6s (fastest tested), $0.0072/piece (≈ Haiku). At low
  effort it barely thinks (~900 output tokens total), which corrects an earlier
  overgeneralization: OpenAI's o-series has an effort dial, so "reasoning model" ≠
  automatically slow — unlike Kimi K2.5's always-on design.
- **Usage quality: weakest tested alongside gpt-5-mini.** Of 4 embedded words, only
  *deft* is clean. "craft bears an unexpected **candor**" (objects can't have candor),
  "ideas that would **eschew** an inquiry" (people eschew, ideas don't), "presence is
  strikingly **ubiquitous** in the cultural lexicon" (semantically muddled).
- **Prose quality: noticeably flatter** — lost the article's concrete details (kohl,
  lamp soot, family ritual) in favor of abstract filler ("invites us to appreciate a
  deeper material narrative"). The one dimension no metric captures, and the reader
  feels it.
- **Verdict: no.** Same cost and speed class as Haiku with clearly worse words and
  flatter prose. D5 stands, now tested against six models.

**High-effort follow-up (same day):** at `reasoning_effort: high` — 5/5 clean word
usages (perfunctory, ubiquitous, zeitgeist, deft, squander — all natural), prose
recovered concreteness. Price of the fix: ~4,900 reasoning tokens → 26.6s, $0.0286/piece
(4× Haiku, 2nd-most-expensive tested), and reasoning-before-output breaks the streamed
tap-to-read moment (~20s+ to first word). **Confirms the cross-model pattern:
deliberation buys word discipline** (Kimi showed the same) — but Haiku + the $0.001 QC
gate buys equivalent discipline for $0.008 total with instant streaming. Verdict
unchanged.

**Medium-effort follow-up:** 7.7s, $0.0105, ~700 reasoning tokens. Quality lands exactly
between low and high: of 3 marked words, 1 clean (*ubiquitous*), 2 borderline ("critical
**candor**" — defensible; "a flair that is both **deft** and…" — strained), plus a
bookkeeping slip (WORDS_USED lists *gravitas*, never marked in text). Full dose-response
curve on one model: ~200 think-tokens → 1/4 clean; ~700 → borderline; ~4,900 → 5/5 clean.
Word discipline scales smoothly with deliberation — and no point on the curve beats
Haiku ($0.007, instant stream) + gate ($0.001).

## Addendum 2026-07-26 (3): Gemini 3.1 Flash-Lite — first genuine challenger to D5

Results (`output/bakeoff/bakeoff-flash-lite.html`): **3.6s (fastest tested), $0.00165
(cheapest tested — 4.3× cheaper than Haiku)**, no hidden thinking tokens (unlike its
3.6-flash sibling), and strong quality: 4 of 5 embedded words clean (*conundrum,
squander, ubiquitous, deft* — all textbook), 1 stretch ("treating objects with the same
**candor** and rigor" — borderline, not broken). Prose kept the article's concrete
detail (lamp soot, brass weight, hinge click) — no o3-mini-style flattening.

**Status: challenger, not champion.** n=1; Haiku's own bake-off run was equally clean
before production variance showed up. Before touching D5, run a proper head-to-head:
≥3 articles × both models × gate on, comparing usage quality, consistency, and format
discipline. If Flash-Lite holds, the digest COGS drops ~4× (heavy user: ~$0.30/mo).

**Word-level finding (cross-model):** *candor* has now strained or broken 5 attempts
across 4 different models (Sonnet stretch, o3-mini misuse, o3-mini-medium borderline,
flash-lite stretch; only Haiku's "restore candor about who made them" passed). Abstract
human-quality nouns resist embedding in object/process-focused texts — an argument for
word→piece routing (D27) to weigh semantic compatibility, not just due-ness.

## Head-to-head 2026-07-26: Haiku 4.5 vs Gemini 3.1 Flash-Lite — challenger wins

3 articles × 3 wrappers (GV news / On This Day / century-OCR), identical 10-word menus,
`candor` planted as the known stress-word. Artifacts: `output/headtohead/`.

| | Haiku 4.5 | Flash-Lite 3.1 |
|---|---|---|
| Embedded (3 pieces) | 16 | 11 |
| Clean usages | ~9 | **10** |
| Misuses/broken | **~5** ("galvanizes the question", "coalesce X with Y", "decision would corroborate a shift", "assuaged testimonies", "unconcerned with his own candor") + 2–3 stretches | **1 borderline** (transitive "coalesce a community") |
| Avg speed | 10.5s | **3.0s** |
| Avg cost/piece | $0.0083 | **$0.0017 (≈5× cheaper)** |

Flash-Lite's edge is *selectivity*: it embedded fewer words per piece (3.7 vs 5.3) and
skipped every trap (used candor flawlessly in the one piece where it fit a person —
"a display of startling candor" — and skipped it elsewhere). Under D27 (menus,
same-day recurrence) fewer-but-cleaner per piece is the correct behavior; density comes
from the daily flow, not per-piece cramming. Haiku's century piece was its worst run
recorded ("the men's assuaged testimonies").

**DECIDED 2026-07-26 (founder): gemini-3.1-flash-lite is the rewrite model for now,
with claude-haiku-4-5 as the named fallback rung (provider outage / deprecation /
regression). QC gate (D19) unchanged and still required — FL's 91% clean is not 100%.**
Evidence: 4 FL runs total (bake-off + 3 H2H), zero hard breaks. Residual risks accepted:
n still modest; Google model-deprecation cadence; multi-provider dependency (harness
already provider-agnostic). Logged as PRD D5 (updated). Code follow-up: switch
`src/generate.py` from the Haiku caller to the Gemini caller.

1. **n=1 article, n=1 run per model.** Enough to pick a default, not a final verdict.
   Re-run on a Gutenberg retold-classic before MVP build (different wrapper stresses
   different skills).
2. **Prompt authorship bias:** the prompt was written by Claude (Fable), which may
   favor Claude-family models' conventions. gpt-5-mini at $0.0026/piece (2.7× cheaper
   than Haiku) could plausibly be prompted into shape — worth revisiting if unit
   economics ever pinch. Its noun-"squander" misuse and loose section ordering are
   the reasons it doesn't win today.
3. **Gemini's hidden thinking tokens** may be controllable with different API params
   (`thinkingLevel`?) — not investigated further since its floor price still exceeds
   Haiku's.
4. Founder skim-test data point: all four passed a casual read — differences only
   surfaced under close per-word review. Supports D19 (occasional imperfection is
   survivable) but also shows why the close-read QC matters for pre-generated slots.

---

## Sentence judge (TD-20, D53) — 2026-10-01

**Task:** judge one sentence a user wrote with a target word. Verdict natural / could-be-better / wrong, a
one-line reason, the smallest fix. Prompt `prompts/exercises/sentence-judge.md`; harness
`python src/evals sentences judge <model>`; set `data/evals/golden/sentences.json` (120 items).

**Answer key.**
- 35 published quotations (natural) and 28 seeded errors (wrong): fixed answers.
- 27 borderline and 30 synthetic learner sentences: Claude Code's labels. The founder chose this for now
  (2026-10-01) instead of writing and labelling himself. **57 of 120 answers have no human check yet.**

**Results** (n = 120 per model, 6 models, $0.68 total including two earlier runs):

| Model | Missed (wrong→natural) | False alarms (natural→wrong) | Could-be agreement | Pushback flips | Fix size | $/grade | p50 |
|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash@nothink | 0% of 35 | **2% of 56 (1)** | 54% | **0% of 18** | 23% | $0.00008 | 1.1 s |
| gemma-4-26b (production checker) | 0% | 9% (5) | 57% | 11% (2) | 17% | $0.00007 | 1.5 s |
| gemini-3.1-flash-lite | 0% | 9% | 68% | 24% (4) | 18% | $0.00024 | 0.9 s |
| gpt-6-luna@none | 3% (1) | 9% | 11% | 12% | 19% | $0.00008 | 1.4 s |
| gemini-3.8-flash | 0% | 9% | 29% | 0% of 19 | 18% | $0.00244 | 4.7 s |
| deepseek-v4-pro | 0% | 9% | 46% | 17% | 14% | $0.00264 | 13.1 s |

**Findings.**
- **Clearly wrong sentences are easy.** Every model caught all 35, including the 7 subtle synthetic ones,
  so the models separate on the in-between calls instead.
- **Stronger models were not better.** The two 30× pricier models did no better than the cheap ones, and
  deepseek-v4-pro took 13 s per grade.
- **deepseek-v4.1-flash leads provisionally.** It had the fewest false alarms and never backed down under
  pushback. The differences are small in counts, though: 1 vs 5 false alarms, 0 vs 2 flips.
- **The answer key is the weakest link.**
  - On 16 items, at least 4 of 6 models disagree with the key. Eleven of them are borderline, and on
    several the models look right: "windfall of a promotion", "adamant that you will like it",
    "zeitgeist at this party" and "a caveat not to be late" are probably *wrong*, not could-be-better.
  - So Claude's labels lean lenient, which is the circularity risk that came up when choosing who labels.
  - Agreement on borderline items is only 54% (pooled).
  - **Cheapest human step:** the founder or a native speaker reviews those 16 items (about 5 minutes)
    before a model is chosen.
- **Shared false alarms.** Most models flag the same 3–5 published sentences ("assuage conflicts",
  "misgivings proved prudent", "an elusive variety of bird"). Published text is not always idiomatic.

**Not decided:** no judge model is chosen yet. Choose after the 16-item human review; re-run is free of new code.

---

## Jev PoC (D54, backlog TD-21) — plan, 2026-10-04

**Question:** at every live step that returns yes/no, a choice or a score, does TypeSafe's Jev
(~$0.00002/call, ~100 ms, no text output) match the current model's quality? If it does, it
replaces it or pre-screens for it.

**Where Jev competes:** the founder's list. These are all the decision-shaped steps in the four
user flows (diagrams/README.md); every other step writes text or is plain code.

| Order | Step (flow) | Jev question shape | Eval | Notes |
|---|---|---|---|---|
| 1 | Word checker (share an article) | one Noul per highlighted word: "is `word` used idiomatically in `sentence`?" | ✅ `judge` (n = 216 graded words) | biggest gap: Gemma catches 55% of wrong words |
| 2 | Sentence judge, write-a-sentence verdict | one 3-way Choice, and separately 5 Nouls (meaning, collocation, register, connotation, word grammar) combined in code | ✅ `sentences judge` (n = 120) | an LLM still writes the reason and fix when the verdict isn't natural |
| 3 | Fact checker (share an article) | one Noul per edited sentence: "does `edited` state anything `original` doesn't?" — not the whole article (Jev degrades on large, mostly irrelevant input) | ❌ build: answer key per edited sentence | users' reading goes to TypeSafe; retention is not zero → founder call before production (D54) |
| 4 | "Is this sentence natural?" check on model-written fill-in sentences | same judge as 2 | ✅ reuses `sentences judge` | only if the check is kept in the fill-in design (UX-16); written once per word, so cost is small either way |
| 5 | "Is this a real English word?" (save a word) | one Noul | ❌ build: small key of real rare words + misspellings / misheard words | low value: runs only when Wiktionary lacks the word, and a real word still needs an LLM for its card |

**Not a Jev step:** the grader inside the article-rewrite eval. It is the answer key, so it stays
the strongest fixed model. It runs only while building, and Jev would otherwise grade a contest
it competes in.

**Method:** a plain HTTP caller (`POST https://api.typesafe.ai/v1/systemone`, no SDK) as a new
eval provider. Same frozen sets and metrics as the LLM candidates. Shuffle Choice options and
re-run, because Jev leans toward the first option. Report Jev's confidence beside each answer to
test confidence-gating: Jev decides confident cases and an LLM takes the rest. Expected cost per
eval: well under 1 cent.

**Win condition (proposed — founder to confirm):** on a step's eval, Jev misses no more wrong
items than the current pick, raises false alarms at most 5 points more, and is cheaper. For a
step that sends users' reading (3), retention must also be accepted.

**Blocked on:** the founder creating a TypeSafe account and putting `TYPESAFE_API_KEY` in
`.env.local`.

### Jev PoC step 1 — word checker, first run (2026-10-04)

Same 557 graded words for both models (127 wrong, 189 idiomatic, 241 acceptable, per the grader).
Answer key = the grader's verdicts, never checked by a human.

| Checker | Wrong words caught | Idiomatic rejected | Cost, all 173 pieces | Time |
|---|---|---|---|---|
| Gemma 4 26B (production) | **58%** (74/127) | **1%** (2/189) | $0.028 | — |
| Jev, keep if P ≥ 0.5 | 18% | 3% | $0.007 | 27 s total (~0.15 s/piece) |
| Jev, keep if P ≥ 0.7 | 35% | 4% | | |
| Jev, keep if P ≥ 0.8 | 57% | 8% | | |
| Jev, keep if P ≥ 0.9 | 97% | 35% | | |

- **Good ranking, misplaced probabilities.** AUC 0.90: a random wrong word scores below a random
  idiomatic word 90% of the time. But almost everything scores high (median 0.78 for wrong words,
  0.91 for idiomatic), so the useful cut-off sits around 0.8–0.9, not at 0.5. On our definition of
  "idiomatic", Jev's probabilities are not calibrated.
- **Fails the proposed win condition as run.** At 0.8 it matches Gemma's catch rate (57% vs 58%),
  but rejects 8% of good words vs 1% (+7 points; the bar is +5). The thresholds above were read off
  the same data they are scored on, so they flatter Jev slightly.
- **The cost gain is small here.** The checker is one call per article, and Gemma is already cheap
  ($0.00016 vs $0.00004 per article). Jev's case at this step would have to be quality, and it
  isn't better.
- Some "wrong" grader verdicts look doubtful (e.g. "a tenuous connection"), so the answer key may
  be off by a few items.
- Not tried yet: tightening Jev's question per the docs (explicit boundary cases, examples in the
  criteria), and choosing a threshold on a held-out half.

### Jev PoC step 2 — sentence judge, first run (2026-10-04)

One request per sentence (n = 120) asked three variants at once: the 3-way Choice, the same Choice
with options reversed, and five single-property Nouls combined in code (thresholds fixed before
the run). $0.00004 per request for all seven questions; 0.2 s p50. Same answer key as the LLM runs
(57 answers are Claude's provisional labels).

| | Wrong → natural (harmful) | Wrong → could-be | Natural → wrong | Natural → could-be | Could-be → natural |
|---|---|---|---|---|---|
| Jev 3-way Choice | 2/35 (6%) | 15/35 (43%) | **0/57** | 1/57 | 19/28 |
| Jev 3-way, options reversed | same verdict on 119 of 120 — no order bias seen | | | | |
| Jev 5 Nouls | 0/35 | 7/35 | 3/57 | 36/57 (too strict at these thresholds) | |
| Best LLMs (gemma, gemini-3.8-flash) | 0/35 | 0/35 | 5/57 | 1–3/57 | — |

- **As the whole judge, Jev is too lenient.** It softens 43% of wrong sentences, passes 2 wrong
  sentences as natural ("adamant on", "mitigate the gap"), and passes 19 of 28 could-be-better
  sentences as natural. The 5-Noul variant goes the other way: too strict.
- **As a gate it works.** The design (flow-write-a-sentence) sends every not-natural verdict to
  an LLM for feedback, so the only harmful Jev error is a false "natural". Give ✓ only when
  P(natural) is high, and send the rest to the LLM:

  | ✓ if P(natural) ≥ | Wrong passed | Could-be passed | Natural given ✓ without an LLM call |
  |---|---|---|---|
  | 0.8 | 0/35 | 8/28 | 50/57 |
  | 0.9 | 0/35 | 2/28 | 47/57 |

  On fixed-answer items only (no Claude labels): at 0.9, 0/28 wrong passed and 28/35 natural
  given ✓. Thresholds were read off this same set, so they flatter Jev. Confirm on fresh
  sentences (ideally the founder's real ones) before production.
- **Money: a modest saving against deepseek, a large one against strong models.** At 10K users ×
  5 sentences/day with the gate at 0.9 (on this set ~59% of sentences still go to the LLM):
  deepseek alone ≈ $120/mo, Jev gate + deepseek ≈ $90–100/mo, Jev gate + gemini-3.8-flash ≈
  $2,200/mo instead of $3,700. The share of natural sentences real users write is unknown; more
  natural sentences means larger savings.
- **Speed:** a natural sentence gets its ✓ in ~0.2 s instead of 1–5 s.
- **Jev raised no false alarms on published sentences** (0/35 fixed natural), where every LLM
  flagged 1–5.
