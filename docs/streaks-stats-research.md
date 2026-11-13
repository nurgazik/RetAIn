# Streaks and stats: research (UX-25)

Research for streaks, daily progress and stats (user, word, exercise) and the data model that
captures them. Done 2026-11-13 by three parallel research passes (competitors, streak science,
data-model practice), then checked against the repo. Founder's rules going in: a day counts if the
user practised or opened the app; a word counts as "shown" only when the user actually saw it.

Evidence labels: **causal** = randomized study or A/B test; **observational** = correlation;
**opinion**; **inferred** = our reasoning, no direct source; **unverified** = secondary sources only.
Duolingo's numbers are its own, self-reported and mostly relative.

---

## 1. What the products do

| | Active day | Protection | Daily goal | Stats | Social |
|---|---|---|---|---|---|
| **Duolingo** | one lesson (since 2020; before: hit the daily goal) | freeze (hold up to 2), gem repair, wager | XP, separate from the streak | streak, XP | weekly leagues, Friend Streak |
| **Anki** | no streak; "days studied" | — | none | calendar heatmap, forecast, true retention, full per-card history | none |
| **Clozemaster** | play any day (global streak); hit points (goal streak, now hidden) | "streak saves" for a 1-day gap | points | days played, streak, % mastered per sentence | points leaderboards |
| **Memrise** | hit the daily goal (help-page snippets) | none found | per course | 2025 "My Activities": words learned / reviewed, *no streaks or points* | none |
| **WaniKani** | no streak; "days studied" = ≥1 lesson or review | — | none | heat map, 24 h and 5-day review forecast | none |
| **Babbel** | any learning activity (snippet) | none found | none found | weekly activity | — |
| **Readwise** | Daily Review completed | recover missed days from the past 7 | the Daily Review | calendar of days done | none |
| **Lingvist** | — | — | 100 cards, 20 new words, 80% correct | daily stats | — |

Sources: blog.duolingo.com/improving-the-streak · Duolingo 10-K FY2025 (sec.gov) ·
blog.duolingo.com/how-duolingo-streak-builds-habit · docs.ankiweb.net/stats.html ·
github.com/ankitects/anki ftl/core/card-stats.ftl · forum.clozemaster.com/t/1345 and /t/67329 ·
docs.clozemaster.com/article/103 · memrise.com/blog/my-activities-2025 ·
knowledge.wanikani.com/widgets/days-studied · readwise.io/changelog/stats ·
support.babbel.com/hc/articles/17020978582162 · lingvist.com/help/when-does-the-app-reset-my-daily-stats.
Not covered: Quizlet (no primary source). Duolingo's Help Center couldn't be rendered; its rules come
from the blog and SEC filings.

**Patterns**
- **No product counts merely opening the app.** The lowest bars are Duolingo's one lesson and Babbel's
  "any learning activity". RetAIn's "opened the app" rule would be the most lenient found.
- Two counters side by side: the **streak** (consecutive, resets) and **total days studied** (never
  resets) — Anki, WaniKani, Clozemaster.
- Protection usually covers **one missed day**: Duolingo freezes held in advance, Clozemaster saves,
  Readwise's 7-day recovery.
- The two SRS-first products (Anki, WaniKani) have **no streak** but show a **review forecast**
  (what's coming due) and a calendar heatmap.
- Per-item history is Anki's strength: added, first/latest review, reviews, lapses (times forgotten),
  interval, average and total time, and a row per review (date, type, rating, interval, time).
- Memrise dropped streaks and points in 2025 ("without the pressure of maintaining streaks").
- Time-zone and daylight-saving bugs are a recurring complaint (Clozemaster, Lingvist, Anki forums).
  RetAIn's stored day key (D51) already avoids the usual cause: recomputing days from timestamps.

## 2. What the evidence says

**Streaks raise engagement; their effect on learning is barely measured.**
- *Causal, engagement.* Duolingo A/B tests: one lesson keeps the streak → +40% learners on 7-day
  streaks, Day-14 retention +3.3%, DAU +1%, **but fewer learners reached their daily goal**
  (improving-the-streak, 2020). Streak wager: Day-7 retention +14%. Weekend amulet: 5% less likely to
  lose the streak, but weekend DAU down 5–10%. Two equipped freezes: DAU +0.38%. Milestone animation:
  new users' Day-7 activity +1.7% (2017, 2022 posts).
- *Causal, learning (weak).* The only randomized study tying streaks to learning: 60,000 Peruvian
  students on a maths platform (Aulagnon, Cristia, Cueto & Malamud, IPR WP-26-05, draft Feb 2026).
  **Weekly** streaks raised weeks connected by 9.4 points; test scores +0.13–0.17 SD, but only 2.3%
  took the test and the effect wasn't significantly different from reminders. No discouragement after
  a break.
- No Duolingo study shows streaks improve learning (as opposed to engagement).

**A broken streak drives people away; slack and repair soften it.**
- *Causal.* Silverman & Barasch 2023 (J. Consumer Research, 7 experiments): an intact streak raises
  repetition vs a broken one even with identical behaviour; the drop is smaller when the break can be
  repaired or blamed on outside causes. "Get back on track" nudges mostly failed.
- *Causal.* Sharif & Shu 2017 (J. Marketing Research): a hard goal with **emergency reserves** (a few
  allowed skips) beat both easy and hard goals; after a miss, 55% rebounded vs 37% (hard) and 44% (easy).
- *Causal.* Milkman et al. 2021 (Nature, gym megastudy, 60,000+ people): the best of 53 interventions
  was a small bonus **for coming back after a miss** (+27% visits over 4 weeks).
- *Observational.* Lally et al. 2010: missing one day "did not materially affect" habit formation;
  median 66 days to automaticity. Dai et al. 2018: resets demotivate people who were doing well →
  keep a counter that never resets.

**Lenient day rules produce token actions.**
- *Natural experiment.* When GitHub removed streak counters, weekend activity and single-contribution
  days fell (Moldon, Strohmaier & Wachs 2021, ICSE): the counter had been producing token one-commit
  days. Closest evidence on "opening the app counts". No study compares "opened" with "one small action"
  directly — *inferred*.

**Streaks must not reward reviewing ahead.**
- *Causal.* Spacing beats massing for 90% of learners, yet 72% believe massing works better (Kornell
  2009); the best gap grows with how long you need to remember (Cepeda et al. 2006, meta-analysis of
  317 experiments). A streak that needs practice on a day with nothing due pushes review-ahead, which
  RetAIn already counts as weaker (D60, D66).

**Stats help when they show competence, not volume.**
- *Causal.* Performance graphs raised felt competence (Sailer et al. 2017). Showing learners the
  system's estimate of their mastery ("open learner model") improved maths-tutor outcomes (Long &
  Aleven 2017, abstract only). Transfer to vocabulary is *inferred*.
