# Model evals: how a model earns a place in the app

Decisions: PRD D54 (2026-10-04: every yes/no, choice or score step is tested against Jev);
model changes go through `src/evals` first (CLAUDE.md). Harness: `src/evals/`; results
`data/evals.db` (gitignored); leaderboard `python src/evals report` → `output/evals/leaderboard.html`.

```mermaid
flowchart TB
    subgraph REW["Article rewrite · D40 · returns text"]
        direction TB
        R1["Judges: the rewritten article"]
        R2["Test set: golden pieces<br/>data/evals/golden/public + private"]
        R3["Answer key: grader model<br/>(+ founder labels when given)"]
        R4["Scored on: words placed, coverage,<br/>wrong usages, invented facts"]
        R5["Candidates: LLMs only"]
        R1 --> R2 --> R3 --> R4 --> R5
    end

    subgraph CHK["Word checker · D19 · yes/no per word"]
        direction TB
        C1["Judges: is this highlighted word idiomatic?"]
        C2["Test set: none of its own —<br/>the highlighted words from rewrite runs"]
        C3["Answer key: grader verdicts<br/>(+ founder labels when given)"]
        C4["Scored on: wrong words caught,<br/>good words rejected"]
        C5["Candidates: LLMs + Jev"]
        C1 --> C2 --> C3 --> C4 --> C5
    end

    subgraph SEN["Sentence judge · D53 · choice of 3"]
        direction TB
        S1["Judges: natural / could-be-better / wrong"]
        S2["Test set: sentences.json, 120 items"]
        S3["Answer key: fixed + founder +<br/>provisional (Claude, 57 items)"]
        S4["Scored on: wrong sentences called natural,<br/>false alarms"]
        S5["Candidates: LLMs + Jev for the verdict;<br/>an LLM writes the feedback"]
        S1 --> S2 --> S3 --> S4 --> S5
    end

    subgraph FAC["Fact check · D36 · yes/no — no eval yet"]
        direction TB
        F1["Judges: did the rewrite invent something?"]
        F2["Test set: none yet"]
        F3["Candidates: LLMs + Jev, once built"]
        F1 --> F2 --> F3
    end

    R2 -. "highlighted words" .-> C2

    REG["Model registry<br/>data/evals/models.json"]
    DB[("Results<br/>data/evals.db")]
    LB["Leaderboard<br/>python src/evals report"]
    PICK{"Founder picks"}
    DEC["PRD decision +<br/>production config"]

    R5 --> REG
    C5 --> REG
    S5 --> REG
    F3 -.-> REG
    REG --> DB --> LB --> PICK --> DEC

    style FAC stroke-dasharray: 6 4
```

## The three eval families today

| Task | Returns | Command | Answer key | Headline metric |
|---|---|---|---|---|
| Rewrite engine (D40) | text | `run <model>` → `grade <run>` | grader model (+ founder labels when given) | words placed, coverage, wrong usages, inventions |
| Word checker (D19) | yes/no per word | `judge <model>` | grader verdicts / founder labels | share of wrong words caught |
| Sentence judge (D53, TD-20) | choice: natural / could-be-better / wrong | `sentences judge <model>` | fixed + provisional (57 of 120 Claude's) | wrong sentences called natural |

Jev candidates are not wired in yet (next step after the founder adds `TYPESAFE_API_KEY`).
Fact check (D36) is yes/no too and has no eval yet.

## Why

- **Four separate evals, shared machinery.** Each eval has its own question, test set, answer key
  and success measure; they share only the model list, the results store, the leaderboard and the
  founder's pick. The word checker is the one exception to "own test set": it re-judges the
  highlighted words that rewrite runs produced.
- **The answer key is labelled by source, in every eval.** Fixed by construction (published usage,
  a seeded error), human (the founder's blind label), provisional (Claude Code's label, counted in
  the report until a human checks) or a grader model. Where a human label disagrees with a fixed
  answer, the item is flagged and left out until resolved. The report says how many answers no
  human has checked, so a ranking built on Claude's own labels is never mistaken for a settled one.
- **One set, many models.** A model is only compared with others on the same frozen set
  and the same prompt version; anything else isn't a comparison.
- **Cost and speed sit beside quality.** With monetization undecided (P2), $ per call at
  10K users decides as much as accuracy. That's why yes/no, choice and score steps always
  get a Jev run: about $0.00002 per call, ~100 ms per TypeSafe's docs.
- **Jev can't write.** Where a step needs an explanation or a fix, Jev can decide and an
  LLM explains, and only on the cases that need it.
- **Pushback isn't tested for exercises.** Users can't argue with a verdict in the UX
  (founder 2026-10-04), so the harness's pushback-flip column doesn't count toward a pick.
