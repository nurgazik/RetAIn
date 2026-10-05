# User flow: write a sentence (daily exercise)

**Status: built 2026-10-04** (PRD D56; any order since D57: the user picks this exercise on the Practice chooser, and may skip it; backlog UX-16): `src/service/practice.py`, `ios/RetAIn/App/PracticeView.swift`.

```mermaid
flowchart TD
    A["Code: today's word<br/>(same daily set as fill-in)"]:::code --> B([You write a sentence using the word<br/>typing or dictation])
    B --> CK{"Code: does the sentence<br/>use the word?"}:::code
    CK -- no --> B
    CK -- yes --> J["<b>JEV</b> · model, choice of three<br/>how sure is it the sentence is natural?"]:::gate
    J -- "P(natural) ≥ 0.9" --> OK(["✓ Natural · ~0.2 s"])
    J -- "less sure, or Jev down" --> F["<b>GEMMA</b> · model writes text<br/>verdict + one-line reason + smallest fix"]:::writer
    F --> SHOW([You see the verdict, why, and the fix · ~3 s])
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
| Feedback writer | [eval-sentence-feedback.md](eval-sentence-feedback.md) |

## Why

- **No arguing with a verdict** (founder 2026-10-04). The verdict is final in the UX, so the
  judge never sees a second, persuasive turn.
- **Feedback only where it teaches.** A natural sentence needs no explanation; paying an LLM to
  write one would multiply cost at 10K users for little learning.
- **Strict beats lenient.** A judge that calls a wrong sentence natural teaches the error, which
  the quality bar ranks worse than nothing.
