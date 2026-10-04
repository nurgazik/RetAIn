# Eval: sentence feedback writer

**Tests:** the FEEDBACK WRITER in [flow-write-a-sentence.md](flow-write-a-sentence.md): the reason and
smallest fix a model writes for a sentence that isn't natural. It runs while building, never on a
user's request. Required by PRD D55. Record: `docs/model-bakeoff.md` "Sentence feedback writer".

```mermaid
flowchart TD
    S[("Test set: the 63 not-natural sentences<br/>from the sentence-judge set (35 wrong + 28 could-be-better)")] --> RUN
    REG["Candidate from the model list"] --> RUN
    RUN["Candidate writes verdict + reason + fix<br/>(today: reused from the sentence-judge runs, same prompt)"] --> PK
    PK["Blind packet: model names hidden, order shuffled<br/>python src/evals sentences feedback-export &lt;runs&gt;"] --> GR
    GR["Grader marks each entry<br/>reason right? · fix natural? · fix keeps the writer's meaning?<br/>(today: Claude Code, no API cost)"] --> IM
    IM["python src/evals sentences feedback-import &lt;folder&gt; &lt;grader&gt;"] --> SC
    SC["Scored on: fully right (all three) over all 63 ·<br/>calling the sentence natural = no feedback ·<br/>fix size · $ per call · seconds"] --> P{"Founder picks"}
```

## Answer key

There is no single correct fix, so a grader judges each one against the rubric (`FEEDBACK_RUBRIC`
in `src/evals/sentences.py`). Today the grader is Claude Code, with one rater and n = 63, so the
results are provisional. A human grader, or a second rater, would firm them up.