- *Causal, small.* Badges + leaderboard lowered intrinsic motivation and exam scores in one course
  (Hanus & Fox 2015, n = 71).
- *Observational.* Goal-gradient: people speed up near a goal (Kivetz et al. 2006) → "2 more clean
  answers until this word reaches the top box" framing.
- "Streak anxiety" appears only in opinion pieces; no measured study found.

## 3. Data-model practice

**Keep facts append-only; derive stats when read.** Anki's `cards` table is current state; its
`revlog` (one row per answer: time, card, button, new interval, previous interval, ease, ms spent,
type learn/review/relearn/manual/rescheduled) is the history. Anki's stats split along that line:
history graphs and Card Info from the log; counts and forecast from current state. The log row carries
the interval before and after, because the card "could have changed" since (docs.ankiweb.net/stats.html).
Manual changes are log rows too (types 4 and 5), not silent edits.
- FSRS (Anki's newer scheduler) trains on each item's full ordered review log, with duration; missing
  history has to be guessed (github.com/open-spaced-repetition/py-fsrs; docs.ankiweb.net/deck-options.html).
- Duolingo's half-life regression data per exposure: time since last seen, times seen, times correct,
  this session's seen/correct (github.com/duolingo/halflife-regression).
- Fields learning systems wish they'd logged from day one (*synthesis*): state before and after,
  duration, time since the previous review, a row for every state change, an unbroken log from the
  first exposure.
- Stored counters drift; computed stats correct themselves. Add a rollup table only when a query is
  measurably slow, and keep it rebuildable from the log (martinfowler.com/eaaDev/EventSourcing.html).
  At RetAIn's size (437 attempts in 7 weeks) every stat computes on read in milliseconds — *inferred*.

**"Seen" needs a definition.** The ad industry's: ≥50% of the item visible for 1 continuous second
(IAB/MRC guideline). Adopting it for "shown" is our choice, not a learning-app standard.
- Reader (web view): IntersectionObserver v1 (in WebKit since iOS 12.2) with a 0.5 threshold and a 1 s
  timer in JavaScript; post one batch per piece, not a message per word.
- SwiftUI `onAppear` fires early for lazy rows and again on re-render → deduplicate by id.
  `onScrollVisibilityChange` needs iOS 18; RetAIn targets **iOS 17.0** (project.yml). Practice shows one
  exercise at a time, so it doesn't need either.
- "App opened" = the scene becoming `.active`; background refresh and widgets don't reach `.active`
  (*inferred*; needs a device test).
- Events sent from the phone: a client-made id so a retry doesn't double-count (`INSERT OR IGNORE` on a
  unique column), the phone's day and time, an on-disk queue, sent in batches.

**Streaks from days.** "Gaps and islands": number each distinct active day in order, subtract from the
date, group → each group is one run. SQLite has the window functions (3.53 in the venv). Current streak
= the run ending today or yesterday, by the user's day key. A freeze or repair is stored as a fact for
that day, and the query reads it (Duolingo repairs outage days the same way:
blog.duolingo.com/protecting-streaks-from-site-issues).

**Privacy.** Collect only what's needed and keep it no longer than needed (GDPR Art. 5). Apps with
accounts must offer account deletion in the app (App Store Review Guideline 5.1.1(v)).

## 4. What RetAIn has today (checked 2026-11-13)

Already logged: every answer (`practice_attempts`: word, day, kind, result, hint), hangman guess logs
with seconds, reader taps (`events`), placements per piece (`pieces.words_used`), answered bank
sentences (`sentence_views`), save date (`words.added`), and a day key on every row (D51).

Gaps:
1. **No before/after on answers.** `reschedule()` overwrites `words.box` and `due_day`; box history is lost.
2. **Status changes leave no trace.** Retained, deleted, learn again, and re-saving a deleted word
   (which overwrites `added`, app.py:131) aren't logged.
3. **No app-open fact** for the streak.
4. **Nothing records what was seen.** `events` was designed for `impression` but it's never written;
   `words_used` is placement, not sight.
5. **Answers don't name their sentence or time spent** (sentence id sits in `practice_sets` JSON; only
   hangman has seconds).
6. **Taps take the day they arrive**, not the day they happened (app.py:414).
7. **No account deletion and no enforced links between tables**: no `PRAGMA foreign_keys`, no
   `ON DELETE`, no delete-account route. Needed before anyone else installs the app.

## 5. Open questions (founder)

See the summary in PROGRESS.md 2026-11-13 and the conversation; decisions go in the PRD log.
- Streak rule: "practised or opened the app" vs a minimum act that teaches.
- Streak protection: automatic skips, earned freezes, or none.
- Daily or weekly streak.
- Which surfaces count as "shown".
