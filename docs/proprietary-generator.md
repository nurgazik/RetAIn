# Proprietary piece generator — design (captured 2026-08-02, build deferred)

Status: **designed, not built.** PoC Source 4 (PRD §7). Founder deferred the build
to prioritize the daily digest habit test; this doc preserves the agreed design so
nothing is re-litigated later. See PROGRESS.md next-up queue.

## Why this slot matters

- **Register vehicle**: words modeled in speech the reader wants in their own mouth
  (dialogue puts words in spoken turns, not just prose).
- **Never-empty floor**: works with zero fetchers alive.
- MVP's narrative slot grows out of it.

## The central design problem

"Write a conversation using these 6 words" produces ESL-textbook theater — the
words become the skeleton and the piece exists for the vocabulary (homework
energy, violates D18). Every other slot avoids this because content has an
independent reason to exist. **Solution: grow our own sources** — premises are
generated separately and become ordinary pantry items; the rewrite pipeline then
treats a premise exactly like a source article (menu-not-quota words, QC, density
floor, D14 taste rule, served ledger — all unchanged).

## Two-stage architecture

**Stage A — premise bank** (batch, ~weekly, one cheap call):
20–30 premises stored as pantry items (source `proprietary`). Each premise =
format + topic + 2–3 sentence setup containing a tension or question.

**Stage B — existing pipeline, unchanged**: `generate.py` with a new
`prompts/proprietary.md` wrapper (dialogue formatting, named speakers, natural
turns, no moral-of-the-story wrap-up, ~250–400 words).

Pipeline adjustments needed at build time:
- Attribution branch: "A RetAIn original."
- Skip the `invented_numbers` tripwire for source `proprietary` (it polices fact
  preservation; fiction is allowed to invent).

## Freshness mechanics (novelty is structural, not vibes)

Lesson repeated all through this project (D28, BC years): the lever must be
mechanical, not a prompt asking the model to behave.

1. **Combinatorial seeding** — `data/premise_axes.json` with founder-editable
   axes: topics (founder's interest areas — NOT yet captured), formats
   (dialogue / mini-column / flash fiction), and ~12 reusable angles ("a belief
   most people hold that's wrong", "the hidden trade-off", "an everyday thing
   nobody can explain", "origin story no one knows", "small ethical dilemma",
   "two experts disagree", "beginner interrogates expert", "what-if"...).
   Code samples (topic × format × angle) briefs; the model fills briefs, it does
   not free-associate. ~15×3×12 = 540 cells ≈ a year+ at 1–2 pieces/day.
2. **Anti-repetition memory** — sampler excludes recently used topic-angle pairs
   (code, exact); generation call receives last ~30 premise titles as "do not
   resemble these" (prompt, near-dupes). Served ledger already tracks usage.
3. **External sparks** — unused pantry items (GV articles never served, SE
   questions, On-This-Day events) seed premises as "riff on this, don't retell
   it". External entropy is inexhaustible; the calendar pair already proves the
   pattern.
4. **Taps as signal** (MVP, not PoC) — reading/tap logs per topic/angle weight
   the sampler toward what the reader actually enjoys. PoC: log only.

## Open founder inputs (gate to building)

1. Interest areas → topics axis.
2. Recurring cast yes/no: 2–3 named characters recurring across conversations
   (serial charm, one-publication feel, MVP narrative seed; risk: staleness —
   premise bank rotates topics underneath them).
