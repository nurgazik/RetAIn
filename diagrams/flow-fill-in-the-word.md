# User flow: fill in the word (daily exercise)

**Status: designed, not built** (PRD D53, backlog UX-16). Open details are marked below; this
drawing changes when UX-16 is designed with the founder.

```mermaid
flowchart TD
    subgraph PREP["Daily prep — on your first open of the day (your day starts 4 am, D51)"]
        direction TB
        P1["Code: pick today's due words<br/>(scheduler; ~5 to start)"]:::code --> P2{"Code: was this word placed<br/>in one of your past articles?"}:::code
        P2 -- yes --> P3["Use that sentence,<br/>blank out the word"]:::code
        P2 -- no --> P4["<b>SENTENCE WRITER</b> · model writes text<br/>one natural sentence using the word"]:::writer
        P4 --> P5["Saved for reuse:<br/>written once per word"]:::code
        P4 -.-> P6["Possible check (open):<br/>is the sentence natural? yes/no"]:::gate
    end

    P3 --> X
    P5 --> X
    X([You see the sentence with a blank]) --> Y([You type the word])
    Y --> Z{"Code: does it match the blanked form?<br/>(exact, ignoring case)"}:::code
    Z -- yes --> OK([Correct])
    Z -- no --> NO([Shown the answer])
    OK --> S["Code: record the attempt,<br/>schedule the word's next date"]:::code
    NO --> S

    classDef writer stroke:#2b6cb0,stroke-width:3px
    classDef gate stroke:#c05621,stroke-width:3px
    classDef code stroke:#718096,stroke-dasharray:4 3
```

**Legend:** blue = a model writes text · orange = a model answers yes/no · dashed grey = plain
code, no model.

**No model runs when you answer.** Models only appear in the prep, and only for words that have
no sentence from your own reading yet.

## Tested by

| Step | Eval |
|---|---|
| Sentence writer | none yet — needed before it ships |
| Possible naturalness check | none yet (yes/no, so Jev is a candidate, D54) |
| Answer check | none needed (code) |

## Open (decide in UX-16)

- **Word forms:** the blank may hold "bolstered" while the list says "bolster" — accept only the
  form in the sentence, or any form?
- Hints (first letter?), second tries, and what a miss does to the schedule.
- Whether prep runs on first open (D51) or ahead of time so it's instant.
