# Model evals: how a model earns a place in the app

Decisions: PRD D54 (2026-10-04: every yes/no, choice or score step is tested against Jev);
model changes go through `src/evals` first (CLAUDE.md). Harness: `src/evals/`; results
`data/evals.db` (gitignored); leaderboard `python src/evals report` → `output/evals/leaderboard.html`.

```mermaid
flowchart TD
    S([A model step in the app<br/>rewrite · word check · fact check · sentence judge]) --> Q{What does the<br/>step return?}
    Q -- "free text<br/>rewrite, feedback, fix" --> L["Candidates: LLMs only"]
    Q -- "yes/no · choice · score" --> J["Candidates: LLMs <b>+ Jev</b><br/>(D54: always test Jev here)"]
    L --> R
    J --> R

    subgraph GOLD["Golden set: frozen, append-only, one per task"]
        G1["Items<br/>e.g. a sentence with a target word"]
        G2{"Where the right<br/>answer comes from"}
        G1 --> G2
        G2 --> K1["Fixed by construction<br/>published usage · seeded error"]
        G2 --> K2["Human: founder's blind label"]
        G2 --> K3["Provisional: Claude Code's label<br/>counted in the report until a human checks"]
        G2 --> K4["Grader model<br/>older rewrite evals"]
    end

    R["Registry: data/evals/models.json<br/>model + settings + list price"] --> RUN["Run every candidate on the same set<br/>python src/evals … &lt;model&gt;"]
    GOLD --> RUN
    RUN --> DB[("data/evals.db<br/>one row per item per run")]
    DB --> SC["Score against the answer key<br/>quality · $ per call · seconds"]
    SC --> F{"Human answer key disagrees<br/>with a fixed answer?"}
    F -- yes --> FL["Flag the item:<br/>left out until resolved"]
    F -- no --> LB["Leaderboard<br/>only same set version + same prompt compare"]
    FL --> LB
    LB --> D{"Founder decides"}
    D -- "pick" --> P["PRD decision + production config"]
    D -- "not yet" --> H["Human review of disputed items,<br/>more data, or a new candidate"]
    H --> RUN
    P -. "prompt or model changes later" .-> RUN
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

- **One set, many models.** A model is only compared with others on the same frozen set
  and the same prompt version; anything else isn't a comparison.
- **The answer key is labelled by source.** Fixed, human, provisional and grader answers
  carry different weight; the report says how many answers no human has checked, so a
  ranking built on Claude's own labels is never mistaken for a settled one.
- **Cost and speed sit beside quality.** With monetization undecided (P2), $ per call at
  10K users decides as much as accuracy. That's why yes/no, choice and score steps always
  get a Jev run: about $0.00002 per call, ~100 ms per TypeSafe's docs.
- **Jev can't write.** Where a step needs an explanation or a fix, Jev can decide and an
  LLM explains, and only on the cases that need it.
- **Pushback isn't tested for exercises.** Users can't argue with a verdict in the UX
  (founder 2026-10-04), so the harness's pushback-flip column doesn't count toward a pick.
