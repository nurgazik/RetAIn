# User flow: fill in the word (daily exercise)

**Status: built 2026-10-04** (PRD D56; any order since D57: the user picks this exercise on the Practice chooser, and may skip it; **rounds and the sentence bank since D60**, 2026-10-28; **one list, no limit since D66**, 2026-10-31; backlog UX-16): `src/service/practice.py`, `ios/RetAIn/App/PracticeView.swift`.

```mermaid
flowchart TD
    subgraph PREP["Rounds of 5 words (D60) — round one on your first open of the day (your day starts 4 am, D51);<br/>the next on Next round; the round after is written in the background so it's ready"]
        direction TB
        P0["Code: one list, no limit (D66)<br/>every learning word: due (most overdue first) → never practised (oldest first)<br/>→ not due yet (soonest first) · go as far as you like"]:::code --> P1
        P1["Code: the next 5 words"]:::code --> P2{"Code: a sentence in the bank for this word<br/>that you haven't answered yet?"}:::code
        P2 -- yes --> P3["Use it (oldest first),<br/>blank out the word"]:::code
        P2 -- "no: you've answered them all" --> P4["<b>SENTENCE WRITER</b> · model writes text<br/>one natural sentence using the word"]:::writer
        P6 --> P5["Added to the bank:<br/>shared by everyone, no cap, no user data"]:::code
        P4 --> P6["<b>JEV CHECK</b> · natural? P ≥ 0.9<br/>else one retry, else no fill-in today"]:::gate
        P7["<b>LOOKALIKE WRITER</b> · DeepSeek · model writes text<br/>5 words that look like the lemma, mean something else<br/>only if this lemma has none stored yet (D58)"]:::writer --> P8["Code: real word? same part of speech?<br/>spelled alike (≥ 0.4)? not a form of it?<br/>stored per lemma, shared by everyone"]:::code
    end

    P3 --> X
    P5 --> X
    X([You see the sentence with a gap: one stardust cluster per letter (D65)<br/>and the word's meaning as the cue]) --> Y([You type into the gap: letters appear out of the dust,<br/>nothing is checked until you tap Check])
    X --> H([Stuck? You tap Hint])
    H --> H1["<b>JEV CHECK</b> · each stored lookalike in your blank:<br/>P(natural) ≥ 0.5 → it fits, dropped · ~0.2 s"]:::gate
    H1 --> H2([4 pills: the word + 3 lookalikes, shuffled])
    H2 -- "you tap one: same as typing it" --> Z
    Y --> Z{"Code: is it the word, in any form?<br/>(the blanked form, the lemma, or an inflection of it)"}:::code
    Z -- yes --> OK([Correct])
    Z -- no --> NO(["Not quite: the gap shakes, your word goes in it, red,<br/>tap it for its meaning (dictionary, no model) · try again"])
    NO --> Y
    NO --> H
    OK --> S["Code: record every try; the sentence is now seen (never shown to you again);<br/>schedule from the FIRST try · due or new: right first → up a gap, wrong first → tomorrow<br/>not due yet: wrong first → tomorrow, right → no change"]:::code
    NO --> S

    classDef writer stroke:#2b6cb0,stroke-width:3px
    classDef gate stroke:#c05621,stroke-width:3px
    classDef code stroke:#718096,stroke-dasharray:4 3
```

**Legend:** blue = a model writes text · orange = a model answers yes/no · dashed grey = plain
code, no model.

**Hint (D58):** a hinted answer counts exactly like a typed one; the options shown are stored on the
attempt. **No model runs when you answer.** Models only appear in the prep, and only when you've answered every
sentence the bank has for that word (~$0.00006 a sentence: Gemma + Jev).

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

## Decided (D60, 2026-10-28)

- **Every fill-in sentence is model-written** (Gemma, Jev-checked). Sentences from your own reads are gone:
  they repeated (always the newest) and came from the rewrite engine, whose checker passes ~12% wrong usages.
- **No limit (D66).** One prioritised list of every learning word, due ones first; rounds of 5 with a
  checkpoint (Next round / Back to exercises) run down the whole list, no locked section.
- **Order inside a round (D72):** each exercise visits the round's 5 words in its own shuffled order, fixed for the day (seeded by day, exercise and word), so one exercise doesn't give away the next word of another; rounds still come in priority order.
- **A word practised before it's due never moves up** (early recall is easy recall); a miss still sends it back
  to tomorrow. The user doesn't see this distinction.
- **A word whose sentences were all rejected** gets one more try in the background on the next open (once a day);
  if it still has none, the chooser names it ("try it in a sentence") instead of counting it as done.
- **The sentence bank:** shared by all users, grows without a cap; `sentence_views` records which ones each
  user has answered; a sentence prepared but never answered stays unseen and is used next time.
- Measured on the dev account 2026-10-28: round one 1.3 s; round two 0.05 s (written in the background).
