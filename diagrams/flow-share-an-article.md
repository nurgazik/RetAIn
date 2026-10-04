# User flow: share an article → read it with your words

Decisions: PRD D40 (three ways a word lands), D41 (a rejected word reverts its sentence, no re-run),
D19 (word checker on), D36 (fact checker), D44–D47 / D52 (how text arrives). Code:
`src/service/engine.py` → `src/generate.py` `generate_piece`. Status phases stream to the sheet
("generating", "checking").

```mermaid
flowchart TD
    U([You share or paste something you're reading]) --> IN{How it arrives}
    IN -- "selected or plain text" --> T["Text as is"]
    IN -- "Safari page" --> RD["Page cleaned on the phone<br/>(Mozilla Readability)"]
    IN -- "a link" --> LR["Link read on the phone, one reader per site<br/>(Reddit and Facebook paused: copy the text, D52)"]
    T --> SV
    RD --> SV
    LR --> SV
    SV["Service: daily cap check, save the piece"] --> W

    W["<b>WRITER</b> · model writes text<br/>places your words three ways:<br/>substitute · rephrase · note"]:::writer --> V
    V["Code: right format, only your words,<br/>enough of them — up to 3 drafts"]:::code --> J1
    V --> J2
    J1["<b>WORD CHECKER</b> · model, yes/no per word<br/>is this usage idiomatic?"]:::gate --> RV
    J2["<b>FACT CHECKER</b> · model, yes/no<br/>did the rewrite invent anything?"]:::gate --> RV
    RV["Code: a sentence with a rejected word<br/>goes back to the author's original"]:::code --> G
    G["Code: sentence guard — keep only changes that<br/>seat one of your words, tag each one<br/>substitute / rephrase / note, check notes"]:::code --> M
    M["Code: attach each word's meaning"]:::code --> R
    R([Reader: highlights + coloured bars<br/>tap a word → meaning · tap a sentence → original])

    classDef writer stroke:#2b6cb0,stroke-width:3px
    classDef gate stroke:#c05621,stroke-width:3px
    classDef code stroke:#718096,stroke-dasharray:4 3
```

**Legend:** blue = a model writes text · orange = a model answers yes/no (a quality gate, live on
every article) · dashed grey = plain code, no model.

## Tested by

| Step | Eval |
|---|---|
| Writer | [eval-article-rewrite.md](eval-article-rewrite.md) |
| Word checker | [eval-word-checker.md](eval-word-checker.md) |
| Fact checker | none yet (yes/no, so Jev is a candidate when built, D54) |

Every model call above goes through [infra-model-fallback.md](infra-model-fallback.md) (a slow or
failing host is raced by a backup model).

## Why

- **Two judges run live on every article.** They are not evals: they protect the reader in
  production. Evals are separate tests we run while building to choose the models that fill
  these boxes.
- **A rejected word costs no extra model call.** Its sentence returns to the author's original
  (D41); waiting beats a second draft.
- **Code decides the tier, not the model.** Substitute / rephrase / note is worked out from a
  word-level comparison with the source, so the reader's colours can be trusted.
