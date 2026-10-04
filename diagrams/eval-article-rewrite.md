# Eval: article rewrite

**Tests:** the WRITER in [flow-share-an-article.md](flow-share-an-article.md) — by default the
whole pipeline (writer + both checkers + guard) with the candidate model in every role, so the
numbers mean "what if we switched". Runs while building, never on a user's request.
Record: `docs/model-bakeoff.md`. Current pick: Gemma 4 26B (PRD D42).

```mermaid
flowchart TD
    S[("Test set: 30 frozen articles<br/>13 public + 17 of the founder's own reads (private, gitignored)<br/>data/evals/golden/")] --> RUN
    REG["Candidate from the model list<br/>data/evals/models.json"] --> RUN
    RUN["Run the production pipeline on every article<br/>python src/evals run &lt;model&gt;"] --> OUT[("Rewritten articles<br/>data/evals.db")]
    OUT --> GR["<b>Grader</b> — one fixed model, never changes between runs<br/>every highlighted word: idiomatic / acceptable / wrong<br/>every article: invented claims, false notes<br/>python src/evals grade &lt;run&gt;"]
    GR -.-> LAB["Founder's blind labels check the grader<br/>python src/evals label (none given yet)"]
    GR --> M["Scored on: words per article · coverage ·<br/>longest stretch without a word · share wrong ·<br/>inventions · $ per article · seconds"]
    M --> LB["Leaderboard<br/>python src/evals report"]
    LB --> P{"Founder picks"}
```

## Answer key

There is no fixed answer for "a good rewrite", so a **grader model** judges every output the same
way across months. How far to trust it is measured by the founder's blind labels; that check
hasn't been done yet, so grades are relative (model vs model), not absolute.

## When it runs

A new model is worth trying, or the writer's instructions change (a run on different engine code
doesn't compare — the leaderboard warns).
