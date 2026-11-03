# A practice day: what starts it, and what carries over

Decisions: PRD D56 (daily practice), D57 (any order), D60 (rounds, sentence bank), D66 (one list, no limit), D72 (each exercise shuffles its round),
D51 (the user's day). Code: `src/service/practice.py`, `ios/RetAIn/App/PracticeView.swift`.

**The one idea to hold on to:** the schedule lives on each **word** (`words.box` = which gap it's on,
`words.due_day` = when it's next due). Today's practice set is only a record of what was prepared and
answered today. There is no queue table: every time, the queue is worked out fresh from the words'
due dates. So nothing needs to "carry over"; an unanswered word simply still has its old due date.

## 1. What starts it

```mermaid
flowchart TD
    O([You open the app, or come back to it<br/>Practice is the first tab, D64]) --> L["App asks: GET /v1/practice/today"]
    L --> D["Server: which day is it for you?<br/>your timezone · days start at 4 am (D51)"]
    D --> E{"A practice set saved for<br/>(you, today)?"}
    E -- "yes" --> G["Return it, refreshed live:<br/>your answers so far · retained? · your note<br/>· how many words are left in each part"]
    E -- "no: first open of your day" --> Q["Code: today's queue<br/>due words, most overdue first<br/>then never-practised words, oldest first"]
    Q --> R["Prepare a round: the next 5 words,<br/>each with a fill-in sentence"]
    R --> BANK{"Bank: a sentence for this word<br/>you haven't answered yet?"}
    BANK -- "yes (instant, free)" --> SV
    BANK -- "no" --> M["<b>SENTENCE WRITER</b> + <b>JEV CHECK</b><br/>~1 s, ~$0.00006 · added to the bank"]:::writer
    M --> SV[("Save the day's set<br/>(you, day)")]
    SV --> BG["Background: write the round after's sentences,<br/>so Next round is instant"]:::code
    SV --> G
    G --> C([Chooser: your words, due first · go as far as you like])
    C --> A([You answer a word]) --> S["Code: reschedule that word now<br/>(words.box, words.due_day)"]:::code
    C --> N([Round done → Next round]) --> P["POST /v1/practice/round"] --> R

    classDef writer stroke:#2b6cb0,stroke-width:3px
    classDef code stroke:#718096,stroke-dasharray:4 3
```

- **Nothing runs overnight.** There is no scheduled job; the day's set is built the first time you
  open the app that day (built when asked for). A day you never open costs nothing.
- **Coming back to the app** (from the background) asks again; the same day returns the saved set,
  a new day (past 4 am) builds a new one.
- **The 7 pm reminder** is only a phone notification; it prepares nothing.
- **Order inside a round (D72):** each exercise visits the round's 5 words in its own shuffled order, fixed for the day (seeded by day, exercise and word), so one exercise doesn't give away the next word of another; rounds still come in priority order. The shuffle is worked out on the phone; the saved set keeps list order.

## 2. What carries over to the next day

```mermaid
flowchart LR
    subgraph D1["Your day (until 4 am)"]
        direction TB
        A["A word you answered<br/>(fill-in or sentence, D57)"] --> A1["Rescheduled at once<br/>right → next gap (3, 7, 14, 30 days)<br/>miss → tomorrow"]
        B["A word you never reached,<br/>or opened and left unanswered"] --> B1["Nothing changes<br/>still due (or still new)"]
        H["A Hint opened, no answer"] --> B1
        S["A sentence shown, never answered"] --> S1["Not marked seen:<br/>stays in the bank for you"]
    end
    A1 --> N
    B1 --> N
    S1 --> N
    N["Next day, first open:<br/>queue rebuilt from every word's due date<br/>overdue words first, then new ones"] --> R([New day's set,<br/>yesterday's leftovers at the top])
```

- **Unpractised words come back by themselves**, at the front: they're the most overdue. Skipping
  several days just makes more words due; nothing is lost and there's no cap.
- **Partly done** counts per word, not per exercise: a word with only its fill-in done has already
  moved on the schedule (either exercise alone moves it, D57); its sentence exercise does not carry over.
- **Not-yet-due** words you didn't touch keep their future due date.
- Yesterday's saved set stays in the database as history (`practice_sets`); it isn't reused.
