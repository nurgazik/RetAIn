# Eval: fill-in sentence writer

**Tests:** the SENTENCE WRITER in [flow-fill-in-the-word.md](flow-fill-in-the-word.md), the model that
writes a fill-in sentence for a word with no sentence from your own reading. It runs while building,
never on a user's request. Required by PRD D55. Record: `docs/model-bakeoff.md` "Fill-in sentence writer".

```mermaid
flowchart TD
    S[("Test set: the 51 golden words + meanings<br/>data/evals/golden/words.json")] --> RUN
    REG["Candidate from the model list"] --> RUN
    RUN["Candidate writes one sentence per word<br/>with the production prompt (prompts/exercises/fill-sentence.md)<br/>python src/evals fill run &lt;model&gt;"] --> CODE
    CODE["Code: is the answer there exactly once? (usable blank)<br/>Jev: P(natural) — the production gate"] --> PK
    PK["Blind packet<br/>python src/evals fill export &lt;runs&gt;"] --> GR
    GR["Grader: natural? · right sense? · clear blank<br/>(this word, not a synonym, is the best fit)<br/>(today: Claude Code)"] --> SC
    SC["Scored on: good exercises out of 51 ·<br/>bad sentences that pass the Jev gate · $ per sentence<br/>python src/evals fill report"] --> P{"Founder picks"}
```

## Answer key

A grader marks each exercise against the rubric (`RUBRIC` in `src/evals/fillin.py`). Today that's
Claude Code alone, so results are provisional.
