# User flow: write a sentence (daily exercise)

**Status: designed, not built** (PRD D53, backlog UX-16). Which model fills each box is being
measured now (TD-20, TD-21); the split below — a cheap decider, an LLM only when feedback is
needed — is the design under test, not yet decided.

```mermaid
flowchart TD
    A["Code: today's word<br/>(same daily set as fill-in)"]:::code --> B([You write a sentence using the word<br/>typing or dictation])
    B --> J["<b>JUDGE</b> · model, choice of three<br/>natural · could be better · wrong<br/>(candidates: Jev or an LLM)"]:::gate
    J -- natural --> OK(["✓ Natural"])
    J -- "could be better / wrong" --> F["<b>FEEDBACK WRITER</b> · model writes text<br/>one-line reason + the smallest fix"]:::writer
    F --> SHOW([You see the verdict, why, and the fix])
    OK --> S["Code: record the attempt,<br/>schedule the word's next date"]:::code
    SHOW --> S
    S --> RET(["You decide when a word is retained<br/>(the verdicts are evidence, not the call)"])

    classDef writer stroke:#2b6cb0,stroke-width:3px
    classDef gate stroke:#c05621,stroke-width:3px
    classDef code stroke:#718096,stroke-dasharray:4 3
```

**Legend:** blue = a model writes text · orange = a model chooses from fixed answers · dashed
grey = plain code, no model.

## Tested by

| Step | Eval |
|---|---|
| Judge | [eval-sentence-judge.md](eval-sentence-judge.md) |
| Feedback writer | measured inside the same eval today (one model returns verdict, reason and fix); its own eval comes if the split is chosen |

## Why

- **No arguing with a verdict** (founder 2026-10-04). The verdict is final in the UX, so the
  judge never sees a second, persuasive turn.
- **Feedback only where it teaches.** A natural sentence needs no explanation; paying an LLM to
  write one would multiply cost at 10K users for little learning.
- **Strict beats lenient.** A judge that calls a wrong sentence natural teaches the error, which
  the quality bar ranks worse than nothing.
