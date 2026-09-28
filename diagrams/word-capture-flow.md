# Word capture: where a word card comes from

Decision: PRD D48 (2026-09-27). Research and spike numbers: `docs/content-sources.md`,
"Dictionary sources for word cards".

```mermaid
flowchart TD
    A([User adds a word]) --> B{Already in the<br/>shared list?}
    B -- yes --> Z([Return the saved card<br/>no model call, instant])
    B -- no --> C["Look up in Wiktionary<br/>(stored on our server;<br/>follows ran→run and spelling variants)"]
    C -- found --> D["<b>From Wiktionary</b><br/>meanings in Wiktionary order<br/>part of speech · labels<br/>pronunciation · audio"]
    D --> E["<b>Model adds only</b><br/>2–3 modern examples per meaning"]
    C -- not found --> F{"Model: is this a<br/>real English word?"}
    F -- yes --> G["<b>Model writes everything</b><br/>meaning(s) · part of speech · examples<br/>badge: written by AI"]
    F -- no --> H["Save the word only<br/>flag: UNVERIFIED<br/>(user checks later; not used in rewrites)"]
    E --> S[("Shared list<br/>next user gets it free")]
    G --> S
    S --> U[("User's word list")]
    H --> U
```

## Rules the diagram encodes

- **Dictionary for facts, model for examples.** Definitions and pronunciation come from
  Wiktionary whenever it has the word; the model never rewrites them. The model always writes
  the examples, because only 62% of the founder's 235 words have a modern Wiktionary example,
  usually on the literal sense.
- **At most one model call per new word, zero for a word already in the shared list.**
- **Unverified words stay private.** They never enter the shared list, so one user's typo
  cannot become everyone's entry.
- **Meaning order is Wiktionary's**, minus senses tagged archaic, obsolete, rare or dated.
  Picking the meaning the user intended (from the sentence it came from) is deferred.
