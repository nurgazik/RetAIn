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
