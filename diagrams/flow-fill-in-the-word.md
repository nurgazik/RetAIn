# User flow: fill in the word (daily exercise)

**Status: built 2026-10-04** (PRD D56; any order since D57: the user picks this exercise on the Practice chooser, and may skip it; backlog UX-16): `src/service/practice.py`, `ios/RetAIn/App/PracticeView.swift`.

```mermaid
flowchart TD
    subgraph PREP["Daily prep — on your first open of the day (your day starts 4 am, D51)"]
        direction TB
        P1["Code: pick today's due words<br/>(scheduler; ~5 to start)"]:::code --> P2{"Code: was this word placed<br/>in one of your past articles?"}:::code
        P2 -- yes --> P3["Use that sentence,<br/>blank out the word"]:::code
        P2 -- no --> P4["<b>SENTENCE WRITER</b> · model writes text<br/>one natural sentence using the word"]:::writer
        P6 --> P5["Saved for reuse:<br/>up to 3 per word, shared"]:::code
        P4 --> P6["<b>JEV CHECK</b> · natural? P ≥ 0.9<br/>else one retry, else no fill-in today"]:::gate
        P7["<b>LOOKALIKE WRITER</b> · DeepSeek · model writes text<br/>5 words that look like the lemma, mean something else<br/>only if this lemma has none stored yet (D58)"]:::writer --> P8["Code: real word? same part of speech?<br/>spelled alike (≥ 0.4)? not a form of it?<br/>stored per lemma, shared by everyone"]:::code
    end

    P3 --> X
    P5 --> X
    X([You see the sentence with a blank<br/>and the word's meaning as the cue]) --> Y([You type the word])
    X --> H([Stuck? You tap Hint])
    H --> H1["<b>JEV CHECK</b> · each stored lookalike in your blank:<br/>P(natural) ≥ 0.5 → it fits, dropped · ~0.2 s"]:::gate
    H1 --> H2([4 pills: the word + 3 lookalikes, shuffled])
    H2 -- "you tap one: same as typing it" --> Z
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

**Hint (D58):** a hinted answer counts exactly like a typed one; the options shown are stored on the
attempt. **No model runs when you answer.** Models only appear in the prep, and only for words that have
no sentence from your own reading yet.

## Tested by

| Step | Eval |
|---|---|
| Sentence writer | [eval-fill-sentence.md](eval-fill-sentence.md) |
| Naturalness check (Jev) | [eval-sentence-judge.md](eval-sentence-judge.md) — same question as the sentence judge |
| Answer check | none needed (code) |

## Decided (D56)

- **Word forms:** the blanked form is right, and so is the base word (shown the form used).
- **One try**, then the answer; a miss sends the word back to tomorrow. No hints beyond the meaning.
- **Prep runs on the first open of the day** (1.6 s measured with four sentences to write).
