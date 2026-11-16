# Streaks and "shown": what gets recorded, and how stats come out of it

Decision: PRD D74 (2026-11-15). Research: `docs/streaks-stats-research.md`. Built 2026-11-15:
`src/service/stats.py`, `EventQueue.swift`, the reader's visibility script (`PieceHTML.swift`).

Two kinds of fact, stored as they happen and never changed; every stat is worked out from them when
asked for (no counters).

```mermaid
flowchart TD
    subgraph Phone["On the phone (app, share sheet, Safari action)"]
        R1["Reader: a highlighted word<br/>≥ half on screen for 1 s<br/>(once per word per opening)"] --> Q
        R2["Reader: piece on screen 10 s"] --> Q
        R3["Reader: tap on a highlight"] --> Q
        P1["Practice: an exercise appears"] --> Q
        Q[["Event queue: one file per event<br/>in the app group · own id · time it happened"]]
        P2["Practice: an answer<br/>+ seconds since it appeared"]
    end

    Q -- "batch, 2 s after the last event<br/>and when the app comes to the front" --> E["POST /v1/events<br/>dated by when it happened;<br/>future or > 3 days old: rejected;<br/>an id seen before: ignored"]
    E --> EV[("events<br/>tap · open · shown")]

    P2 --> A["POST /v1/practice/…<br/>one transaction"]
    A --> PA[("practice_attempts<br/>+ box before / after, sentence, seconds")]
    A --> WB[("words.box / due_day<br/>latest state only")]
    S["Save · retain · learn again · delete"] --> WL[("word_log")]
    S --> WS[("words.status<br/>latest state only")]

    EV --> ST{{"Worked out on request"}}
    PA --> ST
    WL --> ST
    ST --> U["GET /v1/stats<br/>streak · best · total days · today"]
    ST --> W["GET /v1/words/{id}/stats<br/>shown in reading / practice · taps ·<br/>answers · box history · retained, relearned"]
```

## Rules (D74)

- **A streak day** = a day (the user's day, D51) with a practice answer or a read (`open`). A missed day
  resets the streak; the total of days never resets. Later, a day saved with points becomes its own fact.
- **Shown** counts once per piece per day in the reader, once per exercise per day in practice; the raw
  events are all kept, so this rule can change without losing history. The Words list doesn't count.

## Why this shape (standard practice)

- **Append-only facts, derived stats:** Anki's review log vs its card table; a counter that one code path
  forgets to update is wrong forever, a query isn't.
- **Box before and after on each answer:** once `words.box` is overwritten, the past state is gone
  (Anki's `ivl`/`lastIvl`, FSRS review logs).
- **Phone-made ids, resends ignored:** the idempotency-key pattern; the queue can retry safely.
- **One file per event:** the app and its extensions add to the queue without editing a shared file
  (Apple TN2408: atomic writes for data shared with extensions).
- **Answer + schedule change in one transaction:** the log and the word row can't disagree.
